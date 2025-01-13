#!/usr/bin/env python3

import os
import tempfile
import json

import taipy as tp
import taipy.gui.builder as tgb

# Submodules
from .analysis.analysis import *
from .analysis.summary import *
from .annotation.gnps import *
from .annotation.sirius import *
from .conversion.conversion import *
from .feature_finding.feature_finding import *
from .general.general import *

# Configuration
from source.gui.configuration.config import *


# Working directory
local = True
work_dir_root = tempfile.gettempdir()


# SYNCHRONISATION (First GUI, then Scenario)
## Synchronisation of GUI
param_segment_names = ["global", "conversion", "feature_finding", "gnps", "sirius", "summary", "analysis"]
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

	# In Data
	"raw_data": ["conversion_params.scheduled_in"],
	"community_formatted_data": [
		"feature_finding_params.scheduled_in",
		"conversion_params.processed_out",
	],
	"processed_data": [
		"gnps_params.scheduled_in",
		"sirius_params.scheduled_in",
		"feature_finding_params.processed_out",
	],
	"gnps_annotations": ["gnps_params.processed_out"],
	"sirius_annotations": ["sirius_params.processed_out"],
	"summary_data": ["analysis_params.scheduled_in", "summary_params.processed_out"],
	"analysis_data": ["analysis_params.processed_out"],

	# Out Data
	"conversion_out": ["conversion_params.scheduled_out", "feature_finding_params.scheduled_in"],
	"feature_finding_out": [
		"feature_finding_params.scheduled_out",
		"gnps_params.scheduled_in",
		"sirius_params.scheduled_in",
	],
	"gnps_out": ["gnps_params.scheduled_out"],
	"sirius_out": ["sirius_params.scheduled_out"],
	"summary_out": ["summary_params.scheduled_out", "analysis_params.scheduled_in"],
	"analysis_out": ["analysis_params.scheduled_out"],

	# Batches and more
	"mzmine_batch": ["feature_finding_params.batch"],
	"mzmine_log": ["feature_finding_params.log_paths", "gnps_params.mzmine_log"],
	"sirius_config": ["sirius_params.config"],
	"sirius_projectspace": ["sirius_params.projectspace"],
}

optional_data_nodes = [
	"conversion_out",
	"feature_finding_out",
	"gnps_out",
	"sirius_out",
	"summary_out"
	"analysis_out",
]


def lock_scenario(state):
	global scenario
	scenario = state.scenario

	params = construct_params_dict(state)

	data_nodes = params.copy()

	for data_node_key, attribute_keys in match_data_node.items():
		for state_attribute in attribute_keys:
			attribute_split = state_attribute.split(".")
			value = params.get(attribute_split[0]).get(attribute_split[1])
			ic({data_node_key: value})
			ic(optional_data_nodes)
			ic(data_node_key in optional_data_nodes)
			if value or data_node_key in optional_data_nodes:
				ic(data_node_key)
				for state_attribute in attribute_keys:
					set_attribute_recursive(state, state_attribute, value, refresh=True)
				data_nodes[data_node_key] = value

	for key, data_node in scenario.data_nodes.items():
		if data_nodes.get(key) or key in optional_data_nodes:
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


# DATA
data_node = None


style = {".sticky-part": {"position": "sticky", "align-self": "flex-start", "top": "10px"}}

with tgb.Page(style=style) as root:
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
			tgb.text("#### Data", mode="markdown")
			tgb.data_node_selector("{data_node}")

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
			tgb.scenario("{scenario}", show_properties=False, show_tags=False, show_sequences=True)
			tgb.scenario_dag("{scenario}")

			tgb.text("## 📊 Data", mode="markdown")
			tgb.data_node("{data_node}")

			tgb.text("## 🐝 Jobs", mode="markdown")
			tgb.job_selector("{job}")

		# Right part
		with tgb.part():
			pass
