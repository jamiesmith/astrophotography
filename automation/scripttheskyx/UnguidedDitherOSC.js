// UnguidedDitherOSC.js
// Dither with ProTrack - Enhanced Version
// Richard S. Wright Jr.
// Software Bisque
// Assumptions: ProTrack is on and enabled (or your exposures are short enough you don't 
//           	need ProTrack.
//					 	You have slewed to the target and framed up things the way you want
//					 	The camera dialog is set for the binning, saving, etc.
//					 	You are already connected to both scope and camera
//           	The AutoSave is turned on, and configured for the target of choice
//						This version assumes no filters, OSC or DSLR
//


///////////////////////////////////////////////////////////////////////////
// How many images do I want? How much space in arcseconds between them
//////////////////////////////////////////////////////////////////////////////////////////  \/ \/ \/ USRER INPUT HERE 
var ditherStepSizeArcSeconds = 8.0;	     // Amount of dither between exposures in arcseconds
var numImages = 16;	    							// Number of Images to take 
var exposureTime = 300;								// Exposure time for each image
var delay = 5;			    							// Delay between exposures. Give adequate settle time
var decMinus = 1.0;		// Set one of these to zero to limit dec movements to one direction
var decPlus = 1.0;

///////////////////////////////////////////////////////////////////////////////////////////////////^^^ END USER INPUT
///////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////

var Imager = ccdsoftCamera;
Imager.Connect();
Imager.Autoguider = 0;
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

var iImageCount = 0;			// How many images we have taken so far
var angle = 7.0;				//	Past 2 PI to trip the first update
var steps = 4.0;				// Number of steps around the circle doubles each time
										// First ring will actually be 8


// Open a text file for writing 
if(TextFile.createNew("UnguidedOSCLog")) 
    RunJavaScriptOutput.writeLine("Failed to create log file!\r\n");
 

// Okay, start taking images
RunJavaScriptOutput.writeLine("Starting image run.\r\n");

while(iImageCount < numImages)
	{
	// Take one photo at the current position
	var status = "Exposing for (";
	status += exposureTime;
	status += " seconds) ";
	status += " (";
	status += (iImageCount +1);
	status += " of ";
	status += numImages;
	status += ")";

	RunJavaScriptOutput.writeLine(status);
	Imager.ExposureTime = exposureTime;
	Imager.Delay = delay;
	Imager.TakeImage();

	// Write to log file only once image is completed.
	status += " *Completed\r\n";
	TextFile.write(status);
	
	// Time for the next circle?
	if(angle > 2*3.14159265) {
		angle = 0.0;								// Reset rotation
		steps *= 2.0;							// Double steps on circle
		currRadius += ditherStepDegrees;	// Increment radius of circle by dither space
		}
	else
		angle += ((3.14159265 * 2.0) / steps);	// Next sample along ring

	// Compute next dither location
	var deltaRA  = Math.cos(angle) * currRadius/15.0;
	var deltaDEC = Math.sin(angle) * currRadius;

	// Limit dec direction changes?
	if(deltaDEC > 0) deltaDEC *= decPlus;
	if(deltaDEC < 0) deltaDEC *= decMinus;


	// Slew to next location
	RunJavaScriptOutput.writeLine("Moving OTA\r");
	sky6RASCOMTele.SlewToRaDec(startRA + deltaRA, startDEC + deltaDEC,"");					

	// Another image taken, next...
	iImageCount++;
	}

sky6RASCOMTele.Park();


// Old Style output
var out = "Dithered run complete\r\n";

TextFile.write(out);
TextFile.close();

out;

