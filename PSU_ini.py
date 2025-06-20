# Minimal Abaqus script to create the final geometry and loads

from abaqus import *              # type: ignore
from abaqusConstants import *     # type: ignore
from part import *                # type: ignore
from material import *            # type: ignore
from section import *             # type: ignore
from assembly import *            # type: ignore
from step import *                # type: ignore
from interaction import *         # type: ignore
from load import *                # type: ignore
from mesh import *                # type: ignore
from optimization import *        # type: ignore
from job import *                 # type: ignore
from sketch import *              # type: ignore
from visualization import *       # type: ignore
from connectorBehavior import *   # type: ignore

# Create model
modelName = 'PSU-Model-1'
if mdb.models.has_key(modelName):
    model = mdb.models[modelName]
else:
    model = mdb.Model(name=modelName)

# ----------------------------------------------------------------------
# Create side-block part
# ----------------------------------------------------------------------
model.ConstrainedSketch(name='__profile__', sheetSize=200.0)
model.sketches['__profile__'].rectangle(point1=(-50.0, -80.0), point2=(50.0, 80.0))
model.sketches['__profile__'].Line(point1=(45.0, 80.0), point2=(50.0, 75.0))
model.sketches['__profile__'].Line(point1=(45.0, -80.0), point2=(50.0, -75.0))
model.sketches['__profile__'].autoTrimCurve(curve1=model.sketches['__profile__'].geometry[3], 
                                            point1=(47.6, 80.99))
model.sketches['__profile__'].autoTrimCurve(curve1=model.sketches['__profile__'].geometry[4], 
                                            point1=(50.12, 78.11))
model.sketches['__profile__'].autoTrimCurve(curve1=model.sketches['__profile__'].geometry[5], 
                                            point1=(46.88, -79.86))
model.sketches['__profile__'].autoTrimCurve(curve1=model.sketches['__profile__'].geometry[7], 
                                            point1=(49.75, -78.60))
model.Part(dimensionality=THREE_D, name='side-block', type=DEFORMABLE_BODY)
model.parts['side-block'].BaseSolidExtrude(depth=50.0, 
                                           sketch=model.sketches['__profile__'])
del model.sketches['__profile__']

# ----------------------------------------------------------------------
# Create center-block part
# ----------------------------------------------------------------------
model.ConstrainedSketch(name='__profile__', sheetSize=200.0)
model.sketches['__profile__'].rectangle(point1=(-50.0, -100.0), point2=(50.0, 100.0))
model.Part(dimensionality=THREE_D, name='center-block', type=DEFORMABLE_BODY)
model.parts['center-block'].BaseSolidExtrude(depth=60.0, 
                                             sketch=model.sketches['__profile__'])
del model.sketches['__profile__']

# ----------------------------------------------------------------------
# Create MATERIAL: granite
# ----------------------------------------------------------------------
model.Material(name='granite')
model.materials['granite'].Density(table=((2.65426e-09,),))
model.materials['granite'].Elastic(table=((30000.0, 0.25),))
model.HomogeneousSolidSection(name='granite-homogeneous', material='granite')

# Assign section to blocks
model.parts['center-block'].Set(cells=model.parts['center-block'].cells.getSequenceFromMask(
    ('[#1 ]',),), name='center-block')
model.parts['center-block'].SectionAssignment(region=model.parts['center-block'].sets['center-block'],
                                              sectionName='granite-homogeneous',
                                              offset=0.0, offsetType=MIDDLE_SURFACE)
model.parts['side-block'].Set(cells=model.parts['side-block'].cells.getSequenceFromMask(
    ('[#1 ]',),), name='side-block')
model.parts['side-block'].SectionAssignment(region=model.parts['side-block'].sets['side-block'],
                                            sectionName='granite-homogeneous',
                                            offset=0.0, offsetType=MIDDLE_SURFACE)

# ----------------------------------------------------------------------
# Assemble blocks
# ----------------------------------------------------------------------
model.rootAssembly.DatumCsysByDefault(CARTESIAN)
model.rootAssembly.Instance(dependent=OFF, name='center-block', 
                           part=model.parts['center-block'])
model.rootAssembly.Instance(dependent=OFF, name='side-block-left', 
                           part=model.parts['side-block'])
model.rootAssembly.instances['side-block-left'].translate(vector=(110.0, 0.0, 0.0))
model.rootAssembly.translate(instanceList=('side-block-left',), vector=(-210.0, -20.0, 5.0))
model.rootAssembly.Instance(dependent=OFF, name='side-block-right', 
                           part=model.parts['side-block'])
model.rootAssembly.instances['side-block-right'].translate(vector=(110.0, 0.0, 0.0))
model.rootAssembly.rotate(instanceList=('side-block-right',),
                          axisPoint=(160.0, 75.0, 50.0), 
                          axisDirection=(0.0, -10.0, 0.0), angle=180.0)
model.rootAssembly.translate(instanceList=('side-block-right',),
                             vector=(-110.0, -20.0, -45.0))

# ----------------------------------------------------------------------
# Boundary conditions
# ----------------------------------------------------------------------
# Bottom faces
model.rootAssembly.Set(faces=model.rootAssembly.instances['side-block-left'].faces.getSequenceFromMask(
    ('[#20 ]',), ), name='Set-sideblock-left-bottom')
model.DisplacementBC(name='BC-sideblock-left-bottom', createStepName='Initial',
                     region=model.rootAssembly.sets['Set-sideblock-left-bottom'],
                     u2=SET)

model.rootAssembly.Set(faces=model.rootAssembly.instances['side-block-right'].faces.getSequenceFromMask(
    ('[#20 ]',), ), name='Set-sideblock-right-bottom')
model.DisplacementBC(name='BC-sideblock-right-bottom', createStepName='Initial',
                     region=model.rootAssembly.sets['Set-sideblock-right-bottom'],
                     u2=SET)

# Left face
model.rootAssembly.Set(faces=model.rootAssembly.instances['side-block-left'].faces.getSequenceFromMask(
    ('[#1 ]',), ), name='Set-sideblock-left-left')
model.DisplacementBC(name='BC-sideblock-left-left', createStepName='Initial',
                     region=model.rootAssembly.sets['Set-sideblock-left-left'],
                     u1=SET)

# Front edges
model.rootAssembly.Set(edges=model.rootAssembly.instances['side-block-left'].edges.getSequenceFromMask(
    ('[#1 ]',), ), name='Set-sideblock-left-frontleft')
model.DisplacementBC(name='BC-sideblock-left-frontleft', createStepName='Initial',
                     region=model.rootAssembly.sets['Set-sideblock-left-frontleft'],
                     u3=SET)

model.rootAssembly.Set(edges=model.rootAssembly.instances['side-block-right'].edges.getSequenceFromMask(
    ('[#4 ]',), ), name='Set-sideblock-right-frontright')
model.DisplacementBC(name='BC-sideblock-right-frontright', createStepName='Initial',
                     region=model.rootAssembly.sets['Set-sideblock-right-frontright'],
                     u3=SET)

# ----------------------------------------------------------------------
# Create spring part
# ----------------------------------------------------------------------
model.ConstrainedSketch(name='__profile__', sheetSize=200.0)
model.sketches['__profile__'].rectangle(point1=(0.0, 0.0), point2=(40.0, 80.0))
model.Part(dimensionality=THREE_D, name='spring', type=DEFORMABLE_BODY)
model.parts['spring'].BaseSolidExtrude(depth=40.0, sketch=model.sketches['__profile__'])
del model.sketches['__profile__']

# MATERIAL: PMMA and assignment
model.Material(name='PMMA')
model.materials['PMMA'].Elastic(table=((3000.0, 0.35),))
model.HomogeneousSolidSection(name='PMMA', material='PMMA')
model.parts['spring'].Set(cells=model.parts['spring'].cells.getSequenceFromMask(
    ('[#1 ]',), ), name='Set-spring')
model.parts['spring'].SectionAssignment(region=model.parts['spring'].sets['Set-spring'],
                                        sectionName='PMMA')

# Place spring
model.rootAssembly.Instance(dependent=OFF, name='spring',
                           part=model.parts['spring'])
model.rootAssembly.translate(instanceList=('spring', ), vector=(-40.0, 100.0, 0.0))
model.rootAssembly.translate(instanceList=('spring', ), vector=(-5.0, 0.0, 10.0))
model.rootAssembly.translate(instanceList=('spring', ), vector=(25.0, 0.0, 0.0))
model.rootAssembly.translate(instanceList=('spring', ), vector=(0.0, 12.7, 0.0))

# ----------------------------------------------------------------------
# Create steel-plate part
# ----------------------------------------------------------------------
model.ConstrainedSketch(name='__profile__', sheetSize=200.0)
model.sketches['__profile__'].rectangle(point1=(0.0, 0.0), point2=(90.0, 12.7))
model.Part(dimensionality=THREE_D, name='steel-plate', type=DEFORMABLE_BODY)
model.parts['steel-plate'].BaseSolidExtrude(depth=60.0, sketch=model.sketches['__profile__'])
del model.sketches['__profile__']

# MATERIAL: steel and assignment
model.Material(name='steel')
model.materials['steel'].Elastic(table=((200000.0, 0.3),))
model.HomogeneousSolidSection(name='steel', material='steel')
model.parts['steel-plate'].Set(cells=model.parts['steel-plate'].cells.getSequenceFromMask(
    ('[#1 ]',), ), name='Set-steel-plate')
model.parts['steel-plate'].SectionAssignment(region=model.parts['steel-plate'].sets['Set-steel-plate'],
                                             sectionName='steel')

model.rootAssembly.Instance(dependent=OFF, name='steel-plate',
                           part=model.parts['steel-plate'])
model.rootAssembly.translate(instanceList=('steel-plate', ), vector=(-45.0, 100.0, 0.0))

# ----------------------------------------------------------------------
# Steps
# ----------------------------------------------------------------------
model.StaticStep(name='Normal Load', previous='Initial')
model.StaticStep(name='Shear Load', previous='Normal Load')
model.steps['Normal Load'].setValues(nlgeom=ON)

# ----------------------------------------------------------------------
# Loads
# ----------------------------------------------------------------------
# Normal load
model.rootAssembly.Surface(name='Surf-sideblock-right-right',
                           side1Faces=model.rootAssembly.instances['side-block-left'].faces.getSequenceFromMask(
                               ('[#1 ]',),))
model.Pressure(name='normal-load', createStepName='Normal Load', 
               region=model.rootAssembly.surfaces['Surf-sideblock-right-right'],
               magnitude=10.0)

# Shear load
model.rootAssembly.Surface(name='Surf-spring-top',
                           side1Faces=model.rootAssembly.instances['spring'].faces.getSequenceFromMask(
                               ('[#2 ]',),))
model.Pressure(name='shear-load', createStepName='Shear Load', 
               region=model.rootAssembly.surfaces['Surf-spring-top'],
               magnitude=10.0)

# End of script
