# coding=utf-8
import os
import glob
import sys
import time

import cv2
import numpy as np
import tensorflow as tf

sys.path.append(os.getcwd())
from nets import model_train as model
from utils.rpn_msr.proposal_layer import proposal_layer
from utils.text_connector.detectors import TextDetector

tf.app.flags.DEFINE_string('images_dir', 'asset/', '')
tf.app.flags.DEFINE_string('output_dir', 'output/res/', '')
tf.app.flags.DEFINE_string('gpu', '0', '')
tf.app.flags.DEFINE_string('checkpoint_dir', 'checkpoints_mlt/', '')
FLAGS = tf.app.flags.FLAGS


# def get_images():
#     files = []
#     exts = ['jpg', 'png', 'jpeg', 'JPG']
#     for parent, dirnames, filenames in os.walk(FLAGS.images_dir):
#         for filename in filenames:
#             for ext in exts:
#                 if filename.endswith(ext):
#                     files.append(os.path.join(parent, filename))
#                     break
#                 print('Find {} images'.format(len(files)))
#     return files

def get_images():
    image_files = glob.glob(os.path.join(FLAGS.images_dir, '*.png'))
    print("Find {} images".format(len(image_files)))
    return image_files


def resize_image(img):
    img_size = img.shape
    im_size_min = np.min(img_size[0:2])
    im_size_max = np.max(img_size[0:2])

    im_scale = float(600) / float(im_size_min)
    if np.round(im_scale * im_size_max) > 1200:
        im_scale = float(1200) / float(im_size_max)
    new_h = int(img_size[0] * im_scale)
    new_w = int(img_size[1] * im_scale)

    new_h = new_h if new_h // 16 == 0 else (new_h // 16 + 1) * 16
    new_w = new_w if new_w // 16 == 0 else (new_w // 16 + 1) * 16

    re_im = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
    return re_im, (new_h / img_size[0], new_w / img_size[1])


def main(argv=None):
    os.makedirs(FLAGS.output_dir, exist_ok=True)
    os.environ['CUDA_VISIBLE_DEVICES'] = FLAGS.gpu

    with tf.get_default_graph().as_default():
        input_image = tf.placeholder(tf.float32, shape=[None, None, None, 3], name='input_image')
        input_im_info = tf.placeholder(tf.float32, shape=[None, 3], name='input_im_info')

        global_step = tf.get_variable('global_step', [], initializer=tf.constant_initializer(0), trainable=False)

        bbox_pred, cls_pred, cls_prob = model.model(input_image)
        
        variable_averages = tf.train.ExponentialMovingAverage(0.997, global_step)
        saver = tf.train.Saver(variable_averages.variables_to_restore())
        
        with tf.Session(config=tf.ConfigProto(allow_soft_placement=True)) as sess:
            ckpt_state = tf.train.get_checkpoint_state(FLAGS.checkpoint_dir)
            model_path = os.path.join(FLAGS.checkpoint_dir, os.path.basename(ckpt_state.model_checkpoint_path))
            print('Restore from {}'.format(model_path))
            saver.restore(sess, model_path)
            
            im_fn_list = get_images()
            for im_fn in im_fn_list:
                print('===============')
                print(im_fn)
                output_file = os.path.join(FLAGS.output_dir, os.path.splitext(os.path.basename(im_fn))[0]) + ".txt"
                if os.path.isfile(output_file):
                    print("{} exists".format(output_file))
                    continue

                start = time.time()
                try:
                    im = cv2.imread(im_fn)[:, :, ::-1]
                except:
                    print("Error reading image {}!".format(im_fn))
                    cost_time = (time.time() - start)
                    print("cost time: {:.2f}s".format(cost_time))
                    continue

                ## TODO threshold and check if image is empty
                _, thresh = cv2.threshold(cv2.cvtColor(im, cv2.COLOR_BGR2GRAY), 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
                if len(np.unique(thresh)) == 1:
                    print("Image is empty. Passing")
                    cost_time = (time.time() - start)
                    print("cost time: {:.2f}s".format(cost_time))
                    continue

                img, (rh, rw) = resize_image(im)
                h, w, c = img.shape
                print("IMAGE SHAPE:", img.shape)
                im_info = np.array([h, w, c]).reshape([1, 3])
                bbox_pred_val, cls_prob_val = sess.run([bbox_pred, cls_prob],
                                                       feed_dict={input_image: [img],
                                                                  input_im_info: im_info})

                textsegs, _ = proposal_layer(cls_prob_val, bbox_pred_val, im_info)
                scores = textsegs[:, 0]
                textsegs = textsegs[:, 1:5]

                textdetector = TextDetector(DETECT_MODE='O')
                boxes = textdetector.detect(textsegs, scores[:, np.newaxis], img.shape[:2])
                boxes = np.array(boxes, dtype=np.int)

                cost_time = (time.time() - start)
                print("cost time: {:.2f}s".format(cost_time))

                # for i, box in enumerate(boxes):
                #     cv2.polylines(img, [box[:8].astype(np.int32).reshape((-1, 1, 2))], True, color=(0, 255, 0),
                #                   thickness=2)
                # img = cv2.resize(img, None, None, fx=1.0 / rh, fy=1.0 / rw, interpolation=cv2.INTER_LINEAR)
                # cv2.imwrite(os.path.join(FLAGS.output_dir, os.path.basename(im_fn)), img[:, :, ::-1])

                boxes = boxes.astype(np.float)
                boxes[:, [0, 2, 4, 6]] *= 1.0 / rw
                boxes[:, [1, 3, 5, 7]] *= 1.0 / rh
                boxes = boxes.astype(np.int)

                with open(output_file, 'w') as f:
                    for i, box in enumerate(boxes):
                        line = ",".join(str(box[k]) for k in range(8))
                        line += "," + str(scores[i]) + "\r\n"
                        f.writelines(line)

if __name__ == '__main__':
    tf.app.run()
