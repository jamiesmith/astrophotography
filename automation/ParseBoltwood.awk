#!/usr/bin/env gawk -f
{
    FileWriteDate          = $1;
    FileWriteTime          = $2;
    TemperatureScale       = $3;
    WindSpeedScale         = $4;
    SkyTemperature         = $5;
    AmbientTemperature     = $6;
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

    printf("FileWriteDate     [%s]\n", FileWriteDate);
    printf("FileWriteTime     [%s]\n", FileWriteTime);
    printf("TemperatureScale  [%s]\n", TemperatureScale);
    printf("WindSpeedScale    [%s]\n", WindSpeedScale);
    printf("SkyTemperature    [%s]\n", SkyTemperature);
    printf("AmbientTemp       [%s]\n", AmbientTemperature);
    printf("SensorTemp        [%s]\n", SensorTemperature);
    printf("WindSpeed         [%s]\n", WindSpeed);
    printf("Humidity          [%s]\n", Humidity);
    printf("DewPoint          [%s]\n", DewPoint);
    printf("DewHeaterPct      [%s]\n", DewHeaterPercentage);
    printf("RainFlag          [%s]\n", RainFlag);
    printf("WetFlag           [%s]\n", WetFlag);
    printf("TimeSinceWrite    [%s]\n", TimeSinceLastFileWrite);
    printf("DaysSinceWrite    [%s]\n", DaysSinceLastWrite);
    printf("CloudClearFlag    [%s | %s]\n", CloudClearFlagDecoded, CloudClearFlag);
    printf("WindLimitFlag     [%s | %s]\n", WindLimitFlagDecoded, WindLimitFlag);
    printf("RainFlag          [%s | %s]\n", RainFlagDecoded, RainFlag);
    printf("DarknessFlag      [%s | %s]\n", DarknessFlagDecoded, DarknessFlag);
    printf("RoofClosedFlag    [%s | %s]\n", RoofClosedFlagDecoded, RoofClosedFlag);
    printf("AlertFlag         [%s | %s]\n", AlertFlagDecoded, AlertFlag);
}
