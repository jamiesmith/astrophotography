#!/usr/bin/env python3

#
# This takes calibration frames for an entire wheel of filters.
#
# answer the question for the number of filters in the wheel and the number
# of calibration frames you want per filter.
#
# It will shoot flats first. Then, if necessary, SkyX will prompt you to
# cover the OTA so that it can shoot darks.
#
# Ken Sturrock
# August 26, 2018
#

from library.PySkyX_ks import *
from library.PySkyX_jrs import *

import time
import sys
import os
import platform
import csv

import serial
from library.flatman_ctl import *

# imported globals:
# FILTER_NAMES = nameFilters("Local")
# NUM_FILTERS
# LUM
# RED
# GREEN
# BLUE
# SII
# HA
# OIII
# MAX_BINNING = 4

printFilterSettings("Flat panel brightness", FLAT_PANEL_BRIGHTNESS)

printFilterSettings("Flat panel duration", FLAT_DURATION)

if platform.system() == "Darwin":
    FMSerialPort = glob.glob("/dev/tty.usbserial-*")[0]

    writeNote("Promising-looking serial port for the Flatman: ")
    print("                " + FMSerialPort)
    print("")

else:
    FMSerialPort = "COM10"
    
# Setting up the panel

myFMPanel = FlatMan(FMSerialPort, False, model=FLIPFLAP)
myFMPanel.Connect()

print("Starting...")
myFMPanel.Light("OFF")
print("turned off...")
# time.sleep(10)
# myFMPanel.Open()
# time.sleep(10)
myFMPanel.Light("ON")
# time.sleep(10)
myFMPanel.Brightness(255)
time.sleep(10)

myFMPanel.Close()
myFMPanel.Light("OFF")
myFMPanel.Disconnect()

