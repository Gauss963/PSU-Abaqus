from odbAccess import openOdb
from abaqusConstants import INTEGRATION_POINT, NODAL, ELEMENT_NODAL
import numpy as np
import uuid
import os
from collections import defaultdict

# ====================== helpers ======================

def _node_coord_map(instance):
    return {node.label: node.coordinates for node in instance.nodes}

def _surface_node_labels_by_plane(surf1, surf2, instance, round_nd=6, axis='x'):
    """
    Collect candidate nodes from the elements of two surfaces, bin by the coordinate along the given axis,
    take the mode (the plane where the surface lies), and return (surface_node_labels, plane_value).
    """
    idx = {'x':0, 'y':1, 'z':2}[axis]
    candidate = set()
    for ea in list(surf1.elements) + list(surf2.elements):
        for el in ea:
            candidate.update(el.connectivity)
    if not candidate:
        return set(), None

    coord_map = _node_coord_map(instance)
    bins = defaultdict(list)
    for nid in candidate:
        key = round(float(coord_map[nid][idx]), round_nd)
        bins[key].append(nid)
    plane_key, nodes = max(bins.items(), key=lambda kv: len(kv[1]))
    return set(nodes), plane_key

def _collect_surface_nodal_US(instance, disp_field, stress_field, surface_node_labels):
    """
    Collect NODAL displacements and ELEMENT_NODAL stresses for the entire instance, filter to surface_node_labels.
    Average stresses for the same node (from different elements); finally sort by (y,z,nodeLabel), and return aligned arrays.
    """
    coord_map = _node_coord_map(instance)

    # Displacement (NODAL)
    disp_subset = disp_field.getSubset(region=instance, position=NODAL)
    u2_by_node = {}
    for v in disp_subset.values:
        nid = v.nodeLabel
        if nid in surface_node_labels:
            u2_by_node[nid] = float(v.data[1])

    stress_subset = stress_field.getSubset(region=instance, position=ELEMENT_NODAL)
    s_by_node = defaultdict(list)
    for v in stress_subset.values:
        nid = v.nodeLabel
        if nid in surface_node_labels:
            s_by_node[nid].append(np.array(v.data, dtype=float))

    node_ids = sorted([nid for nid in surface_node_labels if nid in coord_map and nid in u2_by_node])
    node_ids.sort(key=lambda nid: (coord_map[nid][1], coord_map[nid][2], nid))

    xs, ys, zs = [], [], []
    s11, s22, s33, s12, s13, s23 = [], [], [], [], [], []
    u2 = []
    node_labels = []

    for nid in node_ids:
        x, y, z = coord_map[nid]
        xs.append(float(x)); ys.append(float(y)); zs.append(float(z))
        u2.append(u2_by_node[nid])
        node_labels.append(int(nid))

        if nid in s_by_node and len(s_by_node[nid]) > 0:
            meanS = np.mean(np.vstack(s_by_node[nid]), axis=0)
            s11.append(meanS[0]); s22.append(meanS[1]); s33.append(meanS[2])
            s12.append(meanS[3]); s13.append(meanS[4]); s23.append(meanS[5])
        else:
            # If the node does not have ELEMENT_NODAL stress (very rare), fill with nan
            s11.append(np.nan); s22.append(np.nan); s33.append(np.nan)
            s12.append(np.nan); s13.append(np.nan); s23.append(np.nan)

    xs = np.array(xs); ys = np.array(ys); zs = np.array(zs)
    u2 = np.array(u2)
    s11 = np.array(s11); s22 = np.array(s22); s33 = np.array(s33)
    s12 = np.array(s12); s13 = np.array(s13); s23 = np.array(s23)
    node_labels = np.array(node_labels, dtype=np.int32)

    with np.errstate(divide='ignore', invalid='ignore'):
        mu = np.where(s11 != 0, -s12 / s11, np.nan)

    return xs, ys, zs, s11, s22, s33, s12, s13, s23, u2, mu, node_labels

# ====================== main ======================

rev = False
if rev:
    RUPTURE_POSITIONS = [145, 135, 125, 115, 105, 95, 85, 80, 75, 70, 65, 60, 55, 50, 45]
else:
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

        # surfaces & instances
        surf1_right = odb.rootAssembly.surfaces['RIGHT-LEFT-TIE']
        surf2_right = odb.rootAssembly.surfaces['RIGHT-LEFT-FRICTION']
        inst_right_name = 'SIDE_RIGHT'
        inst_right = odb.rootAssembly.instances[inst_right_name]

        surf1_center = odb.rootAssembly.surfaces['CENTER-RIGHT-TIE']
        surf2_center = odb.rootAssembly.surfaces['CENTER-RIGHT-FRICTION']
        inst_center_name = 'CENTER_BLOCK'
        inst_center = odb.rootAssembly.instances[inst_center_name]

        # Use X as normal (RIGHT/LEFT face), find surface nodes
        right_nodes, x_right_plane = _surface_node_labels_by_plane(surf1_right, surf2_right, inst_right, axis='x')
        center_nodes, x_center_plane = _surface_node_labels_by_plane(surf1_center, surf2_center, inst_center, axis='x')

        # Collect nodal U2/S for nodes on the surface (right, center, each aligned)
        (x_r, y_r, z_r, s11_r, s22_r, s33_r, s12_r, s13_r, s23_r, u2_r, mu_r, node_lbl_r) = \
            _collect_surface_nodal_US(inst_right, disp_field, stress_field, right_nodes)

        (x_c, y_c, z_c, s11_c, s22_c, s33_c, s12_c, s13_c, s23_c, u2_c, mu_c, node_lbl_c) = \
            _collect_surface_nodal_US(inst_center, disp_field, stress_field, center_nodes)

        # ====== Overwrite old key for file output (right face as backward-compat default) ======
        out = {
            # Old version compatibility (right side)
            'x': x_r, 'y': y_r, 'z': z_r,
            's11': s11_r, 's22': s22_r, 's33': s33_r,
            's12': s12_r, 's13': s13_r, 's23': s23_r,
            'mu': mu_r,
            # Note: node labels are kept for int array semantics and length; old name unchanged
            'element_labels': node_lbl_r,

            # Right side details
            'x_right': x_r, 'y_right': y_r, 'z_right': z_r,
            's11_right': s11_r, 's22_right': s22_r, 's33_right': s33_r,
            's12_right': s12_r, 's13_right': s13_r, 's23_right': s23_r,
            'u2_right': u2_r, 'mu_right': mu_r,
            'element_labels_right': node_lbl_r,

            # Center details
            'x_center': x_c, 'y_center': y_c, 'z_center': z_c,
            's11_center': s11_c, 's22_center': s22_c, 's33_center': s33_c,
            's12_center': s12_c, 's13_center': s13_c, 's23_center': s23_c,
            'u2_center': u2_c, 'mu_center': mu_c,
            'element_labels_center': node_lbl_c,

            # metadata
            'rupture_position': RUPTURE_POSITION,
            'instance_name': inst_right_name,
            'step_name': 'Shear_Load',
            'frame_index': -1
        }

        key_r = {(round(float(y_r[i]),6), round(float(z_r[i]),6)): i for i in range(len(y_r))}
        yy, zz, u2_rel = [], [], []
        for j in range(len(y_c)):
            k = (round(float(y_c[j]),6), round(float(z_c[j]),6))
            if k in key_r:
                i = key_r[k]
                yy.append(y_r[i]); zz.append(z_r[i])
                u2_rel.append(u2_r[i] - u2_c[j])
        if u2_rel:
            out['y_relative'] = np.array(yy)
            out['z_relative'] = np.array(zz)
            out['u2_relative'] = np.array(u2_rel)

        output_file = os.path.join(OUTPUT_FOLDER, f'ShearFace-{RUPTURE_POSITION}.npz')
        np.savez(output_file, **out)

        print(f"  Saved: {output_file}")
        print(f"  RIGHT nodes: {len(x_r)}, CENTER nodes: {len(x_c)}")
        if len(u2_rel) > 0:
            print(f"  Relative U2 stats (R-C): mean={np.mean(out['u2_relative']):.6e}, "
                  f"min={np.min(out['u2_relative']):.6e}, max={np.max(out['u2_relative']):.6e}")

        odb.close()

    except Exception as e:
        print(f"  Error processing {odb_path}: {str(e)}")
        import traceback
        traceback.print_exc()
        continue

print("\nData extraction complete!")
print(f"All files saved in '{OUTPUT_FOLDER}' folder")