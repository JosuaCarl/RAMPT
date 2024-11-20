#!/usr/bin/env python3

import os
import tempfile
import json


import taipy as tp
import taipy.gui.builder as tgb

from source.gui.helpers import *

# Configuration
from source.gui.configuration.config import *


# Working directory
work_dir_root = tempfile.gettempdir()



# PARAMETERS
param_segment_names = [ "global", "conversion", "feature_finding", "gnps", "sirius", "analysis" ]

def save_params( state, scenario_name:str, param_segment_names:list=param_segment_names):
    params = {}
    for segment_name in param_segment_names:
        segment_params = get_attribute_recursive(state, f"{segment_name}_params")
        params[segment_name] = segment_params.dict_representation()
    
    with open(os.path.join(work_dir_root, f"{scenario_name}_config.json"), "w") as file:
        json.dump( params, file )


def load_params( state, scenario_name:str):
    with open( os.path.join(work_dir_root, f"{scenario_name}_config.json"), "w" ) as file:
       params = json.loads( file.read() )

    for segment_name, segment_params in params.items():
        for attribute, param in segment_params.items():
            set_attribute_recursive(state, f"{segment_name}_params.{attribute}", param)


def sync_params( state, sub_classes:str=["scenario", "data_nodes"], param_segment_names:list=param_segment_names ):
    sub_classes = ".".join(sub_classes) + "." if sub_classes else ""
    for segment_name in param_segment_names:
        segment_params = get_attribute_recursive(state, f"{segment_name}_params")
        for attribute, param in segment_params.items():
            set_attribute_recursive(state, f"{sub_classes}{segment_name}_params.{attribute}", param)
    print( state.scenario.data_nodes )



# SCENARIO
scenario = tp.create_scenario( ms_analysis_config )

def write_param_data_nodes():
    pass


def write_input_data_nodes( state ):
    # TODO: Fix
    print( state.scenario.data_nodes )
    print( state.scenario.data_nodes["raw_data"] )
    for data_node in state.scenario.data_nodes:
        data_node.write( [scheduled_path.get("label") for scheduled_path in state.file_converter.scheduled_in] )
    pass


def add_scenario( state, id, payload ):
    save_params( state, payload.get("label", "default"), param_segment_names=param_segment_names )


def change_scenario( state, id, scenario_name ):    
    load_params( state, scenario_name=scenario_name )
    sync_params( state, sub_class="scenario", param_segment_names=param_segment_names)
    
    write_param_data_nodes( state )
    write_input_data_nodes( state )


# JOBS
job = None


# DATA
data_node = None

# OTHER
input_var = ""
press=""
def execute_input( state ):
    os.system(state.input_var)


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
            with tgb.expandable( title="General", expanded=False , hover_text=""):
                tgb.part( page="general" )

            with tgb.expandable( title="Conversion", expanded=False, hover_text="Convert manufacturer files into community formats." ):
                tgb.part( page="conversion" )

            with tgb.expandable( title="Feature finding", expanded=False, hover_text="Find features with MZmine through applying steps via a batch file."):
                tgb.part( page="feature_finding" )

            with tgb.expandable( title="Annotation", expanded=False, hover_text=""):
                tgb.part( page="gnps" )
                tgb.part( page="sirius" )

            with tgb.expandable( title="Analysis", expanded=False, hover_text=""):
                tgb.part( page="analysis" )           

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
