"""Build an editable stylized character study from the supplied portrait.

Run with Blender --background --factory-startup --python scripts/create-avatar-model.py
Outputs are isolated from the live website and contain no rig or animation yet.
"""
import bpy
import math
import random
import runpy
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'models' / 'avatar-v1'
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
    shader.inputs['Specular IOR Level'].default_value = .3
    if skin:
        shader.inputs['Subsurface Weight'].default_value = .07
        shader.inputs['Subsurface Radius'].default_value = (1, .45, .25)
    if fabric:
        shader.inputs['Sheen Weight'].default_value = .18
        noise = nodes.new('ShaderNodeTexNoise')
        noise.inputs['Scale'].default_value = 190
        noise.inputs['Detail'].default_value = 2
        bump = nodes.new('ShaderNodeBump')
        bump.inputs['Strength'].default_value = .13
        bump.inputs['Distance'].default_value = .014
        mat.node_tree.links.new(noise.outputs['Fac'], bump.inputs['Height'])
        mat.node_tree.links.new(bump.outputs['Normal'], shader.inputs['Normal'])
    return mat

skin = material('Piel · melocotón cálido', (.66, .255, .135), .52, skin=True)
skin_inner = material('Piel · interior oreja', (.54, .215, .135), .66, skin=True)
nose_mat = material('Piel · nariz', (.69, .29, .155), .55, skin=True)
black = material('Ojos y sonrisa · carbón', (.012, .009, .009), .55)
hair_mats = [material('Rizos · tono %02d' % i, (.005 + i*.0006, .0045 + i*.0006, .004 + i*.0006), .76) for i in range(5)]
hoodie = material('Sudadera · grafito', (.032, .039, .049), .86, fabric=True)
rib = material('Puños y cintura · canalé', (.025, .03, .039), .89, fabric=True)
lining = material('Capucha · interior', (.039, .044, .052), .94, fabric=True)
seam = material('Costura · grafito suave', (.038, .044, .055), .89)
cordmat = material('Cordones · gris', (.043, .052, .065), .82)
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
    (4.48, .10, .13, 0, -.01), (4.53, .29, .29, 0, -.01),
    (4.63, .48, .42, 0, -.025), (4.80, .65, .535, 0, -.025),
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
    uv('Oreja ' + str(side), (side*.765, .015, 5.04), (.19,.125,.245), skin, HEAD)
    uv('Pliegue oreja ' + str(side), (side*.84,-.084,5.05), (.071,.025,.126), skin_inner, HEAD)
    eye = uv('Ojo ' + str(side), (side*.262,face_y(side*.262,5.33,.014),5.33), (.049,.036,.098), black, HEAD)
    eye.rotation_euler.y = side * -.095
    brow = [(side*.11,-.631,5.57), (side*.24,-.620,5.605), (side*.38,-.578,5.575)]
    brow = [(x,face_y(x,z,.020),z) for x,y,z in brow]
    tube('Ceja ' + str(side), brow, .047, black, HEAD, 4)
    for endpoint in [brow[0], brow[-1]]:
        uv('Extremo suave ceja', endpoint, (.047,.047,.047), black, HEAD, 12, 8)
uv('Nariz redondeada', (0,-.672,5.08), (.117,.133,.125), nose_mat, HEAD)
smile_points = [(-.19,-.568,4.885),(-.105,-.601,4.850),(0,-.613,4.835),(.105,-.601,4.850),(.19,-.568,4.885)]
smile_points = [(x,face_y(x,z,.006),z) for x,y,z in smile_points]
tube('Sonrisa sutil', smile_points, .0175, black, HEAD, 4)
for endpoint in [smile_points[0], smile_points[-1]]:
    uv('Extremo suave sonrisa', endpoint, (.0175,.0175,.0175), black, HEAD, 12, 8)

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
for row, (polar, count) in enumerate([(.12,5),(.43,11),(.73,16),(1.02,20),(1.30,23),(1.59,24),(1.87,25),(2.08,25)]):
    for j in range(count):
        azimuth = math.tau*(j+.45*(row%2))/count
        front = max(0, -math.sin(azimuth))
        limit = 2.13 - 1.15 * front**.65
        if polar > limit + .07:
            continue
        p = polar + random.uniform(-.06,.06)
        a = azimuth + random.uniform(-.055,.055)
        pos = (.79*math.sin(p)*math.cos(a), .065+.66*math.sin(p)*math.sin(a), 5.46+.76*math.cos(p))
        radius = random.uniform(.145,.19)
        obj = uv('Rizo %02d-%02d' % (row,j), pos, (radius, radius*.84, radius*1.12), random.choice(hair_mats), HAIR, 16, 12)
        obj.rotation_euler = (random.uniform(-.3,.3), random.uniform(-.4,.4), a)

# Hoodie shell, ribbing, shaped hood and sewn kangaroo pocket.
torso = [
    (2.24,.67,.35,0,.03),(2.28,.73,.40,0,.025),(2.42,.81,.445,0,.02),
    (2.66,.85,.475,0,.02),(3.02,.83,.46,0,.03),(3.40,.805,.435,0,.035),
    (3.74,.83,.405,0,.04),(3.98,.91,.37,0,.05),(4.13,.81,.33,0,.06),
    (4.25,.54,.28,0,.06),(4.28,.37,.23,0,.06),
]
body = loft('Sudadera · cuerpo', torso, hoodie, CLOTHES, wrinkles=.012)
for vertex in body.data.vertices:
    if vertex.co.z > 4.0 and vertex.co.y < 0:
        vertex.co.z -= (vertex.co.z - 4.0) * .8 * min(1, -vertex.co.y / .2)
loft('Cintura elástica', [(2.18,.69,.36,0,.035),(2.20,.725,.39,0,.035),(2.34,.755,.407,0,.035),(2.38,.75,.4,0,.035)], rib, CLOTHES, subdiv=2)
for j in range(90):
    a = math.tau*j/90
    tube('Canalé cintura %02d' % j, [(.730*math.cos(a),.035+.394*math.sin(a),2.215),(.748*math.cos(a),.035+.405*math.sin(a),2.33)], .0025, seam, CLOTHES, 1)

# Hood as a fabric tube following a sloped neckline: raised back, V at front.
verts, faces = [], []
N, CROSS = 64, 16
for j in range(N):
    a = math.tau*j/N
    front = max(0,-math.sin(a))
    back = max(0,math.sin(a))
    center = Vector((.53*math.cos(a), .08+.365*math.sin(a), 4.20+.245*back-.16*front**5))
    outward = Vector((math.cos(a),math.sin(a),0))
    thickness = .18+.075*back-.05*front
    for k in range(CROSS):
        t = math.tau*k/CROSS
        p = center + outward*(math.cos(t)*thickness) + Vector((0,0,math.sin(t)*(.17+.08*back)))
        verts.append(tuple(p))
for j in range(N):
    for k in range(CROSS):
        faces.append((j*CROSS+k,((j+1)%N)*CROSS+k,((j+1)%N)*CROSS+(k+1)%CROSS,j*CROSS+(k+1)%CROSS))
hood = mesh('Capucha · cuello doblado', verts, faces, hoodie, CLOTHES, 1)
hood.data.materials.append(lining)
for j in range(N):
    for k in range(CROSS):
        if 4 <= k <= 11:
            hood.data.polygons[j*CROSS+k].material_index = 1
uv('Capucha · pliegue posterior', (0,.36,4.13), (.61,.29,.46), hoodie, CLOTHES)
for side in [-1,1]:
    uv('Ojal cordón', (side*.22,-.425,4.02), (.056,.018,.057), rib, CLOTHES, 16, 10)
    cordpts = [(side*.22,-.452,4.04),(side*.245,-.46,3.88),(side*.23,-.445,3.66),(side*.255,-.46,3.36)]
    tube('Cordón capucha', cordpts, .020, cordmat, CLOTHES, 3)
    uv('Terminal cordón', (side*.255,-.46,3.35), (.023,.024,.066), rib, CLOTHES, 16, 10)

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

outline=[(-.58,2.46),(-.61,2.66),(-.47,2.95),(-.35,3.05),(.35,3.05),(.47,2.95),(.61,2.66),(.58,2.46)]
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
    coords=[(side*.36,3.035),(side*.47,2.935),(side*.59,2.67)]
    tube('Abertura bolsillo',[(x,torso_front(x,z,.036),z) for x,z in coords],.009,rib,CLOTHES)
    tube('Costura bolsillo',[(x,torso_front(x,z,.049),z) for x,z in [(side*.55,2.48),(side*.30,2.46),(0,2.46)]],.006,seam,CLOTHES,2)

# Sleeves follow a gently bent arm. One continuous surface avoids elbow seams.
def sleeve(side):
    levels=[
        (2.35,.18,.185,side*1.05,-.20),(2.45,.215,.215,side*1.09,-.15),
        (2.68,.27,.27,side*1.16,-.05),(2.90,.295,.285,side*1.18,.0),
        (3.10,.285,.29,side*1.14,.025),(3.36,.275,.295,side*1.07,.04),
        (3.62,.30,.31,side*.98,.055),(3.86,.325,.315,side*.86,.07),
        (4.02,.27,.28,side*.74,.08),(4.08,.15,.18,side*.69,.09),
    ]
    loft('Manga continua '+str(side),levels,hoodie,CLOTHES,steps=32,wrinkles=.018)
    loft('Puño '+str(side),[(2.25,.166,.17,side*1.035,-.235),(2.28,.188,.19,side*1.04,-.225),(2.44,.203,.205,side*1.075,-.165),(2.48,.19,.197,side*1.09,-.15)],rib,CLOTHES,steps=32,subdiv=2)
    for j in range(28):
        a=math.tau*j/28
        tube('Canalé puño',[(side*1.04+.190*math.cos(a),-.225+.193*math.sin(a),2.285),(side*1.075+.205*math.cos(a),-.165+.208*math.sin(a),2.43)],.0025,seam,CLOTHES,1)

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

area('Luz principal · softbox',(-3,-5,8),650,(1,.90,.82),5)
area('Relleno neutro',(4,-3,5),400,(.80,.88,1),4)
area('Contraluz rosa',(1,3,6),800,(1,.35,.46),3)
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
camera.location=(-6,-11,6.25)
aim(camera,(0,0,4.4))
scene['Estado']='ESTUDIO DE MODELADO V1 · sin rig ni clips; pendiente de aprobación visual'
scene['Referencia']='Retrato del usuario: pelo rizado negro, piel cálida y sudadera grafito'
scene['Orientación']='Blender Z arriba, frente -Y; exportación glTF Y arriba y frente +Z'
scene['Próxima etapa']='Revisar parecido, luego añadir esqueleto, pesos y clips Idle/Wave'
for obj in bpy.context.selected_objects: obj.select_set(False)
for screen in bpy.data.screens:
    for area_ui in screen.areas:
        if area_ui.type=='VIEW_3D':
            area_ui.spaces.active.region_3d.view_perspective='CAMERA'

bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'avatar-model-v1.blend'))

def render(name,location,target,scale,width=1100,height=1100):
    camera.location=location
    aim(camera,target)
    data.ortho_scale=scale
    scene.render.resolution_x=width
    scene.render.resolution_y=height
    scene.render.filepath=str(OUT/name)
    bpy.ops.render.render(write_still=True)

render('portrait.png',(-6,-11,6.25),(0,0,4.4),4.7)
render('front.png',(0,-12,4.3),(0,0,3.28),7.05,900,1100)
render('side.png',(-12,-.4,4.3),(0,0,3.28),7.05,900,1100)

# Optimize only the exported copy; keep all editable objects in the .blend.
runpy.run_path(str(ROOT/'scripts'/'export-avatar-model.py'), run_name='__main__')
print('AVATAR_OUTPUT',OUT)
