#feature-id    Utilities > Smart Rename View
#feature-info  This script renames the target view after the filter name

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
