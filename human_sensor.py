import sys
import time
import RPi.GPIO as GPIO

SLEEP_TIME = 1
SENSOR_GPIO = 5

GPIO.cleanup()
GPIO.setmode(GPIO.BCM)
GPIO.setup(SENSOR_GPIO, GPIO.IN)

while True:
  if GPIO.input(SENSOR_GPIO) == GPIO.HIGH:
    sys.stdout.write("\r動いた　　")
  else:
    sys.stdout.write("\r動いてない")

  time.sleep(SLEEP_TIME)
GPIO.cleanup()
