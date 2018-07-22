/* For brevity, use simpler names for built in objects.*/
var c = RunJavaScriptOutput;
var cds = CameraDependentSetting;

/* Set this property before calling any method that actually communicates with the camera.*/
cds.autoguiderCDS = 0;

/* Query available options.*/
var vals = cds.availableOptions();

/* Show output of cds.*/
c.writeLine("Setting name:" + cds.settingName);
c.writeLine("Available Options : "+vals);
c.writeLine("Array length : "+ vals.length);


/* Show options by looping through array.*/
for (var v=0; v<vals.length;++v)
	c.writeLine(vals[v]);

//cds.currentOption = vals[0];
//cds.currentOption = "Mode 2";
//cds.currentOption = "Bad Value";

/* Show the current setting.*/
cds.currentOption