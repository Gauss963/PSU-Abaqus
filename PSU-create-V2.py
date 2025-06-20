from abaqus import mdb         # type: ignore
from abaqusConstants import *  # type: ignore


W, H, DEPTH = 100.0, 160.0, 50.0
CENTER_DEPTH = 60.0
SPR_W, SPR_H, SPR_D = 40.0, 80.0, 40.0    # spring
PL_W,  PL_H,  PL_D = 90.0, 12.7, 60.0     # steel plate
CHAMFER = 5.0


T_LEFT  = (-100.0, -20.0,   5.0)
T_RIGHT = ( 100.0, -20.0, -45.0)
T_SPR   = (-20.0, 112.7,  10.0)
T_PLT   = (-45.0, 100.0,   0.0)

# ---------------------------------------------------------------------------
# 1. Build Model
# ---------------------------------------------------------------------------
MODEL = mdb.Model(name='Block-Assembly')

# ---------------------------------------------------------------------------
# 2-1  Side block
# ---------------------------------------------------------------------------
sk_side = MODEL.ConstrainedSketch(name='sk_side', sheetSize=400.0)
sk_side.rectangle((-W/2, -H/2), (W/2, H/2))
sk_side.Line(( W/2-CHAMFER,  H/2), ( W/2,  H/2-CHAMFER))
sk_side.Line(( W/2-CHAMFER, -H/2), ( W/2, -H/2+CHAMFER))

side_part = MODEL.Part(name='side_block',
                       dimensionality=THREE_D,
                       type=DEFORMABLE_BODY)
side_part.BaseSolidExtrude(sketch=sk_side, depth=DEPTH)

# ---------------------------------------------------------------------------
# 2-2  Center block
# ---------------------------------------------------------------------------
sk_center = MODEL.ConstrainedSketch(name='sk_center', sheetSize=400.0)
sk_center.rectangle((-50, -100), (50, 100))
center_part = MODEL.Part(name='center_block',
                         dimensionality=THREE_D,
                         type=DEFORMABLE_BODY)
center_part.BaseSolidExtrude(sketch=sk_center, depth=CENTER_DEPTH)
center_part.ChamferEdge(edgeList=center_part.edges,
                        lengths=(CHAMFER, CHAMFER))

# ---------------------------------------------------------------------------
# 2-3  Spring  & 2-4  Steel plate
# ---------------------------------------------------------------------------
sk_spr = MODEL.ConstrainedSketch(name='sk_spring', sheetSize=200.0)
sk_spr.rectangle((0, 0), (SPR_W, SPR_H))
spring_part = MODEL.Part(name='spring',
                         dimensionality=THREE_D,
                         type=DEFORMABLE_BODY)
spring_part.BaseSolidExtrude(sketch=sk_spr, depth=SPR_D)

sk_plate = MODEL.ConstrainedSketch(name='sk_plate', sheetSize=200.0)
sk_plate.rectangle((0, 0), (PL_W, PL_H))
plate_part = MODEL.Part(name='steel_plate',
                        dimensionality=THREE_D,
                        type=DEFORMABLE_BODY)
plate_part.BaseSolidExtrude(sketch=sk_plate, depth=PL_D)

# ---------------------------------------------------------------------------
# 3. Material & Section
# ---------------------------------------------------------------------------
mat_gra = MODEL.Material(name='granite')
mat_gra.Density(table=((2.65426e-9,),))
mat_gra.Elastic(table=((30000.0, 0.25),))
MODEL.HomogeneousSolidSection(name='granite_sec', material='granite')

mat_pmma = MODEL.Material(name='PMMA')
mat_pmma.Elastic(table=((3000.0, 0.35),))
MODEL.HomogeneousSolidSection(name='pmma_sec', material='PMMA')

mat_stl = MODEL.Material(name='steel')
mat_stl.Elastic(table=((200000.0, 0.30),))
MODEL.HomogeneousSolidSection(name='steel_sec', material='steel')

for p in (side_part, center_part):
    p.SectionAssignment(region=p.Set(cells=p.cells, name='Set_all'),
                        sectionName='granite_sec')
spring_part.SectionAssignment(region=spring_part.Set(cells=spring_part.cells,
                                                     name='Set_spring'),
                              sectionName='pmma_sec')
plate_part.SectionAssignment(region=plate_part.Set(cells=plate_part.cells,
                                                   name='Set_plate'),
                             sectionName='steel_sec')

# ---------------------------------------------------------------------------
# 4. Assembly
# ---------------------------------------------------------------------------
a = MODEL.rootAssembly
a.DatumCsysByDefault(CARTESIAN)

a.Instance(name='center_block', part=center_part, dependent=OFF)

inst_left  = a.Instance(name='side_left',  part=side_part, dependent=OFF)
a.translate(instanceList=(inst_left,), vector=T_LEFT)

inst_right = a.Instance(name='side_right', part=side_part, dependent=OFF)
a.rotate(instanceList=(inst_right,),
         axisPoint=(0.0, 0.0, 0.0),
         axisDirection=(0.0, 1.0, 0.0),
         angle=180.0)
a.translate(instanceList=(inst_right,), vector=T_RIGHT)

inst_spr = a.Instance(name='spring', part=spring_part, dependent=OFF)
a.translate(instanceList=(inst_spr,), vector=T_SPR)

inst_plate = a.Instance(name='steel_plate', part=plate_part, dependent=OFF)
a.translate(instanceList=(inst_plate,), vector=T_PLT)

# ---------------------------------------------------------------------------
# 5. Boundary Conditions
# ---------------------------------------------------------------------------
y_bot = -H/2 + T_LEFT[1]

bot_L = inst_left.faces.getByBoundingBox(yMin=y_bot-1e-3, yMax=y_bot+1e-3)
bot_R = inst_right.faces.getByBoundingBox(yMin=y_bot-1e-3, yMax=y_bot+1e-3)

a.Set(name='left_bot',  faces=bot_L)
a.Set(name='right_bot', faces=bot_R)

MODEL.DisplacementBC(name='BC_left_bot',  createStepName='Initial',
                     region=a.sets['left_bot'],  u2=0.0)
MODEL.DisplacementBC(name='BC_right_bot', createStepName='Initial',
                     region=a.sets['right_bot'], u2=0.0)



x_left_face = -W/2 + T_LEFT[0]
lf = inst_left.faces.getByBoundingBox(xMin=x_left_face-1e-3,
                                      xMax=x_left_face+1e-3)
a.Set(name='left_face', faces=lf)
MODEL.DisplacementBC('BC_left_face', 'Initial', a.sets['left_face'], u1=0.0)

# Front edges
z_front_L = DEPTH + T_LEFT[2]
z_front_R = -DEPTH + T_RIGHT[2]

edge_front_L = inst_left.edges.getByBoundingBox(zMin=z_front_L-1e-3,
                                                zMax=z_front_L+1e-3)
edge_front_R = inst_right.edges.getByBoundingBox(zMin=z_front_R-1e-3,
                                                 zMax=z_front_R+1e-3)

a.Set(name='front_edges_L', edges=edge_front_L)
a.Set(name='front_edges_R', edges=edge_front_R)

MODEL.DisplacementBC('BC_front_L', 'Initial',
                     a.sets['front_edges_L'], u3=0.0)
MODEL.DisplacementBC('BC_front_R', 'Initial',
                     a.sets['front_edges_R'], u3=0.0)

# ---------------------------------------------------------------------------
# 6. Analysis Steps
# ---------------------------------------------------------------------------
MODEL.StaticStep(name='Normal_Load', previous='Initial', nlgeom=ON)
MODEL.StaticStep(name='Shear_Load',  previous='Normal_Load')


# ---------------------------------------------------------------------------
# 7. Loads
# ---------------------------------------------------------------------------
x_norm = W/2 + T_LEFT[0]
norm_face = inst_left.faces.getByBoundingBox(xMin=x_norm-1e-3,
                                             xMax=x_norm+1e-3)
a.Surface(name='Surf_norm', side1Faces=norm_face)

MODEL.Pressure('normal_load', 'Normal_Load',
               a.surfaces['Surf_norm'], magnitude=10.0)

# Shear load -> spring
y_top_spr = SPR_H + T_SPR[1]
top_spr = inst_spr.faces.getByBoundingBox(yMin=y_top_spr-1e-3,
                                          yMax=y_top_spr+1e-3)
a.Surface(name='Surf_shear', side1Faces=top_spr)

MODEL.Pressure('shear_load', 'Shear_Load',
               a.surfaces['Surf_shear'], magnitude=10.0)

# ---------------------------------------------------------------------------
# 8. Mesh (size == 5.0)
# ---------------------------------------------------------------------------
for inst in (inst_left, inst_right, inst_spr, inst_plate):
    a.seedPartInstance(regions=(inst,), size=5.00)
    a.generateMesh(regions=(inst,))

# ---------------------------------------------------------------------------
# 9. Job
# ---------------------------------------------------------------------------
job = mdb.Job(name='BlockJob', model='Block-Assembly')
job.writeInput()