# -----------------------------------------------------------------------------
# Weighted Voronoi Stippler
# Copyright (2017) Nicolas P. Rougier - BSD license
# -----------------------------------------------------------------------------
import numpy as np
import scipy.spatial
from numba import prange

def rasterize_outline(V):
    n = len(V)
    X, Y = V[:, 0], V[:, 1]
    ymin = int(np.ceil(Y.min()))
    ymax = int(np.floor(Y.max()))
    points = np.zeros((2+(ymax-ymin)*2, 3), dtype=int)
    index = 0
    for y in prange(ymin, ymax+1):
        segments = []
        for i in range(n):
            index1, index2 = (i-1) % n , i
            y1, y2 = Y[index1], Y[index2]
            x1, x2 = X[index1], X[index2]
            if y1 > y2:
                y1, y2 = y2, y1
                x1, x2 = x2, x1
            elif y1 == y2:
                continue
            if (y1 <= y < y2) or (y == ymax and y1 < y <= y2):
                segments.append((y-y1) * (x2-x1) / (y2-y1) + x1)
        segments.sort()
        for i in range(0, (2*(len(segments)//2)), 2):
            x1 = int(np.ceil(segments[i]))
            x2 = int(np.ceil(segments[i+1]))
            points[index] = x1, x2, y
            index += 1
    return points[:index]

def weighted_centroid_outline(V, P, Q):
    O = rasterize_outline(V)
    X1, X2, Y = O[:,0], O[:,1], O[:,2]

    Y = np.minimum(Y, P.shape[0]-1)
    X1 = np.minimum(X1, P.shape[1]-1)
    X2 = np.minimum(X2, P.shape[1]-1)
        
    d = (P[Y,X2]-P[Y,X1]).sum()
    x = ((X2*P[Y,X2] - Q[Y,X2]) - (X1*P[Y,X1] - Q[Y,X1])).sum()
    y = (Y * (P[Y,X2] - P[Y,X1])).sum()
    if d:
        return [x/d, y/d]
    return [x, y]
    
def in_box(points, bbox):
    return np.logical_and(
        np.logical_and(bbox[0] <= points[:, 0], points[:, 0] <= bbox[1]),
        np.logical_and(bbox[2] <= points[:, 1], points[:, 1] <= bbox[3]))

def voronoi(points, bbox): 
    # Select points inside the bounding box
    i = in_box(points, bbox)

    # Mirror points
    points_center = points[i, :]
    points_left = np.copy(points_center)
    points_left[:, 0] = bbox[0] - (points_left[:, 0] - bbox[0])
    points_right = np.copy(points_center)
    points_right[:, 0] = bbox[1] + (bbox[1] - points_right[:, 0])
    points_down = np.copy(points_center)
    points_down[:, 1] = bbox[2] - (points_down[:, 1] - bbox[2])
    points_up = np.copy(points_center)
    points_up[:, 1] = bbox[3] + (bbox[3] - points_up[:, 1])
    points = np.append(points_center,
                       np.append(np.append(points_left, points_right, axis=0),
                                 np.append(points_down, points_up, axis=0),
                                 axis=0), axis=0)
    # Compute Voronoi
    vor = scipy.spatial.Voronoi(points)

    # Filter regions
    epsilon = 0.1
    regions = []
    for region in vor.regions:
        flag = True
        for index in region:
            if index == -1:
                flag = False
                break
            else:
                x = vor.vertices[index, 0]
                y = vor.vertices[index, 1]
                if not(bbox[0]-epsilon <= x <= bbox[1]+epsilon and
                       bbox[2]-epsilon <= y <= bbox[3]+epsilon):
                    flag = False
                    break
        if region != [] and flag:
            regions.append(region)
    vor.filtered_points = points_center
    vor.filtered_regions = regions
    return vor

def centroids(points, density, density_P=None, density_Q=None):
    X, Y = points[:,0], points[:, 1]
    xmin, xmax = 0, density.shape[1]
    ymin, ymax = 0, density.shape[0]
    bbox = np.array([xmin, xmax, ymin, ymax])
    vor = voronoi(points, bbox)
    regions = vor.filtered_regions
    centroids = []
    for region in regions:
        vertices = vor.vertices[region + [region[0]], :]
        centroid = weighted_centroid_outline(vertices, density_P, density_Q)
        centroids.append(centroid)
    return regions, np.array(centroids)
