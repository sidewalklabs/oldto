#!/usr/bin/env python3
""" Takes a .geojson file that is a feature collection and rewrites the coordinates according the
centroid of the cluster computed by the dbscan algorithm.
"""
import argparse
import json
import sys

from haversine import haversine
import numpy as np
from sklearn.cluster import DBSCAN


def get_feature_collection_from_file(input_file):
    with open(input_file) as f:
        return json.load(f)


def get_furthest_coordinate(original_coordinates, new_coordinates, ids):
    coords = zip(np.fliplr(original_coordinates), np.fliplr(new_coordinates))
    distances = np.fromiter([haversine(list(x), list(y)) for x, y in coords], dtype='float64')
    furthest_distance = distances.max()
    original_coordinate = original_coordinates[distances == furthest_distance]
    new_coordinate = np.array(new_coordinates)[distances == furthest_distance]
    furthest_id = ids[distances == furthest_distance]
    return original_coordinate, new_coordinate, furthest_distance, furthest_id


def get_centroid(points):
    sum_x = np.sum(points[:, 0])
    sum_y = np.sum(points[:, 1])
    return list((sum_x / len(points), sum_y / len(points)))


def cluster_coordinates(coordinates, epsilon, ids):
    """
    Reassign each coordinate according to the dbscan clustering algoritm.

    Args:
        coordinates: an array of coordinates ((x1, y1), (x2, y2) ... (xn, yn))
        epsilon: the haversine distance used to determine dbscan's eps neighborhoods
    Returns:
        a list where each element of the original coordinates has a new coordinate, the centroid
        of its cluster or it's original coordinate if it's a noise point.
    """
    coordinates = np.array([np.array(c) for c in coordinates])
    db = DBSCAN(eps=epsilon, metric='haversine', min_samples=2).fit(np.fliplr(coordinates))
    cluster_labels = db.labels_[db.labels_ != -1]  # cluster label for each data point
    coordinates = coordinates[db.labels_ != -1]
    ids = np.array(ids)[db.labels_ != -1]
    clusters = np.array([coordinates[cluster_labels == cluster]
                         for cluster
                         in np.unique(cluster_labels)])
    cluster_sizes = np.fromiter((len(cluster) for cluster in clusters), int)
    largest_cluster = clusters[cluster_sizes == cluster_sizes.max()][0]
    largest_cluster_size = largest_cluster.shape[0]
    cluster_centers = [
        get_centroid(cluster)
        for cluster in clusters
    ]
    coordinates_remapped_cluster_center = [
        cluster_centers[cluster_label]
        for cluster_label in cluster_labels
    ]
    original, new, furthest_distance, furthest_id = get_furthest_coordinate(
        coordinates, coordinates_remapped_cluster_center, ids)
    sys.stderr.write(f'number of clusters: {cluster_labels.shape[0]}\n')
    sys.stderr.write(f'largest cluster: {largest_cluster_size}\n')
    sys.stderr.write(f'largest cluster centroid: {get_centroid(largest_cluster)}\n')
    sys.stderr.write(f'furthest move: {original} moved to {new}, which is {furthest_distance} km, '
                     f'id: {furthest_id}\n')
    return {
        uid: coord
        for uid, coord in zip(ids, coordinates_remapped_cluster_center)
    }


def main(input_file, output_file, epsilon):
    feature_collection = get_feature_collection_from_file(input_file)
    features = [
        (feature['id'],
         (feature['geometry']['coordinates'][0], feature['geometry']['coordinates'][1]))
        for feature in feature_collection['features']
        if feature['geometry']]
    ids, coordinates = zip(*features)
    id_to_new_coordinates = cluster_coordinates(coordinates, epsilon, ids)
    n_remapped_features = 0
    for feature in feature_collection['features']:
        if feature['geometry'] and feature['id'] in id_to_new_coordinates:
            new_coordinate = id_to_new_coordinates[feature['id']]
            old_coordinate = feature['geometry']['coordinates']
            distance_km = haversine(new_coordinate, old_coordinate)
            if distance_km > 0.0001:
                n_remapped_features += 1
                feature['geometry']['coordinates'] = new_coordinate
    sys.stderr.write(f'changed the location of {n_remapped_features} features\n')

    with open(output_file, 'w') as f:
        json.dump(feature_collection, f)


if __name__ == '__main__':
    parser = argparse.ArgumentParser('implement dbscan for everyone')
    parser.add_argument('--input_file', type=str,
                        help='geojson file in needs of clustering',
                        default='data/images.geojson')
    parser.add_argument('--epsilon', type=float,
                        help='limit of haversine difference for the dbscan epsilon, in radians',
                        default=0.00017)  # used clustering.sh to experimentally determine
    parser.add_argument('--output_file', type=str,
                        help='clustered geojson file',
                        default='data/clustered.images.geojson')
    args = parser.parse_args()

    main(args.input_file, args.output_file, args.epsilon)
