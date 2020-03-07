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
import csv

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
# MAX_BINNING
    
expUsed = []

timeStamp("Starting Calibration Run.")

print("")

filStart = promptForValueWithDefault("With which filter slot should we start? The first slot is 0 (" + getFilterAtSlot(0) + "). ", 0)
numFilters = promptForValueWithDefault("How many filters to calibrate? ", 1)
numFrames = promptForValueWithDefault("How many frames per filter? ", 5 )
takeFlatDarks = promptForValueWithDefault("Take Flat Darks? ", "N")

print("")

print("Calibrating " + numFilters + " filters.")


numFilters = int(numFilters)
filCounter = int(filStart)
target = numFilters + filCounter

# exposureTime = calculateOptimalFlatExposure(str(filCounter), startingExposure = 1, binning = 1)

exposureTime = 1
flatDarksTaken = {}

while (filCounter < target):    

    exposureTime = getFlatExposureForFilter(filCounter, binning = 1)
    
    # Need a way to know if we have taken flats of this duration
    #
    takeDarkFlatsThisTime = takeFlatDarks
    
    if (takeFlatDarks):
        if (str(round(exposureTime, 3)) in flatDarksTaken):
            writeNote("skipping flats of " + str(exposureTime) + ", already done")
            takeDarkFlatsThisTime = "N"
        else:
            writeNote("Taking flats for " + str(exposureTime) + ", not yet done")
    
    expUsed.append(takeFlats(filterNum = str(filCounter), 
                    exposure = exposureTime, 
                    numFlats = str(numFrames), 
                    binning = 1,
                    takeDarks = takeDarkFlatsThisTime,
                    targetBrightness = .45, 
                    tolerance = .1))
                    
    if (takeFlatDarks):
        flatDarksTaken[str(round(exposureTime, 3))] = "yes"        
    
                    
    filCounter = filCounter + 1

timeStamp("Finished Calibration Run.")

done = input("Press enter to exit")
