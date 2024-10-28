#!/usr/bin/env python3
"""
GUI creation with Taipy.
"""

from taipy.gui import Gui, Markdown
import taipy.gui.builder as tgb
from source.conversion.msconv_pipe import File_Converter

# TODO: 
# 1. Make interactive elements (Buttons, File inputs, ...)
# 2. Integrate methods for precessing
# 3. Prettify the execution process with parallelization depiction

content = ""
selected_scenario = None
selected_data_node = None

pages = { "/": Markdown("pages/root.md"),
        
        }



if __name__ == "__main__":
    Gui(pages=pages, css_file="styles.css").run(title="mine2sirius", use_reloader=True, port=5000)