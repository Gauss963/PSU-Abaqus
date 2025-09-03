# -*- coding: mbcs -*-
from part import *
from material import *
from section import *
from assembly import *
from step import *
from interaction import *
from load import *
from mesh import *
from optimization import *
from job import *
from sketch import *
from visualization import *
from connectorBehavior import *
mdb.Model(name='Block-Assembly-115')
mdb.models['Block-Assembly-115'].ConstrainedSketch(name='sk_side', sheetSize=
    400.0)
mdb.models['Block-Assembly-115'].sketches['sk_side'].Line(point1=(-50.0, -80.0)
    , point2=(45.0, -80.0))
mdb.models['Block-Assembly-115'].sketches['sk_side'].Line(point1=(45.0, -80.0), 
    point2=(50.0, -75.0))
mdb.models['Block-Assembly-115'].sketches['sk_side'].Line(point1=(50.0, -75.0), 
    point2=(50.0, 75.0))
mdb.models['Block-Assembly-115'].sketches['sk_side'].Line(point1=(50.0, 75.0), 
    point2=(45.0, 80.0))
mdb.models['Block-Assembly-115'].sketches['sk_side'].Line(point1=(45.0, 80.0), 
    point2=(-50.0, 80.0))
mdb.models['Block-Assembly-115'].sketches['sk_side'].Line(point1=(-50.0, 80.0), 
    point2=(-50.0, -80.0))
mdb.models['Block-Assembly-115'].Part(dimensionality=THREE_D, name='side_block'
    , type=DEFORMABLE_BODY)
mdb.models['Block-Assembly-115'].parts['side_block'].BaseSolidExtrude(depth=
    50.0, sketch=mdb.models['Block-Assembly-115'].sketches['sk_side'])
mdb.models['Block-Assembly-115'].ConstrainedSketch(name='sk_center', sheetSize=
    400.0)
mdb.models['Block-Assembly-115'].sketches['sk_center'].rectangle(point1=(-50, 
    -100), point2=(50, 100))
mdb.models['Block-Assembly-115'].Part(dimensionality=THREE_D, name=
    'center_block', type=DEFORMABLE_BODY)
mdb.models['Block-Assembly-115'].parts['center_block'].BaseSolidExtrude(depth=
    60.0, sketch=mdb.models['Block-Assembly-115'].sketches['sk_center'])
mdb.models['Block-Assembly-115'].parts['center_block'].Chamfer(edgeList=(
    mdb.models['Block-Assembly-115'].parts['center_block'].edges[0], 
    mdb.models['Block-Assembly-115'].parts['center_block'].edges[2], 
    mdb.models['Block-Assembly-115'].parts['center_block'].edges[7], 
    mdb.models['Block-Assembly-115'].parts['center_block'].edges[9]), length=
    5.0)
mdb.models['Block-Assembly-115'].parts['center_block'].PartitionCellByPlaneThreePoints(
    cells=
    mdb.models['Block-Assembly-115'].parts['center_block'].cells.getSequenceFromMask(
    ('[#1 ]', ), ), point1=(10.0, -60.0, 0.0), point2=(0.0, -60.0, 0.0), 
    point3=(0.0, -60.0, 10.0))
mdb.models['Block-Assembly-115'].parts['side_block'].PartitionCellByPlaneThreePoints(
    cells=
    mdb.models['Block-Assembly-115'].parts['side_block'].cells.getSequenceFromMask(
    ('[#1 ]', ), ), point1=(10.0, -40.0, 0.0), point2=(0.0, -40.0, 0.0), 
    point3=(0.0, -40.0, 10.0))
mdb.models['Block-Assembly-115'].ConstrainedSketch(name='sk_spring', sheetSize=
    200.0)
mdb.models['Block-Assembly-115'].sketches['sk_spring'].rectangle((0, 0), (40.0, 
    80.0))
mdb.models['Block-Assembly-115'].Part(dimensionality=THREE_D, name='spring', 
    type=DEFORMABLE_BODY)
mdb.models['Block-Assembly-115'].parts['spring'].BaseSolidExtrude(depth=40.0, 
    sketch=mdb.models['Block-Assembly-115'].sketches['sk_spring'])
mdb.models['Block-Assembly-115'].ConstrainedSketch(name='sk_plate', sheetSize=
    200.0)
mdb.models['Block-Assembly-115'].sketches['sk_plate'].rectangle((0, 0), (90.0, 
    12.7))
mdb.models['Block-Assembly-115'].Part(dimensionality=THREE_D, name=
    'steel_plate', type=DEFORMABLE_BODY)
mdb.models['Block-Assembly-115'].parts['steel_plate'].BaseSolidExtrude(depth=
    60.0, sketch=mdb.models['Block-Assembly-115'].sketches['sk_plate'])
mdb.models['Block-Assembly-115'].Material(name='granite')
mdb.models['Block-Assembly-115'].materials['granite'].Density(table=((
    2.65426e-09, ), ))
mdb.models['Block-Assembly-115'].materials['granite'].Elastic(table=((30000.0, 
    0.25), ))
mdb.models['Block-Assembly-115'].HomogeneousSolidSection(material='granite', 
    name='granite_sec')
mdb.models['Block-Assembly-115'].Material(name='PMMA')
mdb.models['Block-Assembly-115'].materials['PMMA'].Elastic(table=((30000.0, 
    0.35), ))
mdb.models['Block-Assembly-115'].HomogeneousSolidSection(material='PMMA', name=
    'pmma_sec')
mdb.models['Block-Assembly-115'].Material(name='steel')
mdb.models['Block-Assembly-115'].materials['steel'].Elastic(table=((200000.0, 
    0.3), ))
mdb.models['Block-Assembly-115'].HomogeneousSolidSection(material='steel', 
    name='steel_sec')
mdb.models['Block-Assembly-115'].parts['side_block'].Set(cells=
    mdb.models['Block-Assembly-115'].parts['side_block'].cells, name='all')
mdb.models['Block-Assembly-115'].parts['side_block'].SectionAssignment(region=
    mdb.models['Block-Assembly-115'].parts['side_block'].sets['all'], 
    sectionName='granite_sec')
mdb.models['Block-Assembly-115'].parts['center_block'].Set(cells=
    mdb.models['Block-Assembly-115'].parts['center_block'].cells, name='all')
mdb.models['Block-Assembly-115'].parts['center_block'].SectionAssignment(
    region=mdb.models['Block-Assembly-115'].parts['center_block'].sets['all'], 
    sectionName='granite_sec')
mdb.models['Block-Assembly-115'].parts['spring'].Set(cells=
    mdb.models['Block-Assembly-115'].parts['spring'].cells, name='spring_set')
mdb.models['Block-Assembly-115'].parts['spring'].SectionAssignment(
    mdb.models['Block-Assembly-115'].parts['spring'].sets['spring_set'], 
    sectionName='pmma_sec')
mdb.models['Block-Assembly-115'].parts['steel_plate'].Set(cells=
    mdb.models['Block-Assembly-115'].parts['steel_plate'].cells, name=
    'plate_set')
mdb.models['Block-Assembly-115'].parts['steel_plate'].SectionAssignment(
    mdb.models['Block-Assembly-115'].parts['steel_plate'].sets['plate_set'], 
    sectionName='steel_sec')
mdb.models['Block-Assembly-115'].rootAssembly.DatumCsysByDefault(CARTESIAN)
mdb.models['Block-Assembly-115'].rootAssembly.Instance(dependent=OFF, name=
    'center_block', part=
    mdb.models['Block-Assembly-115'].parts['center_block'])
mdb.models['Block-Assembly-115'].rootAssembly.Instance(dependent=OFF, name=
    'side_left', part=mdb.models['Block-Assembly-115'].parts['side_block'])
mdb.models['Block-Assembly-115'].rootAssembly.Instance(dependent=OFF, name=
    'side_right', part=mdb.models['Block-Assembly-115'].parts['side_block'])
mdb.models['Block-Assembly-115'].rootAssembly.Instance(dependent=OFF, name=
    'spring', part=mdb.models['Block-Assembly-115'].parts['spring'])
mdb.models['Block-Assembly-115'].rootAssembly.Instance(dependent=OFF, name=
    'steel_plate', part=mdb.models['Block-Assembly-115'].parts['steel_plate'])
mdb.models['Block-Assembly-115'].rootAssembly.translate(instanceList=(
    'side_left', ), vector=(-100.0, -20.0, 5.0))
mdb.models['Block-Assembly-115'].rootAssembly.rotate(angle=180.0, 
    axisDirection=(0, 1, 0), axisPoint=(0, 0, 0), instanceList=('side_right', 
    ))
mdb.models['Block-Assembly-115'].rootAssembly.translate(instanceList=(
    'side_right', ), vector=(100, -20.0, 55.0))
mdb.models['Block-Assembly-115'].rootAssembly.translate(instanceList=('spring', 
    ), vector=(-20.0, 112.7, 10.0))
mdb.models['Block-Assembly-115'].rootAssembly.translate(instanceList=(
    'steel_plate', ), vector=(-45.0, 100.0, 0.0))
mdb.models['Block-Assembly-115'].rootAssembly.Surface(name='Center-Top', 
    side1Faces=
    mdb.models['Block-Assembly-115'].rootAssembly.instances['center_block'].faces.getSequenceFromMask(
    ('[#8000 ]', ), ))
mdb.models['Block-Assembly-115'].rootAssembly.Surface(name='Center-Left-Tie', 
    side1Faces=
    mdb.models['Block-Assembly-115'].rootAssembly.instances['center_block'].faces.getSequenceFromMask(
    ('[#2 ]', ), ))
mdb.models['Block-Assembly-115'].rootAssembly.Surface(name='Center-Right-Tie', 
    side1Faces=
    mdb.models['Block-Assembly-115'].rootAssembly.instances['center_block'].faces.getSequenceFromMask(
    ('[#10000 ]', ), ))
mdb.models['Block-Assembly-115'].rootAssembly.Surface(name=
    'Center-Left-friction', side1Faces=
    mdb.models['Block-Assembly-115'].rootAssembly.instances['center_block'].faces.getSequenceFromMask(
    ('[#2000 ]', ), ))
mdb.models['Block-Assembly-115'].rootAssembly.Surface(name=
    'Center-Right-friction', side1Faces=
    mdb.models['Block-Assembly-115'].rootAssembly.instances['center_block'].faces.getSequenceFromMask(
    ('[#80 ]', ), ))
mdb.models['Block-Assembly-115'].rootAssembly.Surface(name='Left-Right-Tie', 
    side1Faces=
    mdb.models['Block-Assembly-115'].rootAssembly.instances['side_left'].faces.getSequenceFromMask(
    ('[#80 ]', ), ))
mdb.models['Block-Assembly-115'].rootAssembly.Surface(name=
    'Left-Right-friction', side1Faces=
    mdb.models['Block-Assembly-115'].rootAssembly.instances['side_left'].faces.getSequenceFromMask(
    ('[#4 ]', ), ))
mdb.models['Block-Assembly-115'].rootAssembly.Surface(name='Right-Left-Tie', 
    side1Faces=
    mdb.models['Block-Assembly-115'].rootAssembly.instances['side_right'].faces.getSequenceFromMask(
    ('[#80 ]', ), ))
mdb.models['Block-Assembly-115'].rootAssembly.Surface(name=
    'Right-Left-friction', side1Faces=
    mdb.models['Block-Assembly-115'].rootAssembly.instances['side_right'].faces.getSequenceFromMask(
    ('[#4 ]', ), ))
mdb.models['Block-Assembly-115'].rootAssembly.Surface(name='steel_plate-Top', 
    side1Faces=
    mdb.models['Block-Assembly-115'].rootAssembly.instances['steel_plate'].faces.getSequenceFromMask(
    ('[#2 ]', ), ))
mdb.models['Block-Assembly-115'].rootAssembly.Surface(name='steel_plate-bottom'
    , side1Faces=
    mdb.models['Block-Assembly-115'].rootAssembly.instances['steel_plate'].faces.getSequenceFromMask(
    ('[#8 ]', ), ))
mdb.models['Block-Assembly-115'].rootAssembly.Surface(name='spring-bottom', 
    side1Faces=
    mdb.models['Block-Assembly-115'].rootAssembly.instances['spring'].faces.getSequenceFromMask(
    ('[#8 ]', ), ))
mdb.models['Block-Assembly-115'].Tie(adjust=ON, main=
    mdb.models['Block-Assembly-115'].rootAssembly.surfaces['Left-Right-Tie'], 
    name='Left-Tie', positionToleranceMethod=COMPUTED, secondary=
    mdb.models['Block-Assembly-115'].rootAssembly.surfaces['Center-Left-Tie'], 
    thickness=ON, tieRotations=ON)
mdb.models['Block-Assembly-115'].Tie(adjust=ON, main=
    mdb.models['Block-Assembly-115'].rootAssembly.surfaces['Center-Right-Tie'], 
    name='Right-Tie', positionToleranceMethod=COMPUTED, secondary=
    mdb.models['Block-Assembly-115'].rootAssembly.surfaces['Right-Left-Tie'], 
    thickness=ON, tieRotations=ON)
mdb.models['Block-Assembly-115'].Tie(adjust=ON, main=
    mdb.models['Block-Assembly-115'].rootAssembly.surfaces['spring-bottom'], 
    name='Spring-Steel-Tie', positionToleranceMethod=COMPUTED, secondary=
    mdb.models['Block-Assembly-115'].rootAssembly.surfaces['steel_plate-Top'], 
    thickness=ON, tieRotations=ON)
mdb.models['Block-Assembly-115'].Tie(adjust=ON, main=
    mdb.models['Block-Assembly-115'].rootAssembly.surfaces['steel_plate-bottom']
    , name='Steel-Center-Tie', positionToleranceMethod=COMPUTED, secondary=
    mdb.models['Block-Assembly-115'].rootAssembly.surfaces['Center-Top'], 
    thickness=ON, tieRotations=ON)
mdb.models['Block-Assembly-115'].ContactProperty('FrictionArea')
mdb.models['Block-Assembly-115'].interactionProperties['FrictionArea'].TangentialBehavior(
    dependencies=0, directionality=ISOTROPIC, elasticSlipStiffness=None, 
    formulation=PENALTY, fraction=0.005, maximumElasticSlip=FRACTION, 
    pressureDependency=OFF, shearStressLimit=None, slipRateDependency=OFF, 
    table=((0.7, ), ), temperatureDependency=OFF)
mdb.models['Block-Assembly-115'].interactionProperties['FrictionArea'].NormalBehavior(
    allowSeparation=ON, constraintEnforcementMethod=DEFAULT, 
    pressureOverclosure=HARD)
mdb.models['Block-Assembly-115'].SurfaceToSurfaceContactStd(adjustMethod=NONE, 
    clearanceRegion=None, createStepName='Initial', datumAxis=None, 
    initialClearance=OMIT, interactionProperty='FrictionArea', main=
    mdb.models['Block-Assembly-115'].rootAssembly.surfaces['Center-Left-friction']
    , name='FrictionInteraction_Left', secondary=
    mdb.models['Block-Assembly-115'].rootAssembly.surfaces['Left-Right-friction']
    , sliding=FINITE)
mdb.models['Block-Assembly-115'].SurfaceToSurfaceContactStd(adjustMethod=NONE, 
    clearanceRegion=None, createStepName='Initial', datumAxis=None, 
    initialClearance=OMIT, interactionProperty='FrictionArea', main=
    mdb.models['Block-Assembly-115'].rootAssembly.surfaces['Center-Right-friction']
    , name='FrictionInteraction_Right', secondary=
    mdb.models['Block-Assembly-115'].rootAssembly.surfaces['Right-Left-friction']
    , sliding=FINITE)
mdb.models['Block-Assembly-115'].rootAssembly.Set(faces=
    mdb.models['Block-Assembly-115'].rootAssembly.instances['side_left'].faces.getSequenceFromMask(
    mask=('[#200 ]', ), ), name='left_bot')
mdb.models['Block-Assembly-115'].rootAssembly.Set(faces=
    mdb.models['Block-Assembly-115'].rootAssembly.instances['side_right'].faces.getSequenceFromMask(
    mask=('[#200 ]', ), ), name='right_bot')
mdb.models['Block-Assembly-115'].DisplacementBC('BC_left_bot', 'Initial', 
    mdb.models['Block-Assembly-115'].rootAssembly.sets['left_bot'], u2=0.0)
mdb.models['Block-Assembly-115'].DisplacementBC('BC_right_bot', 'Initial', 
    mdb.models['Block-Assembly-115'].rootAssembly.sets['right_bot'], u2=0.0)
mdb.models['Block-Assembly-115'].rootAssembly.Set(faces=
    mdb.models['Block-Assembly-115'].rootAssembly.instances['side_left'].faces.getSequenceFromMask(
    mask=('[#410 ]', ), ), name='left_face')
mdb.models['Block-Assembly-115'].DisplacementBC('BC_left_face', 'Initial', 
    mdb.models['Block-Assembly-115'].rootAssembly.sets['left_face'], u1=0.0)
mdb.models['Block-Assembly-115'].rootAssembly.Set(edges=
    mdb.models['Block-Assembly-115'].rootAssembly.instances['side_left'].edges.getSequenceFromMask(
    mask=('[#20904f1 ]', ), ), name='front_edges_L')
mdb.models['Block-Assembly-115'].rootAssembly.Set(edges=
    mdb.models['Block-Assembly-115'].rootAssembly.instances['side_right'].edges.getSequenceFromMask(
    mask=('[#1a07904 ]', ), ), name='front_edges_R')
mdb.models['Block-Assembly-115'].DisplacementBC('BC_front_L', 'Initial', 
    mdb.models['Block-Assembly-115'].rootAssembly.sets['front_edges_L'], u3=
    0.0)
mdb.models['Block-Assembly-115'].rootAssembly.Set(name='Set-12', vertices=
    mdb.models['Block-Assembly-115'].rootAssembly.instances['side_right'].vertices.getSequenceFromMask(
    ('[#800 ]', ), ))
mdb.models['Block-Assembly-115'].DisplacementBC('BC_front_bot_u3_R', 'Initial', 
    mdb.models['Block-Assembly-115'].rootAssembly.sets['Set-12'], u3=0.0)
mdb.models['Block-Assembly-115'].StaticStep(name='Normal_Load', nlgeom=ON, 
    previous='Initial')
mdb.models['Block-Assembly-115'].StaticStep(name='Shear_Load', nlgeom=ON, 
    previous='Normal_Load')
mdb.models['Block-Assembly-115'].rootAssembly.Surface(name='Surf_norm_right', 
    side1Faces=
    mdb.models['Block-Assembly-115'].rootAssembly.instances['side_right'].faces.getSequenceFromMask(
    mask=('[#410 ]', ), ))
mdb.models['Block-Assembly-115'].Pressure('normal_load', 'Normal_Load', 
    mdb.models['Block-Assembly-115'].rootAssembly.surfaces['Surf_norm_right'], 
    magnitude=10.0)
mdb.models['Block-Assembly-115'].rootAssembly.Surface(name='Surf_shear', 
    side1Faces=
    mdb.models['Block-Assembly-115'].rootAssembly.instances['spring'].faces.getSequenceFromMask(
    mask=('[#2 ]', ), ))
mdb.models['Block-Assembly-115'].rootAssembly.Set(faces=
    mdb.models['Block-Assembly-115'].rootAssembly.instances['spring'].faces.getSequenceFromMask(
    mask=('[#2 ]', ), ), name='Set_shear')
mdb.models['Block-Assembly-115'].DisplacementBC(amplitude=UNSET, 
    createStepName='Shear_Load', distributionType=UNIFORM, fieldName='', fixed=
    OFF, localCsys=None, name='shear_disp', region=
    mdb.models['Block-Assembly-115'].rootAssembly.sets['Set_shear'], u1=UNSET, 
    u2=-0.256666666666667, u3=UNSET, ur1=UNSET, ur2=UNSET, ur3=UNSET)
mdb.models['Block-Assembly-115'].rootAssembly.setElementType(elemTypes=(
    ElemType(elemCode=C3D8I, elemLibrary=STANDARD), ), regions=(
    mdb.models['Block-Assembly-115'].rootAssembly.instances['side_left'].cells, 
    ))
mdb.models['Block-Assembly-115'].rootAssembly.seedPartInstance(regions=(
    mdb.models['Block-Assembly-115'].rootAssembly.instances['side_left'], ), 
    size=2.0)
mdb.models['Block-Assembly-115'].rootAssembly.generateMesh(regions=(
    mdb.models['Block-Assembly-115'].rootAssembly.instances['side_left'], ))
mdb.models['Block-Assembly-115'].rootAssembly.setElementType(elemTypes=(
    ElemType(elemCode=C3D8I, elemLibrary=STANDARD), ), regions=(
    mdb.models['Block-Assembly-115'].rootAssembly.instances['side_right'].cells, 
    ))
mdb.models['Block-Assembly-115'].rootAssembly.seedPartInstance(regions=(
    mdb.models['Block-Assembly-115'].rootAssembly.instances['side_right'], ), 
    size=2.0)
mdb.models['Block-Assembly-115'].rootAssembly.generateMesh(regions=(
    mdb.models['Block-Assembly-115'].rootAssembly.instances['side_right'], ))
mdb.models['Block-Assembly-115'].rootAssembly.setElementType(elemTypes=(
    ElemType(elemCode=C3D8I, elemLibrary=STANDARD), ), regions=(
    mdb.models['Block-Assembly-115'].rootAssembly.instances['spring'].cells, ))
mdb.models['Block-Assembly-115'].rootAssembly.seedPartInstance(regions=(
    mdb.models['Block-Assembly-115'].rootAssembly.instances['spring'], ), size=
    2.0)
mdb.models['Block-Assembly-115'].rootAssembly.generateMesh(regions=(
    mdb.models['Block-Assembly-115'].rootAssembly.instances['spring'], ))
mdb.models['Block-Assembly-115'].rootAssembly.setElementType(elemTypes=(
    ElemType(elemCode=C3D8I, elemLibrary=STANDARD), ), regions=(
    mdb.models['Block-Assembly-115'].rootAssembly.instances['steel_plate'].cells, 
    ))
mdb.models['Block-Assembly-115'].rootAssembly.seedPartInstance(regions=(
    mdb.models['Block-Assembly-115'].rootAssembly.instances['steel_plate'], ), 
    size=2.0)
mdb.models['Block-Assembly-115'].rootAssembly.generateMesh(regions=(
    mdb.models['Block-Assembly-115'].rootAssembly.instances['steel_plate'], ))
mdb.models['Block-Assembly-115'].rootAssembly.setElementType(elemTypes=(
    ElemType(elemCode=C3D8I, elemLibrary=STANDARD), ), regions=(
    mdb.models['Block-Assembly-115'].rootAssembly.instances['center_block'].cells, 
    ))
mdb.models['Block-Assembly-115'].rootAssembly.seedPartInstance(regions=(
    mdb.models['Block-Assembly-115'].rootAssembly.instances['center_block'], ), 
    size=2.0)
mdb.models['Block-Assembly-115'].rootAssembly.generateMesh(regions=(
    mdb.models['Block-Assembly-115'].rootAssembly.instances['center_block'], ))
del mdb.models['Model-1']
mdb.models['Block-Assembly-115'].FieldOutputRequest(createStepName='Shear_Load'
    , frequency=1, name='Spring-Strain-Energy', rebar=EXCLUDE, region=
    mdb.models['Block-Assembly-115'].rootAssembly.allInstances['spring'].sets['spring_set']
    , sectionPoints=DEFAULT, variables=('ENER', 'ELEN', 'ELEDEN'))
mdb.models['Block-Assembly-115'].FieldOutputRequest(createStepName='Shear_Load'
    , frequency=1, name='Center-Block-Strain-Energy', rebar=EXCLUDE, region=
    mdb.models['Block-Assembly-115'].rootAssembly.allInstances['center_block'].sets['all']
    , sectionPoints=DEFAULT, variables=('ENER', 'ELEN', 'ELEDEN'))
mdb.models['Block-Assembly-115'].FieldOutputRequest(createStepName='Shear_Load'
    , frequency=1, name='Side-Block-Left-Strain-Energy', rebar=EXCLUDE, region=
    mdb.models['Block-Assembly-115'].rootAssembly.allInstances['side_left'].sets['all']
    , sectionPoints=DEFAULT, variables=('ENER', 'ELEN', 'ELEDEN'))
mdb.models['Block-Assembly-115'].FieldOutputRequest(createStepName='Shear_Load'
    , frequency=1, name='Side-Block-Right-Strain-Energy', rebar=EXCLUDE, 
    region=
    mdb.models['Block-Assembly-115'].rootAssembly.allInstances['side_right'].sets['all']
    , sectionPoints=DEFAULT, variables=('ENER', 'ELEN', 'ELEDEN'))
mdb.models['Block-Assembly-115'].FieldOutputRequest(createStepName='Shear_Load'
    , frequency=1, name='Steel-Plate-Energy', rebar=EXCLUDE, region=
    mdb.models['Block-Assembly-115'].rootAssembly.allInstances['steel_plate'].sets['plate_set']
    , sectionPoints=DEFAULT, variables=('ENER', 'ELEN', 'ELEDEN'))
mdb.models['Block-Assembly-115'].FieldOutputRequest(createStepName='Shear_Load'
    , name='Side-Block-Left-Stress', rebar=EXCLUDE, region=
    mdb.models['Block-Assembly-115'].rootAssembly.allInstances['side_left'].sets['all']
    , sectionPoints=DEFAULT, variables=('S', 'MISES'))
mdb.Job(model='Block-Assembly-115', name='BlockJob-115', numCpus=20, 
    numDomains=20)
mdb.models['Block-Assembly-115'].UserAmplitude(name='Amp-1', numVariables=3, 
    timeSpan=STEP)
mdb.models['Block-Assembly-115'].rootAssembly.Set(name='Set-13', vertices=
    mdb.models['Block-Assembly-115'].rootAssembly.instances['center_block'].vertices.getSequenceFromMask(
    ('[#80 ]', ), ))
mdb.models['Block-Assembly-115'].ConcentratedForce(amplitude='Amp-1', cf3=-1.0, 
    createStepName='Shear_Load', distributionType=UNIFORM, field='', localCsys=
    None, name='TestLoad', region=
    mdb.models['Block-Assembly-115'].rootAssembly.sets['Set-13'])
# Save by gauss112 on 2025_09_03-13.41.04; build 2024.HF2 2024_03_16-03.54.40 RELr426 191119
