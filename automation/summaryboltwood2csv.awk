#!/usr/bin/env gawk -f
BEGIN {
    printf("FileWriteDate,");
    printf("FileWriteTime,");
    printf("SkyTemperature,");
    printf("AmbientTemp,");
    printf("DELTA,");
    printf("RainFlag,");
    printf("WetFlag,");
    printf("CloudClearFlag,");
    printf("Cloudy?,");
    printf("RainFlag,");
    printf("Raining?,");
    printf("AlertFlag,");
    printf("AlertFlagDecoded\n");
    
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

if (lastCloud != CloudClearFlagDecoded || lastRain != RainFlagDecoded)
{
    printf("%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n",
        FileWriteDate,
        FileWriteTime,
        SkyTemperature,
        AmbientTemperature,
        TempDelta,
        RainFlag,
        WetFlag,
        CloudClearFlag,
        CloudClearFlagDecoded,
        RainFlag,
        RainFlagDecoded,
        AlertFlag,
        AlertFlagDecoded);
}
lastCloud = CloudClearFlagDecoded;
lastRain = RainFlagDecoded
}
