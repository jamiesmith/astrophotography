/* Java Script */

var Out;

if (sky6Dome.IsConnected==0||
	 sky6RASCOMTele.IsConnected==0)/*Connect failed for some reason*/
{
	Out = "Not connected"
}
else
{
	sky6Dome.IsCoupled = 1;
	sky6Raven.SlewDomeToTelescope();
	Out  = "OK"
}