#!/usr/bin/env python3
"""
Visualize metabolomic data
"""

import json

import taipy as tp
import taipy.gui.builder as tgb
from taipy.gui import notify

from rampt.gui.helpers import *

from rampt.steps.analysis.statistics import *
from rampt.steps.analysis.visualization import *

from rampt.gui.configuration.config import *


# COMMON
def read_data_node(state, data_node: str) -> bool:
    data_node = state.scenario.data_nodes.get(data_node)
    if data_node.is_ready_for_reading:
        return data_node.read()
    else:
        logger.warn(f"Path node {data_node} is not readable. Probably not yet written.")
        notify(f"Path node {data_node} is not readable. Probably not yet written.")
        return None


def ask_filepath(path: StrPath) -> StrPath:
    # Modify path
    if os.path.isdir(path):
        path = open_file_folder(
            select_folder=False, multiple=False, title="Please select file", initialdir=path
        )
    return path


# DATA
path_data_node = None
paths_to_data = []
path_to_data = None
data_node = None

representable_data_nodes = []
representable_data_node_mapping = {
    "gnps_annotated_data_paths": gnps_annotations_config,
    "sirius_annotated_data_paths": sirius_annotations_config,
    "summary_paths": summary_data_config,
    "analysis_paths": analysis_data_config,
}


def filter_representable(state, id, scenario_name) -> bool:
    representable_data_nodes = []
    for name, node in state.scenario.data_nodes.items():
        if name in representable_data_node_mapping and node.is_ready_for_reading and node.read():
            representable_data_nodes.append(node)
    set_attribute_recursive(state, "representable_data_nodes", representable_data_nodes)


def fill_path_selection(state, *args):
    path_data_node = get_attribute_recursive(state, "path_data_node")
    in_outs = path_data_node.read()
    ic(in_outs)

    extracted_single_paths = []
    for in_out in to_list(in_outs):
        # Define path dictionary
        if "in_paths" in in_out:
            path_dict = in_out["in_paths"]
        else:
            path_dict = in_out
        
        # Extract single paths to list
        for in_element in path_dict.values():
            for path in to_list(in_element):
                extracted_single_paths.append(path)

    set_attribute_recursive(state, "paths_to_data", extracted_single_paths)
    set_attribute_recursive(state, "path_to_data", extracted_single_paths[0])


populated_data_nodes = []
populate_data_node_ids = {}


def populate_data_node(state, *args):
    path_node_name = get_attribute_recursive(state, "path_data_node").get_simple_label()
    data_node_name = path_node_name.replace("_paths", "")

    path = get_attribute_recursive(state, "path_to_data")
    path = ask_filepath(path)

    # Write Check if path
    if os.path.isfile(path):
        # Get original config
        data_node_config = representable_data_node_mapping.get(data_node_name)

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
            content = read_df(path)
        elif data_node_config.storage_type in ["json"]:
            with open(path, "r") as file:
                content = json.load(file)
        # Create data_node
        data_node = tp.create_global_data_node(data_node_config)
        data_node.write(content)
    else:
        logger.warn(f"{path} is no path to a file.")

    # Save information
    populated_data_nodes.append(data_node)
    set_attribute_recursive(state, "data_node", data_node)
    set_attribute_recursive(state, "populated_data_nodes", populated_data_nodes)


# FIGURE PLOTTING
figure = None
figure_id = None
figure_path = None

figure_possibilities = [
    "values heatmap",
    "zscore heatmap",
    "zscore cutoff accumulation",
    "signal intensity distribution",
]
figure_path_possibilities = []


def prepare_figure_path(state, name, figure_id: str):
    match figure_id:
        case "values heatmap":
            path_node = "summary_paths"
        case "signal intensity distribution":
            path_node = "summary_paths"
        case "zscore heatmap":
            path_node = "analysis_paths"
        case "zscore cutoff accumulation":
            path_node = "analysis_paths"
    figure_path_possibilities = read_data_node(state, path_node)
    if figure_path_possibilities:
        set_attribute_recursive(state, "figure_path_possibilities", figure_path_possibilities)
        set_attribute_recursive(state, "figure_path", figure_path_possibilities[0])


def set_figure(state, *args):
    figure_path = get_attribute_recursive(state, "figure_path")
    figure_id = get_attribute_recursive(state, "figure_id")

    # Extract dataframe
    df = read_df(figure_path)
    df = get_peaks_df(df, index_col="m/z")
    match figure_id:
        case "values heatmap":
            figure = plot_quantification_heatmap(df)

        case "zscore heatmap":
            figure = plot_heatmap(df, range=(-15.0, 15.0), x=df.columns, y=df.index)

        case "zscore cutoff accumulation":
            figure = plot_cutoff_accumulation(df, cutoff_range=(3, 10), axis=1)

        case "signal intensity distribution":
            figure = plot_quantification_heatmap(df)
    set_attribute_recursive(state, "figure", figure)


# VISUALIZATION PAGE
def create_visualization():
    with tgb.layout(columns="1 3 1", columns__mobile="1", gap="2.5%"):
        # Left part
        with tgb.part(class_name="sticky-part"):
            tgb.text("#### Scenarios", mode="markdown")
            tgb.scenario_selector(
                "{scenario}", show_add_button=False, on_change=filter_representable
            )

            tgb.text("#### 🕸️ Data path nodes", mode="markdown")
            tgb.data_node_selector(
                "{path_data_node}",
                datanodes="{representable_data_nodes}",
                on_change=fill_path_selection,
            )

            tgb.text("#### 🗃️ Path selection", mode="markdown")
            tgb.selector("{path_to_data}", lov="{paths_to_data}", dropdown=True)

            tgb.button("📊 Show data", on_action=populate_data_node)

        # Middle part
        with tgb.part():
            tgb.text("## 📊 Data", mode="markdown")
            tgb.data_node("{data_node}")

            tgb.html("br")

            tgb.text("## 🖌️ Visualization", mode="markdown")
            tgb.chart(figure="{figure}", rebuild=True)

        # Right part
        with tgb.part():
            tgb.text("#### Populated data", mode="markdown")
            tgb.data_node_selector("{data_node}", datanodes="{populated_data_nodes}")

            tgb.html("br")

            tgb.text("#### Visualization options", mode="markdown")
            tgb.selector(
                "{figure_id}",
                lov="{figure_possibilities}",
                dropdown=True,
                on_change=lambda state, name, value: prepare_figure_path(
                    state=state, name=name, figure_id=value
                ),
            )
            tgb.selector("{figure_path}", lov="{figure_path_possibilities}", dropdown=True)
            tgb.button("🖌️ Show visualization", on_action=set_figure)
