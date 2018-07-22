/* Java Script */
/*   RunQuery.js */

/*
This script runs whatever 'Current query' is loaded in TheSkyX
and returns a list of the object names.
See the Path() property to open an file based dbq.
*/
var Out;
var Result;

Out="";
sky6DataWizard.Open();

//Be careful, RunQuery is a property, do not include "()"
//Bug - Only TheSkyX 10.1.11 (build 4621 and later) resolves
//the result of RunQuery correctly to a sky6ObjectInformation
Result = sky6DataWizard.RunQuery;

if (Result.Count>0)
{
	//From sky6ObjectInformation
	var sk6ObjInfoProp_NAME1 = 0;
	var sk6ObjInfoProp_RA_2000 = 56

	for (i=0; i<Result.Count;++i)
	{
		Result.Index = i;
		Result.Property(sk6ObjInfoProp_NAME1);//Latch the object name 
		Out += Result.ObjInfoPropOut + "|"

		//Result.Property(sk6ObjInfoProp_RA_2000);//Latch something else
		//Out += Result.ObjInfoPropOut + "|"
	}
}
else
{
	Out = "No objects found."
}

if (0)//if build<4621, use this work around
{
	sky6ObjectInformation.ForDataWizard = 1;
	sky6ObjectInformation.Index = 0
	Out = sky6ObjectInformation.Count;
	sky6ObjectInformation.Index = 0
	sky6ObjectInformation.Property(0);//Latch the object name 
	Out = sky6ObjectInformation.ObjInfoPropOut
}



