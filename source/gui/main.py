#!/usr/bin/env python3
"""
GUI creation with Taipy.
"""

from taipy.gui import Gui
from taipy import Orchestrator

from .pages import *



pages = { "/": "<|toggle|theme|><center><|navbar|></center>",
          "configuration": root,
          "general": general,
          "conversion": conversion,
          "feature_finding": feature_finding,
          "gnps": gnps,
          "sirius": sirius,
          "analysis": analysis }

gui = Gui(pages=pages)



if __name__ == "__main__":
    Orchestrator().run()

    gui.run(title="mine2sirius", use_reloader=True, port=5000, propagate=True, run_browser=False)