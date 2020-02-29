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

import time
import sys
import os

expUsed = []

timeStamp("Starting Calibration Run.")

print("")

filStart = input("With which filter slot should we start? The first slot is 0 (Zero). ")
numFilters = input("How many filters to calibrate? ")
numFrames = input("How many frames per filter? ")

print("")

print("Calibrating " + numFilters + " filters.")

oldASFormula = TSXSend('ccdsoftCamera.PropStr("m_csCustomFileNameFlat")')
TSXSend('ccdsoftCamera.setPropStr("m_csCustomFileNameFlat", "_:i_:f_:e_")')

numFilters = int(numFilters)
filCounter = int(filStart)
target = numFilters + filCounter

while (filCounter < target):
    expUsed.append(takeFlat(str(filCounter), str(numFrames), "No"))
    filCounter = filCounter + 1

TSXSend('ccdsoftCamera.setPropStr("m_csCustomFileNameFlat", "' + oldASFormula + '")')


print("")
timeStamp("Taking matching dark frames.")
print("")
writeNote("If prompted, please cover OTA or turn off flat panel light.")
print("")


oldASFormula = TSXSend('ccdsoftCamera.PropStr("m_csCustomFileNameDark")')
TSXSend('ccdsoftCamera.setPropStr("m_csCustomFileNameDark", "_:i_:f_:e_")')

numFilters = int(numFilters)
filCounter = int(filStart)
arrayCounter = 0

target = numFilters + filCounter

while (filCounter < target):
    TSXSend("ccdsoftCamera.FilterIndexZeroBased = " + str(filCounter))
    takeDark(expUsed[arrayCounter], numFrames)
    filCounter = filCounter + 1
    arrayCounter = arrayCounter + 1

TSXSend('ccdsoftCamera.setPropStr("m_csCustomFileNameDark", "' + oldASFormula + '")')

print("")

timeStamp("Finished Calibration Run.")

