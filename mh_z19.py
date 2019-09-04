# -*- coding: utf-8 -*-
# refer http://eleparts.co.kr/data/design/product_file/SENSOR/gas/MH-Z19_CO2%20Manual%20V2.pdf
# 
# © Takeyuki UEDA 2015 - 

import serial
import time
import subprocess
#import slider_utils as slider
import getrpimodel
import traceback
# setting

if getrpimodel.model() == "3 Model B":
  serial_dev = '/dev/ttyS0'
  stop_getty = 'sudo systemctl stop serial-getty@ttyS0.service'
  start_getty = 'sudo systemctl start serial-getty@ttyS0.service'
else:
  serial_dev = '/dev/ttyAMA0'
  stop_getty = 'sudo systemctl stop serial-getty@ttyAMA0.service'
  start_getty = 'sudo systemctl start serial-getty@ttyAMA0.service'

def mh_z19():
  try:
    ser = serial.Serial(serial_dev,
                        baudrate=9600,
                        bytesize=serial.EIGHTBITS,
                        parity=serial.PARITY_NONE,
                        stopbits=serial.STOPBITS_ONE,
                        timeout=1.0)
    while 1:
      result=ser.write(b"\xff\x01\x86\x00\x00\x00\x00\x00\x79")
      s=ser.read(9)
      if len(s) >= 4 and s[0] == 255 and s[1] == 134:
        return s[2]*256 + s[3]
      break
#  except IOError:
#    slider.io_error_report()
#  except:
#    slider.unknown_error_report()
  except:
      print("error")
      print(traceback.format_exc())
      pass

def read():
    p = subprocess.call(stop_getty, stdout=subprocess.PIPE, shell=True)
    result = mh_z19()
    print(result)
    p = subprocess.call(start_getty, stdout=subprocess.PIPE, shell=True)
    if result is not None:
        return result
    else:
        return None
if __name__ == '__main__':
# #  value = mh_z19()
# #  print "co2=", value["co2"]
    value = read()
    if value is not None:
        print(value)
    else:
        print("None")

