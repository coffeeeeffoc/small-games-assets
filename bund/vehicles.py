"""Meter-scale sedan, +X forward, tire contact at Z=0. No external model data."""
from geometry import *

paint = material('Sedan | pearl silver paint', (.46, .55, .59), .72, .24)
rubber = material('Sedan | tire rubber', (.012, .016, .02), 0, .92)
glass = material('Sedan | tinted glazing', (.024, .065, .085), .35, .16)
chrome = material('Sedan | brushed alloy', (.65, .7, .72), .85, .23)
lamp = material('Headlamp | warm white', (.95, .91, .77), .1, .2, .5)
tail = material('Tail lamp | red', (.55, .012, .008), .1, .25, .3)

# Curved shoulder and tapered nose/trunk; cabin has separate sloped glazing.
sections = [(-2.3,.72,.62),(-2.05,.91,.88),(-1.2,.94,1.0),
            (.9,.94,.96),(1.8,.87,.82),(2.3,.72,.65)]
points=[]
for x,w,z in sections:
    points.extend([(x,-w*.94,.39),(x,-w,z-.08),(x,-w*.88,z),
                   (x,w*.88,z),(x,w,z-.08),(x,w*.94,.39)])
faces=[tuple(range(5,-1,-1)),tuple(range(len(points)-6,len(points)))]
for i in range(len(sections)-1):
    faces.extend((i*6+j,i*6+(j+1)%6,(i+1)*6+(j+1)%6,(i+1)*6+j) for j in range(6))
meshpart(points,faces,paint)
box(0,0,.35,3.6,1.6,.16,rubber)
meshpart([(-1.4,-.78,.99),(-.83,-.65,1.49),(.51,-.64,1.49),(1.15,-.79,.96),
          (-1.4,.78,.99),(-.83,.65,1.49),(.51,.64,1.49),(1.15,.79,.96)],
         [(0,1,2,3),(4,7,6,5),(1,5,6,2),(0,4,5,1),(3,2,6,7)],glass)
box(-.16,0,1.505,1.42,1.32,.045,paint)
for side in [-1,1]:
    y=side*.8
    for a,b in [((-1.4,y,.99),(-.83,side*.65,1.5)),
                ((.51,side*.64,1.5),(1.15,y,.96)),
                ((-.26,side*.79,.99),(-.26,side*.65,1.5))]: rod(a,b,.035,paint,8)
    rod((-1.4,y,.99),(1.15,y,.96),.022,chrome,8)
    for x in [-.37,1.03]: rod((x,side*.936,.46),(x,side*.936,.94),.009,rubber,6)
    for x in [-.65,.58]: box(x,side*.946,.87,.2,.022,.035,chrome)
    rod((.79,side*.79,1.06),(.76,side*1.02,1.11),.026,rubber,8)
    box(.74,side*1.045,1.12,.25,.16,.12,paint)
    for x in [-1.46,1.46]:
        rod((x,side*.79,.35),(x,side*1.005,.35),.35,rubber,32)
        rod((x,side*1.006,.35),(x,side*1.016,.35),.24,chrome,32)
        rod((x,side*1.018,.35),(x,side*1.02,.35),.19,rubber,24)
        for spoke in range(5):
            a=spoke*math.tau/5
            rod((x,side*1.024,.35),(x+math.cos(a)*.21,side*1.024,.35+math.sin(a)*.21),.035,chrome,6)
        rod((x,side*1.025,.35),(x,side*1.03,.35),.07,chrome,16)
        for j in range(16):
            a=j*math.pi/16; b=(j+1)*math.pi/16
            rod((x+math.cos(a)*.385,side*.945,.35+math.sin(a)*.385),
                (x+math.cos(b)*.385,side*.945,.35+math.sin(b)*.385),.022,paint,6)
    box(2.235,side*.52,.7,.085,.37,.14,lamp)
    box(-2.22,side*.53,.7,.08,.32,.13,tail)
box(2.308,0,.49,.018,.88,.17,rubber)
for z in [.44,.49,.54]: box(2.321,0,z,.012,.86,.012,chrome)
for x in [-2.305,2.325]: box(x,0,.42,.018,.36,.105,WHITE)
rod((-2.29,-.53,.33),(-2.36,-.53,.33),.055,chrome,16)
car=finish('city-car','城市轿车 · 四门旅行款')
bevel=car.modifiers.new('Soft manufactured edges','BEVEL');bevel.width=.018;bevel.segments=2
bpy.context.view_layer.objects.active=car
bpy.ops.object.modifier_apply(modifier=bevel.name)
assert abs(min(v.co.z for v in car.data.vertices)) < .002
