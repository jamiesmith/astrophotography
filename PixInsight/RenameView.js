function main()
{
    if (Parameters.isViewTarget)
    {
        var filterProperty = "Instrument:Filter:Name"
        targetView = Parameters.targetView;
        if (targetView.hasProperty(filterProperty))
        {
            targetView.id = targetView.propertyValue(filterProperty);
        }
        else
        {
            console.show();
            console.warningln("Unable to determine filter, Instrument:Filter:Name not set");
        }
    }
}

main();
