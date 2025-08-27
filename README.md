# PSU DDS Experiment Abaqus Model

This project defines and generates Abaqus finite element models using Python scripting for simulating fracture behavior analysis in structural assemblies. The model consists of granite blocks, a PMMA spring element, and a steel plate subjected to normal and shear loading conditions at various rupture positions.

## Project Overview

This model simulates direct shear tests in rock mechanics, specifically focusing on how rupture position affects the overall structural strain energy distribution. By varying rupture positions and analyzing strain energy distribution across different components, this research provides insights into structural failure mechanisms.

## Model Features

- **Three granite blocks**: Two side blocks (45° chamfer) and one center block (vertical edge chamfer)
- **PMMA spring element**: Simulates deformation behavior
- **Steel plate**: Provides load transfer
- **Automatic mesh generation**: 0.5 mm seed size
- **Multi-rupture position analysis**: 16 different rupture positions
- **Static analysis steps**: Normal loading followed by shear loading

## Geometry Parameters

| Component    | Dimensions (mm)              | Notes                    |
|--------------|------------------------------|--------------------------|
| Side Block   | 100 (X) × 160 (Y) × 50 (Z) | 45° chamfer on top-right |
| Center Block | 100 (X) × 200 (Y) × 60 (Z) | 5mm chamfer on vertical edges |
| Spring       | 40 (X) × 80 (Y) × 40 (Z)   | PMMA material            |
| Steel Plate  | 90 (X) × 12.7 (Y) × 60 (Z) | Load transfer medium     |

**Chamfer size**: All chamfers are 5 mm

## Material Properties

| Material     | Density (t/mm³) | Young's Modulus (MPa) | Poisson's Ratio |
|--------------|-----------------|----------------------|-----------------|
| **Granite**  | 2.65426e-9      | 30,000               | 0.25            |
| **PMMA**     | -               | 3,000                | 0.35            |
| **Steel**    | -               | 200,000              | 0.30            |

## Loading Conditions

- **Normal Load**: 10 MPa pressure applied to the right face of the right side block
- **Shear Load**: Displacement-controlled loading based on friction resistance calculation
  - Friction coefficient: 0.70
  - Shear displacement amplitude: Calculated from spring stiffness and friction resistance

## Boundary Conditions

- **Bottom constraint**: Both side blocks fixed in Y-direction at bottom faces
- **Left constraint**: Left side block fixed in X-direction at left face  
- **Front constraint**: Both side blocks fixed in Z-direction at front edges

## Rupture Position Parameters

The model analyzes the following 16 rupture positions (in mm):

```Python
[115, 110, 105, 100, 95, 90, 85, 80, 75, 65, 55, 45, 35, 25, 15, 5]
```



Rupture positions are implemented by partitioning the center block and side blocks at Z = RUPTURE_START - RUPTURE_POSITION.

## Analysis Steps

1. **Normal_Load**: Apply normal pressure loading
2. **Shear_Load**: Apply shear displacement loading after normal load

Both steps use nonlinear geometry analysis (`nlgeom=ON`).

## File Structure

```
project/
├── README.md                   # Project documentation
├── PSU-Make-DC.py              # Main model generation script
├── PSU-Run.slurm               # SLURM batch job script
├── read-odb.py                 # Strain energy extraction script
├── read-shear-to-npz.py        # Shear stress data extraction script
└── read-npz.py                 # Data visualization script
```


## Usage Instructions

### 1. Model Generation and Execution

#### Local Execution
```bash
# Generate input files for all rupture positions
abaqus cae noGUI=PSU-Make-DC.py

# Run single analysis (example: rupture position 55mm)
abaqus job=BlockJob-55 cpus=20 mp_mode=mpi interactive
```

#### Using SLURM Batch System
```bash
# Submit batch job (automatically runs all rupture positions)
sbatch PSU-Run.slurm
```

### 2. Post-Processing

#### Extract Strain Energy Data
```bash
# Extract total strain energy for each component
abaqus python read-odb.py

# Extract shear face stress data
abaqus python read-shear-to-npz.py
```

#### Data Visualization
```bash
# Requires Python environment (matplotlib, numpy)
python read-npz.py
```

## Output Files

### Model Files
- `BlockJob-{RUPTURE_POSITION}.inp`: Abaqus input files for each rupture position
- `BlockJob-{RUPTURE_POSITION}.odb`: Analysis result databases

### Post-Processing Results
- `strain-energy-{RUPTURE_POSITION}.npz`: Component strain energy data
- `ShearFace/ShearFace-{RUPTURE_POSITION}.npz`: Shear face stress analysis data
- `Strain-energies.pdf`: Strain energy vs. rupture position relationship plot

## Calculation Parameters

### Friction Resistance Calculation
```
RESISTANCE = 2 × Friction_Coefficient × Depth × Resistance_Area_Length × Normal_Stress
CONTACT_AREA = Spring_Width × Spring_Depth  
RESISTANCE_STRESS = RESISTANCE / CONTACT_AREA
```

### Spring Stiffness and Displacement
```
SPRING_STIFFNESS = PMMA_Young_Modulus × Contact_Area / Spring_Height
SHEAR_AMPLITUDE = RESISTANCE / SPRING_STIFFNESS
```

## Contact and Constraint Settings

### Tie Constraints
- Left side block to center block connection
- Right side block to center block connection
- Spring to steel plate connection
- Steel plate to center block connection

### Friction Contact
- Friction surfaces between center block and side blocks
- Friction coefficient: 0.70
- Hard contact with separation allowed

## Mesh Configuration

- **Element type**: C3D8i (8-node linear brick elements with incompatible modes)
- **Seed size**: 2.0 mm (default)
- **CPU cores**: 20 (parallel computation)

## Output Requests

The model is configured with detailed field output requests:
- **Strain energy**: ENER (total strain energy), ELEN (elastic strain energy), ELEDEN (element deletion energy)
- **Stress**: S (stress tensor), MISES (von Mises stress)
- **Output frequency**: Every increment

## System Requirements

### Software Requirements
- Abaqus 2024
- Python 3.12 (Abaqus Python environment)
- matplotlib, numpy (for post-processing)

### Hardware Requirements
- **Memory**: Recommended 400GB+ (for batch runs)
- **CPU**: Support for 20-core parallel computation
- **Storage**: ~10-50GB per analysis

## Troubleshooting

### Common Issues

1. **Memory Insufficient**
   - Reduce parallel core count
   - Increase mesh size (reduce element count)

2. **Convergence Problems**
   - Check contact settings
   - Adjust increment step sizes

3. **File Path Errors**
   - Ensure all scripts are in the same directory
   - Check path settings in SLURM script

## Contact Information

For technical support, please contact: 

`B09501028@ntu.edu.tw` or `R14521220@ntu.edu.tw`

## Version History

- v1.0: Initial version with multi-rupture position analysis support
- Current version implements complete direct shear test simulation workflow