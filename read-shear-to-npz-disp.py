from odbAccess import openOdb
from abaqusConstants import INTEGRATION_POINT, NODAL
import numpy as np
import uuid
import os

# Define rupture positions
RUPTURE_POSITIONS = [115, 110, 105, 100, 95, 90, 85, 80, 75, 65, 55, 45, 35, 25, 15, 5]

# Create output folder
OUTPUT_FOLDER = 'ShearFace'
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

for RUPTURE_POSITION in RUPTURE_POSITIONS:
    
    # === 1. Open ODB ===
    odb_path = f'./BlockJob-{RUPTURE_POSITION}.odb'
    print(f"\nProcessing {odb_path}...")
    
    try:
        odb = openOdb(odb_path)
        
        # Get step and frame
        step = odb.steps['Shear_Load']
        frame = step.frames[-1]  # Last frame
        
        # Get both stress and displacement fields
        stress_field = frame.fieldOutputs['S']
        disp_field = frame.fieldOutputs['U']  # 位移場
        
        # === 2. Process RIGHT side (side_right instance) ===
        surf1_right = odb.rootAssembly.surfaces['RIGHT-LEFT-TIE']
        surf2_right = odb.rootAssembly.surfaces['RIGHT-LEFT-FRICTION']
        
        # Get elements for right side
        all_elements_right = []
        for ea in list(surf1_right.elements) + list(surf2_right.elements):
            all_elements_right.extend(ea)
        
        unique_labels_right = sorted(set(el.label for el in all_elements_right))
        instance_name_right = 'SIDE_RIGHT'
        instance_right = odb.rootAssembly.instances[instance_name_right]
        
        # Node coordinate map for right side
        node_coord_map_right = {node.label: node.coordinates for node in instance_right.nodes}
        
        # Element centroid for right side
        label_to_coord_right = {}
        for el in instance_right.elements:
            if el.label in unique_labels_right:
                coords = [node_coord_map_right[nid] for nid in el.connectivity]
                x = np.mean([pt[0] for pt in coords])
                y = np.mean([pt[1] for pt in coords])
                z = np.mean([pt[2] for pt in coords])
                label_to_coord_right[el.label] = (x, y, z)
        
        # Create region for right side
        region_name_right = 'TEMP_REGION_RIGHT_' + uuid.uuid4().hex[:8]
        region_right = odb.rootAssembly.ElementSetFromElementLabels(
            name=region_name_right,
            elementLabels=((instance_name_right, unique_labels_right),)
        )
        
        # Extract stress data for right side
        subset_stress_right = stress_field.getSubset(region=region_right, position=INTEGRATION_POINT)
        
        # Extract displacement data for right side (at nodes)
        subset_disp_right = disp_field.getSubset(region=region_right, position=NODAL)
        
        # Process right side data
        coords_right = []
        s12_vals_right = []
        s11_vals_right = []
        u2_vals_right = []  # 位移 u2
        element_labels_right = []
        
        # Get stress values
        stress_data_right = {}
        for v in subset_stress_right.values:
            label = v.elementLabel
            if label in label_to_coord_right:
                stress_data_right[label] = {
                    'coord': label_to_coord_right[label],
                    's11': v.data[0],
                    's12': v.data[3]
                }
        
        # Get displacement values (averaged per element)
        disp_data_right = {}
        for v in subset_disp_right.values:
            # 位移數據是節點數據，需要映射到元素
            node_label = v.nodeLabel
            u2 = v.data[1]  # U2 是第二個分量
            
            # 找到包含此節點的元素
            for el in instance_right.elements:
                if el.label in unique_labels_right and node_label in el.connectivity:
                    if el.label not in disp_data_right:
                        disp_data_right[el.label] = []
                    disp_data_right[el.label].append(u2)
        
        # 合併數據
        for label in stress_data_right:
            if label in disp_data_right:
                coords_right.append(stress_data_right[label]['coord'])
                s11_vals_right.append(stress_data_right[label]['s11'])
                s12_vals_right.append(stress_data_right[label]['s12'])
                # 平均該元素所有節點的 u2 值
                u2_vals_right.append(np.mean(disp_data_right[label]))
                element_labels_right.append(label)
        
        # === 3. Process CENTER side (center_block instance) ===
        surf1_center = odb.rootAssembly.surfaces['CENTER-RIGHT-TIE']
        surf2_center = odb.rootAssembly.surfaces['CENTER-RIGHT-FRICTION']
        
        # Similar process for center block
        all_elements_center = []
        for ea in list(surf1_center.elements) + list(surf2_center.elements):
            all_elements_center.extend(ea)
        
        unique_labels_center = sorted(set(el.label for el in all_elements_center))
        instance_name_center = 'CENTER_BLOCK'
        instance_center = odb.rootAssembly.instances[instance_name_center]
        
        # Node coordinate map for center
        node_coord_map_center = {node.label: node.coordinates for node in instance_center.nodes}
        
        # Element centroid for center
        label_to_coord_center = {}
        for el in instance_center.elements:
            if el.label in unique_labels_center:
                coords = [node_coord_map_center[nid] for nid in el.connectivity]
                x = np.mean([pt[0] for pt in coords])
                y = np.mean([pt[1] for pt in coords])
                z = np.mean([pt[2] for pt in coords])
                label_to_coord_center[el.label] = (x, y, z)
        
        # Create region for center
        region_name_center = 'TEMP_REGION_CENTER_' + uuid.uuid4().hex[:8]
        region_center = odb.rootAssembly.ElementSetFromElementLabels(
            name=region_name_center,
            elementLabels=((instance_name_center, unique_labels_center),)
        )
        
        # Extract stress and displacement for center
        subset_stress_center = stress_field.getSubset(region=region_center, position=INTEGRATION_POINT)
        subset_disp_center = disp_field.getSubset(region=region_center, position=NODAL)
        
        # Process center data
        coords_center = []
        s12_vals_center = []
        s11_vals_center = []
        u2_vals_center = []
        element_labels_center = []
        
        # Get stress values for center
        stress_data_center = {}
        for v in subset_stress_center.values:
            label = v.elementLabel
            if label in label_to_coord_center:
                stress_data_center[label] = {
                    'coord': label_to_coord_center[label],
                    's11': v.data[0],
                    's12': v.data[3]
                }
        
        # Get displacement values for center
        disp_data_center = {}
        for v in subset_disp_center.values:
            node_label = v.nodeLabel
            u2 = v.data[1]
            
            for el in instance_center.elements:
                if el.label in unique_labels_center and node_label in el.connectivity:
                    if el.label not in disp_data_center:
                        disp_data_center[el.label] = []
                    disp_data_center[el.label].append(u2)
        
        # 合併數據
        for label in stress_data_center:
            if label in disp_data_center:
                coords_center.append(stress_data_center[label]['coord'])
                s11_vals_center.append(stress_data_center[label]['s11'])
                s12_vals_center.append(stress_data_center[label]['s12'])
                u2_vals_center.append(np.mean(disp_data_center[label]))
                element_labels_center.append(label)
        
        # === 4. Convert to numpy arrays ===
        # Right side
        coords_array_right = np.array(coords_right)
        x_coords_right = coords_array_right[:, 0]
        y_coords_right = coords_array_right[:, 1]
        z_coords_right = coords_array_right[:, 2]
        s11_right = np.array(s11_vals_right)
        s12_right = np.array(s12_vals_right)
        u2_right = np.array(u2_vals_right)
        
        # Center side
        coords_array_center = np.array(coords_center)
        x_coords_center = coords_array_center[:, 0]
        y_coords_center = coords_array_center[:, 1]
        z_coords_center = coords_array_center[:, 2]
        s11_center = np.array(s11_vals_center)
        s12_center = np.array(s12_vals_center)
        u2_center = np.array(u2_vals_center)
        
        # Calculate friction coefficient
        with np.errstate(divide='ignore', invalid='ignore'):
            mu_right = np.where(s11_right != 0, -s12_right / s11_right, np.nan)
            mu_center = np.where(s11_center != 0, -s12_center / s11_center, np.nan)
        
        # === 5. Save as NPZ file ===
        output_file = os.path.join(OUTPUT_FOLDER, f'ShearFace-{RUPTURE_POSITION}.npz')

        # 為了向後兼容，保持原有的變數名稱（使用右側數據）
        np.savez(output_file,
                # 原有格式（保持兼容性）
                x=x_coords_right,
                y=y_coords_right,
                z=z_coords_right,
                s11=s11_right,
                s12=s12_right,
                mu=mu_right,
                element_labels=element_labels_right,
                
                # 新增的詳細數據（兩側分開）
                x_right=x_coords_right,
                y_right=y_coords_right,
                z_right=z_coords_right,
                s11_right=s11_right,
                s12_right=s12_right,
                u2_right=u2_right,
                mu_right=mu_right,
                element_labels_right=element_labels_right,
                
                # Center side data
                x_center=x_coords_center,
                y_center=y_coords_center,
                z_center=z_coords_center,
                s11_center=s11_center,
                s12_center=s12_center,
                u2_center=u2_center,
                mu_center=mu_center,
                element_labels_center=element_labels_center,
                
                # Metadata
                rupture_position=RUPTURE_POSITION,
                instance_name=instance_name_right,
                step_name='Shear_Load',
                frame_index=-1
                )
        
        print(f"  Successfully saved data to {output_file}")
        print(f"  Right side - Number of points: {len(x_coords_right)}")
        print(f"  Right side - U2 range: [{np.min(u2_right):.6f}, {np.max(u2_right):.6f}] mm")
        print(f"  Center side - Number of points: {len(x_coords_center)}")
        print(f"  Center side - U2 range: [{np.min(u2_center):.6f}, {np.max(u2_center):.6f}] mm")
        print(f"  Relative displacement (U2): {np.mean(u2_right) - np.mean(u2_center):.6f} mm")
        
        # Close ODB
        odb.close()
        
    except Exception as e:
        print(f"  Error processing {odb_path}: {str(e)}")
        continue

print("\nData extraction complete!")
print(f"All files saved in '{OUTPUT_FOLDER}' folder")