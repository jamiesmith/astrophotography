#!/usr/bin/env python3
#
# Jamie Smith
# 
#

from library.PySkyX_ks import *
from library.PySkyX_jrs import *

import os
from slack_sdk import WebClient 
from slack_sdk.errors import SlackApiError 

import time
import socket
import sys
import os
import random
import math
import pathlib
import glob
import statistics
import csv

FILTER_NAMES = []
FILTER_NAMES = nameFilters("Local")
NUM_FILTERS = len(FILTER_NAMES)

def promptToExit():
    done = input("Press enter to exit")

def sendToSlack(channel, message):
    # From https://python.plainenglish.io/lets-create-a-slackbot-cause-why-not-2972474bf5c1
    # install sdk via:
    # pip3 install slack_sdk
    #
    slack_token = os.environ.get('SLACK_BOT_NOTIFICATION_TOKEN')

    # Creating an instance of the Webclient class
    client = WebClient(token=slack_token)

    try:
        response = client.chat_postMessage(
            channel=channel,
            text=message)
	
    except SlackApiError as e:
    	assert e.response["error"]


def abort(message):
    writeNote("ERROR: " + message)
    print("aborting")
    promptToExit()
    sys.exit()


def getFilterAtSlot(slot):
    return FILTER_NAMES[slot]

def getIndexForFilter(filterName):        
    i = 0
    
    while i < len(FILTER_NAMES):
        if (filterName[0].upper() == FILTER_NAMES[i][0].upper()):
            return i
            
        i += 1
        
    # If we got here then the filter wasn't found and there's an issue.  
    print(f"ERROR! filter slot for {filterName} not found, aborting")
    exit()

LUM	   = getIndexForFilter("LUM")
RED	   = getIndexForFilter("RED")
GREEN  = getIndexForFilter("GREEN")
BLUE   = getIndexForFilter("BLUE")
SII	   = getIndexForFilter("SII")
HA	   = getIndexForFilter("HA")
OIII   = getIndexForFilter("OIII")

def printFilterSettings(caption, settings):
    print(str(caption))
    rowNum = 0    

    for row in settings:
        print(f"\t{getFilterAtSlot(rowNum)}", end=': ')
        for elem in row:
            print(elem, end=' ')
        print()
        
        rowNum += 1


def csv2settings(filename):  

    csvArray = list(csv.reader(open(filename)))
    
    settings = [[0]*(len(csvArray[0]) - 1)] * (len(csvArray) - 1)
        
    rowNum = 1
    
    while rowNum <= NUM_FILTERS:
        row = csvArray[rowNum]
        settings[getIndexForFilter(row[0])] = row[1:(len(row))]
        rowNum += 1
        
        
    return settings

def getFilterSetting(settings, filterSlot, binning):
    return settings[filterSlot][binning - 1]

def getFlatExposureForFilter(filterNum, binning):
    return float(getFilterSetting(FLAT_DURATION, filterNum, binning))

def getBrightnessForFilter(filterNum, binning):
    return int(getFilterSetting(FLAT_PANEL_BRIGHTNESS, filterNum, binning))

def promptForValueWithDefault(text, defaultValue):
	value = input(text + "(default is <" + str(defaultValue) + ">)")
	if value == "":
		value = str(defaultValue)
		
	return value


## ------------------------------------------------------
## Reused Flat Operations
## ------------------------------------------------------

def getImageBrightness():
    TSXSend("ccdsoftCameraImage.AttachToActiveImager()")

    imageDepth = int(TSXSend('ccdsoftCameraImage.FITSKeyword("BITPIX")'))

    if TSXSend("ccdsoftCamera.ImageUseDigitizedSkySurvey") == "1":
        avgPixelValue = round(random.uniform(20000, 40000), 0)
        writeNote("DSS images in use. Random ADU value assigned: " + str(avgPixelValue))
    else:
        avgPixelValue = float(TSXSend("ccdsoftCameraImage.averagePixelValue()"))

    avgPixelValue = int(round(avgPixelValue, 0))
    fullWell = int(math.pow (2, imageDepth))
    brightness = avgPixelValue / fullWell

    brightness = str(round(brightness, 2))

    return str(brightness) + "," + str(avgPixelValue)


def isExposureInRange(brightness, desiredBrightness, tolerance):        
    return (abs(float(desiredBrightness) - float(brightness)) <= float(tolerance))

    
def shootFlat(exposureTime, binning = 1):
    TSXSend("ccdsoftCamera.Asynchronous = false")
    TSXSend("ccdsoftCamera.AutoSaveOn = true")
    TSXSend("ccdsoftCamera.ImageReduction = 0")
    TSXSend("ccdsoftCamera.Frame = 4")
    TSXSend("ccdsoftCamera.BinX = " + str(binning))
    TSXSend("ccdsoftCamera.BinY = " + str(binning))        
    TSXSend("ccdsoftCamera.Delay = 1")
    TSXSend("ccdsoftCamera.Subframe = false")
    TSXSend("ccdsoftCamera.ExposureTime = " + str(exposureTime))
    TSXSend("ccdsoftCamera.TakeImage()")


def calculateOptimalFlatExposure(filterNum, startingExposure = 1, binning = 1):

    # Main Operation
    # Target brightness is .45
    #
    
    targetBrightness = 0.45
    tolerance = .01
    
    writeNote("Calculating flats for " + str(targetBrightness) + " +/- " + str(tolerance))
    
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
        
    exposureTime = startingExposure

    # Bootstrap an exposure
    #
    shootFlat(exposureTime, binning)
    brightness,adu = getImageBrightness().split(",")
    
    writeNote("exposure: [" + str(exposureTime) + "] yields brightness of [" + str(brightness) + "] at ADU " + adu)
    while (not isExposureInRange(brightness, targetBrightness, tolerance)):
        # Adjust the brightness.  Big or small changes?
        #
        message = ""
        writeNote("exposureTime      : " + str(exposureTime))
        writeNote("brightness        : " + str(brightness))
        writeNote("targetBrightness  : " + str(targetBrightness))
        lastExposure = exposureTime
        
        if (float(brightness) > (1.5 * targetBrightness) or (float(brightness) < (.75 * targetBrightness))):
            if (float(brightness) > (targetBrightness)):
                message= "WAY TOO BRIGHT "
            else:     
                message= "WAY TOO DIM "

            exposureTime = round((exposureTime * (targetBrightness / float(brightness))), 3)
            message += "changing exposure to " + str(exposureTime)
            

        # Finer granularity
        #        
        elif (float(brightness) > targetBrightness):
            # reduce it by 5%
            exposureTime = round(exposureTime * .95, 3)
            message += "decreasing exposure to " + str(exposureTime)

        elif (float(brightness) > targetBrightness):
            # increase it by 2%  - different on purpose, so we don't flip flop.
            exposureTime = round(exposureTime * 1.02, 3)
            message += "increasing exposure to " + str(exposureTime)

            
        writeNote("new exposureTime      : " + str(exposureTime))

        # If the last exposure time is the same as the new one we have a problem.
        #
        if (lastExposure == exposureTime):
            writeNote("WARNING: Exposure of " + str(exposureTime) + " seems to be the best we can do")
            break
            
        writeNote("   " + message)
        shootFlat(exposureTime, binning)
        brightness,adu = getImageBrightness().split(",")
            
            
        writeNote("-----------")


    # Theoretically we should have been in range
    # 
    writeNote("#######################################################")
    writeNote("Target exposure time of " + str(exposureTime) + " seems to yield an image of " + adu + " for filter " + filterNum)
    writeNote("#######################################################")

    return exposureTime   

def takeFauxDark(exposure, numFrames):
#
# Specify exposure duration & qualtity. 
# If exposure is zero, take a bias.
#
    timeStamp("Taking faux dark frames.")
    
    asFormatLight = ":t-:e-:b-:i-:f-:a_:c-:q"
    asFormatDark = ":i_:b_:e_:q_:c"
    asFormatBias = ":i_:b_:e_:c_"
    asFormatFlat = ":i_:f_:e_"
    
    saveLightFormat = TSXSend('ccdsoftCamera.PropStr("m_csCustomFileNameLight")')

    if exposure == "0":
        writeNote("Setting frame type to bias.")
        TSXSend("ccdsoftCamera.Frame = 1")
        frameType = "Bias"
        frameFormat = TSXSend('ccdsoftCamera.PropStr("m_csCustomFileNameBias")')
        
    else:
        writeNote("Setting frame type to dark.")
        TSXSend("ccdsoftCamera.Frame = 1")
        writeNote(f"Setting exposure to {exposure} seconds.")
        TSXSend("ccdsoftCamera.ExposureTime = " + exposure)
        frameType = "Dark"
        frameFormat = TSXSend('ccdsoftCamera.PropStr("m_csCustomFileNameDark")')

    counter = 1

    TSXSend('ccdsoftCamera.setPropStr("m_csCustomFileNameLight", "' + frameFormat + '")')
    
    while (counter <= int(numFrames)):
        timeStamp("Taking frame: " + str(counter) + " of " + numFrames + ".")
        TSXSend("ccdsoftCamera.TakeImage()")
        counter = counter + 1
        imgPath = getActiveImagePath()

        TSXSend('ccdsoftCameraImage.Path = "' + imgPath + '"')
        TSXSend("ccdsoftCameraImage.Open()")
        TSXSend('ccdsoftCameraImage.setFITSKeyword("IMAGETYP", "' + frameType +' Frame")')
        TSXSend("ccdsoftCameraImage.Save()")
        TSXSend("ccdsoftCameraImage.Close()")

        renamePath = imgPath.replace("Light", frameType)
        os.rename(imgPath, renamePath)
        timeStamp(imgPath + " " + renamePath)       
        

    TSXSend('ccdsoftCamera.setPropStr("m_csCustomFileNameLight", "' + saveLightFormat + '")')
    timeStamp("Finished.")


def takeFlats(filterNum, exposure, numFlats, takeDarks = "N", binning = 1, targetBrightness = 0.45, tolerance = .02):

# This function takes an appropriately exposed flat.
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
    # Main operation
    #
    timeStamp("Taking flat frames.")
    writeNote("     PLAN: " + numFlats + " (" + str(exposure) + ") second flat frame(s) takeDarks [" + takeDarks + "]")

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

    counter = 1

    while (counter <= int(numFlats)):
        # Take a flat
        #
        timeStamp("Taking flat image: " + str(counter) + " of " + str(numFlats) + ".")
        shootFlat(exposure, binning)
        
        # Check the exposure/brightness
        #
        brightness,adu = getImageBrightness().split(",")
        brightness = float(brightness)
        adu = int(adu)
        
        imgPath = TSXSend("ccdsoftCameraImage.Path")
        timeStamp(imgPath)
        
        if isExposureInRange(brightness = float(brightness), desiredBrightness = targetBrightness, tolerance = tolerance):
            writeNote("Brightness of " + str(brightness) + " is good enough, appending adu " + str(adu))
            
            # rename the image w/ ADU
            #
            pieces = imgPath.split(".")
            pieces[-2] += "-" + str(adu) + "adu"
            renamePath = ".".join(pieces)
            os.rename(imgPath, renamePath)
            
            counter += 1
                            
        else:
            # delete
            #            
            if os.path.exists(imgPath):
                writeNote("Brightness of " + str(brightness) + " is NOT good enough, removing image")
                
                # I want to see if this helps when they're not good enough, possible drift
                #
                # setFlatPanel(filterNum, binning)
                os.remove(imgPath)            

        timeStamp("")

    if takeDarks.upper() == "DARKS" or takeDarks.upper() == "Y":
        TSXSend("ccdsoftCamera.Frame = 3")

        counter = 1
        while (counter <= int(numFlats)):
            timeStamp("Taking matched (" + str(exposure) + ") dark image: " + str(counter) + " of " + str(numFlats) + ".")
            TSXSend("ccdsoftCamera.TakeImage()")
            counter = counter + 1
    else:
        writeNote("No automatic darks requested.")

    timeStamp("Finished.")
    return str(exposure)	

FLAT_PANEL_BRIGHTNESS = csv2settings("per_filter_flatman_settings.csv")
FLAT_DURATION         = csv2settings("per_filter_exposure_settings.csv")





