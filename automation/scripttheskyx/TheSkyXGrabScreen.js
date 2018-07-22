/* Java Script */
/* Save TheSkyX's current star chart as a JPG image*/

var Folder;
var Width = 1000;
var Height = 800;

var USETHESKYS = -999.0;
var cmd = 14;/*TSWC_PAINT*/
var uid = 100;
var Out;

//enum operatingSystem {osUnknown=0,osWindows=1,osMac=2,osLinux=3};

if (Application.operatingSystem == 1)
	Folder = "c:/";
else
	Folder = "./";

sky6Web.CurAz = USETHESKYS;
sky6Web.CurAlt = USETHESKYS;
sky6Web.CurRotation = USETHESKYS;
sky6Web.CurFOV = USETHESKYS;

sky6Web.CurRa = sky6StarChart.RightAscension;
sky6Web.CurDec = sky6StarChart.Declination;

sky6Web.LASTCOMERROR = 0;
sky6Web.CreateStarChart(USETHESKYS, cmd, uid, USETHESKYS, USETHESKYS, USETHESKYS, Width, Height, Folder);

if (sky6Web.LASTCOMERROR == 0) 
{
	Out = sky6Web.outputChartFileName;
}
else
{
	Out = "Error " + sky6Web.LASTCOMERROR;
}

