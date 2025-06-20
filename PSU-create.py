# simplified_model.py  –  create side blocks, center block, spring and steel plate,
# apply BCs, pressures, and two static steps
from abaqus import mdb           # type: ignore
from abaqusConstants import *    # type: ignore

# ---------------------------------------------------------------------------
# 1. Create Model Object
# ---------------------------------------------------------------------------
MODEL = mdb.Model(name='Block-Assembly')

# ---------------------------------------------------------------------------
# 2. Part：Side Block（右側帶 45° 斜角）--------------------------------------
#    100 × 160 mm 截面，向 Z 擠出 50 mm
# ---------------------------------------------------------------------------
side_sketch = MODEL.ConstrainedSketch(name='sk_side', sheetSize=400.0)
W, H = 100.0, 160.0            # 寬、高
side_sketch.rectangle((-W/2, -H/2), ( W/2,  H/2))
# 加 5 mm 斜角
c = 5.0
side_sketch.Line(( W/2-c,  H/2), ( W/2,  H/2-c))
side_sketch.Line(( W/2-c, -H/2), ( W/2, -H/2+c))
# 擠出
side_part = MODEL.Part(name='side_block', dimensionality=THREE_D, type=DEFORMABLE_BODY)
side_part.BaseSolidExtrude(sketch=side_sketch, depth=50.0)

# ---------------------------------------------------------------------------
# 3. Part：Center Block，Chamfer 5 mm ---------------------------------------
#    100 × 200 mm 截面，擠出 60 mm，然後四周 chamfer
# ---------------------------------------------------------------------------
cent_sketch = MODEL.ConstrainedSketch(name='sk_center', sheetSize=400.0)
cent_sketch.rectangle((-50,-100), (50,100))
center_part = MODEL.Part(name='center_block', dimensionality=THREE_D, type=DEFORMABLE_BODY)
center_part.BaseSolidExtrude(sketch=cent_sketch, depth=60.0)
# chamfer 每條豎邊 5 mm
center_part.Chamfer(edgeList=center_part.edges, length=5.0)

# ---------------------------------------------------------------------------
# 4. Part：Spring (PMMA) 40 × 80 mm，擠出 40 mm ----------------------------
spring_sk = MODEL.ConstrainedSketch(name='sk_spring', sheetSize=200.0)
spring_sk.rectangle((0,0), (40,80))
spring_part = MODEL.Part(name='spring', dimensionality=THREE_D, type=DEFORMABLE_BODY)
spring_part.BaseSolidExtrude(sketch=spring_sk, depth=40.0)

# ---------------------------------------------------------------------------
# 5. Part：Steel Plate 90 × 12.7 mm，擠出 60 mm ---------------------------
plate_sk = MODEL.ConstrainedSketch(name='sk_plate', sheetSize=200.0)
plate_sk.rectangle((0,0), (90,12.7))
plate_part = MODEL.Part(name='steel_plate', dimensionality=THREE_D, type=DEFORMABLE_BODY)
plate_part.BaseSolidExtrude(sketch=plate_sk, depth=60.0)

# ---------------------------------------------------------------------------
# 6. Materials & Sections ----------------------------------------------------
mat_granite = MODEL.Material(name='granite')
mat_granite.Density(table=((2.65426e-9,),))
mat_granite.Elastic(table=((30000.0,0.25),))
sec_granite = MODEL.HomogeneousSolidSection(name='granite_sec', material='granite')

mat_pmma = MODEL.Material(name='PMMA')
mat_pmma.Elastic(table=((3000.0,0.35),))
sec_pmma = MODEL.HomogeneousSolidSection(name='pmma_sec', material='PMMA')

mat_steel = MODEL.Material(name='steel')
mat_steel.Elastic(table=((200000.0,0.3),))
sec_steel = MODEL.HomogeneousSolidSection(name='steel_sec', material='steel')

# assign sections
for p in (side_part, center_part):
    region = p.Set(cells=p.cells, name='Set_all')
    p.SectionAssignment(region=region, sectionName='granite_sec')

spring_part.SectionAssignment(region=spring_part.Set(cells=spring_part.cells, name='Set_spring'), sectionName='pmma_sec')
plate_part.SectionAssignment(region=plate_part.Set(cells=plate_part.cells, name='Set_plate'), sectionName='steel_sec')

# ---------------------------------------------------------------------------
# 7. Assembly ---------------------------------------------------------------
asm = MODEL.rootAssembly
asm.DatumCsysByDefault(CARTESIAN)
asm.Instance(name='center_block', part=center_part, dependent=OFF)

# Side blocks：左右各一，右側鏡像
asm.Instance(name='side_left', part=side_part, dependent=OFF)
asm.translate(('side_left',), vector=(-100.0,-20.0,  5.0))

asm.Instance(name='side_right', part=side_part, dependent=OFF)
asm.rotate(('side_right',), axisPoint=(0,0,0), axisDirection=(0,1,0),
           angle=180.0)          # 簡單 180° about Y
asm.translate(('side_right',), vector=( 100.0,-20.0,-45.0))

# Spring & plate
asm.Instance(name='spring', part=spring_part, dependent=OFF)
asm.translate(('spring',), vector=(-20.0,112.7,10.0))

asm.Instance(name='steel_plate', part=plate_part, dependent=OFF)
asm.translate(('steel_plate',), vector=(-45.0,100.0,0.0))

# ---------------------------------------------------------------------------
# 8. Sets & Boundary Conditions ---------------------------------------------
# 8-1 bottom faces of side blocks：Y 固定
for inst, setname in (('side_left','left_bot'),
                      ('side_right','right_bot')):
    f = asm.instances[inst].faces.findAt(((0,-H/2,25.0),))
    asm.Set(name=setname, faces=f)
    MODEL.DisplacementBC(name='BC_'+setname, createStepName='Initial',
                         region=asm.sets[setname], u2=0)

# 8-2 其它支承：x/z 拘束，如原 jnl
left_face   = asm.instances['side_left' ].faces.findAt(((-W/2,  0,25.0),))
front_edges = asm.instances['side_left' ].edges.findAt(((-W/2, 0,50.0),))
right_edges = asm.instances['side_right'].edges.findAt((( W/2, 0,-50.0),))

asm.Set(name='left_face', faces=left_face)
MODEL.DisplacementBC('BC_left_face', 'Initial', asm.sets['left_face'], u1=0)

asm.Set(name='front_edges_L', edges=front_edges)
MODEL.DisplacementBC('BC_front_L', 'Initial', asm.sets['front_edges_L'], u3=0)

asm.Set(name='front_edges_R', edges=right_edges)
MODEL.DisplacementBC('BC_front_R', 'Initial', asm.sets['front_edges_R'], u3=0)

# ---------------------------------------------------------------------------
# 9. Analysis Steps ----------------------------------------------------------
MODEL.StaticStep(name='Normal_Load', previous='Initial', nlgeom=ON)
MODEL.StaticStep(name='Shear_Load',  previous='Normal_Load')

# ---------------------------------------------------------------------------
# 10. Loads (pressures) ------------------------------------------------------
# normal load on right face of left side-block
right_face_L = asm.instances['side_left'].faces.findAt((( W/2, 0,25.0),))
asm.Surface(name='Surf_norm', side1Faces=right_face_L)
MODEL.Pressure('normal_load', 'Normal_Load', asm.surfaces['Surf_norm'],
               magnitude=10.0)

# shear load on top of spring
top_face_spring = asm.instances['spring'].faces.findAt(((20.0,80.0,20.0),))
asm.Surface(name='Surf_shear', side1Faces=top_face_spring)
MODEL.Pressure('shear_load', 'Shear_Load', asm.surfaces['Surf_shear'],
               magnitude=10.0)

# ---------------------------------------------------------------------------
# 11. (Optional) Mesh & Job --------------------------------------------------
# side_part.setElementType(...)
# asm.seedPartInstance(...)
# asm.generateMesh()
job = mdb.Job(name='BlockJob', model='Block-Assembly')
job.writeInput()   # 產生 *.inp；如要直接跑可改 job.submit()