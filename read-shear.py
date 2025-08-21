from odbAccess import openOdb
from abaqusConstants import INTEGRATION_POINT
import matplotlib.pyplot as plt
import numpy as np
import uuid
import os


RUPTURE_POSITIONS = [115, 110, 105, 100, 95, 90, 85, 80, 75, 65, 55, 45, 35, 25, 15, 5]

AVERAGE_FOLDER = 'Average'
HEATMAP_FOLDER = 'Heatmap'
MIDLINE_FOLDER = 'Midline'
os.makedirs(AVERAGE_FOLDER, exist_ok=True)
os.makedirs(HEATMAP_FOLDER, exist_ok=True)
os.makedirs(MIDLINE_FOLDER, exist_ok=True)

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
    s11_vals = []
    muu_vals = []

    for v in subset.values:
        label = v.elementLabel
        if label in label_to_coord:
            coords.append(label_to_coord[label])
            s12_vals.append(v.data[3])                # S12
            s11_vals.append(v.data[0])                # S11
            muu_vals.append(- v.data[3] / v.data[0])  # MU

    # === 7. Y-Z plane projection ===
    ys = [pt[1] for pt in coords]
    zs = [pt[2] for pt in coords]
    s11 = np.array(s11_vals)
    s12 = np.array(s12_vals)
    muu = np.array(muu_vals)

    plt.figure(figsize=(8, 4))
    sc = plt.scatter(ys, zs, c=s12, cmap='RdBu_r', edgecolors='k', linewidths=0.3)
    plt.colorbar(sc, label='S12 (MPa)')
    plt.xlabel('Y Position')
    plt.ylabel('Z Position')
    plt.title('Shear Stress S12 on RIGHT-LEFT Face (YZ Projection)')
    plt.axis('equal')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(f'./Heatmap/Shear-Stress-{RUPTURE_POSITION}-Heatmap-S12.pdf', dpi=300)
    plt.close()


    plt.figure(figsize=(8, 4))
    sc = plt.scatter(ys, zs, c=muu, cmap='RdBu_r', edgecolors='k', linewidths=0.3)
    plt.colorbar(sc, label=r'$\mu = \frac{S12}{-S11}$')
    plt.xlabel('Y Position')
    plt.ylabel('Z Position')
    plt.title('Shear Stress μ on RIGHT-LEFT Face (YZ Projection)')
    plt.axis('equal')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(f'./Heatmap/Shear-Stress-{RUPTURE_POSITION}-Heatmap-Mu.pdf', dpi=300)
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
    plt.savefig(f'./Average/Shear-Stress-S12-{RUPTURE_POSITION}-Y-Averaged.pdf', dpi=300)
    # plt.show()
    plt.close()

    # === 8.1. Compute average S11 along Y ===
    # 將 Y 值分成 bins
    num_bins = 100
    s11_array = np.array(s11)

    y_min, y_max = y_array.min(), y_array.max()
    bin_edges = np.linspace(y_min, y_max, num_bins + 1)
    bin_centers = 0.5 * (bin_edges[:-1] + bin_edges[1:])
    s11_means = np.zeros(num_bins)
    counts = np.zeros(num_bins)

    for yi, s in zip(y_array, s11_array):
        bin_idx = np.searchsorted(bin_edges, yi, side='right') - 1
        if 0 <= bin_idx < num_bins:
            s11_means[bin_idx] += s
            counts[bin_idx] += 1

    valid = counts > 0
    s11_means[valid] /= counts[valid]
    s11_means[~valid] = np.nan

    # === 9.1. Plot Y vs Avg(mu) ===
    plt.figure(figsize=(8, 4))
    # plt.plot(bin_centers, s12_means, marker='o', linewidth=1.5)
    plt.plot(bin_centers, s11_means, 'o')
    plt.xlabel('Y Position')
    plt.ylabel('Average S11 (MPa)')
    plt.title('Y-direction Averaged Shear Stress S11')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(f'./Average/Shear-Stress-S11-{RUPTURE_POSITION}-Y-Averaged.pdf', dpi=300)
    plt.close()



    # === 8.2. Compute average mu along Y ===
    # 將 Y 值分成 bins
    num_bins = 100
    muu_array = np.array(muu)

    y_min, y_max = y_array.min(), y_array.max()
    bin_edges = np.linspace(y_min, y_max, num_bins + 1)
    bin_centers = 0.5 * (bin_edges[:-1] + bin_edges[1:])
    muu_means = np.zeros(num_bins)
    counts = np.zeros(num_bins)

    for yi, s in zip(y_array, muu_array):
        bin_idx = np.searchsorted(bin_edges, yi, side='right') - 1
        if 0 <= bin_idx < num_bins:
            muu_means[bin_idx] += s
            counts[bin_idx] += 1

    valid = counts > 0
    muu_means[valid] /= counts[valid]
    muu_means[~valid] = np.nan

    # === 9.2. Plot Y vs Avg(mu) ===
    plt.figure(figsize=(8, 4))
    # plt.plot(bin_centers, s12_means, marker='o', linewidth=1.5)
    plt.plot(bin_centers, muu_means, 'o')
    plt.xlabel('Y Position')
    plt.ylabel('Average μ (MPa)')
    plt.title('Y-direction Averaged Shear Stress μ')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(f'./Average/Shear-Stress-Mu-{RUPTURE_POSITION}-Y-Averaged.pdf', dpi=300)
    plt.close()










    # === 10. Midline along Z (Z-mid) → plot S12 vs Y ===
    # 目標：在 Z 中線附近取窄帶，沿 Y 方向做平均，畫出 S12(Y)
    NUM_Y_BINS = 100              # 與上面 average 一致也可以
    INITIAL_TOL_RATIO_Z = 0.01    # Z 厚度的 1% 作為帶寬（可調）
    MAX_TOL_RATIO_Z = 0.05        # 最多放寬到 5%（可調）
    MIN_REQUIRED_POINTS_Z = 50    # 至少需要的點數（可調）

    y_arr = np.asarray(y_array)
    z_arr = np.asarray(zs)
    s_arr = np.asarray(s12_array)

    z_min, z_max = np.min(z_arr), np.max(z_arr)
    z_mid = 0.5 * (z_min + z_max)
    z_span = z_max - z_min
    tol_ratio_z = INITIAL_TOL_RATIO_Z

    # 嘗試在 Z-mid 附近找到足夠的點
    for _ in range(5):
        tol_z = tol_ratio_z * z_span
        mid_mask_z = np.abs(z_arr - z_mid) <= tol_z
        if np.count_nonzero(mid_mask_z) >= MIN_REQUIRED_POINTS_Z or tol_ratio_z >= MAX_TOL_RATIO_Z:
            break
        tol_ratio_z = min(tol_ratio_z * 2, MAX_TOL_RATIO_Z)

    # 以 Y 方向分箱，計算中線帶內的平均 S12
    y_edges_mid = np.linspace(y_min, y_max, NUM_Y_BINS + 1)
    y_centers_mid = 0.5 * (y_edges_mid[:-1] + y_edges_mid[1:])
    s12_midline_y = np.full(NUM_Y_BINS, np.nan)

    if np.count_nonzero(mid_mask_z) > 0:
        counts_y = np.zeros(NUM_Y_BINS, dtype=int)
        for yy, ss in zip(y_arr[mid_mask_z], s_arr[mid_mask_z]):
            bi = np.searchsorted(y_edges_mid, yy, side='right') - 1
            if 0 <= bi < NUM_Y_BINS:
                if np.isnan(s12_midline_y[bi]):
                    s12_midline_y[bi] = 0.0
                s12_midline_y[bi] += ss
                counts_y[bi] += 1
        good_y = counts_y > 0
        s12_midline_y[good_y] /= counts_y[good_y]
    else:
        # Fallback：每個 Y-bin 取「最接近 Z-mid」的那個點
        for bi in range(NUM_Y_BINS):
            in_bin = (y_arr >= y_edges_mid[bi]) & (y_arr < y_edges_mid[bi+1])
            if not np.any(in_bin):
                continue
            idx_local = np.argmin(np.abs(z_arr[in_bin] - z_mid))
            s12_midline_y[bi] = s_arr[in_bin][idx_local]

    # 繪圖：Y vs S12（取 Z = Z-mid 的中線帶）
    plt.figure(figsize=(8, 4))
    plt.plot(y_centers_mid, s12_midline_y, 'o-')
    plt.xlabel('Y Position')
    plt.ylabel('S12 at Z-midline (MPa)')
    plt.title(f'Midline (Z={z_mid:.3f}) Shear Stress S12 vs Y  |  tol≈{tol_ratio_z*100:.1f}% span')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(f'./{MIDLINE_FOLDER}/Shear-Stress-{RUPTURE_POSITION}-MidlineZ-S12-vs-Y.pdf', dpi=300)
    plt.close()

    odb.close()