#!/usr/bin/env python3

#
# This takes calibration frames for an entire wheel of filters and uses the Alnitak
# FlatMan panel. 
#
# The idea is that the regular calibration (flat, dark) routines in my library
# will autoscale the exposure duration but, if you can set the panel brighter or
# dimmer then it will make life easier and faster.
#
# It controls the panel by means of Rodolphe Pineau's Python-based scriptable
# control module (available from his file lbrary on the Bisque support site). 
# In addition to the Python module, Rodolphe wrote a GUI control program for the 
# Macintosh. You can download it (and pay him) here:
#
# http://www.rti-zone.org
#
# After you download Rodolphe's control file (which I put in the library subfolder of my 
# code because it was easy), you'll have to install the PySerial library. There are several ways
# to do this, so you'll need to hit google and figure it out. I used the "pip" method.
#
# Before you use this script, you'll also need to verify the filter slots and flatman settings for 
# each frame. The setting are in the function that starts with "Def FPAdjust(():"
# For example, I usually shoot LRGB filters at a brightness of 50 and NB at 250. My ASI-183 is 
# not sensitive in the red channel, however, so I boost that way up.
#
# When you run this script, answer the question for the number of filters in the wheel and the 
# number of calibration frames you want per filter. Then verify the serial port used by the flatman.
#
# It will shoot flats first. Then, if necessary, SkyX will prompt you to
# cover the OTA so that it can shoot darks. The flatman will be turned off and should
# work as a shutter if you have decent light seal.
#
# Ken Sturrock
# August 26, 2018
#

import time
import sys
import os
import platform
import glob
import serial


from library.PySkyX_ks import *
from library.PySkyX_jrs import *
from library.flatman_ctl import *

if platform.system() == "Darwin":
    FMSerialPort = glob.glob("/dev/tty.usbserial-*")[0]

    writeNote("Promising-looking serial port for the Flatman: ")
    print("                " + FMSerialPort)
    print("")

else:
    FMSerialPort = "COM10"
    
# Setting up the panel

myFMPanel = FlatMan(FMSerialPort, False)

print("")
writeNote("Attempting to connect to: " + FMSerialPort)

myFMPanel.Connect()
writeNote("Switching panel on.")

myFMPanel.Light("ON")

# time.sleep(10)
#
exposure = 0.01
binning = 1
increment = 1
level = increment

print(str(TSXSend("SelectedHardware.cameraModel")))
print(TSXSend('ccdsoftCamera.PropStr("m_csObserver")'))

while exposure <= 1:
    brightness = 0
    level = 5

    while level <= 255 and brightness < 1:
        myFMPanel.Brightness(level)
        shootFlat(exposure, binning)
        brightness,adu = getImageBrightness().split(",")
        brightness = float(brightness)
        adu = int(adu)

        print(f"\tExposure {exposure}s,{level},{adu},{brightness}")
        
        level += increment
        
    exposure = round(exposure + 0.01, 2)



writeNote("Turning off Flatman panel.")
myFMPanel.Light("OFF")
myFMPanel.Disconnect()
