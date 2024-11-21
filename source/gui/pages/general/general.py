#!/usr/bin/env python3

import taipy.gui.builder as tgb

from source.helpers.classes import Step_Configuration



global_params = Step_Configuration()


def create_general():
    with tgb.layout( columns="1 0.1 1", columns__mobile="1"):
        with tgb.part():
            tgb.selector( "{global_params.platform}",
                        label="Platform", lov="Linux;Windows;MacOS", dropdown=True, hover_text="Operating system / Computational platform where this is operated." )
            tgb.number( "{global_params.workers}",
                        label="Workers", hover_text="The number of workers with which to run the program in parallel.")
            tgb.text( "Verbosity: ")
            tgb.slider( "{global_params.verbosity}",
                        label="Verbosity", min=0, max=3, hover_text="Level of verbosity during operations." )
        tgb.part()
        with tgb.part():
            tgb.toggle( "{global_params.nested}",
                        label="Nested execution", hover_text="Whether directories should be executed in a nested fashion.")
            tgb.toggle( "{global_params.save_log}",
                        label="Save logging to file", hover_text="Whether to save output and errors into a log-file.")
            tgb.toggle( "{global_params.overwrite}",
                        label="Overwrite", hover_text="Whether to overwrite upon re-execution.")