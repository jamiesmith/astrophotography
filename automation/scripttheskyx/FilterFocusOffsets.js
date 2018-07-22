// FilterFocusOffsets.js
// Determine filter focuser offsets.
// Prerequisits... the camera, focuser, and filterwheel are all setup and 
// connected before calling this script.

var nNumSamples = 3;							// How many samples for each filter
var filters = [ 0, 1, 2, 3 ];			// Which filters to test
var times = [ 3.0, 4.0, 4.0, 4.0 ];	// Starting time for each filter


RunJavaScriptOutput.writeLine("Filter Focuser Offset Wizard");


// Are we connected to the filter wheel?
ccdsoftCamera.Autoguider = 0;	// Main imager please...
var nNumFilters = filters.length;

try {
	ccdsoftCamera.filterWheelConnect();
	}
catch(e)
  {
  nNumFilters = 0;
  }

var out = "Filter count: ";
out += nNumFilters;
RunJavaScriptOutput.writeLine(out);


///////////////////////////////////////////
// Do the big show
var startTemp = ccdsoftCamera.focTemperature;
out = "Start temp: ";
out += startTemp;
RunJavaScriptOutput.writeLine(out);

var endTemp;

// Container for averaging. Initialize to zero
var focusValues = Array(nNumFilters);
for(i = 0; i < nNumFilters; i++)
	focusValues[i] = 0;


try {
	for(iFilter = 0; iFilter < nNumFilters; iFilter++) {
		ccdsoftCamera.FilterIndexZeroBased  = filters[iFilter];
		ccdsoftCamera.FocusExposureTime = times[iFilter];

		// Run @focus3
		for(samp = 0; samp < nNumSamples; samp++) {
			ccdsoftCamera.AtFocus3(1, false);	


			// Get the focus position for this filter
			focusValues[iFilter] += ccdsoftCamera.focPosition;
			out = ccdsoftCamera.szFilterName(filters[iFilter]);
			out += " Focus position: ";
			out += ccdsoftCamera.focPosition;
     		RunJavaScriptOutput.writeLine(out);
			}

		// Let's see if the temperature is wandering too much
		endTemp = ccdsoftCamera.focTemperature;
		if(Math.abs(endTemp - startTemp) > 1.0)
			break;
		}

	out = "Ending temp: ";
	out += endTemp;
	RunJavaScriptOutput.writeLine(out);

	// Check for temp out of range
	if(Math.abs(endTemp - startTemp) > 1.0) {
		out = "Error: Temperature variance too high: ";
		out += startTemp;
		out += " to ";
		out += endTemp;
		}
	else {	
		// Average the positions
		for(i = 0; i < nNumFilters; i++)
			focusValues[i] /= nNumSamples;

		out = "Averaged Positions: ";
		for(i = 0; i < nNumFilters; i++) {
			out += focusValues[i];
			out += ", ";
			}
		out += "\n";

	out += "Offsets\n";
	for(i = 0; i < nNumFilters; i++) {
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



