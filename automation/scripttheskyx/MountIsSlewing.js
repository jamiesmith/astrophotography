/* Java Script */

var TargetRA = "21";
var TargetDec = "20";
var Out;

sky6RASCOMTele.Connect();

if (sky6RASCOMTele.IsConnected==0)//Connect failed for some reason
{
	Out = "Not connected"
}
else
{
	if (sky6RASCOMTele.IsSlewComplete)
		Out  = "Not Slewing";
	else
		Out  = "Slewing";
}