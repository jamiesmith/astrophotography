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
import argparse

import serial
from library.flatman_ctl import *

parser = argparse.ArgumentParser(description='Params')

parser.add_argument('-e', '--exposure', help="exposure duration", default=1.0)
parser.add_argument('-l', '--level', help="flatpanel level", default=50, type=int)
parser.add_argument('-b', '--binning', help="Binning", default=1)

args = parser.parse_args()

if platform.system() == "Darwin":
    FMSerialPort = glob.glob("/dev/tty.usbserial-*")[0]

    # writeNote("Promising-looking serial port for the Flatman: ")
    print("                " + FMSerialPort)
    print("")

else:
    FMSerialPort = "COM10"
    


myFMPanel = FlatMan(FMSerialPort, False, model=FLATMAN)
myFMPanel.Connect()


# myFMPanel.Open()

myFMPanel.Light("ON")
level = args.level

myFMPanel.Brightness(level)
shootFlat(args.exposure, args.binning)
brightness,adu = getImageBrightness().split(",")
brightness = float(brightness)
adu = int(adu)

print(f"{args.exposure}s at {args.level} ({args.binning}x{args.binning}) yielded adu {adu} @ {brightness}")


level += 5

myFMPanel.Brightness(level)
shootFlat(args.exposure, args.binning)
brightness1,adu1 = getImageBrightness().split(",")
brightness1 = float(brightness1)
adu1 = int(adu1)

print(f"{args.exposure}s at {args.level} ({args.binning}x{args.binning}) yielded adu {adu1} @ {brightness1}")

delta = adu1 - adu

# try to raise it 1000
#
level = level + round((5 * 1000 / delta), 0)
myFMPanel.Brightness(level)
shootFlat(args.exposure, args.binning)
brightness2,adu2 = getImageBrightness().split(",")
brightness2 = float(brightness2)
adu2 = int(adu2)
print(f"{args.exposure}s at {level} ({args.binning}x{args.binning}) yielded adu {adu2} @ {brightness2}")





# myFMPanel.Close()

myFMPanel.Light("OFF")

myFMPanel.Disconnect()

