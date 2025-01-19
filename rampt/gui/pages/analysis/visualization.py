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
        warn(
            f"Path node {data_node} is not readable. Probably not yet written."
		)
        notify(
            f"Path node {data_node} is not readable. Probably not yet written."
		)
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
    path = ask_filepath(path)

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
            content = read_df(path)
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



# FIGURE PLOTTING
figure = None
figure_id = None
figure_path = None

figure_possibilities = ["values heatmap", "zscore heatmap", "zscore cutoff accumulation", "signal intensity distribution"]
figure_path_possibilities = []


def prepare_figure_path(state, name, figure_id: str):
    match figure_id:
        case "values heatmap":
            path_node = "summary_data_paths"
        case "signal intensity distribution":
            path_node = "summary_data_paths"
        case "zscore heatmap":
            path_node = "analysis_data_paths"
        case "zscore cutoff accumulation":
            path_node = "analysis_data_paths"
    figure_path_possibilities = read_data_node(state, path_node)
    if figure_path_possibilities:
        set_attribute_recursive(
            state,
            "figure_path_possibilities",
            figure_path_possibilities
        )
    

def set_figure(state, name, figure_path: StrPath):
    figure_path = ask_filepath(figure_path)
    figure_id = get_attribute_recursive(state, "figure_id")
    
	# Extract dataframe
    df = read_df(figure_path)
    df = get_peaks_df(df, index_col="m/z")
    match figure_id:
        case "values heatmap":
            figure = plot_quantification_heatmap(df)
            
        case "zscore heatmap":
            figure = plot_heatmap(
                df,
                range=(-15.0, 15.0),
                x=df.columns,
                y=df.index
            )
            
        case "zscore cutoff accumulation":
            figure = plot_cutoff_accumulation(df, cutoff_range=(3, 10), axis=1,)
            
        case "signal intensity distribution":
            figure = plot_quantification_heatmap(df)
    set_attribute_recursive(state, "figure", figure)
    


# VISUALIZATION PAGE
def create_visualization():
    with tgb.layout(columns="1 3 1", columns__mobile="1", gap="2.5%"):
        # Left part
        with tgb.part(class_name="sticky-part"):
            tgb.text("#### Scenarios", mode="markdown")
            tgb.scenario_selector("{scenario}", show_add_button=False)

            tgb.text("#### Data paths", mode="markdown")
            tgb.data_node_selector("{path_data_node}", scenario="{scenario}")

        # Middle part
        with tgb.part():
            tgb.text("## 📊 Data", mode="markdown")
            tgb.data_node("{data_node}")
			
            tgb.text("## 🖌️ Visualization", mode="markdown")
            tgb.selector(
				"{figure_id}",
                lov="{figure_possibilities}",
                dropdown=True,
                on_change=prepare_figure_path
            )
            tgb.selector(
				"{figure_path}",
                lov="{figure_path_possibilities}",
                dropdown=True,
                on_change=set_figure
            ) 
            tgb.chart(
                figure="{figure}",
                rebuild=True
            )

		# Right part
        with tgb.part():
            tgb.html("br")

            tgb.text("#### 🗃️ Path selection", mode="markdown")
            tgb.selector("{path_to_data}", lov="{path_data_node.read()}", dropdown=True)
            
            tgb.html("br")

            tgb.button("🖼️ Show data from path", on_action=populate_data_node)

            tgb.text("#### Populated data", mode="markdown")
            tgb.data_node_selector("{data_node}", datanodes="{populated_data_nodes}")