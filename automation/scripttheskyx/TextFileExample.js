var FileName = "ThisIsTheFileName";

//Create a text file and write to it
TextFile.createNew(FileName);
TextFile.write("Hello, today is ");
TextFile.write(Date() + "\n");
TextFile.write("Line1\n");
TextFile.write("Line2\n");
TextFile.write("Line3\n");
TextFile.write("Line5\n");
TextFile.close();

//Append some data to the existing file
TextFile.openForAppend(FileName);
TextFile.write("Line6\n");
TextFile.close();

//Read the above text file line by line and output to the 'Script Output' textbox below
var line;
TextFile.openForRead(FileName);
do 
{ 
	line = TextFile.readLine(); 
	RunJavaScriptOutput.writeLine(line);
} while (line.length>0);
TextFile.close();




