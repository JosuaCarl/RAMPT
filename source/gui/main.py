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
from taipy import Config, Orchestrator
import taipy.gui.builder as tgb

import source.helpers.general as helpers
from source.helpers.types import StrPath


# Configuration loader
from configuration.config import *


# General
## Working directory
work_dir_root = tempfile.gettempdir()
def change_work_dir_root( new_root:StrPath=None ):
    global work_dir_root
    if new_root:
        if os.path.isdir( new_root ):
            work_dir_root = os.path.normpath( new_root )
        else:
            raise( ValueError(f"{new_root} is not a valid directory") )
    else:
        work_dir_root = gui._get_config("upload_folder", tempfile.gettempdir())


### Trees
def get_selection_labels( state, state_attribute:str ):
    selection_labels = [ selection.get("label") for selection in helpers.get_attribute_recursive( state, state_attribute ) ]
    return selection_labels

def add_path_to_tree( local_tree, state, path_state_attribute ):
    local_tree = path_nester.update_nested_paths( new_paths=helpers.get_attribute_recursive( state, path_state_attribute) )
    return local_tree


### Dialogs
def evaluate_dialog( state, payload_pressed, option_list ):
    value = option_list[payload_pressed["args"][0]]
    state.show_dialog = False
    return value



## Helpers
path_nester = helpers.Path_Nester()


# General variables
configuration = MS_Analysis_Configuration()



# Conversion --------------------------------------------
conv_path = "."
conv_tree_paths = []
conv_selection = ""
conv_ask = False
conv_progress = 0

def construct_conversion_selection_tree( state ):
    global conv_tree_paths
    conv_tree_paths = add_path_to_tree( conv_tree_paths, state, "conv_path")

    pruned_tree = path_nester.prune_lca( nested_paths=conv_tree_paths )
    helpers.set_attribute_recursive( state, "conv_tree_paths", pruned_tree )


def download_converted( state ):
    # GREY OUT, WHEN converted IS NOT PRESENT
    pass
    

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
                with tgb.layout( columns="1 0.1 1", columns__mobile="1"):
                    with tgb.part():
                        tgb.selector( "{configuration.platform}",
                                    label="Platform", lov="Linux;Windows;MacOS", dropdown=True, hover_text="Operating system / Computational platform where this is operated." )
                        tgb.number( "{configuration.workers}",
                                    label="Workers", hover_text="The number of workers with which to run the program in parallel.")
                        tgb.text( "Verbosity: ")
                        tgb.slider( "{configuration.verbosity}",
                                    label="Verbosity", min=0, max=3, hover_text="Level of verbosity during operations." )
                    tgb.part()
                    with tgb.part():
                        tgb.toggle( "{configuration.nested}",
                                    label="Nested execution", hover_text="Whether directories should be executed in a nested fashion.")
                        tgb.toggle( "{configuration.save_log}",
                                    label="Save logging to file", hover_text="Whether to save output and errors into a log-file.")
                        tgb.toggle( "{configuration.overwrite}",
                                    label="Overwrite", hover_text="Whether to overwrite upon re-execution.")

            # Conversion
            with tgb.expandable( title="Conversion", expanded=False, hover_text="Convert manufacturer files into community formats." ):
                with tgb.layout( columns="4 1", columns__mobile="1"):
                    with tgb.part():
                        with tgb.layout( columns="1 1", columns__mobile="1"):
                            tgb.file_selector( "{conv_path}",
                                                label="Select File", extensions="*", drop_message="Drop files for conversion here:", multiple=True,
                                                on_action=construct_conversion_selection_tree )
                            tgb.tree( "{configuration.file_converter.scheduled_in}",
                                      lov="{conv_tree_paths}", label="Select for conversion", filter=True, multiple=True, expanded=True )
                        with tgb.layout( columns="1 0.1 1", columns__mobile=1):
                            with tgb.part():
                                with tgb.layout( columns="1 1", columns__mobile="1"):
                                    tgb.text( "`msconvert`\nexecutable: ", multiline=True, mode="markdown")
                                    tgb.input( "{configuration.file_converter.msconvert_path}", hover_text="You may enter the path to msconvert if it is not accessible via \"msconvert\"" )
                            tgb.part()
                            with tgb.part():
                                tgb.selector( "{configuration.file_converter.target_format}",
                                            label="Target_format", lov="mzML;mzXML", dropdown=True, hover_text="The target format for the conversion. mzML is recommended.", width="100px")
                        
                        # Pattern matching
                        tgb.text( "**Pattern matching:**", mode="markdown")
                        with tgb.layout( columns="1 0.1 1", columns__mobile="1"):
                            with tgb.part():
                                with tgb.layout( columns="1 1", columns__mobile="1"):
                                    tgb.text( "Contains:")
                                    tgb.input( "{configuration.file_converter.contains}",
                                                hover_text="String that must be contained in file (e.g. experiment)" )
                                with tgb.layout( columns="1 1", columns__mobile="1"):
                                    tgb.text( "RegEx:")
                                    tgb.input( "{configuration.file_converter.pattern}",
                                                hover_text="Regular expression to filter file (e.g. my_experiment_.*[.]mzML)" )
                            tgb.part()
                            with tgb.part():
                                with tgb.layout( columns="1 1", columns__mobile="1"):
                                    tgb.text( "Prefix:")
                                    tgb.input( "{configuration.file_converter.prefix}",
                                                hover_text="Prefix to filter file (e.g. my_experiment)" )
                                with tgb.layout( columns="1 1", columns__mobile="1"):
                                    tgb.text( "Suffix:")
                                    tgb.input( "{configuration.file_converter.suffix}",
                                                hover_text="Suffix  to filter file (e.g. .mzML)" )

                        # Pattern matching
                        tgb.text( "**Other:**", mode="markdown")
                        with tgb.layout( columns="1 0.1 1", columns__mobile="1"):
                            with tgb.part():
                                tgb.text( "Redo-threshold", multiline=True, mode="markdown")
                                tgb.number(  "{configuration.file_converter.redo_threshold}",
                                            hover_text="File size threshold for repeating the conversion." )
                            tgb.part()
                            with tgb.part():
                                tgb.text( "Additional arguments", multiline=True, mode="markdown")
                                tgb.input( "{configuration.file_converter.additional_args}",
                                            hover_text="Additional arguments that can be given to the msconvert (works with command line interface).")
                    with tgb.part():
                        tgb.progress( "{conv_progress}" )

            with tgb.expandable( title="Feature finding", expanded=False, hover_text="Find features with MZmine through applying steps via a batch file."):
                tgb.text( "LOREM IPSUM" )
                #mzmine_path:StrPath="mzmine", batch_path:StrPath=".mzbatch", login:str="-login", valid_formats:list=["mzML", "mzXML", "imzML"],
                #save_log:bool=False, additional_args:list=[], verbosity:int=1


            with tgb.expandable( title="Annotation", expanded=False, hover_text=""):
                tgb.text( "LOREM IPSUM" )
            

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
    Config.load( os.path.join( os.path.dirname( helpers.get_internal_filepath(__file__) ), "configuration", "config.toml" ) )
    Orchestrator().run()

    gui.run(title="mine2sirius", use_reloader=True, port=5000, propagate=True, run_browser=False)