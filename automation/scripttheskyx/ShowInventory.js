//This script attaches to the active photo in TheSky, locates all the light sources, and outputs the first 100

var strResult = "Done";

function ShowInventory()
{
	var cr = "\n";
	//Index into values
	var cdInventoryX = 0;
	var cdInventoryY = 1;
	var cdInventoryMagnitude = 2;
	var cdInventoryClass = 3;
	var cdInventoryFWHM = 4;
	var cdInventoryMajorAxis = 5;
	var cdInventoryMinorAxis = 6;
	var cdInventoryTheta = 7; 
	var cdInventoryEllipticity = 8;

	ccdsoftCameraImage.AttachToActive();

	//Make sure photo is saved
	var path = ccdsoftCameraImage.Path;
	if (path.length == 0)
	{
		strResult = "ShowInventory requires the photo is saved";
		return;
	}

	ccdsoftCameraImage.ShowInventory();
	
	var X = ccdsoftCameraImage.InventoryArray(cdInventoryX);
	var Y = ccdsoftCameraImage.InventoryArray(cdInventoryY);
	var Mag = ccdsoftCameraImage.InventoryArray(cdInventoryMagnitude);
	var FWHM = ccdsoftCameraImage.InventoryArray(cdInventoryFWHM);

	strResult = "Light Source Count="+X.length+cr+cr;

	var show = X.length;

	//Only show the first 100
	if (show>100)
		show = 100;

	for (ls =0; ls<show;++ls)
	{
		strResult += "LightSource" + ls + cr;
		strResult += "X=" + X[ls] + cr;
		strResult += "Y=" + Y[ls] + cr;
		strResult += "Mag=" + Mag[ls] + cr;
		strResult += "FWHM=" + FWHM[ls] + cr;
		strResult += cr;
	}

	strResult += "Done";

}

function Main()
{
	ShowInventory();
}

Main();

//An easy way to display a result
strResult
