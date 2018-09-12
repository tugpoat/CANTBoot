import RPi.GPIO as GPIO

def GPIO_Reboot():
	GPIO.setmode(GPIO.BOARD)
    GPIO.setup(40, GPIO.OUT)
    GPIO.output(40,1)
    sleep(0.4)
    GPIO.output(40,0)
    sleep(2.0)