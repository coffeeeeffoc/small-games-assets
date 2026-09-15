"""Run with Blender --background --python this-file; exports shared, streaming web assets from the source scene."""
import bpy, json, math, shutil
from pathlib import Path
from mathutils import Vector

SOURCE = Path(__file__).resolve().parent
OUT = SOURCE / 'runtime' / 'world'
OUT.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(SOURCE / 'source/bund-environment.blend'))
objects = [o for c in bpy.data.collections if c.name[:2].isdigit() for o in c.objects if o.type == 'MESH']
assert len(objects) > 3000, 'Source scene collections changed'

def export(name, items):
    bpy.ops.object.select_all(action='DESELECT')
    for o in items: o.select_set(True)
    bpy.context.view_layer.objects.active = items[0]
    bpy.ops.export_scene.gltf(filepath=str(OUT / name), export_format='GLB', use_selection=True,
        export_extras=True, export_cameras=False, export_lights=False,
        # Preserve centimeter-scale walkable heights across the kilometer-wide terrain.
        export_draco_mesh_compression_enable=name.startswith('city_'), export_draco_mesh_compression_level=6,
        export_draco_position_quantization=20)

def xyz(v): return [round(v.x, 4), round(v.z, 4), round(-v.y, 4)]
def box(o, low=None, high=None):
    vs = [v.co for v in o.data.vertices]
    lo = Vector(tuple(min(v[i] for v in vs) for i in range(3))) if low is None else Vector(low)
    hi = Vector(tuple(max(v[i] for v in vs) for i in range(3))) if high is None else Vector(high)
    center = o.matrix_world @ ((lo + hi) / 2)
    half = (hi - lo) / 2
    return {'position': xyz(center), 'half': [round(half.x * abs(o.scale.x),4), round(half.z * abs(o.scale.z),4), round(half.y * abs(o.scale.y),4)], 'yaw': round(o.rotation_euler.z,6)}

colliders, benches, landmarks, props, static, terrain = [], [], [], {}, [], []
promenades=[o for o in objects if o.name.startswith('promenade-section')]
open_deck=None
water = None
for o in objects:
    name = o.name.split('.')[0]
    group = o.users_collection[0].name[:2]
    if group == '05':
        if name == 'huangpu-suzhou-water': water = o
        else: terrain.append(o)
        continue
    if group in ('01','02','03','04'):
        static.append(o)
        # ponytail: exterior envelope colliders; replace with authored concave shells if interiors open.
        colliders.append(box(o))
        if group != '04': landmarks.append({'id':name,'name':o.get('label_zh',name),'position':xyz(o.location)})
        continue
    if group != '06': continue
    if name == 'promenade-section':
        forward=Vector((math.cos(o.rotation_euler.z),math.sin(o.rotation_euler.z),0))
        outward=Vector((-forward.y,forward.x,0))
        # Parallel road ways generated two adjacent strips; only the outer strip needs a railing.
        inner=any(3 < (p.location-o.location).dot(outward) < 10 and abs((p.location-o.location).dot(forward)) < 7
                  and abs(p.rotation_euler.z-o.rotation_euler.z)<.2 for p in promenades if p!=o)
        if inner:
            name='promenade-open'
            if open_deck is None:
                faces=[p for p in o.data.polygons if all(o.data.vertices[i].co.z <= .64 for i in p.vertices)]
                mesh=bpy.data.meshes.new('open-deck');mesh.from_pydata([v.co for v in o.data.vertices],[],[list(p.vertices) for p in faces])
                for m in o.data.materials:mesh.materials.append(m)
                for dest,src in zip(mesh.polygons,faces):dest.material_index=src.material_index
                open_deck=bpy.data.objects.new('promenade-open',mesh);bpy.context.scene.collection.objects.link(open_deck)
    props.setdefault(name, []).append({'position':xyz(o.location),'scale':[o.scale.x,o.scale.z,o.scale.y],'yaw':o.rotation_euler.z})
    if name in ('promenade-section','promenade-open'):
        colliders.append(box(o,(-6,-4,0),(6,4,.62)))
        if name == 'promenade-section':colliders.append(box(o,(-6,3.45,.6),(6,3.9,1.98)))
    elif name == 'garden-bridge':
        colliders.append(box(o,(-14,-3.5,-.2),(14,3.5,.2)))
        for side in [-1,1]: colliders.append(box(o,(-14,side*3.3-.15,.1),(14,side*3.3+.15,1.3)))
        # Bridge's raised deck needs visible approach ramps, added in runtime with matching colliders.
    elif name == 'plane-tree-planter': colliders.append(box(o,(-.45,-.45,0),(.45,.45,3)))
    elif name == 'riverside-lamp': colliders.append(box(o,(-.2,-.2,0),(.2,.2,3.8)))
    elif name == 'wooden-bench':
        colliders.append(box(o,(-1.2,-.38,0),(1.2,.38,1.35)))
        seat = o.matrix_world @ Vector((0,-.8,0))
        benches.append({'position':xyz(seat), 'yaw':o.rotation_euler.z + math.pi})
    elif name not in ('huangpu-cruise-boat','city-car','city-bus'): colliders.append(box(o))

assert water is not None
surfaces=[]
for o in terrain:
    if o.name != 'street-network': continue
    vertices=[o.matrix_world @ v.co for v in o.data.vertices]
    assert len(vertices)%4==0
    for i in range(0,len(vertices),4):
        a,b,c,d=vertices[i:i+4]
        center=(a+b+c+d)/4
        height=center.z
        surfaces.append({'position':xyz(Vector((center.x,center.y,height/2))),
            'half':[(b-a).length/2,height/2,(d-a).length/2],
            'yaw':math.atan2(b.y-a.y,b.x-a.x)})
    # Add the side walls to the runtime road, so the visible curb matches its solid collider.
    verts=[]; faces=[]; slots=[]
    for i in range(0,len(vertices),4):
        v=vertices[i:i+4]; off=len(verts)
        verts += [(p.x,p.y,0) for p in v]+[tuple(p) for p in v]
        faces += [tuple(off+j for j in f) for f in [(4,5,6,7),(0,3,2,1),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]]
        slots += [o.data.polygons[i//2].material_index]*6
    mesh=bpy.data.meshes.new('solid-roads');mesh.from_pydata(verts,[],faces)
    for m in o.data.materials:mesh.materials.append(m)
    for face,slot in zip(mesh.polygons,slots):face.material_index=slot
    o.data=mesh
# Parks use closed convex triangular prisms; internal seams are coplanar.
park_hulls=[]
for o in terrain:
    if o.name != 'riverside-parks': continue
    o.data.calc_loop_triangles()
    for tri in o.data.loop_triangles:
        v=[o.matrix_world @ o.data.vertices[i].co for i in tri.vertices]
        park_hulls.append([xyz(Vector((p.x,p.y,h))) for h in [0,.55] for p in v])
export('terrain.glb', terrain)
export('water.glb', [water])
# Each material is merged within a 250 m tile, preserving useful view frustum culling.
tiles = {}
for o in static:
    key = (math.floor(o.location.x/250), math.floor(o.location.y/250))
    # Context objects store world vertices with identity transforms.
    if o.name.startswith('osm-'):
        center = sum((o.matrix_world @ Vector(v) for v in o.bound_box),Vector())/8
        key = (math.floor(center.x/250), math.floor(center.y/250))
    tiles.setdefault(key, []).append(o)
tile_data=[]
for key, members in tiles.items():
    bpy.ops.object.select_all(action='DESELECT')
    for o in members: o.select_set(True)
    bpy.context.view_layer.objects.active = members[0]
    bpy.ops.object.join()
    obj=bpy.context.view_layer.objects.active; obj.name=f'city_{key[0]}_{key[1]}'
    bounds=[obj.matrix_world @ Vector(v) for v in obj.bound_box]
    low=Vector(tuple(min(v[i] for v in bounds) for i in range(3)))
    high=Vector(tuple(max(v[i] for v in bounds) for i in range(3)))
    tile_data.append({'name':obj.name,'center':xyz((low+high)/2),'radius':(high-low).length/2})
    export(obj.name+'.glb',[obj])
for name in props:
    if name == 'promenade-open':export('promenade-open.glb',[open_deck])
    else:shutil.copy2(SOURCE / 'models' / f'{name}.glb', OUT / f'{name}.glb')

# Water triangles are shared with runtime shore exclusion, in the same world coordinates.
water.data.calc_loop_triangles()
water_triangles = [[xyz(water.matrix_world @ water.data.vertices[i].co)[::2] for i in tri.vertices] for tri in water.data.loop_triangles]
data={'colliders':colliders,'benches':benches,'landmarks':landmarks,'props':props,'water':water_triangles,'bounds':[-950,-1630,2550,1840],'tiles':tile_data,'surfaces':surfaces,'parkHulls':park_hulls}
(OUT/'world.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
shutil.copy2(SOURCE/'reference/ATTRIBUTION.md',OUT/'ATTRIBUTION.md')
print('RUNTIME_EXPORT_OK',json.dumps({'tiles':len(tiles),'colliders':len(colliders),'benches':len(benches),'props':sum(map(len,props.values()))}))


# Draco decoders are vendored once in runtime/draco (Apache-2.0).
