import argparse
import bpy
import math
import mathutils
import numpy as np
import json

# sets up  an empty for us to lock our camera to

# Create a camera and set the scale
bpy.ops.camera.georender()
bpy.context.space_data.context = 'DATA'
bpy.context.object.data.ortho_scale = 256
bpy.context.object.data.clip_end = 350

# create an empty and constrain the camera to it.
bpy.ops.object.empty_add(type='PLAIN_AXES', radius=10, view_align=False, location=(0, 0, 0))
bpy.context.space_data.context = 'OBJECT'
bpy.context.space_data.context = 'CONSTRAINT'
# damped track constraint
bpy.ops.object.constraint_add(type='DAMPED_TRACK')
bpy.context.object.constraints["Damped Track"].target = bpy.data.objects["Empty"]
bpy.context.object.constraints["Damped Track"].track_axis = 'TRACK_NEGATIVE_Z'

bpy.ops.object.constraint_add(type='LIMIT_DISTANCE')
bpy.context.object.constraints["Limit Distance"].target = bpy.data.objects["Empty"]
bpy.context.object.constraints["Limit Distance"].distance = 128


def get_DEM(filepath):
    bpy.ops.importgis.georaster("EXEC_DEFAULT", filepath=filepath, importMode='DEM_RAW')


def get_texture(filepath):
    bpy.ops.importgis.georasteself.shapenet_pathr("EXEC_DEFAULT", filepath=filepath, importMode='MESH')


def hide_model():
    for mod_obj in model_objects:
        mod_obj.hide = True
        mod_obj.hide_render = True


def show_model():
    for mod_obj in model_objects:
        mod_obj.hide = False
        mod_obj.hide_render = False


def render_to_file(path):
    ### PHOTOREALISTIC COLOR TRANSFORM CONFIG
    # From: https://blenderartists.org/t/filmic-settings-do-not-work-with-blender-command-line-rendering-help/1102112
    # See also: https://www.youtube.com/watch?v=m9AT7H4GGrA
    bpy.context.scene.view_settings.view_transform = 'Filmic'
    bpy.context.scene.view_settings.look = 'Filmic - Base Contrast'
    ###

    # Docs: https://docs.blender.org/api/2.76/bpy.types.RenderSettings.html
    bpy.context.scene.render.resolution_x = args.size
    bpy.context.scene.render.resolution_y = args.size
    bpy.context.scene.render.filepath = path
    # # TODO Figure out how to render using GPU?
    # bpy.context.scene.render.engine = 'CYCLES'
    # bpy.context.scene.cycles.device = 'GPU'
    # bpy.context.user_preferences.addons['cycles'].preferences.devices[0].use = True
    # bpy.context.user_preferences.addons['cycles'].preferences.compute_device = 'CUDA_0'
    # # bpy.context.user_preferences.addons['cycles'].preferences.compute_device_type = 'CUDA'
    bpy.ops.render.render(write_still=True)


def export_scene(path, ext='obj'):
    ext = ext.upper()
    assert ext in ['OBJ']
    if ext == 'OBJ':
        bpy.ops.export_scene.obj(filepath=path)


def add_sun():
    # See: https://docs.blender.org/manual/en/latest/render/cycles/lamps.html#sun-lamp
    # API: https://docs.blender.org/api/2.79/bpy.ops.object.html?highlight=lamp_add#bpy.ops.object.lamp_add
    # Docs on coordinate system: https://docs.blender.org/manual/en/latest/editors/3dview/navigate/align.html
    bpy.ops.object.lamp_add(type='SUN', view_align=False, shadow_soft_size=0.1, location=[1, 1, 1])
    # TODO Set sun brightness?
    # From: https://blender.stackexchange.com/questions/92332/change-value-of-sun-light-emission-strength-from-python-console-or-script
    # https://docs.blender.org/api/2.78a/bpy.types.SunLamp.html
    # bpy.context.object.data.node_tree.nodes['Emission'].inputs['Strength'].default_value = 3
    return bpy.context.object
