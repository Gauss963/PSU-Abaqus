ffrom odbAccess import *
from abaqusConstants import *
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import os

odb_path = '/home/u6431365/Job-54.odb' 
odb = openOdb(path=odb_path)

step_name = 'shear load'
if step_name not in odb.steps:
    raise KeyError(f"Step '{step_name}' not found in ODB file.")

step = odb.steps[step_name]
frame = step.frames[-1]


stress_field = frame.fieldOutputs['S']
element_s33 = []
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
            if value.elementLabel == element_label and len(value.data) > 4
        ]

        if s33_values:
            avg_s33 = np.mean(s33_values)
            element_s33.append(avg_s33)
            element_y_positions.append(avg_coords[1]) 
            element_positions.append(avg_coords) 
odb.close()


element_y_positions = np.array(element_y_positions)
element_s33 = np.array(element_s33)
element_positions = np.array(element_positions)


x_min, x_max = 400, 700
y_min, y_max = 980, 1280

mask = (
    (element_positions[:, 0] >= x_min) & (element_positions[:, 0] <= x_max) &
    (element_y_positions >= y_min) & (element_y_positions <= y_max)
)

filtered_positions = element_positions[mask]
filtered_y_positions = element_y_positions[mask]
filtered_s33 = element_s33[mask]



fig = plt.figure(figsize=(12, 8))
ax = fig.add_subplot(111, projection='3d')


surf = ax.plot_trisurf(
    filtered_positions[:, 0],  
    filtered_y_positions,     
    filtered_s33, 
    cmap='viridis',
    edgecolor='none'
)


cbar = plt.colorbar(surf, ax=ax, shrink=0.5, aspect=10)
cbar.set_label("S33 Shear Stress")

ax.set_zlim(ax.get_zlim()[::-1])

ax.set_xlabel("Coordinate Position (Average X)")
ax.set_ylabel("Coordinate Position (Average Y)")
ax.set_zlabel("S33 Normal Stress")
plt.title("Filtered 3D Mesh Plot of S33 Normal Stress (Z-axis Reversed)")

save_path = '/home/u6431365/frame/s25-f100-normal.png'
os.makedirs(os.path.dirname(save_path), exist_ok=True)
plt.savefig(save_path, dpi=300, bbox_inches='tight')