#!/usr/bin/env python3

import taipy.gui.builder as tgb

from source.gui.helpers import *

# Intemediary paths for selections
## File selection
uploaded_paths = {}
select_folders = {}

selection_trees_pruned = {}
selection_trees_full = {}

selected = {}


def create_expandable_setting(
	create_methods: dict, title: str, hover_text: str = "", expanded=False, **kwargs
):
	with tgb.expandable(title=title, hover_text=hover_text, expanded=expanded, **kwargs):
		with tgb.layout(columns="0.02 1 0.02", gap="2%"):
			tgb.part()
			with tgb.part():
				for title, create_method in create_methods.items():
					with tgb.part(class_name="segment-box"):
						if title:
							tgb.text(f"##### {title}", mode="markdown")
						create_method()
					tgb.html("br")
			tgb.part()


def create_advanced_settings():
	tgb.html("br")
	tgb.html("hr")
	tgb.text("###### Advanced settings", mode="markdown")


def create_file_selection(
	process: str,
	param_attribute_in: str = "scheduled_in",
	execution_key_in: str = None,
	out_node: str = "",
):
	naming_list = (
		[process, param_attribute_in, execution_key_in]
		if execution_key_in
		else [process, param_attribute_in]
	)

	# Construct intermediary dicts
	selector_id = "_".join(naming_list)

	selection_trees_pruned.update({selector_id: []})
	selection_trees_full.update({selector_id: []})
	uploaded_paths.update({selector_id: "."})
	select_folders.update({selector_id: False})
	selected.update({selector_id: []})

	def construct_selection_tree(state, new_path: StrPath = None):
		new_path = (
			new_path
			if new_path
			else get_attribute_recursive(state, f"uploaded_paths.{selector_id}")
		)

		if new_path != ".":
			selection_trees_full[selector_id] = path_nester.update_nested_paths(
				selection_trees_full[selector_id], new_paths=new_path
			)
			pruned_tree = path_nester.prune_lca(nested_paths=selection_trees_full[selector_id])
			set_attribute_recursive(state, f"selection_trees_pruned.{selector_id}", pruned_tree)

	def update_selection(state, name, value):
		selected_labels = [
			element.get("label") if isinstance(element, dict) else element for element in value
		]
		if execution_key_in:
			in_list = get_attribute_recursive(state, f"{process}_params.{param_attribute_in}")
			dictionary = in_list[0] if in_list else {}
			dictionary.update({execution_key_in: selected_labels[0]})
			selected_labels = [dictionary]
		set_attribute_recursive(
			state, f"{process}_params.{param_attribute_in}", selected_labels, refresh=True
		)

	with tgb.layout(columns="1 2 2", columns__mobile="1", gap="5%"):
		# In
		with tgb.part():
			with tgb.part(render="{local}"):
				tgb.button(
					"Select in",
					on_action=lambda state: construct_selection_tree(
						state,
						open_file_folder(
							select_folder=get_attribute_recursive(
								state, f"select_folders.{selector_id}"
							)
						),
					),
				)
			with tgb.part(render="{not local}"):
				tgb.file_selector(
					f"{{uploaded_paths.{selector_id}}}",
					label="Select in",
					extensions="*",
					drop_message=f"Drop files/folders for {process} here:",
					multiple=True,
					on_action=lambda state: construct_selection_tree(state),
				)
			tgb.toggle(f"{{select_folders.{selector_id}}}", label="Select folder")

		tgb.tree(
			f"{{selected.{selector_id}}}",
			lov=f"{{selection_trees_pruned.{selector_id}}}",
			label=f"Select in for {process}",
			filter=True,
			multiple=execution_key_in is None,
			expanded=True,
			on_change=lambda state, name, value: update_selection(state, name, value),
		)

		# Out
		with tgb.part():
			with tgb.part():
				with tgb.part(render="{local}"):
					tgb.button(
						"Select out",
						on_action=lambda state: set_attribute_recursive(
							state,
							f"{process}_params.scheduled_out",
							open_file_folder(select_folder=True),
							refresh=True,
						),
					)
				with tgb.part(render="{not local}"):
					tgb.file_download(
						"{None}",
						active=f"{{scenario.data_nodes['{out_node}'].is_ready_for_reading}}",
						label="Download results",
						on_action=lambda state, id, payload: download_data_node_files(
							state, out_node
						),
					)


# List selectors
list_options = {}
list_uploaded = {}
list_selected = {}


def create_list_selection(
	process: str,
	attribute: str = "batch",
	extensions: str = "*",
	name: str = "batch file",
	default_value=None,
):
	selector_id = f"{process}_{attribute}"
	list_options.update({selector_id: []})
	list_uploaded.update({selector_id: ""})
	list_selected.update({selector_id: default_value})

	def construct_selection_list(state, new_path: StrPath = None):
		new_path = (
			new_path if new_path else get_attribute_recursive(state, f"list_uploaded.{selector_id}")
		)

		if new_path != ".":
			if new_path not in list_options:
				list_options[selector_id].append(new_path)
			set_attribute_recursive(state, f"list_options.{selector_id}", list_options[selector_id])

	def update_selection(state, name, value):
		set_attribute_recursive(state, f"{process}_params.{attribute}", value, refresh=True)

	with tgb.layout(columns="1 1", columns__mobile="1", gap="5%"):
		with tgb.part(render="{local}"):
			tgb.button(
				f"Select {name}",
				on_action=lambda state: construct_selection_list(
					state,
					open_file_folder(
						multiple=False,
						filetypes=[
							(f"{ext[1:]} files", f"*{ext}") for ext in extensions.split(",")
						],
					),
				),
			)
		with tgb.part(render="{not local}"):
			tgb.file_selector(
				f"{{list_uploaded.{selector_id}}}",
				label=f"Select {name}",
				extensions=extensions,
				drop_message=f"Drop {name} for {process} here:",
				multiple=False,
				on_action=lambda state: construct_selection_list(state),
			)

		tgb.selector(
			f"{{list_selected.{selector_id}}}",
			lov=f"{{list_options.{selector_id}}}",
			label=f"Select a {name} for {process}",
			filter=True,
			multiple=False,
			mode="radio",
			on_change=lambda state, name, value: update_selection(state, name, value),
		)


def create_exec_selection(process: str, exec_name: str, exec_attribute="exec_path"):
	with tgb.layout(columns="1 1 1 1", columns__mobile="1", gap="5%"):
		tgb.button(
			"Select executable",
			active="{local}",
			on_action=lambda state: set_attribute_recursive(
				state, f"{process}_params.exec_path", open_file_folder(multiple=False), refresh=True
			),
		)
		tgb.input(
			f"{{{process}_params.{exec_attribute}}}",
			active="{local}",
			label=f"`{exec_name}` executable",
			hover_text=f"You may enter the path to {exec_name}.",
		)
		tgb.part()
		tgb.part()
