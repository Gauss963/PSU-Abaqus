"""
Extract U2 (Y-displacement) on both faces of the shear interface.

Outputs →  ShearFace/
    U2-tie-<pos>.npz
    U2-friction-<pos>.npz
    SlipU2-<pos>.npz   (optional, Δu2 = friction – tie)
"""

from odbAccess import openOdb
from abaqusConstants import NODAL
import numpy as np
import uuid, os, sys, traceback

# ---------------------------------------------------------------------------
# 0. User settings
# ---------------------------------------------------------------------------
RUPTURE_POSITIONS = [115, 110, 105, 100, 95, 90, 85, 80, 75, 65, 55, 45, 35, 25, 15, 5]
STEP_NAME         = 'Shear_Load'
FRAME_INDEX       = -1          # last frame
OUTPUT_FOLDER     = 'ShearFace'
SAVE_SLIP         = True        # True → also output Δu2

# ---------------------------------------------------------------------------
# 1. Prepare output dir
# ---------------------------------------------------------------------------
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# ---------------------------------------------------------------------------
# 2. Helpers
# ---------------------------------------------------------------------------
def build_node_coord_map(assembly):
    """Return {(instanceName, nodeLabel): (x,y,z)} for the whole model."""
    mp = {}
    for inst_name, inst in assembly.instances.items():
        for nd in inst.nodes:
            mp[(inst_name, nd.label)] = nd.coordinates
    return mp


def create_nodeset_from_labels(assembly, inst_to_labels):
    """Build a temporary NodeSet given {instanceName: [labels, …]}."""
    region_name = 'TMP_NODESET_' + uuid.uuid4().hex[:6]
    node_labels = tuple((inst, labels) for inst, labels in inst_to_labels.items())
    return assembly.NodeSetFromNodeLabels(name=region_name, nodeLabels=node_labels)


def pair_by_xz(coords_a, coords_b, decimals=6):
    """Pair nodes by rounded (x,z); return index arrays ia, ib."""
    key_a = { (round(x,decimals), round(z,decimals)): i
              for i, (x,_,z) in enumerate(coords_a) }
    ia, ib = [], []
    for j, (x,_,z) in enumerate(coords_b):
        idx = key_a.get((round(x,decimals), round(z,decimals)))
        if idx is not None:
            ia.append(idx);  ib.append(j)
    return np.asarray(ia,int), np.asarray(ib,int)

# ---------------------------------------------------------------------------
# 3. Main loop
# ---------------------------------------------------------------------------
for pos in RUPTURE_POSITIONS:
    odb_path = f'./BlockJob-{pos}.odb'
    print(f'\n=== 處理 {odb_path}')
    try:
        odb   = openOdb(odb_path)
        step  = odb.steps[STEP_NAME]
        frame = step.frames[FRAME_INDEX]
        disp_field = frame.fieldOutputs['U']

        node_coord_map = build_node_coord_map(odb.rootAssembly)

        # surfaceName → tag
        surf_tags = {
            'RIGHT-LEFT-TIE'      : 'tie',
            'RIGHT-LEFT-FRICTION' : 'friction',
        }
        data = {tag: {'coords': [], 'u2': [], 'node_ids': []}
                for tag in surf_tags.values()}

        # -------- gather nodes on each surface --------
        for surf_name, tag in surf_tags.items():
            if surf_name not in odb.rootAssembly.surfaces:
                print(f'    [{tag}] WARNING: surface "{surf_name}" 不存在')
                continue
            surf = odb.rootAssembly.surfaces[surf_name]

            # robust: surf.nodes 可能是 NodeArray 或「NodeArray 的 array」
            inst_to_labels = {}
            def add_node(nd):
                inst_to_labels.setdefault(nd.instanceName, []).append(nd.label)

            for item in surf.nodes:
                # 若 item 本身還是 NodeArray，內層再迭代
                try:
                    _ = item.label          # 成功代表是 Node
                    add_node(item)
                except AttributeError:      # 不是 Node → 當成 NodeArray
                    for nd in item:
                        add_node(nd)

            # 若沒有節點，直接警告並跳過
            if not inst_to_labels:
                print(f'    [{tag}] WARNING: 找不到節點，跳過')
                continue

            region = create_nodeset_from_labels(odb.rootAssembly, inst_to_labels)
            subset = disp_field.getSubset(region=region, position=NODAL)

            for v in subset.values:
                inst  = v.instanceName
                lab   = v.nodeLabel
                coord = node_coord_map[(inst, lab)]
                data[tag]['coords'].append(coord)
                data[tag]['u2'].append(float(v.data[1]))
                data[tag]['node_ids'].append((inst, lab))

        # -------- save single-face npz --------
        for tag, d in data.items():
            if not d['coords']:
                print(f'    [{tag}] WARNING: 無資料，不產生檔案')
                continue
            arr = np.asarray(d['coords'], float)
            u2  = np.asarray(d['u2'],     float)

            np.savez(os.path.join(OUTPUT_FOLDER, f'U2-{tag}-{pos}.npz'),
                     x=arr[:,0], y=arr[:,1], z=arr[:,2],
                     u2=u2,
                     node_ids=d['node_ids'],
                     rupture_position=pos,
                     side=tag,
                     step_name=STEP_NAME,
                     frame_index=FRAME_INDEX)
            print(f'    [{tag:8s}] 已儲存 {len(u2):5d} nodes, '
                  f'u2 ∈ [{u2.min():.4e}, {u2.max():.4e}]')

        # -------- optional Δu2 --------
        if SAVE_SLIP and data['tie']['coords'] and data['friction']['coords']:
            tie_coords  = np.asarray(data['tie']['coords'],  float)
            fric_coords = np.asarray(data['friction']['coords'], float)
            ia, ib = pair_by_xz(tie_coords, fric_coords)
            if ia.size:
                slip = (np.asarray(data['friction']['u2'])[ib] -
                        np.asarray(data['tie']['u2'])[ia])
                np.savez(os.path.join(OUTPUT_FOLDER, f'SlipU2-{pos}.npz'),
                         x=tie_coords[ia,0], y=tie_coords[ia,1], z=tie_coords[ia,2],
                         du2=slip,
                         rupture_position=pos,
                         step_name=STEP_NAME,
                         frame_index=FRAME_INDEX)
                print(f'    [slip]    配對 {ia.size} nodes, '
                      f'Δu2 ∈ [{slip.min():.4e}, {slip.max():.4e}]')
            else:
                print('    [slip]    WARNING: 無法配對任何節點')
        elif SAVE_SLIP:
            print('    [slip]    跳過 — 任一面無節點')

        odb.close()

    except Exception as e:
        print(f'    !! 讀取 {odb_path} 時發生錯誤: {e}')
        traceback.print_exc(file=sys.stdout)
        continue

print(f'\n>>> 全部完成！結果已存至「{OUTPUT_FOLDER}」')