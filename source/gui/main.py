#!/usr/bin/env python3
"""
GUI creation with Taipy.
"""
import os
import tempfile
import datetime

from werkzeug.utils import secure_filename

from taipy.gui import Gui
from taipy import Config, Orchestrator
import taipy.gui.builder as tgb

import source.helpers.general as helpers
from source.helpers.types import StrPath

from source.conversion.msconv_pipe import File_Converter



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


## Projects 
project_counter = 0
project_name = f"{datetime.date.today()}_{project_counter}"
project_path = os.path.join( work_dir_root, project_name )
projects = [ {"name": project_name, "path": project_path} ]

def update_projects( project_id, project_name:str, project_path:StrPath ):
    global projects
    projects.append( {"id": project_id, "name": project_name, "path": project_path} )


def add_project( new_project_name:str=None ):
    global project_name
    global project_path
    global project_counter

    project_counter += 1
    
    if new_project_name:
        if os.path.isdir( new_project_name ):
            directory, name = os.path.split( new_project_name )
            project_name = name
            change_work_dir_root( new_root=directory )
        else:
            project_name = new_project_name
    else:
        project_name = f"{datetime.date.today()}_{project_counter}"
    project_path = os.path.join( work_dir_root, secure_filename( project_name ) )
    update_projects( project_name, project_path )


def change_project( path:StrPath ):
    global project_name
    global project_path
    global projects

    for project in projects:
        if projects.get("path") == path:
            project_path = project.get("path")
            project_name = project.get("name")
    


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


# General variables
platform = ""
overwrite = False
show_ask_overwrite = False

def evaluate_ask_overwrite( state, _, payload_pressed, option_list ):
    state.overwrite = evaluate_dialog( state, payload_pressed, option_list)

def ask_overwrite( state ):
    state.show_ask_overwrite = True
    return state



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




def evaluate_ask_overwrite( state, _, payload_pressed, option_list ):
    state.overwrite = evaluate_dialog( state, payload_pressed, option_list)


def convert_selected( state ):
    global project_path
    conv_out_path = os.path.join( project_path, "converted" )

    selected_for_conversion = extract_attribute( state, "conv_selection" )
    if os.path.isdir( conv_out_path ) and not state.conv_overwrite:
        state = ask_overwrite( state )
        if not state.overwrite:
            return False
    else:
        os.makedirs( conv_out_path , exist_ok=True )

    for i, in_path in enumerate(selected_for_conversion):
        file_converter.convert_file( in_path=in_path, out_path=conv_out_path )
        state.conv_progress = i + 1 / len( selected_for_conversion )
    
    return True

def download_converted( state ):
    # GREY OUT, WHEN converted IS NOT PRESENT
    
    pass



# SCENARIOS
scenario = ""

# JOBS
job = ""


# OTHER
def print_state_properies( state ):
    print("STATE INFO:")
    print(state)
    print(dir(state))
    print(state.__dict__)
    print(state.path)
    

with tgb.Page() as root:
    with tgb.layout( columns="1", columns__mobile="1" ):
        tgb.navbar( lov='{[("/", "Application"), ("https://josuacarl.github.io/mine2sirius_pipe", "Documentation")]}' )

    with tgb.layout( columns="1 3 1", columns__mobile="1" ):
        with tgb.part():
            tgb.scenario_selector( "{scenario}" )
        
        # Main window
        with tgb.part():
            tgb.text( "## Manual configuration", mode="markdown" )

            # General settings
            with tgb.expandable( title="General" , expanded=False , hover_text=""):
                tgb.input( "{project}", hover_text="Use the field to generate or switch between projects.")
                # TODO: Add Project integration
                tgb.selector( "{platform}",
                              label="Platform", lov="Linux;Windows;MacOS",
                              on_change=lambda state, key, value: update_class_instance( file_converter, state, key, value ) )
                tgb.toggle( "{overwrite}",
                            label="Overwrite", lov="True;False", dropdown=True,
                            on_change=lambda state : print( state.overwrite ) )
            
            # Conversion
            with tgb.expandable( title="Conversion", expanded=False, hover_text="Convert manufacturer files into community formats." ):
                with tgb.layout( columns="4 1", columns__mobile="1"):
                    with tgb.part():
                        tgb.text( "#### Settings", mode="markdown" )                        
                        tgb.text( "#### File selection", mode="markdown" )
                        tgb.file_selector( "{conv_path}",
                                        label="Select File", extensions="*", drop_message="Drop files for conversion here:", multiple=True,
                                        on_action=construct_conversion_selection_tree )
                        
                        tgb.dialog( "{show_ask_overwrite}", labels="Yes;No", title="This project was already converted.\nShould it be done again ?", on_action=evaluate_ask_overwrite)
                        tgb.tree( "{conv_selection}", lov="{conv_tree_paths}", label="Select for conversion", filter=True, multiple=True, expanded=True )

                        tgb.button( label="Convert selected", on_action=convert_selected )

                    with tgb.part():
                        tgb.progress( "{conv_progress}" )


            with tgb.expandable( title="Processing", expanded=False, hover_text="Process the data with mzmine through a batch file."):
                tgb.text( "LOREM IPSUM" )
            
            tgb.text( "## Scenario management", mode="markdown" )
            tgb.scenario( "{scenario}", show_tags=False, show_properties=False, show_sequences=False )
            tgb.scenario_dag( "{scenario}" )
            
            tgb.text("## Jobs", mode="markdown")
            tgb.job_selector( "{job}" )


        with tgb.part():
            pass


pages = { "/": root }
gui = Gui(pages=pages, css_file="styles.css")


if __name__ == "__main__":
    Config.load( os.path.join( os.path.dirname( helpers.get_internal_filepath(__file__) ), "configuration", "config.toml" ) )
    Orchestrator().run()

    gui.run(title="mine2sirius", use_reloader=True, port=5000, propagate=True)