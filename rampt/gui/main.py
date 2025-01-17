#!/usr/bin/env python3
"""
GUI creation with Taipy.
"""

import taipy as tp
from taipy.gui import Gui

from rampt.gui.pages.root import *


pages_dict = {
    "/": '<|toggle|theme|><center><|navbar|lov={[("/", "Application"), ("https://josuacarl.github.io/RAMPT", "Documentation")]}|></center>',
    "configuration": root,
}

stylekit = {"color_paper_light": "#EFE6F1", "color_background_light": "#EBE5EC"}


def main():
    ic(os.path.join(ROOT_DIR, "statics", "share", "rampt.png"))
    gui = Gui(pages=pages_dict, css_file="main.css")

    orchestrator = tp.Orchestrator()

    orchestrator.run()
    gui.run(
        title="mine2sirius",
        favicon=os.path.join(ROOT_DIR, "statics", "share", "rampt.png"),
        port=5001,
        stylekit=stylekit,
        run_browser=True,
        debug=True,
    )
