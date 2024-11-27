#!/usr/bin/env python3

import os
import tempfile
import json
import warnings

import taipy as tp
import taipy.gui.builder as tgb

from source.gui.helpers import *

# Submodules
from . import *

# Configuration
from source.gui.configuration.config import *


# Working directory
local = True
work_dir_root = tempfile.gettempdir()


# SYNCHRONISATION (First GUI, then Scenario)
## Synchronisation of GUI
param_segment_names = [ "global", "conversion", "feature_finding", "gnps", "sirius", "analysis" ]
save_path = None
save_file_types = [ ("json files", "*.json") ]

def construct_params_dict( state, param_segment_names:list=param_segment_names ):
    params = {}
    for segment_name in param_segment_names:
        segment_params = get_attribute_recursive(state, f"{segment_name}_params")
        params[f"{segment_name}_params"] = segment_params.dict_representation()
    return params


def save_params( state, path:StrPath=None, scenario_name:str=None ):
    global save_path

    if path:
        path = path
    elif scenario_name:
        path = os.path.join(work_dir_root, f"{scenario_name}_config.json")
    elif save_path:
        path = save_path
    else:
        warnings.warn( f"Saving to default path: {os.path.join(work_dir_root, f"Default_config.json")}" )
        path = os.path.join(work_dir_root, f"Default_config.json")

    with open( path, "w") as file:
        json.dump( construct_params_dict( state ), file )
    save_path = path


def load_params( state, path:StrPath=None, scenario_name:str="Default" ):
    path = path if path else os.path.join(work_dir_root, f"{scenario_name}_config.json")
    with open( path, "r" ) as file:
       params = json.loads( file.read() )

    for segment_name, segment_params in params.items():
        for attribute, param in segment_params.items():
            set_attribute_recursive(state, f"{segment_name}.{attribute}", param, refresh=True)


# SCENARIO
scenario = tp.create_scenario( ms_analysis_config,
                               name="Default" )


## Synchronisation of Scenario
match_in_out = { "conversion_params.scheduled_in": "raw_data",
                 "feature_finding_params.scheduled_in": "community_formatted_data",
                 "gnps_params.scheduled_in":    "processed_data",
                 "sirius_params.scheduled_in":  "processed_data",
                 "analysis_params.scheduled_in": "gnps_annotations",
                 "analysis_params.scheduled_in": "sirius_anntations",
                 "conversion_params.processed_out": "community_formatted_data",
                 "feature_finding_params.processed_out": "processed_data",
                 "gnps_params.processed_out":    "gnps_annotations",
                 "sirius_params.processed_out":  "sirius_anntations",
                 "analysis_params.processed_out": "results" }


def lock_scenario( state ):
    global scenario
    scenario = state.scenario

    params = construct_params_dict( state )
    
    data_nodes = params.copy()
    for segment_name, segment_dict in params.items():
        for in_out in ["scheduled_in", "processed_out"]:
            attribute = f"{segment_name}.{in_out}"
            if attribute in match_in_out:
                data_nodes.update( {match_in_out.get(attribute): segment_dict.get(in_out)} )

    for key, data_node in scenario.data_nodes.items():
        if data_nodes.get(key):
            data_node.write( data_nodes.get(key) )

    state.scenario = scenario
    state.refresh( "scenario" )



## Interaction
def add_scenario( state, id, payload ):
    # Save previous scenario
    save_params( state, scenario_name=state.scenario.name)

    # Lock new scenario into current configuration
    lock_scenario( state )
    save_params( state, scenario_name=payload.get("label", "Default"))


def change_scenario( state, id, scenario_name ):
    # Load parameters into Gui
    if scenario_name:
        load_params( state, scenario_name=scenario_name )

    # Push gui parameters into scenario
    lock_scenario( state )


# JOBS
job = None



# DATA
data_node = None


style = { ".sticky-part":  { "position": "sticky",
                             "align-self": "flex-start",
                             "top": "10px" },
        }

with tgb.Page( style=style ) as root:
    with tgb.layout( columns="1 3 1", columns__mobile="1", gap="2.5%" ):

        # Left part
        with tgb.part( class_name="sticky-part"):
            # Save button
            with tgb.layout(columns="1 1.2 1", gap="2%"):
                tgb.button( "💾 Save", on_action=lambda state, id, payload: save_params( state ) )
                tgb.button( "💾 Save as", on_action=lambda state, id, payload: save_params( state, path=open_file_folder( save=True, multiple=False,
                                                                                                                        filetypes=save_file_types ) ) )
                tgb.button( "📋 Load", on_action=lambda state, id, payload: load_params( state, path=open_file_folder( multiple=False,
                                                                                                                    filetypes=save_file_types ) ) )
            tgb.button( "◀️ Lock scenario", on_action=lambda state, id, payload: lock_scenario( state ) )

            # Scenario selector
            tgb.text( "#### Scenarios", mode="markdown" )
            tgb.scenario_selector( "{scenario}", on_creation=add_scenario, on_change=change_scenario )
            tgb.text( "#### Data", mode="markdown" )
            tgb.data_node_selector( "{data_node}" )
        
        # Middle part
        with tgb.part():
            tgb.text( "## ⚙️Manual configuration", mode="markdown" )
            with tgb.expandable( title="General", expanded=False , hover_text=""):
                create_general()

            with tgb.expandable( title="Conversion", expanded=False, hover_text="Convert manufacturer files into community formats." ):
                create_conversion()

            with tgb.expandable( title="Feature finding", expanded=False, hover_text="Find features with MZmine through applying steps via a batch file."):
                create_feature_finding()

            with tgb.expandable( title="Annotation", expanded=False, hover_text=""):
                create_gnps()
                create_sirius()

            with tgb.expandable( title="Analysis", expanded=False, hover_text=""):
                create_analysis()

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
