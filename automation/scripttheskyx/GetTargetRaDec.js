/* Java Script */

var Target = "Venus";/*Parameterize*/
var TargetRA=0;
var TargetDec=0;
var Out="";

var err;

sky6StarChart.LASTCOMERROR=0;
sky6StarChart.Find(Target);
err = sky6StarChart.LASTCOMERROR;

if (err != 0)
{
	Out =Target + " not found."
}
else
{
	sky6ObjectInformation.Property(54);/*RA_NOW*/
	TargetRA = sky6ObjectInformation.ObjInfoPropOut;

	sky6ObjectInformation.Property(55);/*DEC_NOW*/
	TargetDec = sky6ObjectInformation.ObjInfoPropOut;
	
	Out = String(TargetRA) + "|"+ String(TargetDec);
}


