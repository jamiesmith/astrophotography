/* Java Script */

var Out="";
var dLat;
var dLon;
var cr="\n";
var strTime;
var strDate;
var dLST;
var strLST;
var dUT;
var strUT;

var sk6DocProp_Latitude = 0;
var sk6DocProp_Longitude = 1;
var sk6DocProp_JulianDateNow=9;
var FMT_HMS        =4;
		
sky6StarChart.DocumentProperty(sk6DocProp_Latitude);
dLat = sky6StarChart.DocPropOut

sky6StarChart.DocumentProperty(sk6DocProp_Longitude);
dLon = sky6StarChart.DocPropOut

sky6StarChart.DocumentProperty(sk6DocProp_JulianDateNow);
dJD = sky6StarChart.DocPropOut

sky6Utils.ConvertJulianDateToCalender(dJD)
strDate =String(sky6Utils.dOut0 )+" "+String(sky6Utils.dOut1)+" "+String(sky6Utils.dOut2)
strTime =String(sky6Utils.dOut3 )+" "+String(sky6Utils.dOut4)+" "+String(sky6Utils.dOut5)

sky6Utils.ComputeLocalSiderealTime();
dLST = sky6Utils.dOut0;

sky6Utils.ConvertSexagesimalToString(dLST,FMT_HMS,4);
strLST = sky6Utils.strOut

sky6Utils.ComputeUniversalTime()
dUT = sky6Utils.dOut0;

sky6Utils.ConvertSexagesimalToString(dUT,FMT_HMS,4);
strUT = sky6Utils.strOut

Out += "dLat="+String(dLat)+cr;
Out += "dLon="+String(dLon)+cr;
Out += "dJD="+String(dJD)+cr;
Out += "Date="+strDate+cr;
Out += "Time="+strTime+cr;
Out += "dLST="+String(dLST)+cr;
Out += "strLST="+strLST+cr;
Out += "dUT="+String(dUT)+cr;
Out += "strUT="+String(strUT)+cr;



