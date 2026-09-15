"""Small OSM geometry helpers. Coordinates are local meters, X east / Y north."""
import math
import re

ORIGIN = (121.490, 31.239)
BOUNDS = (-950, -1840, 2550, 1630)

def xy(point):
    return ((point['lon']-ORIGIN[0])*111320*math.cos(math.radians(ORIGIN[1])),
            (point['lat']-ORIGIN[1])*111320)

def area(poly):
    return sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(poly,poly[1:]+poly[:1]))/2

def rings(element):
    if element['type']=='way':
        points=[xy(p) for p in element.get('geometry',[])]
        return [points[:-1] if points and points[0]==points[-1] else points]
    parts=[[xy(p) for p in member.get('geometry',[])]
           for member in element.get('members',[]) if member.get('role') in ('outer','') and member.get('geometry')]
    result=[]
    while parts:
        chain=parts.pop()
        while chain[0]!=chain[-1]:
            for i,part in enumerate(parts):
                if chain[-1]==part[0]: chain+=part[1:]; parts.pop(i); break
                if chain[-1]==part[-1]: chain+=list(reversed(part[:-1])); parts.pop(i); break
                if chain[0]==part[-1]: chain=part[:-1]+chain; parts.pop(i); break
                if chain[0]==part[0]: chain=list(reversed(part[1:]))+chain; parts.pop(i); break
            else: break
        if len(chain)>3 and chain[0]==chain[-1]: result.append(chain[:-1])
    return result

def clip(poly):
    """Sutherland-Hodgman clipping against the delivery rectangle."""
    for axis,edge,sign in [(0,BOUNDS[0],1),(0,BOUNDS[2],-1),(1,BOUNDS[1],1),(1,BOUNDS[3],-1)]:
        output=[]
        if not poly: break
        for a,b in zip(poly[-1:]+poly[:-1],poly):
            ain=(a[axis]-edge)*sign>=0; bin=(b[axis]-edge)*sign>=0
            if ain!=bin:
                t=(edge-a[axis])/(b[axis]-a[axis])
                output.append(tuple(a[j]+t*(b[j]-a[j]) for j in [0,1]))
            if bin: output.append(b)
        poly=output
    return poly

def center(poly):
    return tuple(sum(p[i] for p in poly)/len(poly) for i in [0,1])

def inside(p, poly):
    x,y=p; hit=False
    for a,b in zip(poly,poly[1:]+poly[:1]):
        if (a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]: hit=not hit
    return hit

def number(value,default):
    match=re.search(r'\d+(?:\.\d+)?',str(value or ''))
    return float(match.group()) if match else default

def height(tags):
    if tags.get('height'): return number(tags['height'],18),'OSM height'
    if tags.get('building:levels'): return number(tags['building:levels'],5)*3.4,'OSM floors x estimated 3.4m'
    return (36 if tags.get('building') in ['commercial','office','skyscraper'] else 15),'estimated; no OSM height/floors'

def rectangle(poly, heritage=False):
    """An oriented bounding box aligned to the longest footprint edge."""
    a,b=max(zip(poly,poly[1:]+poly[:1]),key=lambda ab:math.dist(*ab))
    angle=math.atan2(b[1]-a[1],b[0]-a[0])%math.pi
    if heritage and abs(math.cos(angle))>.7: angle=(angle+math.pi/2)%math.pi
    c,s=math.cos(angle),math.sin(angle)
    u=[x*c+y*s for x,y in poly]; v=[-x*s+y*c for x,y in poly]
    uc,vc=(min(u)+max(u))/2,(min(v)+max(v))/2
    return (uc*c-vc*s,uc*s+vc*c),max(u)-min(u),max(v)-min(v),angle

if __name__=='__main__':
    assert xy({'lon':ORIGIN[0],'lat':ORIGIN[1]})==(0,0)
    assert abs(area([(0,0),(2,0),(2,3),(0,3)])-6)<1e-9
    assert inside((1,1),[(0,0),(2,0),(2,2),(0,2)])
    assert not inside((3,1),[(0,0),(2,0),(2,2),(0,2)])
    assert number('8;6',0)==8
    assert height({'height':'632 m'})==(632,'OSM height')
    assert all(BOUNDS[0]<=x<=BOUNDS[2] and BOUNDS[1]<=y<=BOUNDS[3]
               for x,y in clip([(-9999,-9999),(9999,-9999),(9999,9999),(-9999,9999)]))
    print('GEOGRAPHY_CHECK_OK')
