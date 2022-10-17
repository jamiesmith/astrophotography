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
import glob

from library.PySkyX_ks import *
from library.PySkyX_jrs import *

import serial
from library.flatman_ctl import *

timeStamp("Starting Calibration run.")

def setFlatPanel(filterNum, binning):
    
    brightness = getBrightnessForFilter(filterNum, binning)

    print("     ----")
    writeNote(f"Adjusting the panel for filter: {getFilterAtSlot(filterNum)} @ {binning}x{binning} to {brightness}")
    print("     ----")

    myFMPanel.Brightness(brightness)


print("")

# ------------------------------------------------------------
# Get some settings
# ------------------------------------------------------------
#

filStart      = promptForValueWithDefault("With which filter slot should we start? The first slot is 0 (" + getFilterAtSlot(0) + "). ", 0)
numFilters    = promptForValueWithDefault("How many filters to calibrate? ", 1)
numFrames     = promptForValueWithDefault("How many frames per filter? ", 3 )
takeFlatDarks = promptForValueWithDefault("Take Flat Darks? ", "N")

print("")

FMSerialPort = "COM17"

# Setting up the panel

myFMPanel = FlatMan(FMSerialPort, False, model=FLIPFLAP)

print("")
writeNote("Attempting to connect to: " + FMSerialPort)

myFMPanel.Connect()
myFMPanel.Close()

writeNote("Switching panel on.")

myFMPanel.Light("ON")

# Moving on to the real calibration section

writeNote("Calibrating " + numFilters + " filters.")

numFilters = int(numFilters)
filCounter = int(filStart)
target = numFilters + filCounter

# ------------------------------------------------------------
# Take the flats
# ------------------------------------------------------------
#
binning = 1
while (filCounter < target):
    setFlatPanel(filCounter, binning)
    flatExposure = getFlatExposureForFilter(filCounter, binning)
    takeFlats(filterNum = str(filCounter), 
                    exposure = flatExposure, 
                    numFlats = str(numFrames), 
                    binning = binning,
                    takeDarks = "No",
                    targetBrightness = .45, 
                    tolerance = .04)
                        
    filCounter = filCounter + 1

# ------------------------------------------------------------
# Turn off the panel
# ------------------------------------------------------------
#

writeNote("Turning off Flatman panel.")
myFMPanel.Light("OFF")
myFMPanel.Disconnect()

# ------------------------------------------------------------
# See if we need dark flats
# ------------------------------------------------------------
#

if takeFlatDarks.upper() == "DARKS" or takeFlatDarks.upper() == "Y":
    TSXSend("ccdsoftCamera.Frame = 3")
    
    filCounter = int(filStart)
    target = numFilters + filCounter

    # ------------------------------------------------------------
    # Take the darks
    # ------------------------------------------------------------
    #
    binning = 1
    flatDarksTaken = {}
    
    while (filCounter < target):
        flatExposure = getFlatExposureForFilter(filCounter, binning)

        if (str(round(flatExposure, 3)) in flatDarksTaken):
            writeNote("skipping flats of " + str(flatExposure) + ", already done")
        else:
            writeNote("Taking flats for " + str(flatExposure) + ", not yet done")
            takeFauxDark(str(flatExposure), numFrames)
            flatDarksTaken[str(round(flatExposure, 3))] = "yes"
        
        filCounter += 1
else:
    writeNote("No automatic darks requested.")


timeStamp("Finished Calibration Run.")
done = input("Press enter to exit")
