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
# default guider exposure, guiderDelay = default guider delay, defaultFilter = the 
# filter you want to use for focusing and closed loop slews.
#
# If you want to use @F3 instead of @F2, just change the "focusStyle" variable below so
# that it reads ""Three" instead of "Two". CaPiToLiZaTiOn matters, as do the quotes around
# Two and Three.
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
defaultFilter = "0"

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

filterNumC1 = 0
filterNumC2 = 0
perFilC1 = []
perFilC2 = []
numExpC1 = []
numExpC2 = []
expDurC1 = []
expDurC2 = []
totalExpC1 = 0
totalExpC2 = 0
numDupC1 = []
numDupC2 = []
dupGoalC1 = 1
dupGoalC2 = 1
expCountC1 = 1
expCountC2 = 1
totalSecC1 = 0
totalSecC2 = 0
numSets = 0
numSets1 = 0
numSets2 = 0

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

        if CLSlew(target, defaultFilter) == "Fail":
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

def doAnImage(exposureTime, FilterNum):
#
# This function performs the general steps required to take 
# an image. By default, it doesn't mess with the delay and
# only manipulates the camera. It does a follow-up on the
# tracking.
#

    if TSXSend('ccdsoftCamera.PropStr("m_csObserver")') == "Ken Sturrock":
        if TSXSend("SelectedHardware.cameraModel") == "QSI Camera  ":
            TSXSend('ccdsoftCamera.setPropStr("m_csExCameraMode", "Higher Image Quality")')
            writeNote("Setting QSI Camera to high quality mode.")

    if takeImage("Imager", exposureTime, "NA", FilterNum) == "Success":

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
    
        if getStats() == "Fail":
            return "Fail"
    
        return "Success"

    else:
        return "Fail"


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

totalArgs = (len(argumentArray) - 2)

target = argumentArray[1]

camOneExp = []
camTwoExp = []
camTwoIP = "none"

counter = 1

while counter <= totalArgs:
    writeNote("ARGS: " + argumentArray[counter])
    if argumentArray[counter + 1] == "-r":
        if (counter) < totalArgs:
            if "." in argumentArray[counter + 2]:
                camTwoIP = argumentArray[counter + 2]
                counter = counter + 2
            else:
                print("Invalid or incomplete IP address specified for second camera.")
                sys.exit()
        else:
            print("Insufficient arguments provided to specify second camera.")
            sys.exit()

        while counter <= totalArgs:
            camTwoExp.append(argumentArray[counter + 1])
            counter = counter + 1

    else:
        camOneExp.append(argumentArray[counter + 1])

    counter = counter + 1

totalFilC1 = len(camOneExp)
totalFilC2 = len(camTwoExp)

if totalFilC1 > totalFilC2:
    totalFil = totalFilC1
else:
    totalFil = totalFilC2

########################
# Is the target valid? #
########################

chkTarget()

writeNote("Checking cameras.")
camConnect("Imager")

if camTwoIP != "none":
    camConnectRemote(camTwoIP, "Imager")

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

while filterNumC1 < totalFilC1:
    
    perFilC1.append(camOneExp[filterNumC1])


    if perFilC1[filterNumC1].count("x") == 1:
        num,dur=perFilC1[filterNumC1].split("x")
        dup=1

    if perFilC1[filterNumC1].count("x") == 2:
        num,dur,dup=perFilC1[filterNumC1].split("x")

    numDupC1.append(int(dup))
    numExpC1.append(int(num))
    expDurC1.append(int(dur))

    if numDupC1[filterNumC1] == 1:
        adjExposureNum = numExpC1[filterNumC1]
    else:
        adjExposureNum = (numExpC1[filterNumC1] * numDupC1[filterNumC1])

    if TSXSend("SelectedHardware.filterWheelModel") != "<No Filter Wheel Selected>":
        filName = TSXSend("ccdsoftCamera.szFilterName(" + str(filterNumC1) + ")")
    else:
        filName = "no"
     
    print ("           " + str(adjExposureNum) + " exposures for " + str(expDurC1[filterNumC1]) + " secs. with " + filName + " filter.")
    
    totalExpC1 = totalExpC1 + adjExposureNum
    totalSecC1 = totalSecC1 + (expDurC1[filterNumC1] * adjExposureNum)

    if numExpC1[filterNumC1] > numSets1:
        numSets1 = numExpC1[filterNumC1]
    
    filterNumC1 = filterNumC1 + 1
    
print("           -----")
print("           " + str(totalExpC1) + " total exposures for " + str(round((totalSecC1 / 60), 2)) + " total minutes.")
print("           -----")


if camTwoIP != "none":

    print(" ")
    print("           Remote Camera")
    print("           -------------")

    while filterNumC2 < totalFilC2:

        perFilC2.append(camTwoExp[filterNumC2])

        if perFilC2[filterNumC2].count("x") == 1:
            num,dur=perFilC2[filterNumC2].split("x")
            dup=1

        if perFilC2[filterNumC2].count("x") == 2:
            num,dur,dup=perFilC2[filterNumC2].split("x")
    
        numDupC2.append(int(dup))
        numExpC2.append(int(num))
        expDurC2.append(int(dur))
    
        if numDupC2[filterNumC2] == 1:
            adjExposureNum = numExpC2[filterNumC2]
        else:
            adjExposureNum = (numExpC2[filterNumC2] * numDupC2[filterNumC2])

        if TSXSendRemote(camTwoIP,"SelectedHardware.filterWheelModel") != "<No Filter Wheel Selected>":
            filName = TSXSendRemote(camTwoIP,"ccdsoftCamera.szFilterName(" + str(filterNumC2) + ")")
        else:
            filName = "no"

        print ("           " + str(adjExposureNum) + " exposures for " + str(expDurC2[filterNumC2]) + " secs. with " + filName + " filter.")
        
        totalExpC2 = totalExpC2 + adjExposureNum
        totalSecC2 = totalSecC2 + (expDurC2[filterNumC2] * adjExposureNum)

        if numExpC2[filterNumC2] > numSets1:
            numSets1 = numExpC2[filterNumC2]
    
        filterNumC2 = filterNumC2 + 1
    
    print("           -----")
    print("           " + str(totalExpC2) + " total exposures for " + str(round((totalSecC2 / 60), 2)) + " total minutes.")
    print("           -----")
    print(" ")

if numSets1 >= numSets2:
    numSets = numSets1
else:
    numSets = numSets2

######################################
# Move the mount and start the setup #
######################################

#
# My Temmas need the help of Closed Loop Slew to make sure that they get on target
# and resynch. More modern mounts probably don't. If you want to use CLS then
# adjust the logic accordingly.
#


if "Temma" in TSXSend("SelectedHardware.mountModel"):
    if CLSlew(target, defaultFilter) == "Fail":
        timeStamp("There was an error on initial CLS. Stopping script.")
        softPark()
else:
    slew(target)

if camTwoIP != "none":
    slewRemote(camTwoIP, target)

if "<No Focuser Selected>" in TSXSend("SelectedHardware.focuserModel"):
    writeNote("No focuser selected.")

else:
#
# If you have a OSC camera then you'll want to modify the focus routines in this script
# to bin 2x2 before calling atFocus and back to 1x1 after the focus is done.
#
    if camTwoIP == "none":
        timeStamp("Conducting initial focus on local camera.")
        if focusStyle == "Two":
            if atFocus2(target, defaultFilter) == "Fail":
                timeStamp("There was an error on initial focus. Stopping script.")
                softPark()
        elif focusStyle == "Three":
            if atFocus3("NoRTZ", defaultFilter) == "Fail":
                timeStamp("There was an error on initial focus. Stopping script.")
                softPark()
        else:
            writeNote('    ERROR: Focus style not defined. Must be either "Two" or "Three".')
            softPark()
    else:
        timeStamp("Conducting initial focus on both cameras.")
        if focusStyle == "Two":
            if atFocus2Both(camTwoIP, target, defaultFilter) == "Fail":
                timeStamp("There was an error on initial focus. Stopping script.")
                softPark()
        elif focusStyle == "Three":
            if atFocus3("NoRTZ", defaultFilter) == "Fail":
                timeStamp("There was an error on initial (local) focus. Stopping script.")
                softPark()
            elif atFocusRemote(camTwoIP, "Imager", "Three", defaultFilter) == "Fail":
                timeStamp("There was an error on initial (remote) focus. Stopping script.")
                softPark
        else:
            writeNote('    ERROR: Focus style not defined. Must be either "Two" or "Three".')
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
    
        if CLSlew(target, defaultFilter) == "Fail":
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

    while fCounter < totalFil:

        dupCounter = 1
        dupGoalC1 = 1
        dupGoalC2 = 1
       
        if (fCounter <= len(numDupC1) - 1):
            dupGoalC1 = numDupC1[fCounter]

        if (fCounter <= len(numDupC2) - 1):
            dupGoalC2 = numDupC2[fCounter]

        while (dupCounter <= dupGoalC1) or (dupCounter <= dupGoalC2):

            if (fCounter <= (totalFilC2 - 1)) and (numExpC2[fCounter] > 0) and (dupCounter <= dupGoalC2):

                print("           -----")
                writeNote("Starting remote camera image: " + str(expCountC2) + " of " + str(totalExpC2) + ".")
                
                takeImageRemote(camTwoIP, "Imager", str(expDurC2[fCounter]), "0", str(fCounter))
   
            if (fCounter <= (totalFilC1 - 1)) and (numExpC1[fCounter] > 0) and (dupCounter <= dupGoalC1):
                print("           -----")
                writeNote("Starting local camera image " + str(expCountC1) + " of " + str(totalExpC1) + ".")
                expCountC1 = expCountC1 + 1
    
                if doAnImage(str(expDurC1[fCounter]), str(fCounter)) == "Fail":
                    print("    ERROR: Camera problem or clouds..")
    
                    if guiderExposure != "0":
                        stopGuiding()
    
                    cloudWait()
    
                    if CLSlew(target, defaultFilter) == "Fail":
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
                            if doAnImage(str(expDurC1[fCounter]), str(fCounter)) == "Fail":
                                print("    ERROR: There is still a problem.")
                                hardPark()
                            else:
                                writeNote("Resuming Sequence.")
                                
                currentSeconds = round(time.monotonic(),0)

                if "<No Focuser Selected>" in TSXSend("SelectedHardware.focuserModel"):
                    currentTemp = "0"
        
                elif (loopCounter < numSets) or (fCounter < (totalFilC1 - 1)) or (fCounter < (totalFilC2 -1 )):
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
        
                        if camTwoIP == "none":
                            if focusStyle == "Two":
                                if atFocus2(target, defaultFilter) != "Fail":
                                    lastTemp = getTemp()
                                    lastSeconds = round(time.monotonic(),0)
        
                            else:
                                if atFocus3(target, defaultFilter) != "Fail":
                                    lastTemp = getTemp()
                                    lastSeconds = round(time.monotonic(),0)
                        else:
                            if focusStyle == "Two":
                                if atFocus2Both(camTwoIP, target, defaultFilter) != "Fail":
                                    lastTemp = getTemp()
                                    lastSeconds = round(time.monotonic(),0)
        
                            else:
                                if atFocus3(target, defaultFilter) != "Fail":
                                    lastTemp = getTemp()
                                    lastSeconds = round(time.monotonic(),0)
        
                                atFocusRemote(camTwoIP, "Imager", "Three", defaultFilter)

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
                                if CLSlew(target, defaultFilter) == "Fail":
                                    timeStamp("Error finding target post-flip. Stopping script.")
                                    hardPark()

                        if guiderExposure != "0":
                            setUpGuiding()
                
                            if settleGuider(setLimit) == "Lost":
                                print("    ERROR: Guiding setup failed.")
                                stopGuiding()
                
                                cloudWait()
                
                                if CLSlew(target, defaultFilter) == "Fail":
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
    
            if (fCounter <= (totalFilC2 - 1)) and (numExpC2[fCounter] > 0) and (dupCounter <= dupGoalC2):
                print("           -----")
                remoteImageDone(camTwoIP, "Imager")
                getStatsRemote(camTwoIP, "Imager")
                expCountC2 = expCountC2 + 1

            dupCounter = dupCounter + 1

        numExpC1[fCounter] = numExpC1[fCounter] - 1
        if (fCounter <= (totalFilC2 - 1)) and (numExpC2[fCounter] > 0):
            numExpC2[fCounter] = numExpC2[fCounter] - 1

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
                if CLSlew(target, defaultFilter) == "Fail":
                    timeStamp("Error finding target post-flip. Stopping script.")
                    hardPark()
            else:
                CLSlew(target, defaultFilter)

            #
            # This refocuses after a meridian flip in case something mechanical moved.
            #
            if "<No Focuser Selected>" not in TSXSend("SelectedHardware.focuserModel"):

                if camTwoIP == "none":
                    if focusStyle == "Two":
                        atFocus2(target, defaultFilter) 
                    elif focusStyle == "Three":
                        atFocus3("NoRTZ", defaultFilter) 
                else:
                    if focusStyle == "Two":
                        atFocus2Both(camTwoIP, target, defaultFilter)

                    elif focusStyle == "Three":
                        atFocus3("NoRTZ", defaultFilter) == "Fail"
                        atFocusRemote(camTwoIP, "Imager", "Three", defaultFilter)

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
                if CLSlew(target, defaultFilter) == "Fail":
                    timeStamp("Error finding target post-flip. Stopping script.")
                    hardPark()

        if guiderExposure != "0":
            setUpGuiding()
    
            if settleGuider(setLimit) == "Lost":
                print("    ERROR: Guiding setup failed.")
                stopGuiding()
    
                cloudWait()
    
                if CLSlew(target, defaultFilter) == "Fail":
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

if camTwoIP != "none":
    writeNote("Disconnecting remote camera.")
    camDisconnectRemote(camTwoIP, "Imager")

hardPark()

