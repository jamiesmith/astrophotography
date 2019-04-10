// UnguidedDitherWFilters.js
// Dither with ProTrack - Enhanced Version
// Richard S. Wright Jr.
// Software Bisque
// Assumptions: ProTrack is on and enabled (or your exposures are short enough you don't 
//            need ProTrack.
//                     You have slewed to the target and framed up things the way you want
//                     The camera dialog is set for the binning, saving, etc.
//                     You are already connected to both scope and camera
//            The AutoSave is turned on, and configured for the target of choice
//                     Color filters are setup in LRGB order. Ha, OIII, SII
//                     Reording of the variables should be straightforward, even for the 
//            non programmer... I hope ;-)
//
// The dither operation takes place only when the filters have completed one cycle. 
// Eash filter can have it's own exposure time.
// This is a round robin approach... if your filters are not parfocal, you may
// need to setup filter focuser offsets in TheSkyX.

// ###################################################################################################
// Lines that follow this come from the CommonUtils.js file - don't edit here, edit there then import
// ###################################################################################################
// This file contains the things that most of the other things include.  Can't figure out if/how I can include
const LUM   = 0;        // Just makes it easier to not screw up when it's late at night
const RED   = 1;        // change if necessary to match your filer configuration
const GREEN = 2;
const BLUE  = 3;
const SII   = 4;
const HA    = 5;
const OIII  = 6;


function isSimulator(imager)
{
    // If the width is 1000 then it's probably the simulator
    //
    return (imager.WidthInPixels == 1000);
}

// Pass in a connected imager object
function getFilterNameArray(imager)
{
    var filterNames = new Array();
    var idx;
    var msg = "";

    // there may not be a filter wheel
    if (imager.filterWheelIsConnected()) 
    {
        for (idx = 0; idx < imager.lNumberFilters; idx++) 
        {
            filterNames.push(imager.szFilterName(idx))
        }
    }
    else 
    {
        msg = "Filter wheel not connected";
    }

    logOutput(msg);

    return filterNames;
}

function autofocus(imager, exposureTime, binning)
{
    if (isSimulator(imager))
    {
        logOutput("Skipping @focus3, running with the simulator")
    }
    else
    {    
        logOutput("Running @focus3");
        
        var saveBinX = imager.BinX
        var saveBinY = imager.BinY
        var saveDelay = imager.Delay
        var saveExposureTime = imager.ExposureTime
        
        imager.BinX = binning;
        imager.BinY = binning;
        imager.Delay = 0;
        imager.ExposureTime = focusExposureTimePerFilter[currFilter];   
        imager.AtFocus3(3, true);    // Three samples per position, full-auto on subframe selection
        
        imager.BinX = saveBinX;
        imager.BinY = saveBinY;
        imager.Delay = saveDelay;
        imager.ExposureTime = saveExposureTime;        
    }    
}

function prettyFormatSeconds(seconds)
{
    return pad(Math.floor(seconds / 3600 % 24), 2) + ":" 
        + pad(Math.floor(seconds / 60 % 60), 2) + ":" 
        + pad(Math.floor(seconds % 60), 2)
}

///////////////////////////////////////////////////////////////////////////

function pad(num, size) 
{
    var s = "000" + num;
    return s.substr(s.length - size);
}

function padString(text, size) 
{
    var s = text + "            ";
    return s.substr(0, size);
}

function logOutput(logText)
{
    RunJavaScriptOutput.writeLine(logText);
    // TextFile.write(logText);
}

function pad(num, size) 
{
    var s = "000" + num;
    return s.substr(s.length - size);
}

function padString(text, size) 
{
    var s = text + "            ";
    return s.substr(0, size);
}

function logOutput(logText)
{
    RunJavaScriptOutput.writeLine(logText);
}

Date.prototype.addSeconds = function(seconds) 
{
    this.setSeconds(this.getSeconds() + seconds);
    return this;
};


// ###################################################################################################
// Lines that precede this come from the CommonUtils.js file - don't edit here, edit there then import
// ###################################################################################################


///////////////////////////////////////////////////////////////////////////
// How many images do I want? How much space in arcseconds between them
//////////////////////////////////////////////////////////////////////////////////////////  \/ \/ \/ USER INPUT HERE 
var ditherStepSizeArcSeconds = 5.0;  // Amount of dither between exposures in arcseconds
var FIRST_FILTER = LUM;              // Filter to start with
var LAST_FILTER = BLUE;              // Filter to end with
var NUM_IMAGES = 96;                 // Number of Images to take (TOTAL including all filters)
var DELAY = 5;                       // Delay between exposures. Give adequate settle time
var decMinus = 1.0;                  // Set one of these to zero to limit dec movements to one direction
var decPlus = 1.0;
var FOCUS_EVERY_X_IMAGES = 10;       // Refocus every so many targets (just make arbitrarily large to skip)
var vFILTER_CHANGE_TIME = 0;         // This will be calculated and averaged
var vDOWNLOAD_TIME = 0;              // This will be calculated and averaged

// Each filter can have its own exposure length.
var exposureTimePerFilter = new Array(7);
exposureTimePerFilter[LUM  ] = 1; // 300;
exposureTimePerFilter[RED  ] = 1; // 120;
exposureTimePerFilter[GREEN] = 1; // 120;
exposureTimePerFilter[BLUE ] = 1; // 120;
exposureTimePerFilter[SII  ] = 1; // 900;
exposureTimePerFilter[HA   ] = 1; // 900;
exposureTimePerFilter[OIII ] = 1; // 900;

var focusExposureTimePerFilter = new Array(7);
focusExposureTimePerFilter[LUM  ] = 5;
focusExposureTimePerFilter[RED  ] = 5;
focusExposureTimePerFilter[GREEN] = 5;
focusExposureTimePerFilter[BLUE ] = 5;
focusExposureTimePerFilter[SII  ] = 10;
focusExposureTimePerFilter[HA   ] = 10;
focusExposureTimePerFilter[OIII ] = 10;

///////////////////////////////////////////////////////////////////////////////////////////////////^^^ END USER INPUT


function timeRemaining(currentFilterIndex, currentImageIndex)
{
    var imagesRemaining = NUM_IMAGES - currentImageIndex;
    var imagesPerFilter = Math.floor(NUM_IMAGES / ((LAST_FILTER - FIRST_FILTER) + 1));
    var imagesRemainingPerFilter = imagesPerFilter - (Math.floor(currentImageIndex / ((LAST_FILTER - FIRST_FILTER) + 1)) + 1);
    
    
    var secondsRemaining = 0;

    // Filters BEFORE this current one have 
    var delayPerImage = vDOWNLOAD_TIME + DELAY + vFILTER_CHANGE_TIME;
    
    for (var i = FIRST_FILTER ; i < currentFilterIndex ; i++)
    {
        secondsRemaining += Math.floor((exposureTimePerFilter[i] + delayPerImage) * imagesRemainingPerFilter);
    }

    for (i = currentFilterIndex ; i <= LAST_FILTER ; i++)
    {
        secondsRemaining += Math.floor((exposureTimePerFilter[i] + delayPerImage) * (imagesRemainingPerFilter + 1)); 
    }

    return secondsRemaining;
}

///////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////

var Imager = ccdsoftCamera;
Imager.Autoguider = false;
Imager.Connect();
Imager.Asynchronous = false;
Imager.Autosave = true;

var filterNames = getFilterNameArray(Imager);

// Get current position of the telescope
sky6RASCOMTele.Connect();
sky6RASCOMTele.GetRaDec();
var startRA = sky6RASCOMTele.dRa;
var startDEC = sky6RASCOMTele.dDec;

// Get step size in degrees
var ditherStepDegrees = ditherStepSizeArcSeconds / 3600.0;
    
// I want to wait for the scope to finish the slew before doing anything else
sky6RASCOMTele.Asynchronous = false;

// The track will trace a series of ever increasing circles around the target
// the radius of the first circle is the dither step size. Each circle is one
// more ditherStepDegree's out.
var currRadius = ditherStepDegrees;

var iImageCount = 0;                    // How many images we have taken so far
var angle = 7.0;                        //    Past 2 PI to trip the first update
var steps = 4.0;                        // Number of steps around the circle doubles each time
                                        // First ring will actually be 8
var currFilter = FIRST_FILTER;          // Start first filter

var startTime = new Date();
var currentTime;
var totalImagesToTake = 0;
var discreteStartTime = new Date();
var discreteEndTime = new Date();

// Okay, start taking images
//
logOutput("Starting unguided, dithered image run.");
var out = "Dither Step size = ";
out += ditherStepSizeArcSeconds;
out += " arcseconds\r\n";
logOutput(out);

while (iImageCount < NUM_IMAGES)
{
    var discreetStartTime = new Date();
    Imager.FilterIndexZeroBased = currFilter;
    var discreteEndTime = new Date();
    vFILTER_CHANGE_TIME = Math.floor((discreteEndTime - discreetStartTime) / 1000);
    
    if ((iImageCount > 0 ) && (iImageCount % FOCUS_EVERY_X_IMAGES) == 0) 
    {
        autofocus(Imager, focusExposureTimePerFilter[currFilter], 2)
    }

    currentTime = new Date();
    var elapsed = (currentTime - startTime) / 1000;
    var secondsRemaining = timeRemaining(currFilter, iImageCount);

    // Take one photo at the current position
    //
    var status = "";
    status += "Elapsed time [" + prettyFormatSeconds(elapsed) + "] ";
    status += "Exposing for (";
    status += exposureTimePerFilter[currFilter];
    status += " seconds) on ";
    status += padString(filterNames[currFilter], 10);
    status += " (";
    status += Math.floor(iImageCount / ((LAST_FILTER - FIRST_FILTER) + 1)) + 1;
    status += " of ";
    status += NUM_IMAGES / ((LAST_FILTER - FIRST_FILTER) + 1);
    status += ")";
    status += " Remaining [" + prettyFormatSeconds(secondsRemaining) + "] ";
    status += " Estimated Completion [" + currentTime.addSeconds(secondsRemaining).toLocaleTimeString() + "] ";
    
    Imager.BinX = 1;
    Imager.BinY = 1;    
    
    logOutput(status);

    discreetStartTime = new Date();
    Imager.ExposureTime = exposureTimePerFilter[currFilter];
    Imager.Delay = DELAY;
    Imager.TakeImage();
    discreteEndTime = new Date();
    
    // Calculate a better image download time (it doesn't include filterwheel change...)
    //    
    var imageDownloadTime = Math.floor(((discreteEndTime - discreetStartTime) / 1000) - exposureTimePerFilter[currFilter] - DELAY);
    if (vDOWNLOAD_TIME == 0)
    {
        vDOWNLOAD_TIME = imageDownloadTime;
    }
    else
    {
        vDOWNLOAD_TIME = Math.floor((vDOWNLOAD_TIME * (iImageCount - 1) + imageDownloadTime) / iImageCount);
    }

    
    // Change Filters
    currFilter++;
    if (currFilter > LAST_FILTER) 
    {
        currFilter = FIRST_FILTER;    // Back to first, now do dither.
        
        // Time for the next circle?
        if (angle > 2*3.14159265) 
        {
            angle = 0.0;                     // Reset rotation
            steps *= 2.0;                    // Double steps on circle
            currRadius += ditherStepDegrees; // Increment radius of circle by dither space
        }
        else
        {
            angle += ((3.14159265 * 2.0) / steps);    // Next sample along ring
        }

        // Compute next dither location
        var deltaRA  = Math.cos(angle) * currRadius/15.0;
        var deltaDEC = Math.sin(angle) * currRadius;

       // Limit dec direction changes?
        if (deltaDEC > 0) deltaDEC *= decPlus;
        if (deltaDEC < 0) deltaDEC *= decMinus;

        // Slew to next location
        logOutput("Moving OTA");
        sky6RASCOMTele.SlewToRaDec(startRA + deltaRA, startDEC + deltaDEC,"");

        // Done.
    }            

    iImageCount++;
}

// sky6RASCOMTele.Park();

// Old Style output
out = "Dithered run complete\r\n";

logOutput(out);

