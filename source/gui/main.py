#!/usr/bin/env python3
"""
GUI creation with Taipy.
"""

import taipy as tp
from taipy.gui import Gui

from source.gui.pages.root import *



pages = { "/": '<|toggle|theme|><center><|navbar|lov={[("/", "Application"), ("https://josuacarl.github.io/mine2sirius_pipe", "Documentation")]}|></center>',
          "configuration": root }

stylekit={
    "color_paper_light": "#EFE6F1",
    "color_background_light": "#EBE5EC",
}


if __name__ == "__main__":
    gui = Gui( pages=pages, css_file="main.css" )
    orchestrator = tp.Orchestrator()
    
    orchestrator.run()
    gui.run( title="mine2sirius", port=5001, stylekit=stylekit, async_mode="threading", run_browser=False )
