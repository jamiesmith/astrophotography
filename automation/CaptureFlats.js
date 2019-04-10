
var flatBinningControl = [
    false,   // ignore
    false,    // 1x1 binning
    true,    // 2x2 binning
    true,    // 3x3 binning
    true     // 4x4 binning    
]

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
//////////////////////////////////////////////////////////////////////////////////////////  \/ \/ \/ USRER INPUT HERE 
var numImages = 30;                    // Number of Images to take with each filter
var firstFilter = LUM;
var lastFilter = OIII;
var delay = 5;                         // Delay between exposures. Give adequate settle time

// Each filter can have its own exposure length.
var exposureTimes = new Array(7);

// I got these by running the flats calibration wizard in SGP
// first column is always zero.  Other "columns" are binning.  So the time
// to expose red for a 2x2 bin is 5.19 seconds.  
// If it matters, I have my flat frames autosave set to :it_:e_:b_:f_:c_:q
// 
exposureTimes[LUM]   = [0,    6.18,  1.34,  0.54,  0.25 ];
exposureTimes[RED]   = [0,   21.34,  5.19,  2.07,  1.10 ];
exposureTimes[GREEN] = [0,   32.57,  7.87,  3.55,  1.74 ];
exposureTimes[BLUE]  = [0,   14.15,  3.51,  1.34,  0.70 ];
exposureTimes[SII]   = [0,  174.24, 42.86, 18.86, 10.49 ];
exposureTimes[HA]    = [0,  263.30, 64.65, 28.64, 15.97 ];
exposureTimes[OIII]  = [0,  257.32, 62.77, 27.65, 15.36 ];


///////////////////////////////////////////////////////////////////////////////////////////////////^^^ END USER INPUT
///////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////

var Imager = ccdsoftCamera;
Imager.Autoguider = 0;
Imager.Connect();
Imager.Asynchronous = 0;
Imager.Autosave = 1;

Imager.Frame = 4; // Can't get enum to work ccdsoftCamera::ccdsoftImageFrame.cdFlat;

// Open a text file for writing or reading
//
if (TextFile.createNew("FlatsLog"))
{
    RunJavaScriptOutput.writeLine("Could not open log file!\r\n");
} 

// Okay, start taking images
RunJavaScriptOutput.writeLine("Starting flats run.");

var out = "";

RunJavaScriptOutput.writeLine(out);
TextFile.write(out);

for (var bin = 1; bin <=4 ; bin++)
{    
    if (flatBinningControl[bin])
    {
        RunJavaScriptOutput.writeLine("processing " + bin + "x" + bin);
        
        Imager.BinX = bin;
        Imager.BinY = bin;
        
        for (var filter = firstFilter; filter <= lastFilter; filter++)
        {
            RunJavaScriptOutput.writeLine("processing " + filterNames[filter]);
            
            Imager.FilterIndexZeroBased = filter;
            for (var image = 0; image < numImages; image++)
            {
                // Take one photo at the current position
                //
                var status = "Exposing for (";
                status += exposureTimes[filter][bin];
                status += " seconds) on filter ";
                status += filterNames[filter];
                status += " (";
                status += image
                status += " of ";
                status += numImages;
                status += ") bin: " + bin + "x" + bin;

                RunJavaScriptOutput.writeLine(status);
                Imager.ExposureTime = exposureTimes[filter][bin];
                Imager.Delay = delay;
                Imager.TakeImage();

                // Write to log file only once image is completed.
                //
                status += " *Completed\r\n";
                TextFile.write(status);
            }
        }    
    }
}

// Old Style output
out = "run complete\r\n";

TextFile.write(out);
TextFile.close();

out;

