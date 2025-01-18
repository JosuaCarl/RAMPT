#!/usr/bin/env python3

import os

from taipy import Config, Scope

from rampt.helpers.general import *
from rampt.helpers.logging import *

# Import of Pipeline Steps
from rampt.steps.feature_finding.mzmine_pipe import MZmine_Runner
from rampt.steps.conversion.msconv_pipe import MSconvert_Runner
from rampt.steps.annotation.sirius_pipe import Sirius_Runner
from rampt.steps.annotation.gnps_pipe import GNPS_Runner
from rampt.steps.analysis.summary_pipe import Summary_Runner
from rampt.steps.analysis.analysis_pipe import Analysis_Runner

from typing import Any


# Data nodes
## Data paths
raw_data_paths_config = Config.configure_in_memory_data_node(
    id="raw_data_paths", scope=Scope.SCENARIO
)

community_formatted_data_paths_config = Config.configure_in_memory_data_node(
    id="community_formatted_data_paths", scope=Scope.SCENARIO
)

processed_data_paths_config = Config.configure_in_memory_data_node(
    id="processed_data_paths", scope=Scope.SCENARIO
)

gnps_annotation_paths_config = Config.configure_in_memory_data_node(
    id="gnps_annotation_paths", scope=Scope.SCENARIO, default_value=None
)

sirius_annotation_paths_config = Config.configure_in_memory_data_node(
    id="sirius_annotation_paths", scope=Scope.SCENARIO, default_value=None
)

summary_data_paths_config = Config.configure_in_memory_data_node(
    id="summary_data_paths", scope=Scope.SCENARIO
)

analysis_data_paths_config = Config.configure_in_memory_data_node(
    id="analysis_data_paths", scope=Scope.SCENARIO
)


## Real-time data nodes
gnps_annotations_config = Config.configure_json_data_node(
    id="gnps_annotation", scope=Scope.GLOBAL, default_path=""
)

sirius_annotations_config = Config.configure_csv_data_node(
    id="sirius_annotation", scope=Scope.GLOBAL, default_path=""
)

summary_data_config = Config.configure_csv_data_node(id="summary_data", scope=Scope.GLOBAL)

analysis_data_config = Config.configure_csv_data_node(id="analysis_data", scope=Scope.GLOBAL)


## Output paths
conversion_out_paths_config = Config.configure_in_memory_data_node(
    id="conversion_out_paths", scope=Scope.SCENARIO
)

feature_finding_out_paths_config = Config.configure_in_memory_data_node(
    id="feature_finding_out_paths", scope=Scope.SCENARIO
)

gnps_out_paths_config = Config.configure_in_memory_data_node(
    id="gnps_out_paths", scope=Scope.SCENARIO
)

sirius_out_paths_config = Config.configure_in_memory_data_node(
    id="sirius_out_paths", scope=Scope.SCENARIO
)

summary_out_paths_config = Config.configure_in_memory_data_node(
    id="summary_out_paths", scope=Scope.SCENARIO
)

analysis_out_paths_config = Config.configure_in_memory_data_node(
    id="analysis_out_paths", scope=Scope.SCENARIO
)


## Parameters
global_params_config = Config.configure_json_data_node(id="global_params", scope=Scope.SCENARIO)

conversion_params_config = Config.configure_json_data_node(
    id="conversion_params", scope=Scope.SCENARIO
)

feature_finding_params_config = Config.configure_json_data_node(
    id="feature_finding_params", scope=Scope.SCENARIO
)

gnps_params_config = Config.configure_json_data_node(id="gnps_params", scope=Scope.SCENARIO)

sirius_params_config = Config.configure_json_data_node(id="sirius_params", scope=Scope.SCENARIO)

summary_params_config = Config.configure_json_data_node(id="summary_params", scope=Scope.SCENARIO)

analysis_params_config = Config.configure_json_data_node(id="analysis_params", scope=Scope.SCENARIO)


# Batch file nodes
mzmine_batch_config = Config.configure_in_memory_data_node(id="mzmine_batch", scope=Scope.SCENARIO)

mzmine_log_config = Config.configure_in_memory_data_node(id="mzmine_log", scope=Scope.SCENARIO)

sirius_config_config = Config.configure_in_memory_data_node(
    id="sirius_config", scope=Scope.SCENARIO
)


# TODO: DOCUMENTATION & TESTING
# Task methods
def generic_step(
    step_class,
    step_params: dict,
    global_params: dict,
    in_paths: str | list = None,
    out_paths: str | list = None,
    out_path_target: StrPath = ".",
    return_attributes: list = ["processed_out"],
    **kwargs,
) -> tuple[Any] | Any:
    # Fixate parameters
    global_params.pop("patterns")
    global_params.pop("additional_args")
    step_params.update(global_params)
    step_instance = step_class(**step_params)

    log(
        f"Starting {step_instance.name} step",
        minimum_verbosity=3,
        verbosity=global_params.get("verbosity", 0),
    )

    # Overwrite scheduled, when new in_path is given
    if in_paths:
        in_paths = to_list(in_paths)
        step_instance.scheduled_in = []
    elif not step_instance.scheduled_in:
        raise error(
            message=f"No input in in_paths and {step_instance.__class__.__name__}.scheduled_in",
            error_type=TypeError,
            raise_error=False,
        )

    # Add out_paths as relatives to in_path if none is given
    if out_paths:
        out_paths = to_list(out_paths)
        step_instance.scheduled_out = []
    else:
        out_paths = []
        for in_path in in_paths:
            # Get random in_path entry to determine a suitable out_path
            for path in flatten_values(in_path):
                if path:
                    in_path_example = path
                    break
            in_dir = get_directory(in_path_example)
            out_paths.append(os.path.normpath(os.path.join(in_dir, out_path_target)))

    # Run step
    step_instance.run(in_paths=in_paths, out_paths=out_paths, **kwargs)

    # Return results
    results = [getattr(step_instance, attr) for attr in return_attributes]

    return tuple(results) if len(results) > 1 else results[0]


def convert_files(
    raw_data_paths: StrPath, conversion_out_paths: StrPath, step_params: dict, global_params: dict
):
    return generic_step(
        step_class=MSconvert_Runner,
        in_paths=raw_data_paths,
        out_paths=conversion_out_paths,
        out_path_target=os.path.join("..", "converted"),
        step_params=step_params,
        global_params=global_params,
    )


def find_features(
    community_formatted_data_paths: StrPath,
    feature_finding_out_paths: StrPath,
    mzmine_batch: StrPath,
    step_params: dict,
    global_params: dict,
):
    return generic_step(
        step_class=MZmine_Runner,
        in_paths=community_formatted_data_paths,
        out_paths=feature_finding_out_paths,
        out_path_target=os.path.join("..", "processed"),
        step_params=step_params,
        global_params=global_params,
        return_attributes=["processed_out", "log_paths"],
        batch=mzmine_batch,
    )


def annotate_gnps(
    processed_data_paths: StrPath,
    mzmine_log: StrPath,
    gnps_out_paths: StrPath,
    step_params: dict,
    global_params: dict,
):
    return generic_step(
        step_class=GNPS_Runner,
        in_paths=processed_data_paths,
        out_paths=gnps_out_paths,
        out_path_target=os.path.join("..", "annotated"),
        step_params=step_params,
        global_params=global_params,
        mzmine_log=mzmine_log,
    )


def annotate_sirius(
    processed_data_paths: StrPath,
    sirius_out_paths: StrPath,
    config: StrPath,
    step_params: dict,
    global_params: dict,
):
    return generic_step(
        step_class=Sirius_Runner,
        in_paths=processed_data_paths,
        out_paths=sirius_out_paths,
        out_path_target=os.path.join("..", "annotated"),
        step_params=step_params,
        global_params=global_params,
        config=config,
    )


def summarize_annotations(
    processed_data_paths: StrPath,
    gnps_annotation_paths: StrPath,
    sirius_annotation_paths: StrPath,
    summary_out_paths: StrPath,
    step_params: dict,
    global_params: dict,
):
    return generic_step(
        step_class=Summary_Runner,
        in_paths=stretch_to_list_of_dicts(
            {
                "quantification": [processed_data_paths],
                "annotation": [sirius_annotation_paths, gnps_annotation_paths],
            }
        ),
        out_paths=summary_out_paths,
        out_path_target=os.path.join("..", "analysis"),
        step_params=step_params,
        global_params=global_params,
    )


def analyze_difference(
    summary_data_paths: StrPath, analysis_out_paths: StrPath, step_params: dict, global_params: dict
):
    return generic_step(
        step_class=Analysis_Runner,
        in_paths=summary_data_paths,
        out_paths=analysis_out_paths,
        out_path_target=os.path.join("..", "analysis"),
        step_params=step_params,
        global_params=global_params,
    )


# Tasks
convert_files_config = Config.configure_task(
    "convert_files",
    function=convert_files,
    input=[
        raw_data_paths_config,
        conversion_out_paths_config,
        conversion_params_config,
        global_params_config,
    ],
    output=community_formatted_data_paths_config,
    skippable=False,
)

find_features_config = Config.configure_task(
    "find_features",
    function=find_features,
    input=[
        community_formatted_data_paths_config,
        feature_finding_out_paths_config,
        mzmine_batch_config,
        feature_finding_params_config,
        global_params_config,
    ],
    output=[processed_data_paths_config, mzmine_log_config],
    skippable=False,
)

annotate_gnps_config = Config.configure_task(
    "annotate_gnps",
    function=annotate_gnps,
    input=[
        processed_data_paths_config,
        mzmine_log_config,
        gnps_out_paths_config,
        gnps_params_config,
        global_params_config,
    ],
    output=gnps_annotation_paths_config,
    skippable=True,
)

annotate_sirius_config = Config.configure_task(
    "annotate_sirius",
    function=annotate_sirius,
    input=[
        processed_data_paths_config,
        sirius_out_paths_config,
        sirius_config_config,
        sirius_params_config,
        global_params_config,
    ],
    output=sirius_annotation_paths_config,
    skippable=False,
)

summarize_annotations_config = Config.configure_task(
    "summarize_annotations",
    function=summarize_annotations,
    input=[
        processed_data_paths_config,
        gnps_annotation_paths_config,
        sirius_annotation_paths_config,
        summary_out_paths_config,
        summary_params_config,
        global_params_config,
    ],
    output=summary_data_paths_config,
    skippable=False,
)

analyze_difference_config = Config.configure_task(
    "analyze_difference",
    function=analyze_difference,
    input=[
        summary_data_paths_config,
        analysis_out_paths_config,
        analysis_params_config,
        global_params_config,
    ],
    output=analysis_data_paths_config,
    skippable=False,
)


# SCENARIO
ms_analysis_config = Config.configure_scenario(
    id="MS_analysis",
    task_configs=[
        convert_files_config,
        find_features_config,
        annotate_sirius_config,
        annotate_gnps_config,
        summarize_annotations_config,
        analyze_difference_config,
    ],
    sequences={
        "Skip GNPS": [
            convert_files_config,
            find_features_config,
            annotate_sirius_config,
            summarize_annotations_config,
            analyze_difference_config,
        ],
        "Convert": [convert_files_config],
        "Find features": [find_features_config],
        "Sirius annotation": [annotate_sirius_config],
        "GNPS annotation": [annotate_gnps_config],
        "Summarize": [summarize_annotations_config],
        "Analyze": [analyze_difference_config],
    },
)
