"""Offline sidewalk footprints: convex subtraction keeps intersections open."""
import math

ASPHALT_HEIGHT = .02
CURB_HEIGHT = .15
SIDEWALK_WIDTH = 3


def area(poly):
    return sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(poly,poly[1:]+poly[:1]))/2


def bounds(poly):
    return (min(p[0] for p in poly), min(p[1] for p in poly),
            max(p[0] for p in poly), max(p[1] for p in poly))


def overlaps(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def subtract(poly, cutter):
    """Partition a convex polygon into the pieces outside a CCW convex cutter."""
    edges = list(zip(cutter,cutter[1:]+cutter[:1]))
    if any(all((b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0]) <= 1e-7
               for p in poly) for a,b in edges):
        return [poly]
    outside = []
    for a,b in edges:
        if len(poly) < 3: break
        inner, outer = [], []
        def side(p): return (b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0])
        for p,q in zip(poly,poly[1:]+poly[:1]):
            dp,dq = side(p),side(q)
            (inner if dp >= 0 else outer).append(p)
            if (dp >= 0) != (dq >= 0):
                t = dp/(dp-dq)
                cross = (p[0]+t*(q[0]-p[0]),p[1]+t*(q[1]-p[1]))
                inner.append(cross); outer.append(cross)
        if len(outer) >= 3 and area(outer) > .001: outside.append(outer)
        poly = inner
    return outside


def sidewalks(roads):
    """Yield disjoint (convex footprint, top height) beside each road rectangle."""
    cuts = [(poly,height,bounds(poly)) for poly,height in roads]
    previous = []
    for poly,height,bb in cuts:
        a,b,c,d = poly
        width,length = math.dist(a,b),math.dist(b,c)
        u = ((b[0]-a[0])/width,(b[1]-a[1])/width)
        v = ((c[0]-b[0])/length,(c[1]-b[1])/length)
        outer = [(p[0]+SIDEWALK_WIDTH*(sx*u[0]+sy*v[0]),
                  p[1]+SIDEWALK_WIDTH*(sx*u[1]+sy*v[1]))
                 for p,sx,sy in [(a,-1,-1),(b,1,-1),(c,1,1),(d,-1,1)]]
        ob = bounds(outer)
        pieces = [outer]
        # Subtract carriageways first, including cross streets; then earlier sidewalks.
        for cut,h,cb in cuts + previous:
            if abs(h-height) > .01 or not overlaps(ob,cb): continue
            pieces = [part for piece in pieces
                      for part in (subtract(piece,cut) if overlaps(bounds(piece),cb) else [piece])]
            if not pieces: break
        previous.append((outer,height,ob))
        for piece in pieces:
            piece = [p for p,q in zip(piece,piece[-1:]+piece[:-1]) if math.dist(p,q) > .001]
            perimeter = sum(math.dist(p,q) for p,q in zip(piece,piece[1:]+piece[:1]))
            # Sub-centimeter clipping slivers cannot form stable Blender/Rapier faces.
            if len(piece) >= 3 and 2*area(piece) > .01*perimeter:
                yield piece,height+CURB_HEIGHT


if __name__ == '__main__':
    crossing = [([(-2,-10),(2,-10),(2,10),(-2,10)], ASPHALT_HEIGHT),
                ([(-10,-2),(10,-2),(10,2),(-10,2)], ASPHALT_HEIGHT)]
    result = list(sidewalks(crossing))
    assert result and all(abs(h-.17) < 1e-9 for _,h in result)
    for piece,_ in result:
        for road,_ in crossing:
            assert abs(sum(area(p) for p in subtract(piece,road))-area(piece)) < 1e-6
    print('SIDEWALKS_OK: 15 cm curbs; crossing carriageways stay open')
