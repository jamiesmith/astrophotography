/* ClosedLoopSlew.js */
var nErr=0;

sky6StarChart.Find("Uranus");

//Turn on camera autosave
ccdsoftCamera.Connect();
ccdsoftCamera.AutoSaveOn = 1;

//Do the closed loop slew synchronously
nErr = ClosedLoopSlew.exec();