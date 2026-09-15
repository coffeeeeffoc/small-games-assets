"""Distinct rooflines, facade rhythms and structural features for named sites."""
from geometry import *
import geometry as geometry_data

BRICK=material('Heritage red brick',(.33,.13,.085))
BRONZE=material('Bronze fins / Aurora curtain wall',(.47,.32,.12),.72,.27)
PALE=material('Pale blue curtain wall',(.25,.39,.43),.58,.23)
DARK=material('Dark slate roof',(.10,.13,.15),.2,.5)

def pediment(x,y,z,w):
    meshpart([(x-w/2,y-.2,z),(x+w/2,y-.2,z),(x,y-.2,z+w*.19),
              (x-w/2,y+.2,z),(x+w/2,y+.2,z),(x,y+.2,z+w*.19)],
             [(0,1,2),(5,4,3),(0,3,4,1),(1,4,5,2),(2,5,3,0)],TRIM)

def hipped(w,d,z,h,mat=DARK):
    meshpart([(-w/2,-d/2,z),(w/2,-d/2,z),(w/2,d/2,z),(-w/2,d/2,z),
              (-w*.3,0,z+h),(w*.3,0,z+h)],
             [(0,3,2,1),(0,1,5,4),(1,2,5),(2,3,4,5),(3,0,4)],mat)

def heritage(spec):
    floor=spec.get('floors',6); w=22; d=13; h=max(7,floor*2.5)
    tone={'stone':STONE,'cream':TRIM,'brick':BRICK}[spec.get('tone','stone')]
    facade(w,d,h,floor,tone)
    for x in [-8,-4,0,4,8]: arch(x,-d/2-.23,.6,1.75,3)
    columns=spec.get('columns',0)
    for i in range(columns):
        x=(i-(columns-1)/2)*2.6
        rod((x,-d/2-1,.7),(x,-d/2-1,h-.8),.35,TRIM,16)
        for z in [.7,h-1]: rod((x,-d/2-1,z),(x,-d/2-1,z+.25),.55,TRIM,16)
    roof=spec.get('roof','flat')
    if roof in ['mansard','hip']:
        hipped(w,d,h+.4,2.4)
        if roof=='mansard':
            for x in [-8,-4,0,4,8]:
                box(x,-4.7,h+1.15,1.1,.7,1.1,TRIM)
                box(x,-5.08,h+1.15,.65,.04,.8,GLASS)
                pediment(x,-5.12,h+1.7,1.5)
    if roof in ['twin-domes','corner-dome','clock-dome']:
        for x in ([-8,8] if roof=='twin-domes' else [8]):
            box(x,-3,h+1.1,4,5,2.2,tone)
            rod((x,-3,h+2.2),(x,-3,h+3.6),1.8,TRIM,20)
            sphere(x,-3,h+3.7,2,DARK,12,24,stretch=(1,1,.75))
            rod((x,-3,h+5),(x,-3,h+6),.12,IRON,8)
        if roof=='clock-dome':
            rod((8,-4.85,h+2.7),(8,-4.95,h+2.7),.6,WHITE,24)
    if roof=='pediment': pediment(0,-d/2-.3,h+.5,8)
    if roof=='gothic':
        for x in [-9,-4.5,0,4.5,9]:
            box(x,-5.6,h+.9,1.5,1.5,1.8,tone)
            rod((x,-5.6,h+1.8),(x,-5.6,h+4),1.1,DARK,4,0)
    if roof in ['deco','stepped','chinese']:
        for x in range(-10,11,2): box(x,-6.7,h*.52,.25,.45,h*.86,TRIM)
        for j in range(3):
            box(0,0,h+1+j*1.7,15-j*3,9-j*1.4,2.5,tone)
        if roof=='chinese':
            hipped(13,9,h+5.9,1.4,DARK)
            for x in [-6.3,6.3]:
                rod((x,0,h+6),(x,0,h+7),.17,DARK,8)
    return finish(spec['id'],spec['name'])

def modern(spec):
    w,d,h=14,12,48
    mat=BRONZE if spec.get('tone')=='gold' else PALE if len(spec['id'])%2 else BLUE
    roof=spec.get('roof','flat')
    if roof in ['mall','wave']: h=9; w=26; d=20
    if roof=='round':
        rod((0,0,0),(0,0,h),8,mat,48)
        for z in range(2,int(h),2): rod((0,0,z),(0,0,z+.06),8.02,SILVER,48)
        for i in range(32):
            a=i*math.tau/32
            rod((8.03*math.cos(a),8.03*math.sin(a),1),(8.03*math.cos(a),8.03*math.sin(a),h),.045,SILVER,5)
    elif roof=='petal':
        for i in range(3):
            a=i*math.tau/3
            rod((2.7*math.cos(a),2.7*math.sin(a),0),(2.7*math.cos(a),2.7*math.sin(a),h-i*1.7),5,mat,32,3.5)
        for z in range(2,47,2): rod((0,0,z),(0,0,z+.07),6.2,SILVER,32)
    elif roof=='portal':
        for x in [-5,5]: box(x,0,h/2,4,d,h,mat)
        box(0,0,h-7,w,d,9,mat)
        box(0,0,3,w+8,d+5,6,mat)
    else:
        box(0,0,h/2,w,d,h,mat)
        for z in range(1,int(h)):
            box(0,-d/2-.025,z,w,.06,.04,SILVER)
            box(0,d/2+.025,z,w,.06,.04,SILVER)
            box(-w/2-.025,0,z,.06,d,.04,SILVER)
            box(w/2+.025,0,z,.06,d,.04,SILVER)
        for x in range(-6,7,2):
            for y in [-d/2-.04,d/2+.04]: box(x,y,h/2,.065,.1,h,SILVER)
        if roof=='slant':
            meshpart([(-7,-6,h),(7,-6,h),(-7,6,h),(7,6,h),(-7,-6,h+7),(-7,6,h+7)],
                     [(0,1,3,2),(0,4,1),(2,3,5),(4,5,3,1),(0,2,5,4)],mat)
        if roof in ['pyramid','hip']:
            hipped(w+1,d+1,h,4,SILVER if roof=='pyramid' else DARK)
        if roof=='stepped':
            for j in range(4): box(0,0,h+j*2,12-j*2,10-j*1.5,3,mat)
        if roof=='crown':
            rod((0,0,h),(0,0,h+2),6,BRONZE,32)
            for i in range(12):
                a=i*math.tau/12
                rod((6*math.cos(a),6*math.sin(a),h),(3*math.cos(a),3*math.sin(a),h+10),.25,BRONZE,8)
        if roof=='wave':
            for x in range(-13,14):
                rod((x,-10,h+2+math.sin(x/4)),(x,10,h+2+math.sin(x/4)),.25,SILVER,8)
    box(0,0,1,w+3,d+3,2,STONE)
    return finish(spec['id'],spec['name'])

def convention(spec):
    w,d,h=spec['model_width'],spec['model_depth'],spec['model_height']
    facade(w,d,h*.4,3,TRIM)
    radius=h*.42; z=h-radius
    for x in [-w*.32,w*.32]:
        sphere(x,0,z,radius,BLUE,20,40)
        for i in range(12):
            a=i*math.tau/12
            for j in range(12):
                t=-math.pi/2+j*math.pi/12; u=t+math.pi/12
                rod((x+radius*1.005*math.cos(t)*math.cos(a),radius*1.005*math.cos(t)*math.sin(a),z+radius*1.005*math.sin(t)),
                    (x+radius*1.005*math.cos(u)*math.cos(a),radius*1.005*math.cos(u)*math.sin(a),z+radius*1.005*math.sin(u)),.18,SILVER,6)
    return finish(spec['id'],spec['name'])

def peace(spec):
    w,d,h=spec['model_width'],spec['model_depth'],spec['model_height']
    body=h*.53; tower=w*.43; offset=-d*.31
    facade(w,d,body,10,STONE)
    start=len(geometry_data.verts)
    facade(tower,tower,h*.22,3,STONE)
    geometry_data.verts[start:]=[(x,y+offset,z+body) for x,y,z in geometry_data.verts[start:]]
    rod((0,offset,h*.76),(0,offset,h-.5),tower*.73,ROOF,4,0)
    rod((0,offset,h-.5),(0,offset,h),.12,IRON,8)
    for i in range(4):
        a=i*math.pi/2+math.pi/4
        rod((tower*.73*math.cos(a),offset+tower*.73*math.sin(a),h*.76),(0,offset,h-.5),.12,TRIM,6)
    return finish(spec['id'],spec['name'])

def church(spec):
    facade(10,20,8,2,BRICK)
    hipped(11,21,8.5,4,DARK)
    box(0,-8,10,4,4,20,BRICK)
    rod((0,-8,20),(0,-8,29),3,DARK,4,0)
    for x in [-3,3]: arch(x,-10.2,2,1.6,4)
    return finish(spec['id'],spec['name'])

def arts(spec):
    box(0,0,6,23,16,12,GLASS)
    for i in range(100):
        a=i*math.tau/100
        x,y=13*math.cos(a),10*math.sin(a)
        bottom=3+1.7*math.sin(3*a)
        rod((x,y,bottom),(x,y,15),.15,BRONZE,8)
    box(0,0,15,24,17,.4,BRONZE)
    return finish(spec['id'],spec['name'])
