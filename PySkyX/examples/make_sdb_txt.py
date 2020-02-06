#!/usr/bin/env python3

# 
# Take a "reduced" CSV of observations and create a text file for 
# easy import into the SkyX database creation utility.
#
# Ken Sturrock
# December 02, 2019
#

from library.PySkyX_ks import *

import sys
import os
import csv
import statistics

def writeHeader():
#
# This just writes a header for the text
# file to pre-identify columns when
# creating the SDB.
#


    outFile.write('''
<?xml version="1.0"?>
<!DOCTYPE TheSkyDatabase>
<TheSkyDatabaseHeader version="1.00">
    <identifier>WDS-KS</identifier>
    <sdbDescription>&lt;Add Description&gt;</sdbDescription>
    <searchPrefix></searchPrefix>
    <specialSDB>0</specialSDB>
    <plotObjects>1</plotObjects>
    <plotLabels>0</plotLabels>
    <plotOrder>0</plotOrder>
    <searchable>1</searchable>
    <clickIdentify>1</clickIdentify>
    <epoch>        2000.0</epoch>
    <referenceFrame>0</referenceFrame>
    <crossReferenceType>0</crossReferenceType>
    <defaultMaxFOV>      360.0000</defaultMaxFOV>
    <defaultObjectType index="55" description="Reference Point"/>
    <raHours colBeg="22" colEnd="44"/>
    <decSign colBeg="46" colEnd="46"/>
    <decDegrees colBeg="47" colEnd="69"/>
    <labelOrSearch colBeg="1" colEnd="20"/>
    <sampleColumnHeader>
;abel/Search         RA Hours                DDec Degrees             
;------------------- ----------------------- ------------------------
</sampleColumnHeader>
</TheSkyDatabaseHeader>

''')




# Main Program Start ###########################

targets = []
comps = []
priRAs = []
priDecs = []
secRAs = []
secDecs = []
CR = "\n"

#
# Check for and platform rectify the path.
# It isn't necessary here, but old habits die hard.
#
if (len(sys.argv) == 1):
    timeStamp("ERROR. Please specify CSV file to process.")
    sys.exit()

fileName = sys.argv[1]

newPathName = flipPath(fileName)


dirName,fileName = os.path.split(newPathName)

dirName = dirName + "/"

#
# Read through the CVS and put the values into lists
#
# The "Set Trick" is used to create a unique list of targets
# which are then turned back into a list for consistant 
# handling.
#
print("----------")
timeStamp("Reading file: " + newPathName)
print("----------")

with open(newPathName) as csvfile:
#
# Screen out anything bogus or dubious
#
    readCSV = csv.reader(csvfile, delimiter=',')
    for row in readCSV:
        if (row[3] != "X ") and (row[3] != " P-RA (j2k)"):
            targets.append(row[0])
            comps.append(row[2])
            priRAs.append(row[3])
            priDecs.append(row[4])
            secRAs.append(row[5])
            secDecs.append(row[6])

outFile = open(dirName + "txt_for_SDB.txt","w")

writeHeader()

for index in range(len(targets)):

    if "-" in comps[index]:
        priComp,secComp = comps[index].split("-")
    else:
        priComp,secComp = comps[index][:1], comps[index][1:]

    if not priComp:
        priComp = "p"
        secComp = "s"

    #
    # the following blocks tear apart the coordinates and
    # re-assemble them in a very consistantly spaced
    # manner so the column edges match.
    #
    WholeNumber, Fraction = priRAs[index].split(".")
    WholeNumber = WholeNumber.rjust(2, "0")
    Fraction = Fraction.ljust(20, "0")
    priRAs[index] = WholeNumber + "." + Fraction

    WholeNumber, Fraction = secRAs[index].split(".")
    WholeNumber = WholeNumber.rjust(2, "0")
    Fraction = Fraction.ljust(20, "0")
    secRAs[index] = WholeNumber + "." + Fraction

    WholeNumber, Fraction = priDecs[index].split(".")
    if "-" in WholeNumber:
        WholeNumber = "-" + WholeNumber.strip("-").rjust(2, "0")
    else:
        WholeNumber = "+" + WholeNumber.strip("-").rjust(2, "0")
    Fraction = Fraction.ljust(20, "0")
    priDecs[index] = WholeNumber + "." + Fraction

    WholeNumber, Fraction = secDecs[index].split(".")
    if "-" in WholeNumber:
        WholeNumber = "-" + WholeNumber.strip("-").rjust(2, "0")
    else:
        WholeNumber = "+" + WholeNumber.strip("-").rjust(2, "0")
    Fraction = Fraction.ljust(20, "0")
    secDecs[index] = WholeNumber + "." + Fraction

    priTarget = (targets[index].replace("WDS", "(m)") + " (" + priComp + ")")
    secTarget = (targets[index].replace("WDS", "(m)") + " (" + secComp + ")")
                
    outFile.write(priTarget.ljust(20) + " " + priRAs[index] + " " + priDecs[index] + CR)
    outFile.write(secTarget.ljust(20) + " " + secRAs[index] + " " + secDecs[index] + CR)

timeStamp("Wrote to file: " + dirName + "txt_for_SDB.txt")
print("----------")
