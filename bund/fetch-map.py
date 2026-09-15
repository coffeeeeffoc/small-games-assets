"""Fetch a fixed, reviewable OSM extract; geometry is ODbL, not imagery."""
import json
import sys
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urlencode

query = '''[out:json][timeout:90];
(
  way[building](31.222,121.480,31.254,121.518);
  relation[building](31.222,121.480,31.254,121.518);
  way[highway~"primary|secondary|tertiary|residential|pedestrian"](31.222,121.480,31.254,121.518);
  way[natural=water](31.222,121.480,31.254,121.518);
  way[waterway](31.222,121.480,31.254,121.518);
  way[leisure=park](31.222,121.480,31.254,121.518);
  relation[natural=water](31.222,121.480,31.254,121.518);
);out body geom;'''
root = Path(__file__).resolve().parent / 'reference'
root.mkdir(exist_ok=True)
pois = '--pois' in sys.argv
if pois:
    query = '[out:json][timeout:45];nwr[name~"半岛|外滩源|美术馆|金融中心|复星|英国领事|外白渡|人民英雄|陈毅"](31.222,121.480,31.254,121.518);out body geom;'
request = Request('https://overpass-api.de/api/interpreter',
                  data=urlencode({'data':query}).encode(),
                  headers={'User-Agent':'BundEnvironmentStudy/1.0'})
with urlopen(request, timeout=120) as response:
    result = json.load(response)
assert result.get('elements') and not result.get('remark'), result.get('remark')
(root/('osm-pois.json' if pois else 'osm-extract.json')).write_text(json.dumps(result, ensure_ascii=False), encoding='utf-8')
(root/('pois.overpass' if pois else 'query.overpass')).write_text(query, encoding='utf-8')
print('OSM_ELEMENTS', len(result['elements']))
for item in result['elements']:
    tags=item.get('tags',{})
    if tags.get('building') and tags.get('name'):
        print(item['id'],tags.get('name'),tags.get('height'),tags.get('building:levels'))
