from odbAccess import openOdb
from abaqusConstants import INTEGRATION_POINT, NODAL, ELEMENT_NODAL
import numpy as np
import uuid
import os
from collections import defaultdict

# ===== Helper functions =======================================================

def _node_coord_map(instance):
    return {node.label: node.coordinates for node in instance.nodes}

def _surface_u2_map_from_surfaces(disp_field, surf1, surf2, instance, comp_index=1):
    """
    不用 surface 當 region；改取 instance 的 NODAL 位移，然後只挑選屬於 surface 平面上的節點。
    1) 由 surface 的 elements 收集候選節點
    2) 以節點 x 座標四捨五入到 1e-6 分箱，取節點數最多的那一箱作為真正表面平面
    3) 回傳 dict {(round(y,6), round(z,6)): mean(U2)}
    """
    # 兩個 surface 的元素 → 候選節點
    candidate_node_labels = set()
    for ea in list(surf1.elements) + list(surf2.elements):
        for el in ea:
            candidate_node_labels.update(el.connectivity)

    if not candidate_node_labels:
        return {}

    coord_map = _node_coord_map(instance)

    # 以 x 分箱找出表面平面（最多節點的 x-bin）
    x_bins = defaultdict(list)
    for nid in candidate_node_labels:
        x = float(coord_map[nid][0])
        x_key = round(x, 6)
        x_bins[x_key].append(nid)

    x_mode_key, mode_nodes = max(x_bins.items(), key=lambda kv: len(kv[1]))

    surface_node_labels = set(mode_nodes)

    # 從整個 instance 抓 NODAL 位移，再濾到表面節點
    subset = disp_field.getSubset(region=instance, position=NODAL)
    acc = defaultdict(list)
    for v in subset.values:
        nid = v.nodeLabel
        if nid in surface_node_labels:
            y, z = coord_map[nid][1], coord_map[nid][2]
            key = (round(float(y), 6), round(float(z), 6))
            acc[key].append(float(v.data[comp_index]))

    return {k: float(np.mean(vals)) for k, vals in acc.items()}

def _merge_two_maps_avg(m1, m2):
    out = {}
    for k, v in m1.items():
        out[k] = [v]
    for k, v in m2.items():
        out.setdefault(k, []).append(v)
    return {k: float(np.mean(vs)) for k, vs in out.items()}

def _align_yz_maps(map_right, map_center):
    keys = sorted(set(map_right.keys()) & set(map_center.keys()))
    if not keys:
        return (np.array([]),)*4
    y = np.array([k[0] for k in keys])
    z = np.array([k[1] for k in keys])
    u2_r = np.array([map_right[k] for k in keys])
    u2_c = np.array([map_center[k] for k in keys])
    return y, z, u2_r, u2_c

def _collect_element_stress_at_centroid(stress_field, assembly, instance_name, elem_labels, element_map, node_coord_map):
    """
    用 ELEMENT_NODAL 應力，對每元素的節點值做平均，並配上元素幾何心座標。
    回傳：coords, s11,s22,s33,s12,s13,s23, element_labels（同順序）
    """
    region_name = 'TEMP_REGION_' + uuid.uuid4().hex[:8]
    region = assembly.ElementSetFromElementLabels(
        name=region_name, elementLabels=((instance_name, elem_labels),)
    )
    subset = stress_field.getSubset(region=region, position=ELEMENT_NODAL)

    per_elem = defaultdict(list)
    for v in subset.values:
        per_elem[v.elementLabel].append(np.array(v.data, dtype=float))

    coords, s11, s22, s33, s12, s13, s23, el_out = [], [], [], [], [], [], [], []
    for el_label, arrs in per_elem.items():
        if el_label not in element_map:
            continue
        element = element_map[el_label]
        node_coords = [node_coord_map[nid] for nid in element.connectivity]
        x = float(np.mean([pt[0] for pt in node_coords]))
        y = float(np.mean([pt[1] for pt in node_coords]))
        z = float(np.mean([pt[2] for pt in node_coords]))
        meanS = np.mean(np.vstack(arrs), axis=0)
        coords.append((x, y, z))
        s11.append(meanS[0]); s22.append(meanS[1]); s33.append(meanS[2])
        s12.append(meanS[3]); s13.append(meanS[4]); s23.append(meanS[5])
        el_out.append(el_label)

    return coords, s11, s22, s33, s12, s13, s23, el_out

# ===== Main ===================================================================

RUPTURE_POSITIONS = [115, 110, 105, 100, 95, 90, 85, 80, 75, 65, 55, 45, 35, 25, 15, 5]

OUTPUT_FOLDER = 'ShearFace'
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

for RUPTURE_POSITION in RUPTURE_POSITIONS:
    odb_path = f'./BlockJob-{RUPTURE_POSITION}.odb'
    print(f"\nProcessing {odb_path}...")
    try:
        odb = openOdb(odb_path)

        step = odb.steps['Shear_Load']
        frame = step.frames[-1]

        stress_field = frame.fieldOutputs['S']
        disp_field = frame.fieldOutputs['U']

        # === Surfaces & instances =================================================
        # RIGHT 面（RIGHT 塊的左側面）
        surf1_right = odb.rootAssembly.surfaces['RIGHT-LEFT-TIE']
        surf2_right = odb.rootAssembly.surfaces['RIGHT-LEFT-FRICTION']
        instance_name_right = 'SIDE_RIGHT'
        instance_right = odb.rootAssembly.instances[instance_name_right]

        # CENTER 面（CENTER 塊的右側面）
        surf1_center = odb.rootAssembly.surfaces['CENTER-RIGHT-TIE']
        surf2_center = odb.rootAssembly.surfaces['CENTER-RIGHT-FRICTION']
        instance_name_center = 'CENTER_BLOCK'
        instance_center = odb.rootAssembly.instances[instance_name_center]

        # === (A) 以「表面節點」對齊的位移（不使用 surface 當 region） ================
        print("  Extracting surface-nodal U2 and aligning by (y,z) without using surface as region...")

        u2_map_r_1 = _surface_u2_map_from_surfaces(disp_field, surf1_right, surf2_right, instance_right, comp_index=1)
        u2_map_c_1 = _surface_u2_map_from_surfaces(disp_field, surf1_center, surf2_center, instance_center, comp_index=1)

        # 兩個（TIE/FRICTION）面各自已合併在函數內，不過保持接口一致也可再次 merge（等同 no-op）
        u2_map_right = u2_map_r_1
        u2_map_center = u2_map_c_1

        y_surf, z_surf, u2_right_surf, u2_center_surf = _align_yz_maps(u2_map_right, u2_map_center)
        u2_relative_surf = u2_right_surf - u2_center_surf

        print(f"    Surface-aligned nodes: {len(y_surf)} pairs")
        if len(u2_relative_surf) > 0:
            print(f"    Relative U2 (right - center): mean={np.mean(u2_relative_surf):.6f}, "
                  f"min={np.min(u2_relative_surf):.6f}, max={np.max(u2_relative_surf):.6f} (model units)")

        # === (B) 元素心流程（用 ELEMENT_NODAL 應力，避免整合點多筆重複） ============
        # RIGHT
        all_elements_right = []
        for ea in list(surf1_right.elements) + list(surf2_right.elements):
            all_elements_right.extend(ea)
        unique_labels_right = sorted(set(el.label for el in all_elements_right))
        elem_map_right = {el.label: el for el in instance_right.elements}
        node_coord_map_right = _node_coord_map(instance_right)

        coords_right, s11_r, s22_r, s33_r, s12_r, s13_r, s23_r, el_labels_right = _collect_element_stress_at_centroid(
            stress_field, odb.rootAssembly, instance_name_right, unique_labels_right,
            elem_map_right, node_coord_map_right
        )

        disp_values_right_all = disp_field.getSubset(region=instance_right, position=NODAL)
        node_disp_right = {v.nodeLabel: float(v.data[1]) for v in disp_values_right_all.values}
        u2_right_elem = []
        for el_label in el_labels_right:
            el = elem_map_right.get(el_label, None)
            if el is None:
                u2_right_elem.append(np.nan)
                continue
            uvals = [node_disp_right[nid] for nid in el.connectivity if nid in node_disp_right]
            u2_right_elem.append(float(np.mean(uvals)) if uvals else np.nan)

        # CENTER
        all_elements_center = []
        for ea in list(surf1_center.elements) + list(surf2_center.elements):
            all_elements_center.extend(ea)
        unique_labels_center = sorted(set(el.label for el in all_elements_center))
        elem_map_center = {el.label: el for el in instance_center.elements}
        node_coord_map_center = _node_coord_map(instance_center)

        coords_center, s11_c, s22_c, s33_c, s12_c, s13_c, s23_c, el_labels_center = _collect_element_stress_at_centroid(
            stress_field, odb.rootAssembly, instance_name_center, unique_labels_center,
            elem_map_center, node_coord_map_center
        )

        disp_values_center_all = disp_field.getSubset(region=instance_center, position=NODAL)
        node_disp_center = {v.nodeLabel: float(v.data[1]) for v in disp_values_center_all.values}
        u2_center_elem = []
        for el_label in el_labels_center:
            el = elem_map_center.get(el_label, None)
            if el is None:
                u2_center_elem.append(np.nan)
                continue
            uvals = [node_disp_center[nid] for nid in el.connectivity if nid in node_disp_center]
            u2_center_elem.append(float(np.mean(uvals)) if uvals else np.nan)

        # 轉 numpy（元素心版本）
        coords_array_right = np.array(coords_right) if len(coords_right) else np.zeros((0,3))
        x_coords_right = coords_array_right[:,0] if coords_array_right.size else np.array([])
        y_coords_right = coords_array_right[:,1] if coords_array_right.size else np.array([])
        z_coords_right = coords_array_right[:,2] if coords_array_right.size else np.array([])

        coords_array_center = np.array(coords_center) if len(coords_center) else np.zeros((0,3))
        x_coords_center = coords_array_center[:,0] if coords_array_center.size else np.array([])
        y_coords_center = coords_array_center[:,1] if coords_array_center.size else np.array([])
        z_coords_center = coords_array_center[:,2] if coords_array_center.size else np.array([])

        s11_right = np.array(s11_r); s22_right = np.array(s22_r); s33_right = np.array(s33_r)
        s12_right = np.array(s12_r); s13_right = np.array(s13_r); s23_right = np.array(s23_r)
        s11_center = np.array(s11_c); s22_center = np.array(s22_c); s33_center = np.array(s33_c)
        s12_center = np.array(s12_c); s13_center = np.array(s13_c); s23_center = np.array(s23_c)

        u2_right_elem = np.array(u2_right_elem)
        u2_center_elem = np.array(u2_center_elem)

        # 摩擦係數（元素心版本）
        with np.errstate(divide='ignore', invalid='ignore'):
            mu_right = np.where(s11_right != 0, -s12_right / s11_right, np.nan)
            mu_center = np.where(s11_center != 0, -s12_center / s11_center, np.nan)

        # === 儲存 ================================================================
        output_file = os.path.join(OUTPUT_FOLDER, f'ShearFace-{RUPTURE_POSITION}.npz')
        np.savez(output_file,
                 # 舊版相容（右側元素心）
                 x=x_coords_right, y=y_coords_right, z=z_coords_right,
                 s11=s11_right, s22=s22_right, s33=s33_right,
                 s12=s12_right, s13=s13_right, s23=s23_right,
                 mu=mu_right,
                 element_labels=el_labels_right,

                 # 右側元素心資料
                 x_right=x_coords_right, y_right=y_coords_right, z_right=z_coords_right,
                 s11_right=s11_right, s22_right=s22_right, s33_right=s33_right,
                 s12_right=s12_right, s13_right=s13_right, s23_right=s23_right,
                 u2_right=u2_right_elem, mu_right=mu_right,
                 element_labels_right=el_labels_right,

                 # 中央元素心資料
                 x_center=x_coords_center, y_center=y_coords_center, z_center=z_coords_center,
                 s11_center=s11_center, s22_center=s22_center, s33_center=s33_center,
                 s12_center=s12_center, s13_center=s13_center, s23_center=s23_center,
                 u2_center=u2_center_elem, mu_center=mu_center,
                 element_labels_center=el_labels_center,

                 # ★ 新增：表面節點對齊的資料（後處理建議用這組）
                 y_surf=y_surf, z_surf=z_surf,
                 u2_right_surf=u2_right_surf, u2_center_surf=u2_center_surf,
                 u2_relative_surf=u2_relative_surf,

                 # Metadata
                 rupture_position=RUPTURE_POSITION,
                 instance_name=instance_name_right,
                 step_name='Shear_Load',
                 frame_index=-1
                 )

        print(f"  Saved: {output_file}")
        print(f"  Element-centroid (RIGHT) points: {len(x_coords_right)}")
        print(f"  Element-centroid (CENTER) points: {len(x_coords_center)}")
        print(f"  Surface-aligned node pairs: {len(y_surf)}")

        odb.close()

    except Exception as e:
        print(f"  Error processing {odb_path}: {str(e)}")
        import traceback
        traceback.print_exc()
        continue

print("\nData extraction complete!")
print(f"All files saved in '{OUTPUT_FOLDER}' folder")