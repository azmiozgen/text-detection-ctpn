import argparse
import os

import cv2
import numpy as np

def tile(img, tile_ratio):
    img_h, img_w = img.shape[:2]
    img_ar = float(img_w) / img_h
    h_tile_ratio = img_ar * tile_ratio
    tile_h = int(img_h * h_tile_ratio)
    tile_w = int(img_w * tile_ratio)
    crop_coords = []
    crops = []
    for hs in range(0, img_h, int(tile_h / 2.0)):
        he = hs + tile_h
        he = min(img_h, he)
        for ws in range(0, img_w, int(tile_w / 2.0)):
            we = ws + tile_w
            we = min(img_w, we)
            _height = he - hs
            _width = we - ws
            if _height != tile_h:
                hs = he - tile_h
            if _width != tile_w:
                ws = we - tile_w
            _height = he - hs
            _width = we - ws
            crop = img[hs : he, ws : we]
            assert(_height == tile_h)
            assert(_width == tile_w)
            crops.append(crop)
            crop_coords.append([ws, hs, we, he])
    return crops, crop_coords

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--image", type=str, required=True, help="Input image file")
    parser.add_argument("-o", "--output", type=str, required=True, help="Output coordinates file")
    parser.add_argument("-t", "--tile_ratio", type=float, required=False, default=0.3, help="Tile ratio")
    args = vars(parser.parse_args())
    IMAGE_FILE = args['image']
    OUTPUT_FILE = args['output']
    TILE_RATIO = args['tile_ratio']

    # if os.path.isfile(OUTPUT_FILE):
        # print("{} exists.".format(OUTPUT_FILE))
        # exit()

    ## Read image and tile
    img = cv2.imread(IMAGE_FILE)
    crops, crop_coords = tile(img, TILE_RATIO)

    ## Save coordinates file
    np.savetxt(OUTPUT_FILE, crop_coords, delimiter=',', fmt='%d')
    print("Coordinates were written to {}".format(OUTPUT_FILE))

    tile_dir = os.path.join(os.path.dirname(OUTPUT_FILE), 'tiles')
    os.makedirs(tile_dir, exist_ok=True)

    ## Write coordinates and crops (tiles)
    crop_idx = 0
    with open(OUTPUT_FILE, 'w') as f:
        for crop, coord in zip(crops, crop_coords):
            crop_name = "crop_{:03d}.png".format(crop_idx)
            f.write(crop_name)
            f.write(' ')
            f.write(str(coord).strip('[').strip(']').replace(' ', ''))
            f.write('\n')
            cv2.imwrite(os.path.join(tile_dir, crop_name), crop)
            crop_idx += 1
    print("Crops were written to {}".format(tile_dir))
