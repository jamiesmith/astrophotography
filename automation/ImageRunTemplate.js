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
// The dither operation takes place only when the filters have completed
// one cycle. 
// Eash filter can have it's own exposure time.
// This is a round robin approach... if your filters are not parfocal, you may
// need to setup filter focuser offsets in TheSkyX.


///////////////////////////////////////////////////////////////////////////
const LUM   = 0;        // Just makes it easier to not screw up when it's late at night
const RED   = 1;        // change if necessary to match your filer configuration
const GREEN = 2;
const BLUE  = 3;
const SII   = 4;
const HA    = 5;
const OIII  = 6;

const filterNames = ["Luminance", "Red", "Green", "Blue", "Sii5nm", "Ha5nm", "Oiii5nm" ];
///////////////////////////////////////////////////////////////////////////


///////////////////////////////////////////////////////////////////////////
// How many images do I want? How much space in arcseconds between them
//////////////////////////////////////////////////////////////////////////////////////////  \/ \/ \/ USRER INPUT HERE 
var ditherStepSizeArcSeconds = 5.0;    // Amount of dither between exposures in arcseconds
var numImages = 30;                    // Number of Images to take with each filter
var firstFilter = LUM;
var lastFilter = OIII;
var delay = 5;                         // Delay between exposures. Give adequate settle time
var decMinus = 1.0;                    // Set one of these to zero to limit dec movements to one direction
var decPlus = 1.0;

// Each filter can have its own exposure length.
var exposureTimes = new Array(7);
exposureTimes[LUM]   = 1;
exposureTimes[RED]   = 1;
exposureTimes[GREEN] = 1;
exposureTimes[BLUE]  = 1;
exposureTimes[SII]   = 1;
exposureTimes[HA]    = 1;
exposureTimes[OIII]  = 1;
///////////////////////////////////////////////////////////////////////////////////////////////////^^^ END USER INPUT
///////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////

var Imager = ccdsoftCamera;
Imager.Autoguider = 0;
Imager.Connect();
Imager.Asynchronous = 0;
Imager.Autosave = 1;

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

var iImageCount = 0;               // How many images we have taken so far
var angle = 7.0;                   //    Past 2 PI to trip the first update
var steps = 4.0;                   // Number of steps around the circle doubles each time

var currFilter = firstFilter;      // Start first filter


// Open a text file for writing or reading
//
if(TextFile.createNew("UnguidedFilteredLog"))
{
    RunJavaScriptOutput.writeLine("Could not open log file!\r\n");
}
 

// Okay, start taking images
RunJavaScriptOutput.writeLine("Starting unguided, dithered image run.");

var out = "Dither Step size = ";
out += ditherStepSizeArcSeconds;
out += " arcseconds\r\n";
RunJavaScriptOutput.writeLine(out);
TextFile.write(out);

for (var filter = firstFilter; filter <= lastFilter; filter++)
{
    Imager.FilterIndexZeroBased = filter;
    for (var image = 0; image < numImages; image++)
    {
        // Take one photo at the current position
        //
        var status = "Exposing for (";
        status += exposureTimes[filter];
        status += " seconds) on filter ";
        status += filterNames[filter];
        status += " (";
        status += image
        status += " of ";
        status += numImages;
        status += ")";

        RunJavaScriptOutput.writeLine(status);
        Imager.ExposureTime = exposureTimes[filter];
        Imager.Delay = delay;
        Imager.TakeImage();

        // Write to log file only once image is completed.
        //
        status += " *Completed\r\n";
        TextFile.write(status);
    }
}

// Old Style output
out = "run complete\r\n";

TextFile.write(out);
TextFile.close();

out;

