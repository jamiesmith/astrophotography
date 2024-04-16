/* PURPOSE
   Add the information to let PixInsight recognize the script name and installation path
   within the Scripts menu

   NOTES
   With respect script "07. CreateScriptInstanceGUI.js", this script contains:
   1. load/save functions inside the parameters object to store and load the
      instance parameters
   2. the draggable ToolButton to create the script instance
   3. execution context control flow in the main function


   LICENSE
   This script is part of the "An Introduction to PixInsight PJSR Scripting" workshop.

   Copyright (C) 2020 Roberto Sartori.

   This program is free software: you can redistribute it and/or modify it
   under the terms of the GNU General Public License as published by the
   Free Software Foundation, version 3 of the License.

   This program is distributed in the hope that it will be useful, but WITHOUT
   ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
   FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
   more details.

   You should have received a copy of the GNU General Public License along with
   this program.  If not, see <http://www.gnu.org/licenses/>.
 */

#feature-id    Frequent > Smart Rename View as Filter
#feature-info  This script renames the target view after the filter name

#include <pjsr/TextAlign.jsh>
#include <pjsr/Sizer.jsh>          // needed to instantiate the VerticalSizer and HorizontalSizer objects

// #include <pjsr/Sizer.jsh>          // needed to instantiate the VerticalSizer and HorizontalSizer objects
// #include <pjsr/NumericControl.jsh> // needed to instantiate the NumericControl control

// define a global variable containing script's parameters
var SmartRenameViewParameters = {
    targetView: undefined,
    prefix: "",
    suffix: "",

    // stores the current parameters values into the script instance
    save: function() {
        Parameters.set("prefix", SmartRenameViewParameters.prefix);
        Parameters.set("suffix", SmartRenameViewParameters.suffix);
    },

    // loads the script instance parameters
    load: function() {
        if (Parameters.has("prefix"))
        {
            SmartRenameViewParameters.prefix = Parameters.getString("prefix")
        }
        if (Parameters.has("suffix"))
        {
            SmartRenameViewParameters.suffix = Parameters.getString("suffix")
        }
    }
}

function renameView(view, prefix = "", suffix = "") 
{
    var filterProperty = "Instrument:Filter:Name"
    if (view.hasProperty(filterProperty))
    {
        view.id = prefix + view.propertyValue(filterProperty) + suffix;
    }
    else
    {
        console.show();
        console.warningln("Unable to determine filter, Instrument:Filter:Name not set");
    }
}

function getAllMainViews()
{
   var mainViews = [];
   var images = ImageWindow.windows;
   for ( var i in images )
   {
      if (images[i].mainView.isMainView) mainViews.push(images[i].mainView);
   }
   return mainViews;
}


/*
 * Construct the script dialog interface
 */
function SmartRenameViewDialog() 
{
    this.__base__ = Dialog;
    this.__base__();

    // let the dialog to be resizable by fragging its borders
    this.userResizable = false;

    // set the minimum width of the dialog
    //
    this.scaledMinWidth = 340;
    this.scaledMaxWidth = 340;

    // set the minimum width of the dialog
    //
    this.scaledMinheight = 300;
    this.scaledMaxheight = 300;

    // create a title area
    // 1. sets the formatted text
    // 2. sets read only, we don't want to modify it
    // 3. sets the background color
    // 4. sets a fixed height, the control can't expand or contract
    this.title = new TextBox(this);
    this.title.text = "<b>Smart Rename View</b><br><br>Rename the view based on the filter" +
                    "<br><br>don't forget delimiters if you use prefix and/or suffix";
    this.title.readOnly = true;
    this.title.backroundColor = 0x333333ff;
    this.title.minHeight = 120;
    this.title.maxHeight = 120;

    // add a view picker
    // 1. retrieve the whole view list (images and previews)
    // 2. sets the initially selected view
    // 3. sets the selection callback: the target view becomes the selected view
    this.viewList = new ViewList(this);
    this.viewList.getAll();
    SmartRenameViewParameters.targetView = this.viewList.currentView;
    this.viewList.onViewSelected = function (view) {
        SmartRenameViewParameters.targetView = view;
    }

    // prepare the execution button
    // 1. sets the text
    // 2. sets a fixed width
    // 3. sets the onClick function
    this.execButton = new PushButton(this);
    this.execButton.text = "Execute";
    this.execButton.width = 40;
    this.execButton.onClick = () => {
        this.ok();
    };

    // Add create instance button
    //
    this.newInstanceButton = new ToolButton( this );
    this.newInstanceButton.icon = this.scaledResource( ":/process-interface/new-instance.png" );
    this.newInstanceButton.setScaledFixedSize( 24, 24 );
    this.newInstanceButton.toolTip = "New Instance";
    this.newInstanceButton.onMousePress = () => {
        // stores the parameters
        SmartRenameViewParameters.save();
        // create the script instance
        this.newInstance();
    };

    // Add apply global button
    //
    this.applyGlobalButton = new ToolButton( this );
    this.applyGlobalButton.icon = this.scaledResource( ":/process-interface/apply-global.png" );
    this.applyGlobalButton.setScaledFixedSize( 24, 24 );
    this.applyGlobalButton.toolTip = "Apply to all views in current workspace";
    this.applyGlobalButton.onMousePress = () => {
        var vl = new getAllMainViews();
        for (var i = 0; i < vl.length; i++)
        {
            renameView(vl[i], SmartRenameViewParameters.prefix, SmartRenameViewParameters.suffix);            
        }
    };

    this.execButtonSizer = new HorizontalSizer;
    this.execButtonSizer.margin = 8;
    this.execButtonSizer.add(this.newInstanceButton)
    this.execButtonSizer.addSpacing( 8 );
    this.execButtonSizer.add(this.applyGlobalButton)
    this.execButtonSizer.addStretch();
    this.execButtonSizer.add(this.execButton)

    // Set up the prefix field
    //
    this.prefixLabel = new Label (this);
    this.prefixLabel.text = "Prefix:";
    this.prefixLabel.textAlignment = TextAlign_Right|TextAlign_VertCenter;

    this.prefixEdit = new Edit( this );
    this.prefixEdit.text = SmartRenameViewParameters.prefix;
    this.prefixEdit.setScaledFixedWidth( this.font.width( "MMMMMMMMMMMMMMMM" ) );
    this.prefixEdit.toolTip = "Text to add to the start of the view name";
    this.prefixEdit.onTextUpdated = function()
    {
        SmartRenameViewParameters.prefix = this.text;
    };

    this.prefixSizer = new HorizontalSizer;
    this.prefixSizer.spacing = 4;
    this.prefixSizer.add( this.prefixLabel );
    this.prefixSizer.addSpacing( 8 );
    this.prefixSizer.add( this.prefixLabel );
    this.prefixSizer.add( this.prefixEdit );
    this.prefixSizer.addStretch();

    // Set up the suffix field
    //
    this.suffixLabel = new Label (this);
    this.suffixLabel.text = "suffix:";
    this.suffixLabel.textAlignment = TextAlign_Right|TextAlign_VertCenter;

    this.suffixEdit = new Edit( this );
    this.suffixEdit.text = SmartRenameViewParameters.suffix;
    this.suffixEdit.setScaledFixedWidth( this.font.width( "MMMMMMMMMMMMMMMM" ) );
    this.suffixEdit.toolTip = "Text to add to the start of the view name";
    this.suffixEdit.onTextUpdated = function()
    {
        SmartRenameViewParameters.suffix = this.text;
    };

    this.suffixSizer = new HorizontalSizer;
    this.suffixSizer.spacing = 4;
    this.suffixSizer.add( this.suffixLabel );
    this.suffixSizer.addSpacing( 8 );
    this.suffixSizer.add( this.suffixLabel );
    this.suffixSizer.add( this.suffixEdit );
    this.suffixSizer.addStretch();

    // layout the dialog
    //
    this.sizer = new VerticalSizer;
    this.sizer.margin = 8;
    this.sizer.add(this.title);
    this.sizer.addSpacing(8);
    this.sizer.add(this.prefixSizer);
    this.sizer.addSpacing(8);
    this.sizer.add(this.suffixSizer);
    this.sizer.addSpacing(8);
    this.sizer.add(this.viewList);
    this.sizer.addSpacing(8);
    this.sizer.add(this.execButtonSizer);
    this.sizer.addStretch();
}

SmartRenameViewDialog.prototype = new Dialog;

function main() 
{
    // hide the console, we don't need it
    console.hide();

    // perform the script on the target view
    if (Parameters.isViewTarget) 
    {
    // load parameters
        SmartRenameViewParameters.load();
        renameView(Parameters.targetView, SmartRenameViewParameters.prefix, SmartRenameViewParameters.suffix);

        return;
    }

    // is script started from an instance in global context?
    if (Parameters.isGlobalTarget) 
    {
        // load the parameters from the instance
        SmartRenameViewParameters.load();
    }

    // direct contect, create and show the dialog
    let dialog = new SmartRenameViewDialog;
    dialog.execute();

    // check if a valid target view has been selected
    if (SmartRenameViewParameters.targetView && SmartRenameViewParameters.targetView.id) 
    {
        renameView(SmartRenameViewParameters.targetView, SmartRenameViewParameters.prefix, SmartRenameViewParameters.suffix);
    } 
    else 
    {
        console.show();
        console.warningln("No target view is specified ");
    }
}

main();
