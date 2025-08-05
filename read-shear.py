from odbAccess import openOdb
from abaqusConstants import INTEGRATION_POINT
import matplotlib.pyplot as plt
import numpy as np
import uuid
import os


RUPTURE_POSITIONS = [105, 100, 95, 90, 85, 80, 75, 65, 55, 45, 35, 25, 15, 5]

AVERAGE_FOLDER = 'Average'
HEATMAP_FOLDER = 'Heatmap'
os.makedirs(AVERAGE_FOLDER, exist_ok=True)
os.makedirs(HEATMAP_FOLDER, exist_ok=True)

for RUPTURE_POSITION in RUPTURE_POSITIONS:
    
    # === 1. Open ODB ===
    odb_path = f'./BlockJob-{RUPTURE_POSITION}.odb'
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
    plt.savefig(f'./Heatmap/Shear-Stress-{RUPTURE_POSITION}-Heatmap-S12.pdf', dpi=300)
    # plt.show()
    plt.close()

    
    # === 8. Compute average S12 along Y ===
    # 將 Y 值分成 bins
    num_bins = 100
    y_array = np.array(ys)
    s12_array = np.array(s12)

    y_min, y_max = y_array.min(), y_array.max()
    bin_edges = np.linspace(y_min, y_max, num_bins + 1)
    bin_centers = 0.5 * (bin_edges[:-1] + bin_edges[1:])
    s12_means = np.zeros(num_bins)
    counts = np.zeros(num_bins)

    for yi, s in zip(y_array, s12_array):
        bin_idx = np.searchsorted(bin_edges, yi, side='right') - 1
        if 0 <= bin_idx < num_bins:
            s12_means[bin_idx] += s
            counts[bin_idx] += 1

    valid = counts > 0
    s12_means[valid] /= counts[valid]
    s12_means[~valid] = np.nan

    # === 9. Plot Y vs Avg(S12) ===
    plt.figure(figsize=(8, 4))
    # plt.plot(bin_centers, s12_means, marker='o', linewidth=1.5)
    plt.plot(bin_centers, s12_means, 'o')
    plt.xlabel('Y Position')
    plt.ylabel('Average S12 (MPa)')
    plt.title('Y-direction Averaged Shear Stress S12')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(f'./Average/Shear-Stress-{RUPTURE_POSITION}-Y-Averaged.pdf', dpi=300)
    # plt.show()
    plt.close()


    odb.close()