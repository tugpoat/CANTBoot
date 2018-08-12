#ADAFRUIT LCD UI
import os, collections, signal, sys, subprocess, socket
import triforcetools
from Adafruit_CharLCDPlate import Adafruit_CharLCDPlate
from time import sleep

class UI_Adafruit(Process):
	