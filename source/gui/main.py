#!/usr/bin/env python3
"""
GUI creation with Taipy.
"""

from taipy.gui import Gui
from taipy import Orchestrator

from source.gui.pages.root import *



pages = { "/": '<|toggle|theme|><center><|navbar|lov={[("/", "Application"), ("https://josuacarl.github.io/mine2sirius_pipe", "Documentation")]}|></center>',
          "configuration": root }

gui = Gui(pages=pages, css_file="main.css")



if __name__ == "__main__":
    Orchestrator().run()

    gui.run(title="mine2sirius", use_reloader=False, port=5000, run_browser=False)