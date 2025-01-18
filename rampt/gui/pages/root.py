#!/usr/bin/env python3

import os
import tempfile
import json

import taipy as tp
import taipy.gui.builder as tgb
from taipy.gui import notify

# Submodules
from rampt.gui.pages.analysis.analysis import *
from rampt.gui.pages.analysis.summary import *
from rampt.gui.pages.annotation.gnps import *
from rampt.gui.pages.annotation.sirius import *
from rampt.gui.pages.conversion.conversion import *
from rampt.gui.pages.feature_finding.feature_finding import *
from rampt.gui.pages.general.general import *

# Configuration
from rampt.gui.configuration.config import *


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
        warn(f"Saving to default path: {os.path.join(work_dir_root, 'Default_config.json')}")
        path = os.path.join(work_dir_root, "Default_config.json")

    with open(path, "w") as file:
        json.dump(construct_params_dict(state), file, indent=4)
    save_path = path


def load_params(state, path: StrPath = None, scenario_name: str = "Default"):
    path = path if path else os.path.join(work_dir_root, f"{scenario_name}_config.json")
    with open(path, "r") as file:
        params = json.loads(file.read())

    for segment_name, segment_params in params.items():
        for attribute, param in segment_params.items():
            set_attribute_recursive(state, f"{segment_name}.{attribute}", param, refresh=True)


# SCENARIO
scenario = tp.create_scenario(ms_analysis_config, name="Default")


## Synchronisation of Scenario
match_data_node = {
    # Used to decide which values (the last in the list) are used in case of conflicts
    # Processed chained Inputs are preffered to scheduled targets
    # In Data Paths
    "raw_data_paths": ["conversion_params.scheduled_in"],
    "community_formatted_data_paths": [
        "feature_finding_params.scheduled_in",
        "conversion_params.processed_out",
    ],
    "processed_data_paths": [
        "summary_params.scheduled_in['quantification']",
        "gnps_params.scheduled_in",
        "sirius_params.scheduled_in",
        "feature_finding_params.processed_out",
    ],
    "gnps_annotation_paths": [
        "summary_params.scheduled_in['annotation']",
        "gnps_params.processed_out",
    ],
    "sirius_annotation_paths": [
        "summary_params.scheduled_in['annotation']",
        "sirius_params.processed_out",
    ],
    "summary_data_paths": ["analysis_params.scheduled_in", "summary_params.processed_out"],
    "analysis_data_paths": ["analysis_params.processed_out"],
    # Out Data
    "conversion_out_paths": [
        "conversion_params.scheduled_out",
        "feature_finding_params.scheduled_in",
    ],
    "feature_finding_out_paths": [
        "feature_finding_params.scheduled_out",
        "gnps_params.scheduled_in",
        "sirius_params.scheduled_in",
    ],
    "gnps_out_paths": ["gnps_params.scheduled_out"],
    "sirius_out_paths": ["sirius_params.scheduled_out"],
    "summary_out_paths": ["summary_params.scheduled_out", "analysis_params.scheduled_in"],
    "analysis_out_paths": ["analysis_params.scheduled_out"],
    # Batches and more
    "mzmine_batch": ["feature_finding_params.batch"],
    "mzmine_log": ["feature_finding_params.log_paths", "gnps_params.mzmine_log"],
    "sirius_config": ["sirius_params.config"],
    "sirius_projectspace": ["sirius_params.projectspace"],
}

optional_data_nodes = [
    "conversion_out_paths",
    "feature_finding_out_paths",
    "gnps_out_paths",
    "sirius_out_paths",
    "summary_out_paths",
    "analysis_out_paths",
    "sirius_annotation_paths",
    "gnps_annotation_paths",
]


def lock_scenario(state):
    global scenario
    scenario = state.scenario

    # Retrieve parameters
    params = construct_params_dict(state)
    data_nodes = params.copy()

    # Iterate over all possible matches
    for data_node_key, attribute_keys in match_data_node.items():
        # Iterate over all possible places, where data nodes info could come from
        for i, state_attribute in enumerate(attribute_keys):
            # Split to get attributes
            attribute_split = regex.split(r"\.|(?:\[[\"\'](.*?)[\"\']\])", state_attribute)

            # Filter empty strings out
            attribute_split = [part for part in attribute_split if part]

            # Get final value
            value = params
            for key_part in attribute_split:
                # Case there is a list of values that needs to be passed from dict entry
                if isinstance(value, list):
                    value = [entry.get(key_part) for entry in value]
                else:
                    value = value.get(key_part)

            # Check whether the value is written or optional
            if value:
                # Write value to node directory
                for state_attribute in attribute_keys:
                    set_attribute_recursive(state, state_attribute, value, refresh=True)
                data_nodes[data_node_key] = value

    # Write Nones to optional nodes
    for optional_data_node in optional_data_nodes:
        scenario.data_nodes.get(optional_data_node).write(None)

    # Write values to data node
    for key, data_node in scenario.data_nodes.items():
        if data_nodes.get(key) is not None:
            data_node.write(data_nodes.get(key))

    state.scenario = scenario
    state.refresh("scenario")


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
            create_expandable_setting(
                create_methods={"": create_general},
                title="🌐 General",
                hover_text="General settings, that are applied globally.",
            )

            create_expandable_setting(
                create_methods={"": create_conversion},
                title="↔️ Conversion",
                hover_text="Convert manufacturer files into community formats.",
            )

            create_expandable_setting(
                create_methods={"": create_feature_finding},
                title="🔍 Feature finding",
                hover_text="Find features with MZmine through applying steps via a batch file.",
            )

            create_expandable_setting(
                create_methods={"GNPS": create_gnps, "Sirius": create_sirius},
                title="✒️ Annotation",
                hover_text="Annotation of data with GNPS and Sirius.",
            )

            create_expandable_setting(
                create_methods={"Summary": create_summary, "Analysis": create_analysis},
                title="📈 Analysis",
                hover_text="Statistical analysis of annotated features.",
            )

            # Pipeline showcasing
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
            tgb.scenario_dag("{scenario}")

            tgb.text("## 🐝 Jobs", mode="markdown")
            tgb.job_selector("{job}")

        # Right part
        with tgb.part():
            pass


# DATA
path_data_node = None
path_to_data = None
data_node = None

representable_data_nodes = {
    "gnps_annotation": gnps_annotations_config,
    "sirius_annotation": sirius_annotations_config,
    "summary_data": summary_data_config,
    "analysis_data": analysis_data_config,
}


def filter_representable(data_node: tp.DataNode | str) -> bool:
    if data_node:
        if isinstance(data_node, str):
            config_id = data_node
        else:
            config_id = data_node.config_id
        return config_id.replace("_paths", "") in representable_data_nodes.keys()
    else:
        return False


populated_data_nodes = []
populate_data_node_ids = {}


def populate_data_node(state, *args):
    path_node_name = get_attribute_recursive(state, "path_data_node").get_simple_label()
    data_node_name = path_node_name.replace("_paths", "")

    path = get_attribute_recursive(state, "path_to_data")

    # Modify path
    if os.path.isdir(path):
        path = (
            open_file_folder(
                multiple=False, select_folder=False, title="Please select file", initialdir=path
            ),
        )

    # Write Check if path
    if os.path.isfile(path):
        # Get original config
        data_node_config = representable_data_nodes.get(data_node_name)

        # Modify id to allow duplicates
        if data_node_name in populate_data_node_ids:
            populate_data_node_ids[data_node_name] += 1
        else:
            populate_data_node_ids[data_node_name] = 1
        name = "_".join(os.path.split(path)[1].split("."))
        data_node_name = f"{name}_{populate_data_node_ids[data_node_name]}"
        data_node_config.id = data_node_name
        data_node_config.default_path = path

        # Create structure to pass
        if data_node_config.storage_type in ["csv", "excel"]:
            sep = "\t" if "tsv" in path else None
            content = pd.read_csv(path, sep=sep)
        elif data_node_config.storage_type in ["json"]:
            with open(path, "r") as file:
                content = json.load(file)
        # Create data_node
        data_node = tp.create_global_data_node(data_node_config)
        data_node.write(content)
    else:
        warn(f"{path} is no path to a file.")

    # Save information
    populated_data_nodes.append(data_node)
    set_attribute_recursive(state, "data_node", data_node)
    set_attribute_recursive(state, "populated_data_nodes", populated_data_nodes)


with tgb.Page(style=style) as analysis:
    with tgb.layout(columns="1 3 1", columns__mobile="1", gap="2.5%"):
        # Left part
        with tgb.part(class_name="sticky-part"):
            tgb.text("#### Scenarios", mode="markdown")
            tgb.scenario_selector("{scenario}", show_add_button=False, on_change=change_scenario)

            tgb.text("#### Data paths", mode="markdown")
            tgb.data_node_selector("{path_data_node}", scenario="{scenario}")

        # Middle part
        with tgb.part():
            tgb.text("## 📊 Data", mode="markdown")
            tgb.data_node("{data_node}")

        # Right part
        with tgb.part():
            tgb.text("## 🗃️ Path selection", mode="markdown")
            tgb.selector("{path_to_data}", lov="{path_data_node.read()}", dropdown=True)

            tgb.button("🖼️ Show data from path", on_action=populate_data_node)

            tgb.text("#### Populated data", mode="markdown")
            tgb.data_node_selector("{data_node}", datanodes="{populated_data_nodes}")
