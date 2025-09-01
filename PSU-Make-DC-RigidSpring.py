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


def build_model(RUPTURE_POSITION):

    # ---------------------------------------------------------------------------
    # 0. Parameters
    # ---------------------------------------------------------------------------

    # Job names
    model_name = f'Block-Assembly-{int(RUPTURE_POSITION)}'
    job_name = f'BlockJob-{int(RUPTURE_POSITION)}'

    # Geometry parameters
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

    # Simulation parameters
    FRICTION_COEFFICIENT = 0.70
    NORMAL_STRESS = 10.0  # MPa [5.0, 7.5, 10.0, 12.5]
    Y_PMMA = 3000.0       # MPa, PMMA Young's modulus
    MESH_SIZE = 2.000
    RUPTURE_START = 55.00
    RESISTANCE_AREA_LENGTH = 220.0 # mm, length of the resistance area

    RESISTANCE  = 2 * FRICTION_COEFFICIENT * DEPTH * RESISTANCE_AREA_LENGTH * NORMAL_STRESS  # N
    CONTACT_AREA = SPR_W * SPR_D                                                             # mm²
    RESISTANCE_STRESS = RESISTANCE / CONTACT_AREA                                            # MPa

    SPRING_STIFFNESS = Y_PMMA * CONTACT_AREA / SPR_H                                         # N/mm
    SHEAR_AMPLITUDE = RESISTANCE / SPRING_STIFFNESS                                          # mm

    # ----------------------------
    # Switch: use rigid PMMA_R?
    # ----------------------------
    USE_RIGID_SPRING = True  # True=剛體 PMMA_R；False=彈性 PMMA

    # ---------------------------------------------------------------------------
    # 1. Model container
    # ---------------------------------------------------------------------------
    MODEL = mdb.Model(name=model_name)

    # ---------------------------------------------------------------------------
    # 2-1  Side block - 45 bevel in sketch
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

    add_chamfer(center_part, CHAMFER)

    # --- center_block：用 Y = (RUPTURE_START - RUPTURE_POSITION) 的平面分割 ---
    ycut_center = RUPTURE_START - RUPTURE_POSITION  # 例如 55-115=-60，仍在 [-80,80] 內
    cell = center_part.cells.getSequenceFromMask(('[#1 ]', ), )
    center_part.PartitionCellByPlaneThreePoints(
        cells=cell,
        point1=( 0.0, ycut_center, 0.0),
        point2=(10.0, ycut_center, 0.0),
        point3=( 0.0, ycut_center,10.0)
    )

    # --- side_block：用 Y = (RUPTURE_START - RUPTURE_POSITION + 20) 的平面分割 ---
    ycut_side = RUPTURE_START - RUPTURE_POSITION + 20.0
    side_cell = side_part.cells.getSequenceFromMask(('[#1 ]', ), )
    side_part.PartitionCellByPlaneThreePoints(
        cells=side_cell,
        point1=( 0.0, ycut_side, 0.0),
        point2=(10.0, ycut_side, 0.0),
        point3=( 0.0, ycut_side,10.0)
    )

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
    mat_pmma.Elastic(table=((Y_PMMA, 0.35),))
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
    asm.Instance(name='steel_plate',  part=plate_part,   dependent=OFF)

    asm.translate(instanceList=('side_left',), vector=T_LEFT)
    asm.rotate(instanceList=('side_right',), axisPoint=(0,0,0), axisDirection=(0,1,0), angle=180.0)
    T_RIGHT_CORRECTED = (50 - (-50), -20.0, 55.0)
    asm.translate(instanceList=('side_right',), vector=T_RIGHT_CORRECTED)
    asm.translate(instanceList=('steel_plate',), vector=T_PLT)

    # === Spring instance & (optionally) rigid definition ===
    if USE_RIGID_SPRING:
        asm.Instance(name='spring_R', part=spring_part, dependent=OFF)
        asm.translate(instanceList=('spring_R',), vector=T_SPR)
        inst_spr = asm.instances['spring_R']

        # Reference point at top-center of spring_R to drive rigid body
        rp = asm.ReferencePoint(point=(SPR_W/2.0 + T_SPR[0],
                                       SPR_H      + T_SPR[1],
                                       SPR_D/2.0 + T_SPR[2]))
        rp_set = asm.Set(name='PMMA_R_RP', referencePoints=(asm.referencePoints[rp.id],))
        springR_all = asm.Set(name='springR_all', cells=inst_spr.cells)
        MODEL.RigidBody(name='PMMA_RigidDef', refPointRegion=rp_set, bodyRegion=springR_all)
    else:
        asm.Instance(name='spring', part=spring_part, dependent=OFF)
        asm.translate(instanceList=('spring',), vector=T_SPR)
        inst_spr = asm.instances['spring']

    # --- Surfaces (center/side/plate) via masks: keep your original definitions ---
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

    # For spring top surface (for shear BC region in elastic mode; harmless in rigid mode)
    y_top_spr = SPR_H + T_SPR[1]
    top_spr = inst_spr.faces.getByBoundingBox(yMin=y_top_spr-1e-3, yMax=y_top_spr+1e-3)
    asm.Surface(name='Surf_shear', side1Faces=top_spr)

    # Conditional spring bottom surface + Tie to plate
    if USE_RIGID_SPRING:
        y_bot_spr = T_SPR[1]
        spr_bot_faces = inst_spr.faces.getByBoundingBox(yMin=y_bot_spr-1e-3, yMax=y_bot_spr+1e-3)
        asm.Surface(name='springR-bottom', side1Faces=spr_bot_faces)
        MODEL.Tie(
            name='SpringR-Steel-Tie',
            main=asm.surfaces['springR-bottom'],
            secondary=asm.surfaces['steel_plate-Top'],
            positionToleranceMethod=COMPUTED,
            adjust=ON,
            tieRotations=ON,
            thickness=ON
        )
    else:
        # Original spring-bottom surface via mask (stable alternative is also bbox like above)
        asm.Surface(name='spring-bottom', side1Faces=asm.instances['spring'].faces.getSequenceFromMask(('[#8 ]', ), ))
        MODEL.Tie(
            name='Spring-Steel-Tie',
            main=asm.surfaces['spring-bottom'],
            secondary=asm.surfaces['steel_plate-Top'],
            positionToleranceMethod=COMPUTED,
            adjust=ON,
            tieRotations=ON,
            thickness=ON
        )

    # --- Ties between blocks and plate (unchanged) ---
    MODEL.Tie(
        name='Left-Tie',
        main=asm.surfaces['Left-Right-Tie'],
        secondary=asm.surfaces['Center-Left-Tie'],
        positionToleranceMethod=COMPUTED,
        adjust=ON,
        tieRotations=ON,
        thickness=ON
    )
    MODEL.Tie(
        name='Right-Tie',
        main=asm.surfaces['Center-Right-Tie'],
        secondary=asm.surfaces['Right-Left-Tie'],
        positionToleranceMethod=COMPUTED,
        adjust=ON,
        tieRotations=ON,
        thickness=ON
    )
    MODEL.Tie(
        name='Steel-Center-Tie',
        main=asm.surfaces['steel_plate-bottom'],
        secondary=asm.surfaces['Center-Top'],
        positionToleranceMethod=COMPUTED,
        adjust=ON,
        tieRotations=ON,
        thickness=ON
    )

    # --- Contact (unchanged) ---
    MODEL.ContactProperty('FrictionArea')
    MODEL.interactionProperties['FrictionArea'].TangentialBehavior(
        dependencies=0, directionality=ISOTROPIC, elasticSlipStiffness=None,
        formulation=PENALTY, fraction=0.005, maximumElasticSlip=FRACTION,
        pressureDependency=OFF, shearStressLimit=None, slipRateDependency=OFF,
        table=((FRICTION_COEFFICIENT,),), temperatureDependency=OFF
    )
    MODEL.interactionProperties['FrictionArea'].NormalBehavior(
        allowSeparation=ON, constraintEnforcementMethod=DEFAULT, 
        pressureOverclosure=HARD)

    MODEL.SurfaceToSurfaceContactStd(
        name='FrictionInteraction_Left',
        createStepName='Initial',
        main=asm.surfaces['Center-Left-friction'],
        secondary=asm.surfaces['Left-Right-friction'],
        sliding=FINITE,
        interactionProperty='FrictionArea',
        adjustMethod=NONE,
        initialClearance=OMIT,
        datumAxis=None,
        clearanceRegion=None
    )
    MODEL.SurfaceToSurfaceContactStd(
        name='FrictionInteraction_Right',
        createStepName='Initial',
        main=asm.surfaces['Center-Right-friction'],
        secondary=asm.surfaces['Right-Left-friction'],
        sliding=FINITE,
        interactionProperty='FrictionArea',
        adjustMethod=NONE,
        initialClearance=OMIT,
        datumAxis=None,
        clearanceRegion=None
    )

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
    z_R = DEPTH + T_RIGHT_CORRECTED[2]  # 修正：使用 T_RIGHT_CORRECTED
    edge_L = inst_left.edges.getByBoundingBox(zMin=z_L-1e-3, zMax=z_L+1e-3)
    inst_right = asm.instances['side_right']
    edge_R = inst_right.edges.getByBoundingBox(zMin=z_R-1e-3, zMax=z_R+1e-3)
    asm.Set(name='front_edges_L', edges=edge_L)
    asm.Set(name='front_edges_R', edges=edge_R)
    MODEL.DisplacementBC('BC_front_L', 'Initial', asm.sets['front_edges_L'], u3=0.0)
    # MODEL.DisplacementBC('BC_front_R', 'Initial', asm.sets['front_edges_R'], u3=0.0)  # 原設定保留為註解

    asm.Set(name='Set-12', vertices=asm.instances['side_right'].vertices.getSequenceFromMask(('[#800 ]', ), ))  # 2025/08/30
    MODEL.DisplacementBC('BC_front_bot_u3_R', 'Initial', asm.sets['Set-12'], u3=0.0)                            # 2025/08/30

    # ---------------------------------------------------------------------------
    # 6. Analysis steps
    # ---------------------------------------------------------------------------
    MODEL.StaticStep(name='Normal_Load', previous='Initial', nlgeom=ON)
    MODEL.StaticStep(name='Shear_Load',  previous='Normal_Load', nlgeom=ON)

    # ---------------------------------------------------------------------------
    # 7. Loads & Shear displacement BC
    # ---------------------------------------------------------------------------
    x_norm_right =  W/2 + T_RIGHT_CORRECTED[0]
    face_norm_right = inst_right.faces.getByBoundingBox(xMin=x_norm_right-1e-3, xMax=x_norm_right+1e-3)
    asm.Surface(name='Surf_norm_right', side1Faces=face_norm_right)
    MODEL.Pressure('normal_load', 'Normal_Load', asm.surfaces['Surf_norm_right'], magnitude=NORMAL_STRESS)

    if USE_RIGID_SPRING:
        # 位移施加在剛體的 RP
        MODEL.DisplacementBC(
            name='shear_disp',
            createStepName='Shear_Load',
            region=MODEL.rootAssembly.sets['PMMA_R_RP'],
            u1=UNSET, u2=-SHEAR_AMPLITUDE, u3=UNSET,
            ur1=UNSET, ur2=UNSET, ur3=UNSET,
            amplitude=UNSET,
            fixed=OFF,
            distributionType=UNIFORM,
            fieldName='',
            localCsys=None
        )
    else:
        # 位移施加在彈簧上表面（維持原有設計）
        MODEL.rootAssembly.Set(name='Set_shear', faces=asm.surfaces['Surf_shear'].faces)
        MODEL.DisplacementBC(
            name='shear_disp',
            createStepName='Shear_Load',
            region=MODEL.rootAssembly.sets['Set_shear'],
            u1=UNSET, u2=-SHEAR_AMPLITUDE, u3=UNSET,
            ur1=UNSET, ur2=UNSET, ur3=UNSET,
            amplitude=UNSET,
            fixed=OFF,
            distributionType=UNIFORM,
            fieldName='',
            localCsys=None
        )

    # ---------------------------------------------------------------------------
    # 8. Meshing
    # ---------------------------------------------------------------------------
    elem_type = ElemType(elemCode=C3D8I, elemLibrary=STANDARD)
    inst_plt = asm.instances['steel_plate']
    ctr_inst = asm.instances['center_block']
    for inst in (inst_left, inst_right, inst_spr, inst_plt, ctr_inst):
        asm.setElementType(regions=(inst.cells,), elemTypes=(elem_type,))
        asm.seedPartInstance(regions=(inst,), size=MESH_SIZE)
        asm.generateMesh(regions=(inst,))
    if 'Model-1' in mdb.models:
        del mdb.models['Model-1']

    # ---------------------------------------------------------------------------
    # 9. Setup output requests
    # ---------------------------------------------------------------------------
    # 只有在彈性彈簧模式下才輸出彈簧能量（剛體沒有應變能）
    if not USE_RIGID_SPRING:
        MODEL.FieldOutputRequest(
            createStepName='Shear_Load', 
            name='Spring-Strain-Energy', 
            rebar=EXCLUDE,
            region=MODEL.rootAssembly.allInstances['spring'].sets['spring_set'],
            frequency=1,
            sectionPoints=DEFAULT,
            variables=('ENER', 'ELEN', 'ELEDEN')
        )

    MODEL.FieldOutputRequest(
        createStepName='Shear_Load', 
        name='Center-Block-Strain-Energy', 
        rebar=EXCLUDE,
        region=MODEL.rootAssembly.allInstances['center_block'].sets['all'],
        frequency=1,
        sectionPoints=DEFAULT,
        variables=('ENER', 'ELEN', 'ELEDEN')
    )
    MODEL.FieldOutputRequest(
        createStepName='Shear_Load', 
        name='Side-Block-Left-Strain-Energy', 
        rebar=EXCLUDE,
        region=MODEL.rootAssembly.allInstances['side_left'].sets['all'],
        frequency=1,
        sectionPoints=DEFAULT,
        variables=('ENER', 'ELEN', 'ELEDEN')
    )
    MODEL.FieldOutputRequest(
        createStepName='Shear_Load', 
        name='Side-Block-Right-Strain-Energy', 
        rebar=EXCLUDE,
        region=MODEL.rootAssembly.allInstances['side_right'].sets['all'],
        frequency=1,
        sectionPoints=DEFAULT,
        variables=('ENER', 'ELEN', 'ELEDEN')
    )
    MODEL.FieldOutputRequest(
        createStepName='Shear_Load', 
        name='Steel-Plate-Energy', 
        rebar=EXCLUDE,
        region=MODEL.rootAssembly.allInstances['steel_plate'].sets['plate_set'],
        frequency=1,
        sectionPoints=DEFAULT,
        variables=('ENER', 'ELEN', 'ELEDEN')
    )
    MODEL.FieldOutputRequest(
        createStepName='Shear_Load', 
        name='Side-Block-Left-Stress',
        rebar=EXCLUDE,
        region=MODEL.rootAssembly.allInstances['side_left'].sets['all'],
        sectionPoints=DEFAULT,
        variables=('S', 'MISES')
    )

    # ---------------------------------------------------------------------------
    # 10. Job
    # ---------------------------------------------------------------------------
    job = mdb.Job(name=job_name, model=model_name, numCpus=20, numDomains=20)
    job.writeInput()


# -----------------------------
# Main program loop
# -----------------------------
RUPTURE_POSITIONS = [115, 110, 105, 100, 95, 90, 85, 80, 75, 65, 55, 45, 35, 25, 15, 5]

for RUPTURE_POSITION in RUPTURE_POSITIONS:
    build_model(RUPTURE_POSITION)