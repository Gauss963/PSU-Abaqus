from abaqus import mdb
from abaqusConstants import *

# ---------------------------------------------------------------------------
# 0. Geometry parameters
# ---------------------------------------------------------------------------
W,  H,  DEPTH   = 100.0, 160.0, 50.0          # side-block  X, Y, Z
CENTER_D        = 60.0                        # center-block extrusion depth
SPR_W, SPR_H, SPR_D = 40.0, 80.0, 40.0        # spring      X, Y, Z
PL_W,  PL_H,  PL_D = 90.0, 12.7, 60.0         # steel plate X, Y, Z
CHAMFER         = 5.0                         # chamfer size (mm)

# placement vectors (assembly coordinates)
T_LEFT  = (-100.0, -20.0,   5.0)
T_RIGHT = (0.0, -20.0, 5.0)
T_SPR   = (-20.0, 112.7,  10.0)
T_PLT   = (-45.0, 100.0,   0.0)

# ---------------------------------------------------------------------------
# 1. Model container
# ---------------------------------------------------------------------------
MODEL = mdb.Model(name='Block-Assembly')

# ---------------------------------------------------------------------------
# 2-1  Side block – 45 bevel in sketch
# ---------------------------------------------------------------------------
sk_side = MODEL.ConstrainedSketch(name='sk_side', sheetSize=400.0)
pts = [(-W/2, -H/2),
       ( W/2-CHAMFER, -H/2),
       ( W/2,        -H/2+CHAMFER),
       ( W/2,         H/2-CHAMFER),
       ( W/2-CHAMFER,  H/2),
       (-W/2,          H/2)]
for i in range(len(pts)):
    sk_side.Line(point1=pts[i], point2=pts[(i+1) % len(pts)])

side_part = MODEL.Part(name='side_block',
                       dimensionality=THREE_D, type=DEFORMABLE_BODY)
side_part.BaseSolidExtrude(sketch=sk_side, depth=DEPTH)

# ---------------------------------------------------------------------------
# 2-2  Center block
# ---------------------------------------------------------------------------
sk_ctr = MODEL.ConstrainedSketch(name='sk_center', sheetSize=400.0)
sk_ctr.rectangle(point1=(-50, -100), point2=(50, 100))
center_part = MODEL.Part(name='center_block',
                         dimensionality=THREE_D, type=DEFORMABLE_BODY)
center_part.BaseSolidExtrude(sketch=sk_ctr, depth=CENTER_D)

def add_chamfer(part, size):
    """Chamfer every vertical edge by <size> mm (Abaqus 2024)."""
    verts = part.vertices
    vertical_edges = []
    for e in part.edges:
        v1, v2 = e.getVertices()
        p1, p2 = verts[v1].pointOn[0], verts[v2].pointOn[0]
        if abs(p1[0]-p2[0]) < 1e-6 and abs(p1[2]-p2[2]) < 1e-6:
            vertical_edges.append(e)

    if not vertical_edges:
        raise RuntimeError("No vertical edges found to chamfer.")

    part.Chamfer(length=size, edgeList=tuple(vertical_edges))

add_chamfer(center_part, CHAMFER)

# ---------------------------------------------------------------------------
# 2-3  Spring & 2-4  Steel plate
# ---------------------------------------------------------------------------
sk_spr = MODEL.ConstrainedSketch(name='sk_spring', sheetSize=200.0)
sk_spr.rectangle((0, 0), (SPR_W, SPR_H))
spring_part = MODEL.Part(name='spring', dimensionality=THREE_D,
                         type=DEFORMABLE_BODY)
spring_part.BaseSolidExtrude(sketch=sk_spr, depth=SPR_D)

sk_plt = MODEL.ConstrainedSketch(name='sk_plate', sheetSize=200.0)
sk_plt.rectangle((0, 0), (PL_W, PL_H))
plate_part = MODEL.Part(name='steel_plate', dimensionality=THREE_D,
                        type=DEFORMABLE_BODY)
plate_part.BaseSolidExtrude(sketch=sk_plt, depth=PL_D)

# ---------------------------------------------------------------------------
# 3. Materials & sections
# ---------------------------------------------------------------------------
mat_gra = MODEL.Material(name='granite')
mat_gra.Density(table=((2.65426e-9,),))
mat_gra.Elastic(table=((30000.0, 0.25),))
MODEL.HomogeneousSolidSection(name='granite_sec', material='granite')

mat_pmma = MODEL.Material(name='PMMA')
mat_pmma.Elastic(table=((3000.0, 0.35),))
MODEL.HomogeneousSolidSection(name='pmma_sec', material='PMMA')

mat_steel = MODEL.Material(name='steel')
mat_steel.Elastic(table=((200000.0, 0.30),))
MODEL.HomogeneousSolidSection(name='steel_sec', material='steel')

for part in (side_part, center_part):
    part.SectionAssignment(region=part.Set(cells=part.cells, name='all'),
                           sectionName='granite_sec')
spring_part.SectionAssignment(spring_part.Set(cells=spring_part.cells,
                                              name='spring_set'),
                              sectionName='pmma_sec')
plate_part.SectionAssignment(plate_part.Set(cells=plate_part.cells,
                                            name='plate_set'),
                             sectionName='steel_sec')

# ---------------------------------------------------------------------------
# 4. Assembly & positioning
# ---------------------------------------------------------------------------
asm = MODEL.rootAssembly
asm.DatumCsysByDefault(CARTESIAN)

asm.Instance(name='center_block', part=center_part,  dependent=OFF)
asm.Instance(name='side_left',    part=side_part,    dependent=OFF)
asm.Instance(name='side_right',   part=side_part,    dependent=OFF)
asm.Instance(name='spring',       part=spring_part,  dependent=OFF)
asm.Instance(name='steel_plate',  part=plate_part,   dependent=OFF)


asm.translate(instanceList=('side_left',), vector=T_LEFT)
asm.rotate(instanceList=('side_right',), axisPoint=(0,0,0), axisDirection=(0,1,0), angle=180.0)
T_RIGHT_CORRECTED = (50 - (-50), -20.0, 55.0)
asm.translate(instanceList=('side_right',), vector=T_RIGHT_CORRECTED)
asm.translate(instanceList=('spring',),      vector=T_SPR)
asm.translate(instanceList=('steel_plate',), vector=T_PLT)


asm.Surface(name='Center-Right', side1Faces=asm.instances['center_block'].faces.getSequenceFromMask(('[#80 ]', ), ))
asm.Surface(name='Center-Left', side1Faces=asm.instances['center_block'].faces.getSequenceFromMask(('[#10 ]', ), ))
asm.Surface(name='Left-Right', side1Faces=asm.instances['side_left'].faces.getSequenceFromMask(('[#4 ]', ), ))
asm.Surface(name='Right-Left', side1Faces=asm.instances['side_right'].faces.getSequenceFromMask(('[#4 ]', ), ))


# ---------------------------------------------------------------------------
# 5. Boundary conditions
# ---------------------------------------------------------------------------
y_bot = -H/2 + T_LEFT[1]
bot_L = asm.instances['side_left'].faces.getByBoundingBox(yMin=y_bot-1e-3, yMax=y_bot+1e-3)
bot_R = asm.instances['side_right'].faces.getByBoundingBox(yMin=y_bot-1e-3, yMax=y_bot+1e-3)
asm.Set(name='left_bot',  faces=bot_L)
asm.Set(name='right_bot', faces=bot_R)
MODEL.DisplacementBC('BC_left_bot',  'Initial', asm.sets['left_bot'],  u2=0.0)
MODEL.DisplacementBC('BC_right_bot', 'Initial', asm.sets['right_bot'], u2=0.0)

x_sym = -W/2 + T_LEFT[0]
inst_left = asm.instances['side_left']
lf = inst_left.faces.getByBoundingBox(xMin=x_sym-1e-3, xMax=x_sym+1e-3)
asm.Set(name='left_face', faces=lf)
MODEL.DisplacementBC('BC_left_face', 'Initial', asm.sets['left_face'], u1=0.0)

z_L = DEPTH + T_LEFT[2]
z_R = DEPTH + T_RIGHT_CORRECTED[2]
edge_L = inst_left.edges.getByBoundingBox(zMin=z_L-1e-3, zMax=z_L+1e-3)
inst_right = asm.instances['side_right']
edge_R = inst_right.edges.getByBoundingBox(zMin=z_R-1e-3, zMax=z_R+1e-3)
asm.Set(name='front_edges_L', edges=edge_L)
asm.Set(name='front_edges_R', edges=edge_R)
MODEL.DisplacementBC('BC_front_L', 'Initial', asm.sets['front_edges_L'], u3=0.0)
MODEL.DisplacementBC('BC_front_R', 'Initial', asm.sets['front_edges_R'], u3=0.0)

# ---------------------------------------------------------------------------
# 6. Analysis steps
# ---------------------------------------------------------------------------
MODEL.StaticStep(name='Normal_Load', previous='Initial', nlgeom=ON)
MODEL.StaticStep(name='Shear_Load',  previous='Normal_Load')



# ---------------------------------------------------------------------------
# 7. Loads
# ---------------------------------------------------------------------------
x_norm_right =  W/2 + T_RIGHT_CORRECTED[0]
face_norm_right = inst_right.faces.getByBoundingBox(xMin=x_norm_right-1e-3, xMax=x_norm_right+1e-3)
asm.Surface(name='Surf_norm_right', side1Faces=face_norm_right)
MODEL.Pressure('normal_load', 'Normal_Load', asm.surfaces['Surf_norm_right'], magnitude=10.0)

y_top_spr = SPR_H + T_SPR[1]
inst_spr = asm.instances['spring']
top_spr = inst_spr.faces.getByBoundingBox(yMin=y_top_spr-1e-3, yMax=y_top_spr+1e-3)
asm.Surface(name='Surf_shear', side1Faces=top_spr)


# MODEL.Pressure('shear_load', 'Shear_Load', asm.surfaces['Surf_shear'], magnitude=10.0) # This is force control.

MODEL.DisplacementBC(
    name='shear_disp',
    createStepName='Shear_Load',
    region=asm.surfaces['Surf_shear'],
    u1=UNSET,
    u2=0.5,
    u3=UNSET,
    ur1=UNSET, ur2=UNSET, ur3=UNSET,
    amplitude='Shear_Amplitude',
    fixed=OFF,
    distributionType=UNIFORM,
    fieldName='',
    localCsys=None
)

# ---------------------------------------------------------------------------
# 8. Meshing
# ---------------------------------------------------------------------------
inst_plt = asm.instances['steel_plate']
ctr_inst = asm.instances['center_block']
for inst in (inst_left, inst_right, inst_spr, inst_plt, ctr_inst):
    asm.seedPartInstance(regions=(inst,), size=2.00)
    asm.generateMesh(regions=(inst,))

del mdb.models['Model-1']

# ---------------------------------------------------------------------------
# 9. Job
# ---------------------------------------------------------------------------
job = mdb.Job(name='BlockJob', model='Block-Assembly')
job.writeInput()