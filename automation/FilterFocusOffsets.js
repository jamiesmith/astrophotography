// FilterFocusOffsets.js
// Determine filter focuser offsets.
// Prerequisits... the camera, focuser, and filterwheel are all setup and 
// connected before calling this script.
// Pick a star and subframe first.

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
    
    autofocus(imager, exposureTime, binning)
    
    imager.FilterIndexZeroBased = saveFilter;
}

function autofocus(imager, exposureTime, binning)
{
    if (isSimulator(imager))
    {
        logOutput("Skipping @focus3, running with the simulator")
    }
    else
    {    
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

const FOCUS_BINNING = 2;
var times = new Array(7);
times[LUM  ] = 3.0; 
times[RED  ] = 4.0; 
times[GREEN] = 4.0; 
times[BLUE ] = 4.0; 
times[SII  ] = 5.0; 
times[HA   ] = 5.0; 
times[OIII ] = 5.0; 

const MAX_TEMPERATURE_DEVIATION = 3.0;

var nNumSamples = 3;       // How many samples for each filter
var filters = Array();     // Which filters to test

filters.push(LUM);         // comment out any you don't want done
filters.push(RED);         // comment out any you don't want done
filters.push(GREEN);       // comment out any you don't want done
filters.push(BLUE);        // comment out any you don't want done
filters.push(SII);         // comment out any you don't want done
filters.push(HA);          // comment out any you don't want done
filters.push(OIII);        // comment out any you don't want done

logOutput("Filter Focuser Offset Wizard");


// Are we connected to the filter wheel?
ccdsoftCamera.Autoguider = false;
ccdsoftCamera.Connect();
ccdsoftCamera.Asynchronous = false;
ccdsoftCamera.Autosave = true;

var filterNames = getFilterNameArray(ccdsoftCamera);

var numFilters = filters.length;

try 
{
    ccdsoftCamera.filterWheelConnect();
}
catch(e)
{
    numFilters = 0;
}

var out = "";
logOutput("Filter count: " + numFilters);


///////////////////////////////////////////
// Do the big show
var startTemp = ccdsoftCamera.focTemperature;
logOutput("Start temp: " + startTemp);

var endTemp;

// Container for averaging. Initialize to zero
//
var focusValues = Array(numFilters);
for (i = 0; i < numFilters; i++)
{
    focusValues[i] = 0;
}

try 
{
    for (samp = 0; samp < nNumSamples; samp++) 
    {        
        for (iFilter = 0; iFilter < numFilters; iFilter++) 
        {
            autofocusWithFilter(ccdsoftCamera, iFilter, times[iFilter], FOCUS_BINNING)

            focusValues[iFilter] += ccdsoftCamera.focPosition;
            out = ccdsoftCamera.szFilterName(filters[iFilter]);
            out += " Focus position: ";
            out += ccdsoftCamera.focPosition;
            logOutput(out);            
        }
        
        // Let's see if the temperature is wandering too much
        //
        endTemp = ccdsoftCamera.focTemperature;
        if (Math.abs(endTemp - startTemp) > MAX_TEMPERATURE_DEVIATION)
        {
            break;
        }
    }

    logOutput("Ending temp: "+ endTemp);

    // Check for temp out of range
    //
    if (Math.abs(endTemp - startTemp) > MAX_TEMPERATURE_DEVIATION) 
    {
        out = "Error: Temperature variance too high: ";
        out += startTemp;
        out += " to ";
        out += endTemp;
    }
    else
    {    
        // Average the positions
        for(i = 0; i < numFilters; i++)
        {
            focusValues[i] /= nNumSamples;
        }

        out = "Averaged Positions: ";
        for(i = 0; i < numFilters; i++) 
        {
            out += focusValues[i];
            out += ", ";
        }
        out += "\n";

        out += "Offsets\n";
        for(i = 0; i < numFilters; i++) 
        {
            out += ccdsoftCamera.szFilterName(filters[i]);
            out += ":  ";
            out += (focusValues[i] - focusValues[0]);
            out += "\n";
        }
        out += "\n";
    }

}
catch(e)
{
    out = e;
}

// Output
out;



