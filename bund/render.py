"""Re-render saved sources without rebuilding geometry or exporting GLB."""
import bpy
import json
import math
import sys
from pathlib import Path
from mathutils import Vector

root=Path(__file__).resolve().parent
manifest=json.loads((root/'manifest.json').read_text(encoding='utf-8'))
selected=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
def load(filename):
    bpy.ops.wm.open_mainfile(filepath=str(root/'source'/filename))
    prefs=bpy.context.preferences.addons['cycles'].preferences
    try:
        prefs.compute_device_type='OPTIX'; prefs.get_devices()
        for d in prefs.devices: d.use=d.type=='OPTIX'
        if any(d.use for d in prefs.devices): bpy.context.scene.cycles.device='GPU'
    except (TypeError,RuntimeError): pass
    return bpy.context.scene

def render(scene,filename):
    camera=scene.camera; width=scene.render.resolution_x; height=scene.render.resolution_y
    span=camera.data.ortho_scale if camera.data.type=='ORTHO' else 4*math.tan(camera.data.angle_x/2)
    caption=bpy.data.objects['Map attribution']; caption.data.size=span/190
    caption.location=(-span*.48,-span*height/width*.47,-2)
    scene.render.filepath=str(root/'previews'/filename)
    bpy.ops.render.render(write_still=True)

scene=load('bund-environment.blend')
for filename,location,target,size,width,height in manifest['views']:
    if selected and filename not in selected: continue
    camera=scene.camera; camera.data.type='PERSP' if filename=='pudong-from-bund.png' else 'ORTHO'
    camera.data.lens=24; camera.data.ortho_scale=size; camera.location=location
    camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler()
    scene.render.resolution_x=width; scene.render.resolution_y=height
    if filename=='bund-waterfront.png':
        bpy.data.collections['02 陆家嘴地标'].hide_render=True
        for o in bpy.data.collections['04 周边建筑轮廓'].objects: o.hide_render=o.get('map_center_x',0)>150
    render(scene,filename)
    bpy.data.collections['02 陆家嘴地标'].hide_render=False
    for o in bpy.data.collections['04 周边建筑轮廓'].objects: o.hide_render=False
for filename,source in [('pudong-night.png','bund-night.blend'),('asset-library.png','bund-asset-library.blend')]:
    if selected and filename not in selected: continue
    render(load(source),filename)
print('BUND_RENDER_OK',flush=True)
