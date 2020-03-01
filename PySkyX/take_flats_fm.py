#!/usr/bin/env python3

#
# This takes calibration frames for an entire wheel of filters and uses the Alnitak
# FlatMan panel. 
#
# The idea is that the regular calibration (flat, dark) routines in my library
# will autoscale the exposure duration but, if you can set the panel brighter or
# dimmer then it will make life easier and faster.
#
# It controls the panel by means of Rodolphe Pineau's Python-based scriptable
# control module (available from his file lbrary on the Bisque support site). 
# In addition to the Python module, Rodolphe wrote a GUI control program for the 
# Macintosh. You can download it (and pay him) here:
#
# http://www.rti-zone.org
#
# After you download Rodolphe's control file (which I put in the library subfolder of my 
# code because it was easy), you'll have to install the PySerial library. There are several ways
# to do this, so you'll need to hit google and figure it out. I used the "pip" method.
#
# Before you use this script, you'll also need to verify the filter slots and flatman settings for 
# each frame. The setting are in the function that starts with "Def FPAdjust(():"
# For example, I usually shoot LRGB filters at a brightness of 50 and NB at 250. My ASI-183 is 
# not sensitive in the red channel, however, so I boost that way up.
#
# When you run this script, answer the question for the number of filters in the wheel and the 
# number of calibration frames you want per filter. Then verify the serial port used by the flatman.
#
# It will shoot flats first. Then, if necessary, SkyX will prompt you to
# cover the OTA so that it can shoot darks. The flatman will be turned off and should
# work as a shutter if you have decent light seal.
#
# Ken Sturrock
# August 26, 2018
#

import time
import sys
import os
import glob
import serial

from library.PySkyX_ks import *
from library.flatman_ctl import *

LUM	   = 0
RED	   = 1
GREEN  = 2
BLUE   = 3
SII	   = 4
HA	   = 5
OIII   = 6

def getStartingExposureTime(filterNum, binning):
	
	print("	 ----")
	writeNote("Getting the starting exposure for filter: " + str(filCounter))
	print("	 ----")
	exposure = 0

	if filCounter == LUM:
		# .56, .44, .87, .42
		exposure = .56

	if filCounter == RED:
		# 1.33, .87, .55, .36
		exposure = 1.33
		
	if filCounter == GREEN:
		# 1, .58, .46, .46
		exposure = 1.0

	if filCounter == BLUE:
		# .64, .36, .28, .28
		exposure = 0.64

	if filCounter == SII:
		# 23, 5.56, 2.5, 1.2
		exposure = 23.0

	if filCounter == HA:
		# 5.4, 1.16, .63, .61	
		exposure = 5.4
	 
	if filCounter == OIII:
		# 1.33, .87, .55, .36
		exposure = 1.33
	
	writeNote("using starting exposure time of " + str(exposure))
	return exposure

def FPAdjust():
	print("	 ----")
	writeNote("Adjusting the panel for filter: " + str(filCounter))
	print("	 ----")

	if str(TSXSend('ccdsoftCamera.PropStr("m_csObserver")')) ==  "Ken Sturrock":
		#
		# The following two sections are customized for my cameras
		#
		if str(TSXSend("SelectedHardware.cameraModel")) == "ASICamera": 
			writeNote("Setting Panel for Ken's ASI-183")

			if filCounter == LUM:
				writeNote("Setting panel to 40.")
				myFMPanel.Brightness(40)
	
			if filCounter == RED:
				writeNote("Setting panel to 200.")
				myFMPanel.Brightness(200)
	
			if filCounter == GREEN:
				writeNote("Setting panel to 50.")
				myFMPanel.Brightness(50)
		
			if filCounter == BLUE:
				writeNote("Setting panel to 50.")
				myFMPanel.Brightness(50)
		
			if filCounter == SII:
				writeNote("Setting panel to 50.")
				myFMPanel.Brightness(50)

			if filCounter == HA:
				writeNote("Setting panel to 50.")
				myFMPanel.Brightness(50)
			 
			if filCounter == OIII:
				writeNote("Setting panel to 50.")
				myFMPanel.Brightness(50)

		if TSXSend("SelectedHardware.cameraModel") == "QSI Camera  ":
			writeNote("Setting panel for Ken's QSI-690")


			if filCounter == 0:
				writeNote("Setting panel to 40.")
				myFMPanel.Brightness(40)
	
			if filCounter == 1:
				writeNote("Setting panel to 50.")
				myFMPanel.Brightness(50)
	
			if filCounter == 2:
				writeNote("Setting panel to 50.")
				myFMPanel.Brightness(50)
		
			if filCounter == 3:
				writeNote("Setting panel to 50.")
				myFMPanel.Brightness(50)
		
			if filCounter == 4:
				writeNote("Setting panel to 250.")
				myFMPanel.Brightness(250)
		
			if filCounter == 5:
				writeNote("Setting panel to 200.")
				myFMPanel.Brightness(200)
		
			if filCounter == 6:
				writeNote("Setting panel to 250.")
				myFMPanel.Brightness(250)
		
			if filCounter == 7:
				writeNote("Setting panel to 250.")
				myFMPanel.Brightness(250)

	else:
		print("Camera detected as " + str(TSXSend("SelectedHardware.cameraModel")))
	
		if filCounter == LUM:
			# 30, 15, 8, 8
			writeNote("Setting panel to 30.")
			myFMPanel.Brightness(30)

		if filCounter == RED:
			# 255, 55, 38, 32
			writeNote("Setting panel to 255.")
			myFMPanel.Brightness(255)

		if filCounter == GREEN:
			# 60, 30, 20, 15
			writeNote("Setting panel to 60.")
			myFMPanel.Brightness(60)
	
		if filCounter == BLUE:
			# 60, 30, 20, 15
			writeNote("Setting panel to 60.")
			myFMPanel.Brightness(60)
	
		if filCounter == SII:
			# 255, 255, 255, 255
			writeNote("Setting panel to 255.")
			myFMPanel.Brightness(255)

		if filCounter == HA:
			# 255, 255, 255, 255
			writeNote("Setting panel to 255.")
			myFMPanel.Brightness(255)
		 
		if filCounter == OIII:
			# 255, 255, 150, 65
			writeNote("Setting panel to 255.")
			myFMPanel.Brightness(255)		 

expUsed = []

timeStamp("Starting Calibration run.")

print("")

filStart = input("	INPUT: Starting filter number (first slot is 0 (zero))? ")
numFilters = input("	INPUT: How many filters to calibrate? ")
numFrames = input("	INPUT: How many frames per filter? ")

print("")

FMSerialPort = "COM10"

# Setting up the panel

myFMPanel = FlatMan(FMSerialPort, False, model=FLIPFLAP)

print("")
writeNote("Attempting to connect to: " + FMSerialPort)

myFMPanel.Connect()
myFMPanel.Close()

writeNote("Switching panel on.")

myFMPanel.Light("ON")

# Moving on to the real calibration section

writeNote("Calibrating " + numFilters + " filters.")


oldASFormula = TSXSend('ccdsoftCamera.PropStr("m_csCustomFileNameFlat")')
writeNote("Changing the flat Autosave name formula from " + oldASFormula + " to :i_:f_:e_ ")
TSXSend('ccdsoftCamera.setPropStr("m_csCustomFileNameFlat", ":i_:f_:e_")')

numFilters = int(numFilters)
filCounter = int(filStart)
target = numFilters + filCounter
while (filCounter < target):
	
	FPAdjust()
	expUsed.append(takeFlat(str(filCounter), getStartingExposureTime(filCounter, 1), str(numFrames), "No"))
	filCounter = filCounter + 1

writeNote("Restoring previous flat Autosave name formula.")
TSXSend('ccdsoftCamera.setPropStr("m_csCustomFileNameFlat", "' + oldASFormula + '")')


writeNote("Turning off Flatman panel.")
myFMPanel.Light("OFF")
myFMPanel.Disconnect()
print("")
timeStamp("	 NOTE: Taking matching dark frames.")
print("")
writeNote("If prompted, please cover OTA or turn off flat panel light.")
print("")


oldASFormula = TSXSend('ccdsoftCamera.PropStr("m_csCustomFileNameDark")')
writeNote("Changing the dark Autosave name formula from " + oldASFormula + " to :i_:f_:e_ ")
TSXSend('ccdsoftCamera.setPropStr("m_csCustomFileNameDark", ":i_:f_:e_")')

numFilters = int(numFilters)
filCounter = int(filStart)
arrayCounter = 0

target = numFilters + filCounter

while (filCounter < target):
	TSXSend("ccdsoftCamera.FilterIndexZeroBased = " + str(filCounter))
	takeDark(expUsed[arrayCounter], numFrames)
	filCounter = filCounter + 1
	arrayCounter = arrayCounter + 1

writeNote("Restoring previous dark Autosave name formula.")
TSXSend('ccdsoftCamera.setPropStr("m_csCustomFileNameDark", "' + oldASFormula + '")')

print("")

if str(TSXSend('ccdsoftCamera.PropStr("m_csObserver")')) ==  "Ken Sturrock":
	if TSXSend("SelectedHardware.cameraModel") == "QSI Camera  ":
		TSXSend('ccdsoftCamera.setPropStr("m_csExCameraMode", "Faster Image Downloads")')
		writeNote("Setting QSI Camera to faster download mode.")	

timeStamp("Finished Calibration Run.")
myFMPanel.Light("OFF")
myFMPanel.Disconnect()


done = input("Press enter to exit")
