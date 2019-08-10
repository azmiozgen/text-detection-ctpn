import argparse
import glob
import os

import numpy as np

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--directory", type=str, required=True, help="Tile directory")
    parser.add_argument("-o", "--output", type=str, required=True, help="Output coordinates file")
    parser.add_argument("-t", "--tile_coord_file", type=str, required=True, help="Tile coordinates file")
    args = vars(parser.parse_args())
    TILE_DIR = args['directory']
    OUTPUT_FILE = args['output']
    TILE_COORD_FILE = args['tile_coord_file']

    if os.path.isfile(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)

    tile_coords = np.loadtxt(TILE_COORD_FILE, delimiter=' ', dtype=str)
    for tile_name, tile_coord in tile_coords:
        tile_line_coord_file = os.path.join(TILE_DIR, tile_name.replace('.png', '.txt'))

        if not os.path.isfile(tile_line_coord_file):
            #print("{} not found".format(tile_line_coord_file))
            continue
        if os.stat(tile_line_coord_file).st_size == 0:
            #print("{} is empty.".format(tile_line_coord_file))
            continue

        ## Tile reference points
        tile_coord = list(map(int, tile_coord.split(',')))
        x_ref, y_ref, _, _ = tile_coord

        ## Get tile line coordinates
        tile_line_coords = np.loadtxt(tile_line_coord_file, delimiter=',', dtype=float).reshape(-1, 9)
        tile_line_coords[tile_line_coords <= 0] = 0

        ## Update line coordinates
        tile_line_coords[:, [0, 2, 4, 6]] += x_ref
        tile_line_coords[:, [1, 3, 5, 7]] += y_ref
        tile_line_coords = tile_line_coords.astype(int)

        ## Write updated coordinates
        with open(OUTPUT_FILE, 'a') as f:
            for tile_line_coord in tile_line_coords:
                f.write(','.join(list(map(str, tile_line_coord[:8]))) + '\n')

    print("Fixed coordinates were written to {}".format(OUTPUT_FILE))


