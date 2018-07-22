/* Java Script */
/* Socket Start Packet */

var console = RunJavaScriptOutput;

console.writeLine("Find home initiated");
sky6RASCOMTele.Connect();
sky6RASCOMTele.FindHome();
RunJavaScriptOutput.writeLine("Find home complete");


/* Socket End Packet */