import illuminance as illum
import mh_z19 as mh
import bme280_sample as bme280

import boto3

import datetime
import requests
import json 

import os
import sys
import logging

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

    def measure_data(self):
        print("now, getting temperature, humidity, pressure, by bme280")
        bme280.bme.readData()
        self.measure_temperature()
        self.measure_humidity()
        self.measure_pressure()
        
        # self.measure_illuminance()

        self.measure_co2()

    def measure_temperature(self):
        self.temperature = bme280.bme.temperature
    def measure_humidity(self):
        self.humidity = bme280.bme.humidity
    def measure_pressure(self):
        self.pressure = bme280.bme.pressure
    def measure_illuminance(self):
        print("now, getting illuminance, by BH1750FVI ")
        self.illuminance = illum.measure_lux()
    def measure_co2(self):
        print("now, getting co2 by mh_z19")
        self.co2 = mh.read()
    def measure_exist_human(self):
        pass
        #self.exist_human = 

    def json_data_send(self, url=None):
        send_url = self.url if url is None else url
        room_json = {"device_name" : self.device_name, "temperature" : self.temperature, "humidity" : self.humidity, "illuminance" : self.illuminance,"pressure" : self.pressure, "CO2" : self.co2, "exist_human" : self.exist_human, "measured_time" : self.now_datetime.strftime('%s')}
#        room_json = {"device_name" : self.device_name, "temperature" : self.temperature, "humidity" : self.humidity, "illuminance" : self.illuminance, \
#            "pressure" : self.pressure, "CO2" : self.co2, "exist_human" : self.exist_human,  "measured_time" : self.now_datetime}
#        room_json = {"device_name" : self.device_name, "temperature" : self.temperature, "humidity" : self.humidity, "illuminance" : self.illuminance, \
#            "pressure" : self.pressure, "CO2" : self.co2, "human" : self.human}
        print(room_json)
        params = json.dumps(room_json)
        headers = {'Content-Type': 'application/json'}
        response = requests.post(send_url, params, headers=headers)
        print(response)


if __name__ == "__main__":
    previous_minute = datetime.datetime.now().minute
    try:
        while True:
            if previous_minute != datetime.datetime.now().minute:
                print("now is {0}".format(datetime.datetime.now()))
                now = datetime.datetime.now()
                previous_minute = now.minute
                room_data = RoomData(now)
                room_data.measure_data()
                room_data.json_data_send()
    except:
        import traceback
        log_dir = 'log'
        if os.path.isdir(log_dir):
            pass
        else:
            os.makedirs(log_dir)

        logging_fmt = "%(asctime)s  %(levelname)s  %(name)s \n%(message)s\n"
        logging.basicConfig(filename='log/room_data_log', level=logging.ERROR, format=logging_fmt)
        
        logging.error(traceback.format_exc())
        sys.exit()

    
    


