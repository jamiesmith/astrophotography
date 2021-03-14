#!/usr/bin/env python3

import time
import sys
import os
import platform
import glob

from library.PySkyX_ks import *
from library.PySkyX_jrs import *

import serial
from library.flatman_ctl import *

from enum import Enum
class STATUS(Enum):
    INIT = 1
    TOO_DIM = 2
    TOO_BRIGHT = 3

class ADJUSTMENT_MODE(Enum):
    COARSE = 1
    FINE = 2

def setFlatBrightness(level):
    myFMPanel.Brightness(level)
    
timeStamp("Starting Calibration run.")

print("")

# ------------------------------------------------------------
# Get some settings
# ------------------------------------------------------------
#

filterNumber         = promptForValueWithDefault("Which filter slot should we start? The first slot is 0 (" + getFilterAtSlot(0) + "). ", 0)
binning              = promptForValueWithDefault("Enter binning: ", "1" )
exposure             = promptForValueWithDefault("Enter exposure time: ", 1 )
targetBrightness     = promptForValueWithDefault("Enter target brightness: ", 0.45 )
tolerance            = promptForValueWithDefault("Enter brightness tolerance: ", 0.05 )
startBrightness      = promptForValueWithDefault("Starting brightness: ", 20 )
brightnessIncrement  = promptForValueWithDefault("Starting brightness: ", 20 )



# ------------------------------------------------------------
# Fixed exposure, vary the panel level
# ------------------------------------------------------------
#
def findLevel(startingLevel, filterName, exposureTime, binning):
    level = startingLevel
    
    triedLevels = {}
    
    lastStatus = STATUS.INIT
    adjustmentMode = ADJUSTMENT_MODE.COARSE
    
    while True:
        if (level > 255):
            abort("Level too high, giving up")
        elif (level == 0):
            print("Already at min brightness, try decreasing exposure")       
            raise Exception('Try increasing exposure, level={}'.format(level))
        elif (level <= 0):
            abort("Level too low, giving up")
        elif (str(level) in triedLevels):
            abort(f"We've already tried this level ({level}), giving up")
        
        triedLevels[str(level)] = "yes"
        
        setFlatBrightness(level)
        
        shootFlat(exposureTime, binning)
    
        brightness,adu = getImageBrightness().split(",")
        brightness = float(brightness)
        adu = int(adu)

        print(f"\tLevel-based Flat with {filterName} for {exposureTime}s at {level} yielded adu {adu} @ {brightness}")

        if isExposureInRange(brightness, targetBrightness, tolerance):
            return level
        
        else: 
            if brightness > targetBrightness:
                print("\tToo bright, need to lower level")                
                if lastStatus == STATUS.INIT or lastStatus == STATUS.TOO_BRIGHT:

                    # still too bright
                    #
                    lastStatus = STATUS.TOO_BRIGHT
                    
                    level = level - 10
                else:
                    
                    if lastStatus == STATUS.TOO_DIM:
                        # We've passed it.
                        #
                        abort('Cannot get in range, level={}'.format(level))
                        
                    adjustmentMode = ADJUSTMENT_MODE.FINE
                    
                    level = level - 1
                
                
            else:
                print("\tToo dim, need to raise level")

                if lastStatus == STATUS.INIT or lastStatus == STATUS.TOO_DIM:

                    # still too dim
                    #
                    lastStatus = STATUS.TOO_DIM
                    
                    level = level + 10
                else:
                    
                    if lastStatus == BrightnessLevel.TOO_DIM:
                        # We've passed it.
                        #
                        abort('Cannot get in range, level={}'.format(level))
                        
                    adjustmentMode = ADJUSTMENT_MODE.FINE
                    
                    level = level + 1

            
            if brightness < targetBrightness and level >= 255:
                raise Exception('Try increasing exposure, level={}'.format(level))
                
            # delta = 0
            #
            #
            #
            #
            # if brightness == 0:
            #     writeNote("EH?")
            #     level = 2 * level
            #
            # elif brightness > (targetBrightness + (4 * tolerance)):
            #     writeNote("B")
            #     delta = -10
            #
            # elif brightness > (targetBrightness + (2 * tolerance)):
            #     writeNote("C")
            #     delta = -5
            #
            # elif brightness > targetBrightness:
            #     writeNote("D")
            #     delta = -1
            #
            # elif brightness < (targetBrightness - (10 * tolerance)):
            #     writeNote("A")
            #     level = int(round(level * (targetBrightness / brightness / 2), 0))
            #
            # elif brightness < (targetBrightness - (4 * tolerance)):
            #     writeNote("E")
            #     delta = 10
            #
            # elif brightness < (targetBrightness - (2 * tolerance)):
            #     writeNote("F")
            #     delta = 5
            #
            # elif brightness < targetBrightness:
            #     writeNote("G")
            #     delta = 1
            #
            # else:
            #     writeNote("well, this shouldn't happen")
            #     break
            #
            # if (delta < 0):
            #     print(f"\tBrightness {brightness} target {targetBrightness}, Decreasing by {abs(delta)}")
            #
            # elif (delta > 0):
            #     print(f"\tBrightness {brightness} target {targetBrightness}, Increasing by {abs(delta)}")
            #
            # elif (delta == 0):
            #     print(f"\tBrightness {brightness} target {targetBrightness}, setting to {level}")
            #
            # level += delta
            #
        if level > 255:
            level = 255

    return level    

def calculateNextExposureTime(currentExposure, factor, minimum):
    newExposure = round((currentExposure * factor), 4)
    
    if ( abs(currentExposure - newExposure) < abs(minimum) ):
        newExposure = currentExposure + minimum

    return round(newExposure, 4)
    
    
    

# ------------------------------------------------------------
# Main operation starts here    
# ------------------------------------------------------------
#

if platform.system() == "Darwin":
    FMSerialPort = glob.glob("/dev/tty.usbserial-*")[0]

    writeNote("Promising-looking serial port for the Flatman: ")
    print("                " + FMSerialPort)
    print("")

else:
    FMSerialPort = "COM10"
    
# Setting up the panel

myFMPanel = FlatMan(FMSerialPort, False, model=FLIPFLAP)

print("")
writeNote("Attempting to connect to: " + FMSerialPort)

myFMPanel.Connect()
myFMPanel.Close()

targetBrightness = 0.45
tolerance = 0.01

writeNote("Switching panel on.")
myFMPanel.Light("ON")
        

numFilters = int(numFilters)
filterNumber = int(filStart)
target = numFilters + filterNumber

# Arbitrarily start somewhere
#
startingLevel = 20
level = startingLevel

# exposureTime = calculateOptimalFlatExposure(str(filterNumber), startingExposure = 1, binning = 1)


binLevelSlots = csvBinnings .split(",")
calculatedTimes = [[0]*(len(binLevelSlots))] * (numFilters)

maxAttempts = 5

while (filterNumber < target):
    exposureTime = minimumExposure
    binSlot = 0
    while binSlot < len(binLevelSlots):
        attempts = 1
        writeNote(f"Processing filters for {binLevelSlots[binSlot]}x{binLevelSlots[binSlot]} binning")
    
        print(f"\tSwitching to {getFilterAtSlot(filterNumber)} filter.")
        TSXSend("ccdsoftCamera.FilterIndexZeroBased = " + str(filterNumber)) 
        
        while attempts <= maxAttempts:

            try:
                level = findLevel(level, getFilterAtSlot(filterNumber), exposureTime, binning = binLevelSlots[binSlot])
            except Exception as e:
                
                if attempts == maxAttempts:
                    abort("Giving up")
            
                # If we can't find a level, try adjusting the exposure
                #
                lastLevel = int((str(e)).split("=")[1])
                
                if (lastLevel == 255):
                    level = int(lastLevel / 2)
                    exposureTime = round(float(exposureTime) * 2, 3)
                elif (lastLevel == 0 or lastLevel == 1):
                    level = int(startingLevel)
                    exposureTime = round(float(exposureTime) / 2, 3)
                else:
                    abort(f"something is weird {lastLevel}")

                print(f"\tLevel-based flat characterization failed, Last Level was[{lastLevel}] - Trying to vary exposure instead at {level} for {exposureTime}s")
                
            attempts += 1

                # exposureTime = findExposure(level, getFilterAtSlot(filterNumber), useExposure, binning = binLevelSlots[binSlot])
        
        
        print(f"\tFound level for filter {getFilterAtSlot(filterNumber)} as {level}")
        calculatedTimes[filterNumber][binSlot] = level
        binSlot += 1

    filterNumber += 1

filterNumber = int(filStart)

delim = ", "

print("Here's the config:")
binSlot = 0
filterSpec = "Filter Name"

while binSlot < len(binLevelSlots):
    filterSpec += delim + str(binLevelSlots[binSlot]) + "x" + str(binLevelSlots[binSlot])
    binSlot += 1

print(f"\t{filterSpec}")


while (filterNumber < target):
    binSlot = 0
    filterSpec = getFilterAtSlot(filterNumber)
    
    while binSlot < len(binLevelSlots):
        filterSpec += delim + str(calculatedTimes[filterNumber][binSlot])
        
        binSlot += 1

    print(f"\t{filterSpec}")
    filterNumber += 1
    
# For each filter
#     For each binning
#         # First, see if there's a flat panel setting that works for the min exposure


    
# ------------------------------------------------------------
# Turn off the panel
# ------------------------------------------------------------
#

# writeNote("Turning off Flatman panel.")
# myFMPanel.Light("OFF")
myFMPanel.Disconnect()

promptToExit()
