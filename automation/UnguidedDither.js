// UnguidedDither.js
// Based on Dither with ProTrack - Enhanced Version by Richard S. Wright Jr. @ Software Bisque
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
// ###### Things that _should_ just work.  If not you'll ######
// ###### have to hardcode them                          ######
// ############################################################
//

// This should get calculated.  If it doesn't work then do it manually
// The values of these will be calculated from the filter wheel object
// they ASSUME that the first character of your filter names matche one of L/R/G/B/H/S/O
// It's case insensitive, so luminance, lum, Lum
//
const NUMBER_OF_FILTERS = getFilterCount(ccdsoftCamera);  
const LUM               = findFilterIndexFor(ccdsoftCamera, "L");
const RED               = findFilterIndexFor(ccdsoftCamera, "R");
const GREEN             = findFilterIndexFor(ccdsoftCamera, "G");
const BLUE              = findFilterIndexFor(ccdsoftCamera, "B");
const SII               = findFilterIndexFor(ccdsoftCamera, "S");
const HA                = findFilterIndexFor(ccdsoftCamera, "H");
const OIII              = findFilterIndexFor(ccdsoftCamera, "O");

// ############################################################
// ########## Things you will probably change often  ##########
// ############################################################
//
// ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
// ~~~~~~~~~~ IMAGING Paremeters                     ~~~~~~~~~~
// ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
//
var DELAY            = 5;        // Delay between exposures. Give adequate settle time
var FOCUS_AT_START   = true;     // If true then the first thing it does is a focus routine.
// var TARGET_NAME      = "M 51";
// var TARGET_NAME      = "IC 1396";   // Elephant trunk
// var TARGET_NAME      = "NGC 7000";   // North America Nebula
// var TARGET_NAME      = "M 31";
var TARGET_NAME      = "HIP 99893";  // Near the crescent nebula hip 99893 or 100155

// Each filter can have its own exposure length.
// If the exposure length or count is 0 that filter will be skipped when imaging!!
//
var exposureTimePerFilter = new Array(NUMBER_OF_FILTERS);
exposureTimePerFilter[LUM  ] = 120;
exposureTimePerFilter[RED  ] = 120;
exposureTimePerFilter[GREEN] = 120;
exposureTimePerFilter[BLUE ] = 120;
exposureTimePerFilter[SII  ] = 180;
exposureTimePerFilter[HA   ] = 180;
exposureTimePerFilter[OIII ] = 180;

// Each filter can have its own number of exposures
// If the exposure length or count is 0 that filter will be skipped when imaging!!
//
var numberOfExposuresPerFilter = new Array(NUMBER_OF_FILTERS);
numberOfExposuresPerFilter[LUM  ] = 0;
numberOfExposuresPerFilter[RED  ] = 0;
numberOfExposuresPerFilter[GREEN] = 0;
numberOfExposuresPerFilter[BLUE ] = 0;
numberOfExposuresPerFilter[SII  ] = 150;
numberOfExposuresPerFilter[HA   ] = 150;
numberOfExposuresPerFilter[OIII ] = 0;


// Each filter can have its own binning during imaging runs.
//
var binningPerFilter = new Array(NUMBER_OF_FILTERS);
binningPerFilter[LUM  ] = 1;
binningPerFilter[RED  ] = 1;
binningPerFilter[GREEN] = 1;
binningPerFilter[BLUE ] = 1;
binningPerFilter[SII  ] = 1;
binningPerFilter[HA   ] = 1;
binningPerFilter[OIII ] = 1;

// ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
// ~~~~~~~~~~ FOCUSING Paremeters                    ~~~~~~~~~~
// ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
//
var FOCUS_WITH_FILTER = BLUE;
var FOCUS_BINNING     = 2;
var FOCUS_EXPOSURE_TIME = 0.5;

// Focus every x- you can use any of the conditions.  
// If ANY of these conditions are met it will focus.  It won't ever interrupt an image to focus.
// Set to arbitrarily large values to skip/omit any conditions
// Each is reset when focusing, so if it focuses for any condition then they all start over
//
var FOCUS_EVERY_X_IMAGES        = 3;   // Refocus every so many frames (just make arbitrarily large to skip)
var FOCUS_EVERY_X_DEGREES       = 0.5; // Refocus when the temperature changes more than x (just make arbitrarily large to skip)
var FOCUS_EVERY_X_MINUTES       = 30;  // Refocus after elapsed time (just make arbitrarily large to skip)

// ############################################################
// ################ things you will set once  ################$
// ############################################################
// 
var FILTER_CHANGE_TIME          = 5;     // A guess is fine here, it will be calculated
var TIME_IT_TAKES_TO_FOCUS      = 60;    // This will vary and gets calculated when focusing, this is an initial guess

logOutput("LUM position:   " + LUM);
logOutput("RED position:   " + RED);
logOutput("GREEN position: " + GREEN);
logOutput("BLUE position:  " + BLUE);
logOutput("SII position:   " + SII);
logOutput("HA position:    " + HA);
logOutput("OIII position:  " + OIII);

// Image Download Times
//
var imageDownloadTimePerBinning = new Array(5);  // one more slot than binning available on your camera
imageDownloadTimePerBinning[0] = 0;   // Make it easy and make this array st
imageDownloadTimePerBinning[1] = 5;   // download for 1x1 binning
imageDownloadTimePerBinning[2] = 3;   // download for 2x2 binning
imageDownloadTimePerBinning[3] = 3;   // download for 3x3 binning
imageDownloadTimePerBinning[4] = 2;   // download for 4x4 binning
// imageDownloadTimePerBinning[5];   // download for 5x5 binning
// imageDownloadTimePerBinning[6];   // download for 6x6 binning
// imageDownloadTimePerBinning[7];   // download for 7x7 binning (and so on)

// ############################################################
// ########### Things you MIGHT change once         ###########
// ############################################################
//
var ditherStepSizeArcSeconds = 13.0;     // Amount of dither between exposures in arcseconds
var decMinus = 1.0;                      // Set one of these to zero to limit dec movements to one direction
var decPlus  = 1.0;

var IMAGES_REMAINING_PER_FILTER = new Array();

function isSimulator(imager)
{
    // If the width is 1000 then it's probably the simulator
    //
    return ((imager.WidthInPixels * imager.BinX) == 1000);
}

function getFilterCount(imager)
{
    var i = 0;
    // there may not be a filter wheel
    //
    if (imager.filterWheelIsConnected())
    {
        while (i < imager.lNumberFilters)
        {
            var name = imager.szFilterName(i);
            if (name.substr(0, 6).toUpperCase() == "FILTER")
            {
                logOutput("It looks like there are " + i + " filters. If that's not right, hardcode it")
                return i;
            }                
            i++;
        }
    }
    
    return i;
}

function findFilterIndexFor(imager, filter)
{
    // there may not be a filter wheel
    //
    if (imager.filterWheelIsConnected())
    {
        var i = 0;
        while (i < imager.lNumberFilters)
        {
            var name = imager.szFilterName(i);
            
            if (name.substr(0, 1).toUpperCase() == filter.substr(0, 1).toUpperCase())
            {
                return i;
            }
            
            i++;
        }
    }
    else
    {
        logOutput("ERROR: filterwheel is not connected")
    }
    
    // Getting here is a bad thing
    // 
    logOutput("ERROR: could not find filter for " + filter)
    return -1;
}

// Pass in a connected imager object
function getFilterNameArray(imager)
{
    var filterNames = new Array();
    var idx;
    var msg = "";
    var name = "";
    
    // there may not be a filter wheel
    if (imager.filterWheelIsConnected())
    {
        for (idx = 0; idx < NUMBER_OF_FILTERS; idx++) 
        {
            name = imager.szFilterName(idx);
            filterNames.push(name)
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
    
    logOutput("Attempting to focus with " + filterNames[imager.FilterIndexZeroBased] + "  " + binning + "x" + binning + " @ " + FOCUS_EXPOSURE_TIME + " second(s)")
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
        imager.ExposureTime = exposureTime;  // Not convinced that this does anything
        imager.AtFocus3(3, true);            // Three samples per position, full-auto on subframe selection
        
        imager.BinX = saveBinX;
        imager.BinY = saveBinY;
        imager.Delay = saveDelay;
        imager.ExposureTime = saveExposureTime;        
    }
    
    var discreteEndTime = new Date();
    
    TIME_IT_TAKES_TO_FOCUS = Math.floor((discreteEndTime - discreteStartTime) / 1000);
    
    // Reset the last focus variables so we don't focus too soon
    //
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

function timeRemaining(imageCountArray)
{
    var secondsRemaining = 0;

    for (var i = 0; i < NUMBER_OF_FILTERS; i++) 
    {    
        if (exposureTimePerFilter[i] > 0)
        {
            secondsRemaining += (exposureTimePerFilter[i] 
                + imageDownloadTimePerBinning[binningPerFilter[i]]
                + DELAY
                + FILTER_CHANGE_TIME) 
                * imageCountArray[i];
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

function calculateFilterChangeTime(imager)
{
    imager.FilterIndexZeroBased = 0;
    var discretStartTime = new Date();

    imager.FilterIndexZeroBased = NUMBER_OF_FILTERS - 1;

    var discreteEndTime = new Date();
    
    // Use half of what is likely the longest filter change time as the change time
    //
    FILTER_CHANGE_TIME = Math.floor( (discreteEndTime - discretStartTime) / 1000 / 2 );
}

function closedLoopSlew(imager, targetName)
{
    var status = 0;
    
    logOutput("");
    logOutput("Performing a Closed Loop Slew to " + targetName);
    
    sky6StarChart.Find(targetName);
    TheSkyXAction.execute("LOOK_UP");
    
    try 
    {
        // Turn on camera autosave
        //
        imager.Connect();
        imager.AutoSaveOn = 1;
    
        status = ClosedLoopSlew.exec();
    }
    catch(e) 
    {
    	logOutput("");
        logOutput("Closed Loop Slew error: " + e);
    	logOutput("");
        return -999;
    }    
    
    return status;    
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
Imager.Frame = 1;  // Light frames

var filterNames = getFilterNameArray(Imager);

calculateFilterChangeTime(Imager);

// Script assumes that you have focused right before execution
//
var LAST_FOCUS_TIME =  new Date();
var LAST_FOCUS_TEMPERATURE = Imager.focTemperature;
var IMAGES_SINCE_LAST_FOCUS = 0;

// Get current position of the telescope
//
sky6RASCOMTele.Connect();
sky6RASCOMTele.GetRaDec();
var startRA = sky6RASCOMTele.dRa;
var startDEC = sky6RASCOMTele.dDec;

// Get step size in degrees
//
var ditherStepDegrees = ditherStepSizeArcSeconds / 3600.0;
    
// Wait for the scope to finish the slew before doing anything else
//
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

var currentTime = new Date();

var discreteStartTime = new Date();
var discreteEndTime = new Date();

// Start taking images
//
logOutput("Starting unguided, dithered image run of " + getCurrentObjectName());
var status = "";

status = "Dither Step size = ";
status += ditherStepSizeArcSeconds;
status += " arcseconds\r\n";
logOutput(status);

// how many images are we taking?
//
var NUMBER_OF_IMAGES = 0;

for (var i = 0; i < NUMBER_OF_FILTERS; i++) 
{    
    if (exposureTimePerFilter[i] > 0)
    {
        NUMBER_OF_IMAGES += numberOfExposuresPerFilter[i];
        IMAGES_REMAINING_PER_FILTER[i] = numberOfExposuresPerFilter[i];
    }
}

var timeLeft = timeRemaining(IMAGES_REMAINING_PER_FILTER);

status = "";
status += "we are taking " + NUMBER_OF_IMAGES + " images.  ";
status += "Which will take approximately ";
status += timeLeft;
status += " seconds to run; ";
status += " estimated completion time [" + currentTime.addSeconds(timeLeft).toLocaleTimeString() + "] ";
logOutput(status);

var startTime = new Date();

// This assumes that we're close enough to focus to plate solve
// 
if (TARGET_NAME != "")
{
    var ret = closedLoopSlew(Imager, TARGET_NAME);
    
    logOutput("CLS returned [" + ret + "]") 

    if (ret != 0)
    {
        // Not sure how to abort...
        //
        exit;
    }
    
    // Set the save prefix to the current object, when we dither it gets lost
    //
    Imager.AutoSavePrefix = TARGET_NAME + "-";
}
else
{
    Imager.AutoSavePrefix = getCurrentObjectName() + "-";    
}

if (FOCUS_AT_START)
{
    autofocusWithFilter(Imager, FOCUS_WITH_FILTER, FOCUS_EXPOSURE_TIME, FOCUS_BINNING);
}

while (imageCount < NUMBER_OF_IMAGES)
{    
    if (exposureTimePerFilter[currentFilter] > 0 && IMAGES_REMAINING_PER_FILTER[currentFilter] > 0)
    {
        // maybe focus
        //
        if (shouldFocus(imageCount))
        {
            autofocusWithFilter(Imager, FOCUS_WITH_FILTER, FOCUS_EXPOSURE_TIME, FOCUS_BINNING);
        }
    
        // take a picture
        //    
        currentTime = new Date();
        var elapsed = (currentTime - startTime) / 1000;
        var secondsRemaining = timeRemaining(IMAGES_REMAINING_PER_FILTER);

        Imager.FilterIndexZeroBased = currentFilter;
    
        // Take the photo
        //
        status = "";    
        status += "Elapsed time on <" + getCurrentObjectName() + ">: [" + prettyFormatSeconds(elapsed) + "] ";
        status += "Exposing for ";
        status += padString(exposureTimePerFilter[currentFilter], 5);
        status += " seconds ";
        status += binningPerFilter[currentFilter] + "x" + binningPerFilter[currentFilter];
        status += " on ";
        status += padString(filterNames[currentFilter], 10);
        status += " (";
        status += numberOfExposuresPerFilter[currentFilter] - IMAGES_REMAINING_PER_FILTER[currentFilter] + 1;
        status += " of ";
        status += numberOfExposuresPerFilter[currentFilter];
        status += ")";
        status += " Remaining [" + prettyFormatSeconds(secondsRemaining) + "] ";
        status += " Estimated Completion [" + currentTime.addSeconds(secondsRemaining).toLocaleTimeString() + "] ";
        status += " at " + Imager.focTemperature + " degrees";

        logOutput(status);

        Imager.BinX = binningPerFilter[currentFilter];
        Imager.BinY = binningPerFilter[currentFilter];    

        var imageStartTime = new Date();
        Imager.ExposureTime = exposureTimePerFilter[currentFilter];
        Imager.Delay = DELAY;
        Imager.TakeImage();
        var imageEndTIme = new Date();
    
        IMAGES_REMAINING_PER_FILTER[currentFilter] -= 1;

        // Calculate a better image download time (this doesn't include filterwheel change...)
        //        
        var tmp = Math.ceil((imageEndTIme - imageStartTime) / 1000) - exposureTimePerFilter[currentFilter] - DELAY;
        if (imageDownloadTimePerBinning[binningPerFilter[currentFilter]] != tmp)
        {
            imageDownloadTimePerBinning[binningPerFilter[currentFilter]] = tmp;
            // logOutput("Adjusting download time for " + binningPerFilter[currentFilter] + "x" + binningPerFilter[currentFilter] + " images to " + tmp + " seconds");
        }
		
		IMAGES_SINCE_LAST_FOCUS++;
        imageCount++;       
    }
    else
    {
        // logOutput("Skipping filter: " + filterNames[currentFilter]);        
    }
    
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
        logOutput("\n==== Dithering ====\n");
        sky6RASCOMTele.SlewToRaDec(startRA + deltaRA, startDEC + deltaDEC,"");
    }    
}

// sky6RASCOMTele.Park();

logOutput("###############################################");
logOutput("############ Dithered run complete ############");
logOutput("###############################################");
