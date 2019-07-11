# From: https://caretdashcaret.com/2015/05/19/how-to-run-blender-headless-from-the-command-line-without-the-gui/
# See also: https://blender.stackexchange.com/questions/1101/blender-rendering-automation-build-script
# See also: https://stackoverflow.com/questions/14982836/rendering-and-saving-images-through-blender-python

import argparse
import bpy
import math
import mathutils
import numpy as np
import json


# import pandas as pd # Non-trivial: see scripts/blender-pip-install.py


def get_args():
    parser = argparse.ArgumentParser()

    # get all script args
    _, all_arguments = parser.parse_known_args()
    double_dash_index = all_arguments.index('--')
    script_args = all_arguments[double_dash_index + 1:]

    # add parser rules
    parser.add_argument('-i', '--input', default='../trees/data/blends/Tree.blend', help='input model file')
    parser.add_argument('-n', '--n_samples', type=int, default=10,
                        help='# samples, where one sample == one rendered image == one camera location == one CSV containing all occupancy coordinates and values, transformed to a camera-centered coordinate system. ')
    parser.add_argument('-k', '--k_occupancy_samples', type=int, default=1024,
                        help='# of occupancy coordinates to sample and compute whether they are occupied. All coordinates are transformed to camera coordinates and output to a CSV for each camera location')
    parser.add_argument('-p', '--bbox_pad_ratio', type=float, default=.1,
                        help='Fraction to scale the object bbox for sampling random occupancy point coordinates')
    parser.add_argument('-s', '--size', type=int, default=1024,
                        help='width and height of (square) rendered image in pixels')
    parser.add_argument('--viz_occupancy', type=bool, default=False,
                        help='render the occupancy points (with the original object hidden) and output to separate file')
    parser.add_argument('-o', '--out', help="output file basename/prefix (no extension)")
    parsed_script_args, _ = parser.parse_known_args(script_args)
    return parsed_script_args


args = get_args()


def render_occupancy_to_file(basepath, hide_model=True):
    if hide_model:
        hide_model()
    show_occupancy_cubes()
    render_to_file(basepath + '.viz_occupancy.png')
    hide_occupancy_cubes()
    if hide_model:
        show_model()


OCC_CUBE_KEY = '_occ'


def add_occupancy_cubes():
    for obj in bpy.context.scene.objects.values():
        if OCC_CUBE_KEY in obj:
            return

    green = bpy.data.materials.new("green")
    green.diffuse_color = np.array([46., 204., 113.]) / 255
    red = bpy.data.materials.new("red")
    red.diffuse_color = np.array([231., 76., 60.]) / 255
    for occ_point, is_occ in zip(occ_points, is_occupied):
        if is_occ:
            bpy.ops.mesh.primitive_cube_add(view_align=False, radius=0.1, location=occ_point)
            bpy.context.object.active_material = green if is_occ else red
            bpy.context.object[OCC_CUBE_KEY] = 1


def show_occupancy_cubes():
    """
    Intelligently adds/generates the cubes if not already added, otherwise sets them to be visible.
    """
    just_added = False
    for obj in bpy.context.scene.objects.values():
        if OCC_CUBE_KEY in obj:
            break
    else:
        add_occupancy_cubes()
        just_added = True

    if not just_added:
        for obj in bpy.context.scene.objects.values():
            if OCC_CUBE_KEY in obj:
                obj.hide = False
                obj.hide_render = False


def hide_occupancy_cubes():
    for obj in bpy.context.scene.objects.values():
        if OCC_CUBE_KEY in obj:
            obj.hide = True
            obj.hide_render = True


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


def import_scene(path):
    old_objs = bpy.context.scene.objects.values()

    input_ext = path.split('.')[-1].upper()
    assert input_ext in ['BLEND', '3DS', 'OBJ']
    if input_ext == 'BLEND':
        bpy.ops.wm.open_mainfile(filepath=path)
    elif input_ext == '3DS':
        bpy.ops.import_scene.autodesk_3ds(filepath=path)
    elif input_ext == 'OBJ':
        bpy.ops.import_scene.obj(filepath=path)

    return [obj for obj in bpy.context.scene.objects.values() if not obj in old_objs]


def export_scene(path, ext='obj'):
    ext = ext.upper()
    assert ext in ['OBJ']
    if ext == 'OBJ':
        bpy.ops.export_scene.obj(filepath=path)


def get_objects_bbox(objs):
    # Currently ignores non-visible objects and non-mesh objects
    is_visible_mesh = lambda obj: obj.type == 'MESH' and not obj.hide and not obj.hide_render
    objs = [obj for obj in objs if is_visible_mesh(obj)]
    obj_bboxes = np.vstack([obj.bound_box for obj in model_objects])  # One 8x3 array per object, vstacked.
    bbox_min = obj_bboxes.min(axis=0)
    bbox_max = obj_bboxes.max(axis=0)
    return bbox_min, bbox_max


def pad_bbox(bbox_min, bbox_max, pad_ratio=0):
    bbox_size = bbox_min - bbox_max
    bbox_min -= bbox_size * pad_ratio
    bbox_max += bbox_size * pad_ratio
    return bbox_min, bbox_max


def add_sun():
    # See: https://docs.blender.org/manual/en/latest/render/cycles/lamps.html#sun-lamp
    # API: https://docs.blender.org/api/2.79/bpy.ops.object.html?highlight=lamp_add#bpy.ops.object.lamp_add
    # Docs on coordinate system: https://docs.blender.org/manual/en/latest/editors/3dview/navigate/align.html
    bpy.ops.object.lamp_add(type='SUN', view_align=False, location=[1, 1, 1])
    # TODO Set sun brightness?
    # From: https://blender.stackexchange.com/questions/92332/change-value-of-sun-light-emission-strength-from-python-console-or-script
    # https://docs.blender.org/api/2.78a/bpy.types.SunLamp.html
    # bpy.context.object.data.node_tree.nodes['Emission'].inputs['Strength'].default_value = 3
    return bpy.context.object


# def move_sun(xyz):
#     for obj in bpy.context.scene.objects:
#         if obj.type == 'SUN':
#             obj.location = xyz
#             return


def get_random_sun_location(min_inclination=math.radians(30)):
    inclination = np.random.uniform(min_inclination, math.radians(90))
    azimuth = np.random.uniform(math.radians(360))
    location = mathutils.Vector([1, 0, 0])
    rotation = mathutils.Euler([0, -inclination, azimuth])
    location.rotate(rotation)
    return location


def add_camera():
    # Don't add a second camera.
    for obj in bpy.context.scene.objects:
        if obj.type == 'CAMERA':
            return

    # Initial camera rotation is looking "down" the z-axis (as if from above), with positive X to right, and positive Y to top.
    # bpy.ops.object.camera_add(view_align=False, location=CAMERA_LOCATION, rotation=list(map(math.radians, [94,0,180])))
    bpy.ops.object.camera_add(view_align=False, location=[0, 0, 0], rotation=[0, 0, 0])

    # From: https://blender.stackexchange.com/questions/76007/script-to-add-a-number-of-objects-cameras-to-a-scene-but-cannot-rename-data-obj
    # > After running a primitive_add operator the context object will be the newly created object.
    camera = bpy.context.object

    # Set camera as the active camera for the scene.
    # From: https://www.blender.org/forum/viewtopic.php?t=19022
    bpy.context.scene.camera = camera
    return camera


# def move_camera(xyz):
#     for obj in bpy.context.scene.objects:
#         if obj.type == 'CAMERA':
#             obj.location = xyz
#             return


def get_random_camera_location(camera, target_bbox_minmax, height_limits=(3, 15), distance_limits_ratio=(0.5, 2)):
    # Docs on coordinate system: https://docs.blender.org/manual/en/latest/editors/3dview/navigate/align.html
    # "Walk mode" might be useful for generating synthetic "street view" images:
    # https://docs.blender.org/manual/en/latest/editors/3dview/navigate/walk_fly.html#walk-mode

    bbox_max_size = (target_bbox_minmax[1] - target_bbox_minmax[0]).max()
    # FIXME: Handle aspect ratio based on width & height? Right now this might require a 1:1 aspect.
    min_fov = min(camera.data.angle_x, camera.data.angle_y)
    optimal_distance = 0.5 * bbox_max_size / np.tan(min_fov / 2)
    min_distance = (target_bbox_minmax[1] - target_bbox_minmax[0])[:2].max()
    distance_limits = (optimal_distance - min_distance) * np.array(distance_limits_ratio) + min_distance

    random_distance = np.random.uniform(*distance_limits)
    random_height = np.random.uniform(*height_limits)
    random_direction = np.random.uniform(0, 2 * np.pi)
    bbox_center = (target_bbox_minmax[0] + target_bbox_minmax[1]) / 2
    inclination = np.arctan((random_height - bbox_center[2]) / random_distance)

    # rel_location = [
    #     random_distance * np.cos(random_direction),
    #     random_distance * np.sin(random_direction),
    #     random_height
    # ]

    rel_location = mathutils.Vector([random_distance, 0, 0])
    rel_rotation = mathutils.Euler([0, -inclination, random_direction])
    rel_location.rotate(rel_rotation)

    abs_location = rel_location + mathutils.Vector(bbox_center)
    return abs_location


def point_camera_at_location(camera, xyz):
    # From: https://blender.stackexchange.com/questions/51563/how-to-automatically-fit-the-camera-to-objects-in-the-view
    # Attention: Doesn't work for us — it moves the camera location AND rotation, and is deterministic — you always get
    # the same result regardless of starting location/rotation.
    # for obj in bpy.context.scene.objects:
    #     obj.select = False
    # for obj in bpy.context.visible_objects:
    #     if not (obj.hide or obj.hide_render):
    #         obj.select = True
    # bpy.ops.view3d.camera_to_view_selected()
    # Consider "fitting" camera to the N coordinates plus some margin — see: `camera_fit_coords(scene, coordinates)`.

    vec_camera2model = mathutils.Vector(xyz) - camera.location
    # Other camera-pointing formulas: https://blender.stackexchange.com/questions/5210/pointing-the-camera-in-a-particular-direction-programmatically
    camera.rotation_euler = vec_camera2model.to_track_quat('-Z', 'Y').to_euler()


# See "FIXME" and "ATTENTION" for limitations...
def generate_occupancy_data(bbox_minmax, camera_location):
    # Docs: https://docs.blender.org/api/current/bpy.types.Scene.html?highlight=ray_cast#bpy.types.Scene.ray_cast
    # See also: https://blender.stackexchange.com/questions/31693/how-to-find-if-a-point-is-inside-a-mesh
    occ_points = np.random.uniform(size=(args.k_occupancy_samples, 3))
    occ_points = occ_points * bbox_minmax[0] + (1 - occ_points) * bbox_minmax[1]
    is_occupied = []
    occ_origin = mathutils.Vector(camera_location)  # Actually could be any point we know to be outside the model?
    for i, occ_point in enumerate(occ_points):
        if i % 1000 == 0:
            print('Ray casting occupancy point', i)
        occ_point = mathutils.Vector(occ_point)
        # ATTENTION: This is custom "occupied" logic to consider the entire leafy area of the tree as "occupied".
        # TODO: We actually need to find some kind of bounding mesh for the leafy region, OR if we use the camera
        # location as the ray_cast origin, then this might work OK as-is — the camera will consider it occupied
        # from the first leaf it passes through to the last leaf, assuming it passes through multiple leaves, and
        # those are near the outside of the tree...
        occupied = False
        ray = occ_origin - occ_point
        has_object_ahead, _, _, _, obj_ahead, _ = bpy.context.scene.ray_cast(occ_point, ray, distance=ray.length)
        if has_object_ahead:
            has_object_behind, _, _, _, obj_behind, _ = bpy.context.scene.ray_cast(occ_point, -ray)
            # FIXME Should we check to see which objects it's hitting?
            # This method will surely fail in a scene with many objects...
            # if has_object_behind and obj_behind == obj_ahead:
            if has_object_behind:
                occupied = True
        is_occupied.append(occupied)
    return occ_points, is_occupied


### Examples of other stuff
# Access all scene objects:
# print(list(bpy.context.scene.objects))

# Create cubes
# number_of_cubes = int(args.number)
# if number_of_cubes > 1:
#   for x in range(0, number_of_cubes):
#     bpy.ops.mesh.primitive_cube_add(location=(x, x, x))

# Get an object's bounding box
# np.array(bpy.context.scene.objects['Plane.005'].bound_box)
###


model_objects = import_scene(args.input)
model_bbox_minmax = get_objects_bbox(model_objects)
model_bbox_minmax = pad_bbox(*model_bbox_minmax, pad_ratio=args.bbox_pad_ratio)

sun = add_sun()
camera = add_camera()

for n in range(args.n_samples):
    sample_basename = '{prefix}_n{n}_k{k}'.format(
        prefix=args.out,
        n=n,
        k=args.k_occupancy_samples,
    )
    out_image = sample_basename + '_render.png'
    out_occupancy = sample_basename + '_occupancy.npy'
    out_viz_occupancy = sample_basename + '.viz_occupancy.png'

    # Random sun and camera locations.
    sun.location = get_random_sun_location()
    camera.location = get_random_camera_location(camera, model_bbox_minmax)
    bbox_center = (model_bbox_minmax[0] + model_bbox_minmax[1]) / 2
    point_camera_at_location(camera, bbox_center)

    # Transform occupancy point coordinates to camera-centric system.
    occ_points, is_occ_bools = generate_occupancy_data(model_bbox_minmax, camera.location)
    # Results in CRS originating at the center of the camera sensor and oriented with the camera,
    # so that the X axis is "right", the Y axis is "up", and the Z axis is out toward the viewer,
    # and therefore every object in the render has a negative Z axis value.
    # Since the camera is aimed toward the center of the model's bbox, if the camera is D distance
    # from the bbox center, then the bbox center will have the camera-relative coordinates of [0,0,-D].
    camera_crs_transform = camera.matrix_basis.inverted()
    occ_points_camera_crs = np.array([
                                         (camera_crs_transform * mathutils.Vector(p))[:]
                                         for p in occ_points])

    # Render image
    render_to_file(out_image)
    print('Wrote ' + out_image)

    # Write occupancy CSV
    od1 = occ_points_camera_crs.round(4)
    od2 = np.array(is_occ_bools).astype(int)[:, np.newaxis]
    print(od1.shape, od2.shape)
    occupancy_data = np.hstack([
        od1,
        od2,
    ])
    np.save(out_occupancy, occupancy_data)
    print('Wrote ' + out_occupancy)

    # Visualize Occupancy (Optional)
    if args.viz_occupancy:
        render_occupancy_to_file(out_viz_occupancy)
        print('Wrote ' + out_viz_occupancy)





