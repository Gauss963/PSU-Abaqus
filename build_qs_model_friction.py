import abaqusConstants as aq
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
import odbAccess


myModel=mdb.Model(name='model_qs', modelType=aq.STANDARD_EXPLICIT)

# GENERATE PARTS ================================================================================

# generate frame
mySketch=myModel.ConstrainedSketch(name='sketch_frame', sheetSize=2.0)
mySketch.rectangle(point1=(0.0, 0.0), point2=(1.308, 0.826))
mySketch.ArcByCenterEnds(center=(0.216, 0.216), direction=COUNTERCLOCKWISE, point1=(0.165, 0.216), point2=(0.216, 0.165))
mySketch.Line(point1=(0.216, 0.165), point2=(1.092, 0.165))
mySketch.ArcByCenterEnds(center=(1.092, 0.216), direction=COUNTERCLOCKWISE, point1=(1.092, 0.165), point2=(1.143, 0.216))
mySketch.Line(point1=(1.143, 0.216), point2=(1.143, 0.610))
mySketch.ArcByCenterEnds(center=(1.092, 0.610), direction=COUNTERCLOCKWISE, point1=(1.143, 0.610), point2=(1.092, 0.660))
mySketch.Line(point1=(1.092, 0.660), point2=(0.216, 0.660))
mySketch.ArcByCenterEnds(center=(0.216, 0.610), direction=COUNTERCLOCKWISE, point1=(0.216, 0.660), point2=(0.165, 0.610))
mySketch.Line(point1=(0.165, 0.610), point2=(0.165, 0.216))
myPart=myModel.Part(name='part_frame', dimensionality=TWO_D_PLANAR, type=DEFORMABLE_BODY)
myPart.BaseShell(sketch=mySketch)
del mySketch

def makeRectanglePart(name, p1, p2):
	mySketch=myModel.ConstrainedSketch(name=name, sheetSize=2.0)
	mySketch.rectangle(point1=p1, point2=p2)
	myPart=myModel.Part(name='part_'+name, dimensionality=TWO_D_PLANAR, type=DEFORMABLE_BODY)
	myPart.BaseShell(sketch=mySketch)
	del mySketch
	return;

makeRectanglePart('sample_e', (0.322, 0.328), (1.084, 0.528))
makeRectanglePart('sample_w', (0.322, 0.178), (1.111, 0.328))
makeRectanglePart('plate_w_1', (0.216, 0.165), (1.092, 0.171))
makeRectanglePart('plate_w_2', (0.235, 0.171), (1.111, 0.178))
makeRectanglePart('plate_s_1', (1.137, 0.216), (1.143, 0.576))
makeRectanglePart('plate_s_2', (1.124, 0.216), (1.137, 0.316))
makeRectanglePart('plate_s_3', (1.111, 0.178), (1.124, 0.328))
makeRectanglePart('plate_e_1', (0.216, 0.654), (1.092, 0.660))
makeRectanglePart('plate_e_2', (0.216, 0.648), (1.092, 0.654))
makeRectanglePart('plate_e_3', (0.216, 0.641), (1.092, 0.648))
makeRectanglePart('plate_e_4', (0.322, 0.528), (1.084, 0.534))
makeRectanglePart('plate_n_1', (0.165, 0.254), (0.171, 0.610))
makeRectanglePart('plate_n_2', (0.171, 0.254), (0.184, 0.508))
makeRectanglePart('plate_n_3', (0.284, 0.328), (0.297, 0.428))
makeRectanglePart('plate_n_4', (0.297, 0.328), (0.310, 0.478))
makeRectanglePart('plate_n_5', (0.310, 0.328), (0.316, 0.503))
makeRectanglePart('plate_n_6', (0.316, 0.328), (0.322, 0.528))

# generate cylinder_e_*
for i in range(4):
	name='cylinder_e_'+str(i + 1)
	x=0.374 + 0.190 * i
	makeRectanglePart(name+'_e', (x, 0.635), (x + 0.076 , 0.641))
	makeRectanglePart(name+'_w', (x, 0.534), (x + 0.076, 0.542))

# generate cylinder_n_*
for i in range(1):
	name='cylinder_n_'+str(i + 1)
	y=0.328
	makeRectanglePart(name+'_n', (0.184, y), (0.190, y + 0.100))
	makeRectanglePart(name+'_s', (0.276, y), (0.284, y + 0.100))


# GENERATE MATERIALS ============================================================================

myModel.Material(name='steel')
myModel.materials['steel'].Elastic(table=((200000000000.0, 0.3), ))

myModel.Material(name='sample')
myModel.materials['sample'].Elastic(table=((3000000000.0, 0.35), ))

myModel.Material(name='soft')
myModel.materials['soft'].Elastic(table=((2000000000.0, 0.3), ))

# GENERATE SECTIONS =============================================================================

myModel.HomogeneousSolidSection(material='steel', name='frame', thickness=0.127)
myModel.HomogeneousSolidSection(material='sample', name='sample', thickness=0.076)
myModel.HomogeneousSolidSection(material='steel', name='plate152', thickness=0.152)
myModel.HomogeneousSolidSection(material='steel', name='plate102', thickness=0.102)
myModel.HomogeneousSolidSection(material='steel', name='plate127', thickness=0.127)
myModel.HomogeneousSolidSection(material='steel', name='plate203', thickness=0.203)
myModel.HomogeneousSolidSection(material='soft', name='soft', thickness=0.127)
myModel.HomogeneousSolidSection(material='steel', name='cylinder_e', thickness=0.1350)
myModel.HomogeneousSolidSection(material='steel', name='cylinder_n', thickness=0.1981)

# ASSIGN SECTIONS ===============================================================================

def assignSection(name, section):
	myPart = myModel.parts['part_' + name]
	mySet = myPart.Set(faces=myPart.faces.getSequenceFromMask(('[#1 ]', ), ), name='set_' + name)
	myPart.SectionAssignment(offset=0.0, offsetField='', offsetType=MIDDLE_SURFACE, region=mySet, sectionName=section, thicknessAssignment=FROM_SECTION)
	return;

assignSection('frame', 'frame')
assignSection('sample_e', 'sample')
assignSection('sample_w', 'sample')
assignSection('plate_w_1', 'plate152')
assignSection('plate_w_2', 'plate102')
assignSection('plate_s_1', 'plate152')
assignSection('plate_s_2', 'plate102')
assignSection('plate_s_3', 'plate102')
assignSection('plate_e_1', 'plate152')
assignSection('plate_e_2', 'soft')
assignSection('plate_e_3', 'plate127')
assignSection('plate_e_4', 'plate102')
assignSection('plate_n_1', 'plate152')
assignSection('plate_n_2', 'plate203')
assignSection('plate_n_3', 'plate102')
assignSection('plate_n_4', 'plate102')
assignSection('plate_n_5', 'plate102')
assignSection('plate_n_6', 'plate102')

for i in range(4):
	assignSection('cylinder_e_'+str(i + 1)+'_e', 'cylinder_e')
	assignSection('cylinder_e_'+str(i + 1)+'_w', 'cylinder_e')

for i in range(1):
	assignSection('cylinder_n_'+str(i + 1)+'_n', 'cylinder_n')
	assignSection('cylinder_n_'+str(i + 1)+'_s', 'cylinder_n')

# ASSEMBLY ======================================================================

for key, value in myModel.parts.items():
	myModel.rootAssembly.Instance(dependent=OFF, name=myModel.parts[key].name, part=value)

# STEPS =========================================================================

myModel.StaticStep(name='Step-1', previous='Initial')
myModel.StaticStep(name='Step-2', previous='Step-1')

# INTERACTION ===================================================================

myAssembly=myModel.rootAssembly
myInstances=myAssembly.instances
mySurfaces=myAssembly.surfaces

# tie

def tie(name, i, j, point, masterPart, slavePart):
	master=myAssembly.Surface(name='surf_'+name+'_'+str(i)+'_'+str(j), side1Edges=
		myInstances['part_'+masterPart].edges.findAt((point,)))
	slave=myAssembly.Surface(name='surf_'+name+'_'+str(j)+'_'+str(i), side1Edges=
		myInstances['part_'+slavePart].edges.findAt((point,)))
	myModel.Tie(adjust=ON, master=master, name='tie_'+name+'_'+str(i)+'_'+str(j), positionToleranceMethod=COMPUTED, slave=slave, thickness=ON, tieRotations=ON)
	return;

def tie2(name, j, i, point, slavePart, masterPart):
	master=myAssembly.Surface(name='surf_'+name+'_'+str(i)+'_'+str(j), side1Edges=
		myInstances['part_'+masterPart].edges.findAt((point,)))
	slave=myAssembly.Surface(name='surf_'+name+'_'+str(j)+'_'+str(i), side1Edges=
		myInstances['part_'+slavePart].edges.findAt((point,)))
	myModel.Tie(adjust=ON, master=master, name='tie_'+name+'_'+str(i)+'_'+str(j), positionToleranceMethod=COMPUTED, slave=slave, thickness=ON, tieRotations=ON)
	return;

tie('n', 0, 1, (0.165, 0.432, 0.0), 'frame', 'plate_n_1')
tie('n', 1, 2, (0.171, 0.381, 0.0), 'plate_n_1', 'plate_n_2')
tie2('n', 3, 4, (0.297, 0.378, 0.0), 'plate_n_3', 'plate_n_4')
tie2('n', 4, 5, (0.310, 0.415, 0.0), 'plate_n_4', 'plate_n_5')
tie2('n', 5, 6, (0.316, 0.428, 0.0), 'plate_n_5', 'plate_n_6')
tie2('n', 6, 's', (0.322, 0.428, 0.0), 'plate_n_6', 'sample_e')

tie('w', 0, 1, (0.654, 0.165, 0.0), 'frame', 'plate_w_1')
tie('w', 1, 2, (0.654, 0.171, 0.0), 'plate_w_1', 'plate_w_2')
tie('w', 2, 's', (0.673, 0.178, 0.0), 'plate_w_2', 'sample_w')

tie2('s', 0, 1, (1.143, 0.396, 0.0), 'frame', 'plate_s_1')
tie2('s', 1, 2, (1.137, 0.266, 0.0), 'plate_s_1', 'plate_s_2')
tie2('s', 2, 3, (1.124, 0.251, 0.0), 'plate_s_2', 'plate_s_3')
tie2('s', 3, 's', (1.111, 0.253, 0.0), 'plate_s_3', 'sample_w')

tie('e', 0, 1, (0.654, 0.660, 0.0), 'frame', 'plate_e_1')
tie('e', 1, 2, (0.654, 0.654, 0.0), 'plate_e_1', 'plate_e_2')
tie('e', 2, 3, (0.654, 0.648, 0.0), 'plate_e_2', 'plate_e_3')
tie2('e', 4, 's', (0.703, 0.528, 0.0), 'plate_e_4', 'sample_e')

for i in range(1):
	name='cylinder_n_'+str(i + 1)
	y=0.378
	tie('n', 2, 'c'+str(i + 1), (0.184, y, 0.0), 'plate_n_2', name+'_n')
	tie('n', 3, 'c'+str(i + 1), (0.284, y, 0.0), 'plate_n_3', name+'_s')

for i in range(4):
	name='cylinder_e_'+str(i + 1)
	x=0.412 + 0.190 * i
	tie('e', 3, 'c'+str(i + 1), (x, 0.641, 0.0), 'plate_e_3', name+'_e')
	tie('e', 4, 'c'+str(i + 1), (x, 0.534, 0.0), 'plate_e_4', name+'_w')

# friction
contact=myModel.ContactProperty('friction_s_s')
contact.TangentialBehavior(
    dependencies=0, directionality=ISOTROPIC, elasticSlipStiffness=None, 
    formulation=PENALTY, fraction=0.005, maximumElasticSlip=FRACTION, 
    pressureDependency=OFF, shearStressLimit=None, slipRateDependency=OFF, 
    table=((0.8, ), ), temperatureDependency=OFF)
contact.NormalBehavior(
    allowSeparation=ON, constraintEnforcementMethod=DEFAULT, 
    pressureOverclosure=HARD)
master = myAssembly.Surface(name='surf_sw_se', side1Edges=
    myInstances['part_sample_w'].edges.findAt(((0.703, 0.328, 0.0),)))
slave = myAssembly.Surface(name='surf_se_sw', side1Edges=
    myInstances['part_sample_e'].edges.findAt(((0.703, 0.328, 0.0),)))

myModel.Tie(adjust=ON, master=master, name='tie_s_s', positionToleranceMethod=COMPUTED, slave=slave, thickness=ON, tieRotations=ON)

myModel.SurfaceToSurfaceContactStd(adjustMethod=NONE, 
    clearanceRegion=None, createStepName='Initial', datumAxis=None, 
    initialClearance=OMIT, interactionProperty='friction_s_s', 
    master=mySurfaces['surf_sw_se'], name='friction_sw_se', 
    slave=mySurfaces['surf_se_sw'], sliding=FINITE, thickness=ON)

# myModel.constraints['tie_w_0_1'].suppress()
# myModel.SurfaceToSurfaceContactStd(adjustMethod=NONE, 
#     clearanceRegion=None, createStepName='Initial', datumAxis=None, 
#     initialClearance=OMIT, interactionProperty='friction_s_s', 
#     master=mySurfaces['surf_w_0_1'], name='friction_w_0_1', 
#     slave=mySurfaces['surf_w_1_0'], sliding=FINITE, thickness=ON)

# myModel.constraints['tie_s_1_0'].suppress()
# myModel.SurfaceToSurfaceContactStd(adjustMethod=NONE, 
#     clearanceRegion=None, createStepName='Initial', datumAxis=None, 
#     initialClearance=OMIT, interactionProperty='friction_s_s', 
#     master=mySurfaces['surf_s_0_1'], name='friction_s_0_1', 
#     slave=mySurfaces['surf_s_1_0'], sliding=FINITE, thickness=ON)

# BC ============================================================================

myAssembly.Set(name='set_bc_1', vertices=
    myInstances['part_frame'].vertices.findAt(((0.0, 0.0, 0.0),)))
myModel.DisplacementBC(amplitude=UNSET, createStepName='Initial'
    , distributionType=UNIFORM, fieldName='', localCsys=None, name='BC-1', 
    region=myAssembly.sets['set_bc_1'], u1=SET, u2=SET, ur3=UNSET)

myAssembly.Set(name='set_bc_2', vertices=
    myInstances['part_frame'].vertices.findAt(((1.308, 0.826, 0.0),)))
myModel.DisplacementBC(amplitude=UNSET, createStepName='Initial'
    , distributionType=UNIFORM, fieldName='', localCsys=None, name='BC-2', 
    region=myAssembly.sets['set_bc_2'], u1=UNSET, u2=SET, ur3=UNSET)

# LOAD ==========================================================================
A_N = 1.0 * 0.01981
A_S = 4.0 * 0.01026
A_sample = 0.762 * 0.076
pressure_N = 7.75e6 * A_sample / A_N
pressure_S = 6.80e6 * A_sample / A_S
    
for i in range(4):
	name='cylinder_e_' + str(i + 1)
	x=0.412 + 0.190 * i
	point_e=(x, 0.635, 0.0)
	point_w=(x, 0.542, 0.0)
	surf=myAssembly.Surface(name='surf_load_'+name+'_e', 
		side1Edges=myInstances['part_'+name+'_e'].edges.findAt((point_e,)))
	myModel.Pressure(amplitude=UNSET, createStepName='Step-1', 
    	distributionType=UNIFORM, field='', magnitude=pressure_N, name='load_'+name+'_e'
    	, region=surf)
	surf=myAssembly.Surface(name='surf_load_'+name+'_w', 
		side1Edges=myInstances['part_'+name+'_w'].edges.findAt((point_w,)))
	myModel.Pressure(amplitude=UNSET, createStepName='Step-1', 
    	distributionType=UNIFORM, field='', magnitude=pressure_N, name='load_'+name+'_w'
    	, region=surf)

for i in range(1):
	name='cylinder_n_'+str(i + 1)
	y=0.378
	point_n=(0.190, y, 0.0)
	point_s=(0.276, y, 0.0)
	surf=myAssembly.Surface(name='surf_load_'+name+'_n', 
		side1Edges=myInstances['part_'+name+'_n'].edges.findAt((point_n,)))
	myModel.Pressure(amplitude=UNSET, createStepName='Step-2', 
    	distributionType=UNIFORM, field='', magnitude=pressure_S, name='load_'+name+'_n'
    	, region=surf)
	surf=myAssembly.Surface(name='surf_load_'+name+'_s', 
		side1Edges=myInstances['part_'+name+'_s'].edges.findAt((point_s,)))
	myModel.Pressure(amplitude=UNSET, createStepName='Step-2', 
    	distributionType=UNIFORM, field='', magnitude=pressure_S, name='load_'+name+'_s'
    	, region=surf)

# MESH ==========================================================================

for key, value in myInstances.items():
	print(key)
	myAssembly.setElementType(elemTypes=(
		ElemType(elemCode=CPS4R, elemLibrary=STANDARD), 
		ElemType(elemCode=CPS3, elemLibrary=STANDARD)), 
		regions=(value.faces.getSequenceFromMask(('[#1 ]', ), ), ))
	myAssembly.seedPartInstance(deviationFactor=0.1, minSizeFactor=0.1, 
		regions=(value, ), size=0.01)
	myAssembly.generateMesh(regions=(value, ))

# JOB ===========================================================================

mdb.Job(atTime=None, contactPrint=aq.OFF, description='', echoPrint=aq.OFF, 
	explicitPrecision=aq.SINGLE, getMemoryFromAnalysis=True, historyPrint=aq.OFF, 
	memory=90, memoryUnits=aq.PERCENTAGE, model='model_qs', modelPrint=aq.OFF, 
	multiprocessingMode=aq.DEFAULT, name='job_qs', nodalOutputPrecision=aq.SINGLE, 
	numCpus=1, queue=None, scratch='', type=aq.ANALYSIS, userSubroutine='', 
	waitHours=0, waitMinutes=0)
# mdb.jobs['Job-1'].submit(consistencyChecking=aq.OFF)
# mdb.jobs['Job-1'].waitForCompletion()

# POSTPROCESS ===================================================================

# odb=session.openOdb(name='Job-1.odb')