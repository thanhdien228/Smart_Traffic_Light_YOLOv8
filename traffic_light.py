import Rpi.GPIO as GPIO
import time
#define GPIO ports
LED_GREEN = 23
LED_RED = 12
LED_YELLOW = 16

def setup():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(LED_GREEN, GPIO.OUT)
    GPIO.setup(LED_RED, GPIO.OUT)
    GPIO.setup(LED_YELLOW, GPIO.OUT)

def control_traffic_light():
    GPIO.output(LED_GREEN, 1)
    time.delay(params['delay_green'])
    GPIO.output(LED_GREEN, 0)

    GPIO.output(LED_RED, 1)
    time.delay(params['delay_red'])
    GPIO.output(LED_RED, 0)

    GPIO.output(LED_YELLOW, 1)
    time.delay(params['delay_yellow'])
    GPIO.output(LED_YELLOW, 0)

if __name__ == '__main__':
    setup()
    params = {
        'delay_green': 6,
        'delay_yellow': 3,
        'delay_red': 5 #seconds
        }
    while(True):
        control_traffic_light()