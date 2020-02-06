#!/usr/bin/env python3
#
# This is a simple example to demonstrate how to slew, focus, handle
# guiding, take images and park.
#
# You can see an example run in the documents subfolder.
#
# Ken Sturrock
# March 24, 2018
#

# Import all the SkyX functions from the PySkyX_ks library located
# in the subdirectory called "library".
#
from library.PySkyX_ks import *

# Import the time library so that we can use the sleep command to
# introduce delays.
#
import time

# Slew to the star Subra. Note the quotes.
#
slew("subra")

# Use @Focus3 to focus on the field with Subra through the first filter in 
# the wheel (filter zero). The "NoRTZ" (No Return To Zero) tells the focus 
# routine *not* to (potentially) re-slew back to target. It isn't necessary 
# here because this is an initial focus and we haven't dithered.
#
if atFocus3("NoRTZ", "0") == "Fail":
    timeStamp("There was an error on initial focus. Stopping script.")
    softPark()

# Take a picture through the guider so that we have somthing to analyze
# and find a guide star. The exposure is five seconds with a zero second delay.
# The NA indicates that there is no filter wheel.
#
takeImage("Guider", "5", "0", "NA")

# Find a guide star in the guider image that we just took. Put the coordinates
# into the variable AGStar. Note, nothing fancy happens if there is an error. 
# If there is no guide star, tough luck.
#
AGStar = findAGStar()
if "Error" in AGStar:
    softPark()

# The X,Y coordinates for the guide star came packaged as a single variable
# with a comma, so we're going to break them out with split into two variables.
#
XCoord,YCoord = AGStar.split(",")

# Tell SkyX to start guiding on the star that we identified above with a five second
# exposure and no delay.
#
startGuiding("5", "0", XCoord, YCoord)

# Wait 30 seconds to allow guiding a chance to settle.
#
time.sleep(30)

# Take four five minute images through the first four filters in the wheel (0, 1, 2, 3)
# with a one second delay. Note the quotes.
#
takeImage("Imager", "300", "1", "0")
takeImage("Imager", "300", "1", "1")
takeImage("Imager", "300", "1", "2")
takeImage("Imager", "300", "1", "3")

# Stop guiding
#
stopGuiding()

# This will point the mount towards the appropriate pole, disconnect the cameras and
# turn off the sidereal drive.
#
hardPark()


