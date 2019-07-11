import bpy
import numpy as np
import os


class DEMRender:
    def __init__(self, dem_root_path, tex_root_path, max_load=-1):
        if max_load > 0:
            self.dem_paths = sorted([os.path.join(dem_root_path, dem_path) for dem_path in \
                                     os.listdir(dem_root_path)[:max_load]])
            self.tex_paths = sorted([os.path.join(tex_root_path, tex_path) for tex_path in \
                                     os.listdir(tex_root_path)[:max_load]])
        else:
            self.dem_paths = sorted([os.path.join(dem_root_path, dem_path) for dem_path in os.listdir(dem_root_path)])
            self.tex_paths = sorted([os.path.join(tex_root_path, tex_path) for tex_path in os.listdir(tex_root_path)])

        self.dem_root_path = dem_root_path
        self.tex_root_path = tex_root_path

    def load(self, index):
        bpy.ops.geoscene.clear_georef()
        self.get_DEM(self.dem_paths[index])
        self.get_texture(self.tex_paths[index])
        names = [x.name for x in bpy.data.objects if self.dem_paths[index].split('/')[-1].split('.')[0] in x.name]

        if len(names) > 1:
            print('names found more than one object named dsm')
        self.__rename(names[0], 'shape')

    def get_DEM(self, filepath):
        bpy.ops.importgis.georaster("EXEC_DEFAULT", filepath=filepath, importMode='DEM_RAW')

    def get_texture(self, filepath):
        bpy.ops.importgis.georaster("EXEC_DEFAULT", filepath=filepath, importMode='MESH')

    def __rename(self, old, new):
        bpy.data.objects[old].name = new

    def __deleteObject(self, names):
        objs = bpy.data.objects
        for name in names:
            objs.remove(objs[name], True)
