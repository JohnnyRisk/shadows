import math
import bpy

def switchToGPU(verbose=True):
    if verbose:
        print('before changing settings: ', bpy.context.scene.cycles.device)
    bpy.data.scenes['Scene'].cycles.samples = 20
    bpy.data.scenes["Scene"].render.tile_x = 256
    bpy.data.scenes["Scene"].render.tile_y = 256
    bpy.data.scenes['Scene'].cycles.max_bounces = 5
    bpy.data.scenes['Scene'].cycles.caustics_reflective = False
    bpy.data.scenes['Scene'].cycles.caustics_refractive = False

    if verbose:
        print('max bounces: ', bpy.data.scenes['Scene'].cycles.max_bounces)
        print('Samples: ', bpy.data.scenes['Scene'].cycles.samples)
    bpy.data.scenes["Scene"].render.engine = 'CYCLES'

    bpy.context.scene.cycles.device = 'GPU'
    bpy.context.user_preferences.addons['cycles'].preferences.devices[0].use = True
    bpy.context.user_preferences.addons['cycles'].preferences.compute_device = 'CUDA_0'
    bpy.context.user_preferences.addons['cycles'].preferences.compute_device_type = 'CUDA'


def create_sun(energy, size):
    bpy.ops.object.lamp_add(type='SUN')
    sun_obj = bpy.data.objects['Sun']
    sun_obj.data.shadow_soft_size = size
    sun_obj.data.node_tree.nodes['Emission'].inputs['Strength'].default_value = energy
    bpy.ops.object.select_all(action='DESELECT')


def select(function):
    for obj in bpy.data.objects:
        if function(obj):
            obj.select = True
        else:
            obj.select = False


def __ensureList(inp):
    if type(inp) != list:
        inp = [inp]
    return inp


def translate(names, coords):
    names = __ensureList(names)
    for name in names:
        obj = bpy.data.objects[name]
        for dim in range(3):
            obj.location[dim] = coords[dim]


def __toRadians(degree):
    return degree * math.pi / 180.


def rotate(names, angles):
    names = __ensureList(names)
    for name in names:
        obj = bpy.data.objects[name]
        for dim in range(3):
            obj.rotation_euler[dim] = __toRadians(angles[dim])

def sun(energy, sun_size):
    sun_obj = bpy.data.objects['Sun']
    sun_obj.data.shadow_soft_size = sun_size
    sun_obj.data.node_tree.nodes['Emission'].inputs['Strength'].default_value = energy