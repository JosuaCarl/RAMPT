#!/usr/bin/env python3

import os
import tempfile
import json
from pathlib import Path

import taipy as tp
import taipy.gui.builder as tgb
from taipy.gui import notify

# Submodules
from rampt.gui.pages.analysis.analysis import *
from rampt.gui.pages.analysis.summary import *
from rampt.gui.pages.analysis.visualization import *
from rampt.gui.pages.annotation.gnps import *
from rampt.gui.pages.annotation.sirius import *
from rampt.gui.pages.conversion.conversion import *
from rampt.gui.pages.feature_finding.feature_finding import *
from rampt.gui.pages.general.general import *

# Configuration
from rampt.gui.configuration.config import *


# Logger
rampt_user_path = os.path.abspath(os.path.join(Path.home(), ".rampt"))
os.makedirs(rampt_user_path, exist_ok=True)
log_path = os.path.abspath(os.path.join(rampt_user_path, "rampt_log.txt"))
logger.log_file_path = log_path

# Working directory
local = True
work_dir_root = tempfile.gettempdir()

# SYNCHRONISATION (First GUI, then Scenario)
## Synchronisation of GUI
param_segment_names = [
    "global",
    "conversion",
    "feature_finding",
    "gnps",
    "sirius",
    "summary",
    "analysis",
]
save_path = None
save_file_types = [("json files", "*.json")]


def construct_params_dict(state, param_segment_names: list = param_segment_names):
    params = {}
    for segment_name in param_segment_names:
        segment_params = get_attribute_recursive(state, f"{segment_name}_params")
        params[f"{segment_name}_params"] = segment_params.dict_representation()
    return params


def save_params(state, path: StrPath = None, scenario_name: str = None):
    global save_path

    if path:
        path = path
    elif scenario_name:
        path = os.path.join(work_dir_root, f"{scenario_name}_config.json")
    elif save_path:
        path = save_path
    else:
        logger.warn(f"Saving to default path: {os.path.join(work_dir_root, 'Default_config.json')}")
        path = os.path.join(work_dir_root, "Default_config.json")

    with open(path, "w") as file:
        json.dump(construct_params_dict(state), file, indent=4)
    save_path = path


def load_params(state, path: StrPath = None, scenario_name: str = "Default"):
    path = path if path else os.path.join(work_dir_root, f"{scenario_name}_config.json")
    if os.path.isfile(path):
        with open(path, "r") as file:
            params = json.loads(file.read())

        for segment_name, segment_params in params.items():
            for attribute, param in segment_params.items():
                set_attribute_recursive(state, f"{segment_name}.{attribute}", param, refresh=True)
    else:
        logger.warn(f"Invalid path for configuration: {path}")


# SCENARIO
scenario = tp.create_scenario(ms_analysis_config, name="Default")

data_node_in = None
data_nodes_in = []

selected_data_in = []

entrypoints = ["↔️ Conversion", "🔍 Feature finding", "✒️ Annotation", "🧺 Summary", "📈 Analysis"]
entrypoint = ""

# Entrypoint lock matches
optional_data_nodes = {
    "↔️ Conversion": ["sirius_annotated_data_paths", "gnps_annotated_data_paths"],
    "🔍 Feature finding": ["sirius_annotated_data_paths", "gnps_annotated_data_paths"],
    "✒️ Annotation": ["sirius_annotated_data_paths", "gnps_annotated_data_paths"],
    "🧺 Summary": ["sirius_annotated_data_paths", "gnps_annotated_data_paths"],
    "📈 Analysis": [],
}
match_entrypoint_step_node = {
    "↔️ Conversion": {
        "conversion_params": ["raw_data_paths"],
        "feature_finding_params.batch": ["mzmine_batch"],
    },
    "🔍 Feature finding": {
        "feature_finding_params": ["community_formatted_data_paths"],
        "feature_finding_params.batch": ["mzmine_batch"],
    },
    "✒️ Annotation": {
        "gnps_params": ["processed_data_paths_gnps"],
        "sirius_params": ["processed_data_paths_sirius"],
    },
    "🧺 Summary": {
        "summary_params": [
            "processed_data_paths_quant",
            "sirius_annotated_data_paths",
            "gnps_annotated_data_paths",
        ]
    },
    "📈 Analysis": {"analysis_params": ["summary_paths"]},
}


def change_entrypoint(state, *args):
    pass


def lock_scenario(state):
    entrypoint = get_attribute_recursive(state, "entrypoint")
    if entrypoint in match_entrypoint_step_node:
        state.scenario.data_nodes.get("entrypoint").write(entrypoint)

        # Fill optionals
        for optional_data_node_id in optional_data_nodes[entrypoint]:
            state.scenario.data_nodes.get(optional_data_node_id).write(None)

        # Check current step information
        pipe_steps_nodes = match_entrypoint_step_node.get(entrypoint)
        for pipe_step_id, data_node_ids in pipe_steps_nodes.items():
            for data_node_id in data_node_ids:
                if "." in pipe_step_id:
                    data = get_attribute_recursive(state, pipe_step_id)
                    data_node = state.scenario.data_nodes.get(data_node_id)
                    data_node.write(data)
                else:
                    pipe_step = get_attribute_recursive(state, pipe_step_id)
                    io_node = []
                    io = {}
                    for scheduled_in_paths in get_attribute_recursive(
                        state, f"{pipe_step_id}.scheduled_ios"
                    ):
                        ic(scheduled_in_paths)
                        io = {
                            "in_paths": scheduled_in_paths,
                            "out_path": {
                                pipe_step.data_ids["out_path"][0]: get_attribute_recursive(
                                    state, "global_params.out_path_root"
                                )
                            },
                        }
                        valid_run_styles = pipe_step.check_io(io)

                        run_style = get_attribute_recursive(
                            state, f"run_style.{pipe_step_id.replace('_params', '')}_scheduled_ios"
                        )
                        if run_style in valid_run_styles:
                            io.update({"run_style": run_style})
                            io_node.append(io)
                        else:
                            logger.warn(
                                f"Invalid io for run style '{run_style}' in '{pipe_step_id}': {io}"
                            )

                    if io_node:
                        data_node = state.scenario.data_nodes.get(data_node_id)
                        data_node.write(io_node)

        params = construct_params_dict(state)
        for param_id, param in params.items():
            state.scenario.data_nodes.get(param_id).write(param)

        state.refresh("scenario")
    else:
        logger.log("No entrypoint defined.")


## Interaction
def add_scenario(state, id, payload):
    # Save previous scenario
    save_params(state, scenario_name=state.scenario.name)

    # Lock new scenario into current configuration
    lock_scenario(state)
    save_params(state, scenario_name=payload.get("label", "Default"))


def change_scenario(state, id, scenario_name):
    # Load parameters into Gui
    if scenario_name:
        load_params(state, scenario_name=scenario_name)

    # Push gui parameters into scenario
    lock_scenario(state)


# JOBS
job = None


style = {".sticky-part": {"position": "sticky", "align-self": "flex-start", "top": "10px"}}

with tgb.Page(style=style) as configuration:
    with tgb.layout(columns="1 3 1", columns__mobile="1", gap="2.5%"):
        # Left part
        with tgb.part(class_name="sticky-part"):
            # Save button
            with tgb.layout(columns="1 1.2 1", gap="2%"):
                tgb.button("💾 Save", on_action=lambda state, id, payload: save_params(state))
                tgb.button(
                    "💾 Save as",
                    on_action=lambda state, id, payload: save_params(
                        state,
                        path=open_file_folder(save=True, multiple=False, filetypes=save_file_types),
                    ),
                )
                tgb.button(
                    "📋 Load",
                    on_action=lambda state, id, payload: load_params(
                        state, path=open_file_folder(multiple=False, filetypes=save_file_types)
                    ),
                )
            tgb.button("◀️ Lock scenario", on_action=lambda state, id, payload: lock_scenario(state))

            # Scenario selector
            tgb.text("#### Scenarios", mode="markdown")
            tgb.scenario_selector("{scenario}", on_creation=add_scenario, on_change=change_scenario)

        # Middle part
        with tgb.part():
            tgb.text("## ⚙️ Configuration", mode="markdown")

            tgb.text("Where would you like to enter the workflow ?", mode="markdown")
            tgb.selector(
                "{entrypoint}",
                lov="{entrypoints}",
                dropdown=True,
                filter=True,
                multiple=False,
                on_change=change_entrypoint,
            )

            # Create possible settings
            # TODO: Unify outpath selection, where the folders are then created
            # TODO: Parse Batch file
            # TODO: Pass entrypoint to backend
            # TODO: Reflect selection of entrypoint in value filling (Discard all I/O entries, not associated to entrypoint)
            with tgb.expandable(
                title="⭐ Recommended settings:",
                hover_text="Settings that are recommended for entering the workflow at the selected point.",
                expanded=True,
            ):
                create_conversion()
                create_feature_finding()
                create_gnps()
                create_sirius()
                create_summary()
                create_analysis()

                tgb.html("br")

                # Out Path
                tgb.text("###### Select root folder for output", mode="markdown")
                with tgb.layout("1 4", columns__mobile="1"):
                    with tgb.part(render="{local}"):
                        tgb.button(
                            "Select out",
                            on_action=lambda state: set_attribute_recursive(
                                state,
                                "global_params.out_path_root",
                                open_file_folder(select_folder=True, multiple=False),
                            ),
                        )
                    tgb.text("{global_params.out_path_root}")

            # Create advanced settings
            tgb.text("### Advanced settings", mode="markdown")
            create_expandable_setting(
                create_methods={"": create_general_advanced},
                title="🌐 General",
                hover_text="General settings, that are applied globally.",
            )

            create_expandable_setting(
                create_methods={"": create_conversion_advanced},
                title="↔️ Conversion",
                hover_text="Convert manufacturer files into community formats.",
            )

            create_expandable_setting(
                create_methods={"": create_feature_finding_advanced},
                title="🔍 Feature finding",
                hover_text="Find features with MZmine through applying steps via a batch file.",
            )

            create_expandable_setting(
                create_methods={"GNPS": create_gnps_advanced, "Sirius": create_sirius_advanced},
                title="✒️ Annotation",
                hover_text="Annotation of data with GNPS and Sirius.",
            )

            create_expandable_setting(
                create_methods={
                    "🧺 Summary": create_summary_advanced,
                    "📈 Analysis": create_analysis_advanced,
                },
                title="📈 Analysis",
                hover_text="Statistical analysis of annotated features.",
            )

            # Scenario / workflow management
            # TODO: Callback after scenario creation
            tgb.text("## 🎬 Scenario management", mode="markdown")
            tgb.scenario(
                "{scenario}",
                show_properties=False,
                show_tags=False,
                show_sequences=True,
                on_submission_change=lambda state, submission, details: notify(
                    state, "I", f"{submission.get_label()} submitted."
                ),
            )

            # Job management
            tgb.text("## 🐝 Jobs", mode="markdown")
            tgb.job_selector("{job}")

            # Display Graph of scenario
            tgb.scenario_dag("{scenario}")

        # Right part
        with tgb.part():
            pass


with tgb.Page(style=style) as visualization:
    create_visualization()
