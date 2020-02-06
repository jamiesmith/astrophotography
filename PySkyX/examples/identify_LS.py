#!/usr/bin/env python3
#
# Facilitates the identification of light sources within an image.
#
# Open an image within SkyX, run script, click on source of interest in the SkyX
# FITS viewer, return to the script window and press the return key.
#
# Press lowercase "q" to quit.
#
# Ken Sturrock
# August 2019, 2018
#

from library.PySkyX_ks import *

import time
import sys
import os
import statistics

TSXSend("ccdsoftCameraImage.AttachToActive()")
TSXSend("ImageLink.pathToFITS = ccdsoftCameraImage.Path")
writeNote("Using active image.")

ilResults = classicIL()

if "TypeError:" in ilResults :
    print("    ERROR: Image Link Failed.")
    print("    ERROR: " + ilResults)

lsXRaw = TSXSend("ccdsoftCameraImage.InventoryArray(0)")
lsXArray = lsXRaw.split(",")
lsYRaw = TSXSend("ccdsoftCameraImage.InventoryArray(1)")
lsYArray = lsYRaw.split(",")

lsXArrayLength = len(lsXArray)


readChar = "notQ"


readCharacter = input("Click near light source, then press <return>. Press q <return> to end.")

while (readCharacter != "q"):

    cLS = 0
    smallestDist = float(TSXSend("ccdsoftCameraImage.WidthInPixels"))

    targX = TSXSend("ccdsoftCameraImage.mousePressPixelX()")
    targY = TSXSend("ccdsoftCameraImage.mousePressPixelY()")

    writeNote("Pixel: " + targX + ", " + targY)

    for LS in range(lsXArrayLength):
        writeNote("Analyzing LS: " + str(LS))
        distX = float(lsXArray[LS]) - float(targX)
        distY = float(lsYArray[LS]) - float(targY)
        pixDist = math.sqrt((distX * distX) + (distY * distY))
        if pixDist < smallestDist:
            writeNote("LS: " + str(LS) + " is now the closest.")
            cLS = LS
            smallestDist = pixDist
    
    timeStamp("Closest Source Coordinates:  " + lsXArray[cLS] + ", " + lsYArray[cLS] + " [LS: " + str(cLS) + "]")

    RAj2k,DecJ2k,RANow,DecNow = findRADec("Active", lsXArray[cLS], lsYArray[cLS]).split(", ")

    ilFWHM = round(float(TSXSend("ImageLinkResults.imageFWHMInArcSeconds")), 3)

    namesAt(str(RAj2k) + ', ' + str(DecJ2k) , ilFWHM)

    readCharacter = input("Click near light source, then press <return>. Press q <return> to end.")


