
# Block-Assembly Abaqus Model

This project defines and generates an Abaqus model using Python scripting, suitable for simulating a structural assembly consisting of granite blocks, a spring element, and a steel plate. The model applies normal and shear loads and sets appropriate boundary conditions.

## Features

- Two side granite blocks (with 45° chamfer)
- Center granite block (with chamfered vertical edges)
- PMMA spring element
- Steel plate
- Automatic meshing with 2 mm seed size
- Static analysis steps for normal and shear loading

## Geometry Parameters

| Component     | Dimensions (mm)                          |
|---------------|------------------------------------------|
| Side Block    | 100 (X) × 160 (Y) × 50 (Z)               |
| Center Block  | 100 (X) × 200 (Y) × 60 (Z)               |
| Spring        | 40 (X) × 80 (Y) × 40 (Z)                 |
| Steel Plate   | 90 (X) × 12.7 (Y) × 60 (Z)               |

Chamfer size: 5 mm on specific edges.

## Materials

- **Granite**: Density = 2.65426e-9 t/mm³, E = 30000 MPa, ν = 0.25
- **PMMA (spring)**: E = 3000 MPa, ν = 0.35
- **Steel (plate)**: E = 200000 MPa, ν = 0.30

## Loads

- Normal load: 10 MPa pressure applied on the right side block's right face.
- Shear load: 10 MPa pressure applied on the top of the spring.

## Boundary Conditions

- Bottom of both side blocks fixed in Y.
- Left side face of the left side block fixed in X.
- Front edges of both side blocks fixed in Z.

## Steps

1. **Normal_Load**: Apply normal pressure load.
2. **Shear_Load**: Apply shear load after normal load.

## How to Run

1. Load the script in Abaqus Python environment.
2. Execute the script.
3. Submit the generated job input file (`BlockJob.inp`) to Abaqus solver.

## Output

- Generates an input file: `BlockJob.inp`
- Contains the entire model definition including geometry, materials, loads, and mesh.

