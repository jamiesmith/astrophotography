#!/usr/bin/env python3
#
# Python library for automating SkyX functions.
#
# It was a bitch to write, it should be a bitch to read.
#
# There are three broad families of functions: Acquisition, Calibration & Astrometry
#
# Ken Sturrock
# Nov 10, 2019
#

TSXHost = "127.0.0.1"		# You can set this if you want to run the functions remotely
                                # The "*Remote functions" already handle that internally.

TSXPort = 3040                  # 3040 is the default, it can be changed

verbose = False 		# Set this to "True" for debugging to see the Javascript traffic.

CR = "\n"			# A prettier shortcut for a newline.

import time
import socket
import sys
import os
import random
import math
import pathlib
import glob
import statistics


def adjAGExposure(origAGExp, origAGDelay, XCoord, YCoord):
#
# Measure the brightness of the selected guide star and suggest tweaks
# if the star is really bright or really dim. Ideally, the star should
# not be saturated, because the star finder wouldn't have suggested it.
#
#

    if TSXSend("ccdsoftAutoguider.ImageReduction") != "0":

        writeNote("Measuring AG exposure.")
    
        imageDepth = TSXSend('ccdsoftAutoguiderImage.FITSKeyword("BITPIX")')
        if "Error = 250" in imageDepth:
            print("    ERROR: FITS Keyword BITPIX not found. Assuming 16-bit.")
            imageDepth = 16

        newXCoord = float(TSXSend('ccdsoftAutoguider.BinX')) * float(XCoord)  
        newYCoord = float(TSXSend('ccdsoftAutoguider.BinY')) * float(YCoord)
    
        boxSizeVert = int(float(TSXSend("ccdsoftAutoguider.TrackBoxY")) / 2)
        boxSizeHoriz = int(float(TSXSend("ccdsoftAutoguider.TrackBoxX")) / 2)
    
        newTop = int(newYCoord - boxSizeVert)
        newBottom = int(newYCoord + boxSizeVert)
        newLeft = int(newXCoord - boxSizeHoriz)
        newRight = int(newXCoord + boxSizeHoriz)
    
        TSXSend("ccdsoftAutoguider.SubframeTop = " + str(newTop))
        TSXSend("ccdsoftAutoguider.SubframeLeft = " + str(newLeft))
        TSXSend("ccdsoftAutoguider.SubframeBottom = " + str(newBottom))
        TSXSend("ccdsoftAutoguider.SubframeRight = " + str(newRight))
    
        TSXSend("ccdsoftAutoguider.Subframe = true")
        TSXSend("ccdsoftAutoguider.Delay = 1")
        TSXSend("ccdsoftAutoguider.AutoSaveOn = false")
        TSXSend("ccdsoftAutoguider.ExposureTime = " + origAGExp)
    
        TSXSend("ccdsoftAutoguider.TakeImage()")
    
        fullWell = math.pow (2, int(imageDepth))
        brightestPix = TSXSend("ccdsoftAutoguider.MaximumPixel")
        brightness = round((int(brightestPix) / int(fullWell)), 2)
        writeNote("AG Brightness: " + str(brightness))

        totalTime = float(origAGExp) + float(origAGDelay)


        if brightness >= 0.2 and brightness <= 0.75:
            writeNote("No guider exposure change recommended.")
            return str(origAGExp) + "," + str(origAGDelay)

        else:
            units = brightness / float(origAGExp)
    
            if brightness > 0.75:
                writeNote("Star too bright.")

                while brightness > 0.85:

                    origAGExp = float(origAGExp) / 2
                    TSXSend("ccdsoftAutoguider.ExposureTime = " + str(origAGExp))
                    TSXSend("ccdsoftAutoguider.TakeImage()")
                    fullWell = math.pow (2, int(imageDepth))
                    brightestPix = TSXSend("ccdsoftAutoguider.MaximumPixel")
                    brightness = round((int(brightestPix) / int(fullWell)), 2)
                    writeNote("Exposure: " + str(origAGExp) + " Brightness: " + str(brightness))

                    units = brightness / float(origAGExp)

                newExp = 0.55 / units

            if brightness < 0.2:
                newExp = 0.3 / units
    
            newExp = round(newExp, 1)
            newDelay = float(totalTime) - float(newExp) 
            newDelay = round(newDelay, 1)
    
            if newDelay < 0:
                newDelay = 0
    
            if newExp > (float(origAGExp) * 1.5):
                newExp = (float(origAGExp) * 1.5)
    
            writeNote("Recommend AG exposure of " + str(newExp) + " and a delay of " + str(newDelay) + ".")
            return str(newExp) + "," + str(newDelay)
    else:
        writeNote("AG exposure not adjusted because guider is not calibrated.")
        return str(origAGExp) + "," + str(origAGDelay)


def atFocus2(target, filterNum):
#
# Focus using @F2. Because @Focus2 will sometimes do annoying stuff
# like choosing a focus star on the wrong side of the meridian, 
# we force the mount to jog east or west to get it away from the
# meridian if needed.
#
# Uses some DoCommand/BTP analysis action. Thanks to Greg Schwimer for showing
# me how to use that.
#
    if targHA(target) < 0.75 and targHA(target) > -0.75:
        writeNote("Target is near the meridian.")
        if TSXSend("SelectedHardware.mountModel") !=  "Telescope Mount Simulator":
            TSXSend('sky6RASCOMTele.DoCommand(11, "")')
            if TSXSend("sky6RASCOMTele.DoCommandOutput") == "1":
                TSXSend('sky6RASCOMTele.Jog(420, "E")')
                writeNote("OTA is west of the meridian pointing east.")
                writeNote("Slewing towards the east, away from meridian.")

                #
                # This resets the sidereal rate on my Temma because jogging appears
                # to screw up the tracking speed.
                #
                if "Temma" in TSXSend("SelectedHardware.mountModel"):
                    TSXSend("sky6RASCOMTele.SetTracking(1, 1, 0 ,0)")
                    writeNote("Resetting Temma tracking rate.")


            else:
                TSXSend('sky6RASCOMTele.Jog(420, "W")')
                writeNote("OTA is east of the meridian, pointing west.")
                writeNote("Slewing towards the west, away from meridian.")

                #
                # This resets the sidereal rate on my Temma because jogging appears
                # to screw up the tracking speed.
                #
                if "Temma" in TSXSend("SelectedHardware.mountModel"):
                    TSXSend("sky6RASCOMTele.SetTracking(1, 1, 0 ,0)")
                    writeNote("Resetting Temma tracking rate.")

 
    if TSXSend("SelectedHardware.filterWheelModel") != "<No Filter Wheel Selected>":
        TSXSend("ccdsoftCamera.filterWheelConnect()")	
        TSXSend("ccdsoftCamera.FilterIndexZeroBased = " + filterNum) 

    if TSXSend("ccdsoftCamera.ImageUseDigitizedSkySurvey") == "1":
        timeStamp("@Focus2 success (simulated). Position = " + TSXSend("ccdsoftCamera.focPosition"))
        writeNote("Returning to target.")
        if CLSlew(target, filterNum) == "Fail":
            hardPark()
        return "Success"

    else:  
    #
    # Here would be a good place to insert some binning code if you have a OSC camera and     
    # haven't done it elsewhere (which is the better option...). You'd also need to switch it back.
    #
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
            if CLSlew(target, filterNum) == "Fail":
                hardPark()
            return "Success"

def atFocus2Both(host, target, filterNum):
#
# Butchered version of @Focus2 routine to add a second camera.
#
# The only difference is that it calls the remote @Focus2 routine
# before slewing (both) back to target.
#
# It would probably be a lot easier to just use @Focus3 on the remote
# camera. If you use @Focus2, though, make sure that you calibrate
# the remote @Focus2 to use ther same magnitude stars as the main
# camera uses.
#


    if targHA(target) < 0.75 and targHA(target) > -0.75:
        writeNote("Target is near the meridian.")
        if TSXSend("SelectedHardware.mountModel") !=  "Telescope Mount Simulator":
            TSXSend('sky6RASCOMTele.DoCommand(11, "")')
            if TSXSend("sky6RASCOMTele.DoCommandOutput") == "1":
                TSXSend('sky6RASCOMTele.Jog(420, "E")')
                writeNote("OTA is west of the meridian pointing east.")
                writeNote("Slewing towards the east, away from meridian.")

                #
                # This resets the sidereal rate on my Temma because jogging appears
                # to screw up the tracking speed.
                #
                if "Temma" in TSXSend("SelectedHardware.mountModel"):
                    TSXSend("sky6RASCOMTele.SetTracking(1, 1, 0 ,0)")
                    writeNote("Resetting Temma tracking rate.")

            else:
                TSXSend('sky6RASCOMTele.Jog(420, "W")')
                writeNote("OTA is east of the meridian, pointing west.")
                writeNote("Slewing towards the west, away from meridian.")

                #
                # This resets the sidereal rate on my Temma because jogging appears
                # to screw up the tracking speed.
                #
                if "Temma" in TSXSend("SelectedHardware.mountModel"):
                    TSXSend("sky6RASCOMTele.SetTracking(1, 1, 0 ,0)")
                    writeNote("Resetting Temma tracking rate.")

    if TSXSend("SelectedHardware.filterWheelModel") != "<No Filter Wheel Selected>":
        TSXSend("ccdsoftCamera.filterWheelConnect()")	
        TSXSend("ccdsoftCamera.FilterIndexZeroBased = " + filterNum) 

    if TSXSend("ccdsoftCamera.ImageUseDigitizedSkySurvey") == "1":
        timeStamp("@Focus2 success (simulated). Position = " + TSXSend("ccdsoftCamera.focPosition"))

        atFocusRemote(host, "Imager", "Two", filterNum )
        slewRemote(host, target)

        if CLSlew(target, filterNum) == "Fail":
            hardPark()
        return "Success"

    else:  
        result = TSXSend("ccdsoftCamera.AtFocus2()")

        if "Process aborted." in result:
            timeStamp("Script Aborted.")
            sys.exit()

        if "Error" in result:
            timeStamp("@Focus2 failed: " + result)

            if CLSlew(target, filterNum) == "Fail":
                hardPark()

            return "Fail"
        else:
            timeStamp("@Focus2 success.  Position = " + TSXSend("ccdsoftCamera.focPosition"))

            atFocusRemote(host, "Imager", "Two", filterNum )
            slewRemote(host, target)

            if CLSlew(target, filterNum) == "Fail":
                hardPark()
            return "Success"


def atFocus3(target, filterNum):
#
# This function runs @Focus3.
#
# Be aware that, if you're using this function, it's probably because you're
# trying to automate something. In which case, you're probably also dithering
# and you're also probably asleep. Even though @F3 doesn't require a slew back
# to target, this routine includes some code to periodically CLS back to
# your target both to reset the dither pattern and also because bad stuff
# happens and an occasional Return to Zero isn't bad (Until your mount comes
# back around). Specify target as "NoRTZ" to skip the recenter (for example, on 
# the initial focus).
#
# The @Focus3 JS command, itself, has two parameters. The "3" can be replaced by
# some other number to tell it how many samples to take & average at each position.
# Don't bother with two samples. Use one sample if your skies are great, five if 
# terrible and three for most places. The "true" tells it to select a subframe
# automatically. If you use "false" then you will have to define your own subframe
# or it will focus full-frame. It extracts the step size from the INI which you'll 
# have to set with the @F3 dialog box during a previous run.
#
    timeStamp("Focusing with @Focus3.")

    if TSXSend("SelectedHardware.filterWheelModel") != "<No Filter Wheel Selected>":
        TSXSend("ccdsoftCamera.filterWheelConnect()")	
        TSXSend("ccdsoftCamera.FilterIndexZeroBased = " + filterNum) 

    if TSXSend("ccdsoftCamera.ImageUseDigitizedSkySurvey") == "1":
        timeStamp("@Focus3 success (simulated). Position = " + TSXSend("ccdsoftCamera.focPosition"))
        if target != "NoRTZ":
            if random.choice('12') == "2":
                writeNote("Recentering target.")
                if CLSlew(target, filterNum) == "Fail":
                    hardPark()
            else:
                writeNote("Not recentering target at this time.")

        return "Success"

    else:  
        result = TSXSend("ccdsoftCamera.AtFocus3(3, true)")

        if "Process aborted." in result:
            timeStamp("Script Aborted.")
            sys.exit()

        if "Error" in result:
            timeStamp("@Focus3 failed: " + result)
            if target != "NoRTZ":
                if random.choice('12') == "2":
                    writeNote("Recentering target.")
                    if CLSlew(target, filterNum) == "Fail":
                        hardPark()
                else:
                    writeNote("Not recentering target at this time.")
            return "Fail"

        else:
            timeStamp("@Focus3 success. Position = " + TSXSend("ccdsoftCamera.focPosition"))
            if target != "NoRTZ":
                if random.choice('12') == "2":
                    writeNote("Recentering target.")
                    if CLSlew(target, filterNum) == "Fail":
                        hardPark()
                else:
                    writeNote("Not recentering target at this time.")

            return "Success"

def atFocusRemote(host, whichCam, method, filterNum):
#
# This is for focusing a second (or third) remote camera
#

    time.sleep(5)

    TSXSendRemote(host,"ccdsoftCamera.Asynchronous = false")

    if whichCam not in ("Imager", "Guider"):
        print("   ERROR: Please specify remote camera as either: Imager or Guider.")

    if whichCam == "Imager":
        if TSXSendRemote(host,"SelectedHardware.filterWheelModel") != "<No Filter Wheel Selected>":
            TSXSendRemote(host,"ccdsoftCamera.filterWheelConnect()")
            TSXSendRemote(host,"ccdsoftCamera.FilterIndexZeroBased = " + filterNum)

    if whichCam == "Guider":
        if TSXSendRemote(host,"SelectedHardware.autoguiderFilterWheelModel") != "<No Filter Wheel Selected>":
            TSXSendRemote(host,"ccdsoftAutoguider.filterWheelConnect()")
            TSXSendRemote(host,"ccdsoftAutoguider.FilterIndexZeroBased = " + filterNum)

    if whichCam == "Imager":    
        if method == "Three":
            timeStamp("Focusing remote imaging camera with @Focus3.")


            if (TSXSendRemote(host,"ccdsoftCamera.ImageUseDigitizedSkySurvey") == "1") or \
               (TSXSendRemote(host,"SelectedHardware.focuserModel") == "<No Focuser Selected>"):
                if TSXSendRemote(host,"ccdsoftCamera.ImageUseDigitizedSkySurvey") == "1":
                    timeStamp("@Focus3 success (simulated). Position = " + TSXSendRemote(host,"ccdsoftCamera.focPosition"))
                    return "Success"
                else:
                    timeStamp("No remote focuser detected.")
                    return "Success"

            else:  
                result = TSXSendRemote(host,"ccdsoftCamera.AtFocus3(3, true)")

                if "Process aborted." in result:
                    timeStamp("Script Aborted.")
                    sys.exit()

                if "Error" in result:
                    timeStamp("Remote @Focus3 failed: " + result)
                    return "Fail"

                else:
                    timeStamp("@Focus3 success. Position = " + TSXSendRemote(host,"ccdsoftCamera.focPosition"))
                    time.sleep(5)
                    return "Success"


        if method == "Two":
            timeStamp("Focusing remote imaging camera with @Focus2.")

            if (TSXSendRemote(host,"ccdsoftCamera.ImageUseDigitizedSkySurvey") == "1") or \
               (TSXSendRemote(host,"SelectedHardware.focuserModel") == "<No Focuser Selected>"):
                if TSXSendRemote(host,"ccdsoftCamera.ImageUseDigitizedSkySurvey") == "1":
                    timeStamp("@Focus2 success (simulated). Position = " + TSXSendRemote(host,"ccdsoftCamera.focPosition"))
                    return "Success"
                else:
                    timeStamp("No remote focuser detected.")
                    return "Success"

            else:  
                result = TSXSendRemote(host,"ccdsoftCamera.AtFocus2()")

                if "Process aborted." in result:
                    timeStamp("Script Aborted.")
                    sys.exit()

                if "Error" in result:
                    timeStamp("Remote @Focus2 failed: " + result)
                    return "Fail"

                else:
                    timeStamp("@Focus2 success. Position = " + TSXSendRemote(host,"ccdsoftCamera.focPosition"))
                    time.sleep(5)
                    return "Success"

    if whichCam == "Guider": 
        if method == "Three":
            timeStamp("Focusing remote guiding camera with @Focus3.")

            if (TSXSendRemote(host,"ccdsoftCamera.ImageUseDigitizedSkySurvey") == "1") or \
               (TSXSendRemote(host,"SelectedHardware.focuserModel") == "<No Focuser Selected>"):
                if TSXSendRemote(host,"ccdsoftCamera.ImageUseDigitizedSkySurvey") == "1":
                    timeStamp("@Focus3 success (simulated). Position = " + TSXSendRemote(host,"ccdsoftCamera.focPosition"))
                    return "Success"
                else:
                    timeStamp("No remote focuser detected.")
                    return "Success"

            else:  
                result = TSXSendRemote(host,"ccdsoftAutoguider.AtFocus3(3, true)")

                if "Process aborted." in result:
                    timeStamp("Script Aborted.")
                    sys.exit()

                if "Error" in result:
                    timeStamp("Remote @Focus3 failed: " + result)
                    return "Fail"

                else:
                    timeStamp("@Focus3 success. Position = " + TSXSendRemote(host,"ccdsoftAutoguider.focPosition"))
                    return "Success"


        if method == "Two":
            timeStamp("Focusing remote guiding camera with @Focus2.")

            if (TSXSendRemote(host,"ccdsoftCamera.ImageUseDigitizedSkySurvey") == "1") or \
               (TSXSendRemote(host,"SelectedHardware.focuserModel") == "<No Focuser Selected>"):
                if TSXSendRemote(host,"ccdsoftCamera.ImageUseDigitizedSkySurvey") == "1":
                    timeStamp("@Focus2 success (simulated). Position = " + TSXSendRemote(host,"ccdsoftCamera.focPosition"))
                    return "Success"
                else:
                    timeStamp("No remote focuser detected.")
                    return "Success"

            else:  
                result = TSXSendRemote(host,"ccdsoftAutoguider.AtFocus2()")

                if "Process aborted." in result:
                    timeStamp("Script Aborted.")
                    sys.exit()

                if "Error" in result:
                    timeStamp("Remote @Focus2 failed: " + result)
                    return "Fail"

                else:
                    timeStamp("@Focus2 success. Position = " + TSXSendRemote(host,"ccdsoftAutoguider.focPosition"))
                    return "Success"

    timeStamp("Remote focus completed.")



def calcImageScale(whichCam):
#
# Return the image scale for the supplied camera: Imager or Guider.
#

    if whichCam not in ("Imager", "Guider"):
        print("   ERROR: Please specify camera as either: Imager or Guider.")
        return "Fail"
    else:
     
        FITSProblem = "No"
        tempImage = "No"

        if whichCam == "Imager":
            camDevice = "ccdsoftCamera"
            camImage = "ccdsoftCameraImage"
            camAttachment = "AttachToActiveImager()"
        else:
            camDevice = "ccdsoftAutoguider"
            camImage = "ccdsoftAutoguiderImage"
            camAttachment = "AttachToActiveAutoguider()"
    
        if "206" in str(TSXSend(camImage + "." + camAttachment)):
            writeNote("No current image available.")
            tempImage = "Yes"
            if "Error" in takeImage (whichCam, "1", "0", "0"):
                softPark()

            TSXSend(camImage + "." + camAttachment)
    
        if TSXSend(camDevice + ".ImageUseDigitizedSkySurvey") == "1":
            FITSProblem = "Yes"
        
        else:
            if "250" in str(TSXSend(camImage + '.FITSKeyword("FOCALLEN")')):
                writeNote("FOCALLEN keyword not found in FITS header.")
                FITSProblem = "Yes"
    
            if "250" in str(TSXSend(camImage + '.FITSKeyword("XPIXSZ")')):
                writeNote("XPIXSZ keyword not found in FITS header.")
                FITSProblem = "Yes"
    
        if FITSProblem == "Yes":
            ImageScale = 1.70
    
        else: 
            FocalLength = TSXSend(camImage + '.FITSKeyword("FOCALLEN")')
            PixelSize =  TSXSend(camImage + '.FITSKeyword("XPIXSZ")')
            Binning =  TSXSend(camImage + '.FITSKeyword("XBINNING")')

            # 
            # This "real" stuff is needed because T-Point loves to automagically
            # switch your automated ImageLink settings to 2x2 binning which requires
            # us to divide the reported pixel size by the binning and then rescale
            # according to the selected imaging binning for the camera
            #
            realPixelSize = (float(PixelSize) / float(Binning))
            realBinning = TSXSend(camDevice + '.BinX')

            ImageScale = ((float(realPixelSize) * float(realBinning)) / float(FocalLength) ) * 206.3
            ImageScale = round(float(ImageScale), 2)

        if tempImage == "Yes":
            Path = TSXSend(camImage + ".Path")
            if os.path.exists(Path):
                os.remove(Path)

        writeNote("" + whichCam + " image scale is " + str(ImageScale) + " AS/Pixel.")
        return ImageScale

def calcSettleLimit():
#
# Calculate a reasonable settle threshold based on image scale
#
    timeStamp("Determining guider settle limit.")

    AGImageScale = calcImageScale("Guider")
    ImageScale = calcImageScale("Imager")

    pixelRatio = ImageScale / AGImageScale
    pixelRatio = round(pixelRatio, 2)
    writeNote("Image scale ratio is: " + str(pixelRatio) + ".")

    settleThreshold = round((pixelRatio * 0.95), 2)

    #
    # This was done because my Takahashi mounts track like drunk sailors.
    # At least until I finally rebuilt them myself instead of relying on TNR.
    #
    if TSXSend('ccdsoftCamera.PropStr("m_csObserver")') == "Ken Sturrock":
        if "Temma" in TSXSend("SelectedHardware.mountModel"):
            settleThreshold = 0.8
            writeNote("Settle range modified for Ken's Temmas")

    #
    # I have no confidence that less than 1/5 of a pixel is a realistic expectation.
    # Remember that the settle threshold doesn't affect the guider's performance,
    # it just sets how long the script waits before moving on.
    #
    if settleThreshold < 0.2:
        settleThreshold = 0.2

    writeNote("Calculated settle limit: " + str(settleThreshold) + " guider pixels.")

    return settleThreshold


def camConnect(whichCam):
#
# This function connects the specified camera
#
    if whichCam == "Guider":
        out = TSXSend("ccdsoftAutoguider.Connect()")

    elif whichCam == "Imager":
        TSXSend("ccdsoftCamera.Connect()")

        if str(TSXSend('ccdsoftCamera.PropStr("m_csObserver")')) ==  "Ken Sturrock":
            writeNote("Setting imaging camera to -10.")
            TSXSend("ccdsoftCamera.TemperatureSetPoint = -10")
            TSXSend("ccdsoftCamera.RegulateTemperature = true")
            time.sleep(1)

        out = TSXSend("ccdsoftCamera.Connect()")
    else:
        out = "Unknown Camera: " + whichCam

    if out != "0":
        timeStamp("Unable to connect: " + whichCam)
        return "Fail"
    else:
      return "Success"

def camDisconnect(whichCam):
#
# This function disconnects the specified camera
#
    if whichCam == "Guider":
        out = TSXSend("ccdsoftAutoguider.Disconnect()")
    elif whichCam == "Imager":
        out = TSXSend("ccdsoftCamera.Disconnect()")
    else:
        out = "Unknown Camera: " + whichCam

    if out != "0":
        timeStamp("Unable to disconnect: " + whichCam)
        return "Fail"
    else:
        return "Success"

def camConnectRemote(host, whichCam):
#
# This function connects the specified remote camera
#
    if whichCam == "Guider":
        out = TSXSendRemote(host,"ccdsoftAutoguider.Connect()")

    elif whichCam == "Imager":
        TSXSendRemote(host,"ccdsoftCamera.Connect()")
        if str(TSXSend('ccdsoftCamera.PropStr("m_csObserver")')) ==  "Ken Sturrock":
            TSXSendRemote(host, "ccdsoftCamera.TemperatureSetPoint = -10")
            TSXSendRemote(host, "ccdsoftCamera.RegulateTemperature = true")
            time.sleep(1)
        
        out = TSXSendRemote(host,"ccdsoftCamera.Connect()")
    else:
        out = "Unknown Camera: " + whichCam

    if out != "0":
        timeStamp("Unable to connect: " + whichCam)
        return "Fail"
    else:
        return "Success"

def camDisconnectRemote(host, whichCam):
#
# This function disconnects the specified remote camera
#
    if whichCam == "Guider":
        out = TSXSendRemote(host,"ccdsoftAutoguider.Disconnect()")
    elif whichCam == "Imager":
        out = TSXSendRemote(host,"ccdsoftCamera.Disconnect()")
    else:
        out = "Unknown Camera: " + whichCam

    if out != "0":
        timeStamp("Unable to disconnect: " + whichCam)
        return "Fail"
    else:
        return "Success"

def camState(whichCam):
#
# Returns both the numeric and prose status of the specified camera.
#
# Be aware that the documentation may not match reality. Check the codes
# below as they worked at the time of this module's creation.
#

    if whichCam == "Guider":
        state = TSXSend("ccdsoftAutoguider.State")
    elif whichCam == "Imager":
        state = TSXSend("ccdsoftCamera.State")
    else:
        return "Unknown Camera: " + whichCam


    return state + ", " + {
        "0"  : "Idle",
        "1"  : "Taking a single picture",
        "2"  : "Taking a series of pictures",   # The documentation appears to be wrong 
        "3"  : "Taking a focus picture",
        "4"  : "Moving the guide star",
        "5"  : "Guiding",
        "6"  : "Calibrating the guider",
        "7"  : "Taking a color image",          # How would it know this?
        "8"  : "Performing an autofocus",       # Maybe this was the original @Focus?
        "9"  : "Performing @Focus2",
        "10" : "Undocumented",                  # Not documented.
        "11" : "Taking a series of pictures",   # This is the actual "Take a Series"
        "12" : "Performing @Focus3"             
    }[state]


def cloudWait():
#
# Switch off the sidereal drive and wait five minutes.
# Then, keep checking for stars every five minutes for
# the next 25 minutes. 
#
# This used to use the guide camera but I switched it over
# to the imaging camera for unguided people.
#

    if TSXSend("SelectedHardware.mountModel") !=  "Telescope Mount Simulator":
        timeStamp("Switching off sidereal drive.")
        TSXSend("sky6RASCOMTele.SetTracking(0, 1, 0 ,0)")

    shouldWait = "Yes"
    counter = 1
    
    while shouldWait == "Yes" and counter < 6:
    
        writeNote("Waiting five minutes. (" + str(counter) + " of 5)")
        time.sleep(300)
    
        if TSXSend("SelectedHardware.mountModel") !=  "Telescope Mount Simulator":
            TSXSend("sky6RASCOMTele.SetTracking(1, 1, 0 ,0)")
            time.sleep(10)
    
        timeStamp("Testing sky for clouds.")
    
        takeImage("Imager", "10", "0", "NA")
        TSXSend("ccdsoftCameraImage.AttachToActiveImager()")
        TSXSend("ccdsoftCameraImage.ShowInventory()")
        starsFound = TSXSend("ccdsoftCameraImage.InventoryArray(0).length")

        dirName,fileName = os.path.split(TSXSend("ccdsoftCameraImage.Path"))
            
        orgImgName = os.path.splitext(fileName)[0]

        if os.path.exists(dirName + "/" + orgImgName + ".fit"):
            os.remove(dirName + "/" + orgImgName + ".fit")

        if os.path.exists(dirName + "/" + orgImgName + ".SRC"):
            os.remove(dirName + "/" + orgImgName + ".SRC")
        
        if  int(starsFound) > 10:
            shouldWait = "No"
            timeStamp("Detected " + starsFound + " light sources in test image.")
        else:
            timeStamp("No stars seen. Sky still appears cloudy.")
            counter = counter + 1
            if TSXSend("SelectedHardware.mountModel") !=  "Telescope Mount Simulator":
                TSXSend("sky6RASCOMTele.SetTracking(0, 1, 0 ,0)")
    
    if shouldWait == "Yes":
        print("    ERROR: Halting run. Parking Mount.")
        softPark()
    else:    
        writeNote("Attempting to continue.")
                
        if TSXSend("SelectedHardware.mountModel") !=  "Telescope Mount Simulator":
            TSXSend("sky6RASCOMTele.SetTracking(1, 1, 0 ,0)")
            time.sleep(10)

def CLSlew(target, filterNum):
#
# This uses Closed Loop Slew to precisely center the target.
#
# There is a hack, however, because it uses regular slew to "pre-slew" to the
# target before evoking Closed Loop Slew. This is done because I own a really
# slow mount which might time out with a regular CLS. In practice, it adds no 
# real time penalty, so I do it for all mounts. The 10 second delay is another
# Temma mitigation strategy to make sure that the mount really has stopped
# moving before the image is taken.
#
# Finally, you guessed it, the resynch is important for a poor-pointing mount 
# like my Takahashi Temmas.. 
# 
    slew(target)

    timeStamp("Attempting precise positioning with CLS.")


    if TSXSend("SelectedHardware.filterWheelModel") != "<No Filter Wheel Selected>":
        TSXSend("ccdsoftCamera.filterWheelConnect()")	
        TSXSend("ccdsoftCamera.FilterIndexZeroBased = " + filterNum) 

    if TSXSend("ccdsoftCamera.ImageUseDigitizedSkySurvey") == "1":
        timeStamp("CLS to " + target + " success (simulated).")
        
        return "Success"
    else:    
        camDelay = TSXSend("ccdsoftCamera.Delay")

        TSXSend("ccdsoftCamera.Delay = 10")
        TSXSend("ccdsoftCamera.Subframe = false")

        CLSResults = TSXSend("ClosedLoopSlew.exec()")

        if "failed" in CLSResults:
            if "651" in CLSResults:
                CLSResults = "Not Enough Stars in the Photo. Error = 651"

            print("    ERROR: " + CLSResults)
            timeStamp("CLS to " + target + " failed.")

            TSXSend("ccdsoftCamera.Delay = " + camDelay)

            return "Fail"

        else:
            # 
            # This zooms out the chart to make it prettier
            # after an Image Link.
            #
            TSXSend('sky6StarChart.Find("Z 90")')
            TSXSend('sky6StarChart.Find("' + target + '")')
    
            iScale = TSXSend("ImageLinkResults.imageScale")
            timeStamp("CLS to " + target + " success (" + iScale + " AS/pixel).")
        
            TSXSend("ccdsoftCamera.Delay = " + camDelay)

            if "Temma" in TSXSend("SelectedHardware.mountModel"):
                reSynch()

            return "Success"

def dither():
#
# This function dithers the mount based on image scale and declination
#
# It does not "guide to the destination". You must stop guiding and then 
# restart it after.
#

    timeStamp("Calculating dither distance.")
    imageScale = calcImageScale("Imager")

    if imageScale != "Fail":
        maxMove = (imageScale * 7) 
        ditherXsec = maxMove * random.uniform(0.2,1)
        ditherYsec = maxMove * random.uniform(0.2,1)

        TSXSend("sky6ObjectInformation.Property(55)") 	
        targDec = TSXSend("sky6ObjectInformation.ObjInfoPropOut")
        targRads = abs(float(targDec)) * (3.14159/ 180)
        radsValue = math.cos(targRads)
        decFactor = (1 / radsValue)
        if decFactor > 10:
            decFactor = 10

        ditherYsec = ditherYsec * decFactor

        ditherXMin = ditherXsec * 0.01666666666
        ditherYMin = ditherYsec * 0.01666666666

        NorS = random.choice([True, False])
        if NorS == True:
            NorS = "N"
        else:
            NorS = "S"

        EorW = random.choice([True, False])
        if EorW == True:
            EorW = "E"
        else:
            EorW = "W"

        TSXSend('sky6RASCOMTele.Jog(' + str(ditherXMin) + ', "' + str(NorS) + '")')

        TSXSend('sky6RASCOMTele.Jog(' + str(ditherYMin) + ', "' + str(EorW) + '")')

        #
        # This resets the sidereal rate on my Temma because jogging appears
        # to screw up the tracking speed.
        #
        if "Temma" in TSXSend("SelectedHardware.mountModel"):
            TSXSend("sky6RASCOMTele.SetTracking(1, 1, 0 ,0)")
            writeNote("Resetting Temma tracking rate.")

        timeStamp("Dithered: " + str(round(ditherXsec, 1)) + " AS (" + str(NorS) + "), " + str(round(ditherYsec, 1)) + " AS (" + str(EorW) + ")")

        time.sleep(5)


def findAGStar():
#
# This incredible mess is a straight copy of JS code into a "here document".
#
# If you want to grok what it's doing, check out the "diagnostic" version in
# the original bash/JS script set JS_Codons directory.
#
# This code includes ideas (and code) from Ken Sturrock, Colin McGill and 
# Kym Haines. Although it's probably not recognizable by any of us.
#
# Someday, I may re-write it into Python, but maybe not. Just cover your eyes
# and trust the force.
#

    AGFindResults = TSXSend('''

var CAGI = ccdsoftAutoguiderImage; CAGI.AttachToActiveAutoguider();
CAGI.ShowInventory(); var X = CAGI.InventoryArray(0), Y =
CAGI.InventoryArray(1), Mag = CAGI.InventoryArray(2), FWHM =
CAGI.InventoryArray(4), Elong = CAGI.InventoryArray(8); var disMag =
CAGI.InventoryArray(2), disFWHM = CAGI.InventoryArray(4), disElong =
CAGI.InventoryArray(8); var Width = CAGI.WidthInPixels, Height =
CAGI.HeightInPixels; function median(values) { values.sort( function(a,b)
{return a - b;} ); var half = Math.floor(values.length/2); if(values.length
% 2) { return values[half]; } else { return (values[half-1] + values[half])
/ 2.0; } } function QMagTest(ls) { var Ix = 0, Iy = 0, Isat = 0, Msat =
0.0; for (Ix = Math.max(0,Math.floor(X[ls]-FWHM[ls]*2+.5)); Ix <
Math.min(Width-1,X[ls]+FWHM[ls]*2); Ix++ ) { for (Iy =
Math.max(0,Math.floor(Y[ls]-FWHM[ls]*2+.5)); Iy <
Math.min(Height-1,Y[ls]+FWHM[ls]*2); Iy++ ) { if (ImgVal[Iy][Ix] > Msat)
Msat = ImgVal[Iy][Ix]; if (ImgVal[Iy][Ix] > GuideMax) Isat++; } } if (Isat
> 1) { ADUFail = ADUFail + 1; return false; } else { return true; } } var
FlipY = "No", out = "", Brightest = 0, newX = 0, newY = 0,
counter = X.length, failCount = 0, magLimit = 0, k = 0; var passedLS = 0,
ADUFail = 0, medFWHM = median(disFWHM), medMag = median(disMag), medElong =
median(disElong), baseMag = medMag; var halfTBX =
(ccdsoftAutoguider.TrackBoxX / 2) + 5, halfTBY =
(ccdsoftAutoguider.TrackBoxY / 2) + 5, distX = 0, distY = 0, pixDist = 0;
var ImgVal = new Array(Height), Ix = 0, Iy = 0, GuideBits =
CAGI.FITSKeyword("BITPIX"), GuideCamMax = Math.pow(2,GuideBits)-1, GuideMax
= GuideCamMax * 0.9; for (Ix = 0; Ix < Height; Ix++) { ImgVal[Ix] =
CAGI.scanLine(Ix); } var NcoarseX   = Math.floor(Width/halfTBX+1); var
NcoarseY   = Math.floor(Height/halfTBY+1); var CoarseArray = new
Array(NcoarseX); for (Ix = 0; Ix < NcoarseX; Ix++) { CoarseArray[Ix] = new
Array(NcoarseY); for (Iy = 0; Iy < NcoarseY; Iy++) CoarseArray[Ix][Iy] =
new Array(); } for (ls = 0; ls < counter; ls++) { Ix =
Math.floor(X[ls]/halfTBX); Iy = Math.floor(Y[ls]/halfTBY);
CoarseArray[Ix][Iy].push(ls); } function QNeighbourTest(ls) { var Ix, Iy,
Is, MagLimit = (Mag[ls] + medMag) / 2.5, distX, distY, pixDist, Nstar,
Istar; var Isx = Math.floor(X[ls]/halfTBX); var Isy =
Math.floor(Y[ls]/halfTBY); var Ixmin = Math.max(0,Isx-1); var Ixmax =
Math.min(NcoarseX-1,Isx+1); var Iymin = Math.max(0,Isy-1); var Iymax =
Math.min(NcoarseY-1,Isy+1); for (Ix = Ixmin; Ix < Ixmax; Ix++) { for (Iy =
Iymin; Iy < Iymax; Iy++) { Nstar = CoarseArray[Ix][Iy].length; for (Is = 0;
Is < Nstar; Is++) { Istar = CoarseArray[Ix][Iy][Is]; if (Istar != ls) {
distX = Math.abs(X[ls] - X[Istar]); distX = distX.toFixed(2); distY =
Math.abs(Y[ls] - Y[Istar]); distY = distY.toFixed(2); pixDist =
Math.sqrt((distX * distX) + (distY * distY)); pixDist = pixDist.toFixed(2);
if (  distX > halfTBX ||  distY > halfTBY || Mag[k] > MagLimit) { } else {
return (false); } } } } } return (true); } for (ls = 0; ls < counter; ++ls)
{ if ( Mag[ls] < medMag ) { if (((X[ls] > halfTBX && X[ls] < (Width -
halfTBX))) && (Y[ls] > halfTBY && Y[ls] < (Height - halfTBY))) { if
((Elong[ls] < medElong * 2.5)) { if (FWHM[ls] < (medFWHM * 2.5) &&
(FWHM[ls] > 1)) { if ( QMagTest(ls) ) { if ( QNeighbourTest(ls)) { passedLS
= passedLS + 1; if (Mag[ls] < baseMag) { baseMag = Mag[ls]; Brightest = ls;
} } } } } } } } if ( ccdsoftAutoguider.ImageUseDigitizedSkySurvey == "1" )
{ FlipY = "Yes"; var Binned = CAGI.FITSKeyword ("XBINNING"); if ( Binned >
1 ) { FlipY = "No"; } } if (FlipY == "Yes") { newY = (Height -
Y[Brightest]); } else { newY = Y[Brightest]; } newY = newY.toFixed(2); newX
= X[Brightest].toFixed(2); out = newX + ";" + newY + ";" + CAGI.Path
	''')

    if "TypeError" in AGFindResults:
        timeStamp("Error analyzing guider image for a suitable guide star.")
        return "Error,Error"
    else:
        XCoord,YCoord,Path=AGFindResults.split(";")
        timeStamp("Selected a guide star at: " + XCoord + ", " + YCoord)
        dirName,fileName = os.path.split(Path)
            
        orgImgName = os.path.splitext(fileName)[0]

        if os.path.exists(dirName + "/" + orgImgName + ".SRC"):
            os.remove(dirName + "/" + orgImgName + ".SRC")
     
        if os.path.exists(Path):
            os.remove(Path)

        for scrapFile in glob.glob(dirName + "/" + "*Uncalibrated*.fit"):
            if os.path.exists(scrapFile):
                os.remove(scrapFile) 

        for scrapFile in glob.glob(dirName + "/" + "*NoAutoDark*.fit"):
            if os.path.exists(scrapFile):
                os.remove(scrapFile) 
 
        return XCoord + "," + YCoord


def flipPath(imgPath):
# This is designed to help cope with the single most annoying
# thing that I have to program for: Windows using a different 
# path character, which also happens to be a special character
# symbol on *NIX platforms. 
#
    if not os.path.exists(imgPath):
        print("    ERROR: Path not found.")
        sys.exit()

    imgPath = os.path.abspath(imgPath)

    newPathName = pathlib.Path(imgPath)

    if sys.platform == "win32":
    #
    # Because the path uses back-slashes, we must protect them with an additional
    # back-slash so that Javascript on SkyX doesn't interperate them as special
    # character codes when we feed them over the IP port.
    #
        writeNote("Directory is " + str(newPathName.parent))
        writeNote("File is " + newPathName.name)
        newPathName = str(newPathName).replace("\\", "\\\\")

    else:
        writeNote("Directory is " + str(newPathName.parent))
        writeNote("File is " + newPathName.name)
        newPathName = str(newPathName)

    print("     -----")
    return newPathName


def getActiveImagePath():
#
# Quick procedure to assign the active camera image to ccdsoftCamera (not guider)
# and return the OS-specific path.
#
    TSXSend("ccdsoftCameraImage.AttachToActiveImager()")
    imgPath=TSXSend("ccdsoftCameraImage.Path")

    return imgPath
    
def getStats():
#
# Pull some basic statistics for display from the active image. 
# Uses Image Link, so it's kind of slow - especially on a RPi.
#
# Don't use this for stored images, only for just acquired images
# from the imaging camera. For stored images, use: getStatsPath()
#
# Why do I put up with this crap? I should just take up fucking sewing.
#
# Eh. I've actually tried that and it was even worse....
#
 
    if TSXSend("ccdsoftCamera.ImageUseDigitizedSkySurvey") != "1":
        TSXSend("ccdsoftCameraImage.AttachToActiveImager()")

        TSXSend("ImageLink.pathToFITS = ccdsoftCameraImage.Path")
            
        output = classicIL()

        if "TypeError: " not in output:

            imageScale = TSXSend("ImageLinkResults.imageScale")
            avgPixelValue = TSXSend("ccdsoftCameraImage.averagePixelValue()")
            imageCenterRA = TSXSend("ImageLinkResults.imageCenterRAJ2000")
            imageCenterDec = TSXSend("ImageLinkResults.imageCenterDecJ2000")
            positionAngle = TSXSend("ImageLinkResults.imagePositionAngle")
            ilFWHM = TSXSend("ImageLinkResults.imageFWHMInArcSeconds")
            ASIlFWHM = float(ilFWHM) * float(imageScale)
            TSXSend("sky6Utils.ConvertEquatorialToString(" + imageCenterRA + ", " + imageCenterDec + ", 5)")
            centerHMS2k = TSXSend("sky6Utils.strOut")
            TSXSend("sky6Utils.Precess2000ToNow(" + imageCenterRA + ", " + imageCenterDec + ")")
            centerLSRANow = TSXSend("sky6Utils.dOut0")
            centerLSDecNow = TSXSend("sky6Utils.dOut1")
            TSXSend("sky6Utils.ConvertEquatorialToString(" + centerLSRANow + ", " + centerLSDecNow + ", 5)")	
            centerHMSNow = TSXSend("sky6Utils.strOut")

            eArray = []

            aRaw = TSXSend("ccdsoftCameraImage.InventoryArray(5)")
            aArray = aRaw.split(",")

            bRaw = TSXSend("ccdsoftCameraImage.InventoryArray(6)")
            bArray = bRaw.split(",")

            for index in range(len(aArray)):
            # 
            # Yeah. Yeah. It's not "Pythonic" but then I'd have two formats
            # for dealing with the values instead of just indexes.
            #
            # Thanks to Dmitry Pavlov for inspiring me to try to get the
            # eccentricity code to work:
            #
            #                       http://www.bisque.com/sc/forums/p/36422/195504.aspx#195504
            #
            # There may be some variance in measurement depending on how the light sources are
            # generated (Image Link vs. ShowInventory) and the image. They also may or may 
            # not square with how other programs (like PixInsight) do it.
            #
                upperTerm = float(bArray[index]) *  float(bArray[index])    
                lowerTerm = float(aArray[index]) *  float(aArray[index])

                eccen = math.sqrt(1 - (upperTerm / lowerTerm))
                eArray.append(eccen)

            dirName,fileName = os.path.split(TSXSend("ccdsoftCameraImage.Path"))
            
            orgImgName = os.path.splitext(fileName)[0]

            if os.path.exists(dirName + "/" + orgImgName + ".SRC"):
                os.remove(dirName + "/" + orgImgName + ".SRC")
     
            if os.path.exists(dirName + "/Cropped " + orgImgName + ".fit"):
                os.remove(dirName + "/Cropped " + orgImgName + ".fit")

            if os.path.exists(dirName + "/Cropped " + orgImgName + ".SRC"):
                os.remove(dirName + "/Cropped " + orgImgName + ".SRC")

            print("    STATS:")


            filterKeyword = TSXSend('ccdsoftCameraImage.FITSKeyword("FILTER")')
            if not "Error = 250" or "Undefined" in filterKeyword:
                print("           Filter:               " + filterKeyword)

            print("           Image Scale:          " + str(imageScale) + " AS/Pixel")
            print("           Image FWHM:           " + str(round(ASIlFWHM, 2)) + " AS")
            print("           Mean Eccentricity:    " + str(round(statistics.mean(eArray), 2)))
            print("           Median Eccentricity:  " + str(round(statistics.median(eArray), 2)))
            print("           Average Pixel Value:  " + avgPixelValue.split(".")[0] + " ADU")
            print("           Position Angle:       " + positionAngle.split(".")[0] + " degrees")
            print("           Focuser Position:     " + TSXSend("ccdsoftCamera.focPosition"))
            print("           Temperature:          " + TSXSend("ccdsoftCamera.focTemperature.toFixed(1)")) 
            
            altKeyword = TSXSend('ccdsoftCameraImage.FITSKeyword("CENTALT")')
            if not "Error = 250" or "Undefined" in altKeyword:
                altKeyword = round(float(altKeyword), 2)
                print("           Image Altitude:       " + str(altKeyword))

            azKeyword = TSXSend('ccdsoftCameraImage.FITSKeyword("CENTAZ")')
            if not "Error = 250" or "Undefined" in azKeyword:
                azKeyword = round(float(azKeyword), 2)
                print("           Image Aziumth:        " + str(azKeyword))

            print("           Image Center (J2k):   " + centerHMS2k)
            print("           Image Center (JNow):  " + centerHMSNow)
            
            return "Success"

        else:
            print("    ERROR: Image Link failed.")
            
            return "Fail" 
    else:
        writeNote("DSS images are in use. Skipping statistics.")
        
        return "Success"


def getStatsPath(imgPath):
#
# Pull some basic statistics for display from a path. 
# Uses Image Link, so it's kind of slow - especially on a RPi.
#
# This is pretty much the same as the above, but it works on a 
# path. Might be nice to combine them someday, but who knows
# what that would break (a lot, actually...)
#
    newPathName = flipPath(imgPath)



    TSXSend('ImageLink.pathToFITS = "' + newPathName + '"')

    if TSXSend("ccdsoftCameraImage.Path") != newPathName:

        TSXSend("ccdsoftCameraImage.Close()")

        TSXSend('ccdsoftCameraImage.Path = "' + newPathName + '"')
        output = TSXSend("ccdsoftCameraImage.Open()")

        if "rror" in output:
            print("    ERROR: " + output)
            return "Fail"


    output = classicIL()

    if "TypeError: " not in output:

        imageScale = TSXSend("ImageLinkResults.imageScale")
        imageCenterRA = TSXSend("ImageLinkResults.imageCenterRAJ2000")
        imageCenterDec = TSXSend("ImageLinkResults.imageCenterDecJ2000")
        positionAngle = TSXSend("ImageLinkResults.imagePositionAngle")
        ilFWHM = TSXSend("ImageLinkResults.imageFWHMInArcSeconds")
        ASIlFWHM = float(ilFWHM) * float(imageScale)
        TSXSend("sky6Utils.ConvertEquatorialToString(" + imageCenterRA + ", " + imageCenterDec + ", 5)")
        centerHMS2k = TSXSend("sky6Utils.strOut")
        TSXSend("sky6Utils.Precess2000ToNow(" + imageCenterRA + ", " + imageCenterDec + ")")
        centerLSRANow = TSXSend("sky6Utils.dOut0")
        centerLSDecNow = TSXSend("sky6Utils.dOut1")
        TSXSend("sky6Utils.ConvertEquatorialToString(" + centerLSRANow + ", " + centerLSDecNow + ", 5)")	
        centerHMSNow = TSXSend("sky6Utils.strOut")

        filterKeyword = TSXSend('ccdsoftCameraImage.FITSKeyword("FILTER")')

        if not "Error = 250" or "Undefined" in filterKeyword:
            print("           Filter:               " + filterKeyword)

        print("           Image Scale:          " + str(imageScale) + " AS/Pixel")
        print("           Image FWHM:           " + str(round(ASIlFWHM, 2)) + " AS")
        print("           Position Angle:       " + positionAngle.split(".")[0] + " degrees")
            
        altKeyword = TSXSend('ccdsoftCameraImage.FITSKeyword("CENTALT")')

        if not "Error = 250" or "Undefined" in altKeyword:
            altKeyword = round(float(altKeyword), 2)
            print("           Image Altitude:       " + str(altKeyword))

        azKeyword = TSXSend('ccdsoftCameraImage.FITSKeyword("CENTAZ")')
        if not "Error = 250" or "Undefined" in azKeyword:
            azKeyword = round(float(azKeyword), 2)
            print("           Image Aziumth:        " + str(azKeyword))

        print("           Image Center (J2k):   " + centerHMS2k)
        print("           Image Center (JNow):  " + centerHMSNow)
        print(" ")

        TSXSend("ccdsoftCameraImage.Close()")

        return "Success"

    else:
        print("    ERROR: Image Link failed.")
        print(" ")

        TSXSend("ccdsoftCameraImage.Close()")
        
        return "Fail" 

def getStatsRemote(host, whichCam):
#
# Pull some basic statistics for display from the remote computer's imaging (not guiding) camera.
# Uses Image Link, so it's kind of slow - especially on a RPi.
#
# Because we are only controlling the remote machine via SkyX,
# we can't clean up the SRC scratch files.
#
# This is yet another variation of the above. Meant for the "second camera" option that
# absolutely nobody uses.
#
    if whichCam not in ("Imager", "Guider"):
        print("   ERROR: Please specify remote camera as either: Imager or Guider.")

    if whichCam == "Imager":

        if TSXSendRemote(host,"ccdsoftCamera.ImageUseDigitizedSkySurvey") != "1":
    
            print("    STATS:")
    
            TSXSendRemote(host,"ccdsoftCameraImage.AttachToActiveImager()")
    
            TSXSendRemote(host,"ImageLink.pathToFITS = ccdsoftCameraImage.Path")
            if "TypeError: " not in TSXSendRemote(host,"ImageLink.execute()"):
    
                imageScale = TSXSendRemote(host,"ImageLinkResults.imageScale")
                avgPixelValue = TSXSendRemote(host,"ccdsoftCameraImage.averagePixelValue()")
                imageCenterRA = TSXSendRemote(host,"ImageLinkResults.imageCenterRAJ2000")
                imageCenterDec = TSXSendRemote(host,"ImageLinkResults.imageCenterDecJ2000")
                positionAngle = TSXSendRemote(host,"ImageLinkResults.imagePositionAngle")
                ilFWHM = TSXSendRemote(host,"ImageLinkResults.imageFWHMInArcSeconds")
                ASIlFWHM = float(ilFWHM) * float(imageScale)
                TSXSendRemote(host,"sky6Utils.ConvertEquatorialToString(" + imageCenterRA + ", " + imageCenterDec + ", 5)")
                centerHMS2k = TSXSendRemote(host,"sky6Utils.strOut")
                TSXSendRemote(host,"sky6Utils.Precess2000ToNow(" + imageCenterRA + ", " + imageCenterDec + ")")
                centerLSRANow = TSXSendRemote(host,"sky6Utils.dOut0")
                centerLSDecNow = TSXSendRemote(host,"sky6Utils.dOut1")
                TSXSendRemote(host,"sky6Utils.ConvertEquatorialToString(" + centerLSRANow + ", " + centerLSDecNow + ", 5)")	
                centerHMSNow = TSXSendRemote(host,"sky6Utils.strOut")

                filterKeyword = TSXSendRemote(host,'ccdsoftCameraImage.FITSKeyword("FILTER")')
                if not "Error = 250" or "Undefined" in filterKeyword:
                    print("           Filter:               " + filterKeyword)

                print("           Image Scale:          " + str(imageScale) + " AS/Pixel")
                print("           Image FWHM:           " + str(round(ASIlFWHM, 2)) + " AS")
                print("           Average Pixel Value:  " + avgPixelValue.split(".")[0] + " ADU")
                print("           Position Angle:       " + positionAngle.split(".")[0] + " degrees")
                print("           Focuser Position:     " + TSXSendRemote(host,"ccdsoftCamera.focPosition"))
                print("           Temperature:          " + TSXSendRemote(host,"ccdsoftCamera.focTemperature.toFixed(1)")) 
                
                altKeyword = TSXSendRemote(host,'ccdsoftCameraImage.FITSKeyword("CENTALT")')
                if not "TypeError" or "Undefined" in altKeyword:
                    altKeyword = round(float(altKeyword), 2)
                    print("           Image Altitude:       " + str(altKeyword))
    
    
                azKeyword = TSXSendRemote(host,'ccdsoftCameraImage.FITSKeyword("CENTAZ")')
                if not "TypeError" or "Undefined" in azKeyword:
                    azKeyword = round(float(azKeyword), 2)
                    print("           Image Aziumth:        " + str(azKeyword))
    
                print("           Image Center (J2k):   " + centerHMS2k)
                print("           Image Center (JNow):  " + centerHMSNow)
    
                writeNote("Unable to cleanup light source (SRC) scratch files on")
                print("           remote machine: " + host)
                
                return "Success"

            else:
                print("    ERROR: Image Link failed.")
            
                return "Fail" 
        else:
            writeNote("DSS images are in use. Skipping statistics.")
        
            return "Success"

    if whichCam == "Guider":
        writeNote("Statstics for the remote guider not yet implemented.")


def getTemp():
#
# Pulls the temperature - used for deciding when to refocus
#
# It just pulls the teperature from the default temperature source
# which can be set within SkyX.
#
    focTemp = TSXSend("ccdsoftCamera.focTemperature.toFixed(1)")
    return float(focTemp)


def hardPark():
#
# Point the mount towards the correct pole, disconnect cameras. If 
# you have a Paramount, it will then try to park the mount. If you
# have something else, or the park fails then it will just turn off
# the tracking motor.
#
# Set some camera defaults for next time. Exit
#

    timeStamp("Ending imaging run.")

    stopGuiding()

    TSXSend("sky6StarChart.DocumentProperty(0)")
    latitude = TSXSend("sky6StarChart.DocPropOut")
    
    if float(latitude) < 0:
        writeNote("Pointing mount to the south.")
        slew("HIP112405")
    else:
        writeNote("Pointing mount to the north.")
        slew("kochab")

    if "Paramount" in TSXSend("SelectedHardware.mountModel"):
        if not "Error" in TSXSend("sky6RASCOMTele.ParkAndDoNotDisconnect()"):
            timeStamp("Paramount moved to park position.")
        else:
            timeStamp("No park position set. Stopping sidereal motor.")
            TSXSend("sky6RASCOMTele.SetTracking(0, 1, 0 ,0)")
    else:
        if TSXSend("SelectedHardware.mountModel") !=  "Telescope Mount Simulator":
            writeNote("Turning off sidereal drive.")
            TSXSend("sky6RASCOMTele.SetTracking(0, 1, 0 ,0)")

    timeStamp("Resetting camera defaults.")

    TSXSend("ccdsoftCamera.ExposureTime = 5")			
    TSXSend("ccdsoftCamera.AutoSaveOn = true")
    TSXSend("ccdsoftCamera.Frame = 1")
    TSXSend("ccdsoftCamera.Delay = 0")
    TSXSend("ccdsoftCamera.Subframe = false")

    TSXSend("ccdsoftAutoguider.ExposureTime = 5")
    TSXSend("ccdsoftAutoguider.AutoguiderExposureTime = 5")
    TSXSend("ccdsoftAutoguider.AutoSaveOn = false")
    TSXSend("ccdsoftAutoguider.Frame = 1")
    TSXSend("ccdsoftAutoguider.Delay = 0")
    TSXSend("ccdsoftAutoguider.Subframe = false")

    if str(TSXSend('ccdsoftCamera.PropStr("m_csObserver")')) ==  "Ken Sturrock":
        if str(TSXSend("SelectedHardware.cameraModel")) == "QSI Camera  ":
            TSXSend("ccdsoftCamera.ImageReduction = 1")
            TSXSend("ccdsoftCamera.TemperatureSetPoint = 1")
            TSXSend("ccdsoftCamera.FilterIndexZeroBased = 0")
            TSXSend("ccdsoftCamera.ExposureTime = 10")

        if str(TSXSend("SelectedHardware.cameraModel")) == "Camera Simulator":
            TSXSend("ccdsoftCamera.FilterIndexZeroBased = 0")

    camDisconnect("Imager")
    camDisconnect("Guider")

    timeStamp("System Parked.")

    sys.exit()


def isDayLight():
#
# Is the sun above 15 degrees? If so, it's light outside.
#

    if TSXSend("ccdsoftCamera.ImageUseDigitizedSkySurvey") != "1":
        TSXSend("sky6ObjectInformation.Property(0)")
        target = TSXSend("sky6ObjectInformation.ObjInfoPropOut")

        if targAlt("Sun") > -15 and targHA("Sun") < 0:
            timeStamp("Good morning.")
            hardPark()

        while targAlt("Sun") > -15 and targHA("Sun") > 0:
            timeStamp("The sky is not yet dark.")
            timeStamp("Waiting five minutes.")
            time.sleep (300)

        TSXSend('sky6StarChart.Find("' + target + '")')


def isGuiderLost(limit):
#
# Report back if the guider appears to be lost
#
    if TSXSend("ccdsoftCamera.ImageUseDigitizedSkySurvey") != "1":
        errorX = TSXSend('ccdsoftAutoguider.GuideErrorX')
        errorY = TSXSend('ccdsoftAutoguider.GuideErrorY')

        errorX = round(float(errorX), 2)
        errorY = round(float(errorY), 2)

        if abs(round(float(errorX), 2)) < (limit * 3) and abs(errorY) < (limit * 3):
            return "No"

        else:
            return "Yes"
    else:
            return "No"

def linReg(arrayX, arrayY):
#
# This does a quick & dirty linear regression.
#
# Inputs must be numbers, not strings.
#
# Yeah. Yeah. I know. NumPy could have done it for me with a bazillion multi-megabyte
# dependencies. What would I have learned, though?
#
# Modified from code by Trent Richardson at the URL:
#
#           http://trentrichardson.com/2010/04/06/compute-linear-regressions-in-javascript/
#
#
    print("----------")
    timeStamp("Calculating linear least squares regression.")
    print("      ----")

    sum_x = 0
    sum_y = 0
    sum_xy = 0
    sum_xx = 0
    sum_yy = 0
    slope = 0
    intercept = 0
    r2 = 0
    n = len(arrayX)

    for counter,Xvalue in enumerate(arrayX):
        Yvalue = arrayY[counter]
        sum_x = sum_x + Xvalue;
        sum_y = sum_y + arrayY[counter];
        sum_xy = sum_xy + (Xvalue * Yvalue)
        sum_xx = sum_xx + (Xvalue * Xvalue)
        sum_yy = sum_yy + (Yvalue * Yvalue)

    slope = (n * sum_xy - sum_x * sum_y) / (n * sum_xx - sum_x * sum_x)

    intercept = (sum_y - slope * sum_x) / n

    term1 = (n * sum_xy - sum_x * sum_y)
    term2 = (n * sum_xx - sum_x * sum_x)
    term3 = (n * sum_yy - sum_y*sum_y)
    term4 = term2 * term3
    term4 = abs(term4)
    term5 = math.sqrt(term4)

    r2 = math.pow((term1 / term5),2)
  
    print("           Intercept = " + str(intercept))
    print("           Slope = " + str(slope))
    print("           r2 = " + str(r2))

    print("      ----")
    timeStamp("Finished.")
    return str(intercept) + ", " + str(slope) + ", " + str(r2)

def nameFilters(where):
#
# A routine to try to list the filters in the wheel.
#
# It does it by counting up until you get back to zero (the overflow value). 
#
# I used this approach because I didn't know about the ccdsoftCamera.lNumberFilters 
# routine. This routine is still pretty fast.
#
# It then pulls the filter names and returns them in an array.
#
# The simulator has 125 filters, which is a bit much for my testing purposes,
# so I report back eight.
#

    if where == "Local":
        writeNote("Checking filters on local camera")

        allFilNames = []

        if TSXSend("SelectedHardware.filterWheelModel") == "<No Filter Wheel Selected>":
            writeNote("No filter wheel chosen.")
            return "None"

        else:
            TSXSend("ccdsoftCamera.filterWheelConnect()")	
            origFilterNum = TSXSend("ccdsoftCamera.FilterIndexZeroBased")
            counter = 0
            TSXSend("ccdsoftCamera.FilterIndexZeroBased =" + str(counter))
            currentFilterNum = TSXSend("ccdsoftCamera.FilterIndexZeroBased")

            while int(currentFilterNum) == counter:
                filName = TSXSend("ccdsoftCamera.szFilterName(" + currentFilterNum + ")")
                allFilNames.append(filName)
                counter = counter + 1
                TSXSend("ccdsoftCamera.FilterIndexZeroBased =" + str(counter))
                currentFilterNum = TSXSend("ccdsoftCamera.FilterIndexZeroBased")

            if TSXSend("SelectedHardware.filterWheelModel") == "Filter Wheel Simulator":
                writeNote("Simulated filter wheel detected.")
                print("           Reporting first eight filters instead of all 125.")
                allFilNames = allFilNames[0:8]
        
            else:
                timeStamp("Found " + str(counter) + " filter slots in the wheel.")
                TSXSend("ccdsoftCamera.FilterIndexZeroBased =" + str(origFilterNum))

    else:
        IP,Port = where.split(":")
        writeNote("Checking filters on camera located at " + IP + " on port: " + Port + ".")

        allFilNames = []

        if TSXSendRemote(where,"SelectedHardware.filterWheelModel") == "<No Filter Wheel Selected>":
            writeNote("No filter wheel chosen.")
            return "None"

        else:
            TSXSendRemote(where,"ccdsoftCamera.filterWheelConnect()")	
            origFilterNum = TSXSendRemote(where,"ccdsoftCamera.FilterIndexZeroBased")
            counter = 0
            TSXSendRemote(where,"ccdsoftCamera.FilterIndexZeroBased =" + str(counter))
            currentFilterNum = TSXSendRemote(where,"ccdsoftCamera.FilterIndexZeroBased")

            while int(currentFilterNum) == counter:
                filName = TSXSendRemote(where,"ccdsoftCamera.szFilterName(" + currentFilterNum + ")")
                allFilNames.append(filName)
                counter = counter + 1
                TSXSendRemote(where,"ccdsoftCamera.FilterIndexZeroBased =" + str(counter))
                currentFilterNum = TSXSendRemote(where,"ccdsoftCamera.FilterIndexZeroBased")

            if TSXSendRemote(where,"SelectedHardware.filterWheelModel") == "Filter Wheel Simulator":
                writeNote("Simulated filter wheel detected.")
                print("           Reporting first eight filters instead of all 125.")
                allFilNames = allFilNames[0:8]
        
            else:
                timeStamp("Found " + str(counter) + " filter slots in the wheel.")
                TSXSendRemote(where,"ccdsoftCamera.FilterIndexZeroBased =" + str(origFilterNum))

    return allFilNames
        
        
def preRun():
#
# This function checks a few settings that need to be in place before run_target is
# run. It uses the "mysterious" variables found in the Imaging Profile INI file.
# 
# Some of the settings are used by the code to calculate values, other things are
# more good practice items or are done to facilitate file handling.
#
# I know that some people don't mind continuous error messages when they run
# programs, but it bugs me. It also bugs to see error messages from code that I've
# written memorialized on YouTube because the user didnt read the instructions.
#
    print ("     NOTE: Checking configuration settings.")

    result = "Success"
    
    if TSXSend('ccdsoftCamera.PropStr("m_csObserver")') == "":
        print("    ERROR: Please fill in observer name in camera settings")
        result = "Fail"

    if TSXSend('ccdsoftCamera.PropDbl("m_dTeleFocalLength")') == "0":
        print("    ERROR: Please fill in telescope focal length in camera settings")
        result = "Fail"

    if TSXSend('ccdsoftAutoguider.PropDbl("m_dTeleFocalLength")') == "0":
        print("    ERROR: Please fill in telescope focal length in guider settings")
        result = "Fail"

    if " " in TSXSend('ccdsoftCamera.PropStr("m_csAutoSavePath")'):
        print("    ERROR: Please remove any spaces in the autosave path under the camera settings")
        result = "Fail"

    if " " in TSXSend('ccdsoftAutoguider.PropStr("m_csAutoSavePath")'):
        print("    ERROR: Please remove any spaces in the autosave path under the guider settings")
        result = "Fail"

    if " " in TSXSend('ccdsoftCamera.PropStr("m_csAutoSaveColonaDateFormat")'):
        print("    ERROR: Please remove any spaces in the date format under the camera settings")
        result = "Fail"

    if " " in TSXSend('ccdsoftAutoguider.PropStr("m_csAutoSaveColonaDateFormat")'):
        print("    ERROR: Please remove any spaces in the date format under the guider settings")
        result = "Fail"

    if TSXSend("SelectedHardware.cameraModel") != "Camera Simulator":
        if TSXSend("ccdsoftCamera.ImageUseDigitizedSkySurvey") == "1":
            print("    ERROR: Non-simulated camera set to use DSS images.")
            result = "Fail"

    if TSXSend("SelectedHardware.autoguiderCameraModel") != "<No Camera Selected>":
        if TSXSend("SelectedHardware.autoguiderCameraModel") != "Camera Simulator":
            if TSXSend("ccdsoftAutoguider.ImageUseDigitizedSkySurvey") == "1":
                print("    ERROR: Non-simulated guider set to use DSS images.")
                result = "Fail"

    TSXSend('ccdsoftCamera.setPropLng("m_bAutoSaveNoWhiteSpace", 1)')
    TSXSend('ccdsoftAutoguider.setPropLng("m_bAutoSaveNoWhiteSpace", 1)')
    TSXSend('ccdsoftAutoguider.setPropLng("m_bShowAutoguider", 1)')

    return result

def remoteImageDone(host, whichCam):
#
# This checks to see if the remote image is complete.
#
# If the remote image is not done, then wait until it is
# finished.
#

    if whichCam not in ("Imager", "Guider"):
        print("   ERROR: Please specify camera as either: Imager or Guider.")
        print("          ASSuming imaging camera.")
        whichCam = "Imager"

    if whichCam == "Imager":
        timeStamp("Checking remote imaging camera status.")

        camStatus = TSXSendRemote(host,"ccdsoftCamera.Status")
        while camStatus != "Ready":
            writeNote("Status: "+ camStatus)
            writeNote("Waiting.")
            time.sleep(10)
            camStatus = TSXSendRemote(host,"ccdsoftCamera.Status")

    if whichCam == "Guider":
        timeStamp("Checking remote guiding camera status.")

        camStatus = TSXSendRemote(host,"ccdsoftAutoguider.Status")
        while camStatus != "Ready":
            writeNote("Status: "+ camStatus)
            writeNote("Waiting.")
            time.sleep(10)
            camStatus = TSXSendRemote(host,"ccdsoftAutoguider.Status")

    timeStamp("Remote " + whichCam + " is finished.")
    

def reSynch():
#
# Resynchronizes the mount position on the skychart
#
# This can be helpful with poor pointing mounts using no pointing model,
# such as my Takahashi.
# 
# You generally don't want to call it if you're using T_Point.
#
    TSXSend("sky6ObjectInformation.Property(0)")
    targetName =  TSXSend("sky6ObjectInformation.ObjInfoPropOut") 

    TSXSend("sky6ObjectInformation.Property(54)")
    targetRA =  TSXSend("sky6ObjectInformation.ObjInfoPropOut")

    TSXSend("sky6ObjectInformation.Property(55)")		
    targetDec = TSXSend("sky6ObjectInformation.ObjInfoPropOut") 

    TSXSend("sky6RASCOMTele.Sync(" + targetRA + ", " + targetDec + ", " + targetName + " )")

    writeNote("Mount resynched.")


def settleGuider(limit):
#
# Now, we're going to wait for the guider to settle 
# 
# The wait is up to thirty counts. The length of the count will depend
# on your guider settings. It's arbitrary.
#
    if TSXSend("ccdsoftCamera.ImageUseDigitizedSkySurvey") == "0":
        goodCount = 0
        totalCount = 0
        settled = "No"

        pausePeriod = float(TSXSend("ccdsoftAutoguider.AutoguiderExposureTime")) + float(TSXSend("ccdsoftAutoguider.Delay")) + 1.0

        timeStamp("Guider settle limit set to " + str(limit) + " guider pixels.")

        while settled == "No":

            if TSXSend("ccdsoftAutoguider.State") != "5":
                writeNote("Guider has stopped guiding.")

            time.sleep(pausePeriod)

            errorX = TSXSend('ccdsoftAutoguider.GuideErrorX')
            errorY = TSXSend('ccdsoftAutoguider.GuideErrorY')

            errorX = round(float(errorX), 2)
            errorY = round(float(errorY), 2)

            if abs(errorX) > limit or abs(errorY) > limit:
                goodCount = 0
                totalCount = totalCount + 1

                if totalCount >= 30:
                    settled = "Yes"

                timeStamp("Guider off target. (" + str(errorX) + ", " + str(errorY) + ") " + "(" + str(totalCount) + " of 30)")

            else:
                goodCount = goodCount + 1
                totalCount = totalCount + 1

                timeStamp("Guider ON target. (" + str(errorX) + ", " + str(errorY) + ") " + "(" + str(goodCount) + " of 5)")

            if goodCount >= 5 or totalCount >= 30:
                settled = "Yes"

        if totalCount >= 30:
            if abs(errorX) < (limit * 4) and abs(errorY) < (limit * 4):
                writeNote("Guider not settled but does not appear to be lost.")
                timeStamp("Continuing.")
                return "Settled"

            else:
                timeStamp("Guider appears lost.")
                return "Lost"

        else:
            timeStamp("Continuing.")
            return "Settled"
    else:
        writeNote("Using DSS images. Skipping settle.")
        timeStamp("Continuing.")
        return "Settled"


def slew(target):
# 
# Performs a normal slew to the specificed target.
#
# If the mount hasn't succesfully reached its target in twenty minutes, we 
# will assume that it's stalled, jammed, collided or crashed. Even my EM-11
# in "slow mode" can do a complete flip in twelve minutes.
#
    slewCount = 0

    if "ReferenceError" in str(TSXSend('sky6StarChart.Find("' + target + '")')):
        timeStamp("Target not found.")
        return "Error"

    timeStamp("Slew to " + target + " starting.")

    if TSXSend("sky6RASCOMTele.IsParked()") == "true":
        writeNote("Unparking mount.")
        TSXSend("sky6RASCOMTele.Unpark()")

    if TSXSend("SelectedHardware.mountModel") !=  "Telescope Mount Simulator":
        TSXSend("sky6RASCOMTele.SetTracking(1, 1, 0 ,0)")

    TSXSend("sky6ObjectInformation.Property(54)")
    targetRA =  TSXSend("sky6ObjectInformation.ObjInfoPropOut")

    TSXSend("sky6ObjectInformation.Property(55)")		
    targetDEC = TSXSend("sky6ObjectInformation.ObjInfoPropOut") 

    TSXSend("sky6RASCOMTele.Asynchronous = true")

    TSXSend('sky6StarChart.Find("' + target + '")')
   
    TSXSend("sky6ObjectInformation.Property(0)")
    chartName = TSXSend("sky6ObjectInformation.ObjInfoPropOut")

    TSXSend('sky6RASCOMTele.SlewToRaDec(' +targetRA + ', ' + targetDEC + ', "' + chartName + '")')
    time.sleep(0.5)
    
    while TSXSend("sky6RASCOMTele.IsSlewComplete") == "0":
        if slewCount > 119:
            print("    ERROR: Mount appears stuck!")
            timeStamp("Sending abort command.")
            sky6RASCOMTele.Abort()
            if TSXSend("SelectedHardware.mountModel") !=  "Telescope Mount Simulator":
                time.sleep(5)
                timeStamp("Trying to stop sidereal motor.")
                TSXSend("sky6RASCOMTele.SetTracking(0, 1, 0 ,0)")
            timeStamp("Stopping script.")    
            sys.exit()
        else:
            writeNote("Slew in progress.")
            slewCount = slewCount + 1
            time.sleep(10)

    if "Process aborted." in TSXSend("sky6RASCOMTele.IsSlewComplete"):
        timeStamp("Script Aborted.")
        sys.exit()

    TSXSend("sky6RASCOMTele.Asynchronous = false")
    timeStamp("Arrived at " + target)

    TSXSend("sky6RASCOMTele.GetAzAlt()")
    mntAz = round(float(TSXSend("sky6RASCOMTele.dAz")), 2)
    mntAlt = round(float(TSXSend("sky6RASCOMTele.dAlt")), 2) 

    writeNote("Mount currently at: " + str(mntAz)  + " az., " + str(mntAlt) + " alt.")

    

def slewRemote(host, target):
# 
# Performs a normal slew to the specificed target on a remote machine.
#
# The main idea for this routine is to synchronize the simulated mount on a remote
# machine (running real cameras) so that the autosave file labeling correctly identifies the target.
#
# It's all part of the ridiculous dual camera option that nobody uses.
#
# Of course, it could be used to run real hardware if you had the need to organize a ballet of mounts.
#
    if "ReferenceError" in str(TSXSendRemote(host,'sky6StarChart.Find("' + target + '")')):
        timeStamp("Target not found.")
        return "Error"

    timeStamp("Remote slew to " + target + " on " + host + " (port: " + str(TSXPort) + ") starting.")

    if TSXSendRemote(host,"sky6RASCOMTele.IsParked()") == "true":
        writeNote("Unparking remote mount.")
        TSXSendRemote(host,"sky6RASCOMTele.Unpark()")

    if TSXSendRemote(host,"SelectedHardware.mountModel") !=  "Telescope Mount Simulator":
        TSXSendRemote(host,"sky6RASCOMTele.SetTracking(1, 1, 0 ,0)")

    TSXSendRemote(host,"sky6ObjectInformation.Property(54)")
    targetRA =  TSXSendRemote(host,"sky6ObjectInformation.ObjInfoPropOut")

    TSXSendRemote(host,"sky6ObjectInformation.Property(55)")		
    targetDEC = TSXSendRemote(host,"sky6ObjectInformation.ObjInfoPropOut") 

    TSXSendRemote(host,"sky6RASCOMTele.Asynchronous = true")

    TSXSendRemote(host,'sky6RASCOMTele.SlewToRaDec(' +targetRA + ', ' + targetDEC + ', "' + target + '")')
    time.sleep(0.5)
    
    while TSXSendRemote(host,"sky6RASCOMTele.IsSlewComplete") == "0":
        writeNote("Remote slew in progress.")
        time.sleep(10)

    if "Process aborted." in TSXSendRemote(host,"sky6RASCOMTele.IsSlewComplete"):
        timeStamp("Script Aborted.")
        sys.exit()

    TSXSendRemote(host,"sky6RASCOMTele.Asynchronous = false")
    timeStamp("Remote mount arrived at " + target)

    TSXSendRemote(host,"sky6RASCOMTele.GetAzAlt()")
    mntAz = round(float(TSXSendRemote(host,"sky6RASCOMTele.dAz")), 2)
    mntAlt = round(float(TSXSendRemote(host,"sky6RASCOMTele.dAlt")), 2) 

    writeNote("Remote mount currently at: " + str(mntAz)  + " az., " + str(mntAlt) + " alt.")


def softPark():
#
# This is designed to pause the mount and let the user abort the program to
# fix something. If there is no user, it will go ahead and park the mount 
# after 30 seconds.
#
    if TSXSend("SelectedHardware.mountModel") !=  "Telescope Mount Simulator":
        timeStamp("Pausing sidereal motor.")
        TSXSend("sky6RASCOMTele.SetTracking(0, 1, 0 ,0)")

    print(" ")
    writeNote("Please press Control-C to abort the script and intervene.")
    print(" ")
    writeNote("Otherwise, the system will park in 30 seconds.")
    print(" ")

    time.sleep(30)

    if TSXSend("SelectedHardware.mountModel") !=  "Telescope Mount Simulator":
        TSXSend("sky6RASCOMTele.SetTracking(1, 1, 0 ,0)")

    hardPark()


def startGuiding(exposure, delay, XCoord, YCoord):
#
# Fire up guiding with the guiding camera at the supplied coordinates.
#
    # You have to unscale for binning because SkyX will rescale it. 
    newXCoord = float(TSXSend('ccdsoftAutoguider.BinX')) * float(XCoord)  
    newYCoord = float(TSXSend('ccdsoftAutoguider.BinY')) * float(YCoord)

    TSXSend("ccdsoftAutoguider.GuideStarX = " + str(newXCoord))
    TSXSend("ccdsoftAutoguider.GuideStarY = " + str(newYCoord))
    
    TSXSend("ccdsoftAutoguider.AutoSaveOn = false")
    TSXSend("ccdsoftAutoguider.Subframe = false")
    TSXSend("ccdsoftAutoguider.Frame = 1")
    TSXSend("ccdsoftAutoguider.Asynchronous = true")

    TSXSend("ccdsoftAutoguider.AutoguiderExposureTime = " + str(exposure))
    TSXSend("ccdsoftAutoguider.Delay = " + str(delay))

    TSXSend("ccdsoftAutoguider.Autoguide()")

    while TSXSend("ccdsoftAutoguider.State") != "5":
        time.sleep(0.5)

    timeStamp("Autoguiding started.")


def stopGuiding():
#
# This routine clobbers autoguiding.
#
# It has some extra cruft to wait for DSS downloads to complete, which
# throws an error if interrupted, and makes sure that the guiding has
# actually stopped before moving on.
#
    while TSXSend("ccdsoftAutoguider.ExposureStatus") == "DSS From Web":
        time.sleep(0.25)

    TSXSend("ccdsoftAutoguider.Abort()")

    while TSXSend("ccdsoftAutoguider.State") != "0":
        time.sleep(0.5)

    TSXSend("ccdsoftAutoguider.Subframe = false")
    TSXSend("ccdsoftAutoguider.Asynchronous = false")


def takeImageOld(whichCam, exposure, delay, filterNum):
#
# This function takes an image
# 
# Parameters: Guider or Imager, exposure in seconds, delay in seconds (or NA = leave it alone), which filter number.
#
    if whichCam not in ("Imager", "Guider"):
        print("   ERROR: Please specify camera as either: Imager or Guider.")

    if whichCam == "Imager":
        if TSXSend("SelectedHardware.filterWheelModel") != "<No Filter Wheel Selected>":
            TSXSend("ccdsoftCamera.filterWheelConnect()")	
            if filterNum != "NA":
                TSXSend("ccdsoftCamera.FilterIndexZeroBased = " + filterNum)    
                timeStamp("Imager: " + str(exposure) + "s exposure through " \
                + TSXSend("ccdsoftCamera.szFilterName(" + filterNum + ")") + " filter.")
        else:
            timeStamp("Imager: " + str(exposure) + "s exposure")
    else:
        timeStamp("Guider: " + str(exposure) + "s exposure")

    if whichCam == "Imager":    
        TSXSend("ccdsoftCamera.Asynchronous = false")
        TSXSend("ccdsoftCamera.AutoSaveOn = true")
        TSXSend("ccdsoftCamera.ImageReduction = 0")
        TSXSend("ccdsoftCamera.Frame = 1")
        TSXSend("ccdsoftCamera.Subframe = false")
        TSXSend("ccdsoftCamera.ExposureTime = " + exposure)
        if delay != "NA":
            TSXSend("ccdsoftCamera.Delay = " + delay)

        camMesg = TSXSend("ccdsoftCamera.TakeImage()") 

        if camMesg == "0":

            TSXSend("ccdsoftCameraImage.AttachToActiveImager()")
            cameraImagePath =  TSXSend("ccdsoftCameraImage.Path").split("/")[-1] 
            
            if cameraImagePath == "":
                cameraImagePath = "Image not saved"

            timeStamp("Image completed: " + cameraImagePath)
            return "Success"

        else:
            if "Process aborted." in camMesg:
                timeStamp("Script Aborted.")
                stopGuiding()
                sys.exit()

            timeStamp("Error: " + camMesg)
            return "Fail"

    if whichCam == "Guider": 
        TSXSend("ccdsoftAutoguider.Asynchronous = false")
        TSXSend("ccdsoftAutoguider.AutoSaveOn = true")
        TSXSend("ccdsoftAutoguider.Frame = 1")
        TSXSend("ccdsoftAutoguider.Subframe = false")
        TSXSend("ccdsoftAutoguider.ExposureTime = " + exposure)
        if delay != "NA":
            TSXSend("ccdsoftCamera.Delay = " + delay)
  
        camMesg = TSXSend("ccdsoftAutoguider.TakeImage()")

        if camMesg  == "0":
            TSXSend("ccdsoftAutoguiderImage.AttachToActiveAutoguider()")

            guiderImagePath =  TSXSend("ccdsoftAutoguiderImage.Path").split("/")[-1] 
            
            if guiderImagePath == "":
                guiderImagePath = "Image not saved."

            timeStamp("Guider Image completed: " + guiderImagePath)
            return "Success"

        else:
            if "Process aborted." in camMesg:
                timeStamp("Script Aborted.")
                stopGuiding()
                sys.exit()

            timeStamp("Error: " + camMesg)
            return "Fail"

def takeImage(whichCam, exposure, delay, filterNum):
#
# This function takes an image
#
# It was modified from the original to take the image asynchronously. This shouldn't matter to the end user because
# it behaves the same way, except now it no longer holds the TCP socket open during the entire image so that an
# external monitoring routine can slip in a command if needed.
# 
# Parameters: Guider or Imager, exposure in seconds, delay in seconds (or NA = leave it alone), which filter number.
#
    if whichCam not in ("Imager", "Guider"):
        print("   ERROR: Please specify camera as either: Imager or Guider.")

    if whichCam == "Imager":
        if TSXSend("SelectedHardware.filterWheelModel") != "<No Filter Wheel Selected>":
            TSXSend("ccdsoftCamera.filterWheelConnect()")	
            if filterNum != "NA":
                TSXSend("ccdsoftCamera.FilterIndexZeroBased = " + filterNum)    
                timeStamp("Imager: " + str(exposure) + "s exposure through " \
                + TSXSend("ccdsoftCamera.szFilterName(" + filterNum + ")") + " filter.")
        else:
            timeStamp("Imager: " + str(exposure) + "s exposure")
    else:
        timeStamp("Guider: " + str(exposure) + "s exposure")

    if whichCam == "Imager":    
        TSXSend("ccdsoftCamera.Asynchronous = true")
        TSXSend("ccdsoftCamera.AutoSaveOn = true")
        TSXSend("ccdsoftCamera.ImageReduction = 0")
        TSXSend("ccdsoftCamera.Frame = 1")
        TSXSend("ccdsoftCamera.Subframe = false")
        TSXSend("ccdsoftCamera.ExposureTime = " + exposure)
        if delay != "NA":
            TSXSend("ccdsoftCamera.Delay = " + delay)

        TSXSend("ccdsoftCamera.TakeImage()") 
        
        camMesg = TSXSend("ccdsoftCamera.IsExposureComplete")

        while camMesg == "0":
            time.sleep(5)
            camMesg = TSXSend("ccdsoftCamera.IsExposureComplete")

        TSXSend("ccdsoftCamera.Asynchronous = false")

        if camMesg == "1":
            TSXSend("ccdsoftCameraImage.AttachToActiveImager()")
            cameraImagePath =  TSXSend("ccdsoftCameraImage.Path").split("/")[-1] 
            
            if cameraImagePath == "":
                cameraImagePath = "Image not saved"

            timeStamp("Image completed: " + cameraImagePath)
            return "Success"

        else:
            if "Process aborted." in camMesg:
                timeStamp("Script Aborted.")
                stopGuiding()
                sys.exit()

            timeStamp("Error: " + camMesg)
            return "Fail"

    if whichCam == "Guider": 
        TSXSend("ccdsoftAutoguider.Asynchronous = true")
        TSXSend("ccdsoftAutoguider.AutoSaveOn = true")
        TSXSend("ccdsoftAutoguider.Frame = 1")
        TSXSend("ccdsoftAutoguider.Subframe = false")
        TSXSend("ccdsoftAutoguider.ExposureTime = " + exposure)
        if delay != "NA":
            TSXSend("ccdsoftCamera.Delay = " + delay)
  
        TSXSend("ccdsoftAutoguider.TakeImage()")

        camMesg = TSXSend("ccdsoftAutoguider.IsExposureComplete")

        while camMesg == "0":
            time.sleep(5)
            camMesg = TSXSend("ccdsoftAutoguider.IsExposureComplete")

        TSXSend("ccdsoftAutoguider.Asynchronous = false")

        if camMesg == "1":
            TSXSend("ccdsoftAutoguiderImage.AttachToActiveAutoguider()")
            agImagePath =  TSXSend("ccdsoftAutoguiderImage.Path").split("/")[-1] 
            
            if agImagePath == "":
                agImagePath = "Image not saved"

            timeStamp("Image completed: " + agImagePath)
            return "Success"

        else:
            if "Process aborted." in camMesg:
                timeStamp("Script Aborted.")
                sys.exit()

            timeStamp("Error: " + camMesg)
            return "Fail"


def takeImageRemote(host, whichCam, exposure, delay, filterNum):
#
# This function takes an image on a remote machine in ASYNC mode.
# 
# Parameters: Host, Guider or Imager, exposure in seconds, delay in seconds (or NA = leave it alone), which filter number.
#
# It runs in async so that you can come back to the main machine & camera and do something while the second camera is shooting
# in the background. This means that you should use the remoteImageDone routine to see if the remote image is finished.
#
    if whichCam not in ("Imager", "Guider"):
        print("   ERROR: Please specify remote camera as either: Imager or Guider.")

    if whichCam == "Imager":
        if TSXSendRemote(host,"SelectedHardware.filterWheelModel") != "<No Filter Wheel Selected>":
            TSXSendRemote(host,"ccdsoftCamera.filterWheelConnect()")	
            if filterNum != "NA":
                TSXSendRemote(host,"ccdsoftCamera.FilterIndexZeroBased = " + filterNum)    
            timeStamp("Remote Imager: " + str(exposure) + "s exposure through " \
            + TSXSendRemote(host,"ccdsoftCamera.szFilterName(" + filterNum + ")") + " filter.")
        else:
            timeStamp("Remote Imager: " + str(exposure) + "s exposure")
    else:
        timeStamp("Remote Guider: " + str(exposure) + "s exposure")

    if whichCam == "Imager":    
        TSXSendRemote(host,"ccdsoftCamera.Asynchronous = true")
        TSXSendRemote(host,"ccdsoftCamera.AutoSaveOn = true")
        TSXSendRemote(host,"ccdsoftCamera.ImageReduction = 0")
        TSXSendRemote(host,"ccdsoftCamera.Frame = 1")
        TSXSendRemote(host,"ccdsoftCamera.Subframe = false")
        TSXSendRemote(host,"ccdsoftCamera.ExposureTime = " + exposure)
        if delay != "NA":
            TSXSendRemote(host,"ccdsoftCamera.Delay = " + delay)

        TSXSendRemote(host,"ccdsoftCamera.TakeImage()") 

    if whichCam == "Guider": 
        TSXSendRemote(host,"ccdsoftAutoguider.Asynchronous = true")
        TSXSendRemote(host,"ccdsoftAutoguider.AutoSaveOn = true")
        TSXSendRemote(host,"ccdsoftAutoguider.Frame = 1")
        TSXSendRemote(host,"ccdsoftAutoguider.Subframe = false")
        TSXSendRemote(host,"ccdsoftAutoguider.ExposureTime = " + exposure)
        if delay != "NA":
            TSXSendRemote(host,"ccdsoftCamera.Delay = " + delay)
  
        TSXSendRemote(host,"ccdsoftAutoguider.TakeImage()")

    timeStamp("Remote command issued asynchronously.")


def targAlt(target):
#
# Report the altitude of the target.
#
# Useful for determining when to start & stop imaging.
#

    if "ReferenceError" in str(TSXSend('sky6StarChart.Find("' + target + '")')):
        timeStamp("Target not found.")
        return "Error"
    
    TSXSend("sky6ObjectInformation.Property(59)")
    currentAlt = TSXSend("sky6ObjectInformation.ObjInfoPropOut")

    return float(currentAlt)

def targAz(target):
#
# Report the azimuth of the target.
#

    if "ReferenceError" in str(TSXSend('sky6StarChart.Find("' + target + '")')):
        timeStamp("Target not found.")
        return "Error"
    
    TSXSend("sky6ObjectInformation.Property(58)")
    currentAz = TSXSend("sky6ObjectInformation.ObjInfoPropOut")

    return float(currentAz)

def targExists(target):
#
# Target can be found by SkyX?
#
    if "not found" in str(TSXSend('sky6StarChart.Find("' + target + '")')):
        timeStamp("Target " + target + " not found.")
        return "No"
    else:
        return "Yes"


def targFromImage(imgPath):
#
# Extracts a plausable target name from the FITS header of the 
# currently attached CAMERA image.
#
# It uses the OBJECT keyword. If you pointed to the target
# with RA/Dec, then don't use this routine.
#
    imgPath = flipPath(imgPath)
    
    if not os.path.exists(imgPath):
        print("    ERROR: Cannot find image file: " + imgPath)
        return "Fail"
    else:

        if TSXSend("ccdsoftCameraImage.Path") != imgPath:

            TSXSend("ccdsoftCameraImage.Close()")

            writeNote("Specified image not attached.")
            writeNote("Opening file.")
            TSXSend('ccdsoftCameraImage.Path = "' + imgPath + '"')
            output = TSXSend("ccdsoftCameraImage.Open()")

            if "rror" in output:
                print("    ERROR: " + output)
                return "Fail"

            targ = TSXSend('ccdsoftCameraImage.FITSKeyword("OBJECT")')
            targ =  " ".join(targ.split())
            writeNote("Guessing target with OBJECT keyword.")
            writeNote("Target may be: " + targ)

            TSXSend("ccdsoftCameraImage.Close()")
        else:
            targ = TSXSend('ccdsoftCameraImage.FITSKeyword("OBJECT")')
            writeNote("Guessing target with OBJECT keyword.")
            writeNote("Target may be: " + targ)

    return targ


def targHA(target):
#
# Report back the Hour Angle of the target.
#
# Useful for figuring out meridian flips and @F2 "buffering" to avoid crossing the 
# meridian and flipping for a focus star.
#
# Can also be used to determine west (positive value) or east (negative value).
#
    if "ReferenceError" in str(TSXSend('sky6StarChart.Find("' + target + '")')):
        timeStamp("Target not found.")
        return "Error"
    
    TSXSend("sky6ObjectInformation.Property(70)")
    currentHA = TSXSend("sky6ObjectInformation.ObjInfoPropOut")

    return float(currentHA)

def targRiseSetTimes(target, desiredAltitude):
#
# Based on a conversation here: http://www.bisque.com/sc/forums/p/35048/185331.aspx
#
# If you want to try to understand what it does, look at my better commented Javascript
# version of this code which is posted to that thread.
#

    timeStamp("Finding the times that " + target + " will rise and set past " + desiredAltitude + " degrees.")


    TSXSend("sky6StarChart.Find('" + target + "')")

    desiredAltitude = float(desiredAltitude)

    desiredAltitudeRads = (desiredAltitude * (3.14159265359 / 180))

    TSXSend("sky6ObjectInformation.Property(68)")
    transitTime = float(TSXSend("sky6ObjectInformation.ObjInfoPropOut"))

    TSXSend("sky6StarChart.DocumentProperty(0)")
    ourLatitude = float(TSXSend("sky6StarChart.DocPropOut"))
    ourLatitudeRads = (ourLatitude * (3.14159265359 / 180));


    TSXSend("sky6ObjectInformation.Property(55)")
    objDecNow = float(TSXSend("sky6ObjectInformation.ObjInfoPropOut"))
    objDecNowRads = (objDecNow * (3.14159265359 / 180));



    TSXSend("sky6ObjectInformation.Property(59)")
    currentAltitude = float(TSXSend("sky6ObjectInformation.ObjInfoPropOut"))
    writeNote("Current object altitude: " + str(round(currentAltitude,2)) + " degrees.")


    TSXSend("sky6ObjectInformation.Property(70)")
    objHA = float(TSXSend("sky6ObjectInformation.ObjInfoPropOut"))
    objHADeg = objHA * 15.041067;
    objHARad = (objHADeg * (3.14159265359 / 180));

    maxAltitude = (90 - ourLatitude + objDecNow);

    if (maxAltitude > 90):
    # This can happen, so we have to make it fit the convention.
        maxAltitude = 180 - maxAltitude;

    writeNote("Maximum object altitude: " + str(round(maxAltitude,2)) + " degrees.")

    minAltitude = (abs(ourLatitude) - (90 - abs(objDecNow)))

    if ((desiredAltitude > maxAltitude) or (desiredAltitude < minAltitude)):
        print("    ERROR: Desired altitude is higher than object's maximum(" + str(round(maxAltitude,2)) + ")")
        print("           or lower than its minimum (" +  str(round(minAltitude,2)) + ") altitude.")

        return("Invalid Altitude")

    else:
        upperTerm = math.sin(desiredAltitudeRads) - (math.sin(ourLatitudeRads) * math.sin(objDecNowRads))
        lowerTerm = math.cos(ourLatitudeRads) * math.cos(objDecNowRads)
        crossingHACos = (upperTerm / lowerTerm)
        crossingHARads = math.acos(crossingHACos)

        crossingHADeg = crossingHARads * (180 / 3.14159265359)
        crossingHA = crossingHADeg / 15


        if (objHA < 0):
            crossingHA = crossingHA * -1
            writeNote(target + " is currently rising. HA: " + str(round(objHA,6)))
        else:
            writeNote(target + " is currently setting. HA: " + str(round(objHA,6)))


        risingCrossTime = transitTime - abs(crossingHA)


        if (risingCrossTime > 24):
            risingCrossTime = risingCrossTime - 24

        if (risingCrossTime < 0):
            risingCrossTime = risingCrossTime + 24


        hours, minutes = str(risingCrossTime).split(".")             

        if (len(hours) < 2):
            hours = "0" + hours
	
        minutes =  float("0." + minutes)
        minutes = minutes * 60;
        minutes = math.floor(minutes);
        minutes = str(minutes)

        if (len(minutes) < 2):
            minutes = "0" + minutes

        prettyRiseTime = hours + ":" + minutes

        writeNote("It crosses " + str(desiredAltitude) + " degrees on the way up about " + str(prettyRiseTime) + ".")

        hours, minutes = str(transitTime).split(".")             

        if (len(hours) < 2):
            hours = "0" + hours
	
        minutes =  float("0." + minutes)
        minutes = minutes * 60;
        minutes = math.floor(minutes);
        minutes = str(minutes)

        if (len(minutes) < 2):
            minutes = "0" + minutes

        prettyTransitTime = hours + ":" + minutes

        writeNote("It transits the meridian about " + str(prettyTransitTime) + ".")

        settingCrossTime = transitTime + abs(crossingHA)

        if (settingCrossTime > 24):
            settingCrossTime = settingCrossTime - 24

        if (settingCrossTime < 0):
            settingCrossTime = settingCrossTime + 24

        hours, minutes = str(settingCrossTime).split(".")             

        if (len(hours) < 2):
            hours = "0" + hours
	
        minutes =  float("0." + minutes)
        minutes = minutes * 60;
        minutes = math.floor(minutes);
        minutes = str(minutes)

        if (len(minutes) < 2):
            minutes = "0" + minutes

        prettySetTime = hours + ":" + minutes

        writeNote("It crosses " + str(desiredAltitude) + " degrees on the way down about " + str(prettySetTime) + ".")

        hours, minutes = str(transitTime).split(".")             

        if (len(hours) < 2):
            hours = "0" + hours
	
        minutes =  float("0." + minutes)
        minutes = minutes * 60;
        minutes = math.floor(minutes);
        minutes = str(minutes)

        if (len(minutes) < 2):
            minutes = "0" + minutes

        prettyTransitTime = hours + ":" + minutes

        return(prettyRiseTime + " -> " + prettyTransitTime + " -> " + prettySetTime)


def tcpChk():
#
# The script was recently modified to require the "TCP responses close socket" option to be set.
# because there is no way to test that over the socket, we're fishing around in the ini file
# to check for that option as well as the TCP listener.
#
# In case the user has moved their ASF, the script will simply post a warning to check the
# parameters - and if they aren't set, it'll be the last thing that the user sees because the script 
# will lock.
#
    homeDir = os.path.expanduser("~")    

    if (sys.platform == "win32") or (sys.platform == "win64"):
        appSettingsFile = homeDir + "\Documents\Software Bisque\TheSkyX Professional Edition"
        appSettingsFile = appSettingsFile + "\AppSettings.ini"

    if sys.platform == "darwin":
        appSettingsFile = homeDir + "/Library/Application Support/Software Bisque"
        appSettingsFile = appSettingsFile + "/TheSkyX Professional Edition/AppSettings.ini"

    if sys.platform == "linux":

        #
        # This fiasco is required because I occasionally run the system on both native Windows
        # and WSL. Unfortunately, determining the native Windows path from within WSL is a
        # big, fat, pain in the ass. So, I'm going to print a warning and call it good.
        #
        import platform
        moreSystemDetail = platform.release()
        if "Microsoft" in moreSystemDetail:
            writeNote("May be running on the Linux Subsystem for Windows (WSL)")
            print('          * Ensure that "TCP Responses close socket" is set to "True"')
            print('          * Ensure that "TCP Server" is set to "Listen".')
            print('          * The Graphical User Interface option is not available under WSL.')
            return

        else:
            appSettingsFile = homeDir + "/Library/Application Support/Software Bisque"
            appSettingsFile = appSettingsFile + "/TheSkyX Professional Edition/AppSettings.ini"

    socketResponse = "False"
    tcpListen = "False"
    
    if os.path.exists(appSettingsFile):
    
        with open(appSettingsFile) as search:
            for eachLine in search:
                eachLine = eachLine.rstrip() 
                if eachLine == "APP_bTCPResponsesCloseSocket=true":
                    socketResponse = "True"
                if eachLine == "APP_bSetTCPServerToListenOnStart=true":
                    tcpListen = "True"
   
        if tcpListen == "False":
            print('    ERROR: Please activate the TCP Server.')  

        if socketResponse == "False":
            print('    ERROR: Set "TCP Responses close socket" to "True".')
   
        if (socketResponse == "False") or ( tcpListen == "False"):
            sys.exit()

    else:
        writeNote("Unable to find the SkyX Application Support Folder.")
        print('     NOTE: Ensure that "TCP Responses close socket" is set to "True"')
        print('     NOTE: Ensure that "TCP Server" is set to "Listen".')


def themeChk():
#
# Try to find out if we're running the traditional silver/grey color or the newer Darth Vader look.
#
    homeDir = os.path.expanduser("~")    

    if (sys.platform == "win32") or (sys.platform == "win64"):
        appSettingsFile = homeDir + "\Documents\Software Bisque\TheSkyX Professional Edition"
        appSettingsFile = appSettingsFile + "\AppSettings.ini"

    if sys.platform == "darwin":
        appSettingsFile = homeDir + "/Library/Application Support/Software Bisque"
        appSettingsFile = appSettingsFile + "/TheSkyX Professional Edition/AppSettings.ini"

    if sys.platform == "linux":
        import platform
        moreSystemDetail = platform.release()
        if "Microsoft" not in moreSystemDetail:
            appSettingsFile = homeDir + "/Library/Application Support/Software Bisque"
            appSettingsFile = appSettingsFile + "/TheSkyX Professional Edition/AppSettings.ini"

   
    themeColor = "Dark"
    
    if os.path.exists(appSettingsFile): 
        with open(appSettingsFile) as search:
            for eachLine in search:
                eachLine = eachLine.rstrip() 
                if eachLine == "APP_bUseDarkTheme=false":
                    themeColor = "Traditional"
   
    return themeColor




def timeStamp(message):
#
# This function provides a standard time-stamped output statement
#
	timeStamp = time.strftime("[%H:%M:%S]")
	print(timeStamp, message)


def TSXSend(message):
#
# This function routes generic commands to TSX Pro through a TCP/IP port
#
# The code was originally written by Anat Ruangrassamee but was modified for Python 3
# and further cruded up by Ken Sturrock to make it more vebose and slower.
#
# Also incudes code suggested by John Zelle and Charlie Figura. This suggestion should improve
# socket reliability and allows huge amounts of information (like arrays/lists to be brought back
# from SkyX into Python. This change, however, now *requires* that "TCP Response Closes Socket" 
# be set to "True" under Preferences -> Advanced.
#
# Set the verbose flag up top to see the messages back & forth to SkyX for debugging 
# purposes.
#
    TSXSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        TSXSocket.connect((TSXHost, TSXPort))
    except ConnectionRefusedError:
        print("   ERROR: Unable to establish a connection.")
        print("       Is SkyX running? Is the TCP Server Listening?")
        sys.exit()

    fullMessage =  "/* Java Script */" + CR + "/* Socket Start Packet */" + CR + CR         \
    + message + ";"                                                                         \
    + CR + CR + "/* Socket End Packet */"

    TSXSocket.sendall(fullMessage.encode())

    pseudoFile = TSXSocket.makefile()
    data = pseudoFile.read()
 
    TSXSocket.close()

    if verbose: 
    #
    # This is for the debugging option
    #
        print()
        print("---------------------------")
        print("Content of TSX Java Script:")
        print("---------------------------")
        print()
        print(fullMessage)
        print()
        print("--------------------------")
        print("Content of Return Message:")
        print("--------------------------")
        print()
        print(data)
        print()
        print("--------------------------")
        print()

    try:
        retOutput,retError = data.split("|")
    except ValueError:
    #
    # Yeah. It can happen.
    #
        print("    ERROR: No response. Looks like SkyX crashed.")
        sys.exit()

    if "No error." not in retError:
        return retError

    return retOutput


def TSXSendRemote(host, message):
#
# This version sends the message to a remote host & port
#
# See the comments above.
#
    if not ":" in host:    
        print("    ERROR: Remote port not set.")
        print("           Please use XXX.XXX.XXX.XXX:YYYY format for IP address and port.")
        sys.exit()

    TSXHost,TSXPort = host.split(":")
    TSXPort = int(TSXPort)

    TSXSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        TSXSocket.connect((TSXHost, TSXPort))
    except ConnectionRefusedError:
        print("   ERROR: Unable to establish a connection.")
        print("       Is SkyX running? Is the TCP Server Listening?")
        sys.exit()

    fullMessage =  "/* Java Script */" + CR + "/* Socket Start Packet */" + CR + CR         \
    + message + ";"                                                                         \
    + CR + CR + "/* Socket End Packet */"

    TSXSocket.sendall(fullMessage.encode())

    pseudoFile = TSXSocket.makefile()
    data = pseudoFile.read()
    
    TSXSocket.close()

    if verbose:  
        print()
        print("---------------------------")
        print("Content of TSX Java Script:")
        print("---------------------------")
        print()
        print(fullMessage)
        print()
        print("--------------------------")
        print("Content of Return Message:")
        print("--------------------------")
        print()
        print(data)
        print()
        print("--------------------------")
        print()

    retOutput,retError = data.split("|")

    if "No error." not in retError:
        return retError

    return retOutput

def writeNote(text):
#
# I finally added this complement to timeStamp
#
    text = str(text)
    print("     NOTE: " + text)


######################################################################
# Below is a new set of functions for shooting calibration frames    #
######################################################################


def takeDark(exposure, numFrames):
#
# Specify exposure duration & qualtity. 
# If exposure is zero, take a bias.
#
    timeStamp("Taking dark frames.")
    if exposure == "0":
        writeNote("Setting frame type to bias.")
        TSXSend("ccdsoftCamera.Frame = 2")
    else:
        writeNote("Setting frame type to dark.")
        TSXSend("ccdsoftCamera.Frame = 3")
        writeNote("Setting exposure to " + exposure + " seconds.")
        TSXSend("ccdsoftCamera.ExposureTime = " + exposure)

    counter = 1
    while (counter <= int(numFrames)):
        timeStamp("Taking frame: " + str(counter) + " of " + numFrames + ".")
        TSXSend("ccdsoftCamera.TakeImage()")
        counter = counter + 1

    timeStamp("Finished.")


def takeFlat(filterNum, startingExposure, numFlats, takeDarks):
#
# This function takes a an appropriately exposed flat.
#
# filterNum is the filter number used for the flat frame. 
# if there is no filter wheel or filterNum is set to "NA"
# then it won't worry about it.
#
# numFlats is how many flats frames you want to take
# takeDarks is "Darks" or something else. If set to "Darks"
# the routine will take matching dark frames. This is great
# if you have a real shutter but will require you to intervene
# if you do not.
#
    def shootTest(testExposure):
        TSXSend("ccdsoftCamera.Asynchronous = false")
        TSXSend("ccdsoftCamera.AutoSaveOn = true")
        TSXSend("ccdsoftCamera.ImageReduction = 0")
        TSXSend("ccdsoftCamera.Frame = 4")
        TSXSend("ccdsoftCamera.Delay = 1")
        TSXSend("ccdsoftCamera.Subframe = false")
        TSXSend("ccdsoftCamera.ExposureTime = " + str(testExposure))

        timeStamp("Taking test image.")
        TSXSend("ccdsoftCamera.TakeImage()")

    def analyzeImage():
        writeNote("Analyzing test image.")
        TSXSend("ccdsoftCameraImage.AttachToActiveImager()")

        imageDepth = int(TSXSend('ccdsoftCameraImage.FITSKeyword("BITPIX")'))

        if TSXSend("ccdsoftCamera.ImageUseDigitizedSkySurvey") == "1":
            avgPixelValue = round(random.uniform(5000, 50000), 0)
            writeNote("DSS images in use. Random ADU value assigned: " + str(avgPixelValue))
        else:
            avgPixelValue = float(TSXSend("ccdsoftCameraImage.averagePixelValue()"))

        avgPixelValue = int(round(avgPixelValue, 0))
        fullWell = int(math.pow (2, imageDepth))
        brightness = avgPixelValue / fullWell

        units = brightness / float(exposure)
        goalExposure = 0.50 / units
        imgPath=TSXSend("ccdsoftCameraImage.Path")
        if os.path.exists(imgPath):
            writeNote("Removing test image.")
            os.remove(imgPath)

        brightness = str(round(brightness, 2))
        avgPixelValue = str(avgPixelValue)
        units = str(round(units,2))
        goalExposure = str(round(goalExposure,2))
    
        writeNote("Camera exposure was set to: " + str(exposure) + " second(s).")
    
        writeNote("Image Average Brightness is " + brightness + " of FWC (" + avgPixelValue + " ADU).")
    
        writeNote("Brightness-per-second is " + units + " of FWC.")

        return brightness + "," + goalExposure

    # Start main routine 

    timeStamp("Taking flat frames.")
    print("     PLAN: " + numFlats + " flat frame(s).")

    exposure = startingExposure

    if TSXSend("SelectedHardware.filterWheelModel") != "<No Filter Wheel Selected>":
        TSXSend("ccdsoftCamera.filterWheelConnect()")	
        if filterNum != "NA":
            writeNote("Switching to " + TSXSend("ccdsoftCamera.szFilterName(" + filterNum + ")") + " filter.")
            TSXSend("ccdsoftCamera.FilterIndexZeroBased = " + filterNum) 
            time.sleep(0.5)
        else:
            writeNote("No filter specified. Leaving alone.")
    else:
        timeStamp("Imager: No filter used.")

    shootTest(exposure) 
    brightness,goalExposure = analyzeImage().split(",")

    while (float(brightness) > 0.85) or (float(brightness) < 0.15):
        if float(brightness) > 0.85:
            print("    ERROR: Sensor saturated. Reducing exposure.")
            exposure = exposure / 2
        
        if float(brightness) < 0.15:
            print("    ERROR: Signal dim. Increasing exposure.")
            exposure = exposure * 2
        
        shootTest(exposure)
        brightness,goalExposure = analyzeImage().split(",")

    writeNote("Setting exposure to "+ goalExposure + " second(s) to try to reach 40% of FWC.") 

    TSXSend("ccdsoftCamera.ExposureTime = " + str(goalExposure))

    numFlats = int(numFlats)

    counter = 1
    while (counter <= numFlats):
        timeStamp("Taking flat image: " + str(counter) + " of " + str(numFlats) + ".")
        TSXSend("ccdsoftCamera.TakeImage()")
        counter = counter + 1

    if takeDarks == "Darks" or takeDarks == "darks":
        TSXSend("ccdsoftCamera.Frame = 3")

        counter = 1
        while (counter <= numFlats):
            timeStamp("Taking matched dark image: " + str(counter) + " of " + str(numFlats) + ".")
            TSXSend("ccdsoftCamera.TakeImage()")
            counter = counter + 1
    else:
        writeNote("No automatic darks requested.")

    timeStamp("Finished.")
    return str(goalExposure)


##################################################################
# Below is a set of functions for dealing with star measurements #
##################################################################

def circularAverage(type, PAs):
#
# Calculate the average of the angles in the PAs list.
#
# "type" is either median or mean.
#
# Taken from an example here:
#       https://en.wikipedia.org/wiki/Mean_of_circular_quantities
#

    sValue = []
    cValue = []

    coefficient = len(PAs)

    for angle in PAs:
        cValue.append(math.cos(math.radians(angle)))
        sValue.append(math.sin(math.radians(angle)))
    
    if type == "median":
        avgCValue = statistics.median(cValue)
        avgSValue = statistics.median(sValue)
    else:
        avgCValue = statistics.mean(cValue)
        avgSValue = statistics.mean(sValue)


    atValue = math.atan(avgSValue / avgCValue)
    atValue = round(math.degrees(atValue), 2)

    if ((avgSValue < 0) and (avgCValue > 0)):
        atValue = atValue + 360

    if (avgCValue < 0):
        atValue = atValue + 180

    return atValue


def classicIL():
#
# This is a routine to facilitate the use of Classic Image Link. It tries to guess the image scale
# based on the FITS header and, if it has issues, sets a bogus one but also sets the unknown image
# scale flag.
#
# The reason for this routine is so that I can more safely use traditional image link when processing
# pictures for astrometry (not really for telescope pointing). Traditional is faster than blind and
# (at this time) allows me to use Gaia stars for more accurate measurements.
#

    timeStamp("Attempting Image Link.")

    FITSProblem = "No"

    if "undefined" in str(TSXSend('ccdsoftCameraImage.FITSKeyword("FOCALLEN")')):
        print("    ERROR: Bogus File")
        return "Fail"

    if TSXSend("ccdsoftCameraImage.ImageUseDigitizedSkySurvey") == "1":
        FITSProblem = "Yes"
        
    else:
        if "250" in str(TSXSend('ccdsoftCameraImage.FITSKeyword("FOCALLEN")')):
            writeNote("FOCALLEN keyword not found in FITS header.")
            FITSProblem = "Yes"
    
        if "250" in str(TSXSend('ccdsoftCameraImage.FITSKeyword("XPIXSZ")')):
            writeNote("XPIXSZ keyword not found in FITS header.")
            FITSProblem = "Yes"
    
    if FITSProblem == "Yes":
        writeNote("Setting image scale to unknown.")
        ImageScale = 1.70                                               # This is the default IS used by DSS and some value must be entered...
        TSXSend("ImageLink.unknownScale = 1")

    else: 
        FocalLength = TSXSend('ccdsoftCameraImage.FITSKeyword("FOCALLEN")')
        PixelSize =  TSXSend('ccdsoftCameraImage.FITSKeyword("XPIXSZ")')
        Binning =  TSXSend('ccdsoftCameraImage.FITSKeyword("XBINNING")')

        ImageScale = ((float(PixelSize) * float(Binning)) / float(FocalLength) ) * 206.3
        ImageScale = round(float(ImageScale), 2)
        print("     -----")
        writeNote("Guessed image scale:  " + str(ImageScale))
        print("     -----")

    TSXSend("ImageLink.scale = " + str(ImageScale))

    ilResults = TSXSend("ImageLink.execute()")

    # get the determined IS and use it in place of our earlier guess.
    newIS = TSXSend("ImageLinkResults.imageScale")

    TSXSend("ImageLink.scale = " + str(newIS))

    # Now that we, hopefully, know the image link, we'll turn off the unknown IS option for anything
    # downstream. Much of the current code, will ignore this and re-guess it for later.  
    TSXSend("ImageLink.unknownScale = 0")

    TSXSend("ccdsoftCameraImage.ScaleInArcsecondsPerPixel = " + str(newIS))         # insertWCS uses a different set of variables
                                                                                    # which is critical to set for transforming
                                                                                    # X,Y -> RA,Dec


    # Just push the results because the calling routine will determine if the Image Link failed and will, hopefully,
    # do or say something intelligent.
    return ilResults


def dsCatStats():
#
# Looks up catalog statistics for double stars.
#
# returns the PA & Separation (if available).
#
    print("----------")
    timeStamp("Retrieving catalog information")
    print("    ------")

    catalog = ""
    wds = "X"
    comp = ""
    angle = ""
    sep = "NA"
    lastYear = ""

    TSXSend("sky6ObjectInformation.Property(12)")		
    objType = TSXSend("sky6ObjectInformation.ObjInfoPropOut")	

    if (objType != "Double Star"):
        writeNote("Not a double star.")
        return "Fail"

    else:
        TSXSend("sky6ObjectInformation.Property(19)")			
        catalog = TSXSend("sky6ObjectInformation.ObjInfoPropOut")

        TSXSend("sky6ObjectInformation.Property(0)")		
        name = TSXSend("sky6ObjectInformation.ObjInfoPropOut")

        #
        # If you are not using the WDS-2018 or WDS-2019 catalog, it will try
        # to switch because the measures are newer and it has separations.
        #

        if "WDS" and "2019" not in catalog:
                if "WDS" and "2018" not in catalog:
                    name2019 = name.replace("WDS", "WDS-2019")
                    result = TSXSend('sky6StarChart.Find("' + name2019 + '")')
    
                    if ("rror" in result) or ("not found" in result):
                        writeNote("No corresponding WDS-2019 entry found.")
                        TSXSend('sky6StarChart.Find("' + name + '")')
                    else:
                        name = name2019
                        writeNote("Switching to WDS-2019 catalog: " + name)
                        TSXSend("sky6ObjectInformation.Property(19)")			
                        catalog = TSXSend("sky6ObjectInformation.ObjInfoPropOut")

               
        #
        # There are separate sections for the different catalogs.
        # Feel free to add more logic for other catalogs.
        #
        if ("WDS" and "2019" in catalog):           
            TSXSend("sky6ObjectInformation.Property(30)")		
            wds = TSXSend("sky6ObjectInformation.ObjInfoPropOut")
            wds = wds.split()[0]

            TSXSend("sky6ObjectInformation.Property(20)")		
            comp = TSXSend("sky6ObjectInformation.ObjInfoPropOut")
            comp =  " ".join(comp.split())

            TSXSend("sky6ObjectInformation.Property(21)")		
            lastYear = TSXSend("sky6ObjectInformation.ObjInfoPropOut")
            lastYear =  " ".join(lastYear.split())
            lastYear = lastYear.split()[1]
            
            TSXSend("sky6ObjectInformation.Property(24)")			
            angle = TSXSend("sky6ObjectInformation.ObjInfoPropOut")	
            angle = angle.strip()

            TSXSend("sky6ObjectInformation.Property(26)")			
            sep = TSXSend("sky6ObjectInformation.ObjInfoPropOut")	
            sep = sep.strip()


        elif ("WDS" and "2018" in catalog):
            TSXSend("sky6ObjectInformation.Property(20)")		
            wds = TSXSend("sky6ObjectInformation.ObjInfoPropOut")

            TSXSend("sky6ObjectInformation.Property(22)")		
            comp = TSXSend("sky6ObjectInformation.ObjInfoPropOut")
            comp =  " ".join(comp.split())
            
            TSXSend("sky6ObjectInformation.Property(25)")			
            angle = TSXSend("sky6ObjectInformation.ObjInfoPropOut")	
            angle = angle.strip()

            TSXSend("sky6ObjectInformation.Property(28)")			
            sep = TSXSend("sky6ObjectInformation.ObjInfoPropOut")	
            sep = sep.strip()

        elif "Struve" in catalog:
            TSXSend("sky6ObjectInformation.Property(24)")		
            comp = TSXSend("sky6ObjectInformation.ObjInfoPropOut")

            TSXSend("sky6ObjectInformation.Property(25)")			
            angle = TSXSend("sky6ObjectInformation.ObjInfoPropOut")	
            angle = angle.strip()

            TSXSend("sky6ObjectInformation.Property(27)")		
            sep = TSXSend("sky6ObjectInformation.ObjInfoPropOut")
            sep = sep.strip()

        else:
            TSXSend("sky6ObjectInformation.Property(21)")		
            comp = TSXSend("sky6ObjectInformation.ObjInfoPropOut")

            TSXSend("sky6ObjectInformation.Property(25)")		
            angle = TSXSend("sky6ObjectInformation.ObjInfoPropOut")	
            angle = angle.strip()

        print("    STATS:")
        print("           Catalog:    " + catalog)
        if wds:
            print("           WDS:        " + wds)

        if comp:
            comp = comp.replace(",","-") 

            print("           Components: " + comp)
        if angle:
            print("           PA:         " + angle)
        if sep:
            print("           Separation: " + sep + " AS")

        if lastYear:
            print("           Last Obs:   " + lastYear)

    return angle + ";" + sep  + ";" + wds  + ";" + comp



def dsMeasure(imgPath, primaryStarX, primaryStarY, targPA, targSep):
#
# Get your aspirin.
#
# This is a convoluted process to measure double stars.
#
# If there is a PA and a separation provided, it will use those as hints
# to try to snap to the appropriate light source as the secondary.
#
# If there is a PA but no separation distance in the catalog then it will draw
# out a triangular search region centered along the supplied PA.
#
# If there is neither a PA nor a separation supplied, it will try to find
# the closest light source to the primary. In my limited testing, this approach
# was wrong about 40% of the time.
#
# imgPath is either an absolute path to the image or "Active".
#
# primaryStarX&Y are coordinates to the primary star. It's nice if you give it
# a precise LS centroid, but it will snap to the closest one regardless, so don't
# knock yourself out.
#
# targPA & targSep are the afore mentioned hints that can be pulled from the catalog
# using the dsCatStats function or some other source.
#
# Thanks to Rick McAlister for his ideas and listening to me whine while I wrote it.
#

    primaryStarX = float(primaryStarX)
    primaryStarY = float(primaryStarY)

    lsXArray = []
    lsYArray = []
    lsNum = 0

    # This is a default to be changed upon subsequent failure.
    triSearchSuccess = "Success"
    bothHintFail = "Success"

    print("----------")
    timeStamp("Measuring primary & secondary relationship.")
    print("     -----")
    writeNote("Provided Primary Source: " + str(primaryStarX) + ", " + str(primaryStarY))
    print("     -----")

    #
    # Are we working on an active image in SkyX or a file with a path?
    #
    lastILPath = TSXSend("ImageLink.pathToFITS")

    if (imgPath == "Active"):
        TSXSend("ccdsoftCameraImage.AttachToActive()")
        TSXSend("ImageLink.pathToFITS = ccdsoftCameraImage.Path")
        writeNote("Using active image.")

    else:
        new_dir_name = flipPath(imgPath)

        TSXSend("ccdsoftCameraImage.DetachOnClose = 0")
        TSXSend('ImageLink.pathToFITS = "' + new_dir_name + '"')
        TSXSend('ccdsoftCameraImage.Path = "' + new_dir_name + '"')
        TSXSend("ccdsoftCameraImage.Open()")

    #
    # If the last image that we Image Linked the same as the current image, don't
    # bother to re-Image Link the sucker.
    #
    if lastILPath != TSXSend("ImageLink.pathToFITS"):
        ilResults = classicIL()

        #
        # If we do run Image Link, did it work?
        #

        if "rror:" in ilResults :
            print("    ERROR: Image Link Failed.")
            print("    ERROR: " + ilResults)
            return "Fail"

        else:
            timeStamp("Image Link Successful.")
            
    else:
        writeNote("Reusing previous Image Link information.")

    #
    # This takes a long time, but things get odd if I don't re-insert the WCS information.
    # 
    # The function seems to be more than, literally, inserting the WCS information in the
    # FITS header. It also seems to calculate the array of equatorial coordinates that
    # are mapped to the X,Y pixel coordinates.
    #
    TSXSend("ccdsoftCameraImage.InsertWCS()")

    #
    # I am now going to re-extract the light sources from the SexTractor into arrays because
    # the light sources identified by an image link seem to be only the light sources used
    # to calculate the Image Link. Some of the light sources that we want to search for will
    # include light sources that may not have been used by the Image Link.
    #
    dirName,fileName = os.path.split(TSXSend("ccdsoftCameraImage.Path"))
    lsNum = TSXSend("ccdsoftCameraImage.InventoryArray(0).length")
    writeNote(lsNum + " sources found in: " + fileName)

    #
    # These are the usual cool-to-know image statistics which are often used downstream for 
    # calculations
    #
    imageScale = round(float(TSXSend("ImageLinkResults.imageScale")), 3)
    imageCenterRA = TSXSend("ImageLinkResults.imageCenterRAJ2000")
    imageCenterDec = TSXSend("ImageLinkResults.imageCenterDecJ2000")
    ilFWHM = round(float(TSXSend("ImageLinkResults.imageFWHMInArcSeconds")), 3)
    ilPosAng = float(TSXSend("ImageLinkResults.imagePositionAngle"))
    TSXSend("sky6Utils.ConvertEquatorialToString(" + imageCenterRA + ", " + imageCenterDec + ", 5)")
    imageHMS2k = TSXSend("sky6Utils.strOut")
    TSXSend("sky6Utils.Precess2000ToNow( " + imageCenterRA + ", " + imageCenterDec + ")")
    imageRANow = TSXSend("sky6Utils.dOut0")
    imageDecNow = TSXSend("sky6Utils.dOut1")
    TSXSend("sky6Utils.ConvertEquatorialToString(" + imageRANow + ", " + imageDecNow + ", 5)")
    imageHMSNow = TSXSend("sky6Utils.strOut")
    meanPixelValue = float(TSXSend("ccdsoftCameraImage.averagePixelValue()"))
    meanPixelValue = int(round(meanPixelValue, 0))
    
    #
    # Create some arrays to store light source information
    #
    lsNum = TSXSend("ccdsoftCameraImage.InventoryArray(0).length")
    lsXRaw = TSXSend("ccdsoftCameraImage.InventoryArray(0)")
    lsXArray = lsXRaw.split(",")
    lsYRaw = TSXSend("ccdsoftCameraImage.InventoryArray(1)")
    lsYArray = lsYRaw.split(",")
    lsFWHMRaw = TSXSend("ccdsoftCameraImage.InventoryArray(4)")
    lsFWHMArray = lsFWHMRaw.split(",")
    lsXArrayLength = len(lsXArray)
    imageHeight = int(TSXSend("ccdsoftCameraImage.WidthInPixels"))
    imageWidth = int(TSXSend("ccdsoftCameraImage.HeightInPixels"))
    centerXPix = imageWidth / 2
    centerYPix = imageHeight / 2

    #
    # Tell us about the image
    #
    writeNote(str(lsXArrayLength) + " light sources transferred from SkyX.")
    print("     -----")
    writeNote("Image Statistics")
    print("           Scale:          " + str(imageScale) + " AS/pixel")
    print("           FWHM:           " + str(ilFWHM) + " AS")
    print("           Image (j2k) " + imageHMS2k)
    print("           Image (now) " + imageHMSNow)
    print("           Middle (X,Y):   " + str(centerXPix) + ", " + str(centerYPix))
    print("           Position Angle: " + str(round(ilPosAng, 1)) + " deg")
    print("     -----")
    smallestDist = centerYPix / 2
    
    #
    # Trust but verify.
    #
    # We're going to snap to the nearest lightsource for the primary
    # despite the fact that the user should have already done so.
    #
    #
    # Of course, this assumes that the primary is big enough to
    # be considered a bona finde light source by the SexTractor.
    #
    for LS in range(lsXArrayLength):
        distX = float(lsXArray[LS]) - primaryStarX
        distY = float(lsYArray[LS]) - primaryStarY
        pixDist = math.sqrt((distX * distX) + (distY * distY))
        if pixDist < smallestDist:
            cLS = LS
            smallestDist = pixDist

    #
    # Tell us about the primary star.
    #
    print("           Primary (X,Y):    " + lsXArray[cLS] + ", " + lsYArray[cLS] + " [LS: " + str(cLS) + "]")
    TSXSend("ccdsoftCameraImage.XYToRADec(" + lsXArray[cLS] + ", " + lsYArray[cLS] + ")")
    centerLSRAJ2k = TSXSend("ccdsoftCameraImage.XYToRADecResultRA()")
    centerLSDecJ2k = TSXSend("ccdsoftCameraImage.XYToRADecResultDec()")
    TSXSend("sky6Utils.Precess2000ToNow(" + centerLSRAJ2k + ", " + centerLSDecJ2k + ")")
    centerLSRANow = TSXSend("sky6Utils.dOut0")
    centerLSDecNow = TSXSend("sky6Utils.dOut1")
    TSXSend("sky6Utils.ConvertEquatorialToString(" + centerLSRAJ2k + ", " + centerLSDecJ2k + ", 5)")
    centerHMS2k = TSXSend("sky6Utils.strOut")
    TSXSend("sky6Utils.ConvertEquatorialToString(" + centerLSRANow + ", " + centerLSDecNow + ", 5)")
    centerHMSNow = TSXSend("sky6Utils.strOut")
    print("           Primary (j2k) " + centerHMS2k)
    print("           Primary (now) " + centerHMSNow)
    smallestDist = centerYPix / 2

    #
    # Do we have both a PA and a separation hint
    # for where to find the secondary?
    #

    # correct some weirdness by adding more.
    if targSep == " NA":
        targSep = "NA"
    
    if (targSep != "NA") and (targPA != "NA"):

        bothHintFail = "Success"

        writeNote("Using supplied PA & Separation hints.")
        writeNote("Hinted PA & Sep: " + str(targPA) + " & " + str(targSep))
        print("     -----")

        targPA = float(targPA)
        targSep = (float(targSep) / float(imageScale))
        smallestDist = (targSep * 1.5)
        targPA = float(targPA)
        ilPosAng = float(ilPosAng)
        relPA = ilPosAng + targPA

        #
        # Rationalize the location in case it exceeds 0 -> 360
        #
        if (relPA < 0):
            relPA = 360 + relPA

        if (relPA > 360):
            relPA = relPA - 360

        relPA = round(relPA,1)

        #
        # Do the scary trig to convert the PA and seperation into X,Y
        # coordinates.
        #
        # We're going to round it down to avoid over-the-top false precision
        #
        theta_rad = ((math.pi / 2) - math.radians(relPA))
        calcX = round((primaryStarX + (targSep * math.cos(theta_rad))), 3)
        calcY = round((primaryStarY + (targSep * math.sin(theta_rad))), 3)

        writeNote("Guessed Secondary: " + str(calcX) + ", " + str(calcY))

        #
        # The indexes below are the integer versions of the the floating point
        # secondary position estimate. They are used to refer to the bitmap
        # which must be addressed in whole pixels.
        #
        indexX = int(round(calcX, 0))
        indexY = int(round(calcY, 0))

        lineValuesArray = []

        if (indexX > 2 ) and (indexY > 2) and (indexY < (imageHeight - 2)) and (indexX < (imageWidth - 2 )):
        #
        # So, I'm going to be lazy. If the guessed secondary is next to the edge then I'm going
        # to give up and move on because I'm way too lazy to dynamically resize this stupid search pattern.
        #
        # Especially since the mount & pointing should have more-or-less centered the primary.
        #
            timeStamp("Searching for pixels. Creating a brightness array.")

            counterY = (indexY - 2)

            #
            # Take that Aspirin. This reads the ADU values from the image, but I use some ridiculous
            # offset values to avoid reading all the values from the image. I'm going to read in two
            # rows "behind" and two rows "ahead" of the guessed coordinates to create a search
            # box centered around the guessed secondary location.
            #
            while (counterY <= (indexY + 2)):
                lineValues = TSXSend("ccdsoftCameraImage.scanLine(" + str(counterY) + ")")
                lineValuesArray.append(lineValues.split(","))
            
                counterY = counterY + 1
            
            # Resuse this variable
            counterY = 0
            
            # Initialize the comparison value as the mean.
            brightestADU = meanPixelValue
            brightestX = indexX
            brightestY = 2

            while (counterY <= (4)):
                counterX = indexX - 3
                while (counterX <= (indexX + 1)):
                    currentADU = int(lineValuesArray[counterY][counterX])
                    if ( currentADU > brightestADU):
                        brightestADU = currentADU
                        brightestX = counterX
                        brightestY = counterY

                    counterX = counterX + 1
                counterY = counterY + 1

            #
            # Insist that the found candidate secondary be at least 150% of background average.
            #
            if brightestADU > (meanPixelValue * 1.5):
                brightestY = (indexY - 2) + brightestY
                writeNote("Found pixel at: " + str(brightestX) + ", " + str(brightestY) + " with more than 50% over background.")

                #
                # Pad the pixel value with a 0.5 so that it better reflects the "centroid" as being
                # in the middle of the found bright pixel rather than the upper left corner. Then add 
                # it to the X, Y and FWHM array so that we can recycle the LS-oriented code further on.
                #
                brightestX = float(brightestX) + 0.5
                brightestY = float(brightestY) + 0.5 
                lsXArray.append(str(brightestX))
                lsYArray.append(str(brightestY))
                lsFWHMArray.append(str(imageScale))

                nLS = (len(lsFWHMArray) - 1)

                #
                # At this point, we have found a pixel that looks like the secondary. We might, however, 
                # also have a light source from SexTractor that also corresponds to this pixel location.
                # If we do have a SexTractor light source then it will have a legitimate centroid calculated
                # by a real routine. If that exists, we want to use it instead of this "middle of the bright
                # pixel" kludge. On the other hand, maybe there is not a real SexTractor light source that
                # matches up to this pixel. So, we're going to look for a LS that's within an FWHM 
                # of the middle of our bright pixel. If we find one, we'll use it. If we don't, we'll move on.
                #
                writeNote("Searching for a corresponding LS.")

                # Initialize the "adjacent light source" value as the same as the nearest light source.             
                aLS = nLS

                # Set the initial smallestest distance to the image's FWHM in pixels.
                smallestDist = ilFWHM / imageScale

                #
                # If we find a SexTractor light source that's within an FMWH distance of the nearest light source
                # derived from the brightest pixel search above, then we're going to assign the adjacent light source
                # value to that light source. If we don't find one, the aLS will remain the same as the nLS.
                #
                for LS in range(lsXArrayLength):
                    if LS != cLS:
                        distX = brightestX - float(lsXArray[LS])
                        distY = brightestY - float(lsYArray[LS])
                        pixDist = math.sqrt((distX * distX) + (distY * distY))

                        if (pixDist < smallestDist):
                            aLS = int(LS)
                            smallestDist = pixDist

                #
                # If we found an adjacent light source, use it. If not, keep the middle of the bright pixel.
                #
                if (aLS == nLS):
                    writeNote("No corresponding previously identified light source found.")
                    writeNote("Adding this pixel as LS[" + str(nLS) + "]")
                    bitSearch = "Success"
                else:
                    writeNote("Adjacent light source: " + lsXArray[aLS] + ", " + lsYArray[aLS] + " [" + str(aLS) + "].")
                    nLS = aLS
                    bitSearch = "Success"
            else:
                writeNote("No corresponding pixels found.")
                bitSearch = "Fail"

        else:
        #
        # So this should never happen with sane pointing, but if the double star
        # of interest is right along the edge, I'm too lazy to dynamically resize
        # the search box in some goofy asymetrical way, so I'm just going to fail
        # to avoid indexing arrays that are off the edge of the image and invalid.
        #
                writeNote("Too Close to edge for pixel search.")
                bitSearch = "Fail"

        if (bitSearch == "Fail"):

            timeStamp("Pixel search failed.")
            writeNote("Searching for previously identified light sources.")

            nLS = cLS

            #
            # Find the nearest real light source to the guessed secondary light source
            #
            for LS in range(lsXArrayLength):
                if LS != cLS:
                    distX = calcX - float(lsXArray[LS])
                    distY = calcY - float(lsYArray[LS])
                    pixDist = math.sqrt((distX * distX) + (distY * distY))

                    if (pixDist < smallestDist):
                        nLS = LS
                        smallestDist = pixDist

            if (nLS == cLS):
                print("    ERROR: No corresponding light source found.")
                timeStamp("Finished measuring relationship.")
                bothHintFail = "Fail"

        if bothHintFail == "Fail":
            timeStamp("Unable to find secondary at the hinted location.")
        else:
        #
        # This gap measurement isn't really used here, but it's reported out below
        #
            smallestOKGap = (((float(lsFWHMArray[cLS]) * imageScale) / 2) +  ((float(lsFWHMArray[nLS]) \
                * imageScale) / 2) + imageScale)

            # 
            # now, calculate how far away the newly snapped-to secondary is from
            # the provided primary X/Y point. We're re-purposing smallestDist
            # for the diagnostic report at the bottom so that it's compatible
            # with the other methodologies
            #
            distX = primaryStarX - float(lsXArray[nLS])
            distY = primaryStarY - float(lsYArray[nLS])
            smallestDist = math.sqrt((distX * distX) + (distY * distY))

            print("     -----")
            writeNote("Refined Secondary: " + lsXArray[nLS] + ", " + lsYArray[nLS] + " [LS: " + str(nLS) + "] ")

    #
    # Do we have at least a PA hint or did the above routine fail?
    #
    if ((targSep == "NA") and (targPA != "NA")) or bothHintFail == "Fail":

        writeNote("Using supplied PA hint with no separation hint.")
        print("     -----")

        targPA = float(targPA)
        ilPosAng = float(ilPosAng)

        relPA = ilPosAng + targPA

        if (relPA < 0):
            relPA = 360 + relPA

        if (relPA > 360):
            relPA = relPA - 360

        relPA = round(relPA,1)

        #
        # Define the leading edge of a search triangle (PA1) and
        # the trailing edge of the search triangle (PA2)
        #
        relPA1 = relPA + 15
        relPA2 = relPA - 15
        if (relPA1 < 0):
            relPA1 = 360 + relPA1
        if (relPA1 > 360):
            relPA1 = relPA1 - 360
        if (relPA2 < 0):
            relPA2 = 360 + relPA2
        if (relPA2 > 360):
            relPA2 = relPA2 - 360

        AX = float(primaryStarX)
        AY = float(primaryStarY)

        targSep = imageWidth
        smallestDist = (imageWidth / 2)

        theta_rad = ((math.pi / 2) - math.radians(relPA1))
        BX = round((primaryStarX + (targSep * math.cos(theta_rad))), 3)
        BY = round((primaryStarY + (targSep * math.sin(theta_rad))), 3)

        theta_rad = ((math.pi / 2) - math.radians(relPA2))
        CX = round((primaryStarX + (targSep * math.cos(theta_rad))), 3)
        CY = round((primaryStarY + (targSep * math.sin(theta_rad))), 3)

        inArea = 0

        for LS in range(lsXArrayLength):
            DX = float(lsXArray[LS])
            DY = float(lsYArray[LS])

            #
            # So, the concept here is that if you take a point that is within the defined
            # triangle and then calculate three new "sub triangles" using two verticies
            # from the defined triangle and the point as the third vertex then, if you add
            # the area of the three verticies together then they should equal the defined
            # triangle's area. If the point is not inside of the defined triangle then
            # the summed area from the sub-triangles will not equal the defined triangle's 
            # area.
            #
            abcArea = ((AX * (BY - CY)) + (BX * (CY - AY)) + (CX * (AY - BY))) / 2
            abcArea = abs(abcArea)

            bcdArea = ((DX * (BY - CY)) + (BX * (CY - DY)) + (CX * (DY - BY))) / 2
            bcdArea = abs(bcdArea)

            abdArea = ((DX * (BY - AY)) + (BX * (AY - DY)) + (AX * (DY - BY))) / 2
            abdArea = abs(abdArea)
    
            acdArea = ((DX * (AY - CY)) + (AX * (CY - DY)) + (CX * (DY - AY))) / 2
            acdArea = abs(acdArea)

            subTriSum = (bcdArea + abdArea + acdArea)

            if (round(subTriSum, 0) == round(abcArea, 0)):
                # This just counts the sources
                inArea = inArea + 1

                if (LS != cLS):
                    # 
                    # This is the same old "closest point crap" that I
                    # should have probably just written as a function
                    #
                    distX = float(lsXArray[LS]) - float(lsXArray[cLS])
                    distY = float(lsYArray[LS]) - float(lsYArray[cLS])
                    pixDist = math.sqrt((distX * distX) + (distY * distY))
                    smallestOKGap = (((float(lsFWHMArray[cLS]) * imageScale) / 2) +  \
                            ((float(lsFWHMArray[LS]) * imageScale) / 2) + imageScale)
                   

                    if (pixDist < smallestDist) and (pixDist > smallestOKGap ):
                        nLS = LS
                        smallestDist = pixDist

        if nLS != cLS:
            writeNote("Total of " + str(inArea) + " light sources found in the search zone.")
            writeNote("Found Secondary: " + lsXArray[nLS] + ", " + lsYArray[nLS] + " [LS: " + str(nLS) + "] ")
            triSearchSuccess = "Success"
        else:
            writeNote("No light source found in search zone.")
            triSearchSuccess = "Fail"

    #
    # well, we're really screwed then. We've got no hints.
    #
    if (targPA == "NA") or (triSearchSuccess == "Fail"):
        print("     -----")
        writeNote("No hints provided. Flying blind.")
        print("     -----")

        #
        # Just find the closest SexTractor identified light source
        # and call it quits. This is pretty sketchy. During a test
        # run on some moderate spaced WDS stars, it was right about 
        # 60% of the time.
        #
        for LS in range(lsXArrayLength):
            if LS != cLS:
                distX = float(lsXArray[LS]) - float(lsXArray[cLS])
                distY = float(lsYArray[LS]) - float(lsYArray[cLS])
                pixDist = math.sqrt((distX * distX) + (distY * distY))
                smallestOKGap = (((float(lsFWHMArray[cLS]) * imageScale) / 2) +  ((float(lsFWHMArray[LS]) * imageScale) / 2) + imageScale)
                if (pixDist < smallestDist) and (pixDist > smallestOKGap ):
                    nLS = LS
                    smallestDist = pixDist

        print("           Nearest (X,Y):    " + lsXArray[nLS] + ", " + lsYArray[nLS] + " [LS: " + str(nLS) + "] ")
       

    #
    # This block of madness (re) calculates the PA and distance based on the image.
    #
    # I do it two ways - I use the built-in SkyX routines which use the equatorial coordinates
    # but I also use geometry as a double check and because I like to do things from first
    # principles when I can.
    #

    # First, pull the j2k coordinates for the light source from the WCS insertion.
    TSXSend("ccdsoftCameraImage.XYToRADec(" + lsXArray[nLS] + ", " + lsYArray[nLS] + ")")
    nearestLSRAJ2k = TSXSend("ccdsoftCameraImage.XYToRADecResultRA()")
    nearestLSDecJ2k = TSXSend("ccdsoftCameraImage.XYToRADecResultDec()")

    # Now, precess the j2k coordinates to now.
    TSXSend("sky6Utils.Precess2000ToNow(" + nearestLSRAJ2k + ", " + nearestLSDecJ2k + ")")
    nearestLSRANow = TSXSend("sky6Utils.dOut0")
    nearestLSDecNow = TSXSend("sky6Utils.dOut1")

    # Convert the decimal coordinates to a sexagesimal string for display.
    TSXSend("sky6Utils.ConvertEquatorialToString(" + nearestLSRAJ2k + ", " + nearestLSDecJ2k + ", 5)")
    nearestHMS2k = TSXSend("sky6Utils.strOut")
    TSXSend("sky6Utils.ConvertEquatorialToString(" + nearestLSRANow + ", " + nearestLSDecNow + ", 5)")
    nearestHMSNow = TSXSend("sky6Utils.strOut")

    # Dump those secondary star coordinates
    print("           Nearest (j2k) " + nearestHMS2k)
    print("           Nearest (now) " + nearestHMSNow)
    print("     -----")
    writeNote("Positional Measurements")

    # Use the built-in SkyX functions to calculate PA and separation (jnow)
    TSXSend("sky6Utils.ComputeAngularSeparation(" + nearestLSRANow + ", " + nearestLSDecNow + ", " + centerLSRANow + ", " + centerLSDecNow +")")
    distInASNow = 3600 * float(TSXSend("sky6Utils.dOut0"))
    TSXSend("sky6Utils.ComputePositionAngle(" + nearestLSRANow + ", " + nearestLSDecNow + ", " +  centerLSRANow + ", " +  centerLSDecNow + ")")
    ilPosAngleNow = str(round(float(TSXSend("sky6Utils.dOut0")),2))
    print("           Pos. Angle (SkyX now):     " + ilPosAngleNow)

    # Use the built-in SkyX functions to calculate PA and separation (j2k)
    TSXSend("sky6Utils.ComputeAngularSeparation(" + nearestLSRAJ2k + ", " + nearestLSDecJ2k + ", " + centerLSRAJ2k + ", " + centerLSDecJ2k +")")
    distInASJ2k = 3600 * float(TSXSend("sky6Utils.dOut0"))
    TSXSend("sky6Utils.ComputePositionAngle(" + nearestLSRAJ2k + ", " + nearestLSDecJ2k + ", " +  centerLSRAJ2k + ", " +  centerLSDecJ2k + ")")
    ilPosAngleJ2k = str(round(float(TSXSend("sky6Utils.dOut0")),2))
    print("           Pos. Angle (SkyX j2k):     " + ilPosAngleJ2k)

    # Use math to calculate PA and separation    
    deltaX = float(lsXArray[nLS]) - float(lsXArray[cLS]);
    deltaY = float(lsYArray[nLS]) - float(lsYArray[cLS]);
    rad = math.atan2(deltaY, deltaX);
    deg = math.degrees(rad)
    adjAngle = ilPosAng - (deg + 90)
    if adjAngle < 0:
        adjAngle = adjAngle + 360

    distInASMine = (smallestDist * imageScale)
    distInPxMine = smallestDist

    # Dump the results
    print("           Pos. Angle (Geometry):     " + str(round(adjAngle,2)))
    print("           Separation (SkyX now):     " + str(round(distInASNow, 2)) + " AS")
    print("           Separation (SkyX j2k):     " + str(round(distInASJ2k, 2)) + " AS")
    print("           Separation (Geometry):     " +  str(round(distInASMine, 2)) + " AS (" + str(round(distInPxMine, 2)) + " px)")
    print("")
    print("           Reliable separation limit: " + str(round(smallestOKGap, 1)) + " AS")
    print("     -----")
    timeStamp("Finished measuring relationship.")

    #
    # If the image is not the active image, go ahead and close it.
    #
    if (imgPath != "Active"):
        TSXSend("ccdsoftCameraImage.Close()")

    return str(round(adjAngle,2)) + ", " + str(round(distInASMine, 2)) + ", " + centerLSRAJ2k + ", " \
            + centerLSDecJ2k + ", " + nearestLSRAJ2k + ", " + nearestLSDecJ2k + ", " + str(round(smallestOKGap, 2))


def dsProcess(imgPath):
# 
# This is a macro process for several smaller functions
#
# the goal is to return a string with the target name, the measured values and the 
# comparable values from the catalogs.
#
    # Get the target name from the image file.
    #
    # I'm lazy and it's easier than slicing & dicing custom filenames.
    #
    target = targFromImage(imgPath)

    if "Fail" in target:
        writeNote("Unable to identify target.")
        return (target + ", X, X, X, X, X, X, NA, NA, X, X, X")
    
    # Find the X & Y coordinates that represent the target as defined by the OBJECT 
    # keyword in the FITS Header.

    result = findXY(imgPath, target)
    
    #
    # If you specified an unfindable target, then bail.
    #
    if result != "Fail":
        targX = result[0]
        targY = result[1]
    else:
        writeNote("Unable to locate target.")
        return (target + ", X, X, X, X, X, X, NA, NA, X, X, X")
      
       
    
    # Go dig out the expected PA and separation (if available) from the 
    # relevant catalog.
    catOutput = dsCatStats()


    if "Fail" in catOutput:
        catOutput = "NA; NA; X; X"
    
    catPA, catSep, catWDS, catComp = catOutput.split(";")

    # Find the specified target and measure the closest thing to it within
    # reason (as based on the objects' FWHM values and the image scale.
    measureOutput = dsMeasure(imgPath, targX, targY, catPA, catSep)

    if not "Fail" in measureOutput:  
        imagePA, imageSep, primRAJ2k, primDecJ2k, secRAJ2k, secDecJ2k, gap = measureOutput.split(", ")
    else:
        imagePA = "NA"
        imageSep = "NA"

    target = target.replace(",","-") 
    
    return target + "," + catWDS + "," + catComp + "," + primRAJ2k + "," + primDecJ2k + "," + secRAJ2k + "," + secDecJ2k + "," + catPA + "," \
            + catSep + "," + imagePA + "," + imageSep + "," + gap


def dumpStars(imgPath):
#
# Module to dump info about the stars found in an image.
#
# Set the parameter to the string "Active" to analyze the active image, 
# otherwise give it a full path.
#
# You'll see lots of sexy looking data, but the real information will
# be placed in a comma separated values file in the same directory as
# the image file.
#
    lsXArray = []
    lsYArray = []   
    lsFWHMArray = []
    nameListArray = []
    catMagArray = []
    lsDecArray = []
    lsRAArray = []
    realADUs = []
    compareSEMag = []
    compareCatMag = []
    synthMag = []
    gaiaMagArray = []
    gaiaRAArray = []
    gaiaDecArray = []

    lastILPath = TSXSend("ImageLink.pathToFITS")

    if (imgPath == "Active"):
        TSXSend("ccdsoftCameraImage.AttachToActive()")
        TSXSend("ImageLink.pathToFITS = ccdsoftCameraImage.Path")
        writeNote("Using active image.")

    else:
        newPathName = flipPath(imgPath)

        TSXSend("ccdsoftCameraImage.DetachOnClose = 0")
        TSXSend('ImageLink.pathToFITS = "' + newPathName + '"')
        TSXSend('ccdsoftCameraImage.Path = "' + newPathName + '"')
        TSXSend("ccdsoftCameraImage.Open()")

    if lastILPath != TSXSend("ImageLink.pathToFITS"):
        ilResults = classicIL()

        if ("rror:" in ilResults) or ("Fail" in ilResults):
            print("    ERROR: Image Link Failed.")
            print("    ERROR: " + ilResults)
            return "Fail"

        else:
            timeStamp("Image Link Successful.")
    else:
        writeNote("Reusing previous Image Link information.")

    wcsOutput = TSXSend("ccdsoftCameraImage.InsertWCS()")

    dirName,fileName = os.path.split(TSXSend("ccdsoftCameraImage.Path"))
    lsNum = TSXSend("ccdsoftCameraImage.InventoryArray(0).length")
    writeNote(lsNum + " sources found in: " + fileName)

    lsXRaw = TSXSend("ccdsoftCameraImage.InventoryArray(0)")
    lsXArray = lsXRaw.split(",")

    lsYRaw = TSXSend("ccdsoftCameraImage.InventoryArray(1)")
    lsYArray = lsYRaw.split(",")

    lsMagRaw = TSXSend("ccdsoftCameraImage.InventoryArray(2)")
    lsMagArray = lsMagRaw.split(",")

    lsFWHMRaw = TSXSend("ccdsoftCameraImage.InventoryArray(4)")
    lsFWHMArray = lsFWHMRaw.split(",")

    imageScale = round(float(TSXSend("ImageLinkResults.imageScale")), 3)

    numSources = len(lsXArray)
    writeNote(str(numSources) + " light sources transferred from SkyX.")
    print("     -----")

    #
    # This mag output stuff is because I couldn't find a consistanty reliable 
    # measure that I could derive from the image to determine magnitude, so
    # I decided to give the user a selection of options.
    #
    magOutput = getMag(newPathName)

    meanMagArray = magOutput[0]

    medianMagArray = magOutput[1]

    brightestMagArray = magOutput[2]

    sumBrightMagArray = magOutput[3]

    # We have to re-open this crap because getMag closes it.

    TSXSend("ccdsoftCameraImage.DetachOnClose = 0")
    TSXSend('ImageLink.pathToFITS = "' + newPathName + '"')
    TSXSend('ccdsoftCameraImage.Path = "' + newPathName + '"')
    TSXSend("ccdsoftCameraImage.Open()")

    wcsOutput = TSXSend("ccdsoftCameraImage.InsertWCS()")

    counter = 0
    
    while (counter < numSources):
    #
    # Cycle through the light sources and stuff the values into arrays
    #

        TSXSend("ccdsoftCameraImage.XYToRADec(" + lsXArray[counter] + ", " + lsYArray[counter] + ")")

        lsRA = TSXSend("ccdsoftCameraImage.XYToRADecResultRA()")

        lsRA = str(float(lsRA))

        lsRAArray.append(lsRA)

        lsDec = TSXSend("ccdsoftCameraImage.XYToRADecResultDec()")
        lsDec = str(float(lsDec)) 
        lsDecArray.append(lsDec)

        # Figure out the source FWHM in pixels then AS to use as a closeness value for the catalog search.
        lsFWHM = float(lsFWHMArray[counter])
        lsFWHM = round((lsFWHM * imageScale), 2)
        lsFWHMArray.append(lsFWHM)
        
        #
        # Get the averaged magnitude and proper names out of the selected catalogs
        #
        print("----------")
        writeNote("Analyzing light source " + str(counter + 1) + " of " + str(numSources))

        findAtOutput = namesAt(lsRA + ", " + lsDec, lsFWHM)

        if ("None" in findAtOutput):
            catMagArray.append("NA")
            nameListArray.append("Unknown")
            gaiaMagArray.append("NA")
            gaiaRAArray.append("NA")
            gaiaDecArray.append("NA")


        else:
            lsAvgMag,gaiaMag,gaiaRA,gaiaDec,nameList = findAtOutput.split(",")
            catMagArray.append(lsAvgMag)
            gaiaMagArray.append(gaiaMag)
            gaiaRAArray.append(gaiaRA)
            gaiaDecArray.append(gaiaDec)
            nameListArray.append(nameList)
        
        counter = counter + 1

    print("----------")
    timeStamp("Writing CSV file.")
    #
    # This creates a file for the CSV data. It is named after the image
    # and placed in the same directory.
    #
    dirName,fileName = os.path.split(TSXSend("ccdsoftCameraImage.Path"))
    orgImgName = os.path.splitext(fileName)[0]
    csvFile = dirName + "/" + orgImgName + ".csv"
    outFile = open(csvFile, "w")
    outFile.write("Source #, X, Y, RA (j2k), Dec (j2k), Gaia RA (j2k), Gaia Dec (j2k), FWHM, Brightest Pixel," + \
            "Summed LS ADU, Median LS ADU, Mean LS ADU, SE LS Mag, SX Mag, Gaia Mag, Proper Names" + CR)

    counter = 0

    while (counter < numSources):
    #
    # Cycle through the light sources and write the file.
    #
    # This was broken out of the previous loop to give me a little more flexibility
    # while experimenting.
    #
        outFile.write(str(counter) + ", " + lsXArray[counter] + ", " + lsYArray[counter] + ", " + lsRAArray[counter] + ", " \
                + lsDecArray[counter] + ", " + gaiaRAArray[counter] + ", " + gaiaDecArray[counter] + ", " \
                + str(lsFWHMArray[counter]) + ", " + str(brightestMagArray[counter]) + ", " \
                + str(sumBrightMagArray[counter]) + ", " + str(medianMagArray[counter]) + ", " + str(meanMagArray[counter]) \
                + ", " + str(lsMagArray[counter]) + ", " + str(catMagArray[counter]) + ", " \
                + str(gaiaMagArray[counter]) + ", " + nameListArray[counter] + CR)

        counter = counter + 1

    if (imgPath != "Active"):
        TSXSend("ccdsoftCameraImage.Close()")

    csvFile = pathlib.Path(csvFile)

    writeNote("Output: " + str(csvFile.name))  
    print("----------")

def findRADec(imgPath, targX, targY):
#
# Crude module to convert an imag pixel X & Y into an RA/Dec coordinate.
#
# This does *NOT* snap to an actual light source. What you provide
# is what it guesses uses.
#
# Returns equatorial coordinates in j2k & now.
#
    lastILPath = TSXSend("ImageLink.pathToFITS")

    if (imgPath == "Active"):
        TSXSend("ccdsoftCameraImage.AttachToActive()")
        TSXSend("ImageLink.pathToFITS = ccdsoftCameraImage.Path")
        writeNote("Using active image.")

    else:
        newPathName = flipPath(imgPath)

        TSXSend("ccdsoftCameraImage.DetachOnClose = 0")
        TSXSend('ImageLink.pathToFITS = "' + newPathName + '"')
        TSXSend('ccdsoftCameraImage.Path = "' + newPathName + '"')
        TSXSend("ccdsoftCameraImage.Open()")

    if lastILPath != TSXSend("ImageLink.pathToFITS"):
        ilResults = classicIL()

        if "rror:" in ilResults :
            print("    ERROR: Image Link Failed.")
            print("    ERROR: " + ilResults)
            return "Fail"

        else:
            timeStamp("Image Link Successful.")
    else:
        writeNote("Reusing previous Image Link information.")

    TSXSend("ccdsoftCameraImage.InsertWCS()")
    dirName,fileName = os.path.split(TSXSend("ccdsoftCameraImage.Path"))
    lsNum = TSXSend("ccdsoftCameraImage.InventoryArray(0).length")
    writeNote(lsNum + " sources found in: " + fileName)


    TSXSend("ccdsoftCameraImage.XYToRADec(" + str(targX) + ", " + str(targY) + ")")

    RAj2k = TSXSend("ccdsoftCameraImage.XYToRADecResultRA()")
   
    DecJ2k = TSXSend("ccdsoftCameraImage.XYToRADecResultDec()")

    TSXSend("sky6Utils.Precess2000ToNow(" + RAj2k + ", " +  DecJ2k + ")")
    RAnow = TSXSend("sky6Utils.dOut0")
    DecNow = TSXSend("sky6Utils.dOut1")

    TSXSend("sky6Utils.ConvertEquatorialToString(" + RAj2k + ", " + DecJ2k + ", 5)")
    SexJ2k = TSXSend("sky6Utils.strOut")
    TSXSend("sky6Utils.ConvertEquatorialToString(" + RAnow + ", " + DecNow + ", 5)")
    SexNow = TSXSend("sky6Utils.strOut")
    print("           Nearest (j2k) " + SexJ2k)
    print("           Nearest (now) " + SexNow)
    print("     -----")

    if (imgPath != "Active"):
        TSXSend("ccdsoftCameraImage.Close()")
 
    return RAj2k + ", " + DecJ2k + ", " + RAnow + ", " + DecNow


def findXY(imgPath, target):
#
# Returns the X & Y coordinates in the specified image for the 
# specified target. The target can be a proper name or a set of 
# coordinates - anything that is valid for the "Find" field in
# SkyX. 
#
# It will look up the coordinates, translate them to expected X & Y
# coordinates and then do a light source search near the X & Y 
# location to give you an actual light source.
# 
# Returns the X & Y of the centroid of the LS found closest to the
# supplied coordinates.
#
    print("----------")
    timeStamp("Finding target X & Y coordinates in image.")
    print("     -----")

    lastILPath = TSXSend("ImageLink.pathToFITS")

    if (imgPath == "Active"):
        TSXSend("ccdsoftCameraImage.AttachToActive()")
        TSXSend("ImageLink.pathToFITS = ccdsoftCameraImage.Path")
        writeNote("Using active image.")

    else:
        newPathName = flipPath(imgPath)
        
        TSXSend("ccdsoftCameraImage.DetachOnClose = 0")
        TSXSend('ImageLink.pathToFITS = "' + newPathName + '"')
        TSXSend('ccdsoftCameraImage.Path = "' + newPathName + '"')
        TSXSend("ccdsoftCameraImage.Open()")

    if lastILPath != TSXSend("ImageLink.pathToFITS"):
        ilResults = classicIL()

        if ("rror:" in ilResults) or ("Fail" in ilResults):
            print("    ERROR: Image Link Failed.")
            print("    ERROR: " + ilResults)
            return "Fail"

        else:
            timeStamp("Image Link Successful.")
    else:
        writeNote("Reusing previous Image Link information.")

    TSXSend("ccdsoftCameraImage.InsertWCS()")
    dirName,fileName = os.path.split(TSXSend("ccdsoftCameraImage.Path"))
    lsNum = TSXSend("ccdsoftCameraImage.InventoryArray(0).length")
    writeNote(lsNum + " sources found.")
    print("     -----")        

    #
    # This "period after the name" hack is needed because we are
    # going to eventually analyze chart X,Y positions which aren't
    # there if the chart around the target is not visible.
    #
    # A coordinate will, for some reason, cause SkyX to autocenter
    # but a proper name will not, unless you add the period.
    #
    if "," not in target:
        result = TSXSend('sky6StarChart.Find("' + target + '.")')
    else:
        result = TSXSend('sky6StarChart.Find("' + target + '")')

    #
    # If it's a bogus target then tell an adult.
    #
    if ("rror"  in result) or ("not found" in result):
        timeStamp("Target not found.")
        print(" ")
        return "Fail"
    else:
        writeNote("Target: " + target)

    print("     -----")

    #
    # This nonsense is to determine if the object is a double
    # star and, if it is, if it's from the Washington Double Star
    # Catalog and, if it is, are we using the 2018 version.
    #
    # If it's a WDS and you have the 2018 version, then we'll 
    # switch to that catalog because the coordinates are more
    # accurate.
    #
    TSXSend("sky6ObjectInformation.Property(12)")		
    objType = TSXSend("sky6ObjectInformation.ObjInfoPropOut")	

    if (objType == "Double Star"):
        writeNote("Object is a double star.")
        TSXSend("sky6ObjectInformation.Property(19)")			
        catalog = TSXSend("sky6ObjectInformation.ObjInfoPropOut")

        TSXSend("sky6ObjectInformation.Property(0)")		
        name = TSXSend("sky6ObjectInformation.ObjInfoPropOut")

        #
        # If you have the WDS-2019 catalog, it will try to switch
        # because the measures are newer and it has separations.
        #
        if "WDS" and "2019" not in catalog:
                if "WDS" and "2018" not in catalog:
                    name2019 = name.replace("WDS", "WDS-2019")
                    result = TSXSend('sky6StarChart.Find("' + name2019 + '")')
    
                    if ("rror" in result) or ("not found" in result):
                        writeNote("No corresponding WDS-2019 entry found.")
                        TSXSend('sky6StarChart.Find("' + name + '")')
                    else:
                        name = name2019
                        writeNote("Switching to WDS-2019 catalog: " + name)
                        TSXSend("sky6ObjectInformation.Property(19)")			
                        catalog = TSXSend("sky6ObjectInformation.ObjInfoPropOut")


    TSXSend("sky6ObjectInformation.Property(56)")				
    targRA = TSXSend("sky6ObjectInformation.ObjInfoPropOut")	
    TSXSend("sky6ObjectInformation.Property(57)")			
    targDec = TSXSend("sky6ObjectInformation.ObjInfoPropOut")
    
    TSXSend("ccdsoftCameraImage.RADecToXY(" + targRA + ", " + targDec + ")")
    
    targX = TSXSend("ccdsoftCameraImage.RADecToXYResultX()")
    targX = str(round(float(targX),3))
    targY = str(round(float(TSXSend("ccdsoftCameraImage.RADecToXYResultY()")),3))

    if (targX == "0.0") or (targY == "0.0"):
        print("    ERROR: X & Y Results are zero.")
        print("           Something may be wrong with the image or SkyX.")
        print("           Maybe, SkyX is using old Image Link data.")
        print("           If image is OK, try a restart.")
        return "Fail"

    if (float(targX) >= float(TSXSend("ccdsoftCameraImage.WidthInPixels"))) or \
            (float(targX) < 0):
                print("    ERROR: Target location exceeds supplied image boundries.")
                return "Fail"

    if (float(targY) >= float(TSXSend("ccdsoftCameraImage.HeightInPixels"))) or \
            (float(targY) < 0):
                print("    ERROR: Target location exceeds supplied image boundries.")
                return "Fail"

    writeNote("Calculated Coordinates:      " + targX + ", " + targY)
    print("     -----")

    imageScale = round(float(TSXSend("ImageLinkResults.imageScale")), 3)
    imageCenterRA = TSXSend("ImageLinkResults.imageCenterRAJ2000")
    imageCenterDec = TSXSend("ImageLinkResults.imageCenterDecJ2000")
    
    lsXRaw = TSXSend("ccdsoftCameraImage.InventoryArray(0)")
    lsXArray = lsXRaw.split(",")
    lsYRaw = TSXSend("ccdsoftCameraImage.InventoryArray(1)")
    lsYArray = lsYRaw.split(",")

    lsFWHMRaw = TSXSend("ccdsoftCameraImage.InventoryArray(4)")
    lsFWHMArray = lsFWHMRaw.split(",")
    lsXArrayLength = len(lsXArray)
    
    smallestDist = float(TSXSend("ccdsoftCameraImage.HeightInPixels")) / 4

    #
    # Find the nearest "real" light source
    #
    for LS in range(lsXArrayLength):

        distX = float(lsXArray[LS]) - float(targX)
        distY = float(lsYArray[LS]) - float(targY)
        pixDist = math.sqrt((distX * distX) + (distY * distY))
        if pixDist < smallestDist:
            cLS = LS
            smallestDist = pixDist
    
    timeStamp("Closest Source Coordinates:  " + lsXArray[cLS] + ", " + lsYArray[cLS] + " [LS: " + str(cLS) + "]")
    
    TSXSend("ccdsoftCameraImage.XYToRADec(" + lsXArray[cLS] + ", " + lsYArray[cLS] + ")")
    centerLSRAJ2k = TSXSend("ccdsoftCameraImage.XYToRADecResultRA()")
    centerLSDecJ2k = TSXSend("ccdsoftCameraImage.XYToRADecResultDec()")
    TSXSend("sky6Utils.Precess2000ToNow(" + centerLSRAJ2k + ", " + centerLSDecJ2k + ")")
    centerLSRANow = TSXSend("sky6Utils.dOut0")
    centerLSDecNow = TSXSend("sky6Utils.dOut1")
    TSXSend("sky6Utils.ConvertEquatorialToString(" + centerLSRAJ2k + ", " + centerLSDecJ2k + ", 5)")
    centerHMS2k = TSXSend("sky6Utils.strOut")
    TSXSend("sky6Utils.ConvertEquatorialToString(" + centerLSRANow + ", " + centerLSDecNow + ", 5)")
    centerHMSNow = TSXSend("sky6Utils.strOut")
    print("    ------")
    print("           (j2k) " + centerHMS2k)
    print("           (now) " + centerHMSNow)

    if (imgPath != "Active"):
        TSXSend("ccdsoftCameraImage.Close()")

    returnArray = [lsXArray[cLS], lsYArray[cLS]]

    return returnArray


def getMag(imgPath):
#
# Extract averaged ADU values from around light sources based on the light source's
# FWHM.
#
# This is an alternate method for trying to quantify brightness because the sextractor's
# magnitude value sometimes seems whacked.
#
# Inspired by a technique from Colin McGill for analyzing guider images and informed by 
# discussion with Rick McAlister.
#

    meanADUarray = []
    medianADUarray = []
    brightestADUarray =[]
    sumADUarray = []
    compMeanADUarray = []

    print("----------")
    timeStamp("Finding brightness values in image.")
    print("     -----")

    lastILPath = TSXSend("ImageLink.pathToFITS")

    if (imgPath == "Active"):
        TSXSend("ccdsoftCameraImage.AttachToActive()")
        TSXSend("ImageLink.pathToFITS = ccdsoftCameraImage.Path")
        writeNote("Using active image.")

    else:
        newPathName = flipPath(imgPath)

        TSXSend("ccdsoftCameraImage.DetachOnClose = 0")
        TSXSend('ImageLink.pathToFITS = "' + newPathName + '"')
        TSXSend('ccdsoftCameraImage.Path = "' + newPathName + '"')
        TSXSend("ccdsoftCameraImage.Open()")

    if lastILPath != TSXSend("ImageLink.pathToFITS"):

        ilResults = classicIL()

        if "TypeError:" in ilResults :
            print("    ERROR: Image Link Failed.")
            print("    ERROR: " + ilResults)
            return "Fail"

        else:
            timeStamp("Image Link Successful.")
    else:
        writeNote("Reusing previous Image Link information.")

    TSXSend("ccdsoftCameraImage.InsertWCS()")
    dirName,fileName = os.path.split(TSXSend("ccdsoftCameraImage.Path"))
    lsNum = TSXSend("ccdsoftCameraImage.InventoryArray(0).length")
    writeNote(lsNum + " sources found.")

    lsXRaw = TSXSend("ccdsoftCameraImage.InventoryArray(0)")
    lsXArray = lsXRaw.split(",")
    lsYRaw = TSXSend("ccdsoftCameraImage.InventoryArray(1)")
    lsYArray = lsYRaw.split(",")

    lsFWHMRaw = TSXSend("ccdsoftCameraImage.InventoryArray(4)")
    lsFWHMArray = lsFWHMRaw.split(",")

    meanPixelValue = float(TSXSend("ccdsoftCameraImage.averagePixelValue()"))

    meanPixelValue = round(meanPixelValue, 0)
    meanPixelValue = int(meanPixelValue)
    
    writeNote("Image Mean Brightness: " + str(meanPixelValue))

    print("     -----")

    lineValuesArray = []
    
    imageHeight = int(TSXSend("ccdsoftCameraImage.HeightInPixels"))
    imageWidth = int(TSXSend("ccdsoftCameraImage.WidthInPixels"))
    
    timeStamp("Image Dimensions: " + str(imageWidth) + "x" + str(imageHeight))
    
    writeNote("Creating ADU array.")

    counter = 0

    #
    # this creates a giant two dimensional array, I mean list, to store the
    # ADU values for each pixel.
    #
    while (counter < imageHeight):
        lineValues = TSXSend("ccdsoftCameraImage.scanLine(" + str(counter) + ")")
        lineValuesArray.append(lineValues.split(","))
            
        counter = counter + 1
    
    print("     -----")

    LS = 0

    #
    # Now we'll cycle through each light source
    #
    while LS < int(lsNum):
        brightest = 0
        brightX = 0
        brightY = 0
    
        targX = float(lsXArray[LS])
        targY = float(lsYArray[LS])
        FWHM = float(lsFWHMArray[LS])
    
        targX = round(targX, 0)
        targY = round(targY, 0)
        FWHM = round(FWHM, 0)
    
        targX = int(targX)
        targY = int(targY)
        FWHM = int(FWHM)

        FWHM = FWHM 
    
        counter = -1

        #
        # Don't explore around edge pixels because the values off the edge of
        # the plate don't exist. This means that, sometimes, you'll misrepresent
        # a big fat star sitting right on the edge.
        #
        while (counter <= 1):
            if not (targY <= FWHM) and not (targY >= (imageHeight - FWHM)) \
                    and not (targX <= 0) and not (targX >= (imageWidth - FWHM)):
                
                #
                # The reason for this is because the SexTractor lives in an idealized and smoothed
                # world of light sources based on sub-pixel centroids. What we want here is to 
                # dive back into the raw pixel ADU counts, but the sub-pixel centroid may be
                # centered on a pixel that isn't the brightest. I want to start from the brightest
                # pixel because, theory aside, that is the pixel recording the greatest flux.
                #
                # So, we have to feel around the neighboring pixels to see if one of them is actually
                # brighter than the pixel containing the derived centroid. If so, that will be the
                # central point for the box of pixels that we're going to measure and average.
                #
                counter2 = -1

                while (counter2 <= 1):
                    if int(lineValuesArray[targY + counter ][targX + counter2]) > brightest:
                        brightest = int(lineValuesArray[targY + counter][targX + counter2])
                        brightX = int(targX + counter2)
                        brightY = int(targY + counter)
                    counter2 = counter2 + 1
    
                counter = counter + 1

            else:
                FWHM = 1
                counter = counter + 1

        if int(FWHM) <= 1:
            meanADUvalue = brightest - meanPixelValue
            medianADUvalue = meanADUvalue
            sumADUvalue = meanADUvalue
            brightest = meanADUvalue
    
        else:
            aduList = []

            # 
            # We're setting the measurement window/aperture based on the
            # SexTractor's FWHM. I played with a bigger window, but found that
            # it incuded too much darkness around the source.
            #
            radius = (FWHM / 2)
            radius = round(radius, 0)
            radius = int(radius)
    
            #
            # Now we're going to measure around the brightest pixel in the source
            # with a box of pixels that are sort-of defined by the FWHM provided
            # in the SexTractor array as explained above
            #
            counter = (-1 * radius)
    
            while (counter <= radius):
                counter2 = (-1 * radius)
    
                while (counter2 <= radius):
                    currentX = (brightX + counter2)
                    currentY = (brightY + counter)
    
                    aduList.append(int(lineValuesArray[currentY][currentX]))
                    
                    counter2 = counter2 + 1
    
                counter = counter + 1


            meanADUvalue = statistics.mean(aduList)
            meanADUvalue = meanADUvalue - meanPixelValue
            meanADUvalue = round(meanADUvalue, 0)
            meanADUvalue = int(meanADUvalue)

            medianADUvalue = statistics.median(aduList)
            medianADUvalue = medianADUvalue - meanPixelValue
            medianADUvalue = round(medianADUvalue, 0)
            medianADUvalue = int(medianADUvalue)

            sumADUvalue = (sum(aduList) - (meanPixelValue * len(aduList)))
            sumADUvalue = int(sumADUvalue)

            brightest = brightest - meanPixelValue
            brightest = int(brightest)

        meanADUarray.append(meanADUvalue)
        medianADUarray.append(medianADUvalue)
        brightestADUarray.append(brightest)
        sumADUarray.append(sumADUvalue)

        LS = LS + 1

    returnArray = [meanADUarray, medianADUarray, brightestADUarray, sumADUarray]

    if (imgPath != "Active"):
        TSXSend("ccdsoftCameraImage.Close()")

    timeStamp("Finished brightness search.")

    return returnArray

def namesAt(target, limit):
#
# This routine takes a target proper name or set of j2k coordinates and
# does a "fuzzy" match against all the currently selected object
# catalogs. It prints much impressive looking text but returns a 
# simple string of the averaged magnitude followed by a comma and then 
# semi-colon seperated proper names associated with that position.
#
# You could use it to cross check names but the main reason that
# I wrote it was to catalog light source inventories.
#
# Target is the target location and limit defines how close in
# arc seconds two points are to be considered the same. The limit
# won't let you expand much, it's more to reduce the area around the
# supplied target that's considered valid.
#
# If you don't find the sources that you're looking for, check
# your catalog selections (or maybe try restarting SkyX...)
#
# Thanks to Rick McAlister for the great idea and instructions for the 
# find-click command.
#
    counter = 0
    targX = " "
    targY = " "
    targRA = " "
    targDec = " "
    nameIndex = 1
    uniqueName = []
    uniqueRA = []
    uniqueDec = []
    uniqueMag = []
    uniqueName = []
    objMagValues = []
    uniqueDist = []
    otherNames = set()
    outputStatement = ""
    objName1 = " "
    objNameX = " "
    result = "nothing"
    gaiaRA = "X"
    gaiaDec = "X"
    gaiaMag = "X"

    print("----------")
    timeStamp("Searching near: " + target)

    writeNote("Distance Limit: " + str(round(float(limit),2)) + " AS")
    TSXSend('sky6StarChart.Find("Z 0.5")')
            
    TSXSend("sky6StarChart.Refresh()")

    #
    # This "period after the name" hack is needed because we are
    # going to eventually analyze chart X,Y positions which aren't
    # there is the chart around the target is not visible.
    #
    # A coordinate will, for some reason, cause SkyX to autocenter
    # but a proper name will not, unless you add the period.
    #
    if "," not in target:
        result = TSXSend('sky6StarChart.Find("' + target + '.")')
    else:
        result = TSXSend('sky6StarChart.Find("' + target + '")')

    #
    # If it's a bogus target then tell an adult.
    #
    if "rror" in result:
        timeStamp("Target not found.")
        sys.exit()

    #
    # Get the coordinates so that we can then pull chart-specific
    # X,Y coordinates and simulate a click at that point so that the
    # neighboring objects will be found.
    #
    TSXSend("sky6ObjectInformation.Property(56)")				
    targRA = TSXSend("sky6ObjectInformation.ObjInfoPropOut")	

    TSXSend("sky6ObjectInformation.Property(57)")			
    targDec = TSXSend("sky6ObjectInformation.ObjInfoPropOut")

    TSXSend('sky6StarChart.EquatorialToStarChartXY(' + targRA + ', ' + targDec + ')')
    
    targX = TSXSend("sky6StarChart.dOut0")
    targY = TSXSend("sky6StarChart.dOut1")

    TSXSend("sky6StarChart.ClickFind(" + targX + ", " + targY + ")")

    #
    # How many objects are found "around" the click point. These objects should
    # be the same ones listed in the "Related Searches" window under the Find
    # pane/panel.
    #
    numObjects = int(TSXSend("sky6ObjectInformation.Count")) 
   
    writeNote("Found " + str(numObjects) + " items associated with this location.")

    # 
    # The objects associated with the click point have their information stored 
    # in an array of arrays. The index for each object in incremented in this
    # while loop to cycle through them all.
    #
    while (counter < numObjects):
  
        # 
        # This variable sets the index for which of the related objects we are
        # going to analyze.
        TSXSend("sky6ObjectInformation.Index = " + str(counter))
        
        TSXSend("sky6ObjectInformation.Property(0)")
        objName1 = TSXSend("sky6ObjectInformation.ObjInfoPropOut") 
 
        #
        # Part of the issue is that each object goes by many names and
        # each one of the associated objects (which are probably duplicates
        # from different catalogs) may have different names.
        #
        # This routine just loops through the properties which represent 
        # most of the alternate names.
        #
        nameIndex = 1

        while ( nameIndex < 7 ):
            TSXSend("sky6ObjectInformation.Property(" + str(nameIndex) + ")")
            objNameX = TSXSend("sky6ObjectInformation.ObjInfoPropOut")
            if not objNameX.isspace() and (len(objNameX.strip()) > 2):
                otherNames.add(objNameX.strip())
            nameIndex = nameIndex + 1

        #
        # Pull other data
        #
        TSXSend("sky6ObjectInformation.Property(65)")
        objMag = round(float(TSXSend("sky6ObjectInformation.ObjInfoPropOut")),2)


        TSXSend("sky6ObjectInformation.Property(56)")
        objRAj2k = TSXSend("sky6ObjectInformation.ObjInfoPropOut") 
        objRAj2k = str(float(objRAj2k))
    

        TSXSend("sky6ObjectInformation.Property(57)")
        objDecj2k = TSXSend("sky6ObjectInformation.ObjInfoPropOut") 
        objDecj2k = str(float(objDecj2k))

    
        TSXSend("sky6ObjectInformation.Property(54)")
        objRANow = TSXSend("sky6ObjectInformation.ObjInfoPropOut") 
        objRANow = str(float(objRANow))

        TSXSend("sky6ObjectInformation.Property(55)")
        objDecNow = TSXSend("sky6ObjectInformation.ObjInfoPropOut") 
        objDecNow = str(float(objDecNow))

        TSXSend("sky6Utils.ComputeAngularSeparation(" + targRA + ", " + targDec + ", " \
        + objRAj2k + ", " + objDecj2k +")")

        distInAS = 3600 * float(TSXSend("sky6Utils.dOut0"))

        distInAS = round(distInAS,2)

        #
        # If the click point is just "screen center", it's not a real object so report it
        # but don't do anything with it.
        #
        if (objName1 == "Sky Chart Center") or (objName1 == "Screen Center") or "Image Link Photo" in objName1:
            print("              Item #" + str(counter + 1) + " corresponds to the screen center or placed image.")

        else:
            #
            # This is the same idea as above. The Mouse Click Position isn't a real thing.
            #
            if (objName1 == "Mouse click position"):
                print("              Item #" + str(counter + 1) + " corresponds to the mouse position.")

            else:
                if (objName1 not in uniqueName):
                    if (objRANow in uniqueRA) and (objDecNow in uniqueDec):
                        starIndex = uniqueRA.index(objRANow)
                        otherNames.add(objName1.strip())

                        uniqueName.append(objName1)

                        uniqueRA.append(objRANow)
                        uniqueDec.append(objDecNow)
                        uniqueMag.append(objMag)
                        objMagValues.append(objMag)
                        uniqueDist.append(distInAS)

                        magLowerLimit = (uniqueMag[starIndex] - (0.25 * uniqueMag[starIndex]))
                        magUpperLimit = (uniqueMag[starIndex] + (0.25 * uniqueMag[starIndex]))

                        if (objMag > magLowerLimit) and (objMag < magUpperLimit):
                            print('             "' + objName1 + '" appears the same as "' + uniqueName[starIndex] +'"')
                        else:
                            print('             "' + objName1 + '" differs in magnitude from "' + uniqueName[starIndex] +'"')

                            outputStatement += ("                {0:<20} {1:<20} {2:<5} {3:<5} {4:<5}".format(objRAj2k, objDecj2k, \
                                objMag, distInAS, objName1)) + CR

                    else:
                        #
                        # Here is where the limit value gets used.
                        #

                        if (distInAS > limit):
                            print('             "' + objName1 + '" (' + str(distInAS) + ' AS) is too far away.')

                        else:
                            uniqueName.append(objName1)
                            uniqueRA.append(objRANow)
                            uniqueDec.append(objDecNow)
                            uniqueMag.append(objMag)
                            otherNames.add(objName1.strip())
                            objMagValues.append(objMag)
                            uniqueDist.append(distInAS)


                            if "Gaia" in objName1:
                                gaiaMag = str(objMag)
                                gaiaRA = objRAj2k
                                gaiaDec = objDecj2k
                             
    
                            print('             "' + objName1 + '" appears to be discrete.')
                            outputStatement += ("              {0:<20} {1:<20} {2:<5} {3:<5} {4:<5}".format(objRAj2k, objDecj2k, \
                                    objMag, distInAS, objName1)) + CR
                        
                else:
                    if (objRANow in uniqueRA) and (objDecNow in uniqueDec):
                        starIndex = uniqueRA.index(objRANow)
                        print('             "' + objName1 + '" appears to be a duplicate.')
                    elif (distInAS <= limit):
                        starIndex = uniqueName.index(objName1)
                        print('             "' + objName1 + '" shares a name with "' + uniqueName[starIndex] +'"' + " and is within resolution cutoff.")


                        # Need to do something here to keep the same name object that's closest as a hack for Gaia.
                        # Will need to turn distInAS into some sort of array so that you can compare the current 
                        # distance to previous ones.

                        if (distInAS < uniqueDist[starIndex]):

                            print('               -Closer than previous object with that name: ' + str(distInAS) + ' vs ' + str(uniqueDist[starIndex]))

                            uniqueName[starIndex] = objName1
                            uniqueRA[starIndex] = objRANow
                            uniqueDec[starIndex] = objDecNow
                            uniqueMag[starIndex] = objMag
                            objMagValues[starIndex] = objMag
                            uniqueDist[starIndex] = distInAS

                            if "Gaia" in objName1:
                                gaiaMag = str(objMag)
                                gaiaRA = objRAj2k
                                gaiaDec = objDecj2k


                            outputStatement += ("              {0:<20} {1:<20} {2:<5} {3:<5} {4:<5}".format(objRAj2k, objDecj2k, \
                                objMag, distInAS, objName1)) + CR

                        else:
                            print('               -Farther than previous object with that name: ' + str(distInAS) + ' AS vs ' + str(uniqueDist[starIndex]) + ' AS')

                    else:
                        starIndex = uniqueName.index(objName1)
                        print('             "' + objName1 + '" shares a name with "' + uniqueName[starIndex] +'"' + " but beyond distance cutoff")


                          
                
        counter = counter + 1   

    if not uniqueName:
        print("")
        writeNote("No associated items or names.")
        print("")
        timeStamp("Analysis of " + target + " complete.")
        print(" ") 
        return "None"

    else:
        print(" ")
        timeStamp("Object Details:")
        print("              {0:<20} {1:<20} {2:<5} {3:<5} {4:<5}".format("RA (j2k)", "Dec (j2k)", "Mag", "Dist", "Name"))
        print("              {0:<20} {1:<20} {2:<5} {3:<5} {4:<5}".format("--------", "---------", "---", "----", "----"))
        print(outputStatement)
    
        writeNote("Associated Names \n              " + '\n              '.join(otherNames))
        print(" ")    
        timeStamp("Analysis of " + target + " complete.")
        print(" ")    

        avgMag = round(statistics.mean(objMagValues), 2)

        return str(avgMag) + "," + gaiaMag + "," + gaiaRA + "," + gaiaDec + "," + "; ".join(otherNames) 


#####################################################
# Below is a set of functions for dealing with time #
#####################################################



def HMSToDec(H, M, S):
#
# Return zero-padded "pretty" H, M, S values and
# a decimal hour representation.
#


    if S == 60:
        S = 0
        M = M + 1
    prettyS = str(S)
    if len(prettyS) == 1:
        prettyS = "0" + prettyS
    
    if M == 60:
        M = 0
        H = H + 1
    prettyM = str(M)
    if len(prettyM) == 1:
        prettyM = "0" + prettyM

    prettyH = str(H)
    if len(prettyH) == 1:
        prettyH = "0" + prettyH
    
    M = float(M) / 60
    S = float(S) / 3600

    decTime = H + M + S

    return (prettyH, prettyM, prettyS, decTime)


def GregToJD(Y, M, D, decHours):
#
# Return Julian date & time from Gregorian units
#
# Borrowed from Bill Jefferies:
#       https://quasar.as.utexas.edu/BillInfo/JulianDatesG.html
#
    if (M == 1) or (M == 2):
        Y = Y - 1
        M = M + 12

    A = math.floor(Y/100)
    B = math.floor(A/4)
    C = math.floor(2-A+B)
    E = math.floor(365.25 *(Y + 4716))
    F = math.floor(30.6001 * (M + 1))
    JulianDate = C+D+E+F-1524.5 + (decHours / 24)

    return JulianDate

def JulToGreg(Julian):
#
# Return Gregorian date & time from a Julian number
#
# Borrowed from Bill Jefferies:
#       https://quasar.as.utexas.edu/BillInfo/JulianDatesG.html
#
    hours = (Julian - math.floor(Julian))
    
    if hours < 0.5: 
        hours = hours + 0.5
    else:
        hours = hours - 0.5

    hours = hours * 24

    cleanHours = math.floor(hours)

    Minutes = (hours - cleanHours) * 60

    cleanMinutes = math.floor(Minutes)

    cleanSeconds = round((Minutes - cleanMinutes) * 60)

    Q = Julian + 0.5
    Z = math.floor(Q)
    W = math.floor((Z - 1867216.25)/36524.25)
    X = math.floor(W/4)
    A = math.floor(Z+1+W-X)
    B = math.floor(A+1524)
    C = math.floor((B-122.1)/365.25)
    D = math.floor(365.25 * C)
    E = math.floor((B-D)/30.6001)
    F = math.floor(30.6001 * E)

    Day = math.floor(B-D-F+(Q-Z))

    Month = E - 1
    if Month > 12:
        Month = E - 13

    if (Month == 1) or (Month == 2):
        Year = C - 4715
    else:
        Year = C - 4716

    return (Year, Month, Day, cleanHours, cleanMinutes, cleanSeconds)

    

