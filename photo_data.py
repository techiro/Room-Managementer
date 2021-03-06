# for AWS S3
import boto3

# logging error 
import logging
import traceback

import warnings
warnings.filterwarnings('ignore')

# raspi camera and save photo 
import datetime
import time
import picamera

# for AWS Dynamodb through soracom and aws IoT
import requests
import json 

# for object recognation
import numpy as np
import os
import sys
import tensorflow as tf
from collections import defaultdict
from io import StringIO
from PIL import Image
from object_detection.utils import label_map_util
from object_detection.utils import visualization_utils as vis_util


##   logging for debug
logging_fmt = "%(asctime)s  %(levelname)s  %(name)s \n%(message)s\n"
logging.basicConfig(filename='log/photo_data_log', level=logging.info, format=logging_fmt)
root_dir = "/home/pi/Desktop/Room-Managementer/"

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
    str_dirname = str(dirname)
    if os.path.isdir(str_dirname):
        pass
    else:
        os.makedirs(str_dirname)

detection_graph = tf.Graph()
with detection_graph.as_default():
  od_graph_def = tf.GraphDef()
  with tf.gfile.GFile(root_dir + 'ssd_mobilenet_v1_coco_2018_01_28/frozen_inference_graph.pb', 'rb') as fid:
    serialized_graph = fid.read()
    od_graph_def.ParseFromString(serialized_graph)
    tf.import_graph_def(od_graph_def, name='')

label_map = label_map_util.load_labelmap(root_dir + 'mscoco_label_map.pbtxt')
categories = label_map_util.convert_label_map_to_categories(label_map, max_num_classes=90, use_display_name=True)
category_index = label_map_util.create_category_index(categories)


class Media(object):
    def __init__(self, now_datetime):
        self.now_datetime = now_datetime
        self.create_mdeia_directory()
        self.media_name = str(self.now_datetime.hour) + "時_" + str(self.now_datetime.minute) + "分"
        self.media_root = root_dir + "media/" + self.media_name
        self.media_ext = ".jpg"
        self.media_path = self.media_root + self.media_ext
        self.output_media_path = self.media_root + "_output" + self.media_ext
        print("self.media_path is {0}\n self.output_media_path is {1}".format(self.media_path, self.output_media_path))
        self.take_pic()
    
    @staticmethod
    def create_mdeia_directory(): 
        media_dir = "media/"
        confirm_and_create_dir(media_dir)

    def take_pic(self, save_path=None):
        print(" ------------  photo mode  -------------")
        media_save_path = self.media_path if save_path is None else self.media_path
        with picamera.PiCamera() as camera:
            camera.resolution = (1920, 1080)
            camera.capture(media_save_path)
            print("photo captured !!")
    def delete_media(self):
        os.remove(self.media_path)
        os.remove(self.output_media_path)

class S3(object):
    def __init__(self):
        self.bucket_name = None
        self.upload_file = None
        self.save_name_as = None
    
    def data_send(self):
        s3_instance = boto3.resource('s3')
        s3_instance.Bucket(self.bucket_name).upload_file(self.upload_file, self.save_name_as)

class RoomData(object):
    def __init__(self, now_datetime, human):
        self.now_datetime = now_datetime
        self.human = human
        self.device_name = "raspi_1"
        self.url = "http://funnel.soracom.io"

    def json_data_send(self, url=None):
        send_url = self.url if url is None else url
        room_json = {"device_name" : self.device_name, "human" : self.human, "measured_time" : self.now_datetime.strftime('%s')}
        params = json.dumps(room_json)
        headers = {'Content-Type': 'application/json'}
        response = requests.post(send_url, params, headers=headers)
        logging.info("data send !! response is {0}".format(response))
        print(response)


###   TensorFlow 制御部 end   ####

def main():
    Media.create_mdeia_directory()
    previous_minute = datetime.datetime.now().minute
    s3 = S3()
    s3.bucket_name = "plute-room-picture"
    while True:
        if previous_minute != datetime.datetime.now().minute:
            now = datetime.datetime.now()
            previous_minute = now.minute
            media = Media(now)
            s3.upload_file = media.media_path
            s3.save_name_as = media.media_name + media.media_ext
            s3.data_send()
            print("now analyze")
            image = Image.open(media.media_path)
            image_np = load_image_into_numpy_array(image)
            image_np_expanded = np.expand_dims(image_np, axis=0)
            output_dict = run_inference_for_single_image(image_np, detection_graph)

            person_index = np.where(np.array(output_dict['detection_classes']) == 1)
            pscore_array = np.array(output_dict['detection_scores'])[person_index]
            congestion = len(np.where(pscore_array >= 0.4)[0])
            room_data = RoomData(now, congestion)
            room_data.json_data_send()
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
                
            Image.fromarray(image_np).save(media.output_media_path)
            s3.upload_file = media.output_media_path
            s3.save_name_as = media.media_name + '_output' + media.media_ext
            s3.data_send()
            media.delete_media()


if __name__ == "__main__":
    while True:
        try:
            main()
        except:
            print("-----  into  except  ------ ")

            log_dir = 'log'
            if os.path.isdir(log_dir):
                pass
            else:
                os.makedirs(log_dir)

            logging.error(traceback.format_exc())

    