"""Run with Blender --background --factory-startup --python build.py.

Original detailed architectural geometry, no downloaded models or textures.
Blender coordinates: Z up, landmarks face -Y, asset origin at ground center.
"""
import bpy
import json
import math
import random
import sys
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
for folder in ('source', 'models', 'previews'):
    (ROOT / folder).mkdir(exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.preferences.filepaths.save_version=0
random.seed(29)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.world = bpy.data.worlds.new('Warm studio sky')
scene.world.use_nodes = True
scene.world.node_tree.nodes['Background'].inputs[0].default_value = (.36, .46, .53, 1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value = .45

MATS = []
def material(name, color, metallic=0, roughness=.7, emission=0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value = (*color, 1)
    shader.inputs['Metallic'].default_value = metallic
    shader.inputs['Roughness'].default_value = roughness
    shader.inputs['Emission Color'].default_value = (*color, 1)
    shader.inputs['Emission Strength'].default_value = emission
    MATS.append(mat)
    return len(MATS) - 1

STONE = material('Limestone | warm ivory', (.69, .58, .42))
TRIM = material('Carved stone | cream', (.88, .79, .59))
SAND = material('Sandstone | rose', (.57, .35, .26))
ROOF = material('Patinated copper | jade', (.055, .25, .20), .35)
GLASS = material('Window glass | deep teal', (.035, .13, .17), .35, .28)
BLUE = material('Tower glass | blue', (.16, .39, .46), .5, .26)
SILVER = material('Tower ribs | silver', (.53, .65, .65), .65, .35)
PINK = material('Pearl spheres | muted ruby', (.65, .20, .29), .45, .3)
GOLD = material('Warm lamp glass', (1, .66, .24), .1, .4, .4)
IRON = material('Street iron | midnight', (.035, .075, .085), .55)
WOOD = material('Bench timber', (.36, .17, .075))
LEAF = material('Foliage | sage', (.18, .39, .25))
LEAF2 = material('Foliage | sunlit', (.34, .50, .25))
PAVE = material('Promenade paving', (.60, .62, .55))
ASPHALT = material('Road asphalt', (.14, .20, .22))
WATER = material('Huangpu water | jade', (.075, .34, .38), .28, .3)
FOAM = material('Water ripples', (.18, .43, .45), .1)
WHITE = material('Boat paint / markings', (.90, .89, .76))

# Fine stone grain is procedural in .blend; GLB retains portable PBR colors.
for slot in [STONE,TRIM,SAND,PAVE]:
    nodes=MATS[slot].node_tree.nodes; links=MATS[slot].node_tree.links
    noise=nodes.new('ShaderNodeTexNoise'); noise.inputs['Scale'].default_value=42
    noise.inputs['Detail'].default_value=3
    bump=nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value=.16
    bump.inputs['Distance'].default_value=.025
    links.new(noise.outputs['Fac'],bump.inputs['Height'])
    links.new(bump.outputs['Normal'],nodes.get('Principled BSDF').inputs['Normal'])

verts, faces, slots, smooth = [], [], [], []
ASSETS = {}
LABELS = {}
def meshpart(points, polygons, mat, curved=False):
    offset = len(verts)
    verts.extend(points)
    faces.extend(tuple(i + offset for i in face) for face in polygons)
    slots.extend([mat] * len(polygons))
    smooth.extend([curved] * len(polygons))

def box(x, y, z, sx, sy, sz, mat):
    meshpart([(x + a*sx/2, y + b*sy/2, z + c*sz/2)
              for a,b,c in [(-1,-1,-1),(-1,-1,1),(-1,1,-1),(-1,1,1),
                            (1,-1,-1),(1,-1,1),(1,1,-1),(1,1,1)]],
             [(0,2,6,4),(1,5,7,3),(0,4,5,1),(2,3,7,6),(0,1,3,2),(4,6,7,5)], mat)

def rod(a, b, radius, mat, n=16, top=None):
    a,b = Vector(a),Vector(b)
    axis = (b-a).normalized()
    ref = Vector((0,1,0)) if abs(axis.y) < .9 else Vector((1,0,0))
    u = axis.cross(ref).normalized()
    v = axis.cross(u)
    phase=math.pi/4 if n==4 else 0
    points = [tuple(p + (u*math.cos(i*math.tau/n+phase)+v*math.sin(i*math.tau/n+phase))*r)
              for p,r in [(a,radius),(b,radius if top is None else top)] for i in range(n)]
    polys = [tuple(reversed(range(n))),tuple(range(n,2*n))]
    polys += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    meshpart(points, polys, mat)

def sphere(x,y,z,r,mat, rings=10, segments=20, stretch=(1,1,1)):
    points = [(x,y,z-r*stretch[2]), (x,y,z+r*stretch[2])]
    for j in range(1,rings):
        phi = -math.pi/2 + j*math.pi/rings
        for i in range(segments):
            t = i*math.tau/segments
            points.append((x+r*math.cos(phi)*math.cos(t)*stretch[0],
                           y+r*math.cos(phi)*math.sin(t)*stretch[1], z+r*math.sin(phi)*stretch[2]))
    polys = []
    for i in range(segments):
        nxt=(i+1)%segments
        polys.extend([(0,2+nxt,2+i),(1,2+(rings-2)*segments+i,2+(rings-2)*segments+nxt)])
    for j in range(rings-2):
        for i in range(segments):
            a=2+j*segments+i; b=2+j*segments+(i+1)%segments
            polys.append((a,b,b+segments,a+segments))
    meshpart(points,polys,mat,curved=True)

def finish(name,label):
    global verts,faces,slots,smooth
    mesh=bpy.data.meshes.new(name)
    mesh.from_pydata(verts,[],faces)
    mesh.update()
    obj=bpy.data.objects.new(name,mesh)
    scene.collection.objects.link(obj)
    for mat in MATS: mesh.materials.append(mat)
    for polygon,slot in zip(mesh.polygons,slots): polygon.material_index=slot
    for polygon,curved in zip(mesh.polygons,smooth): polygon.use_smooth=curved
    # Keep only used slots, so each GLB carries the materials it actually uses.
    used=sorted(set(slots)); mesh.materials.clear()
    for slot in used: mesh.materials.append(MATS[slot])
    for polygon,slot in zip(mesh.polygons,slots): polygon.material_index=used.index(slot)
    obj['label_zh']=label
    obj['style']='Detailed architectural interpretation; non-survey scale'
    if name in ['customs-house','hsbc-building','bund-heritage-block','signal-tower']:
        bevel=obj.modifiers.new('Stone edge highlights','BEVEL')
        bevel.width=.035; bevel.segments=2; bevel.limit_method='ANGLE'
        bpy.context.view_layer.objects.active=obj
        obj.select_set(True)
        bpy.ops.object.modifier_apply(modifier=bevel.name)
        obj.select_set(False)
    ASSETS[name]=obj; LABELS[name]=label
    verts,faces,slots,smooth=[],[],[],[]
    return obj

def facade(w,d,h,floors,mat=STONE):
    box(0,0,h/2,w,d,h,mat)
    box(0,0,.4,w+1,d+1,.8,TRIM)
    for floor in range(floors):
        z=2.5+floor*(h-3)/floors
        box(0,0,z-1.15,w+.5,d+.5,.28,TRIM)
        for side in [-1,1]:
            for i in range(int(w/2.4)):
                x=(i-(int(w/2.4)-1)/2)*2.4
                box(x,side*(d/2+.025),z,1.15,.08,1.55,GLASS)
                box(x,side*(d/2+.12),z+.87,1.5,.3,.17,TRIM)
                box(x,side*(d/2+.12),z-.85,1.5,.35,.16,TRIM)
                for dx in [-.67,.67]: box(x+dx,side*(d/2+.1),z,.15,.25,1.65,TRIM)
                box(x,side*(d/2+.09),z,.055,.10,1.55,ROOF)
                box(x,side*(d/2+.09),z+.12,1.15,.10,.055,ROOF)
            for i in range(int(d/2.6)):
                y=(i-(int(d/2.6)-1)/2)*2.6
                box(side*(w/2+.025),y,z,.08,1.1,1.55,GLASS)
                for dy in [-.63,.63]: box(side*(w/2+.10),y+dy,z,.22,.12,1.7,TRIM)
                box(side*(w/2+.12),y,z-.87,.3,1.5,.15,TRIM)
                box(side*(w/2+.08),y,z,.1,.05,1.55,ROOF)
                box(side*(w/2+.08),y,z+.12,.1,1.1,.05,ROOF)
    for x in [-w/2+.35,w/2-.35]:
        for side in [-1,1]:
            for z in range(1,int(h)):
                box(x,side*(d/2+.13),z,.75,.3,.44,TRIM)
    for side in [-1,1]:
        for z in [h-.15,h+.2,h+.5]: box(0,side*(d/2+.3),z,w+1,.65,.17,TRIM)
        box(0,side*(d/2-.15),h+.9,w,.28,.65,STONE)
        for x in range(-int(w/2)+1,int(w/2)):
            box(x,side*(d/2+.25),h-.63,.23,.40,.32,TRIM)
    for x in [-w/2+.15,w/2-.15]: box(x,0,h+.9,.28,d,.65,STONE)
    box(0,0,h-.3,w+.9,d+.9,.6,TRIM)
    box(0,0,h+.2,w+.3,d+.3,.4,STONE)

def arch(x,y,bottom,width,height,depth=.22):
    radius=width/2; spring=bottom+height-radius
    for side in [-1,1]: box(x+side*(radius+.12),y,(bottom+spring)/2,.24,depth,spring-bottom,TRIM)
    for i in range(16):
        a=i*math.pi/16; b=(i+1)*math.pi/16
        p=[(x+r*math.cos(t),y+d,spring+r*math.sin(t))
           for d in [-depth/2,depth/2] for r,t in [(radius,a),(radius,b),(radius+.25,b),(radius+.25,a)]]
        meshpart(p,[(0,1,2,3),(7,6,5,4),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],TRIM)
    box(x,y+.04,bottom+(height-radius)/2,width,.06,height-radius,GLASS)
    rod((x,y+.08,spring),(x,y+.02,spring),radius,GLASS,32)

# Historic Bund architecture: silhouettes and repeated facade relief.
facade(22,13,15,5)
for x in [-7.2,-4.8,-2.4,0,2.4,4.8,7.2]: arch(x,-6.75,.7,1.5,3.1)
for x in [-4,-2,0,2,4]:
    rod((x,-7,1),(x,-7,6),.42,TRIM,12)
box(0,0,18,8,7,6,STONE)
box(0,0,22,6.7,6.3,2,TRIM)
box(0,0,24.5,5.8,5.8,3,STONE)
for side in [-1,1]:
    rod((0,side*2.95,24.4),(0,side*3.04,24.4),1.05,WHITE,32)
    for i in range(12):
        a=i*math.tau/12
        rod((.83*math.sin(a),side*3.14,24.4+.83*math.cos(a)),
            (.96*math.sin(a),side*3.14,24.4+.96*math.cos(a)),.025,IRON,6)
    box(0,side*3.12,24.7,.10,.07,.75,IRON)
    box(.3,side*3.12,24.4,.65,.07,.10,IRON)
    rod((side*2.95,0,24.4),(side*3.04,0,24.4),1.05,WHITE,32)
    for i in range(12):
        a=i*math.tau/12
        rod((side*3.14,.83*math.sin(a),24.4+.83*math.cos(a)),
            (side*3.14,.96*math.sin(a),24.4+.96*math.cos(a)),.025,IRON,6)
    box(side*3.12,0,24.7,.07,.10,.75,IRON)
    box(side*3.12,.3,24.4,.07,.65,.10,IRON)
box(0,0,26.4,6.5,6.5,.7,TRIM)
rod((0,0,26.8),(0,0,28),4.6,ROOF,4,2.7)
finish('customs-house','江海关大楼（钟楼）')

facade(28,15,13,4)
for x in [-10,-7.5,-5,-2.5,0,2.5,5,7.5,10]: arch(x,-7.72,.8,1.65,3.5)
for x in [-6,-3.6,-1.2,1.2,3.6,6]:
    rod((x,-8.4,1),(x,-8.4,9.3),.55,TRIM,12)
    box(x,-8.4,9.25,1.35,1.35,.5,TRIM)
    for z in [1,1.2,8.8,9]: rod((x,-8.4,z),(x,-8.4,z+.15),.7,TRIM,20)
box(0,-7.6,10,16,3,1,TRIM)
rod((0,0,13),(0,0,16),4.3,STONE,24)
sphere(0,0,16,4.4,ROOF,24,48,stretch=(1,1,.8))
for i in range(16):
    a=i*math.tau/16
    for j in range(8):
        t=j*math.pi/16; u=(j+1)*math.pi/16
        rod((4.43*math.cos(t)*math.cos(a),4.43*math.cos(t)*math.sin(a),16+3.55*math.sin(t)),
            (4.43*math.cos(u)*math.cos(a),4.43*math.cos(u)*math.sin(a),16+3.55*math.sin(u)),.055,TRIM,6)
rod((0,0,19.3),(0,0,20.2),1.1,TRIM,12)
finish('hsbc-building','原汇丰银行大楼（穹顶）')

facade(20,13,20,7)
for x in [-7.2,-4.8,-2.4,0,2.4,4.8,7.2]: box(x,-6.7,11,.18,.25,17,TRIM)
for x in [-4,0,4]: arch(x,-6.8,.7,2,3.4)
box(0,0,22,10,9,4,STONE)
for x in [-4,-2,0,2,4]: box(x,-4.6,22,.7,.15,2.5,GLASS)
box(0,0,24.3,11,10,.7,TRIM)
rod((0,0,24.7),(0,0,32.5),7.3,ROOF,4,0)
for i in range(4):
    a=i*math.pi/2+math.pi/4
    rod((7.3*math.cos(a),7.3*math.sin(a),24.7),(0,0,32.5),.065,TRIM,6)
rod((0,0,32.5),(0,0,34),.10,IRON,8)
finish('peace-hotel','和平饭店（绿色金字塔顶）')

facade(17,12,14,4,SAND)
for x in [-6.5,6.5]:
    box(x,0,15,3.8,12,2,TRIM)
    rod((x,0,16),(x,0,18.4),2.7,ROOF,4,0)
box(0,-6.5,12.5,8,1,.5,TRIM)
finish('bund-heritage-block','外滩历史街区通用楼')

rod((0,0,0),(0,0,1),3,TRIM,16)
rod((0,0,1),(0,0,12),1.8,STONE,16,1.4)
rod((0,0,12),(0,0,12.5),2.4,TRIM,16)
rod((0,0,12.5),(0,0,15),1.8,GLASS,12)
rod((0,0,15),(0,0,16.5),2.3,ROOF,12,0)
rod((0,0,16.5),(0,0,19),.09,IRON,8)
finish('signal-tower','外滩信号台')

# Pudong landmarks, compressed height for a compact playable diorama.
for angle in [0,math.tau/3,2*math.tau/3]:
    x,y=5*math.cos(angle),5*math.sin(angle)
    rod((x,y,0),(x*.32,y*.32,23),.9,SILVER,12)
    rod((x*.32,y*.32,19),(x*.32,y*.32,48),.55,SILVER,12)
rod((0,0,0),(0,0,60),.8,SILVER,12)
for z,r in [(17,6.3),(43,4.6),(57,1.7)]:
    sphere(0,0,z,r,PINK,24,48)
    rod((0,0,z-.65),(0,0,z+.65),r*1.01,GLASS,48)
    for i in range(32):
        a=i*math.tau/32
        rod((r*1.02*math.cos(a),r*1.02*math.sin(a),z-.65),
            (r*1.02*math.cos(a),r*1.02*math.sin(a),z+.65),.035,SILVER,5)
rod((0,0,58),(0,0,69),.35,SILVER,10,0)
finish('oriental-pearl','东方明珠')

# Twisting tapered rings keep the Shanghai Tower silhouette legible.
points=[]; count=48; levels=48
for j in range(levels+1):
    z=j*1.8; t=j/levels; angle=t*math.pi*.7
    for i in range(count):
        theta=i*math.tau/count+angle
        radius=(6.2-3*t)*(1+.12*math.cos(3*(theta-angle)))
        points.append((radius*math.cos(theta),radius*math.sin(theta),z))
polys=[tuple(reversed(range(count))),tuple(range(levels*count,(levels+1)*count))]
for j in range(levels):
    for i in range(count): polys.append((j*count+i,j*count+(i+1)%count,(j+1)*count+(i+1)%count,(j+1)*count+i))
meshpart(points,polys,BLUE)
for i in range(0,count,2):
    for j in range(levels): rod(points[j*count+i],points[(j+1)*count+i],.075,SILVER,5)
for j in range(1,levels):
    for i in range(count): rod(points[j*count+i],points[j*count+(i+1)%count],.055,SILVER,4)
finish('shanghai-tower','上海中心大厦（扭转轮廓）')

z=0
for i in range(10):
    h=9-i*.55; w=11-i*.78
    box(0,0,z+h/2,w,w,h,BLUE)
    for floor in range(1,4): box(0,0,z+h*floor/4,w+.2,w+.2,.16,SILVER)
    box(0,0,z+h,w+.8,w+.8,.55,SILVER)
    for side in [-1,1]:
        for offset in [-.36,-.18,0,.18,.36]:
            box(offset*w,side*w/2,z+h/2,.065,.12,h,SILVER)
            box(side*w/2,offset*w,z+h/2,.12,.065,h,SILVER)
    z+=h
rod((0,0,z),(0,0,z+9),1.5,SILVER,8,0)
finish('jin-mao-tower','金茂大厦（层叠塔冠）')

# Real opening at the top, made from separate side pillars and lintel.
meshpart([(-6,-3,0),(6,-3,0),(6,3,0),(-6,3,0),
          (-4.5,-2,58),(4.5,-2,58),(4.5,2,58),(-4.5,2,58)],
         [(0,3,2,1),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)],BLUE)
for x in [-3.85,3.85]: box(x,0,62.5,1.3,4,9,BLUE)
box(0,0,67.5,9,4,1.4,SILVER)
for z in range(1,58):
    w=12-3*z/58
    box(0,-3+z/58-.035,z,w,.07,.12,SILVER)
    box(0,3-z/58+.035,z,w,.07,.12,SILVER)
for x in [-4,-2,0,2,4]:
    rod((x,-3.05,0),(x*.75,-2.05,58),.045,SILVER,5)
    rod((x,3.05,0),(x*.75,2.05,58),.045,SILVER,5)
finish('world-financial-center','环球金融中心（贯通顶部开口）')

# Reusable streetscape pieces.
box(0,0,.3,12,8,.6,PAVE)
for x in range(-5,6,2): box(x,0,.608,.035,8,.016,TRIM)
for y in [-2,0,2]: box(0,y,.608,12,.035,.016,TRIM)
box(0,3.7,.75,12,.55,.3,TRIM)
for x in range(-6,7,2):
    box(x,3.7,1.3,.25,.3,1.2,STONE)
box(0,3.7,1.9,12,.34,.16,TRIM)
for x in range(-5,6): box(x,3.7,1.25,.055,.06,.9,IRON)
finish('promenade-section','滨江步道与栏杆（12米拼接段）')

rod((0,0,0),(0,0,.2),.55,IRON)
rod((0,0,.2),(0,0,4.5),.16,IRON,10,.1)
rod((-1.05,0,4.4),(1.05,0,4.4),.08,IRON,8)
for x in [-1,1]:
    rod((x,0,4.1),(x,0,4.65),.30,GOLD,6,.22)
    rod((x,0,4.65),(x,0,4.85),.4,IRON,6,0)
finish('riverside-lamp','滨江双头路灯')

for x in [-.9,.9]:
    box(x,0,.35,.13,.7,.7,IRON)
    box(x,.31,.8,.1,.12,1.1,IRON)
for y in [-.25,0,.25]: box(0,y,.64,2.4,.19,.12,WOOD)
for z in [.94,1.18]: box(0,.34,z,2.4,.12,.18,WOOD)
finish('wooden-bench','木质长椅')

box(0,0,.35,3,3,.7,STONE)
box(0,0,.72,2.75,2.75,.06,WOOD)
rod((0,0,.7),(0,0,4.5),.22,WOOD,8,.12)
for x,y,z,r in [(-.8,0,4,1.8),(.8,.1,4.6,1.9),(0,-.4,5.6,1.7)]:
    sphere(x,y,z,r,LEAF if x<0 else LEAF2,8,14)
    for i in range(14):
        a=random.uniform(0,math.tau); dz=random.uniform(-1,1)
        sphere(x+math.cos(a)*r*.8,y+math.sin(a)*r*.8,z+dz*r*.65,
               random.uniform(.35,.65),LEAF if i%2 else LEAF2,5,8)
finish('plane-tree-planter','悬铃木意象与树池')

box(0,0,.35,3.8,1.4,.7,TRIM)
for x in [-1.3,0,1.3]: sphere(x,0,.85,.7,LEAF,4,8,stretch=(1,.8,.8))
finish('hedge-planter','绿篱花池')

rod((0,0,0),(0,0,.75),.16,IRON,10)
sphere(0,0,.77,.19,IRON,5,10)
rod((0,0,.51),(0,0,.61),.165,GOLD,10)
finish('bollard','步道隔离桩')

box(0,0,.08,12,10,.16,ASPHALT)
for x in [-4,0,4]: box(x,0,.167,2.2,.16,.012,WHITE)
for y in [-4.5,4.5]: box(0,y,.167,12,.10,.012,WHITE)
finish('road-section','双向道路（12米拼接段）')

# Garden Bridge inspired steel truss, shortened to a reusable crossing.
box(0,0,1,28,6,.6,ASPHALT)
for side in [-1,1]:
    y=side*3.15
    for z in [1,4.8]: rod((-14,y,z),(14,y,z),.16,IRON,6)
    for i in range(7):
        x=-14+i*4
        rod((x,y,1),(x,y,4.8),.13,IRON,6)
        rod((x,y,1),(x+4,y,4.8),.13,IRON,6)
        rod((x,y,4.8),(x+4,y,1),.13,IRON,6)
    rod((14,y,1),(14,y,4.8),.13,IRON,6)
for x in [-12,12]: box(x,0,.25,2,7,.5,STONE)
finish('garden-bridge','外白渡桥意象钢桁架桥段')

meshpart([(-6,-1.8,0),(4,-1.8,0),(6,0,0),(4,1.8,0),(-6,1.8,0),
          (-6,-2.2,1.4),(4,-2.2,1.4),(7,0,1.4),(4,2.2,1.4),(-6,2.2,1.4)],
         [(4,3,2,1,0),(5,6,7,8,9),(0,1,6,5),(1,2,7,6),(2,3,8,7),(3,4,9,8),(4,0,5,9)],WHITE)
box(-.7,0,2.1,8,3,1.4,WHITE)
box(-.7,0,3,8.6,3.5,.35,ROOF)
for x in [-3.5,-2,-.5,1,2.5]:
    for side in [-1,1]: box(x,side*1.52,2.2,1,.05,.65,GLASS)
box(-1,0,3.6,4.5,2,1,WHITE)
box(-1,0,4.15,5,2.5,.2,TRIM)
rod((1,0,4.3),(1,0,5.4),.07,IRON,6)
finish('huangpu-cruise-boat','黄浦江游船')

box(0,0,-.4,12,12,.8,WATER)
for i in range(12):
    x,y=random.uniform(-5,5),random.uniform(-5,5)
    box(x,y,.012,random.uniform(.5,1.5),.065,.018,FOAM)
finish('river-tile','黄浦江水面（12米拼接块）')

