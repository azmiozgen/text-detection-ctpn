import argparse
import os

import numpy as np

from shapely.geometry import Polygon
from shapely.ops import cascaded_union


def convert2polygon(bbox):
    assert len(bbox) == 8, bbox
    return Polygon([bbox[6:8], bbox[4:6], bbox[2:4], bbox[0:2]])

def almost_contains(p1, p2, epsilon=1e-2):
    if p1.area >= p2.area:
        return (p2.difference(p1).area / p1.area) < epsilon
    else:
        return False

def merge_polygons(p1, p2):
    p3 = cascaded_union([p1, p2])
    try:
        bbox_merged = np.vstack((p3.minimum_rotated_rectangle.exterior.coords.xy)).flatten(order='F')[:-2].astype(int)
#         bbox_merged = np.vstack((p3.exterior.coords.xy)).flatten(order='F')[:-2].astype(int)
    except AttributeError:
#         return [bbox1, bbox2]
        return []
    return [bbox_merged]

def in_same_line(bbox1, bbox2, epsilon=2e-1):
    bbox1_mean_y = np.mean(bbox1[[1, 3, 5, 7]])
    bbox2_mean_y = np.mean(bbox2[[1, 3, 5, 7]])
    bbox1_height = np.max(bbox1[[1, 3, 5, 7]]) - np.min(bbox1[[1, 3, 5, 7]])
    bbox2_height = np.max(bbox2[[1, 3, 5, 7]]) - np.min(bbox2[[1, 3, 5, 7]])
    return np.abs(bbox1_mean_y - bbox2_mean_y) / np.minimum(bbox1_height, bbox2_height) < epsilon

def merge_all(bboxes, containment_epsilon=1e-2, same_line_epsilon=2e-1):
    _merged_bboxes = []
    merge_counter = 0
    # print("Bbox count:", len(bboxes))
    for bbox1 in bboxes:
        for bbox2 in bboxes:

            ## If same boxes, pass
            if np.all(np.array(bbox1) == np.array(bbox2)):
                continue

            p1 = convert2polygon(bbox1)
            p2 = convert2polygon(bbox2)

            ## If bbox1 is almost a sub box, break
            if almost_contains(p2, p1, epsilon=containment_epsilon):
                break

            ## If not in same line, pass
            if in_same_line(bbox1, bbox2, epsilon=same_line_epsilon):
                if p1.intersects(p2):
                    merged = merge_polygons(p1, p2)
                    _merged_bboxes.extend(merged)
                    merge_counter += 1
                    break
        else:
            _merged_bboxes.extend([bbox1])
    # print(merge_counter, "merged")
    _merged_bboxes = np.unique(np.array(_merged_bboxes), axis=0)
    if merge_counter > 0:
        return merge_all(_merged_bboxes, 
                         containment_epsilon=containment_epsilon, 
                         same_line_epsilon=same_line_epsilon)
    else:
        return bboxes

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--coord_file", type=str, required=True, help="Line coordinates file")
    parser.add_argument("-o", "--output", type=str, required=True, help="Output coordinates file")
    args = vars(parser.parse_args())
    OUTPUT_FILE = args['output']
    COORD_FILE = args['coord_file']

    if os.path.isfile(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)

    ## Get tile line coordinates
    bboxes = np.loadtxt(COORD_FILE, delimiter=',', dtype=int)

    ## Merge bboxes
    merged_bboxes = merge_all(bboxes, 
                              containment_epsilon=1e-2, 
                              same_line_epsilon=2e-1)

    ## Write merged bboxes
    np.savetxt(OUTPUT_FILE, merged_bboxes, delimiter=',', fmt='%d')
