#!/usr/bin/env python3
#
# Script to dump stars in several images or a folder into CSV files.
#
# It gives you the X, Y, j2k RA & Dec. It also gives you a wide
# variety of brightness measures and the catalog magnitude if available.
# 
# Finally, it gives you star proper names.
#
# Please note that results will depend on your catalogs. At the end of the day
# though, it's all just a crap shoot. If your rocket crashes, I will deny
# any and all responsibility.
#
# Ken Sturrock
# October 10, 2018
#

from library.PySkyX_ks import *

import time
import sys
import os
import statistics
import glob

argvLen = len(sys.argv)

if (argvLen == 1):
    timeStamp("ERROR. Please specify image names to process.")
    sys.exit()
 
if sys.platform == "win32":
    fileList = []
    print(sys.argv[1])
    
    for fileName in glob.glob(sys.argv[1]):
        fileList.append(fileName)
else:
    fileList = sys.argv
    fileList.pop(0)

fileNum = (len(fileList))


counter = 0



print("----------")
timeStamp("Starting to dump star lists from images.")

while (counter < fileNum):

    print("--------------------------------------------------------------------------------")
    print("Processing image: " + str(counter + 1) + " of " + str(fileNum))
    print("--------------------------------------------------------------------------------")

    dumpStars(fileList[counter])

    counter = counter + 1

print("----------")
timeStamp("Finished dumping.")
sys.exit()


