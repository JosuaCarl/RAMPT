#!/usr/bin/env python3
"""
GUI creation with Taipy.
"""
import os

from taipy.gui import Gui
from taipy import Config, Orchestrator
import taipy.gui.builder as tgb

import source.helpers.general as helpers
from source.conversion.msconv_pipe import File_Converter


# Conversion

path = ""    
in_paths = []
nested_in_paths = [{"id": "0", "label": "", "children": []}]
path_nester = helpers.Path_Nester()
selection = nested_in_paths[0]
def add_in_path( state ):
    if isinstance( state.path, list ):
        in_paths.extend( state.path )
    else:
        in_paths.append( state.path )

    nested_in_paths = path_nester.update_nested_paths( new_paths=state.path )
    state.nested_in_paths = nested_in_paths
    state.selection = nested_in_paths[0]
    state.refresh("nested_in_paths")
  



out_path = ""
platform = ""
file_converter = File_Converter()
def update_converter( state, var, val ):
    file_converter.update( {var: val} )

def convert_selected( state ):
    for in_path in in_paths:
        file_converter.convert_file( in_path=in_path, out_path=out_path )


# SCENARIOS
scenario = ""

# JOBS
job = ""


# OTHER
def print_state_properies( state, var, val ):
    print("STATE INFO:")
    print(state)
    print(dir(state))
    print(state.__dict__)
    print(state.path)
    print("\nVALUE")
    print(f"{var}: {val}")
    

with tgb.Page() as root:
    with tgb.layout( columns="1", columns__mobile="1" ):
        tgb.navbar( lov='{[("/", "Application"), ("https://josuacarl.github.io/mine2sirius_pipe", "Documentation")]}' )

    with tgb.layout( columns="1 3 1", columns__mobile="1" ):
        with tgb.part():
            tgb.scenario_selector( "{scenario}" )
        
        # Main window
        with tgb.part():
            tgb.text( "## Manual configuration", mode="markdown" )
            with tgb.expandable( title="Conversion", expanded=False, hover_text="Convert manufacturer files into communtiy formats." ):
                tgb.selector( "{platform}",
                              label="Platform", lov="Linux;Windows;MacOS", dropdown=True, on_change=update_converter )
                tgb.file_selector( "{path}",
                                   label="Select File", extensions="*", drop_message="Drop files for conversion here:",
                                   multiple=True, on_action=add_in_path )
                tgb.tree( "{selection}", lov="{nested_in_paths}", label="Select for conversion", filter=True, multiple=True, expanded=True )
                tgb.text( "Paths: {path}" )
                tgb.button( label="Convert selected", on_action='{None}' )

            with tgb.expandable( title="Processing", expanded=False, hover_text="Process the data with mzmine through a batch file."):
                tgb.text( "LOREM IPSUM" )
            
            tgb.text( "## Scenario management", mode="markdown" )
            tgb.scenario( "{scenario}", show_tags=False, show_properties=False, show_sequences=False )
            tgb.scenario_dag( "{scenario}" )
            
            tgb.text("## Jobs", mode="markdown")
            tgb.job_selector( "{job}" )


        with tgb.part():
            pass


pages = { "/": root,
        }
gui = Gui(pages=pages, css_file="styles.css")


if __name__ == "__main__":
    Config.load( os.path.join( os.path.dirname( helpers.get_internal_filepath(__file__) ), "configuration", "config.toml" ) )
    Orchestrator().run()

    gui.run(title="mine2sirius", use_reloader=True, port=5000, propagate=True)