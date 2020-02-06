#!/usr/bin/env python3

#
# This takes my usual dark frames (for the ZWO ASI-183 and QSI-690).
#
# You can change the commands after "else" to do whatever you need.
#
# Ken Sturrock
# August 26, 2018
#

from library.PySkyX_ks import *

import time
import sys
import os

timeStamp("Starting Dark Frame Run.")

print("")

if str(TSXSend('ccdsoftCamera.PropStr("m_csObserver")')) ==  "Ken Sturrock":
    if str(TSXSend("SelectedHardware.cameraModel")) == "ASICamera": 
        print("Taking dark frames for ZWO ASI-183")
        takeDark("60", "9")
        takeDark("180", "9")
        takeDark("0", "9")

    if str(TSXSend("SelectedHardware.cameraModel")) == "QSI Camera  ":
        print("Taking dark frames for QSI-690")
        TSXSend('ccdsoftCamera.setPropStr("m_csExCameraMode", "Higher Image Quality")')
        print("Setting QSI Camera to high quality mode.")

        takeDark("60", "9")
        takeDark("180", "9")
        takeDark("240", "9")
        takeDark("600", "9")
        takeDark("0", "9")

        TSXSend('ccdsoftCamera.setPropStr("m_csExCameraMode", "Faster Image Downloads")')
        print("Setting QSI Camera to faster download mode.") 


else:
    print("Taking generic dark frame mixture: 1, 3 and 5 minutes plus bias.")
    takeDark("60", "9")
    takeDark("180", "9")
    takeDark("300", "9")
    takeDark("0", "9")

print("")

timeStamp("Finishing Dark Frame Run.")

