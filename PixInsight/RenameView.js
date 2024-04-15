function getFilter(view)
{
   newId = "WTH";

   if (view.id.indexOf("Lum") > 0)
   {
       newId = "Lum"
   }
   else if (view.id.indexOf("Red") > 0)
   {
       newId = "Red"
       Console.writeln("ZZZZ");
   }
   else if (view.id.indexOf("Green") > 0)
   {
       newId = "Green"
   }
   else if (view.id.indexOf("Blue") > 0)
   {
       newId = "Blue"
   }
   else if (view.id.indexOf("Sii") > 0)
   {
       newId = "Sii"
   }
   else if (view.id.indexOf("Ha") > 0)
   {
       newId = "Ha"
   }
   else if (view.id.indexOf("Oiii") > 0)
   {
       newId = "Oiii"
   }
   else
   {
      newId = "WTH";
   }

   return newId;
}

function main()
{
   if (Parameters.isViewTarget)
    {
        filter = getFilter(Parameters.targetView);
        Parameters.targetView.id = filter;
    }
}

main();
