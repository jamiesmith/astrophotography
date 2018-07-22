/*   Find.js */
var Out;
var PropCnt = 189;
var p;

Out="";
sky6StarChart.Find("Saturn");

for (p=0;p<PropCnt;++p)
{
   if (sky6ObjectInformation.PropertyApplies(p) != 0)
	{
		/*Latch the property into ObjInfoPropOut*/
      sky6ObjectInformation.Property(p)

		/*Append into s*/
      Out += sky6ObjectInformation.ObjInfoPropOut + "|"

		//print(p);
   }
}
