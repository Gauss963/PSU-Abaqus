from odbAccess import openOdb
from abaqusConstants import INTEGRATION_POINT

# RUPTURE_POSITIONS = [105, 100, 95, 90, 85, 80, 75, 65, 55, 45, 35, 25, 15, 5]
RUPTURE_POSITIONS = [105]

for RUPTURE_POSITION in RUPTURE_POSITIONS:
    
    odb_path = f'./BlockJob-{RUPTURE_POSITION}.odb'
    print(f"\nOpening {odb_path}...")
    odb = openOdb(odb_path)
    
    step = odb.steps['Shear_Load']
    frame = step.frames[-1]
    
    """
    Opening ./BlockJob-105.odb...
    - CENTER_BLOCK
    - SIDE_LEFT
    - SIDE_RIGHT
    - SPRING
    - STEEL_PLATE
    (base) [gauss112@intgpn02 2025-07-25-00-08-34]$ 
    """

    # instance = odb.rootAssembly.instances['CENTER_BLOCK']
    # print(odb.rootAssembly.instances.keys())
    # print(odb.rootAssembly.elementSets.keys())
    # print(odb.rootAssembly.surfaces.keys())
    
    stress_field = frame.fieldOutputs['S']
    
    

    surf1_element_arrays = odb.rootAssembly.surfaces['RIGHT-LEFT-TIE'].elements
    surf2_element_arrays = odb.rootAssembly.surfaces['RIGHT-LEFT-FRICTION'].elements

    all_elements = []
    for element_array in surf1_element_arrays + surf2_element_arrays:
        all_elements.extend(element_array)

    unique_labels = sorted(set(el.label for el in all_elements))
    instance_name = 'SIDE_RIGHT'

    region = odb.rootAssembly.ElementSetFromElementLabels(
        name='TEMP_REGION',
        elementLabels=( (instance_name, unique_labels), )
    )

    subset = stress_field.getSubset(region=region, position=INTEGRATION_POINT)

    for v in subset.values:
        print(f"Element {v.elementLabel}: S12 = {v.data[3]:.3f}")

    odb.close()