#!/usr/bin/env python3
#
# Run an automated session on SkyX.
#
# In addition to activating the TCP Server, you also have to switch on "TCP socket closing"
# under SkyX's Preferences -> Advanced.
#
# Syntax and functions are almost the same as the older Bash-based run_target script.
#
#       ./run_target-2 m51 5x300 5x300 5x300 5x300
#
# Second camera is activated with the "-r" option followed by the IP address and port
# of the second SkyX instance:
#
#       ./run_target-2 m51 5x300 5x300 5x300 5x300 -r 10.0.1.11:3040 3x240 3x240 3x240 3x240
#
# You can also add extra non-dithered frames to each set with an addition "x". For example:
#
#       ./run_target-2 m51 5x300x2 5x300 5x300 5x300
#
# will cause an LLRGB LLRGB pattern.
#
# Set the four variables below (altLimit = minumum starting altitude, guiderExposure =
# default guider exposure, guiderDelay = default guider delay
#
#
# Ken Sturrock
# November 16, 2019
#

#############################
# User Modifiable Variables #
#############################

# How low can we start?
altLimit = 30

# Which filter should we use for focuses and CLS?
#
focusWithFilter = "0"
clsWithFilter = "0"

imageBinning = "1"

# Do you use a default guider delay?
guiderDelay = "0"

# Which version of @Focus do you use? Two or Three?
focusStyle = "Three"

# Set guiderExposure to 0 (zero) for guiderless or don't choose a guide camera in SkyX.
guiderExposure = "5"

# This is the hour angle at which the mount flips if a GoTo is commanded.
# Logically, a flip angle of zero is easiest to wrap your mind around but it
# can be anything so long as it matches what the mount does. If you are using
# a Paramount, consult your flip angle settings within Bisque TCS.
flipAngle = 0
focusTempDelta = 0.5
focusTimeDelta = 30 * 60
defaultSettleTime = 5

####################
# Import Libraries #
####################

from library.PySkyX_ks import *

import time
import sys
import os
import datetime

########################
# Script set Variables #
########################

filterNumber = 0
perFil = []
numExp = []
exposureDurations = []
totalExposures = 0
numDup = []
dupGoal = 1
expCount = 1
totalSeconds = 0
remainingSeconds = 0
numSets = 0

####################
# Define Functions #
####################


def chkTarget():
#
# This validates the target and ensures that it is up & that it's night.
#
    timeStamp("Target is " + target + ".")

    if targExists(target) == "No":
        print("    ERROR: " + target + " not found in SkyX database.")
        softPark()
    
    isDayLight()

    currentHA = targHA(target)
    currentAlt = targAlt(target) 

    if currentAlt < altLimit and currentHA > 0:
        timeStamp("Target " + target + " is " + str(round(currentAlt, 2)) + " degrees high.")
        timeStamp("Target " + target + " has sunk too low.")
        softPark()
    
    while currentAlt < altLimit:
        writeNote("Target " + target + " is " + str(round(currentAlt, 2)) + " degrees high.")
        writeNote("Starting altitude is set for: " + str(altLimit) + " degrees.")
        writeNote("Target " + target + " is still too low.")
        timeStamp("Waiting five minutes.")
        time.sleep (360)
        currentAlt = targAlt(target) 


def setUpGuiding():
#
# This is a "macro" that calls several simpler functions in 
# order to set up autoguiding.
#
    camConnect("Guider")

    stopGuiding()

    time.sleep(5)

    takeImage("Guider", guiderExposure, "0", "NA")

    AGStar = findAGStar()

    if "Error" in AGStar:
        cloudWait()

        if CLSlew(target, clsWithFilter) == "Fail":
            timeStamp("There was an error CLSing to Target. Stopping script.")
            hardPark()

        takeImage("Guider", guiderExposure, "0", "NA")

        AGStar = findAGStar()
     
        if "Error" in AGStar:
            print("    ERROR: Still cannot find a guide star. Sorry it didn't work out...")
            hardPark()
        else:
            XCoord,YCoord = AGStar.split(",")
    else:    
        XCoord,YCoord = AGStar.split(",")

    expRecommends = adjAGExposure(guiderExposure, guiderDelay, XCoord, YCoord)
    newGuiderExposure,newGuiderDelay = expRecommends.split(",")

    startGuiding(newGuiderExposure, newGuiderDelay, float(XCoord), float(YCoord))

def doAnImage(exposureTime, filterNumber, binning):
#
# This function performs the general steps required to take 
# an image. By default, it doesn't mess with the delay and
# only manipulates the camera. It does a follow-up on the
# tracking.
#

    TSXSend("ccdsoftCamera.BinX = " + str(binning))
    TSXSend("ccdsoftCamera.BinY = " + str(binning))

    if TSXSend('ccdsoftCamera.PropStr("m_csObserver")') == "Ken Sturrock":
        if TSXSend("SelectedHardware.cameraModel") == "QSI Camera  ":
            TSXSend('ccdsoftCamera.setPropStr("m_csExCameraMode", "Higher Image Quality")')
            writeNote("Setting QSI Camera to high quality mode.")

    if takeImage("Imager", exposureTime, "NA", filterNumber) == "Success":

        if TSXSend('ccdsoftCamera.PropStr("m_csObserver")') == "Ken Sturrock":
            if TSXSend("SelectedHardware.cameraModel") == "QSI Camera  ":
                TSXSend('ccdsoftCamera.setPropStr("m_csExCameraMode", "Faster Image Downloads")')
                writeNote("Setting QSI Camera to faster download mode.")

        if guiderExposure != "0":
            if isGuiderLost(setLimit) == "Yes":
                #
                # If the guider looks lost, try it again
                #
                writeNote("Double Checking Guider.")
                time.sleep(5)
                if isGuiderLost(setLimit) == "Yes":
                    print("    ERROR: Guider looks lost")
                    return "Fail"
                else:
                    writeNote("Guiding is questionable.")
            else:
                writeNote("Guider Tracking.")
    
        # if getStats() == "Fail":
        #     return "Fail"
    
        return "Success"

    else:
        return "Fail"

def estimatedCompletionTime(secondsRemaining):
    now = datetime.datetime.now() + datetime.timedelta(seconds=secondsRemaining)
    return now.strftime("%H:%M:%S")

######################
# Main Program Start #
######################

timeStamp("Script Running")

print("     DATE: " + datetime.date.today().strftime("%Y" + "-" + "%B" + "-" + "%d"))

tcpChk()

writeNote("SkyX Pro Build Level: " + TSXSend("Application.build"))

if sys.platform == "win32":
    writeNote("Running on Windows.")

if sys.platform == "darwin":
    writeNote("Running on Macintosh.")

if sys.platform == "linux":
	if os.uname()[4].startswith("arm"):
		writeNote("Running on R-Pi.")
	else:
		writeNote("Running on Linux.")

#
# preRun checks some settings to head off questions later
#
if preRun() == "Fail":
    sys.exit()


# Turn off guiding functions if no guider chosen in SkyX.
if TSXSend("SelectedHardware.autoguiderCameraModel") == "<No Camera Selected>":
    guiderExposure = "0"

if guiderExposure == "0":
    writeNote("Guiding disabled.")


#####################################################################
# Take apart the arguments to figure out what the user wants to do. #
#####################################################################

totalArgs = (len(sys.argv) - 2)

if totalArgs < 1:
#
# If the user hasn't specified command line arguments, fire up the GUI.
#
    timeStamp("Insufficient command line arguments.")
    print("           Syntax: " + sys.argv[0] + " target FxE FxE ...")
    
    print(" ")
    print("----------")
    timeStamp("Launching graphical interface.")

    # Only load the GUI libraries if they need to be used.
    from library.RT_GUI import runGUI
    
    GUIresults = runGUI()
    timeStamp("Closing graphical interface.")
    print("----------")
    print(" ")

    argumentArray = GUIresults[0]
    guiderExposure = GUIresults[1]
    guiderDelay = GUIresults[2]
    focusStyle = GUIresults[3]

else:
    argumentArray = sys.argv

totalArgs = (len(argumentArray) - 1)

exposures = []

counter = 1
target = argumentArray[counter]
counter = counter + 1


while counter <= totalArgs:
    writeNote("ARGS: " + argumentArray[counter])
    exposures.append(argumentArray[counter])
    counter = counter + 1

totalFilters = len(exposures)

########################
# Is the target valid? #
########################

writeNote("Checking Target: " + target)
chkTarget()

writeNote("Checking cameras.")
camConnect("Imager")

if str(TSXSend("SelectedHardware.mountModel")) ==  "Telescope Mount Simulator":
    writeNote("Simulated Mount.")
else:
    writeNote("Checking sidereal drive.")
    TSXSend("sky6RASCOMTele.SetTracking(1, 1, 0 ,0)")

#############################################
# Work out the imaging plan and explain it. #
#############################################

print("     PLAN:")
print("           Local Camera")
print("           ------------")

while filterNumber < totalFilters:
    
    perFil.append(exposures[filterNumber])

    if perFil[filterNumber].count("x") == 1:
        num,dur=perFil[filterNumber].split("x")
        dup=1

    if perFil[filterNumber].count("x") == 2:
        num,dur,dup=perFil[filterNumber].split("x")

    numDup.append(int(dup))
    numExp.append(int(num))
    exposureDurations.append(int(dur))

    if numDup[filterNumber] == 1:
        adjExposureNum = numExp[filterNumber]
    else:
        adjExposureNum = (numExp[filterNumber] * numDup[filterNumber])

    if TSXSend("SelectedHardware.filterWheelModel") != "<No Filter Wheel Selected>":
        filName = TSXSend("ccdsoftCamera.szFilterName(" + str(filterNumber) + ")")
    else:
        filName = "no"
     
    print ("           " + str(adjExposureNum) + " exposures for " + str(exposureDurations[filterNumber]) + "s with " + filName + " filter.")
    
    totalExposures = totalExposures + adjExposureNum
    totalSeconds = totalSeconds + (exposureDurations[filterNumber] * adjExposureNum)
    if numExp[filterNumber] > numSets:
        numSets = numExp[filterNumber]
    
    remainingSeconds = totalSeconds
    filterNumber = filterNumber + 1

print("           -----")
print("           " + str(totalExposures) + " total exposures for " + str(round((totalSeconds / 60), 2)) + " total minutes.")
print("           " + "Earliest completion time: " + estimatedCompletionTime(totalSeconds))
print("           -----")

######################################
# Move the mount and start the setup #
######################################

if CLSlew(target, clsWithFilter) == "Fail":
    timeStamp("There was an error on initial CLS. Stopping script.")
    softPark()

if "<No Focuser Selected>" in TSXSend("SelectedHardware.focuserModel"):
    writeNote("No focuser selected.")

else:

# If you have a OSC camera then you'll want to modify the focus routines in this script
# to bin 2x2 before calling atFocus and back to 1x1 after the focus is done.
#
    timeStamp("Conducting initial focus on local camera.")
    if atFocus3("NoRTZ", focusWithFilter) == "Fail":
        timeStamp("There was an error on initial focus. Stopping script.")
        softPark()

lastTargHA = targHA(target)

if "<No Focuser Selected>" not in TSXSend("SelectedHardware.focuserModel"):
    lastTemp = getTemp()
    lastSeconds = round(time.monotonic(),0)

#
# Are we guiding?
#
if guiderExposure != "0":
 
    setLimit = calcSettleLimit()
    setUpGuiding()

    #
    # Figure out what to do if guider settling fails
    #
    if settleGuider(setLimit) == "Lost":
        print("    ERROR: Guiding setup failed.")
        stopGuiding()
    
        cloudWait()
    
        if CLSlew(target, clsWithFilter) == "Fail":
            timeStamp("There was an error CLSing to Target. Stopping script.")
            hardPark()
    
        setUpGuiding()
    
        setLimit = calcSettleLimit()
    
        if settleGuider(setLimit) == "Lost":
            print("    ERROR: Guiding setup failed again.")
            hardPark()
else:
    timeStamp("Waiting  " + defaultSettleTime + " seconds for mount to settle.")
    time.sleep(defaultSettleTime)

###############################
# Start the main imaging loop #
###############################

loopCounter = 1 

while loopCounter <= numSets:

    print("     -----")
    writeNote("Starting image SET " + str(loopCounter) + " of " + str(numSets) + ".")
    
    fCounter = 0

    while fCounter < totalFilters:

        dupCounter = 1
        dupGoal = 1
       
        if (fCounter <= len(numDup) - 1):
            dupGoal = numDup[fCounter]

        while (dupCounter <= dupGoal):

            if (fCounter <= (totalFilters - 1)) and (numExp[fCounter] > 0) and (dupCounter <= dupGoal):

                remainingSeconds = remainingSeconds - exposureDurations[fCounter]
                
                print("           -----")
                
                writeNote("Starting local camera image " + str(expCount) + " of " + str(totalExposures) + " - Earliest completion: " + estimatedCompletionTime(remainingSeconds))
                expCount = expCount + 1
    
                if doAnImage(str(exposureDurations[fCounter]), str(fCounter), imageBinning) == "Fail":
                    print("    ERROR: Camera problem or clouds..")
    
                    if guiderExposure != "0":
                        stopGuiding()
    
                    cloudWait()
    
                    if CLSlew(target, clsWithFilter) == "Fail":
                        timeStamp("There was an error CLSing to Target. Stopping script.")
                        hardPark()
    
                    if guiderExposure != "0":
                        setUpGuiding()
    
                        setLimit = calcSettleLimit()
    
                        if settleGuider(setLimit) == "Lost":
                            print("    ERROR: Unable to setup guiding.")
                            hardPark()
                        else:
                            writeNote("Attempting to retake image.")
                            if doAnImage(str(exposureDurations[fCounter]), str(fCounter), imageBinning) == "Fail":
                                print("    ERROR: There is still a problem.")
                                hardPark()
                            else:
                                writeNote("Resuming Sequence.")
                                
                currentSeconds = round(time.monotonic(),0)

                if "<No Focuser Selected>" in TSXSend("SelectedHardware.focuserModel"):
                    currentTemp = "0"
        
                elif (loopCounter < numSets) or (fCounter < (totalFilters - 1)):
                #
                # This is the usual periodic focus touch up after a temperature change
                # or time elapse.
                #    

                    currentTemp = getTemp()
    
                    if abs(lastTemp - currentTemp) > focusTempDelta or (currentSeconds - lastSeconds) > focusTimeDelta:
                        print("     -----")
                        writeNote("Touching-up Focus.")
        
                        if guiderExposure != "0":
                            stopGuiding()
                            writeNote("Guiding Stopped.")
        
                        if atFocus3(target, focusWithFilter) != "Fail":
                            lastTemp = getTemp()
                            lastSeconds = round(time.monotonic(),0)

                        dither()

                        #            
                        # Did the mount flip unexpectedly?
                        #
                        if TSXSend("SelectedHardware.mountModel") !=  "Telescope Mount Simulator":
                            TSXSend('sky6RASCOMTele.DoCommand(11, "")')
                            if (TSXSend("sky6RASCOMTele.DoCommandOutput") == "1") and (targHA(target) > flipAngle):
                                print("    ERROR: The target is west of the meridian but the mount has not appeared to flip.")
                
                            if (TSXSend("sky6RASCOMTele.DoCommandOutput") == "0") and (targHA(target) <= flipAngle):
                                print("    ERROR: The target is still east of the meridian but the mount appears to have flipped.")
                                writeNote("Using CLS to ensure target alignment.")
                                if CLSlew(target, clsWithFilter) == "Fail":
                                    timeStamp("Error finding target post-flip. Stopping script.")
                                    hardPark()

                        if guiderExposure != "0":
                            setUpGuiding()
                
                            if settleGuider(setLimit) == "Lost":
                                print("    ERROR: Guiding setup failed.")
                                stopGuiding()
                
                                cloudWait()
                
                                if CLSlew(target, clsWithFilter) == "Fail":
                                    timeStamp("There was an error CLSing to Target. Stopping script.")
                                    hardPark()
                
                                setUpGuiding()
                
                                setLimit = calcSettleLimit()
                
                                if settleGuider(setLimit) == "Lost":
                                    print("    ERROR: Guiding setup failed again.")
                                    hardPark()
                        else:
                            timeStamp("Waiting 20 seconds for mount to settle.")
                            time.sleep(20)

            dupCounter = dupCounter + 1

        numExp[fCounter] = numExp[fCounter] - 1

        fCounter = fCounter + 1

    loopCounter = loopCounter + 1

    if guiderExposure != "0":
        stopGuiding()
        print("     -----")
        writeNote("Guiding Stopped.")

#########################################################
# Start the between-imaging-set housekeeping functions #
#########################################################

    print("     -----")
    
    if loopCounter <= numSets:
        isDayLight()

        if targAlt(target) < 35 and targHA(target) > 0:
            timeStamp("Target has sunk too low.")
            hardPark()


        if targHA(target) > flipAngle and lastTargHA <= flipAngle:
            timeStamp("Target has crossed the meridian.")
                
            if "Temma" in TSXSend("SelectedHardware.mountModel"):
                if CLSlew(target, clsWithFilter) == "Fail":
                    timeStamp("Error finding target post-flip. Stopping script.")
                    hardPark()
            else:
                CLSlew(target, clsWithFilter)

            #
            # This refocuses after a meridian flip in case something mechanical moved.
            #
            if "<No Focuser Selected>" not in TSXSend("SelectedHardware.focuserModel"):

                atFocus3("NoRTZ", focusWithFilter) 

                lastTemp = getTemp()
                lastSeconds = round(time.monotonic(),0)

            lastTargHA = targHA(target)

        
        else:
            dither()

        #            
        # Did the mount flip unexpectedly?
        #
        if TSXSend("SelectedHardware.mountModel") !=  "Telescope Mount Simulator":
            TSXSend('sky6RASCOMTele.DoCommand(11, "")')
            if (TSXSend("sky6RASCOMTele.DoCommandOutput") == "1") and (targHA(target) > flipAngle):
                print("    ERROR: The target is west of the meridian but the mount has not appeared to flip.")

            if (TSXSend("sky6RASCOMTele.DoCommandOutput") == "0") and (targHA(target) <= flipAngle):
                print("    ERROR: The target is still east of the meridian but the mount appears to have flipped.")
                writeNote("Using CLS to ensure target alignment.")
                if CLSlew(target, clsWithFilter) == "Fail":
                    timeStamp("Error finding target post-flip. Stopping script.")
                    hardPark()

        if guiderExposure != "0":
            setUpGuiding()
    
            if settleGuider(setLimit) == "Lost":
                print("    ERROR: Guiding setup failed.")
                stopGuiding()
    
                cloudWait()
    
                if CLSlew(target, clsWithFilter) == "Fail":
                    timeStamp("There was an error CLSing to Target. Stopping script.")
                    hardPark()
    
                setUpGuiding()
    
                setLimit = calcSettleLimit()
    
                if settleGuider(setLimit) == "Lost":
                    print("    ERROR: Guiding setup failed again.")
                    hardPark()
        else:
            timeStamp("Waiting 20 seconds for mount to settle.")
            time.sleep(20)

hardPark()

