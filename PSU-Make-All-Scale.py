from driverUtils import executeOnCaeStartup
executeOnCaeStartup()
from caeModules import *
from abaqus import mdb, session
from abaqusConstants import *


from part import *
from material import *
from section import *
from assembly import *
from step import *
from interaction import *
from load import *
from mesh import *
from mesh import ElemType
from optimization import *
from job import *
from sketch import *
from visualization import *
from connectorBehavior import *

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

def spring_translation_centered_on_plate(T_PLT_s, PL_W_s, PL_H_s, PL_D_s, SPR_W, SPR_H, SPR_D):
    return (
        T_PLT_s[0] + (PL_W_s - SPR_W) * 0.5,
        T_PLT_s[1] + PL_H_s,
        T_PLT_s[2] + (PL_D_s - SPR_D) * 0.5
    )

def build_model(RUPTURE_POSITION, scale_factor=1.0):
    # ---------------------------------------------------------------------------
    # 0. Parameters (base, unscaled)
    # ---------------------------------------------------------------------------
    model_name = f'Block-Assembly-{int(RUPTURE_POSITION)}'
    job_name   = f'BlockJob-{int(RUPTURE_POSITION)}'

    # --- geometry (base) ---
    W,  H,  DEPTH   = 100.0, 160.0, 50.0       # side-block  X, Y, Z
    CENTER_D        = 60.0                     # center-block extrusion depth
    SPR_W, SPR_H, SPR_D = 40.0, 80.0, 40.0     # spring      X, Y, Z  (NOT scaled)
    PL_W,  PL_H,  PL_D = 90.0, 12.7, 60.0      # steel plate X, Y, Z
    CHAMFER         = 5.0                      # chamfer size (mm)

    # --- placements (base) ---
    T_LEFT  = (-100.0, -20.0,  5.0)
    T_RIGHT = (0.0,    -20.0,  5.0)
    T_SPR   = (-20.0,  112.7, 10.0)
    T_PLT   = (-45.0,  100.0,  0.0)

    # --- simulation (base) ---
    FRICTION_COEFFICIENT = 0.70
    NORMAL_STRESS = 10.0     # MPa
    Y_PMMA = 3000.0          # MPa
    MESH_SIZE = 2.00
    RUPTURE_START = 55.00
    RESISTANCE_AREA_LENGTH = 220.0  # mm, length of the resistance area

    # ---------------------------------------------------------------------------
    # 0.1 Helpers: scale everything except spring dimensions
    # ---------------------------------------------------------------------------
    s = float(scale_factor)

    def S(v):  # scale a 3-tuple
        return (s*v[0], s*v[1], s*v[2])

    # scaled geometry (non-spring)
    W_s, H_s, DEPTH_s   = s*W, s*H, s*DEPTH
    CENTER_D_s          = s*CENTER_D
    PL_W_s, PL_H_s, PL_D_s = s*PL_W, s*PL_H, s*PL_D
    CHAMFER_s           = s*CHAMFER

    # spring geometry: NOT scaled
    SPR_W_s, SPR_H_s, SPR_D_s = SPR_W, SPR_H, SPR_D

    # placements: all translated positions scale so相對位置維持
    T_LEFT_s  = S(T_LEFT)
    T_RIGHT_s = S(T_RIGHT)
    # 原碼的右塊採用 rotate+translate，實際使用的是 T_RIGHT_CORRECTED
    T_RIGHT_CORRECTED_base = (50 - (-50), -20.0, 55.0)  # = (100, -20, 55)
    T_RIGHT_CORRECTED_s = S(T_RIGHT_CORRECTED_base)
    T_PLT_s   = S(T_PLT)

    T_SPR_s = spring_translation_centered_on_plate(
        T_PLT_s, PL_W_s, PL_H_s, PL_D_s,
        SPR_W, SPR_H, SPR_D
    )

    # mesh size: non-spring scaled, spring unchanged
    # MESH_SIZE_body = MESH_SIZE * s
    # MESH_SIZE_spring = MESH_SIZE

    # rupture plane y coordinate (both constants and positions scaled)
    y_rupture = s*(RUPTURE_START - RUPTURE_POSITION)
    y_rupture_side = s*(RUPTURE_START - RUPTURE_POSITION + 20.0)

    # shear amplitude: 接觸抗力隨面積 ~ s^2 放大（DEPTH、長度都放大），彈簧剛度不變 → 位移放大 ~ s^2
    CONTACT_AREA = SPR_W_s * SPR_D_s                        # mm^2 (unchanged)
    SPRING_STIFFNESS = Y_PMMA * CONTACT_AREA / SPR_H_s      # N/mm (unchanged)
    RESISTANCE = 2 * FRICTION_COEFFICIENT * DEPTH_s * (s*RESISTANCE_AREA_LENGTH) * NORMAL_STRESS  # N
    SHEAR_AMPLITUDE = RESISTANCE / SPRING_STIFFNESS         # mm

    # ---------------------------------------------------------------------------
    # 1. Model container
    # ---------------------------------------------------------------------------
    MODEL = mdb.Model(name=model_name)

    # ---------------------------------------------------------------------------
    # 2-1  Side block with 45° bevel in sketch (scaled)
    # ---------------------------------------------------------------------------
    sk_side = MODEL.ConstrainedSketch(name='sk_side', sheetSize=400.0*s)
    pts = [(-W_s/2, -H_s/2),
           ( W_s/2-CHAMFER_s, -H_s/2),
           ( W_s/2,        -H_s/2+CHAMFER_s),
           ( W_s/2,         H_s/2-CHAMFER_s),
           ( W_s/2-CHAMFER_s,  H_s/2),
           (-W_s/2,           H_s/2)]
    for i in range(len(pts)):
        sk_side.Line(point1=pts[i], point2=pts[(i+1) % len(pts)])
    side_part = MODEL.Part(name='side_block', dimensionality=THREE_D, type=DEFORMABLE_BODY)
    side_part.BaseSolidExtrude(sketch=sk_side, depth=DEPTH_s)

    # ---------------------------------------------------------------------------
    # 2-2  Center block (scaled) + chamfer
    # ---------------------------------------------------------------------------
    sk_ctr = MODEL.ConstrainedSketch(name='sk_center', sheetSize=400.0*s)
    sk_ctr.rectangle(point1=(-50.0*s, -100.0*s), point2=(50.0*s, 100.0*s))
    center_part = MODEL.Part(name='center_block', dimensionality=THREE_D, type=DEFORMABLE_BODY)
    center_part.BaseSolidExtrude(sketch=sk_ctr, depth=CENTER_D_s)
    add_chamfer(center_part, CHAMFER_s)

    # Partition center_block with XY plane at scaled y = y_rupture
    cell = center_part.cells.getSequenceFromMask(('[#1 ]', ), )
    center_part.PartitionCellByPlaneThreePoints(
        cells=cell,
        point1=(10.0*s, y_rupture, 0.0),
        point2=(0.0,    y_rupture, 0.0),
        point3=(0.0,    y_rupture, 10.0*s)
    )

    # Partition side_block with XY plane at scaled y = y_rupture_side
    side_cell = side_part.cells.getSequenceFromMask(('[#1 ]', ), )
    side_part.PartitionCellByPlaneThreePoints(
        cells=side_cell,
        point1=(10.0*s, y_rupture_side, 0.0),
        point2=(0.0,    y_rupture_side, 0.0),
        point3=(0.0,    y_rupture_side, 10.0*s)
    )

    # ---------------------------------------------------------------------------
    # 2-3  Spring (NOT scaled) & 2-4  Steel plate (scaled)
    # ---------------------------------------------------------------------------
    sk_spr = MODEL.ConstrainedSketch(name='sk_spring', sheetSize=200.0)
    sk_spr.rectangle((0.0, 0.0), (SPR_W_s, SPR_H_s))
    spring_part = MODEL.Part(name='spring', dimensionality=THREE_D, type=DEFORMABLE_BODY)
    spring_part.BaseSolidExtrude(sketch=sk_spr, depth=SPR_D_s)

    sk_plt = MODEL.ConstrainedSketch(name='sk_plate', sheetSize=200.0*s)
    sk_plt.rectangle((0.0, 0.0), (PL_W_s, PL_H_s))
    plate_part = MODEL.Part(name='steel_plate', dimensionality=THREE_D, type=DEFORMABLE_BODY)
    plate_part.BaseSolidExtrude(sketch=sk_plt, depth=PL_D_s)

    # ---------------------------------------------------------------------------
    # 3. Materials & sections (unchanged properties)
    # ---------------------------------------------------------------------------
    mat_gra = MODEL.Material(name='granite')
    mat_gra.Density(table=((2.65426e-9,),))
    mat_gra.Elastic(table=((30000.0, 0.25),))
    MODEL.HomogeneousSolidSection(name='granite_sec', material='granite')

    mat_pmma = MODEL.Material(name='PMMA')
    mat_pmma.Elastic(table=((Y_PMMA, 0.35),))
    MODEL.HomogeneousSolidSection(name='pmma_sec', material='PMMA')

    mat_steel = MODEL.Material(name='steel')
    mat_steel.Elastic(table=((200000.0, 0.30),))
    MODEL.HomogeneousSolidSection(name='steel_sec', material='steel')

    for part in (side_part, center_part):
        part.SectionAssignment(region=part.Set(cells=part.cells, name='all'), sectionName='granite_sec')
    spring_part.SectionAssignment(spring_part.Set(cells=spring_part.cells, name='spring_set'), sectionName='pmma_sec')
    plate_part.SectionAssignment(plate_part.Set(cells=plate_part.cells, name='plate_set'), sectionName='steel_sec')

    # ---------------------------------------------------------------------------
    # 4. Assembly & positioning (scaled translations; rotate same)
    # ---------------------------------------------------------------------------
    asm = MODEL.rootAssembly
    asm.DatumCsysByDefault(CARTESIAN)

    asm.Instance(name='center_block', part=center_part,  dependent=OFF)
    asm.Instance(name='side_left',    part=side_part,    dependent=OFF)
    asm.Instance(name='side_right',   part=side_part,    dependent=OFF)
    asm.Instance(name='spring',       part=spring_part,  dependent=OFF)
    asm.Instance(name='steel_plate',  part=plate_part,   dependent=OFF)

    asm.translate(instanceList=('side_left',), vector=T_LEFT_s)
    asm.rotate(instanceList=('side_right',), axisPoint=(0,0,0), axisDirection=(0,1,0), angle=180.0)
    asm.translate(instanceList=('side_right',), vector=T_RIGHT_CORRECTED_s)
    asm.translate(instanceList=('spring',),      vector=T_SPR_s)
    asm.translate(instanceList=('steel_plate',), vector=T_PLT_s)

    # Surfaces (masks不受縮放影響)
    asm.Surface(name='Center-Top',  side1Faces=asm.instances['center_block'].faces.getSequenceFromMask(('[#8000 ]', ), ))
    asm.Surface(name='Center-Left-Tie',  side1Faces=asm.instances['center_block'].faces.getSequenceFromMask(('[#2 ]', ), ))
    asm.Surface(name='Center-Right-Tie', side1Faces=asm.instances['center_block'].faces.getSequenceFromMask(('[#10000 ]', ), ))
    asm.Surface(name='Center-Left-friction',  side1Faces=asm.instances['center_block'].faces.getSequenceFromMask(('[#2000 ]', ), ))
    asm.Surface(name='Center-Right-friction', side1Faces=asm.instances['center_block'].faces.getSequenceFromMask(('[#80 ]', ), ))
    asm.Surface(name='Left-Right-Tie',   side1Faces=asm.instances['side_left'].faces.getSequenceFromMask(('[#80 ]', ), ))
    asm.Surface(name='Left-Right-friction',   side1Faces=asm.instances['side_left'].faces.getSequenceFromMask(('[#4 ]', ), ))
    asm.Surface(name='Right-Left-Tie',   side1Faces=asm.instances['side_right'].faces.getSequenceFromMask(('[#80 ]', ), ))
    asm.Surface(name='Right-Left-friction',   side1Faces=asm.instances['side_right'].faces.getSequenceFromMask(('[#4 ]', ), ))
    asm.Surface(name='steel_plate-Top',  side1Faces=asm.instances['steel_plate'].faces.getSequenceFromMask(('[#2 ]', ), ))
    asm.Surface(name='steel_plate-bottom', side1Faces=asm.instances['steel_plate'].faces.getSequenceFromMask(('[#8 ]', ), ))
    asm.Surface(name='spring-bottom', side1Faces=asm.instances['spring'].faces.getSequenceFromMask(('[#8 ]', ), ))

    MODEL.Tie(name='Left-Tie',  main=asm.surfaces['Left-Right-Tie'],  secondary=asm.surfaces['Center-Left-Tie'],  positionToleranceMethod=COMPUTED, adjust=ON, tieRotations=ON, thickness=ON)
    MODEL.Tie(name='Right-Tie', main=asm.surfaces['Center-Right-Tie'], secondary=asm.surfaces['Right-Left-Tie'], positionToleranceMethod=COMPUTED, adjust=ON, tieRotations=ON, thickness=ON)
    MODEL.Tie(name='Spring-Steel-Tie', main=asm.surfaces['spring-bottom'], secondary=asm.surfaces['steel_plate-Top'], positionToleranceMethod=COMPUTED, adjust=ON, tieRotations=ON, thickness=ON)
    MODEL.Tie(name='Steel-Center-Tie', main=asm.surfaces['steel_plate-bottom'], secondary=asm.surfaces['Center-Top'], positionToleranceMethod=COMPUTED, adjust=ON, tieRotations=ON, thickness=ON)

    MODEL.ContactProperty('FrictionArea')
    MODEL.interactionProperties['FrictionArea'].TangentialBehavior(
        dependencies=0, directionality=ISOTROPIC, elasticSlipStiffness=None,
        formulation=PENALTY, fraction=0.005, maximumElasticSlip=FRACTION,
        pressureDependency=OFF, shearStressLimit=None, slipRateDependency=OFF,
        table=((FRICTION_COEFFICIENT,),), temperatureDependency=OFF
    )
    MODEL.interactionProperties['FrictionArea'].NormalBehavior(allowSeparation=ON, constraintEnforcementMethod=DEFAULT, pressureOverclosure=HARD)

    MODEL.SurfaceToSurfaceContactStd(name='FrictionInteraction_Left',  createStepName='Initial',
        main=asm.surfaces['Center-Left-friction'],  secondary=asm.surfaces['Left-Right-friction'],
        sliding=FINITE, interactionProperty='FrictionArea', adjustMethod=NONE, initialClearance=OMIT)

    MODEL.SurfaceToSurfaceContactStd(name='FrictionInteraction_Right', createStepName='Initial',
        main=asm.surfaces['Center-Right-friction'], secondary=asm.surfaces['Right-Left-friction'],
        sliding=FINITE, interactionProperty='FrictionArea', adjustMethod=NONE, initialClearance=OMIT)

    # ---------------------------------------------------------------------------
    # 5. Boundary conditions (selection coords scaled)
    # ---------------------------------------------------------------------------
    y_bot = -H_s/2 + T_LEFT_s[1]
    bot_L = asm.instances['side_left'].faces.getByBoundingBox(yMin=y_bot-1e-3*s, yMax=y_bot+1e-3*s)
    bot_R = asm.instances['side_right'].faces.getByBoundingBox(yMin=y_bot-1e-3*s, yMax=y_bot+1e-3*s)
    asm.Set(name='left_bot',  faces=bot_L)
    asm.Set(name='right_bot', faces=bot_R)
    MODEL.DisplacementBC('BC_left_bot',  'Initial', asm.sets['left_bot'],  u2=0.0)
    MODEL.DisplacementBC('BC_right_bot', 'Initial', asm.sets['right_bot'], u2=0.0)

    x_sym = -W_s/2 + T_LEFT_s[0]
    inst_left  = asm.instances['side_left']
    lf = inst_left.faces.getByBoundingBox(xMin=x_sym-1e-3*s, xMax=x_sym+1e-3*s)
    asm.Set(name='left_face', faces=lf)
    MODEL.DisplacementBC('BC_left_face', 'Initial', asm.sets['left_face'], u1=0.0)

    z_L = DEPTH_s + T_LEFT_s[2]
    inst_right = asm.instances['side_right']
    # z_R = DEPTH_s + T_RIGHT_CORRECTED_s[2]   # 修正：使用放大後的右塊位移
    z_R = DEPTH_s + T_RIGHT_s[2]
    edge_L = inst_left.edges.getByBoundingBox(zMin=z_L-1e-3*s, zMax=z_L+1e-3*s)
    edge_R = inst_right.edges.getByBoundingBox(zMin=z_R-1e-3*s, zMax=z_R+1e-3*s)
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
    # 7. Loads (selection coords scaled; magnitude is stress → 不需縮放)
    # ---------------------------------------------------------------------------
    x_norm_right =  W_s/2 + T_RIGHT_CORRECTED_s[0]
    face_norm_right = inst_right.faces.getByBoundingBox(xMin=x_norm_right-1e-3*s, xMax=x_norm_right+1e-3*s)
    asm.Surface(name='Surf_norm_right', side1Faces=face_norm_right)
    MODEL.Pressure('normal_load', 'Normal_Load', asm.surfaces['Surf_norm_right'], magnitude=NORMAL_STRESS)

    y_top_spr = SPR_H_s + T_SPR_s[1]
    inst_spr = asm.instances['spring']
    top_spr = inst_spr.faces.getByBoundingBox(yMin=y_top_spr-1e-3*s, yMax=y_top_spr+1e-3*s)
    asm.Surface(name='Surf_shear', side1Faces=top_spr)

    region = MODEL.rootAssembly.Set(name='Set_shear', faces=asm.surfaces['Surf_shear'].faces)
    MODEL.DisplacementBC(
        name='shear_disp', createStepName='Shear_Load', region=MODEL.rootAssembly.sets['Set_shear'],
        u1=UNSET, u2=-SHEAR_AMPLITUDE, u3=UNSET, ur1=UNSET, ur2=UNSET, ur3=UNSET,
        amplitude=UNSET, fixed=OFF, distributionType=UNIFORM, fieldName='', localCsys=None
    )

    # ---------------------------------------------------------------------------
    # 8. Meshing (non-spring uses scaled seed; spring keeps original seed)
    # ---------------------------------------------------------------------------
    elem_type = ElemType(elemCode=C3D8I, elemLibrary=STANDARD)

    inst_plt = asm.instances['steel_plate']
    ctr_inst = asm.instances['center_block']

    # 非彈簧
    for inst in (inst_left, inst_right, inst_plt, ctr_inst):
        asm.setElementType(regions=(inst.cells,), elemTypes=(elem_type,))
        asm.seedPartInstance(regions=(inst,), size=MESH_SIZE)
        asm.generateMesh(regions=(inst,))

    # 彈簧：保持原本 seed
    asm.setElementType(regions=(inst_spr.cells,), elemTypes=(elem_type,))
    asm.seedPartInstance(regions=(inst_spr,), size=MESH_SIZE)
    asm.generateMesh(regions=(inst_spr,))

    if 'Model-1' in mdb.models:
        del mdb.models['Model-1']

    # ---------------------------------------------------------------------------
    # 9. Field Output Requests (同原本；集合/實體名稱未變)
    # ---------------------------------------------------------------------------
    MODEL.FieldOutputRequest(
        createStepName='Shear_Load', name='Spring-Strain-Energy', rebar=EXCLUDE,
        region=MODEL.rootAssembly.allInstances['spring'].sets['spring_set'], frequency=1,
        sectionPoints=DEFAULT, variables=('ENER', 'ELEN', 'ELEDEN')
    )
    MODEL.FieldOutputRequest(
        createStepName='Shear_Load', name='Center-Block-Strain-Energy', rebar=EXCLUDE,
        region=MODEL.rootAssembly.allInstances['center_block'].sets['all'], frequency=1,
        sectionPoints=DEFAULT, variables=('ENER', 'ELEN', 'ELEDEN')
    )
    MODEL.FieldOutputRequest(
        createStepName='Shear_Load', name='Side-Block-Left-Strain-Energy', rebar=EXCLUDE,
        region=MODEL.rootAssembly.allInstances['side_left'].sets['all'], frequency=1,
        sectionPoints=DEFAULT, variables=('ENER', 'ELEN', 'ELEDEN')
    )
    MODEL.FieldOutputRequest(
        createStepName='Shear_Load', name='Side-Block-Right-Strain-Energy', rebar=EXCLUDE,
        region=MODEL.rootAssembly.allInstances['side_right'].sets['all'], frequency=1,
        sectionPoints=DEFAULT, variables=('ENER', 'ELEN', 'ELEDEN')
    )
    MODEL.FieldOutputRequest(
        createStepName='Shear_Load', name='Steel-Plate-Energy', rebar=EXCLUDE,
        region=MODEL.rootAssembly.allInstances['steel_plate'].sets['plate_set'], frequency=1,
        sectionPoints=DEFAULT, variables=('ENER', 'ELEN', 'ELEDEN')
    )
    MODEL.FieldOutputRequest(
        createStepName='Shear_Load', name='Side-Block-Left-Stress', rebar=EXCLUDE,
        region=MODEL.rootAssembly.allInstances['side_left'].sets['all'], sectionPoints=DEFAULT,
        variables=('S', 'MISES')
    )

    # ---------------------------------------------------------------------------
    # 10. Job
    # ---------------------------------------------------------------------------
    job = mdb.Job(name=job_name, model=model_name)
    job.writeInput()


# -----------------------------
# Main program loop
# -----------------------------
RUPTURE_POSITIONS = [105, 100, 95, 90, 85, 80, 75, 65, 55, 45, 35, 25, 15, 5]
# RUPTURE_POSITIONS = [105]
SCALES = [5]


for RUPTURE_POSITION in RUPTURE_POSITIONS:
    for SCALE in SCALES:
        build_model(RUPTURE_POSITION, SCALE)