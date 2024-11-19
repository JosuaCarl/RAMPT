#!/usr/bin/env python3
"""
GUI creation with Taipy.
"""
import os
import tempfile
import datetime
import json

from werkzeug.utils import secure_filename

import taipy as tp
from taipy.gui import Gui
from taipy import Orchestrator
import taipy.gui.builder as tgb


# Configuration
from source.gui.configuration.config import *

# Pages
from .pages import *


# Working directory
work_dir_root = tempfile.gettempdir()



# SCENARIOS
scenario = tp.create_scenario( ms_analysis_config )

def update_global_variables( state ):
    global configuration

    for attribute in ["nested", "workers", "verbosity", "save_log"]:
        val = getattr(state.configuration, attribute)
        setattr( configuration.file_converter, attribute, val )
        setattr( configuration.mzmine_runner, attribute, val )
        setattr( configuration.gnps_runner, attribute, val )
        setattr( configuration.sirius_runner, attribute, val )
    state.configuration = configuration
    state.configuration.file_converter.update_regex()
    state.refresh("configuration")

def add_scenario( state, id, payload ):
    global configuration

    update_global_variables( state )
    
    configuration = state.configuration
    configuration.save( os.path.join(work_dir_root, f"{payload.get("label", "default")}_config.json") )
    
    print("ADD:")
    print(configuration.dict_representation())


def change_scenario( state, id, payload ):
    global configuration
    
    configuration.load( os.path.join(work_dir_root, f"{payload}_config.json") )
    
    state.scenario.data_nodes["ms_analysis_configuration"].write( configuration.dict_representation() )
    state.scenario.data_nodes["raw_data"].write( [scheduled_path.get("label") for scheduled_path in state.configuration.file_converter.scheduled_in] )
 

    print("CHANGE:")
    print(configuration.dict_representation())


# JOBS
job = None


# DATA
data_node = None

# OTHER
input_var = ""
press=""
def execute_input( state ):
    os.system(state.input_var)


# PAGE
with tgb.Page() as root:
    with tgb.layout( columns="1", columns__mobile="1" ):
        tgb.part()
        tgb.navbar( lov='{[("/", "Application"), ("https://josuacarl.github.io/mine2sirius_pipe", "Documentation")]}' )
        tgb.part()

    with tgb.layout( columns="1 0.1 3 0.1 1", columns__mobile="1" ):

        # Left pane
        with tgb.part():
            # Scenario selector
            tgb.text( "#### Scenarios", mode="markdown" )
            tgb.scenario_selector( "{scenario}", on_creation=add_scenario, on_change=change_scenario )
            tgb.text( "#### Data", mode="markdown" )
            tgb.data_node_selector( "{data_node}" )
        
        tgb.part()
        
        # Middle window
        with tgb.part():
            tgb.text( "## ⚙️Manual configuration", mode="markdown" )
            # General settings
            with tgb.expandable( title="General", expanded=False , hover_text=""):
                general

            # Conversion
            with tgb.expandable( title="Conversion", expanded=False, hover_text="Convert manufacturer files into community formats." ):
                tgb.part( page=conversion )

            with tgb.expandable( title="Feature finding", expanded=False, hover_text="Find features with MZmine through applying steps via a batch file."):
                feature_finding

            with tgb.expandable( title="Annotation", expanded=False, hover_text=""):
                gnps
                sirius

            with tgb.expandable( title="Analysis", expanded=False, hover_text=""):
                analysis
            

            # Pipeline showcasing
            tgb.text( "## 🎬Scenario management", mode="markdown" )
            tgb.scenario( "{scenario}", show_properties=False, show_tags=False, show_sequences=True )
            tgb.scenario_dag( "{scenario}" )
            
            tgb.text("## 📊Data", mode="markdown")
            tgb.data_node( "{data_node}" )

            tgb.text("## 🐝Jobs", mode="markdown")
            tgb.job_selector( "{job}" )

        tgb.part()

        # Right pane
        with tgb.part():
            pass

pages = {"/": root}
gui = Gui(pages=pages, css_file="styles.css")


if __name__ == "__main__":
    Orchestrator().run()

    gui.run(title="mine2sirius", use_reloader=True, port=5000, propagate=True, run_browser=False)