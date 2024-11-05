// MessierMarathon.js
// Messier Marathon Script
// Initially by Richard S. Wright Jr.
// Software Bisque

/* This script can easily be generalized for any kind of nights observing goals.
    Very simply, it takes a list of objects, and images everyhing it can in the list.
    The other input parameters, are how long to expose, how many exposures to make, etc.
    You can also choose to refocus periodically with @focus3.
    (This is for one shot color cameras, you'll have to add filters yourself)
    The priority is what is setting first. So, the lowest objet to the west is picked
    first. Then the next higher object, etc. until we have to shoot targets on the east
    side of the meridian. On the east side of the meridian of course we choose the target
    that is the highest.
    
    At the end, a list of targets sucessfully imaged is presented, and a list of targets that were 
    missed because they were below the horizon. You could used the missed targets list to 
    rebuild a new list for another attempt, or restart after waiting for objects to get above
     the horizon.

    The script allows for continuous "retries", that is when there are remaining objects, but they 
    are below the minimum altitude set, it will wait for one hour (also configurble) and restart
    the remaining list.

*/

/////////////////////////////////////////////////////////////////////////////////////
// This is the list of targets to shoot. You can remove specific targets that you
// might already have, etc.
// My Missing targets

var Objects = [    
"M1",    "M2",    "M3",     "M4",     "M5",
"M6",    "M7",    "M8",     "M9",     "M10",
"M11",   "M12",   "M13",    "M14",    "M15",
"M16",   "M17",   "M18",    "M19",    "M20",
"M21",   "M22",   "M23",    "M24",    "M25",
"M26",   "M27",   "M28",    "M29",    "M30",
"M31",   "M32",   "M33",    "M34",    "M35",
"M36",   "M37",   "M38",    "M39",    "M40",
"M41",   "M42",   "M43",    "M44",    "M45",
"M46",   "M47",   "M48",    "M49",    "M50",
"M51",   "M52",   "M53",    "M54",    "M55",
"M56",   "M57",   "M58",    "M59",    "M60",
"M61",   "M62",   "M63",    "M64",    "M65",
"M66",   "M67",   "M68",    "M69",    "M70",
"M71",   "M72",   "M73",    "M74",    "M75",
"M76",   "M77",   "M78",    "M79",    "M80",               
"M81",   "M82",   "M83",    "M84",    "M85",               
"M86",   "M87",   "M88",    "M89",    "M90",               
"M91",   "M92",   "M93",    "M94",    "M95",               
"M96",   "M97",   "M98",    "M99",    "M100",          
"M101",  "M102",  "M103",   "M104",   "M105",          
"M106",  "M107",  "M108",   "M109",   "M110"               
];


/////////////////////////////////////////////////////////////////////////////
// Globals that you can muck with
var nExposures = 1;          // Number of exposures per target
var exposureTime = 300.0;    // Number of seconds for each exposure
var exposureDelay = 5.0;     // Delay between exposures
var ditherArcSeconds = 0.0;  // Dither amount per exposure (in arcseconds)
                                    
var focusEveryXObjects = 500;       // Refocus every so many targets (just make arbitrarily large to skip)
var minAltitude = 22.0;             // Minumum altitude at which something can be imaged
var maxAltitude = 88.0;             // Minumum altitude at which something can be imaged
var waitRetryDelay = 60; //60*60;   // If we run out of targets, wait this long (in seconds) and try clearing the list again
var FileName = "MessierLog";        // Log file as .txt (don't put .txt)

///////////////////////////////////////////////////////////////////////////
// Don't touch these end user...

// Other variables we need
var sky6ObjInfoProp_AZM =58;
var sky6ObjInfoProp_ALT =59;
var sky6ObjInfoProp_RA_NOW =54;
var sky6ObjInfoProp_DEC_NOW =55;
var imagedList = "Targets Imaged: ";
var notImagedList = "Targets Not Imaged: ";

// The current targets coordinates
var targetRA = 0.0;
var targetDEC = 0.0;
var targetALT = 0.0;
var targetAZ = 0.0;


///////////////////////////////////////////////////////////////////////////
// FUNCTIONS that do repeatable tasks
///////////////////////////////////////////////////////////////////////////

///////////////////////////////////////////////////////////////////////
// Write to both the JavaScript output window and a text log file
function logOutput(logText)
{
    RunJavaScriptOutput.writeLine(logText);
    TextFile.write(logText);
}


///////////////////////////////////////////////////////////////////////////
// Find the next best candidate object
// This also removes the oject from the main list. If no objects are available
// above the minimum altitude limit it returns specifically returns "None"
function findNextCandidate()
{
    logOutput("Searching for next candidate object...");

    var nBestObjectIndex = -1;
    var Azimuth = -1.0;
    var Altitude = -1.0;
    
    for(i = 0; i < Objects.length; i++) 
    {
        sky6StarChart.LASTCOMERROR = 0;
        sky6StarChart.Find(Objects[i]);
        
        out = "";
        // Get the alt/az, and make sure they actually exist!
        if (sky6StarChart.LASTCOMERROR != 0)
        {
            out = Objects[i] + "could not be found!."
            throw new Error(out);
         }
    
        // Oject exists, get pertinent info about it
        sky6ObjectInformation.Property(sky6ObjInfoProp_AZM);
        Azimuth = sky6ObjectInformation.ObjInfoPropOut;
        sky6ObjectInformation.Property(sky6ObjInfoProp_ALT);
        Altitude = sky6ObjectInformation.ObjInfoPropOut;
        sky6ObjectInformation.Property(sky6ObjInfoProp_RA_NOW);
        RA = sky6ObjectInformation.ObjInfoPropOut;
        sky6ObjectInformation.Property(sky6ObjInfoProp_DEC_NOW);
        DEC = sky6ObjectInformation.ObjInfoPropOut;
        
        // If this is the first time through the loop, the first object (so far)
        // is the best object, as long as it's above the horizon
        if (nBestObjectIndex < 0)
        {    // Seeking first object above the horizon
            if ((Altitude > minAltitude) && (Altitude < maxAltitude))
            {
                nBestObjectIndex = i;
                targetRA = RA;
                targetDEC = DEC;
                targetAZ = Azimuth;
                targetALT = Altitude;
            }
            continue;    // Next item
        }

        ///////////////////////////////////////////////////////////
        // There are several criteria for seeing if this current object
        // is a better next target. For starters, is it even above the horizon?     
        // Nope, below the horizon, that's a non starter no matter what
        if ((Altitude < minAltitude) || (Altitude > maxAltitude))
        {            
            continue;
        }


        // If we have an object in the west already (setting), and this new object is the
        // East (rising), skip it out of hand
        if (targetAZ > 180.0 && Azimuth < 180.0)
        {
            continue;
        }

        // If the last known good target is to the East (rising), and the candidate is to the West (setting),
        // It is automatically a better fit because we preference the West side first
        // because these objects are setting
        if (targetAZ < 180.0 && Azimuth > 180.0) 
        {
            nBestObjectIndex = i;
            targetRA = RA;
            targetDEC = DEC;
            targetAZ = Azimuth;
            targetALT = Altitude;
            continue;
        }

        // Both the last best guess and the new candidate are on the same side of the meridian

        // If they are both West, the lowest one wins
        if (Azimuth > 180.0 && targetAZ > 180.0) 
        {
            if (Altitude < targetALT) 
            {
                nBestObjectIndex = i;
                targetRA = RA;
                targetDEC = DEC;
                targetAZ = Azimuth;
                targetALT = Altitude;
            }
            continue;
        }

        // They are both on the East side, which means we are cleaning up
        if (Altitude > targetALT) 
        {
            nBestObjectIndex = i;
            targetRA = RA;
            targetDEC = DEC;
            targetAZ = Azimuth;
            targetALT = Altitude;
            }
        }
 

    // Perhaps nothing remains that is aviailable?
    if (nBestObjectIndex < 0)
    {
        return "None";
    }

    // This is what we will return
    out = Objects[nBestObjectIndex];

    // Make this the current target
    sky6StarChart.Find(Objects[nBestObjectIndex]);

    // Remove it from the list though
    Objects.splice(nBestObjectIndex, 1);
    
    return out;
}



/////////////////////////////////////////////////////////////////////
// Main loop
function ProcessList()
{
    var nTargets = 0;
    while(Objects.length > 0) 
    {
        var objectIndex = 0;
    
        // Find the index of the lowest object we haven't shot yet to the west.
        // If we have no objects to the west, start picking from the east, but
        // select the highest objects first    
        // Get the next best object we have not imaged yet
        var Object = findNextCandidate();
        if (Object == "None")         // Essentially return if no objects are high enough
        {
            break;
        }

        // Wait.. it is possible it is below the horizon (or minimum limit)?
        if (targetALT < minAltitude)    // We still have objects in the list, 
        {
            break;    // But they are all below the horizon
        }

        // Slew to the initial target coordinates
        out = "Slewing to target: ";
        out += Object;
        logOutput(out);
        sky6RASCOMTele.Asynchronous = false;
        
        try 
        {
        sky6RASCOMTele.SlewToRaDec(targetRA, targetDEC, Object);
        }
        catch(e) 
        {
            logOutput("Caught an exception slewing");
            break;
        }        
        
        // We've slewed to a target... do we need to refocus?
        if (nTargets == focusEveryXObjects) 
        {
            logOutput("Running @focus3");
            Imager.BinX = 2;
            Imager.BinY = 2;
            Imager.Delay = 0;
            Imager.ExposureTime = 3;     // Three second exposures for focus samples
            Imager.AtFocus3(3, true);    // Three samples per position, full auto on subframe selection


            // Done, reset the counter, bin mode, and delay
            Imager.BinX = 1;
            Imager.BinY = 1;
            Imager.Delay = exposureDelay;
            Imager.ExposureTime = exposureTime;
            nTarget = 0;
        }

        // Image it
        out = "Imaging object: ";
        out += Object;
        out += " at Altitude: ";
        out += targetALT;
        out += " Azimuth: ";
        out += targetAZ;
        out += " at: "
        out += Date();

        logOutput(out);

        Imager.AutoSavePrefix = Object + "_";
        for(exp = 0 ; exp < nExposures; exp++) 
        {
            Imager.TakeImage();

            // Dither, just bump to east, KISS (Keep it Simple S...)
            if (ditherArcSeconds != 0)
            {
                sky6RASCOMTele.Jog("E", ditherArcSeconds / 60.0);
            }
        }

        imagedList += Object;
        imagedList += ", ";
        nTargets++;
    }
}


//////////////////////////////////////////////////////////////////////
// THINGS START HAPPENING HERE
//////////////////////////////////////////////////////////////////////
TextFile.createNew(FileName);
var out = "Imaging ";
out += Objects.length;
out += " Targets, starting at ";
out += Date();
logOutput("******************************************");
logOutput(out);


/////////////////////////////////////////////////////////////////////
// Make sure we are connected to the imager
try 
{
    var Imager = ccdsoftCamera;
    Imager.Autoguider = 0;
    Imager.Asynchronous = 0;
    Imager.Autosave = 1;
    Imager.Delay = exposureDelay;
    Imager.ExposureTime = exposureTime;
    Imager.Connect();
    Imager.BinX = 1;
    Imager.BinY = 1;
}
catch(e)
{
    throw new Error("No connection to the main imager!");
}


/////////////////////////////////////////////////////////////////////
// Make sure we are connected to the mount
try 
{
    sky6RASCOMTele.Connect();
}
catch(e) 
{
    throw new Error("No connection to the mount!");
}


// Process the list of targets
ProcessList();

// Were they all processed, or were remaining targets just too low?
// If there are still targets in the list, wait... and do, just one more iteration
while (Objects.length > 0)
{
    out = "\n\n##################################################\n"
    out += "There are ";
    out += Objects.length;
    out += " objects remaining that are too low. Waiting ";
    out += waitRetryDelay;
    out += " seconds. ";
    out += Date();
    out += "\n##################################################\n\n"
    logOutput(out);

    // Wait (one hour default) and then take a one second sacrificial image.
    Imager.Delay = waitRetryDelay;
    Imager.ExposureTime = 1;
    Imager.AutoSavePrefix = "WaitFrame_";    // Reset to object name on next good image
    
    Imager.TakeImage();

    Imager.Delay = exposureDelay;            // Reset for resume 
    Imager.ExposureTime = exposureTime;

    out = "Attempting to resume at ";
    out += Date();
    logOutput(out);
    ProcessList();                           // Give the list another crack
}


///////////////////////////////////////////////////////////
// All objects that can be imaged have been.
if (Objects.length == 0)
{
    notImagedList += "None."
}
else 
{
    for(i = 0; i < Objects.length; i++) 
    {
        notImagedList += Objects[i];

        if (i < Objects.length-1)
        {
            notImagedList += ", ";
        }
        else
        {
            notImagedList += ".";
        }
    }
}

/////////////////////////////////////////////////////////////////////////////////////////
logOutput("Finished Messier Marathon");
logOutput(Date());
logOutput("******************************************");
logOutput(imagedList);
logOutput(notImagedList);
TextFile.close();
