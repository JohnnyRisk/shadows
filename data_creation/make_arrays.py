import numpy as np
import argparse
import math

parser = argparse.ArgumentParser()
parser.add_argument('--sun_energy_size_low', default=[2, 0.01])
parser.add_argument('--sun_energy_size_high', default=[5, 0.5])
parser.add_argument('--sun_phi_theta_low', default=[0.0, -180.0])
parser.add_argument('--sun_phi_theta_high', default=[70.0, 180.0])
parser.add_argument('--camera_phi_theta_low', default=[0.0, -180.0])
parser.add_argument('--camera_phi_theta_high', default=[35.0, 180.0])
parser.add_argument('--dsm_theta_low', default=-180)
parser.add_argument('--dsm_theta_high', default=180)
parser.add_argument('--n_repeat', default=200)
parser.add_argument('--n_images', default=100)
parser.add_argument('--top_image', default=True, help='this takes a top view of the image first with default sun and lighting')
parser.add_argument('--save_path', default='arrays/shader.npy')
args = parser.parse_args()

size = args.n_repeat * args.n_images

def random(low, high):
    if type(high) == list:
        params = [np.random.uniform(low=low[ind], high=high[ind]) for ind in range(len(high))]
    else:
        params = np.random.uniform(low=low, high=high)
    return params


def __toRadians(degree):
    return degree * math.pi / 180.


def spherical2Cartesian(phi_theta, rho=1.0):
    phi, theta = phi_theta
    phi = __toRadians(phi)
    theta = __toRadians(theta)
    x = rho * math.sin(phi) * math.cos(theta)
    y = rho * math.sin(phi) * math.sin(theta)
    z = rho * math.cos(phi)
    return [x, y, z, phi, theta]


# this will output a list of lists that has arguments
# Sun: [x,y,z,phi,theta, energy, size] followed by Camera: [x,y,z,phi,theta] then DSM: theta. should
# have a size args.size x 13
default_top = [0.0, 0.0, 1.0, 0.0, 0.0, 3.0, 0.1, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0]

if args.top_image:
    params = [spherical2Cartesian(random(args.sun_phi_theta_low, args.sun_phi_theta_high)) + \
              random(args.sun_energy_size_low, args.sun_energy_size_high) + \
              spherical2Cartesian(random(args.camera_phi_theta_low, args.camera_phi_theta_high)) + \
              [random(args.dsm_theta_low, args.dsm_theta_high)] if (i%args.n_repeat != 0) else default_top \
              for i in range(size)]
else:
    params = [spherical2Cartesian(random(args.sun_phi_theta_low, args.sun_phi_theta_high)) + \
              random(args.sun_energy_size_low, args.sun_energy_size_high) + \
              spherical2Cartesian(random(args.camera_phi_theta_low, args.camera_phi_theta_high)) + \
              [random(args.dsm_theta_low, args.dsm_theta_high)] for i in range(size)]

np.save(args.save_path, params)
