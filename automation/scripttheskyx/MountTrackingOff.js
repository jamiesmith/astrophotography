/* Java Script */
var Out;
var cr;

cr = "\n";

sky6RASCOMTele.Connect();

if (sky6RASCOMTele.IsConnected==0)//Connect failed for some reason
{
	Out = "Not connected"
}
else
{
	sky6RASCOMTele.SetTracking(0,1,0,0);
	Out = "TheSkyX Build " + Application.build + cr;
	Out += "RA Rate = " +sky6RASCOMTele.dRaTrackingRate + cr;
	Out += "Dec Rate = " + sky6RASCOMTele.dDecTrackingRate + cr; 
}