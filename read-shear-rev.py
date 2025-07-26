from odbAccess import openOdb
from abaqusConstants import INTEGRATION_POINT
import matplotlib.pyplot as plt
import numpy as np
import uuid


RUPTURE_POSITIONS = [140, 130, 120, 110, 100, 90, 80, 70, 60]

for RUPTURE_POSITION in RUPTURE_POSITIONS:
    
    # === 1. Open ODB ===
    odb_path = f'./BlockJob-Rev-{RUPTURE_POSITION}.odb'
    print(f"\nOpening {odb_path}...")
    odb = openOdb(odb_path)
    
    step = odb.steps['Shear_Load']
    frame = step.frames[-1]
    stress_field = frame.fieldOutputs['S']


    # === 2. Get surface elements ===
    surf1 = odb.rootAssembly.surfaces['RIGHT-LEFT-TIE']
    surf2 = odb.rootAssembly.surfaces['RIGHT-LEFT-FRICTION']

    # Expand element arrays
    all_elements = []
    for ea in list(surf1.elements) + list(surf2.elements):
        all_elements.extend(ea)

    # Remove duplicates and sort by label
    unique_labels = sorted(set(el.label for el in all_elements))
    instance_name = 'SIDE_RIGHT'
    instance = odb.rootAssembly.instances[instance_name]

    # === 3. Prepare for node lookup table：nodeLabel -> coordinate ===
    node_coord_map = {node.label: node.coordinates for node in instance.nodes}

    # === 4. elementLabel -> element centroid ===
    label_to_coord = {}
    for el in instance.elements:
        if el.label in unique_labels:
            coords = [node_coord_map[nid] for nid in el.connectivity]
            x = np.mean([pt[0] for pt in coords])
            y = np.mean([pt[1] for pt in coords])
            z = np.mean([pt[2] for pt in coords])
            label_to_coord[el.label] = (x, y, z)

    # === 5. Naming ===
    region_name = 'TEMP_REGION_' + uuid.uuid4().hex[:8]
    region = odb.rootAssembly.ElementSetFromElementLabels(
        name=region_name,
        elementLabels=((instance_name, unique_labels),)
    )

    # === 6. S12 Data Extraction ===
    subset = stress_field.getSubset(region=region, position=INTEGRATION_POINT)

    coords = []
    s12_vals = []

    for v in subset.values:
        label = v.elementLabel
        if label in label_to_coord:
            coords.append(label_to_coord[label])
            s12_vals.append(v.data[3])  # S12

    # === 7. Y-Z plane projection ===
    ys = [pt[1] for pt in coords]
    zs = [pt[2] for pt in coords]
    s12 = np.array(s12_vals)

    plt.figure(figsize=(8, 6))
    sc = plt.scatter(ys, zs, c=s12, cmap='RdBu_r', edgecolors='k', linewidths=0.3)
    plt.colorbar(sc, label='S12 (MPa)')
    plt.xlabel('Y Position')
    plt.ylabel('Z Position')
    plt.title('Shear Stress S12 on RIGHT-LEFT Face (YZ Projection)')
    plt.axis('equal')
    plt.grid(True)
    plt.tight_layout()
    # plt.savefig(f'Shear-Stress-{RUPTURE_POSITION}-Heatmap-S12.png', dpi=300)
    plt.savefig(f'Shear-Stress-Rev-{RUPTURE_POSITION}-Heatmap-S12.pdf', dpi=300)
    # plt.show()

    odb.close()