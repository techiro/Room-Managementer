
import warnings
warnings.filterwarnings('ignore')

import datetime
import time
import picamera

import numpy as np
import os
import sys
import tensorflow as tf

from collections import defaultdict
from io import StringIO
from PIL import Image

from object_detection.utils import label_map_util
from object_detection.utils import visualization_utils as vis_util


###   TensorFlow 制御部       ####

def load_image_into_numpy_array(image):
  (im_width, im_height) = image.size
  return np.array(image.getdata()).reshape(
      (im_height, im_width, 3)).astype(np.uint8)

def run_inference_for_single_image(image, graph):
  with graph.as_default():
    with tf.Session() as sess:
      # Get handles to input and output tensors
      ops = tf.get_default_graph().get_operations()
      all_tensor_names = {output.name for op in ops for output in op.outputs}
      tensor_dict = {}
      for key in [
          'num_detections', 'detection_boxes', 'detection_scores',
          'detection_classes', 'detection_masks'
      ]:
        tensor_name = key + ':0'
        if tensor_name in all_tensor_names:
          tensor_dict[key] = tf.get_default_graph().get_tensor_by_name(
              tensor_name)
      if 'detection_masks' in tensor_dict:
        # The following processing is only for single image
        detection_boxes = tf.squeeze(tensor_dict['detection_boxes'], [0])
        detection_masks = tf.squeeze(tensor_dict['detection_masks'], [0])
        # Reframe is required to translate mask from box coordinates to image coordinates and fit the image size.
        real_num_detection = tf.cast(tensor_dict['num_detections'][0], tf.int32)
        detection_boxes = tf.slice(detection_boxes, [0, 0], [real_num_detection, -1])
        detection_masks = tf.slice(detection_masks, [0, 0, 0], [real_num_detection, -1, -1])
        detection_masks_reframed = utils_ops.reframe_box_masks_to_image_masks(
            detection_masks, detection_boxes, image.shape[0], image.shape[1])
        detection_masks_reframed = tf.cast(
            tf.greater(detection_masks_reframed, 0.4), tf.uint8)
        # Follow the convention by adding back the batch dimension
        tensor_dict['detection_masks'] = tf.expand_dims(
            detection_masks_reframed, 0)
      image_tensor = tf.get_default_graph().get_tensor_by_name('image_tensor:0')

      # Run inference
      output_dict = sess.run(tensor_dict,
                             feed_dict={image_tensor: np.expand_dims(image, 0)})

      # all outputs are float32 numpy arrays, so convert types as appropriate
      output_dict['num_detections'] = int(output_dict['num_detections'][0])
      output_dict['detection_classes'] = output_dict[
          'detection_classes'][0].astype(np.uint8)
      output_dict['detection_boxes'] = output_dict['detection_boxes'][0]
      output_dict['detection_scores'] = output_dict['detection_scores'][0]
      if 'detection_masks' in output_dict:
        output_dict['detection_masks'] = output_dict['detection_masks'][0]
  return output_dict

def confirm_and_create_dir(dirname):
    if os.path.isdir(dirname):
        pass
    else:
        os.path.mkdir(dirname)

detection_graph = tf.Graph()
with detection_graph.as_default():
  od_graph_def = tf.GraphDef()
  with tf.gfile.GFile('ssd_mobilenet_v1_coco_2018_01_28/frozen_inference_graph.pb', 'rb') as fid:
    serialized_graph = fid.read()
    od_graph_def.ParseFromString(serialized_graph)
    tf.import_graph_def(od_graph_def, name='')

label_map = label_map_util.load_labelmap('mscoco_label_map.pbtxt')
categories = label_map_util.convert_label_map_to_categories(label_map, max_num_classes=90, use_display_name=True)
category_index = label_map_util.create_category_index(categories)

###   TensorFlow 制御部 end   ####

if __name__ == "__main__":

    confirm_and_create_dir("media")
    previous_minute = datetime.datetime.now().minute
    while True:
        if previous_minute != datetime.datetime.now().minute:
            now = datetime.datetime.now()
            previous_minute = now.minute
            this_year = now.year
            this_month = now.month
            this_day = now.day
            image_save_dir = this_year + "/" + this_month + "/" + this_day
            confirm_and_create_dir(this_year)
            confirm_and_create_dir(this_year + "/" + this_month)
            confirm_and_create_dir(image_save_dir)
            image_save_path = "media/" + image_save_dir + "/" + now.hour + "_" + now.minute + ".jpg"
            with picamera.PiCamera() as camera:
                camera.resolution = (1920, 1080)
                camera.capture(image_save_path)
            media_root, media_ext = os.path.splitext(image_save_path)
                    
            image = Image.open(image_save_path)
            image_np = load_image_into_numpy_array(image)
            image_np_expanded = np.expand_dims(image_np, axis=0)
            output_dict = run_inference_for_single_image(image_np, detection_graph)

            person_index = np.where(np.array(output_dict['detection_classes']) == 1)
            pscore_array = np.array(output_dict['detection_scores'])[person_index]
            congestion = len(np.where(pscore_array >= 0.4)[0])
            print(congestion)

            vis_util.visualize_boxes_and_labels_on_image_array(
                image_np,
                output_dict['detection_boxes'],
                output_dict['detection_classes'],
                output_dict['detection_scores'],
                category_index,
                instance_masks=output_dict.get('detection_masks'),
                use_normalized_coordinates=True,
                line_thickness=8,
                min_score_thresh=0.4
                )
                
            Image.fromarray(image_np).save(media_root + "_output" + media_ext)
    
    


