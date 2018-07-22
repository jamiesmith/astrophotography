
var flatBinningControl = [
    false,   // ignore
    false,    // 1x1 binning
    true,    // 2x2 binning
    true,    // 3x3 binning
    true     // 4x4 binning    
]

///////////////////////////////////////////////////////////////////////////
var LUM     = 0;        // Just makes it easier to not screw up when it's late at night
var RED     = 1;    // change if necessary to match your filer configuration
var GREEN   = 2;
var BLUE    = 3;
var SII     = 4;
var HA      = 5;
var OIII    = 6;

var filterNames = ["Luminance", "Red", "Green", "Blue", "SII", "Ha", "OIII" ];
///////////////////////////////////////////////////////////////////////////


///////////////////////////////////////////////////////////////////////////
// How many images do I want? How much space in arcseconds between them
//////////////////////////////////////////////////////////////////////////////////////////  \/ \/ \/ USRER INPUT HERE 
var ditherStepSizeArcSeconds = 5.0;    // Amount of dither between exposures in arcseconds
var numImages = 1;                    // Number of Images to take with each filter
var firstFilter = LUM;
var lastFilter = OIII;
var delay = 0;                         // Delay between exposures. Give adequate settle time
var decMinus = 1.0;                    // Set one of these to zero to limit dec movements to one direction
var decPlus = 1.0;

// Each filter can have its own exposure length.
var exposureTimes = new Array(7);
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
if(TextFile.createNew("FlatsLog"))
{
    RunJavaScriptOutput.writeLine("Could not open log file!\r\n");
} 

// Okay, start taking images
RunJavaScriptOutput.writeLine("Starting flats run.");

var out = "Dither Step size = ";
out += ditherStepSizeArcSeconds;
out += " arcseconds\r\n";
RunJavaScriptOutput.writeLine(out);
TextFile.write(out);

for (var bin = 1; bin <=4 ; bin++)
{    
    if (flatBinningControl[bin])
    {
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

