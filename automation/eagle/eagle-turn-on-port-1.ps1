try
{
	Invoke-WebRequest -UseBasicParsing "http://localhost:1380/setpwrout?idx=1&state=1"
}
catch { }
