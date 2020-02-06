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
import serial

from library.PySkyX_ks import *
from library.flatman_ctl import *

def FPAdjust():
    print("     ----")
    writeNote("Adjusting the panel for filter: " + str(filCounter))
    print("     ----")

    if str(TSXSend('ccdsoftCamera.PropStr("m_csObserver")')) ==  "Ken Sturrock":
        #
        # The following two sections are customized for my cameras
        #
        if str(TSXSend("SelectedHardware.cameraModel")) == "ASICamera": 
            writeNote("Setting Panel for Ken's ASI-183")

            if filCounter == 0:
                writeNote("Setting panel to 40.")
                myFMPanel.Brightness(40)
    
            if filCounter == 1:
                writeNote("Setting panel to 200.")
                myFMPanel.Brightness(200)
    
            if filCounter == 2:
                writeNote("Setting panel to 50.")
                myFMPanel.Brightness(50)
        
            if filCounter == 3:
                writeNote("Setting panel to 50.")
                myFMPanel.Brightness(50)
        
            if filCounter == 4:
                writeNote("Setting panel to 50.")
                myFMPanel.Brightness(50)
             

        if TSXSend("SelectedHardware.cameraModel") == "QSI Camera  ":
            writeNote("Setting panel for Ken's QSI-690")


            if filCounter == 0:
                writeNote("Setting panel to 40.")
                myFMPanel.Brightness(40)
    
            if filCounter == 1:
                writeNote("Setting panel to 50.")
                myFMPanel.Brightness(50)
    
            if filCounter == 2:
                writeNote("Setting panel to 50.")
                myFMPanel.Brightness(50)
        
            if filCounter == 3:
                writeNote("Setting panel to 50.")
                myFMPanel.Brightness(50)
        
            if filCounter == 4:
                writeNote("Setting panel to 250.")
                myFMPanel.Brightness(250)
        
            if filCounter == 5:
                writeNote("Setting panel to 200.")
                myFMPanel.Brightness(200)
        
            if filCounter == 6:
                writeNote("Setting panel to 250.")
                myFMPanel.Brightness(250)
        
            if filCounter == 7:
                writeNote("Setting panel to 250.")
                myFMPanel.Brightness(250)

    else:
        #
        # Set these brightness values to work for your system
        #
        if filCounter == 0:
            writeNote("Setting panel to 40.")
            myFMPanel.Brightness(40)
    
        if filCounter == 1:
            writeNote("Setting panel to 70.")
            myFMPanel.Brightness(70)
    
        if filCounter == 2:
            writeNote("Setting panel to 50.")
            myFMPanel.Brightness(50)
        
        if filCounter == 3:
            writeNote("Setting panel to 50.")
            myFMPanel.Brightness(50)
        
        if filCounter == 4:
            writeNote("Setting panel to 100.")
            myFMPanel.Brightness(100)

        if filCounter == 5:
            writeNote("Setting panel to 200.")
            myFMPanel.Brightness(200)

        if filCounter == 6:
            writeNote("Setting panel to 200.")
            myFMPanel.Brightness(200)

        if filCounter == 7:
            writeNote("Setting panel to 200.")
            myFMPanel.Brightness(200)
             
 


expUsed = []

timeStamp("Starting Calibration run.")

print("")

filStart = input("    INPUT: Starting filter number (first slot is 0 (zero))? ")
numFilters = input("    INPUT: How many filters to calibrate? ")
numFrames = input("    INPUT: How many frames per filter? ")

print("")

FMSerialPort = glob.glob("/dev/tty.usbserial-*")[0]

writeNote("Promising-looking serial port for the Flatman: ")
print("                " + FMSerialPort)
print("")
print("    INPUT: If you know of a better one, please type in the absolute path.")
newPort = input("    INPUT: Otherwise, press the return key:")

if "/dev/" in newPort:
    FMSerialPort = newPort

# Setting up the panel

myFMPanel = FlatMan(FMSerialPort, False)

print("")
writeNote("Attempting to connect to: " + FMSerialPort)

myFMPanel.Connect()

writeNote("Switching panel on.")

myFMPanel.Light("ON")

# Moving on to the real calibration section

writeNote("Calibrating " + numFilters + " filters.")


if str(TSXSend('ccdsoftCamera.PropStr("m_csObserver")')) ==  "Ken Sturrock":
#
# The following section is customized for my cameras because I am 
# forgetful.
#

    writeNote("Verifying imaging camera at -10.")
    TSXSend("ccdsoftCamera.TemperatureSetPoint = -10")
    TSXSend("ccdsoftCamera.RegulateTemperature = true")

    if TSXSend("SelectedHardware.cameraModel") == "QSI Camera  ":
        TSXSend('ccdsoftCamera.setPropStr("m_csExCameraMode", "Higher Image Quality")')
        writeNote("Setting QSI Camera to high quality mode.")

oldASFormula = TSXSend('ccdsoftCamera.PropStr("m_csCustomFileNameFlat")')
writeNote("Changing the flat Autosave name formula from " + oldASFormula + " to :i_:f_:e_ ")
TSXSend('ccdsoftCamera.setPropStr("m_csCustomFileNameFlat", ":i_:f_:e_")')

numFilters = int(numFilters)
filCounter = int(filStart)
target = numFilters + filCounter

while (filCounter < target):
    FPAdjust()
    expUsed.append(takeFlat(str(filCounter), str(numFrames), "No"))
    filCounter = filCounter + 1

writeNote("Restoring previous flat Autosave name formula.")
TSXSend('ccdsoftCamera.setPropStr("m_csCustomFileNameFlat", "' + oldASFormula + '")')


writeNote("Turning off Flatman panel.")
myFMPanel.Light("OFF")
myFMPanel.Disconnect()
print("")
timeStamp("     NOTE: Taking matching dark frames.")
print("")
writeNote("If prompted, please cover OTA or turn off flat panel light.")
print("")


oldASFormula = TSXSend('ccdsoftCamera.PropStr("m_csCustomFileNameDark")')
writeNote("Changing the dark Autosave name formula from " + oldASFormula + " to :i_:f_:e_ ")
TSXSend('ccdsoftCamera.setPropStr("m_csCustomFileNameDark", ":i_:f_:e_")')

numFilters = int(numFilters)
filCounter = int(filStart)
arrayCounter = 0

target = numFilters + filCounter

while (filCounter < target):
    TSXSend("ccdsoftCamera.FilterIndexZeroBased = " + str(filCounter))
    takeDark(expUsed[arrayCounter], numFrames)
    filCounter = filCounter + 1
    arrayCounter = arrayCounter + 1

writeNote("Restoring previous dark Autosave name formula.")
TSXSend('ccdsoftCamera.setPropStr("m_csCustomFileNameDark", "' + oldASFormula + '")')

print("")

if str(TSXSend('ccdsoftCamera.PropStr("m_csObserver")')) ==  "Ken Sturrock":
    if TSXSend("SelectedHardware.cameraModel") == "QSI Camera  ":
        TSXSend('ccdsoftCamera.setPropStr("m_csExCameraMode", "Faster Image Downloads")')
        writeNote("Setting QSI Camera to faster download mode.")    

timeStamp("Finished Calibration Run.")

