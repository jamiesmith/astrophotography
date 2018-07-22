// AtFocus3.js
// Run Atfocus3 from a script

var Manual = false;		// Use full auto or manual. Full auto find best subframe, uses initial guess for exposure time.
var filterIndex = 0; 	// Which filter?

RunJavaScriptOutput.writeLine("Starting @focus3 run");

try {

// First make sure we are connected to devices
ccdsoftCamera.focConnect();
ccdsoftCamera.filterWheelConnect();
ccdsoftCamera.Connect();

// Set the filter index
if(ccdsoftCamera.filterWheelIsConnected())
	ccdsoftCamera.FilterIndexZeroBased = filterIndex;

if(Manual == false) {
	
	// Run @focus3 in full auto. One sample per position, automatically determines
	// exposure time and optimal subframe
	ccdsoftCamera.FocusExposureTime = 2;
	ccdsoftCamera.AtFocus3(1, true);	
	}
else
	{		
	// Run @focus3 a bit more manually. User/script is responsible
	// for setting he expousre time and setting a subframe (or not using a subframe)
	ccdsoftCamera.FocusExposureTime = 2;
	ccdsoftCamera.Subframe = true;
	ccdsoftCamera.SubframeLeft = 0;
	ccdsoftCamera.SubframeTop = 0;
	ccdsoftCamera.SubframeRight = 512;
	ccdsoftCamera.SubframeBottom = 512;
	ccdsoftCamera.AtFocus3(1, false);
	}

out = "Focus position = ";
out += ccdsoftCamera.focPosition;

}
catch(e) {
	out = "@Focus3 error: ";
	out += e;
}



// Output
out;



