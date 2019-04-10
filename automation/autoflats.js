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
var ditherStepSizeArcSeconds = 5.0;     // Amount of dither between exposures in arcseconds
var numImages = 96;                     // Number of Images to take (TOTAL including all filters)
var firstFilter = RED;                 // Start with Lum
var lastFilter = BLUE;                 // Stop with Blue
var delay = 5;                         // Delay between exposures. Give adequate settle time
var decMinus = 1.0;        // Set one of these to zero to limit dec movements to one direction
var decPlus = 1.0;

// Each filter can have its own exposure length.
var exposureTimes = new Array(7);
exposureTimes[LUM  ] = 300;
exposureTimes[RED  ] = 120;
exposureTimes[GREEN] = 120;
exposureTimes[BLUE ] = 120;
exposureTimes[SII  ] = 900;
exposureTimes[HA   ] = 900;
exposureTimes[OIII ] = 900;
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

var iImageCount = 0;            // How many images we have taken so far
var angle = 7.0;                //    Past 2 PI to trip the first update
var steps = 4.0;                // Number of steps around the circle doubles each time
                                        // First ring will actually be 8
var currFilter = firstFilter;            // Start first filter


// Open a text file for writing or reading
if(TextFile.createNew("UnguidedFilteredLog")) 
    RunJavaScriptOutput.writeLine("Could not open log file!\r\n");
 

// Okay, start taking images
RunJavaScriptOutput.writeLine("Starting unguided, dithered image run.");
var out = "Dither Step size = ";
out += ditherStepSizeArcSeconds;
out += " arcseconds\r\n";
RunJavaScriptOutput.writeLine(out);
TextFile.write(out);

while (iImageCount < numImages)
{
    Imager.FilterIndexZeroBased = currFilter;

    // Take one photo at the current position
    var status = "Exposing for (";
    status += exposureTimes[currFilter];
    status += " seconds) on filter ";
    status += filterNames[currFilter];
    status += " (";
    status += Math.floor(iImageCount / ((lastFilter - firstFilter) + 1))+1;
    status += " of ";
    status += numImages / ((lastFilter - firstFilter)+1);
    status += ")";

    RunJavaScriptOutput.writeLine(status);
    Imager.ExposureTime = exposureTimes[currFilter];
    Imager.Delay = delay;
    Imager.TakeImage();

    // Write to log file only once image is completed.
    status += " *Completed\r\n";
    TextFile.write(status);
    
    // Change Filters
    currFilter++;
    if(currFilter > lastFilter) 
    {
        currFilter = firstFilter;    // Back to first, now do dither.
        
        // Time for the next circle?
        if(angle > 2*3.14159265) 
        {
            angle = 0.0;                                // Reset rotation
            steps *= 2.0;                            // Double steps on circle
            currRadius += ditherStepDegrees;    // Increment radius of circle by dither space
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
        RunJavaScriptOutput.writeLine("Moving OTA\r");
        sky6RASCOMTele.SlewToRaDec(startRA + deltaRA, startDEC + deltaDEC,"");


        // Done.
    }        

    // Another image taken, next...
    iImageCount++;
}

sky6RASCOMTele.Park();

// Old Style output
out = "Dithered run complete\r\n";

TextFile.write(out);
TextFile.close();

out;

