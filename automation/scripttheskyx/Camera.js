//Make a shorter named variable to represent the built in camera
var Imager = ccdsoftCamera;
function TakeOnePhoto()
{
	Imager.Connect();
	Imager.Asynchronous = 0;
	Imager.TakeImage();
}

function Main()
{
	Imager.ImageUseDigitizedSkySurvey = 1;
	for (i=0; i<1; ++i)
	{
		TakeOnePhoto();
	}
}

Main();

"Done"
