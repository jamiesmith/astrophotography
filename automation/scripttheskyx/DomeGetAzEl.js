/* Java Script */

var Out;
sky6Dome.Connect();

if (sky6Dome.IsConnected==0)/*Connect failed for some reason*/
{
	Out = "Not connected"
}
else
{
	sky6Dome.GetAzEl();
	Out  = String(sky6Dome.dAz) +"| " + String(sky6Dome.dEl);
}