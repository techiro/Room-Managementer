import illuminance as illum
import mh_z19 as mh
import bme280_sample as bme280

import weather_receive as weather

import boto3

import datetime
import requests
import json 

import os
import sys
import logging

import traceback

#logging_fmt = "%(asctime)s  %(levelname)s  %(name)s \n%(message)s\n"
#logging.basicConfig(filename='log/room_data_log', level=logging.INFO, format=logging_fmt)


class RoomData(object):
    def __init__(self, now_datetime):
        self.now_datetime = now_datetime
        self.exist_human = None
        self.temperature = 28
        self.humidity = 60
        self.illuminance = 750
        self.pressure = 1013
        self.co2 = 1000
        self.device_name = "raspi_2"
        self.url = "http://funnel.soracom.io"
        self.bme = bme280.Bme()
        self.room_datas = None

    def measure_data(self):
        print("now, getting temperature, humidity, pressure, by bme280")
        try:
            self.bme.setup()
            self.bme.get_calib_param()
            self.bme.readData()
            self.measure_temperature()
            self.measure_humidity()
            self.measure_pressure()
        except:
            print(traceback.format_exc())
            print("bme280 error in room_data.py  RoomData().measure_data , 温度センサーの接続を確認してください")
            self.temperature = None
            self.humidity = None
            self.pressure = None
        
        # self.measure_illuminance()

        self.measure_co2()

    def measure_temperature(self):
        self.temperature = self.bme.temperature
    def measure_humidity(self):
        self.humidity = self.bme.humidity
    def measure_pressure(self):
        self.pressure = self.bme.pressure
    def measure_illuminance(self):
        print("now, getting illuminance, by BH1750FVI ")
        self.illuminance = illum.measure_lux()
    def measure_co2(self):
        print("now, getting co2 by mh_z19")
        self.co2 = mh.read()
    def measure_exist_human(self):
        pass
        #self.exist_human = 

    def send_data_make(self, dict_data=None):
        self.room_datas = {"device_name" : self.device_name, "temperature" : self.temperature, \
            "humidity" : self.humidity, "illuminance" : self.illuminance,\
                "pressure" : self.pressure, "CO2" : self.co2, "exist_human" : self.exist_human, \
                "measured_time" : self.now_datetime.strftime('%s')}
        if dict_data is not None:
            self.room_datas.update(dict_data)

    def data_send_as_json(self, url=None):
        send_url = self.url if url is None else url
        params = json.dumps(self.room_datas)
        headers = {'Content-Type': 'application/json'}
        response = requests.post(send_url, params, headers=headers)
        logging.info("data send !! response is {0}".format(response))
        print(response)


if __name__ == "__main__":
 
    weather_data = weather.Weather_api_data()
    weather_data.get_weather_data()

    previous_minute = datetime.datetime.now().minute
    while True:
        if previous_minute != datetime.datetime.now().minute:
            print("now is {0}".format(datetime.datetime.now()))
            now = datetime.datetime.now()
            previous_minute = now.minute
            room_data = RoomData(now)
            room_data.measure_data()
            weather_data = weather.Weather_api_data()
            weather_data.get_weather_data()
            outside = weather_data.read_main_data()
            outside.update({"weather":weather_data.read_weather_data()})
            room_data.send_data_make(outside)
            room_data.data_send_as_json()
    # while True:
    #     try:
    #         while True:
    #             if previous_minute != datetime.datetime.now().minute:
    #                 print("now is {0}".format(datetime.datetime.now()))
    #                 now = datetime.datetime.now()
    #                 previous_minute = now.minute
    #                 room_data = RoomData(now)
    #                 room_data.measure_data()
    #                 weather_data = weather.Weather_api_data()
    #                 weather_data.get_weather_data()
    #                 outside = weather_data.read_main_data()
    #                 outside.update({"weather":weather_data.read_weather_data()})
    #                 room_data.send_data_make(outside)
    #                 room_data.data_send_as_json()
    #     except:

    #         log_dir = 'log'
    #         if os.path.isdir(log_dir):
    #             pass
    #         else:
    #             os.makedirs(log_dir)           
    #         logging.error(traceback.format_exc())
            # sys.exit()

    
    


