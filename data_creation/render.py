import sys, argparse

################################
############ Setup #############
################################

parser = argparse.ArgumentParser()
parser.add_argument('--gpu', default=True, type=bool, help='gpu-enabled rendering')
parser.add_argument('--staging', default='staging', type=str, help='temp directory for copying ShapeNet files')
parser.add_argument('--output', default='output/normals/', type=str, help='save directory')
parser.add_argument('--category', default='DEM', type=str,
                    help='object category (from ShapeNet or primitive, see options in config.py)')
parser.add_argument('--dem_root_path', default='tiff_files/dems/', type=str, help='root_dir for dems')
parser.add_argument('--tex_root_path', default='tiff_files/texs/', type=str, help='rood_dir for textures')
parser.add_argument('--max_load', default=0, type=int, help='maximum number of dems to use')
parser.add_argument('--x_res', default=512, type=int, help='x resolution')
parser.add_argument('--y_res', default=512, type=int, help='x resolution')
parser.add_argument('--start', default=0, type=int, help='min image index')
parser.add_argument('--finish', default=10, type=int, help='max image index')
parser.add_argument('--array_path', default='arrays/shader.npy', type=str, help='path to array of lighting parameters')
parser.add_argument('--include', default='.', type=str, help='directory to include in python path')
parser.add_argument('--repeat', default=10, type=int, help='number of renderings per object')

# TODO : look into this for when we may have to call blender
## ignore the blender arguments
cmd = sys.argv
print(cmd)
args = cmd[cmd.index('--') + 1:]
args = parser.parse_args(args)
# args = parser.parse_args()

## blender doesn't by default include, the working
## directory, so add the repo folder manually
sys.path.append(args.include)
print(sys.path)
## grab config parameters from repo folder

## add any other libraries not by default in blender's python
## (e.g., scipy)

## import everything else
import os, random  # , math, argparse, scipy.io, scipy.stats, time, subprocess, pdb
import numpy as np
import bpy
import time
## import repo modules
from data_creation import BlenderRender, DEMRender, IntrinsicRender

# from dataset.BlenderShapenet import BlenderRender, ShapenetRender, IntrinsicRender
# from dataset.PrimitiveRender import PrimitiveRender

## convert params to lists if strings (e.g., '[0,0,0]' --> [0,0,0])
# utils.parse_attributes(args, 'theta_high', 'theta_low', 'pos_high', 'pos_low')

## use a temp folder for copying and manipulating ShapeNet objects
staging = os.path.join(args.staging, str(random.random()))

## choose a renderer based on category
loader = DEMRender.DEMRender(args.dem_root_path, args.tex_root_path, max_load=args.max_load)
# we do this before blenderrender because we neeed to initialize the camera

################################
########## Rendering ###########
################################

## standard blender operations
blender = BlenderRender.BlenderRender(args.gpu)

## rendering intrinsic images along with composite object
intrinsic = IntrinsicRender.IntrinsicRender(args.x_res, args.y_res)

## load light array created with make_array.py
movement_params = np.load(args.array_path)

blender.sphere([0, 0, 0], 100, label='sphere')

count = args.start
start_time = time.time()
while count < args.finish:

    ## load a new object from the category
    ## and copy it for shading / shape renderings
    loader.load(count)
    blender.duplicate('shape', 'shape_shading')
    blender.duplicate('shape', 'shape_normals')

    ## render it args.repeat times in different positions and orientations
    rep_time =time.time()
    for rep in range(args.repeat):
        movement_param = movement_params[count]
        sun_euler = [0.0] + list(movement_param[3:5])
        sun_light_size = list(movement_param[5:7])
        camera_loc = list(128.0 * movement_param[7:10])
        dsm_euler = [0.0, 0.0] + [movement_param[12]]
        """ print out the parameters for debugging
        print('movement_param: {}'.format(movement_param))
        print('sun_euler: {}'.format(sun_euler))
        print('sun_light_size: {}'.format(sun_light_size))
        print('camera_loc: {}'.format(camera_loc))
        print('dsm_euler: {}'.format(dsm_euler))
        """

        ## get position, orientation, and scale uniformly at random based on high / low from arguments
        # change the camera. This should still be pointing at (0,0,0) because of the constraints

        blender.translate(['Camera'], camera_loc)
        # this will rotate the sun angle (we use rotation not position because of the way blender does sun
        blender.rotate(['Sun'], sun_euler)
        # change the size and emission of the sun
        energy, sun_size = sun_light_size
        blender.sun(energy, sun_size)
        # Rotate the shape
        blender.rotate(['shape', 'shape_shading', 'shape_normals'],
                       dsm_euler)
        ## render the composite image and intrinsic images
        for mode in ['composite', 'albedo', 'depth', 'normals', 'shading', 'mask', 'specular', 'lights']:
            filename = str(count) + '_' + mode
            ## This is added because world lighting should be used with no sun lighting for albedo
            if mode=='albedo':
                blender.world_lighting(2.0)
                blender.sun(0.0, sun_size)
                intrinsic.changeMode(mode)
                blender.write(args.output, filename)
                blender.world_lighting(0.0)
                blender.sun(energy, sun_size)
            else:
                intrinsic.changeMode(mode)
                blender.write(args.output, filename)
        count += 1
    end_rep = time.time()
    ## delete object
    blender.delete(lambda x: x.name in ['shape', 'shape_shading', 'shape_normals'])
end_time = time.time()

print('rep time: {}'.format(end_rep-rep_time))
print('end time: {}'.format(end_time-start_time))

################################
########## Reference ###########
################################
"""
#### create a sphere as a shape / shading reference
blender.sphere([0, 0, 0], 100)
blender.duplicate('shape', 'shape_shading')
blender.duplicate('shape', 'shape_normals')

## render it
for mode in ['composite', 'albedo', 'depth', 'depth_hires', 'normals', 'shading', 'mask', 'specular']:
    filename = 'sphere_' + mode
    intrinsic.changeMode(mode)
    blender.write(args.output, filename)

"""
## delete it
blender.delete(lambda x: x.name in ['shape'])
