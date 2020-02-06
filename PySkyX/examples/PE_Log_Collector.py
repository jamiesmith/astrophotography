#!/usr/bin/env python3
#
# Code to automate the collection of tracking logs
#
# Takes five 25-minute tracking logs in the east and then five more to the west. Focuses between each log.
#
# This is setup for my system. It shoots images through the guide camera, but you can change that
# in each routine. It also uses AF2, which you could change to AF3.
#
# Ken Sturrock
# October 12, 2019
#

from library.PySkyX_ks import *

import time
import sys
import os

def doTrackingLogE():
 
    def wasteTime():
        for counter in range (1, 26):
            time.sleep(60)
            timeStamp( str(counter) + " minutes elapsed.")
       

    if TSXSend("SelectedHardware.mountModel") !=  "Telescope Mount Simulator":
        result = TSXSend("ccdsoftCamera.AtFocus2()")
        if "Error" in result:
            timeStamp("@Focus2 failed: " + result)
            softPark()

    TSXSend('sky6RASCOMTele.SlewToAzAlt(156, 47, "Start_Point")')

    time.sleep(30)

    takeImage("Guider", "3", "0", "NA")

    AGStar = findAGStar()
    if "Error" in AGStar:
        timeStamp("There was an error finding a star. Stopping script.")
        softPark()

    XCoord,YCoord = AGStar.split(",")
    startGuiding("3", "0", XCoord, YCoord)

    wasteTime()

    stopGuiding()

    TSXSend('sky6RASCOMTele.Jog(420, "E")')  

def doTrackingLogW():
 
    def wasteTime():
        for counter in range (1, 26):
            time.sleep(60)
            timeStamp( str(counter) + " minutes elapsed.")
       

    if TSXSend("SelectedHardware.mountModel") !=  "Telescope Mount Simulator":
        result = TSXSend("ccdsoftCamera.AtFocus2()")
        if "Error" in result:
            timeStamp("@Focus2 failed: " + result)
            softPark()

    TSXSend('sky6RASCOMTele.SlewToAzAlt(197, 47, "Start_Point")')

    time.sleep(30)

    takeImage("Guider", "3", "0", "NA")

    AGStar = findAGStar()
    if "Error" in AGStar:
        timeStamp("There was an error finding a star. Stopping script.")
        softPark()

    XCoord,YCoord = AGStar.split(",")
    startGuiding("3", "0", XCoord, YCoord)

    wasteTime()

    stopGuiding()

    TSXSend('sky6RASCOMTele.Jog(420, "W")')  


garbage = input("Please ensure that PEC is deactivated.")
garbage = input("Please ensure that ProTrack is deactivated.")
garbage = input("Please ensure that guiding corrections are disabled.")



timeStamp("Starting East tracking log collection.")

TSXSend('sky6RASCOMTele.SlewToAzAlt(156, 47, "Start_Point")')

for runs in range(1, 6):
    print(" ")
    timeStamp("Collecting Log: " + str(runs))
    doTrackingLogE()
    timeStamp("Finishing Log.")
    print(" ")

timeStamp("Starting West tracking log collection.")

TSXSend('sky6RASCOMTele.SlewToAzAlt(197, 47, "Start_Point")')

for runs in range(1, 6):
    print(" ")
    timeStamp("Collecting Log: " + str(runs))
    doTrackingLogW()
    timeStamp("Finishing Log.")
    print(" ")



softPark()

timeStamp("Finished.")

