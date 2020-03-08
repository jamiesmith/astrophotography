#!/usr/bin/env python3

import time
import sys
import os
import glob

from library.PySkyX_ks import *
from library.PySkyX_jrs import *

import serial
from library.flatman_ctl import *

def setFlatBrightness(level):
    writeNote(f"Setting flat panel to {level}")
    myFMPanel.Brightness(level)
    
timeStamp("Starting Calibration run.")

print("")

# ------------------------------------------------------------
# Get some settings
# ------------------------------------------------------------
#

filterNumber = int(promptForValueWithDefault("With filter slot should we characterize? The first slot is 0 (" + getFilterAtSlot(0) + "). ", 0))
print(f"\tprocessing {getFilterAtSlot(filterNumber)}")

binning = int(promptForValueWithDefault("Binning?", 1))
startingLevel  = int(promptForValueWithDefault("Starting brightness?", 10))
exposure = int(promptForValueWithDefault("exposure length?", 2))

writeNote(getFilterAtSlot(int(filterNumber)))

FMSerialPort = "COM10"

# Setting up the panel

myFMPanel = FlatMan(FMSerialPort, False, model=FLIPFLAP)

print("")
writeNote("Attempting to connect to: " + FMSerialPort)

myFMPanel.Connect()
myFMPanel.Close()

targetBrightness = 0.45
tolerance = 0.03

writeNote("Switching panel on.")
myFMPanel.Light("ON")


def findLevel(startingLevel, filterName, exposureTime):
    level = startingLevel
    
    while True:
    
        writeNote(f"Taking a flat with {filterName} for {exposure}s at {level}")
        if level > 255:
            abort("Level too high, giving up")
        
        setFlatBrightness(level)
        shootFlat(exposure, binning)
    
        brightness,adu = getImageBrightness().split(",")
        brightness = float(brightness)
        adu = int(adu)

        writeNote(f"Took a flat with {filterName} for {exposure}s yielded adu {adu} @ {brightness}")

        if isExposureInRange(brightness, targetBrightness, tolerance):
            writeNote("Looks good!")
            break
        
        else: 
            
            if brightness < targetBrightness and level == 255:
                abort("Already at max brightness, try increasing exposure")       
                
            writeNote(f"Brightness {brightness} target {targetBrightness}")
            if brightness > (targetBrightness + (4 * tolerance)):
                writeNote("decrement 10")
                level -= 10

            elif brightness > (targetBrightness + (2 * tolerance)):
                writeNote("decrement 5")
                level -= 5
            
            elif brightness > targetBrightness:
                writeNote("decrement 1")
                level -= 1

            elif brightness < (targetBrightness - (4 * tolerance)):
                writeNote("increment 10")
                level += 10

            elif brightness < (targetBrightness - (2 * tolerance)):
                writeNote("increment 5")
                level += 5

            elif brightness < targetBrightness:
                writeNote("increment 1")            
                level += 1
            
            else:
                writeNote("well, this shouldn't happen")
                break          
                
            if level > 255:
                level = 255

    return level    
        
writeNote(f"Switching to {getFilterAtSlot(filterNumber)} filter.")
TSXSend("ccdsoftCamera.FilterIndexZeroBased = " + str(filterNumber)) 

level = findLevel(startingLevel, getFilterAtSlot(filterNumber), 1.0)

writeNote(f"Found level for filter {getFilterAtSlot(filterNumber)} as {level}")
    

# ------------------------------------------------------------
# Turn off the panel
# ------------------------------------------------------------
#

# writeNote("Turning off Flatman panel.")
# myFMPanel.Light("OFF")
myFMPanel.Disconnect()

promptToExit()
