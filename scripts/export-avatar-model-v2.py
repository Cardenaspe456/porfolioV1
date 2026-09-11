"""Export a compact static GLB and verify it by importing and rendering it again."""
import bpy
import json
import math
from pathlib import Path
from mathutils import Vector

OUT = Path(__file__).resolve().parents[1] / 'models' / 'avatar-v2'
bpy.ops.wm.open_mainfile(filepath=str(OUT / 'avatar-model-v2.blend'))
bpy.ops.object.select_all(action='DESELECT')
actor = [obj for obj in bpy.context.scene.objects
         if obj.type in {'MESH', 'CURVE'} and not any(c.name.startswith('90') for c in obj.users_collection)]
for obj in actor:
    obj.select_set(True)
bpy.context.view_layer.objects.active = actor[0]
bpy.ops.object.convert(target='MESH')
bpy.ops.object.join()
model = bpy.context.object
model.name = 'Avatar · estudio de modelado v2'
model.data.calc_loop_triangles()
original_triangles = len(model.data.loop_triangles)
if original_triangles > 60000:
    modifier = model.modifiers.new('Optimización de la copia GLB', 'DECIMATE')
    modifier.ratio = 60000 / original_triangles
    modifier.use_collapse_triangulate = True
    bpy.ops.object.modifier_apply(modifier=modifier.name)
model.data.calc_loop_triangles()
export_triangles = len(model.data.loop_triangles)
path = OUT / 'avatar-model-v2.glb'
bpy.ops.export_scene.gltf(filepath=str(path), export_format='GLB', use_selection=True,
                         export_apply=True, export_animations=False, export_yup=True,
                         export_cameras=False, export_lights=False)

# Reload the exported geometry, not the high-resolution Blender source.
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(path))
imported = [obj for obj in bpy.context.selected_objects if obj.type == 'MESH']
assert imported, 'El GLB no contiene geometría visible.'
coordinates = [obj.matrix_world @ Vector(corner) for obj in imported for corner in obj.bound_box]
minimum = [min(co[i] for co in coordinates) for i in range(3)]
maximum = [max(co[i] for co in coordinates) for i in range(3)]
assert all(math.isfinite(value) for value in minimum + maximum), 'Dimensiones no finitas.'
report = {
    'status': 'static-model-review',
    'has_rig': False,
    'has_animation': False,
    'source_triangles': original_triangles,
    'export_triangles': export_triangles,
    'glb_bytes': path.stat().st_size,
    'under_4_mib': path.stat().st_size <= 4 * 1024 * 1024,
    'roundtrip_meshes': len(imported),
    'dimensions_blender_xyz': [round(maximum[i] - minimum[i], 4) for i in range(3)],
    'reference_fidelity': 'Interpretación estilizada; pendiente de revisión del usuario.',
    'remaining_work': ['Aprobación del parecido', 'Topología para deformación', 'Rig y pesos', 'Idle y Wave', 'Pruebas web'],
}
assert report['under_4_mib'], 'El GLB supera el presupuesto de 4 MiB.'
(OUT / 'model-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf8')
scene = bpy.context.scene
scene.render.filepath = str(OUT / 'glb-preview.png')
scene.cycles.samples = 32
bpy.ops.render.render(write_still=True)
print('MODEL_REPORT', json.dumps(report, ensure_ascii=False))


