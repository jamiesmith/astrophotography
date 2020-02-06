#!/usr/bin/env python3

from library.PySkyX_ks import *

# This just shows how to manipulate remote cameras

slewRemote("10.0.1.11:3040","hip46774")
atFocusRemote("10.0.1.11:3040", "Imager", "Two", "0")
takeImageRemote("10.0.1.11:3040", "Imager", "5", "1", "0")
takeImageRemote("10.0.1.11:3040", "Guider", "10", "1", "NA")
remoteImageDone("10.0.1.11:3040", "Imager")
remoteImageDone("10.0.1.11:3040", "Guider")
getStatsRemote("10.0.1.11:3040", "Guider")
