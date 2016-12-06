import numpy as np
import random

def kmeans(X, K, maxIters = 10, plot_progress = None):

    centroids = []
    for i in range(K):
        centroids.append(X[random.choice(np.arange(len(X))), :])
    for i in range(maxIters):
        # Cluster Assignment step
        C = np.array([np.argmin([np.dot(x_i-y_k, x_i-y_k) for y_k in centroids]) for x_i in X])
        # Move centroids step
        centroids = [X[C == k].mean(axis = 0) for k in range(K)]
        if plot_progress != None: plot_progress(X, C, np.array(centroids))
    return np.array(centroids) , C