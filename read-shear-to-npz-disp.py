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
        disp_field = frame.fieldOutputs['U']
        
        # === 2. Process RIGHT side (SIDE_RIGHT instance) ===
        surf1_right = odb.rootAssembly.surfaces['RIGHT-LEFT-TIE']
        surf2_right = odb.rootAssembly.surfaces['RIGHT-LEFT-FRICTION']
        
        # Get elements for right side
        all_elements_right = []
        for ea in list(surf1_right.elements) + list(surf2_right.elements):
            all_elements_right.extend(ea)
        
        unique_labels_right = sorted(set(el.label for el in all_elements_right))
        instance_name_right = 'SIDE_RIGHT'
        instance_right = odb.rootAssembly.instances[instance_name_right]
        
        print(f"  Found {len(unique_labels_right)} unique elements on right side")
        print(f"  Building element map...")
        
        # Build element map for efficiency - 這是關鍵優化
        element_map_right = {}
        for el in instance_right.elements:
            element_map_right[el.label] = el
        
        print(f"  Getting displacement data...")
        # Get displacement for entire instance
        disp_values_right_all = disp_field.getSubset(region=instance_right, position=NODAL)
        
        # Create a dictionary of node displacements
        node_disp_right = {}
        for v in disp_values_right_all.values:
            node_disp_right[v.nodeLabel] = v.data[1]  # U2 component
        
        print(f"  Getting node coordinates...")
        # Node coordinate map
        node_coord_map_right = {node.label: node.coordinates for node in instance_right.nodes}
        
        # Process elements and get their data
        coords_right = []
        s11_vals_right = []
        s22_vals_right = []
        s33_vals_right = []
        s12_vals_right = []
        s13_vals_right = []
        s23_vals_right = []
        u2_vals_right = []
        element_labels_right = []
        
        print(f"  Getting stress data...")
        # Create region for stress extraction
        region_name_right = 'TEMP_REGION_RIGHT_' + uuid.uuid4().hex[:8]
        region_right = odb.rootAssembly.ElementSetFromElementLabels(
            name=region_name_right,
            elementLabels=((instance_name_right, unique_labels_right),)
        )
        
        # Get stress data
        subset_stress_right = stress_field.getSubset(region=region_right, position=INTEGRATION_POINT)
        
        print(f"  Processing {len(subset_stress_right.values)} stress values...")
        # Process each element
        processed_count = 0
        for v in subset_stress_right.values:
            el_label = v.elementLabel
            
            # Use the pre-built map instead of searching
            if el_label in element_map_right:
                element = element_map_right[el_label]
                
                # Get element centroid
                node_coords = [node_coord_map_right[nid] for nid in element.connectivity]
                x = np.mean([pt[0] for pt in node_coords])
                y = np.mean([pt[1] for pt in node_coords])
                z = np.mean([pt[2] for pt in node_coords])
                
                # Get average U2 for this element's nodes
                u2_values = []
                for nid in element.connectivity:
                    if nid in node_disp_right:
                        u2_values.append(node_disp_right[nid])
                
                if u2_values:  # Only add if we have displacement data
                    coords_right.append((x, y, z))
                    s11_vals_right.append(v.data[0])
                    s22_vals_right.append(v.data[1])
                    s33_vals_right.append(v.data[2])
                    s12_vals_right.append(v.data[3])
                    s13_vals_right.append(v.data[4])
                    s23_vals_right.append(v.data[5])
                    u2_vals_right.append(np.mean(u2_values))
                    element_labels_right.append(el_label)
                    processed_count += 1
                    
                    if processed_count % 500 == 0:
                        print(f"    Processed {processed_count} elements...")
        
        print(f"  Right side: Processed {len(coords_right)} elements with complete data")
        
        # === 3. Process CENTER side (CENTER_BLOCK instance) ===
        surf1_center = odb.rootAssembly.surfaces['CENTER-RIGHT-TIE']
        surf2_center = odb.rootAssembly.surfaces['CENTER-RIGHT-FRICTION']
        
        # Get elements for center side
        all_elements_center = []
        for ea in list(surf1_center.elements) + list(surf2_center.elements):
            all_elements_center.extend(ea)
        
        unique_labels_center = sorted(set(el.label for el in all_elements_center))
        instance_name_center = 'CENTER_BLOCK'
        instance_center = odb.rootAssembly.instances[instance_name_center]
        
        print(f"  Found {len(unique_labels_center)} unique elements on center side")
        print(f"  Building element map...")
        
        # Build element map for efficiency
        element_map_center = {}
        for el in instance_center.elements:
            element_map_center[el.label] = el
        
        print(f"  Getting displacement data...")
        # Get displacement for entire instance
        disp_values_center_all = disp_field.getSubset(region=instance_center, position=NODAL)
        
        # Create a dictionary of node displacements
        node_disp_center = {}
        for v in disp_values_center_all.values:
            node_disp_center[v.nodeLabel] = v.data[1]  # U2 component
        
        print(f"  Getting node coordinates...")
        # Node coordinate map
        node_coord_map_center = {node.label: node.coordinates for node in instance_center.nodes}
        
        # Process elements and get their data
        coords_center = []
        s11_vals_center = []
        s22_vals_center = []
        s33_vals_center = []
        s12_vals_center = []
        s13_vals_center = []
        s23_vals_center = []
        u2_vals_center = []
        element_labels_center = []
        
        print(f"  Getting stress data...")
        # Create region for stress extraction
        region_name_center = 'TEMP_REGION_CENTER_' + uuid.uuid4().hex[:8]
        region_center = odb.rootAssembly.ElementSetFromElementLabels(
            name=region_name_center,
            elementLabels=((instance_name_center, unique_labels_center),)
        )
        
        # Get stress data
        subset_stress_center = stress_field.getSubset(region=region_center, position=INTEGRATION_POINT)
        
        print(f"  Processing {len(subset_stress_center.values)} stress values...")
        # Process each element
        processed_count = 0
        for v in subset_stress_center.values:
            el_label = v.elementLabel
            
            # Use the pre-built map
            if el_label in element_map_center:
                element = element_map_center[el_label]
                
                # Get element centroid
                node_coords = [node_coord_map_center[nid] for nid in element.connectivity]
                x = np.mean([pt[0] for pt in node_coords])
                y = np.mean([pt[1] for pt in node_coords])
                z = np.mean([pt[2] for pt in node_coords])
                
                # Get average U2 for this element's nodes
                u2_values = []
                for nid in element.connectivity:
                    if nid in node_disp_center:
                        u2_values.append(node_disp_center[nid])
                
                if u2_values:  # Only add if we have displacement data
                    coords_center.append((x, y, z))
                    s11_vals_center.append(v.data[0])
                    s22_vals_center.append(v.data[1])
                    s33_vals_center.append(v.data[2])
                    s12_vals_center.append(v.data[3])
                    s13_vals_center.append(v.data[4])
                    s23_vals_center.append(v.data[5])
                    u2_vals_center.append(np.mean(u2_values))
                    element_labels_center.append(el_label)
                    processed_count += 1
                    
                    if processed_count % 500 == 0:
                        print(f"    Processed {processed_count} elements...")
        
        print(f"  Center side: Processed {len(coords_center)} elements with complete data")
        
        # === 4. Convert to numpy arrays ===
        # Right side
        if len(coords_right) > 0:
            coords_array_right = np.array(coords_right)
            if coords_array_right.ndim == 1:
                coords_array_right = coords_array_right.reshape(1, -1)
            x_coords_right = coords_array_right[:, 0]
            y_coords_right = coords_array_right[:, 1]
            z_coords_right = coords_array_right[:, 2]
        else:
            x_coords_right = np.array([])
            y_coords_right = np.array([])
            z_coords_right = np.array([])
        
        s11_right = np.array(s11_vals_right)
        s22_right = np.array(s22_vals_right)
        s33_right = np.array(s33_vals_right)
        s12_right = np.array(s12_vals_right)
        s13_right = np.array(s13_vals_right)
        s23_right = np.array(s23_vals_right)
        u2_right = np.array(u2_vals_right)
        
        # Center side
        if len(coords_center) > 0:
            coords_array_center = np.array(coords_center)
            if coords_array_center.ndim == 1:
                coords_array_center = coords_array_center.reshape(1, -1)
            x_coords_center = coords_array_center[:, 0]
            y_coords_center = coords_array_center[:, 1]
            z_coords_center = coords_array_center[:, 2]
        else:
            x_coords_center = np.array([])
            y_coords_center = np.array([])
            z_coords_center = np.array([])
        
        s11_center = np.array(s11_vals_center)
        s22_center = np.array(s22_vals_center)
        s33_center = np.array(s33_vals_center)
        s12_center = np.array(s12_vals_center)
        s13_center = np.array(s13_vals_center)
        s23_center = np.array(s23_vals_center)
        u2_center = np.array(u2_vals_center)
        
        # Calculate friction coefficient
        with np.errstate(divide='ignore', invalid='ignore'):
            mu_right = np.where(s11_right != 0, -s12_right / s11_right, np.nan)
            mu_center = np.where(s11_center != 0, -s12_center / s11_center, np.nan)
        
        # === 5. Save as NPZ file ===
        output_file = os.path.join(OUTPUT_FOLDER, f'ShearFace-{RUPTURE_POSITION}.npz')
        
        np.savez(output_file,
                 # 保持向後兼容（使用右側數據）
                 x=x_coords_right,
                 y=y_coords_right,
                 z=z_coords_right,
                 s11=s11_right,
                 s22=s22_right,
                 s33=s33_right,
                 s12=s12_right,
                 s13=s13_right,
                 s23=s23_right,
                 mu=mu_right,
                 element_labels=element_labels_right,
                 
                 # Right side detailed data
                 x_right=x_coords_right,
                 y_right=y_coords_right,
                 z_right=z_coords_right,
                 s11_right=s11_right,
                 s22_right=s22_right,
                 s33_right=s33_right,
                 s12_right=s12_right,
                 s13_right=s13_right,
                 s23_right=s23_right,
                 u2_right=u2_right,
                 mu_right=mu_right,
                 element_labels_right=element_labels_right,
                 
                 # Center side detailed data
                 x_center=x_coords_center,
                 y_center=y_coords_center,
                 z_center=z_coords_center,
                 s11_center=s11_center,
                 s22_center=s22_center,
                 s33_center=s33_center,
                 s12_center=s12_center,
                 s13_center=s13_center,
                 s23_center=s23_center,
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
        print(f"  Right side - {len(x_coords_right)} data points")
        if len(u2_right) > 0:
            print(f"    U2 range: [{np.min(u2_right):.6f}, {np.max(u2_right):.6f}] mm")
            print(f"    S12 range: [{np.min(s12_right):.3f}, {np.max(s12_right):.3f}] MPa")
        print(f"  Center side - {len(x_coords_center)} data points")
        if len(u2_center) > 0:
            print(f"    U2 range: [{np.min(u2_center):.6f}, {np.max(u2_center):.6f}] mm")
            print(f"    S12 range: [{np.min(s12_center):.3f}, {np.max(s12_center):.3f}] MPa")
        if len(u2_right) > 0 and len(u2_center) > 0:
            print(f"  Relative displacement (U2): {np.mean(u2_right) - np.mean(u2_center):.6f} mm")
        
        # Close ODB
        odb.close()
        
    except Exception as e:
        print(f"  Error processing {odb_path}: {str(e)}")
        import traceback
        traceback.print_exc()
        continue

print("\nData extraction complete!")
print(f"All files saved in '{OUTPUT_FOLDER}' folder")