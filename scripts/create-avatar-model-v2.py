"""Build an editable stylized character study from the supplied portrait.

Run with Blender --background --factory-startup --python scripts/create-avatar-model-v2.py
Outputs are isolated from the live website and contain no rig or animation yet.
"""
import bpy
import math
import random
import runpy
from pathlib import Path
from mathutils import Vector, Matrix

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'models' / 'avatar-v2'
OUT.mkdir(parents=True, exist_ok=True)
random.seed(19)
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

def collection(name):
    result = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(result)
    return result

HEAD = collection('01 · Rostro y cuello')
HAIR = collection('02 · Cabello rizado')
CLOTHES = collection('03 · Sudadera y detalles')
HANDS = collection('04 · Manos completas')
LEGS = collection('05 · Pantalón y zapatillas')
STUDIO = collection('90 · Estudio de iluminación')

def move(obj, target):
    for current in list(obj.users_collection):
        current.objects.unlink(obj)
    target.objects.link(obj)

def material(name, color, roughness=.65, fabric=False, skin=False):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    shader = nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value = (*color, 1)
    shader.inputs['Roughness'].default_value = roughness
    shader.inputs['Specular IOR Level'].default_value = .22
    if skin:
        shader.inputs['Subsurface Weight'].default_value = .07
        shader.inputs['Subsurface Radius'].default_value = (1, .45, .25)
    if fabric:
        shader.inputs['Sheen Weight'].default_value = .06
        noise = nodes.new('ShaderNodeTexNoise')
        noise.inputs['Scale'].default_value = 190
        noise.inputs['Detail'].default_value = 2
        bump = nodes.new('ShaderNodeBump')
        bump.inputs['Strength'].default_value = .13
        bump.inputs['Distance'].default_value = .014
        mat.node_tree.links.new(noise.outputs['Fac'], bump.inputs['Height'])
        mat.node_tree.links.new(bump.outputs['Normal'], shader.inputs['Normal'])
    return mat

skin = material('Piel · melocotón cálido', (.78, .215, .10), .62, skin=True)
skin_inner = material('Piel · interior oreja', (.54, .215, .135), .66, skin=True)
nose_mat = material('Piel · nariz', (.71, .235, .105), .62, skin=True)
black = material('Ojos y sonrisa · carbón', (.009, .007, .007), .8)
hair_mats = [material('Rizos · tono %02d' % i, (.0025 + i*.0004, .0025 + i*.0004, .0028 + i*.0004), .65) for i in range(5)]
hoodie = material('Sudadera · grafito', (.040, .044, .052), .94, fabric=True)
rib = material('Puños y cintura · canalé', (.025, .027, .03), .96, fabric=True)
lining = material('Capucha · interior', (.014, .016, .018), .96, fabric=True)
seam = material('Costura · grafito suave', (.038, .044, .055), .89)
cordmat = material('Cordones · gris', (.035, .038, .043), .93)
pants = material('Pantalón · negro lavado', (.022, .025, .032), .91, fabric=True)
shoe = material('Zapatillas · carbón', (.032, .037, .043), .76)
sole = material('Suela · gris hueso', (.44, .43, .40), .79)

def finish(obj, mat, target):
    if mat:
        obj.data.materials.append(mat)
    move(obj, target)
    if obj.type == 'MESH':
        for poly in obj.data.polygons:
            poly.use_smooth = True
    return obj

def uv(name, location, scale, mat, target, segments=24, rings=16):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return finish(obj, mat, target)

def mesh(name, vertices, faces, mat, target, subdiv=0):
    data = bpy.data.meshes.new(name)
    data.from_pydata(vertices, [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    target.objects.link(obj)
    finish(obj, mat, target)
    if subdiv:
        modifier = obj.modifiers.new('Superficie suave editable', 'SUBSURF')
        modifier.levels = subdiv
        modifier.render_levels = subdiv
    return obj

def tube(name, points, radius, mat, target, resolution=3):
    data = bpy.data.curves.new(name, 'CURVE')
    data.dimensions = '3D'
    data.resolution_u = 10
    data.bevel_depth = radius
    data.bevel_resolution = resolution
    data.use_fill_caps = True
    spline = data.splines.new('BEZIER')
    spline.bezier_points.add(len(points)-1)
    for node, coordinate in zip(spline.bezier_points, points):
        node.co = coordinate
        node.handle_left_type = 'AUTO'
        node.handle_right_type = 'AUTO'
    obj = bpy.data.objects.new(name, data)
    target.objects.link(obj)
    obj.data.materials.append(mat)
    return obj

def loft(name, levels, mat, target, steps=48, subdiv=2, wrinkles=0):
    # Each row: height, X radius, Y radius, X center, Y center.
    vertices, faces = [], []
    for index, (z, rx, ry, cx, cy) in enumerate(levels):
        for j in range(steps):
            a = math.tau * j / steps
            wrinkle = 1 + wrinkles * math.sin(7*a + index*.8) * math.sin(math.pi*index/(len(levels)-1))
            vertices.append((cx + rx*math.cos(a)*wrinkle, cy + ry*math.sin(a)*wrinkle, z))
    for i in range(len(levels)-1):
        for j in range(steps):
            faces.append((i*steps+j, i*steps+(j+1)%steps, (i+1)*steps+(j+1)%steps, (i+1)*steps+j))
    faces += [tuple(range(steps-1, -1, -1)), tuple((len(levels)-1)*steps+j for j in range(steps))]
    return mesh(name, vertices, faces, mat, target, subdiv)

# Soft jaw and cheeks, with a flatter face than an ordinary sphere.
head_levels = [
    (4.48, .13, .15, 0, -.015), (4.53, .34, .31, 0, -.02),
    (4.63, .51, .44, 0, -.04), (4.80, .66, .555, 0, -.035),
    (5.02, .765, .605, 0, -.018), (5.26, .79, .64, 0, 0),
    (5.49, .77, .625, 0, .018), (5.70, .72, .58, 0, .03),
    (5.90, .60, .48, 0, .035), (6.04, .36, .29, 0, .04),
    (6.09, .04, .04, 0, .04),
]
head = loft('Cabeza · mejillas y mandíbula', head_levels, skin, HEAD, subdiv=2)

def face_y(x, z, inset):
    # Project features onto the evaluated face, including subdivision.
    # Fixed Y coordinates can look correct from the front yet float in profile.
    bpy.context.view_layer.update()
    evaluated = head.evaluated_get(bpy.context.evaluated_depsgraph_get())
    hit, location, normal, index = evaluated.ray_cast(Vector((x,-3,z)), Vector((0,1,0)))
    if not hit:
        raise ValueError('No face surface at %s, %s' % (x,z))
    return location.y - inset

loft('Cuello', [(4.05,.25,.23,0,.025),(4.12,.26,.235,0,.025),(4.57,.255,.24,0,.025),(4.7,.29,.25,0,.025)], skin, HEAD, steps=32, subdiv=2)
for side in [-1, 1]:
    uv('Oreja ' + str(side), (side*.765, .015, 5.04), (.175,.12,.218), skin, HEAD)
    eye = uv('Ojo ' + str(side), (side*.275,face_y(side*.275,5.37,.010),5.37), (.050,.028,.088), black, HEAD)
    eye.rotation_euler.y = -.10
    brow = [(side*.16,-.631,5.58), (side*.265,-.620,5.610), (side*.37,-.578,5.594)]
    brow = [(x,face_y(x,z,.020),z) for x,y,z in brow]
    tube('Ceja ' + str(side), brow, .037, black, HEAD, 4)
    for endpoint in [brow[0], brow[-1]]:
        uv('Extremo suave ceja', endpoint, (.037,.037,.037), black, HEAD, 12, 8)
uv('Nariz redondeada', (0,-.68,5.095), (.108,.118,.111), nose_mat, HEAD)
smile_points = [(-.155,-.568,4.878),(-.08,-.601,4.850),(0,-.613,4.842),(.08,-.601,4.850),(.155,-.568,4.873)]
smile_points = [(x,face_y(x,z,.006),z) for x,y,z in smile_points]
tube('Sonrisa sutil', smile_points, .015, black, HEAD, 4)
for endpoint in [smile_points[0], smile_points[-1]]:
    uv('Extremo suave sonrisa', endpoint, (.015,.015,.015), black, HEAD, 12, 8)

# A fitted scalp beneath individually editable soft curls.
scalp_vertices, scalp_faces = [], []
HAIR_STEPS, HAIR_RINGS = 48, 14
for row in range(HAIR_RINGS):
    for j in range(HAIR_STEPS):
        azimuth = math.tau*j/HAIR_STEPS
        front = max(0, -math.sin(azimuth))
        limit = 2.13 - 1.15 * front**.65
        polar = .02 + (limit-.02)*row/(HAIR_RINGS-1)
        scalp_vertices.append((.775*math.sin(polar)*math.cos(azimuth), .055+.65*math.sin(polar)*math.sin(azimuth), 5.46+.74*math.cos(polar)))
for row in range(HAIR_RINGS-1):
    for j in range(HAIR_STEPS):
        scalp_faces.append((row*HAIR_STEPS+j,row*HAIR_STEPS+(j+1)%HAIR_STEPS,(row+1)*HAIR_STEPS+(j+1)%HAIR_STEPS,(row+1)*HAIR_STEPS+j))
mesh('Base de cabello', scalp_vertices, scalp_faces, hair_mats[0], HAIR, 1)
# Variable-radius Poisson distribution avoids both horizontal and diagonal rows.
curl_samples=[]
for attempt in range(8000):
    p=math.acos(1-random.random()*1.62)
    a=random.random()*math.tau
    front = max(0,-math.sin(a))
    limit = 2.13 - 1.15*front**.65 + .075*math.cos(a)
    if p > limit:
        continue
    pos=Vector((.785*math.sin(p)*math.cos(a),.065+.65*math.sin(p)*math.sin(a),5.46+.75*math.cos(p)))
    radius=random.uniform(.125,.165)*(1.05 if p<.8 else 1)
    if any((pos-other).length < .74*(radius+other_radius) for other,other_radius in curl_samples):
        continue
    curl_samples.append((pos,radius))
    i=len(curl_samples)
    obj = uv('Rizo irregular %03d' % i, pos,
             (radius*random.uniform(.90,1.12),radius*random.uniform(.86,1.03),radius*random.uniform(.91,1.14)),
             random.choice(hair_mats),HAIR,28,18)
    obj.rotation_euler=(random.uniform(-.8,.8),random.uniform(-.8,.8),a)

# Cover the scalp edge with curls; a random interior distribution alone leaves
# an unnaturally straight visible band along the forehead.
for i in range(17):
    a=-math.pi+(i+.5)*math.pi/17
    front=max(0,-math.sin(a))
    p=2.13-1.15*front**.65+.075*math.cos(a)-.035
    pos=Vector((.785*math.sin(p)*math.cos(a),.065+.65*math.sin(p)*math.sin(a),5.46+.75*math.cos(p)))
    if any((pos-other).length < .115 for other,other_radius in curl_samples):
        continue
    radius=random.uniform(.135,.153)
    obj=uv('Rizo del nacimiento %02d' % i,pos,(radius,radius*.91,radius*1.05),random.choice(hair_mats),HAIR,28,18)
    obj.rotation_euler=(random.uniform(-.4,.4),random.uniform(-.4,.4),a)

# Narrower face and less oversized head, keeping all attached features aligned.
pivot=Vector((0,0,4.48))
head_transform=Matrix.Translation(pivot) @ Matrix.Diagonal((.89,.94,.91,1)) @ Matrix.Translation(-pivot)
for coll in [HEAD,HAIR]:
    for obj in coll.objects:
        if obj.name != 'Cuello':
            obj.matrix_world=head_transform @ obj.matrix_world


# Hoodie shell, ribbing, shaped hood and sewn kangaroo pocket.
torso = [
    (2.24,.67,.35,0,.03),(2.28,.73,.40,0,.025),(2.42,.81,.445,0,.02),
    (2.66,.85,.475,0,.02),(3.02,.83,.46,0,.03),(3.40,.805,.435,0,.035),
    (3.74,.83,.405,0,.04),(3.98,.91,.37,0,.05),(4.13,.81,.33,0,.06),
    (4.25,.54,.28,0,.06),(4.28,.37,.23,0,.06),
]
# Densify the torso before adding subtle longitudinal fabric folds.
dense_torso=[]
for i in range(len(torso)-1):
    for k in range(4):
        t=k/4
        dense_torso.append(tuple(torso[i][j]*(1-t)+torso[i+1][j]*t for j in range(5)))
dense_torso.append(torso[-1])
body=loft('Sudadera · cuerpo',dense_torso,hoodie,CLOTHES,steps=64,wrinkles=.008)
for vertex in body.data.vertices:
    x,y,z=vertex.co
    if y < -.12:
        fold_x=.37+.14*(4.15-z)
        fold=-.018*math.exp(-((abs(x)-fold_x)/.045)**2)*math.exp(-((z-3.72)/.38)**2)
        hem=.012*math.sin(21*x+.5)*math.exp(-((z-2.42)/.18)**2)
        vertex.co.y-=fold+hem

for vertex in body.data.vertices:
    if vertex.co.z > 4.0 and vertex.co.y < 0:
        vertex.co.z -= (vertex.co.z - 4.0) * .8 * min(1, -vertex.co.y / .2)
loft('Cintura elástica', [(2.18,.69,.36,0,.035),(2.20,.725,.39,0,.035),(2.34,.755,.407,0,.035),(2.38,.75,.4,0,.035)], rib, CLOTHES, subdiv=2)
for j in range(90):
    a = math.tau*j/90
    tube('Canalé cintura %02d' % j, [(.730*math.cos(a),.035+.394*math.sin(a),2.215),(.748*math.cos(a),.035+.405*math.sin(a),2.33)], .0025, seam, CLOTHES, 1)

# A broad folded fabric collar with a V-shaped front replaces the padded torus.
verts,faces=[],[]
N,STRIPS=64,9
inner_edge=[]
for j in range(N):
    a=math.tau*j/N
    front=max(0,-math.sin(a))
    back=max(0,math.sin(a))
    inner=Vector(((.30+.10*back)*math.cos(a),.04+(.23+.05*back)*math.sin(a),
                  4.27+.16*back+.03*abs(math.cos(a))-.18*front**4))
    outer=Vector(((.72+.02*back)*math.cos(a),.04+(.39+.17*back)*math.sin(a),
                  4.20+.12*back+.10*abs(math.cos(a))-.23*front**4))
    inner_edge.append(tuple(inner))
    for k in range(STRIPS):
        t=k/(STRIPS-1)
        point=inner.lerp(outer,t)
        point.z+=(.12-.035*front)*math.sin(math.pi*t)
        point.y+=.012*math.sin(3*a)*math.sin(math.pi*t)
        verts.append(tuple(point))
for j in range(N):
    for k in range(STRIPS-1):
        faces.append((j*STRIPS+k,j*STRIPS+k+1,((j+1)%N)*STRIPS+k+1,((j+1)%N)*STRIPS+k))
hood=mesh('Capucha · cuello en V de tela doblada',verts,faces,hoodie,CLOTHES,2)
hood.data.materials.append(lining)
solid=hood.modifiers.new('Espesor tela capucha','SOLIDIFY')
solid.thickness=.032
solid.material_offset=1
loft('Capucha · bolsa posterior',
     [(3.73,.18,.065,0,.41),(3.79,.36,.12,0,.44),(3.98,.53,.17,0,.46),
      (4.16,.64,.19,0,.45),(4.29,.53,.20,0,.40),(4.36,.39,.19,0,.32)],
     hoodie,CLOTHES,steps=48,subdiv=2,wrinkles=.025)
tube('Borde interior de la capucha',inner_edge+[inner_edge[0]],.018,hoodie,CLOTHES,2)
for side in [-1,1]:
    uv('Ojal cordón',(side*.245,-.372,4.05),(.045,.015,.047),rib,CLOTHES,16,10)
    cordpts=[(side*.245,-.395,4.065),(side*.265,-.425,3.88),
             (side*.29,-.428,3.62),(side*.315,-.445,3.43)]
    tube('Cordón capucha',cordpts,.019,cordmat,CLOTHES,3)
    uv('Terminal cordón',(side*.315,-.445,3.425),(.021,.022,.057),rib,CLOTHES,16,10)


def torso_front(x,z, extra=.02):
    # Interpolate the torso cross section so seams remain on the fabric.
    for i in range(len(torso)-1):
        a,b = torso[i],torso[i+1]
        if a[0] <= z <= b[0]:
            t=(z-a[0])/(b[0]-a[0])
            rx=a[1]*(1-t)+b[1]*t
            ry=a[2]*(1-t)+b[2]*t
            cy=a[4]*(1-t)+b[4]*t
            return cy-ry*math.sqrt(max(.05,1-(x/rx)**2))-extra
    return -.42-extra

outline=[(-.65,2.42),(-.69,2.66),(-.54,2.98),(-.42,3.06),(.42,3.06),(.54,2.98),(.69,2.66),(.65,2.42)]
# Fill as concentric rings, keeping the patch slightly raised off the torso.
verts=[(0,torso_front(0,2.72,.045),2.72)]
boundary=[]
for i in range(len(outline)):
    a,b=outline[i],outline[(i+1)%len(outline)]
    for k in range(5):
        t=k/5
        boundary.append((a[0]*(1-t)+b[0]*t,a[1]*(1-t)+b[1]*t))
for ring in [.33,.66,1]:
    for x,z in boundary:
        xx=x*ring
        zz=2.72+(z-2.72)*ring
        verts.append((xx,torso_front(xx,zz,.025+.02*(1-ring)),zz))
faces=[]
L=len(boundary)
for j in range(L):
    faces.append((0,1+j,1+(j+1)%L))
for r in range(2):
    for j in range(L):
        faces.append((1+r*L+j,1+(r+1)*L+j,1+(r+1)*L+(j+1)%L,1+r*L+(j+1)%L))
patch=mesh('Bolsillo canguro · panel',verts,faces,hoodie,CLOTHES,1)
solid=patch.modifiers.new('Grosor de tela','SOLIDIFY')
solid.thickness=.014
for side in [-1,1]:
    coords=[(side*.43,3.045),(side*.535,2.97),(side*.675,2.69)]
    tube('Abertura bolsillo',[(x,torso_front(x,z,.036),z) for x,z in coords],.009,rib,CLOTHES)
    tube('Costura bolsillo',[(x,torso_front(x,z,.049),z) for x,z in [(side*.62,2.445),(side*.33,2.435),(0,2.435)]],.006,seam,CLOTHES,2)

# Sleeves sweep through a bent elbow into the kangaroo pocket.
def swept(name, rows, mat, target, steps=36):
    centers=[Vector(row[:3]) for row in rows]
    verts,faces=[],[]
    for i,row in enumerate(rows):
        tangent=(centers[min(i+1,len(rows)-1)]-centers[max(i-1,0)]).normalized()
        front=Vector((0,-1,0))
        front=(front-tangent*front.dot(tangent)).normalized()
        across=front.cross(tangent).normalized()
        for j in range(steps):
            a=math.tau*j/steps
            amount=1+.012*math.sin(5*a+i*.8)*math.sin(math.pi*i/(len(rows)-1))
            p=centers[i]+across*(row[3]*math.cos(a)*amount)+front*(row[4]*math.sin(a)*amount)
            verts.append(tuple(p))
    for i in range(len(rows)-1):
        for j in range(steps):
            faces.append((i*steps+j,i*steps+(j+1)%steps,(i+1)*steps+(j+1)%steps,(i+1)*steps+j))
    faces+=[tuple(range(steps-1,-1,-1)),tuple((len(rows)-1)*steps+j for j in range(steps))]
    return mesh(name,verts,faces,mat,target,2)

def sleeve(side):
    rows=[
        (side*.56,.065,4.05,.16,.20),(side*.65,.05,4.00,.28,.29),
        (side*.90,.02,3.80,.32,.32),(side*1.07,-.025,3.50,.32,.32),
        (side*1.17,-.09,3.13,.335,.33),(side*1.18,-.17,2.88,.33,.315),
        (side*1.10,-.27,2.72,.29,.285),(side*.94,-.37,2.73,.25,.255),
        (side*.80,-.35,2.80,.215,.225),(side*.74,-.33,2.84,.20,.208)]
    swept('Manga · codo doblado '+str(side),rows,hoodie,CLOTHES)
    cuffrows=[
        (side*.805,-.35,2.79,.199,.205),(side*.79,-.34,2.80,.213,.22),
        (side*.66,-.27,2.875,.191,.193),(side*.645,-.255,2.885,.176,.18)]
    swept('Puño en bolsillo '+str(side),cuffrows,rib,CLOTHES,32)


def capsule(name,a,b,radius,mat,target):
    a,b=Vector(a),Vector(b)
    obj=uv(name,(a+b)/2,(radius,radius,(b-a).length/2+radius),mat,target,16,12)
    obj.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler()
    return obj

for side in [-1,1]:
    sleeve(side)
    # Five distinct digits, palm and wrist; voxel union produces a single hand mesh.
    pieces=[]
    cx=side*1.035
    pieces.append(uv('Muñeca', (cx,-.237,2.24),(.115,.115,.145),skin,HANDS))
    pieces.append(uv('Palma', (cx,-.275,2.07),(.143,.086,.188),skin,HANDS))
    for j,(offset,length) in enumerate([(-.135,.185),(-.045,.25),(.045,.225),(.13,.16)]):
        base=(cx+side*offset,-.275,1.995)
        end=(cx+side*(offset*1.18),-.30,1.995-length)
        pieces.append(capsule('Dedo '+str(j),base,end,.032 if j<3 else .027,skin,HANDS))
    pieces.append(capsule('Pulgar',(cx-side*.10,-.28,2.13),(cx-side*.205,-.31,2.005),.055,skin,HANDS))
    bpy.ops.object.select_all(action='DESELECT')
    for obj in pieces: obj.select_set(True)
    bpy.context.view_layer.objects.active=pieces[0]
    bpy.ops.object.join()
    hand=bpy.context.object
    hand.name='Mano completa · '+('izquierda' if side==1 else 'derecha')
    remesh=hand.modifiers.new('Unión anatómica','REMESH')
    remesh.mode='VOXEL'
    remesh.voxel_size=.012
    bpy.ops.object.modifier_apply(modifier=remesh.name)
    smooth=hand.modifiers.new('Suavizar nudillos','SMOOTH')
    smooth.factor=.7
    smooth.iterations=4
    bpy.ops.object.modifier_apply(modifier=smooth.name)
    for poly in hand.data.polygons: poly.use_smooth=True
    # Full hand geometry is retained, tucked behind the pocket cloth.
    hand.rotation_euler=Vector((0,0,-1)).rotation_difference(Vector((-side*.80,.48,.22)).normalized()).to_euler()
    hand.location=(side*.605,-.20,2.84)


trouser_parts=[loft('Pantalón · cadera',[(1.68,.50,.29,0,.04),(1.9,.65,.35,0,.04),(2.18,.685,.37,0,.04),(2.27,.64,.34,0,.04)],pants,LEGS,subdiv=2)]
for side in [-1,1]:
    trouser_parts.append(loft('Pierna '+str(side),[(.32,.22,.235,side*.36,.06),(.42,.245,.255,side*.36,.06),(.78,.26,.27,side*.355,.05),(1.1,.275,.285,side*.35,.045),(1.42,.30,.31,side*.335,.045),(1.75,.34,.335,side*.32,.045),(1.96,.34,.33,side*.31,.04)],pants,LEGS,steps=32,subdiv=2,wrinkles=.008))
    uv('Zapatilla '+str(side),(side*.36,-.105,.245),(.267,.445,.218),shoe,LEGS,32,16)
    uv('Suela '+str(side),(side*.36,-.12,.102),(.275,.451,.078),sole,LEGS,32,12)
    for z,y in [(.385,-.21),(.37,-.28),(.344,-.35)]:
        tube('Cordón zapatilla',[(side*.36-.10,y,z),(side*.36,y-.013,z+.014),(side*.36+.10,y,z)],.012,sole,LEGS,2)

bpy.ops.object.select_all(action='DESELECT')
for obj in trouser_parts:
    obj.select_set(True)
    bpy.context.view_layer.objects.active=obj
    bpy.ops.object.convert(target='MESH')
bpy.context.view_layer.objects.active=trouser_parts[0]
bpy.ops.object.join()
trousers=bpy.context.object
trousers.name='Pantalón · malla continua'
modifier=trousers.modifiers.new('Unir cadera y piernas','REMESH')
modifier.mode='VOXEL'
modifier.voxel_size=.024
bpy.ops.object.modifier_apply(modifier=modifier.name)
modifier=trousers.modifiers.new('Suavizar unión','SMOOTH')
modifier.factor=.75
modifier.iterations=6
bpy.ops.object.modifier_apply(modifier=modifier.name)
for poly in trousers.data.polygons: poly.use_smooth=True

# An embedded reference is available in the .blend without modifying the source.
reference_path=Path(r'C:\Users\dcard\Downloads\ChatGPT Image Sep 9, 2026, 02_28_10 PM.png')
if reference_path.exists():
    reference=bpy.data.images.load(str(reference_path))
    reference.pack()
    reference.name='Referencia original · no es textura del modelo'

scene=bpy.context.scene
scene.render.engine='CYCLES'
scene.cycles.samples=48
scene.cycles.use_denoising=True
scene.render.resolution_x=1100
scene.render.resolution_y=1100
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.render.image_settings.color_mode='RGBA'
scene.render.film_transparent=False
scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.075,.08,.10,1)
scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.45
scene.view_settings.view_transform='AgX'

def aim(obj,point):
    obj.rotation_euler=(Vector(point)-obj.location).to_track_quat('-Z','Y').to_euler()

def area(name,location,power,color,size):
    data=bpy.data.lights.new(name,'AREA')
    data.energy=power
    data.color=color
    data.shape='DISK'
    data.size=size
    obj=bpy.data.objects.new(name,data)
    STUDIO.objects.link(obj)
    obj.location=location
    aim(obj,(0,0,3.8))

area('Luz principal · softbox',(-3,-5,8),650,(1,.96,.92),5)
area('Relleno neutro',(4,-3,5),300,(.88,.94,1),4)
area('Contraluz rosa',(1,3,6),450,(1,.72,.64),3)
area('Luz superior',(-1,1,9),450,(1,.96,.91),3)
floor_mat=material('Estudio · fondo oscuro',(.018,.02,.029),.92)
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,.015))
floor=finish(bpy.context.object,floor_mat,STUDIO)
floor.name='Suelo de estudio'
data=bpy.data.cameras.new('Cámara retrato')
camera=bpy.data.objects.new('Cámara retrato',data)
STUDIO.objects.link(camera)
scene.camera=camera
data.type='ORTHO'
data.lens=65
data.ortho_scale=4.7
camera.location=(-11,-12,5.65)
aim(camera,(0,0,4.23))
scene['Estado']='ESTUDIO DE MODELADO V2 · sin rig ni clips; pendiente de aprobación visual'
scene['Referencia']='Retrato del usuario: pelo rizado negro, piel cálida y sudadera grafito'
scene['Orientación']='Blender Z arriba, frente -Y; exportación glTF Y arriba y frente +Z'
scene['Próxima etapa']='Revisar parecido, luego añadir esqueleto, pesos y clips Idle/Wave'
for obj in bpy.context.selected_objects: obj.select_set(False)
for screen in bpy.data.screens:
    for area_ui in screen.areas:
        if area_ui.type=='VIEW_3D':
            area_ui.spaces.active.region_3d.view_perspective='CAMERA'

bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'avatar-model-v2.blend'))

def render(name,location,target,scale,width=1100,height=1100):
    camera.location=location
    aim(camera,target)
    data.ortho_scale=scale
    scene.render.resolution_x=width
    scene.render.resolution_y=height
    scene.render.filepath=str(OUT/name)
    bpy.ops.render.render(write_still=True)

render('portrait.png',(-11,-12,5.65),(0,0,4.23),4.7)
render('reference-view.png',(-11,-12,5.65),(0,0,4.23),8.35,1672,941)
render('front.png',(0,-12,4.3),(0,0,3.28),7.05,900,1100)
render('side.png',(-12,-.4,4.3),(0,0,3.28),7.05,900,1100)

# Optimize only the exported copy; keep all editable objects in the .blend.
runpy.run_path(str(ROOT/'scripts'/'export-avatar-model-v2.py'), run_name='__main__')
print('AVATAR_OUTPUT',OUT)
