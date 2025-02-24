"""
    THIS LIBRARY WAS MADE FOR THE SPARKFUN XRP CONTROL BOARD.
    PLEASE USE THE ASSOCIATED MICROPYTHON UF2 FILE.
"""

import sys
if not "XRP" in sys.implementation._machine:
    raise NotImplementedError("This library does not support your version of MicroPython. "
                              + "Please update your UF2 File for the Beta XRP Controller here: "
                              + "https://github.com/Open-STEM/XRP_MicroPython/releases/tag/v2.0.0")