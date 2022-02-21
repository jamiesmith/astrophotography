#!/usr/bin/env python3

#
# This takes my usual dark frames (for the ZWO ASI-183 and QSI-690).
#
# You can change the commands after "else" to do whatever you need.
#
# Ken Sturrock
# August 26, 2018
#

from library.PySkyX_ks import *
from library.PySkyX_jrs import *

import time
import sys
import os

timeStamp("Starting Dark Frame Run.")

print("")

print("Taking generic dark frame mixture: 1, 3 and 5 minutes plus bias.")
# Duration, quantity
#
takeFauxDark("1", "1")
takeFauxDark("0", "1")
# takeFauxDark("60", "9")
# takeFauxDark("180", "9")
# takeFauxDark("300", "9")
# takeFauxDark("0", "9")

print("")

timeStamp("Finishing Dark Frame Run.")

