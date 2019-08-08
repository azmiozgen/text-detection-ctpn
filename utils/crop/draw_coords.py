import argparse
import glob
import os

import numpy as np
import cv2

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--image", type=str, required=True, help="Input image file")
    parser.add_argument("-o", "--output", type=str, required=True, help="Output image file")
    parser.add_argument("-c", "--coord_file", type=str, required=True, help="Coordinates file")
    args = vars(parser.parse_args())
    IMAGE_FILE = args['image']
    OUTPUT_FILE = args['output']
    COORD_FILE = args['coord_file']
    THICKNESS = 2

    if not os.path.isfile(IMAGE_FILE):
        print("{} not found.".format(IMAGE_FILE))
        exit()
    if not os.path.isfile(COORD_FILE):
        print("{} not found.".format(COORD_FILE))
        exit()
    if os.stat(COORD_FILE).st_size == 0:
        print("{} is empty.".format(COORD_FILE))
        exit()

    img = cv2.imread(IMAGE_FILE)
    coords = np.loadtxt(COORD_FILE, delimiter=',', dtype=str)
    if len(coords) == 0:
        print("Coords are empty. Delimiter should be comma(,)")
        exit()

    for coord in coords:
        n = len(coord)
        if n < 4:
            print("{} has wrong coordinates. Passing".format(COORD_FILE))
            continue
        if n % 2 == 1:
            coord = coord[:n - 1]
        try:
            coord = coord.astype(int)
        except (ValueError, AttributeError):
            print("{} has wrong coordinates. Passing".format(COORD_FILE))
            continue

        random_color = (np.random.randint(256), np.random.randint(256), np.random.randint(256))
        if len(coord) == 4:
            cv2.rectangle(img, tuple(coord[:2]), tuple(coord[2:]), color=random_color, thickness=THICKNESS)
        elif len(coord) > 4:
            cv2.polylines(img, [coord.reshape((-1, 1, 2))], True, 
                          color=random_color, thickness=THICKNESS,
                          lineType=cv2.LINE_AA)

    if os.path.isfile(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)
    cv2.imwrite(OUTPUT_FILE, img)
    print("{} was written".format(OUTPUT_FILE))