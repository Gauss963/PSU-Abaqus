from odbAccess import *
from abaqusConstants import *
import numpy as np
import matplotlib.pyplot as plt
import os

odb_path = '/home/u6431365/Job-s25-f100-stress.odb' 
odb = openOdb(path=odb_path)
step_name = 'shear load'
if step_name not in odb.steps:
    raise KeyError(f"Step '{step_name}' not found in ODB file.")

step = odb.steps[step_name]
frame = step.frames[-1]

stress_field = frame.fieldOutputs['S']
element_ratio = []
element_y_positions = []
element_positions = []
INSTANCE_NAME = 'STATIONARY_BLOCK'
instance = odb.rootAssembly.instances[INSTANCE_NAME]


for element in instance.elements:
    if element.type == 'C3D8': 
        node_labels = element.connectivity  
        element_label = element.label
        node_coords = np.array([instance.nodes[node_label - 1].coordinates for node_label in node_labels])
        avg_coords = np.mean(node_coords, axis=0)

        s33_values = [
            value.data[2] for value in stress_field.values
            if value.elementLabel == element_label and len(value.data) > 2
        ]
        s13_values = [
            value.data[4] for value in stress_field.values
            if value.elementLabel == element_label and len(value.data) > 4
        ]

        if s33_values and s13_values:
            avg_s33 = np.mean(s33_values)
            avg_s13 = np.mean(s13_values)
            if avg_s33 != 0:
                ratio = avg_s13 / avg_s33 
                element_ratio.append(ratio)
                element_y_positions.append(avg_coords[1])
                element_positions.append(avg_coords)

odb.close()

element_y_positions = np.array(element_y_positions) 
element_ratio = np.array(element_ratio)
element_positions = np.array(element_positions)

valid_indices = np.where(
    (element_positions[:, 0] >= 400) & (element_positions[:, 0] <= 700) &  
    (element_y_positions >= 980) & (element_y_positions <= 1280) & 
    (element_ratio >= 0) & (element_ratio <= 1)
)

element_positions = element_positions[valid_indices]
element_y_positions = element_y_positions[valid_indices]
element_ratio = element_ratio[valid_indices]


fig = plt.figure(figsize=(12, 8))
ax = fig.add_subplot(111, projection='3d')

scatter = ax.scatter(
    element_positions[:, 0],      
    element_y_positions,        
    element_ratio, 
    c=element_ratio,
    cmap='viridis',
    s=10,
    marker='o' 
)

cbar = plt.colorbar(scatter, ax=ax, shrink=0.5, aspect=10)
cbar.set_label("S13 / S33 Stress Ratio (μ)")

ax.set_xlabel("Coordinate Position (Average X)")
ax.set_ylabel("Coordinate Position (Average Y)")
ax.set_zlabel("S13 / S33 Stress Ratio (μ)")
ax.set_zlim(0, 1)
plt.title("3D Discrete Plot of S13/S33 Stress Ratio vs Coordinate Positions")


save_path = '/home/u6431365/experiment data/s25-f100-friction.png'
os.makedirs(os.path.dirname(save_path), exist_ok=True)
plt.savefig(save_path, dpi=300, bbox_inches='tight')
plt.close()

