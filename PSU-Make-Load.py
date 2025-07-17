# ------ FILE DEBUG BLOCK (toggle by uncommenting) -------------
# import os, sys, datetime
# dbg = open("make_debug.txt", "w", buffering=1)
# def dlog(*msg):
#     dbg.write("[{}] ".format(datetime.datetime.now().isoformat()))
#     dbg.write(" ".join(str(m) for m in msg) + "\n")
#     dbg.flush()
#---------------------------------------------------------------

from abaqus import *
from abaqusConstants import *
from caeModules import *
from regionToolset import *

# ---------------------------------------------------------------
# 0. Global parameters
# ---------------------------------------------------------------
W, H, DEPTH = 100.0, 160.0, 50.0          # side blocks size (X,Y,Z)
CENTER_D = 60.0                           # center block depth (Z)
SPR_W, SPR_H, SPR_D = 40.0, 80.0, 40.0    # spring block size
PL_W, PL_H, PL_D = 90.0, 12.7, 60.0       # steel plate size
CHAMFER = 10.0                            # bevel size on side blocks

# Translation vectors (placement in assembly coordinates)
T_LEFT  = (-100.0, -20.0,   5.0)
T_RIGHT = ( 100.0, -20.0,  55.0)          # after rotation correction
T_SPR   = ( -20.0, 112.7,  10.0)
T_PLT   = ( -45.0,  60.0, -30.0)

MESH_SIZE = 2.0                           # element size (mm)

# ---------------------------------------------------------------
# 1. Model & geometry creation
# ---------------------------------------------------------------
MODEL = mdb.Model(name='Block-Assembly')

# Side block with chamfer 45°
sk_side = MODEL.ConstrainedSketch(name='sk_side', sheetSize=500.0)
poly = [(-W/2, -H/2),
        ( W/2-CHAMFER, -H/2),
        ( W/2, -H/2+CHAMFER),
        ( W/2,  H/2-CHAMFER),
        ( W/2-CHAMFER, H/2),
        (-W/2, H/2)]
for p1, p2 in zip(poly, poly[1:]+poly[:1]):
    sk_side.Line(point1=p1, point2=p2)
side_part = MODEL.Part(name='side_block', dimensionality=THREE_D, type=DEFORMABLE_BODY)
side_part.BaseSolidExtrude(sketch=sk_side, depth=DEPTH)

# Center block
sk_ctr = MODEL.ConstrainedSketch(name='sk_ctr', sheetSize=200.0)
sk_ctr.rectangle(point1=(-PL_W/2, -PL_H/2), point2=(PL_W/2, PL_H/2))
center_part = MODEL.Part(name='center_block', dimensionality=THREE_D, type=DEFORMABLE_BODY)
center_part.BaseSolidExtrude(sketch=sk_ctr, depth=CENTER_D)

# Spring block
sk_spr = MODEL.ConstrainedSketch(name='sk_spr', sheetSize=200.0)
sk_spr.rectangle(point1=(-SPR_W/2, -SPR_H/2), point2=(SPR_W/2, SPR_H/2))
spring_part = MODEL.Part(name='spring', dimensionality=THREE_D, type=DEFORMABLE_BODY)
spring_part.BaseSolidExtrude(sketch=sk_spr, depth=SPR_D)

# Steel plate
sk_plt = MODEL.ConstrainedSketch(name='sk_plt', sheetSize=200.0)
sk_plt.rectangle(point1=(-PL_W/2, -PL_H/2), point2=(PL_W/2, PL_H/2))
plate_part = MODEL.Part(name='steel_plate', dimensionality=THREE_D, type=DEFORMABLE_BODY)
plate_part.BaseSolidExtrude(sketch=sk_plt, depth=PL_D)

# ---------------------------------------------------------------
# 2. Material & Section assignment
# ---------------------------------------------------------------
steel = MODEL.Material(name='Steel')
steel.Elastic(table=((210000.0, 0.3),))
MODEL.HomogeneousSolidSection(name='SteelSection', material='Steel')
for p in (side_part, center_part, spring_part, plate_part):
    p.SectionAssignment(region=(p.cells,), sectionName='SteelSection')

# ---------------------------------------------------------------
# 3. Assembly instances & positioning
# ---------------------------------------------------------------
asm = MODEL.rootAssembly
asm.DatumCsysByDefault(CARTESIAN)

asm.Instance(name='center_block', part=center_part, dependent=OFF)
asm.Instance(name='side_left',    part=side_part,  dependent=OFF)
asm.Instance(name='side_right',   part=side_part,  dependent=OFF)
asm.Instance(name='spring',       part=spring_part,dependent=OFF)
asm.Instance(name='steel_plate',  part=plate_part, dependent=OFF)

asm.translate(instanceList=('side_left',), vector=T_LEFT)
asm.rotate(instanceList=('side_right',), axisPoint=(0,0,0), axisDirection=(0,1,0), angle=180.0)
asm.translate(instanceList=('side_right',), vector=T_RIGHT)
asm.translate(instanceList=('spring',), vector=T_SPR)
asm.translate(instanceList=('steel_plate',), vector=T_PLT)

# Helpful instance handles
SPR_INST  = asm.instances['spring']
PLT_INST  = asm.instances['steel_plate']
CTR_INST  = asm.instances['center_block']
LEFT_INST = asm.instances['side_left']
RIGHT_INST= asm.instances['side_right']

# ---------------------------------------------------------------
# 4. Define surfaces used for Tie constraints
# ---------------------------------------------------------------
# spring-bottom (Z at placement origin)
z_spr_bot = T_SPR[2]
spr_bot_faces = SPR_INST.faces.getByBoundingBox(zMin=z_spr_bot-1e-3, zMax=z_spr_bot+1e-3)
asm.Surface(name='spring-bottom', side1Faces=spr_bot_faces)

# steel plate top & bottom
z_plt_bot = T_PLT[2]
z_plt_top = T_PLT[2] + PL_D
plt_bot_faces = PLT_INST.faces.getByBoundingBox(zMin=z_plt_bot-1e-3, zMax=z_plt_bot+1e-3)
plt_top_faces = PLT_INST.faces.getByBoundingBox(zMin=z_plt_top-1e-3, zMax=z_plt_top+1e-3)
asm.Surface(name='steel_plate-bottom', side1Faces=plt_bot_faces)
asm.Surface(name='steel_plate-Top',    side1Faces=plt_top_faces)

# Center block top (Z = CENTER_D)
ctr_top_faces = CTR_INST.faces.getByBoundingBox(zMin=CENTER_D-1e-3, zMax=CENTER_D+1e-3)
asm.Surface(name='Center-Top', side1Faces=ctr_top_faces)

# ---------------------------------------------------------------
# 5. Tie interactions
# ---------------------------------------------------------------
MODEL.Tie(name='Spring-Steel-Tie',
          main=asm.surfaces['spring-bottom'],
          secondary=asm.surfaces['steel_plate-Top'],
          positionToleranceMethod=COMPUTED, adjust=ON,
          tieRotations=ON, thickness=ON)

MODEL.Tie(name='Steel-Center-Tie',
          main=asm.surfaces['steel_plate-bottom'],
          secondary=asm.surfaces['Center-Top'],
          positionToleranceMethod=COMPUTED, adjust=ON,
          tieRotations=ON, thickness=ON)

# ---------------------------------------------------------------
# 6. Mesh all instances (required before node-based BC)
# ---------------------------------------------------------------
for inst in asm.instances.values():
    asm.seedPartInstance(regions=(inst,), size=MESH_SIZE)
    asm.generateMesh(regions=(inst,))

# ---------------------------------------------------------------
# 7. Boundary conditions
# ---------------------------------------------------------------
# 7.1 Bottom faces of side blocks fixed in Y
# Use vertex.pointOn to avoid AttributeError
left_y_coords  = [v.pointOn[0][1] for v in LEFT_INST.vertices]
right_y_coords = [v.pointOn[0][1] for v in RIGHT_INST.vertices]

y_bot = min(left_y_coords + right_y_coords)
faces_left_bot  = LEFT_INST.faces.getByBoundingBox(yMin=y_bot-1e-3, yMax=y_bot+1e-3)
faces_right_bot = RIGHT_INST.faces.getByBoundingBox(yMin=y_bot-1e-3, yMax=y_bot+1e-3)
asm.Set(name='left_bot',  faces=faces_left_bot)
asm.Set(name='right_bot', faces=faces_right_bot)
MODEL.DisplacementBC('BC_left_bot',  'Initial', asm.sets['left_bot'],  u2=0.0)
MODEL.DisplacementBC('BC_right_bot', 'Initial', asm.sets['right_bot'], u2=0.0)

# 7.2 Symmetry plane of left block (min X) fixed in X
left_x_coords = [v.pointOn[0][0] for v in LEFT_INST.vertices]
x_sym = min(left_x_coords)
faces_left_sym = LEFT_INST.faces.getByBoundingBox(xMin=x_sym-1e-3, xMax=x_sym+1e-3)
asm.Set(name='left_sym', faces=faces_left_sym)
MODEL.DisplacementBC('BC_left_sym', 'Initial', asm.sets['left_sym'], u1=0.0)

# 7.3 Front nodes in Z of side blocks fixed in Z
z_front_L = max([n.coordinates[2] for n in LEFT_INST.nodes])
z_front_R = max([n.coordinates[2] for n in RIGHT_INST.nodes])
front_tol = 0.5
nodes_front_L = LEFT_INST.nodes.getByBoundingBox(zMin=z_front_L-front_tol, zMax=z_front_L+front_tol)
nodes_front_R = RIGHT_INST.nodes.getByBoundingBox(zMin=z_front_R-front_tol, zMax=z_front_R+front_tol)
asm.Set(name='front_nodes_L', nodes=nodes_front_L)
asm.Set(name='front_nodes_R', nodes=nodes_front_R)
MODEL.DisplacementBC('BC_front_L', 'Initial', asm.sets['front_nodes_L'], u3=0.0)
MODEL.DisplacementBC('BC_front_R', 'Initial', asm.sets['front_nodes_R'], u3=0.0)

# ---------------------------------------------------------------
# 8. Analysis steps & a demo load
# ---------------------------------------------------------------
MODEL.StaticStep(name='Normal_Load', previous='Initial', nlgeom=ON)
MODEL.StaticStep(name='Shear_Load', previous='Normal_Load')

# Replace generic Amplitude with explicit TabularAmplitude to avoid keyword errors
MODEL.TabularAmplitude(
    name='Shear_Amplitude',
    timeSpan=STEP,
    smooth=SOLVER_DEFAULT,
    data=((0.0, 0.0), (1.0, 1.0))
)

asm.Surface(name='Surf_shear', side1Faces=plt_top_faces)
MODEL.DisplacementBC(name='shear_disp', createStepName='Shear_Load',
                     region=asm.surfaces['Surf_shear'], u2=0.5,
                     amplitude='Shear_Amplitude')

# ---------------------------------------------------------------
# 9. Job submission helper – write input only
# ---------------------------------------------------------------
if 'Model-1' in mdb.models:
    del mdb.models['Model-1']

job = mdb.Job(name='BlockJob', model='Block-Assembly')
job.writeInput()
