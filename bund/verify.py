"""Blender --background --factory-startup --python assets/bund/verify.py"""
import bpy
import json
import math
import struct
import sys
from pathlib import Path

root = Path(__file__).resolve().parent
sys.path.insert(0,str(root))
import geography
manifest = json.loads((root / 'manifest.json').read_text(encoding='utf-8'))
specs=json.loads((root/'landmarks.json').read_text(encoding='utf-8'))
assert manifest['landmark_count']==len(specs)==67
assert len({a['id'] for a in manifest['assets']})==len(manifest['assets'])
assert len(manifest['context_buildings'])>2000
assert manifest['coordinates']['units']=='meters'
assert all(a.get('osm') and a.get('height_source') for a in manifest['assets'] if a['id'] in {s['id'] for s in specs})
expected={Path(a['file']).name for a in manifest['assets']} | set(manifest['scene_files'])
assert expected=={p.name for p in (root/'models').glob('*.glb')},'Missing or stale GLB'
heights={a['id']:a['height_m'] for a in manifest['assets'] if 'height_m' in a}
assert heights['shanghai-tower']>heights['world-financial-center']>heights['oriental-pearl']>heights['jin-mao-tower']
results = []
for path in sorted((root / 'models').glob('*.glb')):
    raw = path.read_bytes()
    magic, version, size = struct.unpack_from('<4sII', raw)
    assert magic == b'glTF' and version == 2 and size == len(raw), path.name
    length, kind = struct.unpack_from('<II', raw, 12)
    assert kind == 0x4E4F534A
    data = json.loads(raw[20:20 + length])
    assert not data.get('images'), 'Unexpected external texture dependency'
    assert all('uri' not in buffer for buffer in data.get('buffers', []))
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(path))
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']
    assert meshes, f'{path.name}: no geometry'
    triangles = 0
    for obj in meshes:
        obj.data.calc_loop_triangles()
        triangles += len(obj.data.loop_triangles)
        assert all(math.isfinite(v) for vertex in obj.data.vertices for v in vertex.co)
        assert sum(d > 1e-6 for d in obj.dimensions)>=2, f'{path.name}: degenerate bounds'
        assert obj.data.materials, f'{path.name}: missing materials'
    results.append({'file': path.name, 'triangles': triangles,
                    'mesh_objects': len(meshes), 'bytes': len(raw)})
assert len(results)==len(expected)
for filename in ['bund-environment.blend', 'bund-asset-library.blend','bund-night.blend']:
    bpy.ops.wm.open_mainfile(filepath=str(root / 'source' / filename))
    assert bpy.context.scene.camera is not None
    assert len(bpy.data.objects)>3000
    assert 'OpenStreetMap' in bpy.context.scene['attribution']
    if filename=='bund-asset-library.blend':
        assert sum(o.asset_data is not None for o in bpy.data.objects)==len(manifest['assets'])
for filename in manifest['previews']:
    raw = (root / 'previews' / filename).read_bytes()
    assert raw[:8] == b'\x89PNG\r\n\x1a\n'
    width, height = struct.unpack_from('>II', raw, 16)
    assert width >= 1600 and height >= 900
assert (root/'previews/coverage-map.svg').is_file()
(root / 'validation.json').write_text(json.dumps({
    'passed': True, 'checks': f'{len(expected)} GLB round trips; finite geometry; nondegenerate surfaces; materials; 3 blend reopen; 6 PNG dimensions; landmark sources and height ordering',
    'files': results}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('BUND_VERIFY_OK',len(results),'GLBs, 3 blend sources, 6 renders; 67 landmarks; >2000 context buildings')
