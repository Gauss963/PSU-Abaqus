from abaqus import mdb
from abaqusConstants import *

# ---------------------------------------------------------------------------
# 0. Geometry parameters
# ---------------------------------------------------------------------------
W, H, DEPTH  = 100.0, 160.0, 50.0          # side-block  X, Y,  extrusion Z
CENTER_D     = 60.0                        # center-block extrusion depth
SPR_W, SPR_H, SPR_D = 40.0, 80.0, 40.0     # spring  X, Y, Z
PL_W,  PL_H,  PL_D = 90.0, 12.7, 60.0      # plate   X, Y, Z
CHAMFER      = 5.0

# placement vectors (assembly coordinates)
T_LEFT  = (-100.0, -20.0,   5.0)
T_RIGHT = ( 100.0, -20.0, -45.0)
T_SPR   = (-20.0, 112.7,  10.0)
T_PLT   = (-45.0, 100.0,   0.0)

# ---------------------------------------------------------------------------
# 1. Model container
# ---------------------------------------------------------------------------
MODEL = mdb.Model(name='Block-Assembly')

# ---------------------------------------------------------------------------
# 2-1  Side block – 45° bevel already included in the sketch
# ---------------------------------------------------------------------------
sk_side = MODEL.ConstrainedSketch(name='sk_side', sheetSize=400.0)
# vertices (counter-clockwise)
pts = [(-W/2, -H/2),
       ( W/2-CHAMFER, -H/2),
       ( W/2,        -H/2+CHAMFER),
       ( W/2,         H/2-CHAMFER),
       ( W/2-CHAMFER,  H/2),
       (-W/2,  H/2)]
for i in range(len(pts)):
    sk_side.Line(point1=pts[i], point2=pts[(i+1) % len(pts)])

side_part = MODEL.Part(name='side_block',
                       dimensionality=THREE_D,
                       type=DEFORMABLE_BODY)
side_part.BaseSolidExtrude(sketch=sk_side, depth=DEPTH)

# ---------------------------------------------------------------------------
# 2-2  Center block – add 5 mm chamfer on every vertical edge
# ---------------------------------------------------------------------------
sk_ctr = MODEL.ConstrainedSketch(name='sk_center', sheetSize=400.0)
sk_ctr.rectangle(point1=(-50, -100), point2=(50, 100))
center_part = MODEL.Part(name='center_block',
                         dimensionality=THREE_D,
                         type=DEFORMABLE_BODY)
center_part.BaseSolidExtrude(sketch=sk_ctr, depth=CENTER_D)

def add_chamfer(part, size):
    """Add a symmetric (size, size) chamfer on every vertical edge, version-agnostic."""
    # Select only vertical edges (parallel to Y axis)
    vertical_edges = []
    seen = set()
    min_edge_length = None
    for e in part.edges:
        v1 = e.getVertices()
        if len(v1) != 2:
            continue
        p1 = part.vertices[v1[0]].pointOn[0]
        p2 = part.vertices[v1[1]].pointOn[0]
        # Check if edge is vertical (Y-direction)
        if abs(p1[0]-p2[0]) < 1e-6 and abs(p1[2]-p2[2]) < 1e-6 and abs(p1[1]-p2[1]) > 1e-6:
            # Avoid duplicates by using sorted vertex indices as a key
            key = tuple(sorted(v1))
            if key not in seen:
                seen.add(key)
                # Also check for zero-length edges
                edge_length = ((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2 + (p1[2]-p2[2])**2)**0.5
                if edge_length > 1e-8:
                    vertical_edges.append(e)
                    if min_edge_length is None or edge_length < min_edge_length:
                        min_edge_length = edge_length

    if len(vertical_edges) == 0:
        print("Warning: No vertical edges found for chamfering. Skipping chamfer operation.")
        return

    # Chamfer size must be strictly less than half the minimum edge length
    if min_edge_length is not None and size >= min_edge_length / 2.0:
        new_size = min_edge_length / 2.01
        print("Warning: Chamfer size too large for geometry. Reducing size to {:.3f}".format(new_size))
        size = new_size

    # Only perform chamfer if there are valid edges and size is positive
    if len(vertical_edges) > 0 and size > 0.0:
        if hasattr(part, 'ChamferEdge'):                         # 2022+
            part.ChamferEdge(edgeList=vertical_edges,
                             lengths=(size, size))
        else:                                                    # legacy
            part.Chamfer(edgeList=vertical_edges, distance1=size, distance2=size)
    else:
        print("Warning: Chamfer skipped due to invalid edge list or size.")

add_chamfer(center_part, CHAMFER)

# ---------------------------------------------------------------------------
# 2-3  Spring  & 2-4  Steel plate
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

ctr_inst = asm.Instance(name='center_block', part=center_part, dependent=OFF)

inst_left  = asm.Instance(name='side_left',  part=side_part,  dependent=OFF)
asm.translate(instanceList=(inst_left,),  vector=T_LEFT)

inst_right = asm.Instance(name='side_right', part=side_part,  dependent=OFF)
asm.rotate(instanceList=(inst_right,),
           axisPoint=(0.0, 0.0, 0.0),
           axisDirection=(0.0, 1.0, 0.0),
           angle=180.0)
asm.translate(instanceList=(inst_right,), vector=T_RIGHT)

inst_spr = asm.Instance(name='spring', part=spring_part, dependent=OFF)
asm.translate(instanceList=(inst_spr,), vector=T_SPR)

inst_plt = asm.Instance(name='steel_plate', part=plate_part, dependent=OFF)
asm.translate(instanceList=(inst_plt,), vector=T_PLT)

# ---------------------------------------------------------------------------
# 5. Boundary conditions
# ---------------------------------------------------------------------------
# Bottom faces of both side blocks: fix Y-translation
y_bot = -H/2 + T_LEFT[1]                               # -80 - 20 = -100 mm

bot_L = inst_left.faces.getByBoundingBox(yMin=y_bot-1e-3, yMax=y_bot+1e-3)
bot_R = inst_right.faces.getByBoundingBox(yMin=y_bot-1e-3, yMax=y_bot+1e-3)
asm.Set(name='left_bot',  faces=bot_L)
asm.Set(name='right_bot', faces=bot_R)

MODEL.DisplacementBC('BC_left_bot',  'Initial', asm.sets['left_bot'],  u2=0.0)
MODEL.DisplacementBC('BC_right_bot', 'Initial', asm.sets['right_bot'], u2=0.0)

# X-symmetry at left outer face of side_left
x_sym = -W/2 + T_LEFT[0]                               # -50 - 100 = -150 mm
lf = inst_left.faces.getByBoundingBox(xMin=x_sym-1e-3, xMax=x_sym+1e-3)
asm.Set(name='left_face', faces=lf)
MODEL.DisplacementBC('BC_left_face', 'Initial', asm.sets['left_face'], u1=0.0)

# Front edges (u3 = 0)
z_L = DEPTH + T_LEFT[2]                                # 55 mm
z_R = -DEPTH + T_RIGHT[2]                              # -95 mm
edge_L = inst_left.edges.getByBoundingBox(zMin=z_L-1e-3, zMax=z_L+1e-3)
edge_R = inst_right.edges.getByBoundingBox(zMin=z_R-1e-3, zMax=z_R+1e-3)
asm.Set(name='front_edges_L', edges=edge_L)
asm.Set(name='front_edges_R', edges=edge_R)

MODEL.DisplacementBC('BC_front_L', 'Initial',
                     asm.sets['front_edges_L'], u3=0.0)
MODEL.DisplacementBC('BC_front_R', 'Initial',
                     asm.sets['front_edges_R'], u3=0.0)

# ---------------------------------------------------------------------------
# 6. Analysis steps
# ---------------------------------------------------------------------------
MODEL.StaticStep(name='Normal_Load', previous='Initial', nlgeom=ON)
MODEL.StaticStep(name='Shear_Load',  previous='Normal_Load')

# ---------------------------------------------------------------------------
# 7. Loads
# ---------------------------------------------------------------------------
# 7-1 Normal pressure on right face of side_left
x_norm =  W/2 + T_LEFT[0]                              # -50 mm
face_norm = inst_left.faces.getByBoundingBox(xMin=x_norm-1e-3,
                                             xMax=x_norm+1e-3)
asm.Surface(name='Surf_norm', side1Faces=face_norm)
MODEL.Pressure('normal_load', 'Normal_Load',
               asm.surfaces['Surf_norm'], magnitude=10.0)

# 7-2 Shear pressure on top face of the spring
y_top_spr = SPR_H + T_SPR[1]                           # 192.7 mm
top_spr = inst_spr.faces.getByBoundingBox(yMin=y_top_spr-1e-3,
                                          yMax=y_top_spr+1e-3)
asm.Surface(name='Surf_shear', side1Faces=top_spr)
MODEL.Pressure('shear_load', 'Shear_Load',
               asm.surfaces['Surf_shear'], magnitude=10.0)

# ---------------------------------------------------------------------------
# 8. Meshing – coarse demo seeds (size = 20 mm)
# ---------------------------------------------------------------------------
for inst in (inst_left, inst_right, inst_spr, inst_plt, ctr_inst):
    asm.seedPartInstance(regions=(inst,), size=20.0)
asm.generateMesh()

# ---------------------------------------------------------------------------
# 9. Job
# ---------------------------------------------------------------------------
job = mdb.Job(name='BlockJob', model='Block-Assembly')
job.writeInput()          # use job.submit() to solve immediately