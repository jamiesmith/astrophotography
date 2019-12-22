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
// Eash filter can have its own exposure time.
// This is a round robin approach... if your filters are not parfocal, you may
// need to setup filter focuser offsets in TheSkyX.

//////////////////////////////////////////////////////////////////////////////////////////  \/ \/ \/ USER INPUT HERE 

// ############################################################
// ########## Things you will probably change often  ##########
// ############################################################
//
var NUMBER_OF_IMAGES_PER_FILTER = 60;   // Number of Images per filter
var DELAY                       = 5;   // Delay between exposures. Give adequate settle time

// Focus every x- you can use any of the conditions.  Each is reset when focusing
//
var FOCUS_EVERY_X_IMAGES        = 3;  // Refocus every so many frames (just make arbitrarily large to skip)
var FOCUS_EVERY_X_DEGREES       = 0.5; // Refocus when the temperature changes more than x (just make arbitrarily large to skip)
var FOCUS_EVERY_X_MINUTES       = 30;  // Refocus after elapsed time (just make arbitrarily large to skip)

// Each filter can have its own exposure length.
//
var exposureTimePerFilter = new Array(NUMBER_OF_FILTERS);
exposureTimePerFilter[LUM  ] = 3;
exposureTimePerFilter[RED  ] = 3;
exposureTimePerFilter[GREEN] = 3;
exposureTimePerFilter[BLUE ] = 3;
exposureTimePerFilter[SII  ] = 3;
exposureTimePerFilter[HA   ] = 3;
exposureTimePerFilter[OIII ] = 3;

// Each filter can have its own binning.
// If the binning for the filter is 0 that filter will be skipped when imaging!!
//
var binningPerFilter = new Array(NUMBER_OF_FILTERS);
binningPerFilter[LUM  ] = 1;
binningPerFilter[RED  ] = 0;
binningPerFilter[GREEN] = 0;
binningPerFilter[BLUE ] = 0;
binningPerFilter[SII  ] = 1;
binningPerFilter[HA   ] = 1;
binningPerFilter[OIII ] = 1;

// How to focus?
//
var FOCUS_WITH_FILTER = BLUE;
var FOCUS_BINNING     = 2;

var focusExposureTimePerFilter = new Array(NUMBER_OF_FILTERS);
focusExposureTimePerFilter[LUM  ] = 1;   // Yeah. these are tied to binning.  
focusExposureTimePerFilter[RED  ] = 1;
focusExposureTimePerFilter[GREEN] = 1;
focusExposureTimePerFilter[BLUE ] = 1;
focusExposureTimePerFilter[SII  ] = 1;
focusExposureTimePerFilter[HA   ] = 1;
focusExposureTimePerFilter[OIII ] = 1;

// ############################################################
// ################ things you will set once  ################$
// ############################################################
// 
var NUMBER_OF_FILTERS           = 7;
var FILTER_CHANGE_TIME          = 5;
var TIME_IT_TAKES_TO_FOCUS      = 60;    // This will vary and gets calculated when focusing

const LUM   = 0;        // Just makes it easier to not screw up when it's late at night
const RED   = 1;        // change if necessary to match your filer configuration
const GREEN = 2;
const BLUE  = 3;
const SII   = 4;
const HA    = 5;
const OIII  = 6;

// Image Download Times
//
var imageDownloadTime = new Array();
imageDownloadTime.push(23);  // download for 1x1 binning
imageDownloadTime.push(7);   // download for 2x2 binning
imageDownloadTime.push(3);   // download for 3x3 binning
imageDownloadTime.push(2);   // download for 4x4 binning
// imageDownloadTime.push(2);   // download for 5x5 binning
// imageDownloadTime.push(2);   // download for 6x6 binning
// imageDownloadTime.push(2);   // download for 7x7 binning (and so on)

// ############################################################
// ########### Things you likely won't change ever  ###########
// ############################################################
//
var ditherStepSizeArcSeconds = 5.0;      // Amount of dither between exposures in arcseconds
var decMinus = 1.0;                      // Set one of these to zero to limit dec movements to one direction
var decPlus = 1.0;

var IMAGES_REMAINING_PER_FILTER = new Array();

function isSimulator(imager)
{
    // If the width is 1000 then it's probably the simulator
    //
    return ((imager.WidthInPixels * imager.BinX) == 1000);
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

function autofocusWithFilter(imager, filterNum, exposureTime, binning)
{
    var saveFilter = imager.FilterIndexZeroBased;
    
    imager.FilterIndexZeroBased = filterNum;
    imager.Delay = 0;    
    autofocus(imager, exposureTime, binning)
    
    imager.FilterIndexZeroBased = saveFilter;
}

function autofocus(imager, exposureTime, binning)
{    
    var discreteStartTime = new Date();
    
    logOutput("Attempting to focus with " + filterNames[imager.FilterIndexZeroBased] + " bin:" + binning + "x" + binning + " @ " + focusExposureTimePerFilter[imager.FilterIndexZeroBased] + " second(s)")
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
        imager.ExposureTime = exposureTime;
        imager.AtFocus3(3, true);    // Three samples per position, full-auto on subframe selection
        
        imager.BinX = saveBinX;
        imager.BinY = saveBinY;
        imager.Delay = saveDelay;
        imager.ExposureTime = saveExposureTime;        
        
    }
    
    var discreteEndTime = new Date();
    
    TIME_IT_TAKES_TO_FOCUS = Math.floor((discreteEndTime - discreetStartTime) / 1000);
    
    LAST_FOCUS_TIME =  new Date();
    LAST_FOCUS_TEMPERATURE = Imager.focTemperature;
    IMAGES_SINCE_LAST_FOCUS = 0;
    
    
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

function totalTime(imageCountArray)
{
    var secondsRemaining = 0;

    for (var i = 0; i < NUMBER_OF_FILTERS; i++) 
    {    
        if (binningPerFilter[i] > 0)
        {
            secondsRemaining += (exposureTimePerFilter[i] + imageDownloadTime[binningPerFilter[i]] + FILTER_CHANGE_TIME) * imageCountArray[i];
        }
    }    
    return secondsRemaining;
}

function shouldFocus(imageCount)
{
    var currentTime = new Date();    
    var elapsed = (currentTime - startTime) / 1000;
    var message = "It's not time to focus";
    var shouldFocus = false;
    
    var temperatureDelta = Math.abs(LAST_FOCUS_TEMPERATURE - Imager.focTemperature);
    var timeDelta = (currentTime - LAST_FOCUS_TIME) / 1000 / 60;
    var imageDelta = FOCUS_EVERY_X_IMAGES - IMAGES_SINCE_LAST_FOCUS;
    
    var debug = " -- Temp Delta [" + temperatureDelta + "] timeDelta [" + timeDelta + "] imageDelta [" + imageDelta + "]";
    
    if ( timeDelta > FOCUS_EVERY_X_MINUTES )
    {
        message = "Focus based on last focus time";
        shouldFocus = true;
    }
    else if ( temperatureDelta > FOCUS_EVERY_X_DEGREES )
    {
        message = "Focus based temperature";
        shouldFocus = true;
    }
    else if (IMAGES_SINCE_LAST_FOCUS >= FOCUS_EVERY_X_IMAGES)
    {
        message = "Focus based on number of images";
        shouldFocus = true;
    }

    if (shouldFocus)
    {
        logOutput(message + debug);
    }
    return shouldFocus;
}

function getProperty(propertyNum)
{
    var name = "";
    
    if (sky6ObjectInformation.PropertyApplies(propertyNum) != 0)
    {
        sky6ObjectInformation.Property(propertyNum);
        name = sky6ObjectInformation.ObjInfoPropOut;
    }
    
    return name;
}

function getCurrentObjectName()
{
    var name0 = getProperty(0);
    var name1 = getProperty(1);
    
    if (name1.lastIndexOf("M", 0) === 0)
    {
        return name1;
    }
    else
    {
        return name0;
    }    
}

///////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////

// Initialize a few things
//
for (var i = 0; i < NUMBER_OF_FILTERS; i++)
{
    // Default to 
    IMAGES_REMAINING_PER_FILTER[i] = 0;
}

var Imager = ccdsoftCamera;
Imager.Autoguider = false;
Imager.Connect();
Imager.Asynchronous = false;
Imager.Autosave = true;

var filterNames = getFilterNameArray(Imager);

var LAST_FOCUS_TIME =  new Date();
var LAST_FOCUS_TEMPERATURE = Imager.focTemperature;
var IMAGES_SINCE_LAST_FOCUS = 0;


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
//
var currRadius = ditherStepDegrees;

var imageCount = 0;      // How many images we have taken so far
var angle = 7.0;         //    Past 2 PI to trip the first update
var steps = 4.0;         // Number of steps around the circle doubles each time
                         // First ring will actually be 8
var currentFilter = 0;   // Start first filter

var startTime = new Date();
var currentTime;

var discreteStartTime = new Date();
var discreteEndTime = new Date();

// Start taking images
//
logOutput("Starting unguided, dithered image run.");
var out = "Dither Step size = ";
out += ditherStepSizeArcSeconds;
out += " arcseconds\r\n";
logOutput(out);

// how many images are we taking?
NUMBER_OF_IMAGES = 0;
for (var i = 0; i < NUMBER_OF_FILTERS; i++) 
{    
    if (binningPerFilter[i] > 0)
    {
        NUMBER_OF_IMAGES += NUMBER_OF_IMAGES_PER_FILTER;
        IMAGES_REMAINING_PER_FILTER[i] = NUMBER_OF_IMAGES_PER_FILTER;
    }
}

logOutput("we are taking " + NUMBER_OF_IMAGES + " images.  " + "Looks like it will take " + totalTime(IMAGES_REMAINING_PER_FILTER) + " seconds to run");

// Set the save prefix to the current object, when we dither it gets lost
//
Imager.AutoSavePrefix = getCurrentObjectName() + "-";

while (imageCount < NUMBER_OF_IMAGES)
{    
    var discreetStartTime = new Date();
    var discreteEndTime = new Date();
    
    if (binningPerFilter[currentFilter] == 0)
    {
        // logOutput("Skipping filter: " + filterNames[currentFilter]);
        currentFilter++;
        if (currentFilter >= NUMBER_OF_FILTERS) 
        {
            currentFilter = 0;    // Back to first, now do dither.
        }
        continue;        
    }
    
    // maybe focus
    //
    if (shouldFocus(imageCount))
    {
        autofocusWithFilter(Imager, FOCUS_WITH_FILTER, focusExposureTimePerFilter[FOCUS_WITH_FILTER], FOCUS_BINNING);
    }
    
    // take a picture
    //    
    currentTime = new Date();
    var elapsed = (currentTime - startTime) / 1000;
    var secondsRemaining = totalTime(IMAGES_REMAINING_PER_FILTER);

    // Take one photo at the current position
    //
    var status = "";
    
    status += "Elapsed time on <" + getCurrentObjectName() + ">: [" + prettyFormatSeconds(elapsed) + "] ";
    status += "Exposing for (";
    status += exposureTimePerFilter[currentFilter];
    status += " seconds) on ";
    status += padString(filterNames[currentFilter], 10);
    status += " (";
    status += NUMBER_OF_IMAGES_PER_FILTER - IMAGES_REMAINING_PER_FILTER[currentFilter];
    status += " of ";
    status += IMAGES_REMAINING_PER_FILTER[currentFilter];
    status += ")";
    status += " Remaining [" + prettyFormatSeconds(secondsRemaining) + "] ";
    status += " Estimated Completion [" + currentTime.addSeconds(secondsRemaining).toLocaleTimeString() + "] ";
    status += " at " + Imager.focTemperature + "°";

    logOutput(status);

    Imager.BinX = binningPerFilter[currentFilter];
    Imager.BinY = binningPerFilter[currentFilter];    

    discreetStartTime = new Date();
    Imager.ExposureTime = exposureTimePerFilter[currentFilter];
    Imager.Delay = DELAY;
    Imager.TakeImage();
    discreteEndTime = new Date();
    
    IMAGES_REMAINING_PER_FILTER[currentFilter] -= 1;

    // change the filter
    //    
    currentFilter++;
    if (currentFilter >= NUMBER_OF_FILTERS) 
    {
        currentFilter = 0;    // Back to first, now do dither.
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
        //
        logOutput("\n==== Dithering OTA ====\n");
        sky6RASCOMTele.SlewToRaDec(startRA + deltaRA, startDEC + deltaDEC,"");

        // Done.        
    }
    
    imageCount++;    
}

// sky6RASCOMTele.Park();

// Old Style output
out = "Dithered run complete\r\n";

logOutput(out);

