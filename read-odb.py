from odbAccess import openOdb
import numpy as np

MESH_SIZES = [20, 15, 10, 5]
RUPTURE_POSITIONS = [115, 110, 105, 100, 95, 90, 85, 80, 75, 65, 55, 45, 35, 25, 15, 5]

# for MESH_SIZE in MESH_SIZES:
    

for RUPTURE_POSITION in RUPTURE_POSITIONS:

    # odb_path = f'./BlockJob-{MESH_SIZE}-{RUPTURE_POSITION}.odb'
    odb_path = f'./BlockJob-{RUPTURE_POSITION}.odb'
    print(f"\nOpening {odb_path}...")
    odb = openOdb(odb_path)

    step = odb.steps['Shear_Load']
    frame = step.frames[-1]

    try:
        instances = odb.rootAssembly.instances

        spring_region       = instances['SPRING'].elementSets['SPRING_SET']
        center_block_region = instances['CENTER_BLOCK'].elementSets['ALL']
        left_block_region   = instances['SIDE_LEFT'].elementSets['ALL']
        right_block_region  = instances['SIDE_RIGHT'].elementSets['ALL']
        steel_plate_region  = instances['STEEL_PLATE'].elementSets['PLATE_SET']
    except KeyError as e:
        print(f"[ERROR] Can't find elementSet or instance: {e}")
        odb.close()
        raise

    print("Element counts:")
    print(f"  - Spring:         {len(spring_region.elements)}")
    print(f"  - Center Block:   {len(center_block_region.elements)}")
    print(f"  - Left Block:     {len(left_block_region.elements)}")
    print(f"  - Right Block:    {len(right_block_region.elements)}")
    print(f"  - Steel Plate:    {len(steel_plate_region.elements)}")

    target_vars = ['ELSE']
    energy_data = {}

    print("\n--- Total strain energy values ---")
    for var in target_vars:
        if var in frame.fieldOutputs:
            field = frame.fieldOutputs[var]

            def get_total_energy(subset):
                return sum(v.data for v in subset.values)

            energy_data[f'{var}-Spring']         = get_total_energy(field.getSubset(region=spring_region))
            energy_data[f'{var}-Center-Block']   = get_total_energy(field.getSubset(region=center_block_region))
            energy_data[f'{var}-Left-Block']     = get_total_energy(field.getSubset(region=left_block_region))
            energy_data[f'{var}-Right-Block']    = get_total_energy(field.getSubset(region=right_block_region))
            energy_data[f'{var}-Steel-Plate']    = get_total_energy(field.getSubset(region=steel_plate_region))

            for key, val in energy_data.items():
                print(f"[{key}] Total Energy: {val:.12f}")
        else:
            print(f"[{var}] not found in field outputs.")

    # np.savez(f'strain-energy-{MESH_SIZE}-{RUPTURE_POSITION}.npz', **energy_data)
    np.savez(f'strain-energy-{RUPTURE_POSITION}.npz', **energy_data)
    odb.close()