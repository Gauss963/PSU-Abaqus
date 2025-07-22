from odbAccess import openOdb
import numpy as np

odb = openOdb('BlockJob-75.odb')

step = odb.steps['Shear_Load']
frame = step.frames[-1]

try:
    spring_region = odb.rootAssembly.instances['SPRING'].elementSets['SPRING_SET']
    block_region = odb.rootAssembly.instances['CENTER_BLOCK'].elementSets['ALL']
except KeyError as e:
    print(f"[ERROR] 找不到指定的 elementSet 或 instance: {e}")
    odb.close()
    raise

print(f"Spring region contains {len(spring_region.elements)} elements.")
print(f"Block region contains {len(block_region.elements)} elements.")

available_outputs = list(frame.fieldOutputs.keys())
print("\nAvailable field output variables in 'Normal_Load' last frame:")
for var in available_outputs:
    print(f" - {var}")

target_vars = ['EENER']

energy_data = {}

print("\n--- Total strain energy values ---")
for var in target_vars:
    if var in frame.fieldOutputs:
        field = frame.fieldOutputs[var]
        spring_subset = field.getSubset(region=spring_region)
        block_subset = field.getSubset(region=block_region)

        spring_sum = sum([v.data for v in spring_subset.values])
        block_sum = sum([v.data for v in block_subset.values])

        energy_data[f'{var}_spring'] = spring_sum
        energy_data[f'{var}_block'] = block_sum

        print(f"[{var}] Spring Set Energy: {spring_sum:.12f}")
        print(f"[{var}] Block Set Energy : {block_sum:.12f}")
    else:
        print(f"[{var}] not found in field outputs.")

np.savez('strain_energy_results.npz', **energy_data)

odb.close()