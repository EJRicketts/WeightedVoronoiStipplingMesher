"""
Mesh generator based on weighted voronoi stippling, where an image is taken as 
input, and its luminosity dictates mesh density.

See Github README for sources.

Author: Evan John Ricketts
Afffiliation: Cardiff University
License: MIT
Date: April 27, 2024
"""

import os
import numpy as np
from tqdm import tqdm, trange
from PIL import Image, ImageChops
import utils
from scipy.spatial import Delaunay
from scipy.ndimage import sobel, gaussian_filter, laplace
import matplotlib.pyplot as plt

# Import from files
import voronoi
import scipy

def main():
    # Input parsing
    import argparse
    default = {
        "npoin": 5000,
        "niter": 10,
        "save": False,
        "animate": False,
        "plot": False,
        "dpi": 400,
    }

    description = "Stippling mesh generation"
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('fname', type=str, help='Density image filename ')
    parser.add_argument('--niter', type=int, default=default["niter"], help='Maximum number of iterations')
    parser.add_argument('--npoin', type=int, default=default["npoin"], help='Number of points')
    parser.add_argument('--save', action='store_true', default=default["save"], help='Save computed points')
    parser.add_argument('--animate', action='store_true', default=default["animate"], help='Animate and save .gif')
    parser.add_argument('--plot', action='store_true', default=default["plot"], help='Plot final mesh')
    parser.add_argument('--dpi', type=int, default=default["dpi"], help='Set dpi of all plots')
    args = parser.parse_args()

    # Initialise inputs
    import matplotlib as mpl
    mpl.rcParams['figure.dpi'] = args.dpi
    print("Points:", args.npoin)
    print("Iterations:", args.niter)
    npoint = args.npoin
    filename = args.fname

    # Initialise output directories
    if not os.path.exists(f'out/{args.fname}'):
        os.makedirs(f'out/{args.fname}')
    else:
        import shutil
        shutil.rmtree(f'out/{args.fname}')
        os.makedirs(f'out/{args.fname}')
    if args.animate: os.makedirs(f'out/{args.fname}/frames')

    # Process input image
    image = Image.open(f'images/{filename}')
    image = np.array(image)
    # Calculate pixel intensity
    r_weight = 0.2126
    g_weight = 0.7152
    b_weight = 0.0722
    density = np.dot(image[..., :3], [r_weight, g_weight, b_weight])
    zoom = (npoint * 500) / (density.shape[0]*density.shape[1])
    zoom = int(round(np.sqrt(zoom)))
    density = scipy.ndimage.zoom(density, zoom, order=0)
    density = 1.0 - utils.normalise(density)
    density = density[::-1, :]
    density_P = density.cumsum(axis=1)
    density_Q = density_P.cumsum(axis=1)

    # Generate initial points
    points = utils.initialise_points(npoint, density)

    # Main computation loop
    image_files = []
    for i in trange(args.niter):
        regions, points = voronoi.centroids(points, density, density_P, density_Q)

        if args.animate:
            plt.figure()
            plt.scatter(points[:,0], points[:,1], color = 'k', s=0.1, alpha=1)
            tri = Delaunay(points)
            plt.triplot(points[:,0], points[:,1], tri.simplices, color = 'k', linewidth=0.2, alpha=0.6)
            plt.gca().set_aspect('equal', adjustable='box')
            plt.axis('off')
            plt.title(f'Iteration: {i+1}')
            plt.tight_layout()
            plt.savefig(f'out/{args.fname}/frames/frame_{i}')
            image_files.append(f'out/{args.fname}/frames/frame_{i}.png')
            plt.close('all')

    # Create .gif of meshing process
    if args.animate:
        if os.path.exists(f'out/{args.fname}/anim.gif'):
            os.remove(f'out/{args.fname}/anim.gif')
        images = [Image.open(img) for img in image_files]
        images[0].save(f'out/{args.fname}/anim.gif', save_all=True, append_images=images[1:], optimize=False, duration=10, loop=0)

    # Save final array of points
    if args.save:
        np.save(f'out/{args.fname}/final_points', points)

    # Ploy final mesh
    if args.plot:
        tri = Delaunay(points)
        plt.figure()
        plt.triplot(points[:,0], points[:,1], tri.simplices, color = 'k', linewidth=0.2, alpha=0.6)
        plt.scatter(points[:,0], points[:,1], color = 'k', s=0.25, alpha=1)
        plt.gca().set_aspect('equal', adjustable='box')
        plt.axis('off')
        plt.tight_layout()
        plt.savefig(f'out/{args.fname}/final_mesh.png')
        plt.close('all')

if __name__ == "__main__":
    main()