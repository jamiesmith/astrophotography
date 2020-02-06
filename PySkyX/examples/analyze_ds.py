#!/usr/bin/env python3
#
# Script to try to measure double stars.
#
# Give it a path, or paths.
#
# Wildcards should work but Windows users beware.
#
# Results go into a CSV in the first image's directory.
#
# Don't trust it.
#
# Ken Sturrock
# August 24, 2019
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
timeStamp("Starting to analyze double star images.")

dirName,fileName = os.path.split(fileList[0])

csvFile = dirName + "/" + "ds_measures.csv"
outFile = open(csvFile, "w")
outFile.write("Discoverer, WDS, Components, P-RA (j2k), P-Dec (j2k), S-RA (j2k), S-Dec (j2k), Catalog PA, Catalog Separation, Image PA, Image Separation, Rel. Sep. Dist. \n")

while (counter < fileNum):

    print("--------------------------------------------------------------------------------")
    print("Processing image: " + str(counter + 1) + " of " + str(fileNum))
    print("--------------------------------------------------------------------------------")

    dsResults = dsProcess(fileList[counter])

    if "Fail" not in dsResults:
        outFile.write(dsResults + "\n")
    else:
        timeStamp("Failure.")
        outFile.write(dsResults + "\n")


    counter = counter + 1

outFile.close()

print("----------")
timeStamp("Finished analyzing double star images.")
