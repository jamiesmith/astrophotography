#!/usr/bin/env python3

#
# Script to image a list of double stars (or other targets). The input list should be a single column 
# and the targets recognizeable by SkyX's "find".
#
# You will specify the file name as the command line argument. 
#
# Ken Sturrock
# September 14, 2019
#

from library.PySkyX_ks import *

import time
import sys
import os

uniqueTargSet = set()

initialFocused = "No"

def chkTarget(target):
#
# This is a modified version of the routine from run_target-2.
#
# It makes sure that the target is valid & up and that the sky is dark.
#
#

    if targExists(target) == "No":
        print("    ERROR: " + target + " not found in SkyX database.")
        return "Fail"

    # If you're on the simulator, you're probably debugging during the day.
    if str(TSXSend("SelectedHardware.mountModel")) ==  "Telescope Mount Simulator":
        writeNote("Running on simulated mount.")
        return "Success"

    altLimit = 35

    # If light outside then wait or pack it in.
    isDayLight()

    currentHA = targHA(target)
    currentAlt = targAlt(target) 
    currentAz = targAz(target)

    #
    # This code is to handle my neighbor's giant "ghetto palm"
    #
    if str(TSXSend('ccdsoftCamera.PropStr("m_csObserver")')) ==  "Ken Sturrock":
        if currentAlt < 55 and currentHA < 0 and currentAz < 80:
            writeNote('Target is in "star-eating tree" zone. Skipping.')
            return "Fail"

    if currentAlt < altLimit and currentHA > 0:
        timeStamp("Target " + target + " is " + str(round(currentAlt, 2)) + " degrees high.")
        timeStamp("Target " + target + " has sunk too low.")
        return "Fail"

    if currentAlt < altLimit and currentHA < 0:
        writeNote("Target " + target + " is " + str(round(currentAlt, 2)) + " degrees high.")
        writeNote("Target " + target + " is still too low.")
        return "Fail"

    return "Success"

def imageStar(target):
#
# DS alternative to regular takeImage
#
    slew(target)

    for loop in [1, 2, 3]:

        TSXSend("ccdsoftCamera.Asynchronous = false")
        TSXSend("ccdsoftCamera.AutoSaveOn = true")
        TSXSend("ccdsoftCamera.Frame = 1")
        TSXSend("ccdsoftCamera.Subframe = false")
        TSXSend("ccdsoftCamera.Delay = 5")
        TSXSend("ccdsoftCamera.ExposureTime = 10")

        timeStamp("Shooting image " + str(loop) + ".")

        camMesg = TSXSend("ccdsoftCamera.TakeImage()") 

        TSXSend("ccdsoftCamera.Delay = 0")

        if "Process aborted." in camMesg:
            timeStamp("Script Aborted.")
            sys.exit()

        if camMesg == "0":
        #
        # Results from the camera are normal. Check if there are any stars.
        #
            TSXSend("ccdsoftCameraImage.AttachToActiveImager()")
            TSXSend("ccdsoftCameraImage.ShowInventory()")
            starsFound = TSXSend("ccdsoftCameraImage.InventoryArray(0).length")
    
            dirName,fileName = os.path.split(TSXSend("ccdsoftCameraImage.Path"))
            
            orgImgName = os.path.splitext(fileName)[0]

            if os.path.exists(dirName + "/" + orgImgName + ".SRC"):
                os.remove(dirName + "/" + orgImgName + ".SRC")
        
            if  int(starsFound) < 10:
                writeNote("There are only " + starsFound + " light sources in image.")
                if os.path.exists(dirName + "/" + orgImgName + ".fit"):
                    writeNote("Deleting image.")
                    os.remove(dirName + "/" + orgImgName + ".fit")
                cloudWait()

        else:
            timeStamp("ERROR: " + camMesg)
            softPark()
    
def dsFocus(target):
#
# I did not use the normal atFocus2() routine from the library because I
# don't care about the filters and don't want it to CLS back to target.
# Rather, I'll let the imageStar() logic slew back.
#
    if targHA(target) < 0.75 and targHA(target) > -0.75:
        writeNote("Target is near the meridian.")
        if TSXSend("SelectedHardware.mountModel") !=  "Telescope Mount Simulator":
            TSXSend('sky6RASCOMTele.DoCommand(11, "")')
            if TSXSend("sky6RASCOMTele.DoCommandOutput") == "1":
                TSXSend('sky6RASCOMTele.Jog(420, "E")')
                writeNote("OTA is west of the meridian pointing east.")
                writeNote("Slewing towards the east, away from meridian.")

            else:
                TSXSend('sky6RASCOMTele.Jog(420, "W")')
                writeNote("OTA is east of the meridian, pointing west.")
                writeNote("Slewing towards the west, away from meridian.")


            if "Temma" in TSXSend("SelectedHardware.mountModel"):
                TSXSend("sky6RASCOMTele.SetTracking(1, 1, 0 ,0)")
                writeNote("Resetting Temma tracking rate.")


 
    if TSXSend("ccdsoftCamera.ImageUseDigitizedSkySurvey") == "1":
        timeStamp("@Focus2 success (simulated). Position = " + TSXSend("ccdsoftCamera.focPosition"))
        return "Success"

    else:  
        result = TSXSend("ccdsoftCamera.AtFocus2()")

        if "Process aborted." in result:
            timeStamp("Script Aborted.")
            sys.exit()

        if "Error" in result:
            timeStamp("@Focus2 failed: " + result)
            return "Fail"
        else:

            TSXSend("sky6ObjectInformation.Property(0)")
            TSXSend("sky6ObjectInformation.ObjInfoPropOut")
            
            timeStamp("@Focus2 success.  Position = " + TSXSend("ccdsoftCamera.focPosition") + ". Star = " \
                    + TSXSend("sky6ObjectInformation.ObjInfoPropOut"))
            return "Success"


##### Start of actual program ######

#
# Read through the command line arguments
#
if (len(sys.argv) == 1):
    timeStamp("ERROR. Please specify list of target names to process.")
    sys.exit()

#
# Grab the first (and hopefully only) argument as a file name.
#

fileName = sys.argv[1]

#
# This unfucks windows paths if relevant
#
newPathName = flipPath(fileName)

print("Processing: " + newPathName)

#
# Set some defaults for my camera that other people may not want.
#
if str(TSXSend('ccdsoftCamera.PropStr("m_csObserver")')) ==  "Ken Sturrock":
    if str(TSXSend("SelectedHardware.cameraModel")) == "QSI Camera  ":
        writeNote("Setting up Ken's QSI camera defaults.")
        TSXSend("ccdsoftCamera.TemperatureSetPoint = -10")
        TSXSend("ccdsoftCamera.RegulateTemperature = true")
        TSXSend("ccdsoftCamera.FilterIndexZeroBased = 0")
        TSXSend("ccdsoftCamera.ImageReduction = 1")
        TSXSend('ccdsoftCamera.setPropStr("m_csExCameraMode", "Faster Image Downloads")')

#
# Create variable to hold the star names
#
with open(newPathName) as starNameFile:
    starList = starNameFile.readlines()

# 
# Convert the string of names into a list
#
starList = [line.rstrip() for line in starList]


#
# Create a unique set.
#
for star in starList:
    if ("Object" not in star):
        uniqueTargSet.add(star)

#
# This re-sorts the set back to the optimized order that the SkyX creates.
uniqueTargSet = sorted(uniqueTargSet, key=starList.index)

#
# Convert the set back to a list
#
starList = list(uniqueTargSet)

#
# Remove extra spaces in the name from SkyX
#
for index in range(len(starList)):
    starList[index] = " ".join(starList[index].split())

total = len(starList)

writeNote("Found " + str(total) + " unique target names.")

for index,star in enumerate(starList):

    print("----------")
    timeStamp("Processing: " + star + " (" + str(index + 1) + " of " + str(total) + ")")
    print("----------")


    #
    # Is the target valid?
    #
    result = chkTarget(star)

    if result == "Success":

        if (index % 20 == 0) or (initialFocused == "No"):
        #
        # This calls an initial focus and then one every twenty stars.
        # the yes/no variable is only because if the first star is
        # invalid then it won't do the initial focus.
        #
            writeNote("Attempting to focus.")
            slew(star)
            result = dsFocus(star)
            if result != "Success":
                print("Focus failed!")
                softPark()
            initialFocused = "Yes"

        imageStar(star)

softPark()
