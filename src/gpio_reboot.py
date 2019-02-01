#import RPi.GPIO as GPIO
import time

def GPIO_Reboot():
	#GPIO.setmode(GPIO.BOARD)
    #GPIO.setup(40, GPIO.OUT)
    #GPIO.output(40,1)
    time.sleep(0.4)
    #GPIO.output(40,0)
    time.sleep(2.0)
    print("did it lmao")