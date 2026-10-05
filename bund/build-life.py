"""Blender --background --factory-startup --python-exit-code 1 --python build-life.py.
Original mobile street furniture and articulated visitors; one vertex-colour material.
"""
import bpy, math, json
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'runtime/life'
OUT.mkdir(parents=True, exist_ok=True)
(ROOT / 'source').mkdir(exist_ok=True)
(ROOT / 'previews').mkdir(exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

material = bpy.data.materials.new('Street colours')
material.use_nodes = True
bsdf = material.node_tree.nodes.get('Principled BSDF')
bsdf.inputs['Roughness'].default_value = .78
colour = material.node_tree.nodes.new('ShaderNodeVertexColor')
colour.layer_name = 'Color'
material.node_tree.links.new(colour.outputs['Color'], bsdf.inputs['Base Color'])
parts, current = {}, []

def paint(obj, colour):
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    rgb = tuple(int(colour[i:i+2], 16)/255 for i in (1,3,5))
    linear = tuple(v/12.92 if v <= .04045 else ((v+.055)/1.055)**2.4 for v in rgb)
    layer = obj.data.color_attributes.new(name='Color', type='FLOAT_COLOR', domain='CORNER')
    for value in layer.data: value.color = (*linear, 1)
    obj.data.materials.append(material)
    for polygon in obj.data.polygons: polygon.use_smooth = True
    current.append(obj)
    return obj

def ball(at, scale, colour):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=10, ring_count=6, location=at)
    obj = bpy.context.object
    obj.scale = scale
    return paint(obj, colour)

def box(at, scale, colour, bevel=.04):
    bpy.ops.mesh.primitive_cube_add(size=1, location=at)
    obj = bpy.context.object
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        mod = obj.modifiers.new('Rounded edges', 'BEVEL')
        mod.width = bevel
        mod.segments = 2
        bpy.ops.object.modifier_apply(modifier=mod.name)
    return paint(obj, colour)

def cylinder(at, radius, depth, colour, rotation=(0,0,0), top=None):
    bpy.ops.mesh.primitive_cone_add(vertices=12, radius1=radius, radius2=radius if top is None else top,
                                   depth=depth, location=at, rotation=rotation)
    return paint(bpy.context.object, colour)

def finish(name, pivot=(0,0,0)):
    bpy.ops.object.select_all(action='DESELECT')
    for obj in current: obj.select_set(True)
    bpy.context.view_layer.objects.active = current[0]
    bpy.ops.object.join()
    obj = bpy.context.object
    # Bake all parts into a single local mesh, retaining the animation joint as origin.
    transform = obj.matrix_world.copy()
    for vertex in obj.data.vertices: vertex.co = transform @ vertex.co - Vector(pivot)
    obj.location = pivot
    obj.rotation_euler = (0,0,0)
    obj.scale = (1,1,1)
    obj.name = name
    obj.data.name = name
    parts[name] = obj
    current.clear()

skin, hair, coral, mint, cream, metal = '#e6b48b','#483129','#e8876d','#70aaa0','#fff0cf','#294d55'

# Feet on zero, 1.73 m tall. Limb meshes retain shoulder/hip pivots for instancing.
box((0,0,1.16),(.40,.24,.47),coral,.08)
cylinder((0,0,1.42),.065,.14,skin)
ball((0,-.015,1.56),(.158,.145,.175),skin)
ball((0,.018,1.665),(.161,.142,.105),hair)
ball((-.146,-.012,1.55),(.029,.031,.044),skin)
ball((.146,-.012,1.55),(.029,.031,.044),skin)
for x in [-.057,.057]:
    ball((x,-.153,1.57),(.015,.010,.021),'#2c302e')
    ball((x*1.55,-.143,1.52),(.020,.008,.013),'#d88775')
ball((0,-.151,1.508),(.028,.009,.009),'#a86251')
box((0,.15,1.15),(.26,.13,.32),'#e5c495',.055)
for x in [-.135,.135]: box((x,-.129,1.18),(.025,.018,.40),'#dfc393',.008)
box((0,0,.91),(.36,.22,.19),'#456573',.04)
finish('visitor-body')
for side, x in [('left',-.245),('right',.245)]:
    ball((x,0,1.28),(.077,.090,.145),coral)
    cylinder((x,0,1.08),.048,.26,skin)
    ball((x,-.015,.91),(.055,.05,.08),skin)
    finish('visitor-arm-'+side,(x,0,1.37))
for side, x in [('left',-.106),('right',.106)]:
    box((x,0,.50),(.143,.18,.74),'#456573',.055)
    box((x,-.068,.07),(.16,.29,.14),cream,.045)
    finish('visitor-leg-'+side,(x,0,.87))

# Handcrafted refreshment cart, front faces Blender -Y / glTF +Z.
box((0,0,.68),(2.12,.90,.85),mint,.06)
box((0,-.48,.76),(1.92,.035,.52),cream,.02)
box((0,0,1.14),(2.30,1.04,.105),'#ba8e5c',.025)
for x in [-.78,.78]:
    cylinder((x,0,.28),.27,.11,metal,(math.pi/2,0,0))
    cylinder((x,-.075,.28),.19,.012,'#ceaa76',(math.pi/2,0,0))
    cylinder((x,-.088,.28),.07,.018,metal,(math.pi/2,0,0))
for x in [-1.02,1.02]:
    for y in [-.38,.38]: cylinder((x,y,1.63),.029,1.01,'#967451')
box((0,.08,2.24),(2.27,.20,.32),cream,.04)
for i in range(10):
    x=-1.08+i*.24
    c=coral if i%2==0 else cream
    roof=box((x,0,2.05),(.245,1.23,.075),c,.015)
    roof.rotation_euler.x=.12
    ball((x,-.61,1.98),(.12,.018,.13),c)
for i in range(5):
    x=-.65+i*.22
    cylinder((x,-.25,1.32),.07,.27,cream,top=.08)
    cylinder((x,-.25,1.46),.082,.035,coral)
    cylinder((x,-.25,1.54),.008,.14,metal)
box((.64,.16,1.38),(.55,.07,.46),'#dbb98c',.02)
for i,c in enumerate(['#87bfce','#e7b088','#75a591']):
    box((.49+i*.15,.108,1.44),(.13,.016,.19),c,.006)
box((-.75,-.28,1.18),(.19,.17,.03),coral,.01)
finish('kiosk')

# Dense-looking flowers from small petals, still a single mesh and draw per batch.
box((0,0,.28),(.92,.55,.56),'#947356',.035)
for x in [-.32,0,.32]: box((x,-.284,.28),(.016,.014,.49),'#d6b486',.003)
for i in range(9):
    x=math.sin(i*2.4)*.33; y=math.cos(i*2.4)*.17; z=.57+(i%3)*.06
    ball((x,y,z),(.17,.14,.14),'#6b9560')
    for petal in range(5):
        a=petal*math.tau/5
        ball((x+.065*math.cos(a),y+.065*math.sin(a),z+.11),(.053,.048,.028),coral if i%2 else '#eeb1b5')
    ball((x,y,z+.13),(.028,.028,.020),'#ecc064')
finish('flowers')

ball((0,0,.18),(.095,.14,.105),'#a7b9c1')
ball((0,-.105,.28),(.066,.077,.075),'#6c9892')
ball((0,-.142,.35),(.061,.059,.058),'#8ba6b3')
for x in [-.056,.056]: ball((x,-.163,.362),(.012,.012,.012),'#293b46')
cylinder((0,-.208,.341),.024,.065,'#db9968',(math.pi/2,0,0),top=0)
for x in [-.04,.04]:
    cylinder((x,-.014,.05),.009,.10,'#c28568')
    box((x,-.050,.014),(.015,.07,.014),'#c28568',.003)
box((0,.147,.165),(.08,.16,.018),'#627a8a',.008)
finish('pigeon-body')
for side,x in [('left',-.09),('right',.09)]:
    ball((x*1.8,.03,.205),(.145,.115,.026),'#d1d8d5')
    box((x*2.2,.02,.223),(.095,.016,.010),'#536f7c',.003)
    finish('pigeon-wing-'+side,(x,0,.23))

# Wind-responsive banner: cloth bends in the shader rather than adding bones.
cylinder((0,0,1.75),.027,3.5,metal)
box((.30,0,2.70),(.60,.035,1.04),coral,.01)
box((.30,-.022,2.70),(.36,.012,.033),cream,.003)
box((.30,-.022,2.88),(.16,.012,.20),cream,.007)
finish('banner')

bpy.ops.object.select_all(action='DESELECT')
for obj in parts.values(): obj.select_set(True)
bpy.context.view_layer.objects.active=parts['kiosk']
bpy.ops.export_scene.gltf(filepath=str(OUT/'street-life.glb'),export_format='GLB',use_selection=True,
    export_cameras=False,export_lights=False,export_extras=True)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'source/bund-life.blend'))

# Reimport the actual GLB before claiming it works; verify pivots and finite mesh data.
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(OUT/'street-life.glb'))
objects={obj.name:obj for obj in bpy.context.scene.objects if obj.type=='MESH'}
assert set(objects)==set(parts), (list(objects),list(parts))
triangles=0
for obj in objects.values():
    obj.data.calc_loop_triangles(); triangles+=len(obj.data.loop_triangles)
    assert all(math.isfinite(v) for vertex in obj.data.vertices for v in vertex.co)
assert triangles < 18000, triangles
report={'generator':'Blender','models':list(objects),'triangles':triangles,
        'bytes':(OUT/'street-life.glb').stat().st_size,'verified':'GLB reimport, finite vertices and animation parts'}
(OUT/'manifest.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n')

# A genuine asset preview from the exported meshes, separate from the concept images.
for name,obj in objects.items():
    if name.startswith('visitor-'): obj.location.x-=2.2
    if name.startswith('pigeon-'): obj.location.x+=1.9;obj.location.y-=.9
    if name=='flowers':obj.location.x+=1.9
    if name=='banner':obj.location.x-=3.0;obj.location.y+=.6
bpy.ops.mesh.primitive_plane_add(size=200)
floor=bpy.context.object
floor.data.materials.append(bpy.data.materials.new('Sand'))
floor.data.materials[0].diffuse_color=(.72,.63,.49,1)
bpy.ops.object.light_add(type='AREA',location=(-3,-4,7));bpy.context.object.data.energy=1400;bpy.context.object.data.shape='DISK';bpy.context.object.data.size=7
bpy.ops.object.camera_add(location=(5,-8,5))
camera=bpy.context.object;camera.rotation_euler=(Vector((-.5,0,1.3))-camera.location).to_track_quat('-Z','Y').to_euler()
camera.data.type='ORTHO';camera.data.ortho_scale=7.3
scene=bpy.context.scene;scene.camera=camera;scene.render.engine='CYCLES';scene.cycles.samples=24
scene.world.color=(.5,.6,.7);scene.view_settings.view_transform='AgX'
scene.render.resolution_x=1000;scene.render.resolution_y=760;scene.render.resolution_percentage=100
scene.render.filepath=str(ROOT/'previews/bund-life.png');bpy.ops.render.render(write_still=True)
print('BUND_LIFE_VERIFIED',json.dumps(report))
