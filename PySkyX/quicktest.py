#!/usr/bin/env python3


from library.PySkyX_ks import *

# Import the time library so that we can use the sleep command to
# introduce delays.
#
import time

def getAndPrintAltAz():
    TSXSend("sky6RASCOMTele.GetAzAlt()")
    mntAz = round(float(TSXSend("sky6RASCOMTele.dAz")), 2)
    mntAlt = round(float(TSXSend("sky6RASCOMTele.dAlt")), 2) 
    writeNote("Mount currently at: " + str(mntAz)  + " az., " + str(mntAlt) + " alt.")

def slewToAltAz(alt, az):

    slewCount = 0
    
    getAndPrintAltAz()
    
    TSXSend("sky6RASCOMTele.Asynchronous = true")
    writeNote("Slewing to alt/az: " + str(alt) + " / " + str(az))
    TSXSend("sky6RASCOMTele.SlewToAzAlt(" + str(az) + ", " + str(alt) + ", 'zzz')")

    while TSXSend("sky6RASCOMTele.IsSlewComplete") == "0":
        if slewCount > 119:
            print("    ERROR: Mount appears stuck!")
            timeStamp("Sending abort command.")
            sky6RASCOMTele.Abort()
            if TSXSend("SelectedHardware.mountModel") !=  "Telescope Mount Simulator":
                time.sleep(5)
                timeStamp("Trying to stop sidereal motor.")
                TSXSend("sky6RASCOMTele.SetTracking(0, 1, 0 ,0)")
            timeStamp("Stopping script.")    
            sys.exit()
        else:
            writeNote("Slew in progress.")
            slewCount = slewCount + 1
            time.sleep(10)

    if "Process aborted." in TSXSend("sky6RASCOMTele.IsSlewComplete"):
        timeStamp("Script Aborted.")
        sys.exit()

    TSXSend("sky6RASCOMTele.Asynchronous = false")
    writeNote(TSXSend("sky6RASCOMTele.LastSlewError"))

slewToAltAz(70, 70)

slewToAltAz(10, 90)

getAndPrintAltAz()