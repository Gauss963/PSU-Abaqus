from odbAccess import openOdb
from abaqusConstants import INTEGRATION_POINT
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
        stress_field = frame.fieldOutputs['S']
        
        # === 2. Get surface elements ===
        surf1 = odb.rootAssembly.surfaces['RIGHT-LEFT-TIE']
        surf2 = odb.rootAssembly.surfaces['RIGHT-LEFT-FRICTION']
        
        # Expand element array
        all_elements = []
        for ea in list(surf1.elements) + list(surf2.elements):
            all_elements.extend(ea)
        
        # Remove duplicates and sort by label
        unique_labels = sorted(set(el.label for el in all_elements))
        instance_name = 'SIDE_RIGHT'
        instance = odb.rootAssembly.instances[instance_name]
        
        # === 3. Prepare node lookup table: nodeLabel -> coordinate ===
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
        
        # === 5. Create region ===
        region_name = 'TEMP_REGION_' + uuid.uuid4().hex[:8]
        region = odb.rootAssembly.ElementSetFromElementLabels(
            name=region_name,
            elementLabels=((instance_name, unique_labels),)
        )
        
        # === 6. Extract stress data ===
        subset = stress_field.getSubset(region=region, position=INTEGRATION_POINT)
        
        # Initialize data lists
        coords = []
        s12_vals = []
        s11_vals = []
        s22_vals = []  # May be used
        s33_vals = []  # May be used
        s13_vals = []  # May be used
        s23_vals = []  # May be used
        element_labels = []
        
        for v in subset.values:
            label = v.elementLabel
            if label in label_to_coord:
                coords.append(label_to_coord[label])
                element_labels.append(label)
                
                # Extract all stress components
                # Abaqus stress tensor order: S11, S22, S33, S12, S13, S23
                s11_vals.append(v.data[0])  # S11
                s22_vals.append(v.data[1])  # S22
                s33_vals.append(v.data[2])  # S33
                s12_vals.append(v.data[3])  # S12
                s13_vals.append(v.data[4])  # S13
                s23_vals.append(v.data[5])  # S23
        
        # === 7. Convert to numpy arrays ===
        coords_array = np.array(coords)
        x_coords = coords_array[:, 0]
        y_coords = coords_array[:, 1]
        z_coords = coords_array[:, 2]
        
        s11 = np.array(s11_vals)
        s22 = np.array(s22_vals)
        s33 = np.array(s33_vals)
        s12 = np.array(s12_vals)
        s13 = np.array(s13_vals)
        s23 = np.array(s23_vals)
        
        # Calculate friction coefficient
        # Avoid division by zero
        with np.errstate(divide='ignore', invalid='ignore'):
            mu = np.where(s11 != 0, -s12 / s11, np.nan)
        
        # === 8. Save as NPZ file ===
        output_file = os.path.join(OUTPUT_FOLDER, f'ShearFace-{RUPTURE_POSITION}.npz')
        
        # Save all relevant data
        np.savez(output_file,
                 # Coordinates
                 x=x_coords,
                 y=y_coords,
                 z=z_coords,
                 # Stress components
                 s11=s11,
                 s22=s22,
                 s33=s33,
                 s12=s12,
                 s13=s13,
                 s23=s23,
                 # Calculated values
                 mu=mu,
                 # Element labels (for tracking if needed)
                 element_labels=element_labels,
                 # Metadata
                 rupture_position=RUPTURE_POSITION,
                 instance_name=instance_name,
                 step_name='Shear_Load',
                 frame_index=-1
                 )
        
        print(f"  Successfully saved data to {output_file}")
        print(f"  Number of data points: {len(x_coords)}")
        print(f"  Y range: [{np.min(y_coords):.3f}, {np.max(y_coords):.3f}]")
        print(f"  Z range: [{np.min(z_coords):.3f}, {np.max(z_coords):.3f}]")
        print(f"  S12 range: [{np.min(s12):.3f}, {np.max(s12):.3f}]")
        
        # Close ODB
        odb.close()
        
    except Exception as e:
        print(f"  Error processing {odb_path}: {str(e)}")
        continue

print("\nData extraction complete!")
print(f"All files saved in '{OUTPUT_FOLDER}' folder")