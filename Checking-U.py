from odbAccess import openOdb
from abaqusConstants import INTEGRATION_POINT, NODAL
import numpy as np
import os

# Test with one file first
RUPTURE_POSITION = 115
odb_path = f'./BlockJob-{RUPTURE_POSITION}.odb'
print(f"\nDiagnostic test for {odb_path}...")

odb = openOdb(odb_path)

# Get step and frame
step = odb.steps['Shear_Load']
frame = step.frames[-1]

# Check what field outputs are available
print("\nAvailable field outputs:")
for field_name in frame.fieldOutputs.keys():
    print(f"  - {field_name}")

# Get displacement field
if 'U' in frame.fieldOutputs:
    disp_field = frame.fieldOutputs['U']
    print("\nDisplacement field found")
else:
    print("\nERROR: No displacement field 'U' found!")
    print("Trying to find alternative displacement fields...")
    for field_name in frame.fieldOutputs.keys():
        if 'U' in field_name or 'DISP' in field_name:
            print(f"  Found: {field_name}")

# Test getting displacement for the entire instance first
instance_right = odb.rootAssembly.instances['SIDE_RIGHT']
print(f"\nTesting displacement extraction for SIDE_RIGHT instance:")
print(f"  Number of nodes in instance: {len(instance_right.nodes)}")

# Try to get displacement for the entire instance
try:
    # Create a node set for the entire instance
    all_node_labels = [node.label for node in instance_right.nodes]
    print(f"  First 10 node labels: {all_node_labels[:10]}")
    
    # Get displacement values directly
    disp_values = disp_field.getSubset(region=instance_right)
    print(f"  Number of displacement values: {len(disp_values.values)}")
    
    # Check a few values
    for i, v in enumerate(disp_values.values):
        if i < 5:  # Print first 5 values
            print(f"    Node {v.nodeLabel}: U1={v.data[0]:.6f}, U2={v.data[1]:.6f}, U3={v.data[2]:.6f}")
        else:
            break
            
except Exception as e:
    print(f"  Error getting displacement: {e}")

# Now test for surface elements specifically
print(f"\nTesting surface elements:")
surf1 = odb.rootAssembly.surfaces['RIGHT-LEFT-TIE']
surf2 = odb.rootAssembly.surfaces['RIGHT-LEFT-FRICTION']

# Get surface elements
surface_elements = []
for ea in list(surf1.elements) + list(surf2.elements):
    surface_elements.extend(ea)

print(f"  Number of surface elements: {len(surface_elements)}")

# Get unique element labels
unique_element_labels = sorted(set(el.label for el in surface_elements))
print(f"  Number of unique elements: {len(unique_element_labels)}")

# Find nodes associated with these elements
surface_nodes = set()
for el in surface_elements:
    if hasattr(el, 'connectivity'):
        for node_id in el.connectivity:
            surface_nodes.add(node_id)

print(f"  Number of unique nodes on surface: {len(surface_nodes)}")

# Try to create a region and get displacement
if len(unique_element_labels) > 0:
    region = odb.rootAssembly.ElementSetFromElementLabels(
        name='TEST_REGION',
        elementLabels=(('SIDE_RIGHT', unique_element_labels[:10]),)  # Test with first 10 elements
    )
    
    try:
        disp_subset = disp_field.getSubset(region=region, position=NODAL)
        print(f"  Displacement values for test region: {len(disp_subset.values)}")
        
        for i, v in enumerate(disp_subset.values):
            if i < 3:
                print(f"    Node {v.nodeLabel}: U2={v.data[1]:.6f}")
            else:
                break
    except Exception as e:
        print(f"  Error getting displacement for region: {e}")

odb.close()
print("\nDiagnostic complete.")