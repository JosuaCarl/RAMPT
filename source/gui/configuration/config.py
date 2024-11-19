#

import os
import json

from werkzeug.utils import secure_filename

from taipy import Config, Frequency, Scope

from source.helpers.types import StrPath

# Import of Pipeline Steps
from source.helpers.classes import Step_Configuration
from source.conversion.msconv_pipe import File_Converter
from source.feature_finding.mzmine_pipe import MZmine_Runner
from source.annotation.sirius_pipe import Sirius_Runner
from source.annotation.gnps_pipe import GNPS_Runner


class MS_Analysis_Configuration(Step_Configuration):
    """
    GLobal configuration of MS analysis
    """
    def __init__( self, platform:str="Linux", overwrite:bool=False, nested:bool=False,
                  save_log:bool=True, workers:int=1, verbosity:int=1,
                  file_converter:File_Converter|dict=File_Converter(),
                  mzmine_runner:MZmine_Runner|dict=MZmine_Runner(),
                  gnps_runner:GNPS_Runner|dict=GNPS_Runner(),
                  sirius_runner:Sirius_Runner|dict=Sirius_Runner() ):
        super().__init__( platform=platform, overwrite=overwrite, nested=nested, save_log=save_log, workers=workers,
                          verbosity=verbosity )
        self.file_converter = File_Converter(**file_converter)  if isinstance(file_converter, dict) else file_converter
        self.mzmine_runner  = MZmine_Runner(**mzmine_runner)    if isinstance(mzmine_runner, dict)  else mzmine_runner
        self.gnps_runner    = GNPS_Runner(**gnps_runner)        if isinstance(gnps_runner, dict)    else gnps_runner
        self.sirius_runner  = Sirius_Runner(**sirius_runner)    if isinstance(sirius_runner, dict)  else sirius_runner
                  


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

conversion_params_config = Config.configure_json_data_node( id="conversion_params",
                                                                   scope=Scope.SCENARIO )

conversion_params_config = Config.configure_json_data_node( id="conversion_params",
                                                                   scope=Scope.SCENARIO )


# Task methods
def generic_step( step_class, in_paths:list, out_path_target:StrPath, step_params:dict, global_params:dict):
    step_params.update( global_params )
    step_instance = step_class( **step_params )

    out_paths = [os.path.join(in_path, out_path_target) for in_path in in_paths]

    print(f"\nParameters:\n{step_params}\nInput:\n{in_paths}\n Output:\n{out_paths}\n")
    step_instance.run( in_paths=in_paths, out_paths=out_paths)

    return step_instance.processed_out


def convert_files( raw_data, conversion_params:dict, global_params:dict ):
    return generic_step( step_class=File_Converter,
                         input=raw_data, output="../converted",
                         step_params=conversion_params,
                         global_params=global_params )

def find_features( community_formatted_data, conversion_params:dict, global_params:dict ):
    return generic_step( step_class=MZmine_Runner,
                         input=community_formatted_data, output="../processed",
                         step_params=conversion_params,
                         global_params=global_params )

def annotate_gnps( processed_data, conversion_params:dict, global_params:dict ):
    return generic_step( step_class=GNPS_Runner,
                         input=processed_data, output="../annotated",
                         step_params=conversion_params,
                         global_params=global_params )

def annotate_sirius( processed_data, conversion_params:dict, global_params:dict ):
    return generic_step( step_class=Sirius_Runner,
                         input=processed_data, output="../annotated",
                         step_params=conversion_params,
                         global_params=global_params )


def analyze_difference( gnps_annotated_data, sirius_annotated_data, conversion_params:dict, global_params:dict ):
    print("Analyze difference not implemented yet.")
    pass
    """
    return generic_step( step_class="",
                         input=annotated_data, output="../results",
                         step_params=conversion_params,
                         global_params=global_params )
    """



# Tasks
convert_files_config = Config.configure_task( "convert_files",
                                              function=convert_files,
                                              input=[raw_data_config, conversion_params_config, global_params_config],
                                              output=community_formatted_data_config,
                                              skippable=False)

find_features_config = Config.configure_task( "find_features",
                                              function=find_features,
                                              input=[community_formatted_data_config, conversion_params_config, global_params_config],
                                              output=processed_data_config,
                                              skippable=False)

annotate_gnps_config = Config.configure_task( "annotate_gnps",
                                              function=annotate_gnps,
                                              input=[processed_data_config, conversion_params_config, global_params_config],
                                              output=gnps_annotations_config,
                                              skippable=False)

annotate_sirius_config = Config.configure_task( "annotate_sirius",
                                              function=annotate_sirius,
                                              input=[processed_data_config, conversion_params_config, global_params_config],
                                              output=sirius_anntations_config,
                                              skippable=False)

analyze_difference_config = Config.configure_task( "analyze_difference",
                                              function=analyze_difference,
                                              input=[gnps_annotations_config, sirius_anntations_config, conversion_params_config, global_params_config],
                                              output=results_config,
                                              skippable=False)



# SCENARIO
ms_analysis_config = Config.configure_scenario( id="MS_analysis",
                                                task_configs=[ convert_files_config,
                                                               find_features_config,
                                                               annotate_gnps_config,
                                                               annotate_sirius_config,
                                                               analyze_difference_config],
                                                sequences={ "convert": [ convert_files_config ]} )


# CORE
core_config = Config.configure_core(
                                    root_folder=".process/",
                                    storage_folder=".out/",
                                    read_entity_retry=2,
                                    mode="experiment",
                                    version_number="1.0.0",
                                    application_name="mine2sirius",
                                )
