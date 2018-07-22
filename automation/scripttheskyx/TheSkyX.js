var Out;
sky6RASCOMTele.Connect()
if (sky6RASCOMTele.isConnected=0)
{
out = "Not connected"
}
else
{
sky6RASCOMTele.GetRaDec()
 Out  = String(sky6RASCOMTele.dRa);
 Out += " " + String(sky6RASCOMTele.dDec);
}
