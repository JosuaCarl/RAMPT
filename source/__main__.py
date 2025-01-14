#!/usr/bin/env python3
# __init__.py

from source.gui.main import *

if __name__ == "__main__":
	gui = Gui(pages=pages, css_file="main.css")
	orchestrator = tp.Orchestrator()

	orchestrator.run()
	gui.run(
		title="mine2sirius", port=5001, stylekit=stylekit, async_mode="threading", run_browser=False
	)
