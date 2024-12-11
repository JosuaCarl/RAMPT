#!/usr/bin/env python3

import os

from taipy import Config, Scope

from source.helpers.types import StrPath

# Import of Pipeline Steps
from source.steps.feature_finding.mzmine_pipe import MZmine_Runner
from source.steps.conversion.msconv_pipe import MSconvert_Runner
from source.steps.annotation.sirius_pipe import Sirius_Runner
from source.steps.annotation.gnps_pipe import GNPS_Runner

from typing import Any



# Data nodes
## Data paths
raw_data_config = Config.configure_in_memory_data_node( id="raw_data",
                                                        scope=Scope.SCENARIO )

community_formatted_data_config = Config.configure_in_memory_data_node( id="community_formatted_data",
                                                                        scope=Scope.SCENARIO )

processed_data_config = Config.configure_in_memory_data_node( id="processed_data",
                                                              scope=Scope.SCENARIO )

gnps_annotations_config = Config.configure_json_data_node( id="gnps_annotations",
                                                           scope=Scope.SCENARIO )

sirius_annotations_config = Config.configure_csv_data_node( id="sirius_annotations",
                                                           scope=Scope.SCENARIO )

results_config = Config.configure_csv_data_node( id="results",
                                                 scope=Scope.SCENARIO )

## Output paths
conversion_out_config = Config.configure_in_memory_data_node( id="conversion_out",
                                                              scope=Scope.SCENARIO )

feature_finding_out_config = Config.configure_in_memory_data_node( id="feature_finding_out",
                                                                   scope=Scope.SCENARIO )

gnps_out_config = Config.configure_in_memory_data_node( id="gnps_out",
                                                        scope=Scope.SCENARIO )

sirius_out_config = Config.configure_in_memory_data_node( id="sirius_out",
                                                          scope=Scope.SCENARIO )

results_out_config = Config.configure_in_memory_data_node( id="results_out",
                                                           scope=Scope.SCENARIO )


## Parameters
global_params_config = Config.configure_json_data_node( id="global_params",
                                                        scope=Scope.SCENARIO )

conversion_params_config = Config.configure_json_data_node( id="conversion_params",
                                                            scope=Scope.SCENARIO )

feature_finding_params_config = Config.configure_json_data_node( id="feature_finding_params",
                                                                   scope=Scope.SCENARIO )

gnps_params_config = Config.configure_json_data_node( id="gnps_params",
                                                      scope=Scope.SCENARIO )

sirius_params_config = Config.configure_json_data_node( id="sirius_params",
                                                        scope=Scope.SCENARIO )

analysis_params_config = Config.configure_json_data_node( id="analysis_params",
                                                        scope=Scope.SCENARIO )


# Batch file nodes
mzmine_batch_config = Config.configure_in_memory_data_node( id="mzmine_batch",
                                                            scope=Scope.SCENARIO )

mzmine_log_config = Config.configure_in_memory_data_node( id="mzmine_log",
                                                          scope=Scope.SCENARIO )

sirius_config_config = Config.configure_in_memory_data_node( id="sirius_config",
                                                             scope=Scope.SCENARIO )


# Task methods
def generic_step( step_class, step_params:dict, global_params:dict, in_paths:list=None, out_paths:list=None,
                  out_path_target:StrPath=None, return_attributes:list=["processed_out"],
                  **kwargs) -> tuple[Any]|Any:

    # Fix parameters
    step_params.update( global_params )
    step_instance = step_class( **step_params )

    # Overwrite scheduled, when new in_path is given
    if in_paths:
        step_instance.scheduled_in = []
    if out_paths:
        step_instance.scheduled_out = []
    # Add out_paths as relatives to in_path if none is given
    else:
        for in_path in in_paths:
            if os.path.isfile(in_path):
                out_paths.append( os.path.abspath(os.path.join(os.path.dirname(in_path), out_path_target)) )
            else:
                out_paths.append( os.path.abspath(os.path.join(in_path, out_path_target)) )
    
    # Run step
    step_instance.run( in_paths=in_paths, out_paths=out_paths, **kwargs )

    # Return results
    results =  [ getattr(step_instance, attr) for attr in return_attributes ] 

    return tuple(results) if len(results) > 1 else results[0]



def convert_files( raw_data:StrPath, conversion_out:StrPath, step_params:dict, global_params:dict ):
    return generic_step(
        step_class=MSconvert_Runner,
        in_paths=raw_data,
        out_paths=conversion_out,
        out_path_target="converted",
        step_params=step_params,
        global_params=global_params )

def find_features( community_formatted_data:StrPath, feature_finding_out:StrPath, mzmine_batch:StrPath, step_params:dict, global_params:dict ):
    return generic_step(
        step_class=MZmine_Runner,
        in_paths=community_formatted_data,
        out_paths=feature_finding_out,
        out_path_target="processed",
        step_params=step_params,
        global_params=global_params,
        return_attributes=["processed_out", "log_paths"],
        batch=mzmine_batch
    )

def annotate_gnps( processed_data:StrPath, mzmine_log:StrPath, gnps_out:StrPath, step_params:dict, global_params:dict ):
    return generic_step(
        step_class=GNPS_Runner,
        in_paths=processed_data,
        out_paths=gnps_out,
        out_path_target="annotated",
        step_params=step_params,
        global_params=global_params,
        mzmine_log=mzmine_log 
    )

def annotate_sirius( processed_data:StrPath, sirius_out:StrPath, config:StrPath, step_params:dict, global_params:dict ):
    return generic_step(
        step_class=Sirius_Runner,
        in_paths=processed_data,
        out_paths=sirius_out,
        out_path_target="annotated",
        step_params=step_params,
        global_params=global_params,
        config=config
    )


def analyze_difference( gnps_annotated_data:StrPath, sirius_annotated_data:StrPath, results_out:StrPath, step_params:dict, global_params:dict ):
    print("Analyze difference not implemented yet.")
    pass
    """
    return generic_step( step_class="",
        
                         input=annotated_data, output=os.path.join("..", "results"),
                         step_params=step_params,
                         global_params=global_params )
    """



# Tasks
convert_files_config = Config.configure_task( "convert_files",
                                              function=convert_files,
                                              input=[ raw_data_config,
                                                      conversion_out_config,
                                                      conversion_params_config,
                                                      global_params_config ],
                                              output=community_formatted_data_config,
                                              skippable=False )

find_features_config = Config.configure_task( "find_features",
                                              function=find_features,
                                              input=[ community_formatted_data_config,
                                                      feature_finding_out_config,
                                                      mzmine_batch_config,
                                                      feature_finding_params_config,
                                                      global_params_config ],
                                              output=[ processed_data_config,
                                                       mzmine_log_config ],
                                              skippable=False )

annotate_gnps_config = Config.configure_task( "annotate_gnps",
                                              function=annotate_gnps,
                                              input=[ processed_data_config,
                                                      mzmine_log_config,
                                                      gnps_out_config,
                                                      gnps_params_config,
                                                      global_params_config ],
                                              output=gnps_annotations_config,
                                              skippable=False )

annotate_sirius_config = Config.configure_task( "annotate_sirius",
                                              function=annotate_sirius,
                                              input=[ processed_data_config,
                                                      sirius_out_config,
                                                      sirius_config_config,
                                                      sirius_params_config,
                                                      global_params_config ],
                                              output=sirius_annotations_config,
                                              skippable=False )

analyze_difference_config = Config.configure_task( "analyze_difference",
                                              function=analyze_difference,
                                              input=[ gnps_annotations_config,
                                                      sirius_annotations_config,
                                                      results_out_config,
                                                      analysis_params_config, 
                                                      global_params_config ],
                                              output=results_config,
                                              skippable=False )



# SCENARIO
ms_analysis_config = Config.configure_scenario( id="MS_analysis",
                                                task_configs=[ convert_files_config,
                                                               find_features_config,
                                                               annotate_sirius_config,
                                                               annotate_gnps_config,
                                                               analyze_difference_config ],
                                                sequences={ "conversion": [ convert_files_config ],
                                                            "feature finding": [ find_features_config ],
                                                            "gnps": [ annotate_gnps_config ],
                                                            "sirius": [ annotate_sirius_config ],
                                                            "analysis": [ analyze_difference_config ] } )


# CORE
"""
core_config = Config.configure_core(
                                    root_folder=".process/",
                                    storage_folder=".out/",
                                    read_entity_retry=2,
                                    mode="experiment",
                                    version_number="1.0.0",
                                    application_name="mine2sirius",
                                )
"""
