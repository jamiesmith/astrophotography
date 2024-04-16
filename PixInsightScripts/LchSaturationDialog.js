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

#feature-id    Utilities > Lch Saturation

#feature-info  This script performs an image saturation in the Lch color space.

#include <pjsr/Sizer.jsh>          // needed to instantiate the VerticalSizer and HorizontalSizer objects
#include <pjsr/NumericControl.jsh> // needed to instantiate the NumericControl control

// define a global variable containing script's parameters
var LchSaturationParameters = {
   satAmount: 0,
   targetView: undefined,

   // stores the current parameters values into the script instance
   save: function() {
      Parameters.set("satAmount", LchSaturationParameters.satAmount);
   },

   // loads the script instance parameters
   load: function() {
      if (Parameters.has("satAmount"))
         LchSaturationParameters.satAmount = Parameters.getReal("satAmount")
   }
}

/*
 * This function takes a view and the amount value (between 0 and 1) and
 * applies a linear curves transformation on the C channel of the Lch color
 * space to increase the image saturation.
 */
 function applyCurves(view, amount) {

   // Instantiate the CurvesTransformation process
   var P = new CurvesTransformation;

   // set the curve depending on the amount
   P.c = [ // x, y
      [0.00000, 0.00000],
      [(1 - amount), 1.00000],
      [1.00000, 1.00000]
   ];
   P.ct = CurvesTransformation.prototype.Linear;

   // Perform the transformation
   P.executeOn(view);
}

/*
 * Construct the script dialog interface
 */
function LchSaturationDialog() {
   this.__base__ = Dialog;
   this.__base__();

   // let the dialog to be resizable by fragging its borders
   this.userResizable = true;

   // set the minimum width of the dialog
   this.scaledMinWidth = 340;

   // create a title area
   // 1. sets the formatted text
   // 2. sets read only, we don't want to modify it
   // 3. sets the background color
   // 4. sets a fixed height, the control can't expand or contract
   this.title = new TextBox(this);
   this.title.text = "<b>Lch Saturation</b><br><br>This script increases" +
                     " the target image saturation by linearly stretching the C " +
                     " channel in Lch color space";
   this.title.readOnly = true;
   this.title.backroundColor = 0x333333ff;
   this.title.minHeight = 80;
   this.title.maxHeight = 80;

   // add a view picker
   // 1. retrieve the whole view list (images and previews)
   // 2. sets the initially selected view
   // 3. sets the selection callback: the target view becomes the selected view
   this.viewList = new ViewList(this);
   this.viewList.getAll();
   LchSaturationParameters.targetView = this.viewList.currentView;
   this.viewList.onViewSelected = function (view) {
      LchSaturationParameters.targetView = view;
   }

   // create the input slider
   // 1. sets the text
   // 2. stes a fixed label width
   // 3. sets the range of the value
   // 4. sets the value precision (number of decimal digits)
   // 5. sets the range of the slider
   // 6. sets a tooltip text
   // 7. defines the behaviour on value change
   this.satAmountControl = new NumericControl(this);
   this.satAmountControl.label.text = "Saturation level:";
   this.satAmountControl.label.width = 60;
   this.satAmountControl.setRange(0, 1);
   this.satAmountControl.setPrecision( 2 );
   this.satAmountControl.setValue( LchSaturationParameters.satAmount );
   this.satAmountControl.slider.setRange( 0, 100 );
   this.satAmountControl.toolTip = "<p>Sets the amount of saturation.</p>";
   this.satAmountControl.onValueUpdated = function( value )
   {
      LchSaturationParameters.satAmount = value;
   };

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
   this.newInstanceButton = new ToolButton( this );
   this.newInstanceButton.icon = this.scaledResource( ":/process-interface/new-instance.png" );
   this.newInstanceButton.setScaledFixedSize( 24, 24 );
   this.newInstanceButton.toolTip = "New Instance";
   this.newInstanceButton.onMousePress = () => {
      // stores the parameters
      LchSaturationParameters.save();
      // create the script instance
      this.newInstance();
   };

   // create a horizontal slider to layout the execution button
   // 1. sets the margins
   // 2. add the newInstanceButton, a spcer and the execButton
   this.execButtonSizer = new HorizontalSizer;
   this.execButtonSizer.margin = 8;
   this.execButtonSizer.add(this.newInstanceButton)
   this.execButtonSizer.addStretch();
   this.execButtonSizer.add(this.execButton)

   // layout the dialog
   this.sizer = new VerticalSizer;
   this.sizer.margin = 8;
   this.sizer.add(this.title);
   this.sizer.addSpacing(8);
   this.sizer.add(this.viewList);
   this.sizer.addSpacing(8);
   this.sizer.add(this.satAmountControl);
   this.sizer.addSpacing(8);
   this.sizer.add(this.execButtonSizer);
   this.sizer.addStretch();
}

LchSaturationDialog.prototype = new Dialog;

function main() {

   // hide the console, we don't need it
   Console.hide();

   // perform the script on the target view
   if (Parameters.isViewTarget) {
      // load parameters
      LchSaturationParameters.load();
      applyCurves(Parameters.targetView, LchSaturationParameters.satAmount);
      return;
   }

   // is script started from an instance in global context?
   if (Parameters.isGlobalTarget) {
      // load the parameters from the instance
      LchSaturationParameters.load();
   }

   // direct contect, create and show the dialog
   let dialog = new LchSaturationDialog;
   dialog.execute();

   // check if a valid target view has been selected
   if (LchSaturationParameters.targetView && LchSaturationParameters.targetView.id) {
      // perform the Lch saturation
      applyCurves(LchSaturationParameters.targetView, LchSaturationParameters.satAmount);
   } else {
      Console.warningln("No target view is specified ");
   }
}

main();
