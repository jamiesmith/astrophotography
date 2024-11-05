#!/usr/bin/env gawk -f
BEGIN {

printf("<html>\n");
printf("<head>\n");
printf("<link rel='stylesheet' href='weather.css'>\n");
printf("</head>\n");
printf("<body>\n");

    printf("<table><thead><tr>");
    printf("<thead>");
    printf("<tr>");
    printf("<td>AllSky</td>");
    printf("<td>Cloudy?</td>");
    printf("<td>Raining?</td>");
    printf("<td>Dark?</td>");
    printf("<td>Alert?</td>");
    printf("<td>DELTA</td>");
    printf("<td>FileWriteDate</td>");
    printf("<td>FileWriteTime</td>");
    printf("<td>AmbientTemp</td>");
    printf("<td>SkyTemp</td>");
    printf("<td>Rain Flag</td>");
    printf("<td>Wet Flag</td>");
    printf("<td>Cloud Flag</td>");
    printf("<td>RainFlag</td>");
    printf("<td>AlertFlag</td>");
    printf("<td>Changed?</td>");
    printf("</tr>");
    printf("</thead>");
    printf("<tbody>");
    
    lastRain = "";
    lastCloud = "";

}
{
    FileWriteDate          = $1;
    FileWriteTime          = $2;
    TemperatureScale       = $3;
    WindSpeedScale         = $4;
    SkyTemperature         = $5;
    AmbientTemperature     = $6;
    TempDelta              = AmbientTemperature - SkyTemperature;
    SensorTemperature      = $7;
    WindSpeed              = $8;
    Humidity               = $9;
    DewPoint               = $10;
    DewHeaterPercentage    = $11;
    RainFlag               = $12;
    WetFlag                = $13;
    TimeSinceLastFileWrite = $14;
    DaysSinceLastWrite     = $15;

    CloudClearFlag         = $16;
    switch (CloudClearFlag)
    {
        case 1:
            tmp="Clear"
            break;
        case 2:
            tmp="LightClouds"
            break;
        case 3:
            tmp="VeryCloudy";
            break;
        default:
            tmp = CloudClearFlag;
    }
    CloudClearFlagDecoded=tmp;

    WindLimitFlag          = $17;
    switch (WindLimitFlag)
    {
        case 1:
            tmp="Calm";
            break;
        case 2:
            tmp="Windy";
            break;
        case 3:
            tmp="VeryWindy";
            break;
        default:
            tmp = WindLimitFlag;

    }
    WindLimitFlagDecoded=tmp;

    RainFlag               = $18;
    switch (RainFlag)
    {
        case 1:
            tmp="Dry";
            break;
        case 2:
            tmp="Damp";
            break;
        case 3:
            tmp="Rain";
            break;
        default:
            tmp = RainFlag;
    }
    RainFlagDecoded=tmp;

    DarknessFlag           = $19;
    switch (DarknessFlag)
    {
        case 1:
            tmp = "Dark";
            break;
        case 2:
            tmp = "Dim";
            break;
        case 3:
            tmp = "Daylight";
            break;
        default:
            tmp = DarknessFlag;
    }
    DarknessFlagDecoded = tmp;

    RoofClosedFlag         = $20;
    RoofClosedFlagDecoded = "dunno";

    AlertFlag              = $21;
    switch (AlertFlag)
    {
        case 0:
            tmp = "NoAlert";
            break;
        case 1:
            tmp = "Alert";
            break;
        default:
            tmp = AlertFlag;
    }
    AlertFlagDecoded = tmp;

    image = "./data/AllSky-" FileWriteDate "-" substr(FileWriteTime,0,2) "-" substr(FileWriteTime,4,2) ".jpg"

    changed = "";
    rowClass = "";
    split($2, time, ":"); 
    hour = time[1];

    if (lastCloud != CloudClearFlagDecoded || lastRain != RainFlagDecoded)
    {
        changed = "<strong>YES</strong>";
        rowClass = "class='delta'";
    }

    if ((hour > 18 || hour < 7) && (DarknessFlagDecoded == "Dark"))
    {
        printf("<tr %s><td><a href=%s target=_blank><img src=%s/></href></td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td><strong>%s</strong></td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>\n",
            rowClass,
            image,
            image,
            CloudClearFlagDecoded,
            RainFlagDecoded,
            DarknessFlagDecoded,
            AlertFlagDecoded,
            TempDelta,
            FileWriteDate,
            FileWriteTime,
            AmbientTemperature,
            SkyTemperature,
            RainFlag,
            WetFlag,
            CloudClearFlag,
            RainFlag,
            AlertFlag,
            changed);
        lastCloud = CloudClearFlagDecoded;
        lastRain = RainFlagDecoded
    }
}
END{
printf("</tbody></table></body></html>");
}