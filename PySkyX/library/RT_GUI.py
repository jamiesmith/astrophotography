#!/usr/bin/env python3

#
# Nasty GUI front end to collect run_target-2 style variables for an imaging run.
#
# This was my first attempt at writing GUI code in Python and is full of dubious practices.
#
# Ken Sturrock
# November 16, 2019
#

from tkinter import Tk, Frame, Toplevel, Label, Entry, StringVar, IntVar, Button, Text, Radiobutton
from library.PySkyX_ks import *

import time
import sys
import socket
import os
import datetime

def runGUI():

    themeColor = themeChk()

    def buildCountField(index, filterName):
    #
    # Taken from an example by Bryan Oakley at: 
    #                   https://stackoverflow.com/questions/43360921/dont-understand-tkinter-entry-box-validatiom
    #
        def do_validation(enteredValue):
            return enteredValue == "" or enteredValue.isnumeric()

        vcmd = (filterMatrix.register(do_validation), '%P')

        countEntryField.append(StringVar())

        # This is really going to be an integer, but if I set it to integer than the default value 
        # becomes zero and I might want it blank or something else
        countFormVals.append(StringVar()) 
    
        Label(filterMatrix, text=filterName).grid(column=1, row=index + 2)
        countEntryField[index] = Entry(filterMatrix, width=3, validate='key', validatecommand=vcmd, textvariable=countFormVals[index]).grid(column=2, row=index + 2)


    def buildExposureField(index, filterName):
    
        def do_validation(enteredValue):
            return enteredValue == "" or enteredValue.isnumeric()

        vcmd = (filterMatrix.register(do_validation), '%P')

        expEntryField.append(StringVar())

        expFormVals.append(StringVar()) 
    
        Label(filterMatrix, text="x").grid(column=3, row=index + 2)
        expEntryField[index] = Entry(filterMatrix, width=4, validate='key', validatecommand=vcmd, textvariable=expFormVals[index]).grid(column=4, row=index + 2)


    def buildRepeatField(index, filterName):
    
        def do_validation(enteredValue):
            return enteredValue == "" or enteredValue.isnumeric()

        vcmd = (filterMatrix.register(do_validation), '%P')

        repEntryField.append(StringVar())

        repFormVals.append(StringVar()) 
    
        Label(filterMatrix, text="x").grid(column=5, row=index + 2)
        repEntryField[index] = Entry(filterMatrix, width=2, validate='key', validatecommand=vcmd, textvariable=repFormVals[index]).grid(column=6, row=index + 2)

    def writeHeader():
        countHeader = Label(filterMatrix, text="Sets")
        countHeader.grid(column=2, row=1)

        expHeader = Label(filterMatrix, text="Time (s)")
        expHeader.grid(column=4, row=1)

        repHeader = Label(filterMatrix, text="Repeat")
        repHeader.grid(column=6, row=1)

    def end():
        time.sleep(0.5)
        filterMatrix.destroy()
        filterMatrix.quit()


    def buildTargetField():
        def chkTarget(event):
            if targExists(target.get()) == "No":
                targetField.configure(background="red")
                time.sleep(0.5)
            else:
                targetField.configure(background="green")

                TSXSend("sky6ObjectInformation.Property(0)")		

                targText.set(TSXSend("sky6ObjectInformation.ObjInfoPropOut"))

                TSXSend("sky6ObjectInformation.Property(12)")	

                typeText.set(TSXSend("sky6ObjectInformation.ObjInfoPropOut"))

                timeText.set(targRiseSetTimes(target.get(), "30")) 
            
                subButton = Button(targetFrame, text = "OK", bg = "grey", fg = "black")
                subButton.bind("<Button-1>", closeBox)
                subButton.grid(column = 3, row = 5)


        def closeBox(event):
            time.sleep(0.5)
            targetFrame.destroy()
            targetFrame.quit()

                
        Label(targetFrame, text="Target:").grid(column=1, row=1)
        targetField = Entry(targetFrame, width=20, textvariable=target)
        targetField.grid(column=2, row=1)

        window.bind("<Return>", chkTarget)

        chkButton = Button(targetFrame,text = "Check", bg = "grey", fg = "black")
        chkButton.bind("<Button-1>", chkTarget)
        chkButton.grid(column = 3, row = 1)

        targText = StringVar()

        typeText = StringVar()

        timeText = StringVar()

        Label(targetFrame, text=" Verified: ").grid(column=1, row=2)
        Label(targetFrame, textvariable=targText ).grid(column=2, row=2)
        Label(targetFrame, text=" Type: ").grid(column=1, row=3)
        Label(targetFrame, textvariable=typeText ).grid(column=2, row=3)
        Label(targetFrame, text=" Times: ").grid(column=1, row=4)
        Label(targetFrame, textvariable=timeText ).grid(column=2, row=4)


    def closeFocusBox(event):
        time.sleep(0.5)
        focusFrame.destroy()
        focusFrame.quit()

    def askDefGuideTime():    
        def do_validation(enteredValue):
            return enteredValue == "" or enteredValue.isnumeric()

        def closeBox(event):
            time.sleep(0.5)
            guideFrame.destroy()
            guideFrame.quit()

        vcmd = (guideFrame.register(do_validation), '%P')

        Label(guideFrame, text="Initial Guide Exposure: ").grid(column=1, row=1)
        guideField = Entry(guideFrame, width=2, validate='key', validatecommand=vcmd, textvariable=guiderInitExpField).grid(column=2, row=1)
        window.bind("<Return>", closeBox)
        Label(guideFrame, text="s  ").grid(column=3, row=1)

        Label(guideFrame, text="Initial Guide Delay: ").grid(column=1, row=2)
        guideField = Entry(guideFrame, width=2, validate='key', validatecommand=vcmd, textvariable=guiderInitDelayField).grid(column=2, row=2)
        window.bind("<Return>", closeBox)
        Label(guideFrame, text="s  ").grid(column=3, row=2)

        subButton = Button(guideFrame,text = "OK", bg = "grey", fg = "black")
        subButton.bind("<Button-1>", closeBox)
        subButton.grid(column = 4, row = 3)

    def verifySecondCamera():

        def chkCam(event):

            def closeBox(event):
                time.sleep(0.5)
                secondCamFrame.destroy()
                secondCamFrame.quit()

            def abortBox(event):
                useSecondCamera.set("1")
                time.sleep(0.5)
                secondCamFrame.destroy()
                secondCamFrame.quit()
    

            def chkPort(event):
                timeStamp("Checking for remote host.")

                hostFound = os.system("ping -c 1 " + secondCameraIP.get())
                
                if hostFound == 0:
                    timeStamp("Remote host found.")

                    timeStamp("Checking for second SkyX instance.")
                
                    testSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

                    try:
                        testSocket.connect((secondCameraIP.get(), int(secondCameraPort.get())))

                    except ConnectionRefusedError:
                        print("    ERROR: Unable to establish a connection.")
                        print("           Is SkyX running? Is the TCP Server Listening?")
                        secondIPField.configure(background="red")
                        secondIPPort.configure(background="red")

                    else:

                        ipPort = str(secondCameraPort.get())
                        ipAddress = str(secondCameraIP.get())

                        timeStamp("Found Second SkyX instance at: " + ipAddress + ":" + ipPort)

                        camType = TSXSendRemote( ipAddress + ":" + ipPort, "SelectedHardware.cameraModel")
                        if  camType != "<No Camera Selected>":
                            secondIPField.configure(background="green")
                            secondIPPort.configure(background="green")
                            time.sleep(0.5)

                            camDesc.set(camType)

                            chkButton.destroy()
            
                            subButton = Button(secondCamFrame,text = "OK", bg = "grey", fg = "black")
                            subButton.bind("<Button-1>", closeBox)
                            subButton.grid(column = 3, row = 4)

                        else:
                            secondIPField.configure(background="red")
                            secondIPPort.configure(background="red")
                            print("    ERROR: No remote camera selected.")
                else:
                    print("    ERROR: No remote host found.")
                    secondIPField.configure(background="red")
                    secondIPPort.configure(background="red")

	

            if useSecondCamera.get() == 2:

                secondCamLabel.destroy()
                secondCamNButton.destroy()
                secondCamYButton.destroy()

                endButton.destroy()
                
                Label(secondCamFrame, text="IP Address:").grid(column=1, row=1)
                secondIPField = Entry(secondCamFrame, width=16, textvariable=secondCameraIP)
                secondIPField.grid(column=2, row=1)

                Label(secondCamFrame, text="Port:").grid(column=1, row=2)
                secondIPPort = Entry(secondCamFrame, width=16, textvariable=secondCameraPort)
                secondIPPort.grid(column=2, row=2)

                chkButton = Button(secondCamFrame,text = "Check", bg = "grey", fg = "black")
                chkButton.bind("<Button-1>", chkPort)
                chkButton.grid(column = 3, row = 2)

                exButton = Button(secondCamFrame,text="Exit")
                exButton.bind("<Button-1>", abortBox)
                exButton.grid(column = 4, row = 2)

                camDesc = StringVar()

                Label(secondCamFrame, text=" Camera: ").grid(column=1, row=3)
                Label(secondCamFrame, textvariable=camDesc ).grid(column=2, row=3)

            elif useSecondCamera.get() == 1:
                timeStamp("Using local camera only.")
                closeBox("nothing")
            else:
                timeStamp("No camera option identified.")

        secondCamLabel = Label(secondCamFrame, text="Second Camera?")
        secondCamLabel.grid(column=1, row=1)


        secondCamNButton = Radiobutton(secondCamFrame, text="No", variable=useSecondCamera, value=1)
        secondCamNButton.grid(column=2, row=1)
        secondCamYButton = Radiobutton(secondCamFrame, text="Yes", variable=useSecondCamera, value=2)
        secondCamYButton.grid(column=3, row=1)

        endButton = Button(secondCamFrame,text = "OK", bg = "grey", fg = "black")
        endButton.bind("<Button-1>", chkCam)
        endButton.grid(column = 4, row = 1)


    #---[Create master parameter array to pass to run_target-2]------------------------------------------------------------
    outputArray = []
    outputArray.append("GUI_FrontEnd")

    #---[Create main window]-----------------------------------------------------------------------------------------------


    window = Tk()
    window.title("Run Target")

    #
    # Unfortunately, there are some weird issues with
    # button color on Macintosh. 
    #
    if (themeColor == "Traditional"):
        window.tk_setPalette(background="grey91")

    else:
        window.tk_setPalette(background="grey26", foreground="white")


    #---[Validate Target]--------------------------------------------------------------------------------------------------

    window.geometry("350x140")

    target = StringVar()

    targetFrame = Frame()

    buildTargetField()
    targetFrame.pack()
    targetFrame.mainloop()

    timeStamp("Target set to: " + target.get())

    outputArray.append(target.get())

    #---[Ask about guiding]------------------------------------------------------------------------------------------------


    if TSXSend("SelectedHardware.autoguiderCameraModel") == "<No Camera Selected>":
        guiderExposure = "0"
        timeStamp("No guide camera selected.")
    else:
        window.geometry("320x90")
        guiderInitExpField = StringVar()
        guiderInitDelayField = StringVar()
        guideFrame = Frame()
        askDefGuideTime()
        guideFrame.pack()
        guideFrame.mainloop()

    if (guiderInitExpField.get().isnumeric()):
        guiderExposure = guiderInitExpField.get()
        guiderDelay = guiderInitDelayField.get()
        if not guiderDelay:
            guiderDelay = 0

        if guiderExposure == "0":
            timeStamp("Script will run unguided.")
        else:
            timeStamp("Initial Guider Exposure: " + str(guiderExposure))
            timeStamp("Initial Guider Delay: " + str(guiderDelay))
    else:
        writeNote("Bogus Guide Camera Exposure Submitted.")
        print("           Setting initial expousure to five seconds.")
        print("           Setting initial delay to zero seconds.")
        guiderExposure = "5"
        guiderDelay = "0"


    #---[Ask about focusing]-----------------------------------------------------------------------------------------------


    if TSXSend("SelectedHardware.focuserModel") != "<No Focuser Selected>":
        window.geometry("350x100")
        whichFocusRoutine = IntVar()
        focusFrame = Frame()

        Label(focusFrame, text="Which routine for focusing?").grid(column=1, row=1)

        Radiobutton(focusFrame, text="@Focus2", variable=whichFocusRoutine, value=2).grid(column=2, row=2)
        Radiobutton(focusFrame, text="@Focus3", variable=whichFocusRoutine, value=3).grid(column=2, row=3)

        subButton = Button(focusFrame,text = "OK", bg = "grey", fg = "black")
        subButton.bind("<Button-1>", closeFocusBox)
        subButton.grid(column = 3, row = 4)

        focusFrame.pack()
        focusFrame.mainloop()

        if whichFocusRoutine.get() == 2:
            focusStyle = "Two"
            timeStamp("Focus routine set to @Focus2.")
        else:
            focusStyle = "Three"
            timeStamp("Focus routine set to @Focus3.")
    else:
        timeStamp("No focuser selected.")
    

    #---[Filter Matrix code]-----------------------------------------------------------------------------------------------

    camConnect("Imager")

    filters = []
    filters = nameFilters("Local")
    if filters == "None":
        numFilters = 1
        filters = [""]
        
    numFilters = len(filters)

    countEntryField = [] 
    countFormVals = []
    countRealVals = [0] * numFilters

    expEntryField = []
    expFormVals = []
    expRealVals = [0]  * numFilters

    repEntryField = []
    repFormVals = []
    repRealVals = [0]  * numFilters

    filterMatrix = Frame(window)

    window.geometry("400x" + str((numFilters * 28) + 100))

    filterMatrix.pack()

    lCamLabel = Label(filterMatrix, text="Local Camera:")
    lCamLabel.grid(column=0, row=0)

    writeHeader()

    for index,filterName in enumerate(filters):
        buildCountField(index, filterName)
        buildExposureField(index, filterName)
        buildRepeatField(index, filterName)

    endButton = Button(filterMatrix,text = "Submit", bg = "grey", fg = "black",command=end)
    endButton.grid(column = 7, row = len(countEntryField) + 2)

    filterMatrix.mainloop()

    # 
    # This takes the matrix of values from the form
    # and moves them over to a more easily addressable
    # list, which is already pre-populated with zero
    # values as defaults.
    #

    print("     ----------------------------")
    print("     Local Camera Exposure Matrix")
    print("     ----------------------------")

    for index,filterName in enumerate(filters):
        if (expFormVals[index].get().isnumeric()) and (expFormVals[index].get() != "0"): 
            if countFormVals[index].get().isnumeric():
                countRealVals[index] = int(countFormVals[index].get())

        if countRealVals[index] == 0:
            expRealVals[index] = 0
        else:
            if expFormVals[index].get().isnumeric():
                expRealVals[index] = int(expFormVals[index].get())

        if repFormVals[index].get().isnumeric():
            if (countRealVals[index] == 0) or (expRealVals[index] == 0):
                repRealVals[index] = 0
            else:
                repRealVals[index] = int(repFormVals[index].get())
        else:
            if (countRealVals[index] != 0) and (expRealVals[index] != 0):
                repRealVals[index] = 1

        if repRealVals[index] == 0:
            expRealVals[index] = 0
            countRealVals[index] = 0

        print("     " + str(filterName) + ":\t" + str(countRealVals[index]) + "\t" + str(expRealVals[index]) + "\t" + str(repRealVals[index]))

        outputArray.append(str(countRealVals[index]) + "x" + str(expRealVals[index]) + "x" + str(repRealVals[index]))

    print("     ----------------------------")

    #---[Second Camera Code]-----------------------------------------------------------------------------------------------

    window.geometry("450x150")
    useSecondCamera = IntVar()
    secondCameraIP = StringVar()
    secondCameraIP.set("XXX.XXX.XXX.XXX")
    secondCameraPort = StringVar()
    secondCameraPort.set("3040")
    secondCamFrame = Frame()

    verifySecondCamera()
    secondCamFrame.pack()
    secondCamFrame.mainloop()


    if useSecondCamera.get() == 2:


        #---[Second Camera Filter Matrix code]------------------------------------------------------------------------------

        camConnectRemote(str(secondCameraIP.get()) + ":" + str(secondCameraPort.get()), "Imager")

        filters = []
        filters = nameFilters(str(secondCameraIP.get()) + ":" + str(secondCameraPort.get()))
    
        if filters == "None":
            numFilters = 1
            filters = [""]
    
        numFilters = len(filters)

        countEntryField = [] 
        countFormVals = []
        countRealVals = [0] * numFilters

        expEntryField = []
        expFormVals = []
        expRealVals = [0]  * numFilters

        repEntryField = []
        repFormVals = []
        repRealVals = [0]  * numFilters

        filterMatrix = Frame(window)

        window.geometry("405x" + str((numFilters * 28) + 100))

        filterMatrix.pack()

        lCamLabel = Label(filterMatrix, text="Second Camera:")
        lCamLabel.grid(column=0, row=0)

        writeHeader()

        for index,filterName in enumerate(filters):
            buildCountField(index, filterName)
            buildExposureField(index, filterName)
            buildRepeatField(index, filterName)

        endButton = Button(filterMatrix,text = "Submit", bg = "grey", fg = "black",command=end)
        endButton.grid(column = 7, row = len(countEntryField) + 2)

        filterMatrix.mainloop()

        outputArray.append("-r")
        outputArray.append(str(secondCameraIP.get()) + ":" + str(secondCameraPort.get()))

        print("     -----------------------------")
        print("     Remote Camera Exposure Matrix")
        print("     -----------------------------")

        for index,filterName in enumerate(filters):
            if (expFormVals[index].get().isnumeric()) and (expFormVals[index].get() != "0"): 
                if countFormVals[index].get().isnumeric():
                    countRealVals[index] = int(countFormVals[index].get())

            if countRealVals[index] == 0:
                expRealVals[index] = 0
            else:
                if expFormVals[index].get().isnumeric():
                    expRealVals[index] = int(expFormVals[index].get())

            if repFormVals[index].get().isnumeric():
                if (countRealVals[index] == 0) or (expRealVals[index] == 0):
                    repRealVals[index] = 0
                else:
                    repRealVals[index] = int(repFormVals[index].get())
            else:
                if (countRealVals[index] != 0) and (expRealVals[index] != 0):
                    repRealVals[index] = 1

            if repRealVals[index] == 0:
                expRealVals[index] = 0
                countRealVals[index] = 0

            print("     " + str(filterName) + ":\t" + str(countRealVals[index]) + "\t" + str(expRealVals[index]) + "\t" + str(repRealVals[index]))

            outputArray.append(str(countRealVals[index]) + "x" + str(expRealVals[index]) + "x" + str(repRealVals[index]))

        print("     ---------------")

    window.destroy()
    window.quit()


    #---[Dump Array]-------------------------------------------------------------------------------------------------------

    GUIresults = []

    GUIresults.append(outputArray)
    GUIresults.append(str(guiderExposure))
    GUIresults.append(str(guiderDelay))
    GUIresults.append(str(focusStyle))

    return(GUIresults)

