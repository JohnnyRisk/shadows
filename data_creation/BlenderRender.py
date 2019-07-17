import sys, os, math, time, random, subprocess
import numpy as np
import bpy


class BlenderRender:
    def __init__(self, gpu, ortho_scale=256):
        if gpu:
            self.switchToGPU()
        self.delete(lambda x: x.name != 'Camera')
        self.ortho_scale = ortho_scale
        self.setup_camera(ortho_scale=self.ortho_scale)
        self.create_sun(energy=0.5, size=0.1)
        bpy.data.worlds['World'].horizon_color = (0, 0, 0)
        bpy.data.scenes['Scene'].render.resolution_percentage = 100
        #self.__wall()

    def write(self, path, name, extension='png'):
        bpy.context.scene.render.filepath = os.path.join(path, name + '.' + extension)
        bpy.ops.render.render(write_still=True)

    def switchToGPU(self, verbose=True):
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
        """
        for scene in bpy.data.scenes:
            scene.cycles.device = 'GPU'
        bpy.context.user_preferences.addons['cycles'].preferences.compute_device_type = 'CUDA'
        bpy.context.user_preferences.addons['cycles'].preferences.devices[0].use = True
        if verbose:
            print('after changing settings: ', bpy.context.scene.cycles.device)
        """

    def __wall(self):
        bpy.ops.mesh.primitive_plane_add()
        bpy.data.objects['Plane'].location = [0, 10, 0]
        bpy.data.objects['Plane'].rotation_euler = [math.pi / 3., 0, 0]
        bpy.data.objects['Plane'].scale = [20, 20, 20]
        bpy.data.objects['Plane'].hide_render = True

    def setup_camera(self, ortho_scale=256):
        #self.select(lambda x: x.name == 'dsm_cropped')
        # Create a camera and set the scale
        cam = bpy.data.objects['Camera']
        cam.data.type = 'ORTHO'
        cam.data.ortho_scale = ortho_scale
        cam.data.clip_end = 350
        cam.location = [0.0, 0.0, 128.0]
        cam.rotation_euler = [0.0, 0.0, 0.0]

        # create an empty and constrain the camera to it.
        bpy.ops.object.empty_add(type='PLAIN_AXES', radius=10, view_align=False, location=(0, 0, 0))
        empty = bpy.data.objects['Empty']
        bpy.ops.object.select_all(action='DESELECT')
        cam.select = True
        bpy.context.scene.objects.active = cam

        # damped track constraint
        bpy.ops.object.constraint_add(type='DAMPED_TRACK')
        cam.constraints["Damped Track"].target = empty
        cam.constraints["Damped Track"].track_axis = 'TRACK_NEGATIVE_Z'

        bpy.ops.object.constraint_add(type='LIMIT_DISTANCE')
        cam.constraints["Limit Distance"].target = empty
        cam.constraints["Limit Distance"].distance = int(ortho_scale // 2)
        bpy.ops.object.select_all(action='DESELECT')

    def create_sun(self, energy, size):
        bpy.ops.object.lamp_add(type='SUN')
        sun_obj = bpy.data.objects['Sun']
        sun_obj.data.shadow_soft_size = size
        sun_obj.data.node_tree.nodes['Emission'].inputs['Strength'].default_value = energy
        bpy.ops.object.select_all(action='DESELECT')

    def hideAll(self):
        for obj in bpy.data.objects:
            obj.hide_render = True

    def __scale(self, name, size):
        obj = bpy.data.objects[name]
        for dim in range(3):
            obj.scale[dim] = size

    def __ensureList(self, inp):
        if type(inp) != list:
            inp = [inp]
        return inp

    def select(self, function):
        for obj in bpy.data.objects:
            if function(obj):
                obj.select = True
            else:
                obj.select = False

    def resize(self, names, size, dim=0):
        names = self.__ensureList(names)
        if type(names) == str:
            names = [names]
        for name in names:
            obj = bpy.data.objects[name]
            obj.dimensions[dim] = size
            scale = obj.scale[dim]
            self.__scale(name, scale)

    def translate(self, names, coords):
        names = self.__ensureList(names)
        for name in names:
            obj = bpy.data.objects[name]
            for dim in range(3):
                obj.location[dim] = coords[dim]

    def rotate(self, names, angles):
        names = self.__ensureList(names)
        for name in names:
            obj = bpy.data.objects[name]
            for dim in range(3):
                obj.rotation_euler[dim] = self.__toRadians(angles[dim])

    def delete(self, function):
        for obj in bpy.data.objects:
            if function(obj):
                obj.select = True
            else:
                obj.select = False
        bpy.ops.object.delete()

    def __toRadians(self, degree):
        return degree * math.pi / 180.

    def random(self, low, high):
        if type(high) == list:
            params = [np.random.uniform(low=low[ind], high=high[ind]) for ind in range(len(high))]
            return params
        else:
            return np.random.uniform(low=low, high=high)

    def random_camera(self, low, high):
        """
        Takes in a list of [phi, theta] for low and high and outputs x,y,z for camera position
        phi is measured where 0 is directly vertical. We will generate theta and phi and calculate x and y and z

        :param low:
        :param high:
        :return:
        """
        if type(high) == list:
            params = [np.random.uniform(low=low[ind], high=high[ind]) for ind in range(len(high))]
        else:
            raise ValueError("there is a problem with random camera")
        rho = int(self.ortho_scale // 2)
        phi = params[0]
        theta = params[1]
        x = rho * math.sin(phi) * math.cos(theta)
        y = rho * math.sin(phi) * math.sin(theta)
        z = rho * math.cos(phi)
        return [x, y, z, phi, theta]

    def sun(self, energy, sun_size):
        sun_obj = bpy.data.objects['Sun']
        sun_obj.data.shadow_soft_size = sun_size
        sun_obj.data.node_tree.nodes['Emission'].inputs['Strength'].default_value = energy

    def __select(self, function):
        for obj in bpy.data.objects:
            if function(obj):
                obj.select = True
            else:
                obj.select = False

    def duplicate(self, old, new):
        self.__select(lambda x: x.name == old)
        bpy.ops.object.duplicate()
        obj = bpy.data.objects[old + '.001']
        obj.name = new

    def sphere(self, location, scale, label='shape'):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=200, ring_count=200, location=location, size=scale)
        bpy.data.objects['Sphere'].name = label
        if 'sphere' not in bpy.data.materials:
            bpy.data.materials.new('sphere')
        bpy.ops.object.material_slot_add()
        bpy.data.objects[label].data.materials[0] = bpy.data.materials['sphere']

    def spotlight(self, x, y, z, rot_x, rot_y, rot_z):
        spot = bpy.data.objects['Spot']
        spot.location = [x, y, z]
        spot.rotation_euler = [self.__toRadians(rot_x), self.__toRadians(rot_y), self.__toRadians(rot_z)]
