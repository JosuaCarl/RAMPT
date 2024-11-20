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

def get_params_dict( state, param_segment_names:list=param_segment_names ):
    print(state)
    print(dir(state))
    params = {}
    for segment_name in param_segment_names:
        segment_params = get_attribute_recursive(state, f"{segment_name}_params")
        params[segment_name] = segment_params.dict_representation()
    return params


def save_params( state, scenario_name:str ):
    with open(os.path.join(work_dir_root, f"{scenario_name}_config.json"), "w") as file:
        json.dump( get_params_dict( state ), file )

def load_params( state, scenario_name:str ):
    with open( os.path.join(work_dir_root, f"{scenario_name}_config.json"), "w" ) as file:
       params = json.loads( file.read() )

    for segment_name, segment_params in params.items():
        for attribute, param in segment_params.items():
            set_attribute_recursive(state, f"{segment_name}_params.{attribute}", param)


# SCENARIO
scenario = tp.create_scenario( ms_analysis_config )

## Synchronisation
def sync_scenario_params( state ):
    params = get_params_dict( state )
    scenario.data_nodes.update( params )
    state.scenario = scenario


def sync_scenario_in( state, attribute:str ):
    match_in = { "conversion_params.scheduled_in": "raw_data",
                 "feature_finding_params.scheduled_in": "community_formatted_data",
                 "gnps_params.scheduled_in":    "processed_data",
                 "sirius_params.scheduled_in":  "processed_data",
                 "analysis_params.scheduled_in": "gnps_annotations",
                 "analysis_params.scheduled_in": "sirius_anntations" }
    scenario.data_nodes.update( {match_in[attribute]: get_attribute_recursive( state, attribute )} )
    state.scenario = scenario


def sync_scenario_out( state, attribute:str ):
    match_out = { "conversion_params.processed_out": "community_formatted_data",
                  "feature_finding_params.processed_out": "processed_data",
                  "gnps_params.processed_out":    "gnps_annotations",
                  "sirius_params.processed_out":  "sirius_anntations",
                  "analysis_params.processed_out": "results" }

    scenario.data_nodes.update( {match_out[attribute]: get_attribute_recursive( state, attribute )} )
    state.scenario = scenario

def sync_scenario_in_out( state, attribute ):
    sync_scenario_in( state, attribute )
    sync_scenario_out( state, attribute )


def sync_scenario( state, param_segment_names:list=param_segment_names ):
    sync_scenario_params( state )
    for segment_name in param_segment_names:
        sync_scenario_in( state, f"{segment_name}_params.scheduled_in" )
        sync_scenario_out( state, f"{segment_name}_params.processed_out" )


## Interaction
def add_scenario( state, id, payload ):
    save_params( state, payload.get("label", "default"), param_segment_names=param_segment_names )


def change_scenario( state, id, scenario_name ):    
    load_params( state, scenario_name=scenario_name )
    sync_scenario( state )



# JOBS
job = None



# DATA
data_node = None



style = { ".sticky-part": 
          { "position": "sticky",
            "align-self": "flex-start",
             "top": "0" } }

with tgb.Page( style=style ) as root:
    with tgb.layout( columns="1 3 1", columns__mobile="1", gap="2.5%" ):

        # Left part
        with tgb.part( class_name="sticky-part"):
            # Scenario selector
            tgb.text( "#### Scenarios", mode="markdown" )
            tgb.scenario_selector( "{scenario}", on_creation=add_scenario, on_change=change_scenario )
            tgb.text( "#### Data", mode="markdown" )
            tgb.data_node_selector( "{data_node}" )
        
        # Middle part
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

            # Save button
            tgb.html( "br" )
            tgb.button( "Lock configuration", on_action=lambda state, id, payload: sync_scenario( state ) )

            # Pipeline showcasing
            tgb.text( "## 🎬Scenario management", mode="markdown" )
            tgb.scenario( "{scenario}", show_properties=False, show_tags=False, show_sequences=True )
            tgb.scenario_dag( "{scenario}" )
            
            tgb.text("## 📊Data", mode="markdown")
            tgb.data_node( "{data_node}" )

            tgb.text("## 🐝Jobs", mode="markdown")
            tgb.job_selector( "{job}" )

        # Right part
        with tgb.part():
            pass
