#!/usr/bin/env python3

import time
import sys
import os
import glob
import serial

from library.PySkyX_ks import *
from library.flatman_ctl import *



myFMPanel = FlatMan("COM10", False, model=FLIPFLAP)
myFMPanel.Connect()
myFMPanel.Light("OFF")
time.sleep(10)
myFMPanel.Open()
time.sleep(10)
myFMPanel.Light("ON")
time.sleep(10)
myFMPanel.Brightness(255)
time.sleep(10)

myFMPanel.Close()
myFMPanel.Light("OFF")
myFMPanel.Disconnect()
