#!/usr/bin/env python3
"""
GUI creation with Taipy.
"""
import os
import tempfile
import datetime
import yaml

from werkzeug.utils import secure_filename

from taipy.gui import Gui
from taipy import Config, Orchestrator
import taipy.gui.builder as tgb

import source.helpers.general as helpers
from source.helpers.types import StrPath

# Import of Pipeline Steps
from source.conversion.msconv_pipe import File_Converter
from source.feature_finding.mzmine_pipe import MZmine_Runner
from source.annotation.sirius_pipe import Sirius_Runner
from source.annotation.gnps_pipe import GNPS_Runner

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


## State handling
def extract_attribute( state, state_attribute:str ):
    return getattr( state, state_attribute )

def replace_attribute( state, state_attribute:str, replacement ):
    setattr( state, state_attribute, replacement )
    state.refresh( state_attribute )

def update_class_instance( class_instance, state, key, value ):
    class_instance.update( {key: value} )

def extend_local_list( local_list, state, state_attribute ):
    value = extract_attribute( state, state_attribute )
    if isinstance( value, list ):
        local_list.extend( value )
    else:
        local_list.append( value )
    return local_list


### Trees
def get_selection_labels( state, state_attribute:str ):
    selection_labels = [ selection.get("label") for selection in extract_attribute( state, state_attribute ) ]
    return selection_labels

def add_path_to_tree( local_tree, state, path_state_attribute ):
    local_tree = path_nester.update_nested_paths( new_paths=extract_attribute( state, path_state_attribute) )
    return local_tree


### Dialogs
def evaluate_dialog( state, payload_pressed, option_list ):
    value = option_list[payload_pressed["args"][0]]
    state.show_dialog = False
    return value



## Helpers
path_nester = helpers.Path_Nester()


# TODO integrate configuration into class
class MS_Analysis_Configuration:
    def __init__( self ): #, construction_dict:dict=None ):
        #if construction_dict:
        #    self.__dict__ = construction_dict
        #else:
        self.platform       = "Linux"
        self.overwrite      = False
        self.nested         = True
        self.save_log       = True
        self.verbosity      = 1
        self.file_converter = File_Converter()
        self.mzmine_runner  = MZmine_Runner()
        self.gnps_runner    = GNPS_Runner()
        self.sirius_runner  = Sirius_Runner()


    def update( self, dictionary:dict, **kwargs ):
        if not dictionary:
            dictionary = kwargs
        for key, value in dictionary:
            setattr( self, key, value )

    def save( self, location ):
        with open( location, "w") as f:
            yaml.safe_dump( self, f )


# General variables
configuration = MS_Analysis_Configuration()

def change_global_attibute( state, state_attribute:str ):
    global file_converter

    value = extract_attribute( state, state_attribute )
    for pipe_step in [file_converter]:
        if hasattr( pipe_step, state_attribute):
            setattr( pipe_step, state_attribute, value)
    print(value)



# Conversion --------------------------------------------
conv_path = ""
conv_tree_paths = []
conv_selection = ""
conv_ask = False
conv_progress = 0
file_converter = File_Converter()

def construct_conversion_selection_tree( state ):
    global conv_tree_paths
    conv_tree_paths = add_path_to_tree( conv_tree_paths, state, "conv_path")
    replace_attribute( state, "conv_tree_paths", conv_tree_paths )





def download_converted( state ):
    # GREY OUT, WHEN converted IS NOT PRESENT
    
    pass



# SCENARIOS
scenario = ""

def add_scenario( state, id ):
    configuration.save( os.path.join(work_dir_root, f"{id}_config.yaml") )
    configuration.update()


def change_scenario( state, id ):
    with open( os.path.join(work_dir_root, f"{id}_config.yaml"), "w") as f:
        configuration = yaml.safe_load( f ) # MS_Analysis_Configuration( yaml.safe_load( f ) )
    print( configuration )


# JOBS
job = ""


# DATA
data_node = ""

    

with tgb.Page() as root:
    with tgb.layout( columns="1", columns__mobile="1" ):
        tgb.navbar( lov='{[("/", "Application"), ("https://josuacarl.github.io/mine2sirius_pipe", "Documentation")]}' )

    with tgb.layout( columns="1 3 1", columns__mobile="1" ):
        with tgb.part():
            # Scenario selector
            tgb.scenario_selector( "{scenario}", on_creation=add_scenario, on_change=change_scenario )
        
        # Main window
        with tgb.part():
            tgb.text( "## ⚙️Manual configuration", mode="markdown" )

            # General settings
            with tgb.expandable( title="General" , expanded=False , hover_text=""):
                with tgb.layout( columns="1 0.1 1", columns__mobile="1"):
                    with tgb.part():
                        tgb.selector( "{configuration.platform}",
                                    label="Platform", lov="Linux;Windows;MacOS", dropdown=True, hover_text="Operating system / Computational platform where this is operated." )
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
                            tgb.tree( "{conv_selection}", lov="{conv_tree_paths}", label="Select for conversion", filter=True, multiple=True, expanded=True )
                        with tgb.layout( columns="1 0.1 1", columns__mobile=1):
                            with tgb.part():
                                with tgb.layout( columns="1 1", columns__mobile="1"):
                                    tgb.text( "msconvert command/path: ")
                                    tgb.input( "{configuration.file_converter.msconvert_path}", hover_text="You may enter the path to msconvert if it is not accessible via \"msconvert\"" )
                            tgb.part()
                            with tgb.part():
                                tgb.selector( "{configuration.file_converter.target_format}",
                                            label="Target_format", lov="mzML;mzXML", dropdown=True, hover_text="The target format for the conversion. mzML is recommended.", width="100px")
                        with tgb.part():
                            tgb.input( "{configuration.file_converter.suffix}",
                                        hover_text="Suffix  to filter file (e.g. .mzML)" )
                            tgb.input( "{configuration.file_converter.prefix}",
                                        hover_text="Prefix to filter file (e.g. my_experiment)" )
                            tgb.input( "{configuration.file_converter.contains}",
                                        hover_text="String that must be contained in file (e.g. experiment)" )
                            tgb.input( "{configuration.file_converter.pattern}",
                                        hover_text="Regular expression to filter file (e.g. my_experiment_.*[.]mzML)" )
                        tgb.number(  "{configuration.file_converter.redo_threshold}",
                                     hover_text="File size threshold for repeating the conversion." )
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
            

            # Scenario
            tgb.text( "## 🎬Scenario management", mode="markdown" )
            tgb.scenario( "{scenario}", show_tags=False, show_properties=False, show_sequences=False )
            tgb.scenario_dag( "{scenario}" )
            
            tgb.text("## 🐝Jobs", mode="markdown")
            tgb.job_selector( "{job}" )

            tgb.data_node_selector( "{data_node}" )
        with tgb.part():
            pass

pages = {"/": root}
gui = Gui(pages=pages, css_file="styles.css")


if __name__ == "__main__":
    Config.load( os.path.join( os.path.dirname( helpers.get_internal_filepath(__file__) ), "configuration", "config.toml" ) )
    Orchestrator().run()

    gui.run(title="mine2sirius", use_reloader=True, port=5000, propagate=True, run_browser=False)