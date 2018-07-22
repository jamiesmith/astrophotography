/* Java Script */
var Out="";
var TargetRA=0;
var TargetDec=0;

function targetRaDec(t) 
{
	var err;

	sky6StarChart.LASTCOMERROR=0;
	sky6StarChart.Find(t);

	err = sky6StarChart.LASTCOMERROR;

	if (err != 0)
	{
		Out = t + " not found."
		return false;
	}
	sky6ObjectInformation.Property(54);//RA_NOW
	TargetRA = sky6ObjectInformation.ObjInfoPropOut;

	sky6ObjectInformation.Property(55);//DEC_NOW
	TargetDec = sky6ObjectInformation.ObjInfoPropOut;

	return true;
}

function main()
{
	var Target = "Venus";//Replace this

	if (targetRaDec(Target)==0)
	{
		return;
	}

	Out = String(TargetRA);
	Out += " " + String(TargetDec);
}

main();
Out = Out;

