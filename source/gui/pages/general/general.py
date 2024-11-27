#!/usr/bin/env python3

import taipy.gui.builder as tgb

from source.helpers.classes import Step_Configuration



global_params = Step_Configuration()


def create_general():
    tgb.text( "###### Computation:", mode="markdown")
    with tgb.layout( columns="1 1 1", columns__mobile="1", gap="5%"):
        tgb.toggle( "{local}",
                label="Process locally", hover_text="Whether to use the server functionality of taipy to upload files and process them,\
                                                    or to use files that are present on the local machine.")
        tgb.selector( "{global_params.platform}",
                    label="Platform", lov="Linux;Windows;MacOS", dropdown=True, hover_text="Operating system / Computational platform where this is operated." )
        tgb.number( "{global_params.workers}",
                    label="Workers", hover_text="The number of workers with which to run the program in parallel.")
    

    tgb.text( "###### Execution parameters:", mode="markdown")
    with tgb.layout( columns="1 1 1 1", columns__mobile="1", gap="5%"):
        tgb.toggle( "{global_params.nested}",
                    label="Nested execution", hover_text="Whether directories should be executed in a nested fashion.")
        tgb.toggle( "{global_params.save_log}",
                    label="Save logging to file", hover_text="Whether to save output and errors into a log-file.")
        tgb.toggle( "{global_params.overwrite}",
                    label="Overwrite", hover_text="Whether to overwrite upon re-execution.")
        with tgb.part():
            tgb.text( "Verbosity: ")
            tgb.slider( "{global_params.verbosity}",
                        label="Verbosity", min=0, max=3, hover_text="Level of verbosity during operations." )