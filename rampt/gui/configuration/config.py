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
## Entrypoint
entrypoint_config = Config.configure_in_memory_data_node(id="entrypoint", scope=Scope.SCENARIO)

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
out_path_root_config = Config.configure_in_memory_data_node(
    id="out_path_root", scope=Scope.SCENARIO
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
    entrypoint: bool,
    in_outs: list[dict] = None,
    out_path_root: str = "..",
    out_folder: StrPath = ".",
    return_attributes: list = ["processed_ios"],
    **kwargs,
) -> tuple[Any] | Any:
    # Fixate parameters
    if not entrypoint:
        for entry in ["patterns", "pattern", "contains", "prefix", "suffix"]:
            global_params.pop(entry)
    step_params.update(global_params)
    step_instance = step_class(**step_params)

    logger.log(
        f"Starting {step_instance.name} step",
        minimum_verbosity=3,
        verbosity=global_params.get("verbosity", 0),
    )

    # Overwrite scheduled, when new in_path is given
    if in_outs:
        step_instance.scheduled_ios = to_list(in_outs)
    elif not step_instance.scheduled_ios:
        raise logger.error(
            message=f"No input in `in_outs` and `{step_instance.__class__.__name__}.scheduled_ios`",
            error_type=ValueError,
            raise_error=False,
        )

    for scheduled_io in step_instance.scheduled_ios:
        if "out" not in scheduled_io:
            if os.path.isabs(out_path_root):
                scheduled_io["out_path"] = {"standard": os.path.join(out_path_root, out_folder)}

    # Run step
    step_instance.run(out_folder=out_folder, **kwargs)

    # Return results
    results = [getattr(step_instance, attr) for attr in return_attributes]

    return tuple(results) if len(results) > 1 else results[0]


def convert_files(
    entrypoint: bool,
    raw_data_paths: StrPath,
    out_path_root: StrPath,
    step_params: dict,
    global_params: dict,
):
    return generic_step(
        step_class=MSconvert_Runner,
        match_patterns="conv" in entrypoint.lower(),
        # in_paths=raw_data_paths,
        out_path_root=out_path_root,
        out_folder="converted",
        step_params=step_params,
        global_params=global_params,
    )


def find_features(
    entrypoint: bool,
    community_formatted_data_paths: StrPath,
    out_path_root: StrPath,
    mzmine_batch: StrPath,
    step_params: dict,
    global_params: dict,
):
    return generic_step(
        step_class=MZmine_Runner,
        match_patterns="feat" in entrypoint.lower(),
        # in_paths=community_formatted_data_paths,
        out_path_root=out_path_root,
        out_folder="processed",
        step_params=step_params,
        global_params=global_params,
        return_attributes=["processed_out", "log_paths"],
        batch=mzmine_batch,
    )


def annotate_gnps(
    entrypoint: bool,
    processed_data_paths: StrPath,
    mzmine_log: StrPath,
    out_path_root: StrPath,
    step_params: dict,
    global_params: dict,
):
    return generic_step(
        step_class=GNPS_Runner,
        match_patterns="annot" in entrypoint.lower(),
        # in_paths=processed_data_paths,
        out_path_root=out_path_root,
        out_folder="annotated",
        step_params=step_params,
        global_params=global_params,
        mzmine_log=mzmine_log,
    )


def annotate_sirius(
    entrypoint: bool,
    processed_data_paths: StrPath,
    out_path_root: StrPath,
    config: StrPath,
    step_params: dict,
    global_params: dict,
):
    return generic_step(
        step_class=Sirius_Runner,
        match_patterns="annot" in entrypoint.lower(),
        # in_paths=processed_data_paths,
        out_path_root=out_path_root,
        out_folder="annotated",
        step_params=step_params,
        global_params=global_params,
        config=config,
    )


def summarize_annotations(
    entrypoint: bool,
    processed_data_paths: StrPath,
    gnps_annotation_paths: StrPath,
    sirius_annotation_paths: StrPath,
    out_path_root: StrPath,
    step_params: dict,
    global_params: dict,
):
    return generic_step(
        step_class=Summary_Runner,
        match_patterns="summ" in entrypoint.lower(),
        # in_paths=stretch_to_list_of_dicts(
        #    {
        #        "quantification": [processed_data_paths],
        #        "annotation": [sirius_annotation_paths, gnps_annotation_paths],
        #    }
        # ),
        out_path_root=out_path_root,
        out_folder="analysis",
        step_params=step_params,
        global_params=global_params,
    )


def analyze_difference(
    entrypoint: bool,
    summary_data_paths: StrPath,
    out_path_root: StrPath,
    step_params: dict,
    global_params: dict,
):
    return generic_step(
        step_class=Analysis_Runner,
        # Not kidding, because this covers analysis and analize
        match_patterns="anal" in entrypoint.lower(),
        # in_paths=summary_data_paths,
        out_path_root=out_path_root,
        out_folder="analysis",
        step_params=step_params,
        global_params=global_params,
    )


# Tasks
convert_files_config = Config.configure_task(
    "convert_files",
    function=convert_files,
    input=[
        entrypoint_config,
        raw_data_paths_config,
        out_path_root_config,
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
        entrypoint_config,
        community_formatted_data_paths_config,
        out_path_root_config,
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
        entrypoint_config,
        processed_data_paths_config,
        mzmine_log_config,
        out_path_root_config,
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
        entrypoint_config,
        processed_data_paths_config,
        out_path_root_config,
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
        entrypoint_config,
        processed_data_paths_config,
        gnps_annotation_paths_config,
        sirius_annotation_paths_config,
        out_path_root_config,
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
        entrypoint_config,
        summary_data_paths_config,
        out_path_root_config,
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
        "Convert": [convert_files_config],
        "Find features": [find_features_config],
        "Sirius annotation": [annotate_sirius_config],
        "GNPS annotation": [annotate_gnps_config],
        "Summarize": [summarize_annotations_config],
        "Analyze": [analyze_difference_config],
    },
)
