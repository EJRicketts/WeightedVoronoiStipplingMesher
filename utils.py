import numpy as np

def scale_image(image, min_val, max_val):
    image_scaled = (image - np.min(image)) / (np.max(image) - np.min(image))
    image_scaled = image_scaled * (max_val - min_val) + min_val
    
    return image_scaled

def normalise(D):
    Vmin, Vmax = D.min(), D.max()
    if Vmax - Vmin > 1e-5:
        D = (D-Vmin)/(Vmax-Vmin)
    else:
        D = np.zeros_like(D)
    return D

def initialise_points(n, D):
    samples = []
    while len(samples) < n:
        X = np.random.uniform(0, D.shape[1], 10*n)
        Y = np.random.uniform(0, D.shape[0], 10*n)
        P = np.random.uniform(0, 1, 10*n)
        index = 0
        while index < len(X) and len(samples) < n:
            x, y = X[index], Y[index]
            x_, y_ = int(np.floor(x)), int(np.floor(y))
            if P[index] < D[y_, x_]:
                samples.append([x, y])
            index += 1
    return np.array(samples)
