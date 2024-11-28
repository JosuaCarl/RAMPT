#!/usr/bin/env python3

import os
import json

from werkzeug.utils import secure_filename

from taipy import Config, Frequency, Scope

from source.helpers.types import StrPath

# Import of Pipeline Steps
from source.feature_finding.mzmine_pipe import MZmine_Runner
from source.conversion.msconv_pipe import File_Converter
from source.annotation.sirius_pipe import Sirius_Runner
from source.annotation.gnps_pipe import GNPS_Runner



# Data nodes
raw_data_config = Config.configure_in_memory_data_node( id="raw_data",
                                                        scope=Scope.SCENARIO )

community_formatted_data_config = Config.configure_in_memory_data_node( id="community_formatted_data",
                                                                        scope=Scope.SCENARIO )

processed_data_config = Config.configure_in_memory_data_node( id="processed_data",
                                                              scope=Scope.SCENARIO )

gnps_annotations_config = Config.configure_csv_data_node( id="gnps_annotations",
                                                          scope=Scope.SCENARIO )

sirius_anntations_config = Config.configure_csv_data_node( id="sirius_anntations",
                                                           scope=Scope.SCENARIO )

results_config = Config.configure_csv_data_node( id="results",
                                                 scope=Scope.SCENARIO )


# Parameter nodes
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

sirius_projectspace_config = Config.configure_in_memory_data_node( id="sirius_projectspace",
                                                                   scope=Scope.SCENARIO )


# Task methods
def generic_step( step_class, step_params:dict, global_params:dict, in_paths:list=None, out_path_target:StrPath=None, **kwargs):
    step_params.update( global_params )
    step_instance = step_class( **step_params )

    if in_paths:
        step_instance.scheduled_in = []

    in_paths = [ in_path["label"] if isinstance(in_path, dict) else in_path for in_path in in_paths ]
    if not step_instance.scheduled_out:
        out_paths = [ os.path.abspath(os.path.join(in_path, out_path_target)) for in_path in in_paths]

    step_instance.run( in_paths=in_paths, out_paths=out_paths, **kwargs )

    return step_instance.processed_out


def convert_files( raw_data:StrPath, step_params:dict, global_params:dict ):
    return generic_step( step_class=File_Converter,
                         in_paths=raw_data,
                         out_path_target=os.path.join("..", "converted"),
                         step_params=step_params,
                         global_params=global_params )

def find_features( community_formatted_data:StrPath, mzmine_batch_file:StrPath, step_params:dict, global_params:dict ):
    return generic_step( step_class=MZmine_Runner,
                         in_paths=community_formatted_data,
                         out_path_target=os.path.join("..", "processed"),
                         step_params=step_params,
                         global_params=global_params,
                         batch_file=mzmine_batch_file )

def annotate_gnps( processed_data:StrPath, mzmine_log:StrPath, step_params:dict, global_params:dict ):
    return generic_step( step_class=GNPS_Runner,
                         in_paths=processed_data,
                         out_path_target=os.path.join("..", "annotated"),
                         step_params=step_params,
                         global_params=global_params,
                         mzmine_log=mzmine_log )

def annotate_sirius( processed_data:StrPath, projectspace:StrPath, step_params:dict, global_params:dict ):
    return generic_step( step_class=Sirius_Runner,
                         in_paths=processed_data,
                         out_path_target=os.path.join("..", "annotated"),
                         step_params=step_params,
                         global_params=global_params,
                         projectspace=projectspace )


def analyze_difference( gnps_annotated_data:StrPath, sirius_annotated_data:StrPath, step_params:dict, global_params:dict ):
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
                                                      conversion_params_config,
                                                      global_params_config ],
                                              output=community_formatted_data_config,
                                              skippable=False)

find_features_config = Config.configure_task( "find_features",
                                              function=find_features,
                                              input=[ community_formatted_data_config,
                                                      mzmine_batch_config,
                                                      feature_finding_params_config,
                                                      global_params_config ],
                                              output=processed_data_config,
                                              skippable=False)

annotate_gnps_config = Config.configure_task( "annotate_gnps",
                                              function=annotate_gnps,
                                              input=[ processed_data_config,
                                                      mzmine_log_config,
                                                      gnps_params_config,
                                                      global_params_config ],
                                              output=gnps_annotations_config,
                                              skippable=False)

annotate_sirius_config = Config.configure_task( "annotate_sirius",
                                              function=annotate_sirius,
                                              input=[ processed_data_config,
                                                      sirius_projectspace_config,
                                                      sirius_params_config,
                                                      global_params_config ],
                                              output=sirius_anntations_config,
                                              skippable=False)

analyze_difference_config = Config.configure_task( "analyze_difference",
                                              function=analyze_difference,
                                              input=[ gnps_annotations_config,
                                                      sirius_anntations_config,
                                                      analysis_params_config, 
                                                      global_params_config],
                                              output=results_config,
                                              skippable=False)



# SCENARIO
ms_analysis_config = Config.configure_scenario( id="MS_analysis",
                                                task_configs=[ convert_files_config,
                                                               find_features_config,
                                                               annotate_gnps_config,
                                                               annotate_sirius_config,
                                                               analyze_difference_config],
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
