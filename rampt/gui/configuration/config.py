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

processed_data_paths_gnps_config = Config.configure_in_memory_data_node(
    id="processed_data_paths_gnps", scope=Scope.SCENARIO
)
processed_data_paths_sirius_config = Config.configure_in_memory_data_node(
    id="processed_data_paths_sirius", scope=Scope.SCENARIO
)
processed_data_paths_quant_config = Config.configure_in_memory_data_node(
    id="processed_data_paths_quant", scope=Scope.SCENARIO
)

gnps_annotated_data_paths_config = Config.configure_in_memory_data_node(
    id="gnps_annotated_data_paths", scope=Scope.SCENARIO, default_value=None
)

sirius_annotated_data_paths_config = Config.configure_in_memory_data_node(
    id="sirius_annotated_data_paths", scope=Scope.SCENARIO, default_value=None
)

summary_paths_config = Config.configure_in_memory_data_node(
    id="summary_paths", scope=Scope.SCENARIO
)

analysis_paths_config = Config.configure_in_memory_data_node(
    id="analysis_paths", scope=Scope.SCENARIO
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


# Sorter methods
def merge_ios(*args) -> list[dict]:
    merged_ios = []
    for io_dicts in zip(*args):
        merged_io_dict = {}
        # Iterate over found yes ("in_paths", "out_paths")
        for io_key in io_dicts[0].keys():
            merged_io_key = {}
            for io_dict in io_dicts:
                if io_key in merged_io_key:
                    merged_io_key[io_key].update(io_dict[io_key])
                else:
                    merged_io_key.update({io_key: io_dict[io_key]})
            merged_io_dict.update(merged_io_key)

        merged_ios.append(merged_io_dict)
    return merged_ios


def sort_out(
    io_dicts: list[dict],
    step_instance,
    out_step_params: list,
    out_key: str = "out_path",
    return_key: str = "in_paths",
) -> list[list]:
    pipe_step_ios = []
    for pipe_step_param in out_step_params:
        sorted_ios = []
        for io_dict in io_dicts:
            sorted_io = {}
            # Fill all needed parameters
            for key in io_dict[out_key].keys():
                sorted_io.update({key: io_dict[out_key][key]})
            sorted_ios.append({return_key: sorted_io})
        pipe_step_ios.append(sorted_ios)
    return pipe_step_ios


def fixate_global_parameters(global_params: dict, entrypoint: bool = False) -> dict:
    """
    Delete overhanging entries in the global parameters

    :param global_params: Global parameters
    :type global_params: dict
    :param entrypoint: Whether the parameters are set to an entry point, defaults to False
    :type entrypoint: bool, optional
    :return: Curated global parameters
    :rtype: dict
    """
    # Delete mandatory patterns (as they should not be overwritten, because they are mandatory)
    global_params.pop("mandatory_patterns")
    # Delete patterns overwrite, when not set
    for attribute in ["patterns", "pattern", "contains", "prefix", "suffix"]:
        if not entrypoint or global_params.get(attribute, None) is None:
            global_params.pop(attribute, None)
    return global_params


# TODO: DOCUMENTATION & TESTING
# Task methods
def generic_step(
    step_class,
    step_params: dict,
    global_params: dict,
    entrypoint: bool,
    in_outs: list[dict] = None,
    out_folder: StrPath = ".",
    out_step_params: list[dict] = [],
    **kwargs,
) -> tuple[Any] | Any:
    ic(in_outs)
    # Fixate parameters
    global_params = fixate_global_parameters(global_params=global_params, entrypoint=entrypoint)

    # Create step_instance
    step_params.update(global_params)
    # Delete valid runs, as this is saved incorrectly
    step_params.pop("valid_runs")
    step_instance = step_class(**step_params)

    logger.log(
        f"Starting {step_instance.name} step",
        minimum_verbosity=3,
        verbosity=global_params.get("verbosity", 0),
    )

    # Overwrite scheduled, when new in_paths is given
    if in_outs:
        step_instance.scheduled_ios = to_list(in_outs)
    elif not step_instance.scheduled_ios:
        raise logger.error(
            message=f"No input in `in_outs` and `{step_instance.__class__.__name__}.scheduled_ios`",
            error_type=ValueError,
            raise_error=False,
        )

    # Add out_folder to out_root
    for scheduled_io in step_instance.scheduled_ios:
        ic(scheduled_io)
        out_path_root = global_params["out_path_root"]
        scheduled_io["out_path"] = {
            step_instance.data_ids["out_path"][0]: os.path.join(out_path_root, out_folder)
        }

    # Run step
    step_instance.run(out_folder=out_folder, **kwargs)

    # Only retain unique computations
    processed_out = get_uniques(arr=step_instance.processed_ios)
    if out_step_params:
        out = sort_out(
            io_dicts=processed_out, step_instance=step_instance, out_step_params=out_step_params
        )
    else:
        out = [processed_out]
    ic(out)
    return out[0] if len(out) == 1 else out


def convert_files(
    entrypoint: bool,
    raw_data_paths: dict[str, StrPath],
    step_params: dict,
    global_params: dict,
    *out_step_params: list[dict],
):
    return generic_step(
        step_class=MSconvert_Runner,
        entrypoint="conv" in entrypoint.lower(),
        in_outs=raw_data_paths,
        out_folder="converted",
        step_params=step_params,
        global_params=global_params,
        out_step_params=out_step_params,
    )


def find_features(
    entrypoint: bool,
    community_formatted_data_paths: dict[str, StrPath],
    mzmine_batch: StrPath,
    step_params: dict,
    global_params: dict,
    *out_step_params: list[dict],
):
    return generic_step(
        step_class=MZmine_Runner,
        entrypoint="feat" in entrypoint.lower(),
        in_outs=community_formatted_data_paths,
        out_folder="processed",
        step_params=step_params,
        global_params=global_params,
        batch=mzmine_batch,
        out_step_params=out_step_params,
    )


def annotate_gnps(
    entrypoint: bool,
    processed_data_paths: dict[str, StrPath],
    step_params: dict,
    global_params: dict,
    *out_step_params: list[dict],
):
    return generic_step(
        step_class=GNPS_Runner,
        entrypoint="annot" in entrypoint.lower(),
        in_outs=processed_data_paths,
        out_folder="annotated",
        step_params=step_params,
        global_params=global_params,
        out_step_params=out_step_params,
    )


def annotate_sirius(
    entrypoint: bool,
    processed_data_paths: dict[str, StrPath],
    step_params: dict,
    global_params: dict,
    *out_step_params: list[dict],
):
    return generic_step(
        step_class=Sirius_Runner,
        entrypoint="annot" in entrypoint.lower(),
        in_outs=processed_data_paths,
        out_folder="annotated",
        step_params=step_params,
        global_params=global_params,
        out_step_params=out_step_params,
    )


def summarize_annotations(
    entrypoint: bool,
    processed_data_paths: dict[str, StrPath],
    gnps_annotation_paths: dict[str, StrPath],
    sirius_annotation_paths: dict[str, StrPath],
    step_params: dict,
    global_params: dict,
    *out_step_params: list[dict],
):
    return generic_step(
        step_class=Summary_Runner,
        entrypoint="summ" in entrypoint.lower(),
        in_outs=merge_ios(processed_data_paths, gnps_annotation_paths, sirius_annotation_paths),
        out_folder="analysis",
        step_params=step_params,
        global_params=global_params,
        out_step_params=out_step_params,
    )


def analyze_difference(
    entrypoint: bool, summary_data_paths: dict[str, StrPath], step_params: dict, global_params: dict
):
    return generic_step(
        step_class=Analysis_Runner,
        # Not kidding, this covers analysis and analize
        entrypoint="anal" in entrypoint.lower(),
        in_outs=summary_data_paths,
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
        conversion_params_config,
        global_params_config,
        feature_finding_params_config,
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
        mzmine_batch_config,
        feature_finding_params_config,
        global_params_config,
        summary_params_config,
        sirius_params_config,
        gnps_params_config,
    ],
    output=[
        processed_data_paths_quant_config,
        processed_data_paths_sirius_config,
        processed_data_paths_gnps_config,
    ],
    skippable=False,
)

annotate_gnps_config = Config.configure_task(
    "annotate_gnps",
    function=annotate_gnps,
    input=[
        entrypoint_config,
        processed_data_paths_gnps_config,
        gnps_params_config,
        global_params_config,
        summary_params_config,
    ],
    output=gnps_annotated_data_paths_config,
    skippable=True,
)

annotate_sirius_config = Config.configure_task(
    "annotate_sirius",
    function=annotate_sirius,
    input=[
        entrypoint_config,
        processed_data_paths_sirius_config,
        sirius_params_config,
        global_params_config,
        summary_params_config,
    ],
    output=sirius_annotated_data_paths_config,
    skippable=True,
)

summarize_annotations_config = Config.configure_task(
    "summarize_annotations",
    function=summarize_annotations,
    input=[
        entrypoint_config,
        processed_data_paths_quant_config,
        gnps_annotated_data_paths_config,
        sirius_annotated_data_paths_config,
        summary_params_config,
        global_params_config,
        analysis_params_config,
    ],
    output=summary_paths_config,
    skippable=False,
)

analyze_difference_config = Config.configure_task(
    "analyze_difference",
    function=analyze_difference,
    input=[entrypoint_config, summary_paths_config, analysis_params_config, global_params_config],
    output=analysis_paths_config,
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
