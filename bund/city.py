"""Build the Bund from a pinned OSM extract and individually modeled landmarks."""
import json
import math
import random
import sys
from xml.sax.saxutils import escape
from pathlib import Path
import bpy
from mathutils import Vector
from mathutils.geometry import tessellate_polygon
import geography as geo
import architecture as buildings
from geometry import *

data=json.loads((ROOT/'reference/osm-extract.json').read_text(encoding='utf-8'))
pois=json.loads((ROOT/'reference/osm-pois.json').read_text(encoding='utf-8'))
elements={(e['type'],e['id']):e for e in data['elements']+pois['elements']}
specs=json.loads((ROOT/'landmarks.json').read_text(encoding='utf-8'))
metadata={}; placements=[]; mapped=[]
for element in elements.values():
    if element.get('tags',{}).get('building'):
        for poly in geo.rings(element):
            poly=geo.clip(poly)
            if len(poly)>=3 and abs(geo.area(poly))>12: mapped.append((element,poly))

def resolve(spec):
    if spec.get('osm'):
        return elements[(spec.get('osm_type','way'),spec['osm'])]
    matches=[e for e in elements.values() if e.get('tags',{}).get('addr:housenumber')==spec['address']
             and e.get('tags',{}).get('addr:street')=='中山东一路']
    assert len(matches)==1,(spec['id'],len(matches))
    return matches[0]

def fit(obj,width,depth,height):
    bpy.context.view_layer.update()
    size=obj.dimensions.copy()
    assert min(size)>0,obj.name
    for vertex in obj.data.vertices:
        vertex.co.x*=width/size.x; vertex.co.y*=depth/size.y; vertex.co.z*=height/size.z
    obj.data.update()

for spec in specs:
    e=resolve(spec); tags=e.get('tags',{})
    footprint=max(geo.rings(e),key=lambda p:abs(geo.area(p)))
    historic=spec['kind'] in ['heritage','church'] or spec['id'] in ['hsbc-building','customs-house','peace-hotel']
    pos,w,d,angle=geo.rectangle(footprint,historic)
    h,source=geo.height(tags)
    if 'height' in spec:
        h=spec['height']; source=spec.get('height_source','OSM height' if str(tags.get('height'))==str(h) else 'specified approximate height')
    spec.setdefault('floors',int(geo.number(tags.get('building:levels'),6)))
    spec.update(model_width=spec.get('width',w)*.94,model_depth=spec.get('depth',d)*.94,model_height=h)
    if spec['id']=='peace-hotel':
        bpy.data.objects.remove(ASSETS[spec['id']],do_unlink=True)
        spec['kind']='peace'
    obj=ASSETS[spec['id']] if spec['kind']=='existing' else getattr(buildings,spec['kind'])(spec)
    fit(obj,spec.get('width',w)*.94,spec.get('depth',d)*.94,h)
    obj['osm_url']=f"https://www.openstreetmap.org/{e['type']}/{e['id']}"
    obj['height_source']=source
    obj['style']='Architectural exterior interpretation; georeferenced placement; not a measured facade'
    metadata[spec['id']]={'osm':obj['osm_url'],'position_m':[round(v,3) for v in pos],
        'rotation_z':angle,'height_m':h,'height_source':source,'category':spec['kind'],
        'identity_note':spec.get('identity_note','OSM identity/address'),
        'geometry':'modeled facade and roof; oriented to OSM footprint'}
    placements.append((spec['id'],pos,angle,footprint))

# Site-specific environment assets.
box(0,0,1,22,22,2,TRIM)
for a in [0,math.tau/3,math.tau*2/3]:
    x,y=math.cos(a),math.sin(a)
    rod((x*7,y*7,2),(x*1.3,y*1.3,26),2.1,TRIM,4,1.3)
finish('peoples-heroes-monument','上海市人民英雄纪念塔')
box(0,0,1,4,4,2,STONE)
sphere(0,0,5.9,.48,buildings.BRONZE,10,16)
box(0,0,4.5,1.2,.7,2.1,buildings.BRONZE)
for x in [-.34,.34]: rod((x,0,2),(x,0,3.6),.23,buildings.BRONZE,10)
rod((-.65,0,5.2),(-.8,-.15,3.8),.18,buildings.BRONZE,10)
rod((.65,0,5.2),(.8,-.15,3.8),.18,buildings.BRONZE,10)
finish('chen-yi-statue','陈毅雕像（轮廓模型）')
box(0,0,1.4,40,14,2.8,PAVE)
box(0,0,4.4,26,8,4.5,GLASS)
box(0,0,7,29,10,.6,SILVER)
finish('ferry-terminal','滨江渡口候船设施')
for i in range(8): box(0,i*.5,i*.22,12,.5,.35,TRIM)
finish('promenade-stairs','滨江步道阶梯')
import vehicles  # Sedan geometry shares the asset library material table.
box(0,0,1.8,11,2.6,3,TRIM)
for x in [-3.5,-2,-.5,1,2.5,4]:
    for y in [-1.32,1.32]: box(x,y,2.2,1.1,.07,1.1,GLASS)
for x in [-3.5,3.5]:
    for y in [-1.4,1.4]: rod((x,y-.1,.65),(x,y+.1,.65),.6,IRON,12)
finish('city-bus','城市公交车')
box(0,0,2,2,1.4,4,IRON)
box(0,-.73,2.5,1.65,.1,2.5,BLUE)
finish('wayfinding-sign','滨江导览牌')
rod((0,0,0),(0,0,5),.1,IRON,8)
box(0,0,4.5,.55,.35,1.5,IRON)
for z,m in [(4,GOLD),(4.5,LEAF),(5,PINK)]: sphere(0,-.23,z,.15,m,6,10)
finish('traffic-light','道路信号灯')

def export(path, objects):
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects: obj.select_set(True)
    bpy.context.view_layer.objects.active=objects[0]
    temporary=path.with_name(path.stem+'.writing.glb')
    bpy.ops.export_scene.gltf(filepath=str(temporary),export_format='GLB',use_selection=True,
                              export_extras=True,export_cameras=False,export_lights=False)
    temporary.replace(path)

catalog=[]
for name,obj in ASSETS.items():
    obj.data.calc_loop_triangles()
    export(ROOT/'models'/f'{name}.glb',[obj])
    catalog.append({'id':name,'name':LABELS[name],'file':f'models/{name}.glb',
        'triangles':len(obj.data.loop_triangles),'dimensions_blender_xyz':[round(v,3) for v in obj.dimensions],
        **metadata.get(name,{'category':'prop','geometry':'original environment prop'})})
    scene.collection.objects.unlink(obj)

collections={}
for key,label in [('historic','01 外滩历史建筑带'),('pudong','02 陆家嘴地标'),('north','03 苏州河口与北外滩'),
                  ('context','04 周边建筑轮廓'),('terrain','05 岸线道路与绿地'),('props','06 滨江设施')]:
    col=bpy.data.collections.new(label); scene.collection.children.link(col); collections[key]=col

def place(name,x,y,z=1,angle=0,scale=1,group='props'):
    obj=ASSETS[name].copy(); obj.data=ASSETS[name].data
    collections[group].objects.link(obj)
    obj.location=(x,y,z); obj.rotation_euler.z=angle; obj.scale=(scale,)*3
    return obj

def finish_scene(name,label,group):
    obj=finish(name,label)
    scene.collection.objects.unlink(obj); collections[group].objects.link(obj)
    del ASSETS[name]; del LABELS[name]
    return obj

for name,pos,angle,poly in placements:
    group=next(s['district'] for s in specs if s['id']==name)
    place(name,*pos,z=-min(v.co.z for v in ASSETS[name].data.vertices),angle=angle,group=group)

def polygon(poly,z,h,mat):
    if geo.area(poly)<0: poly=list(reversed(poly))
    vectors=[Vector((x,y,z+h)) for x,y in poly]
    lookup={tuple(v):i for i,v in enumerate(vectors)}
    n=len(poly)
    top=[tuple(v if isinstance(v,int) else lookup[tuple(v)] for v in tri)
         for tri in tessellate_polygon([vectors])]
    if h==0: meshpart([tuple(v) for v in vectors],top,mat); return
    points=[(x,y,z) for x,y in poly]+[tuple(v) for v in vectors]
    faces=[tuple(i+n for i in tri) for tri in top]
    faces += [tuple(reversed(tri)) for tri in top]
    faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    meshpart(points,faces,mat)

minx,miny,maxx,maxy=geo.BOUNDS
box((minx+maxx)/2,(miny+maxy)/2,-6,maxx-minx,maxy-miny,12,PAVE)
finish_scene('terrain-base','米制范围地表','terrain')
water_polys=[]
for e in elements.values():
    if e.get('tags',{}).get('natural')!='water': continue
    for poly in geo.rings(e):
        poly=geo.clip(poly)
        if len(poly)>2 and abs(geo.area(poly))>5:
            polygon(poly,.25,0,WATER); water_polys.append(poly)
finish_scene('huangpu-suzhou-water','黄浦江与苏州河水面 · OSM 岸线','terrain')

# Roads follow OSM centerlines. Width is a stated rendering estimate, not a survey.
road_segments=[]
for e in elements.values():
    tags=e.get('tags',{}); highway=tags.get('highway')
    if not highway or tags.get('tunnel')=='yes': continue
    width={'primary':18,'secondary':12,'tertiary':9,'residential':6,'pedestrian':8}.get(highway,6)
    points=[geo.xy(p) for p in e.get('geometry',[])]
    for a,b in zip(points,points[1:]):
        if not all(minx<=p[0]<=maxx and miny<=p[1]<=maxy for p in [a,b]): continue
        length=math.dist(a,b)
        if length<.2: continue
        dx,dy=(b[0]-a[0])/length*width/2,(b[1]-a[1])/length*width/2
        polygon([(a[0]-dy,a[1]+dx),(a[0]+dy,a[1]-dx),(b[0]+dy,b[1]-dx),(b[0]-dy,b[1]+dx)],
                1 if tags.get('bridge')=='yes' else .45,0,PAVE if highway=='pedestrian' else ASPHALT)
        if tags.get('name')=='中山东一路': road_segments.append((a,b))
finish_scene('street-network','街道与步行道路网 · OSM 中心线','terrain')

parks=[]
for e in elements.values():
    if e.get('tags',{}).get('leisure')!='park': continue
    for poly in geo.rings(e):
        poly=geo.clip(poly)
        if len(poly)>2:
            polygon(poly,.55,0,LEAF); parks.append(poly)
finish_scene('riverside-parks','滨江公园与陆家嘴绿地','terrain')

landmark_keys={(resolve(s)['type'],resolve(s)['id']) for s in specs}
relation_members={m['ref'] for e in elements.values() if e['type']=='relation' and e.get('tags',{}).get('building')
                  for m in e.get('members',[]) if m.get('role')=='outer'}
background=[]
for e,poly in mapped:
    if (e['type'],e['id']) in landmark_keys or (e['type']=='way' and e['id'] in relation_members): continue
    pos=geo.center(poly)
    if any(geo.inside(pos,p) for _,_,_,p in placements): continue
    tags=e.get('tags',{}); h,source=geo.height(tags)
    if h<2: continue
    mat=buildings.PALE if h>65 else STONE if e['id']%3 else buildings.BRICK
    polygon(poly,0,h,mat)
    # ponytail: context facades use floor bands; use surveyed elevations for street-level closeups.
    for z in range(4,int(h),4):
        for a,b in zip(poly,poly[1:]+poly[:1]):
            length=math.dist(a,b)
            if length<1: continue
            nx,ny=(b[1]-a[1])/length*.035,-(b[0]-a[0])/length*.035
            meshpart([(a[0]+nx,a[1]+ny,z),(b[0]+nx,b[1]+ny,z),
                      (b[0]+nx,b[1]+ny,z+1.25),(a[0]+nx,a[1]+ny,z+1.25)],[(0,1,2,3)],GLASS)
    obj=finish_scene(f'osm-{e["type"]}-{e["id"]}',tags.get('name','周边建筑'),'context')
    obj['osm_url']=f'https://www.openstreetmap.org/{e["type"]}/{e["id"]}'
    obj['height_source']=source
    obj['map_center_x']=pos[0]
    background.append({'osm':obj['osm_url'],'name':tags.get('name'),'height_m':h,'height_source':source})

# Promenade follows the actual river-facing road, with repeated street furniture.
for a,b in road_segments:
    length=math.dist(a,b)
    if length<10: continue
    if a[1]>b[1]: a,b=b,a
    angle=math.atan2(b[1]-a[1],b[0]-a[0]); step=Vector((math.cos(angle),math.sin(angle)))
    east=Vector((step.y,-step.x))
    for dist in range(0,int(length),12):
        p=Vector(a)+step*(dist+6)+east*18
        place('promenade-section',p.x,p.y,.3,angle=angle+math.pi)
    for dist in range(12,int(length),36):
        p=Vector(a)+step*dist+east*17
        place('riverside-lamp',p.x,p.y,1,scale=1.25)
        place('wooden-bench',p.x+3,p.y,1,angle=angle+math.pi)
    if length>45:
        p=Vector(a)+step*(length*.45)
        place('city-car',p.x,p.y,.45,angle=angle)

for poly in parks:
    xs=[p[0] for p in poly]; ys=[p[1] for p in poly]
    for x in range(int(min(xs))+10,int(max(xs)),28):
        for y in range(int(min(ys))+10,int(max(ys)),28):
            p=(x+random.uniform(-7,7),y+random.uniform(-7,7))
            if geo.inside(p,poly) and not any(geo.inside(p,w) for w in water_polys):
                place('plane-tree-planter',*p,scale=random.uniform(1.2,1.8))

def poi_pos(id):
    e=next(e for e in pois['elements'] if e['id']==id)
    return geo.xy(e) if e['type']=='node' else geo.center(geo.rings(e)[0])
place('chen-yi-statue',*poi_pos(476071294))
place('peoples-heroes-monument',*poi_pos(47007059),scale=1.2)
bridge=next(e for e in pois['elements'] if e['id']==27498117)
bridgepoints=[geo.xy(p) for p in bridge['geometry']]
bridgea,bridgeb=bridgepoints[0],bridgepoints[-1]
bridgecenter=tuple((a+b)/2 for a,b in zip(bridgea,bridgeb))
bridgeobj=place('garden-bridge',*bridgecenter,z=3,angle=math.atan2(bridgeb[1]-bridgea[1],bridgeb[0]-bridgea[0]))
bridgeobj.scale=(math.dist(bridgea,bridgeb)/28,18/6,2)
place('signal-tower',*geo.xy({'lon':121.48815,'lat':31.23355}),scale=1.75)
for lon,lat in [(121.4902,31.2342),(121.4893,31.2385),(121.4925,31.2467),(121.4939,31.2309)]:
    place('huangpu-cruise-boat',*geo.xy({'lon':lon,'lat':lat}),z=.6,scale=4,angle=.7)
for lon,lat in [(121.4885,31.2330),(121.4974,31.2298)]:
    place('ferry-terminal',*geo.xy({'lon':lon,'lat':lat}),z=.7)

scene_objects=[o for col in collections.values() for o in col.objects]
bpy.context.view_layer.update()
scene_files=['bund-environment.glb']
export(ROOT/'models'/'bund-environment.glb',scene_objects)
for filename,groups in [('bund-historic-district.glb',['historic']),('lujiazui-skyline.glb',['pudong']),
                        ('suzhou-north-bund.glb',['north']),('surrounding-buildings.glb',['context']),
                        ('river-roads-parks.glb',['terrain'])]:
    export(ROOT/'models'/filename,[o for key in groups for o in collections[key].objects]); scene_files.append(filename)

studio=bpy.data.collections.new('STUDIO | Cameras and lighting'); scene.collection.children.link(studio)
world=scene.world.node_tree.nodes['Background']; world.inputs[0].default_value=(.52,.65,.79,1); world.inputs[1].default_value=.55
sun_data=bpy.data.lights.new('Afternoon sunlight','SUN'); sun_data.energy=3; sun_data.angle=.10
sun=bpy.data.objects.new('Afternoon sunlight',sun_data); studio.objects.link(sun)
sun.rotation_euler=(.55,-.42,-1.1)
camera_data=bpy.data.cameras.new('Bund view'); camera=bpy.data.objects.new('Bund view',camera_data)
studio.objects.link(camera); scene.camera=camera; camera_data.type='ORTHO'; camera_data.clip_end=20000
scene.render.engine='CYCLES'; scene.cycles.samples=48; scene.cycles.use_denoising=True
prefs=bpy.context.preferences.addons['cycles'].preferences
try:
    prefs.compute_device_type='OPTIX'; prefs.get_devices()
    for device in prefs.devices: device.use=device.type=='OPTIX'
    if any(d.use for d in prefs.devices): scene.cycles.device='GPU'
except (TypeError,RuntimeError): pass
scene.render.image_settings.file_format='PNG'; scene.view_settings.view_transform='AgX'
scene.render.resolution_percentage=100
textmat=bpy.data.materials.new('Caption'); textmat.use_nodes=True
textshader=textmat.node_tree.nodes.get('Principled BSDF'); textshader.inputs['Base Color'].default_value=(1,1,1,1)
textshader.inputs['Emission Color'].default_value=(1,1,1,1); textshader.inputs['Emission Strength'].default_value=1
textdata=bpy.data.curves.new('Map attribution','FONT')
textdata.body='Map data (c) OpenStreetMap contributors | ODbL | openstreetmap.org/copyright'
caption=bpy.data.objects.new('Map attribution',textdata); studio.objects.link(caption)
caption.parent=camera; caption.data.materials.append(textmat)
caption.visible_shadow=False

views=[('bund-overview.png',(-3300,-3600,3300),(650,-120,130),5350,2400,1800),
       ('bund-waterfront.png',(1120,-240,565),(-520,80,35),1760,2400,1200),
       ('pudong-from-bund.png',(-320,150,18),(1050,-100,260),2380,2400,1300),
       ('suzhou-river-mouth.png',(850,-350,950),(-360,560,45),1610,2000,1300)]
def set_view(location,target,size,width,height):
    camera.location=location; camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler()
    camera_data.ortho_scale=size
    scene.render.resolution_x=width; scene.render.resolution_y=height
    caption_width=size if camera_data.type=='ORTHO' else 4*math.tan(camera_data.angle_x/2)
    textdata.size=caption_width/190
    caption.location=(-caption_width*.48,-caption_width*height/width*.47,-2)

set_view(*views[0][1:])
scene['geography']='Local equirectangular meters; X east, Y north; origin 121.490E 31.239N'
scene['attribution']='Map data © OpenStreetMap contributors; ODbL; https://www.openstreetmap.org/copyright'
scene['accuracy']='OSM footprint/placement; modeled facades; height source stored on each building'
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_perspective='CAMERA'
            area.spaces.active.clip_end=20000
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'source/bund-environment.blend'),compress=True)
for filename,*view in views:
    camera_data.type='PERSP' if filename=='pudong-from-bund.png' else 'ORTHO'
    camera_data.lens=24
    set_view(*view); scene.render.filepath=str(ROOT/'previews'/filename)
    if filename=='bund-waterfront.png':
        collections['pudong'].hide_render=True
        for o in collections['context'].objects: o.hide_render=o.get('map_center_x',0)>150
    if '--no-render' not in sys.argv: bpy.ops.render.render(write_still=True)
    collections['pudong'].hide_render=False
    for o in collections['context'].objects: o.hide_render=False

# A separate night source preserves the daylight materials in the primary file.
sun_data.energy=.06; world.inputs[0].default_value=(.035,.07,.16,1); world.inputs[1].default_value=.22
night_values={GLASS:((1,.55,.18,1),.7),GOLD:((1,.66,.24,1),4),
              BLUE:((.12,.28,.50,1),.14),buildings.PALE:((.18,.32,.48,1),.10),
              SILVER:((.35,.65,1,1),.65),PINK:((.85,.09,.25,1),.30),
              buildings.BRONZE:((1,.52,.13,1),.30)}
day_emission={}
for index,(color,strength) in night_values.items():
    shader=MATS[index].node_tree.nodes.get('Principled BSDF')
    day_emission[index]=(tuple(shader.inputs['Emission Color'].default_value),shader.inputs['Emission Strength'].default_value)
    shader.inputs['Emission Color'].default_value=color
    shader.inputs['Emission Strength'].default_value=strength
camera_data.type='PERSP'; camera_data.lens=24
set_view(*views[2][1:]); scene.render.filepath=str(ROOT/'previews/pudong-night.png')
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'source/bund-night.blend'),compress=True)
if '--no-render' not in sys.argv: bpy.ops.render.render(write_still=True)

sun_data.energy=3; world.inputs[0].default_value=(.52,.65,.79,1); world.inputs[1].default_value=.55
for index,(color,strength) in day_emission.items():
    shader=MATS[index].node_tree.nodes.get('Principled BSDF')
    shader.inputs['Emission Color'].default_value=color
    shader.inputs['Emission Strength'].default_value=strength
for col in collections.values(): col.hide_render=True; col.hide_viewport=True
library=bpy.data.collections.new('ASSETS | Named buildings and props'); scene.collection.children.link(library)
for i,(name,obj) in enumerate(sorted(ASSETS.items(),key=lambda item:item[1].dimensions.z)):
    library.objects.link(obj); obj.location=((i%10)*180,(i//10)*200,0)
    obj.asset_mark(); obj.asset_data.description=LABELS[name]
camera_data.type='ORTHO'
set_view((2400,-3000,2900),(800,800,150),3300,2400,1800)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'source/bund-asset-library.blend'),compress=True)
scene.render.filepath=str(ROOT/'previews/asset-library.png')
if '--no-render' not in sys.argv: bpy.ops.render.render(write_still=True)

for o in scene_objects: o.data.calc_loop_triangles()
manifest={'name':'外滩两岸与周边街区 · 地理布局扩展版','version':2,'blender':bpy.app.version_string,
          'coordinates':{'origin_lon_lat':geo.ORIGIN,'units':'meters','axes':'Blender X east / Y north / Z up; GLB Y up'},
          'bounds_m':geo.BOUNDS,'attribution':scene['attribution'],
          'osm_timestamp':data.get('osm3s',{}).get('timestamp_osm_base'),
          'scene':'models/bund-environment.glb','scene_files':scene_files,
          'assets':catalog,'landmark_count':len(specs),'context_buildings':background,
          'scene_objects':len(scene_objects),'scene_triangles':sum(len(o.data.loop_triangles) for o in scene_objects),
          'scene_bytes':(ROOT/'models/bund-environment.glb').stat().st_size,
          'views':views,'previews':[v[0] for v in views]+['pudong-night.png','asset-library.png']}
(ROOT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="1460" viewBox="0 0 1400 1460">',
     '<rect width="1400" height="1460" fill="#f2eee5"/>',
     '<text x="35" y="42" font-size="25" fill="#253b40">BUND / MODEL COVERAGE — NORTH ↑</text>']
def svgpoly(poly,color):
    points=' '.join(f'{40+(x-minx)/(maxx-minx)*1320:.1f},{85+(maxy-y)/(maxy-miny)*1280:.1f}' for x,y in poly)
    return f'<polygon points="{points}" fill="{color}" stroke="#f2eee5" stroke-width=".6"/>'
for poly in water_polys: svg.append(svgpoly(poly,'#77afb8'))
for e,poly in mapped: svg.append(svgpoly(poly,'#b3b3aa'))
for name,pos,angle,poly in placements:
    svg.append('<g><title>'+escape(LABELS.get(name,name))+'</title>'+svgpoly(poly,'#c66b41')+'</g>')
svg+=['<text x="40" y="1400" font-size="18">Orange: 67 modeled landmarks | Grey: surrounding OSM building envelopes</text>',
      '<text x="40" y="1432" font-size="15">Map data © OpenStreetMap contributors | ODbL | openstreetmap.org/copyright</text></svg>']
(ROOT/'previews/coverage-map.svg').write_text('\n'.join(svg),encoding='utf-8')
print('BUND_CITY_COMPLETE',len(specs),'landmarks',len(background),'context buildings',len(catalog),'assets',flush=True)
