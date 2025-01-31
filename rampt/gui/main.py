#!/usr/bin/env python3
"""
GUI creation with Taipy.
"""

import taipy as tp
from taipy.gui import Gui

from rampt.gui.pages.root import *


pages_dict = {
    "/": '<|toggle|theme|><center><|navbar|lov={[("/configuration", "Configuration"), ("/visualization", "Visualization"), ("https://josuacarl.github.io/RAMPT", "Documentation")]}|></center>',
    "configuration": configuration,
    "visualization": visualization,
}

stylekit = {"color_paper_light": "#EFE6F1", "color_background_light": "#EBE5EC"}


def main():
    gui = Gui(pages=pages_dict, css_file="main.css")

    orchestrator = tp.Orchestrator()

    orchestrator.run(force_restart=True)
    gui.run(
        title="RAMPT",
        favicon=os.path.join("..", "rampt.ico"),
        port=5001,
        stylekit=stylekit,
        run_browser=True,
    )
