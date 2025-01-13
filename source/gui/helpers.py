#!/usr/bin/env python3
from icecream import ic as ic
import os
import tempfile

import tkinter.filedialog as fd

from taipy.gui import download

from source.helpers.general import *
from source.helpers.logging import *

### Trees
def get_selection_labels(state, state_attribute: str):
	selection_labels = [
		selection.get("label") for selection in get_attribute_recursive(state, state_attribute)
	]
	return selection_labels


### Dialogs
def evaluate_dialog(state, payload_pressed, option_list):
	value = option_list[payload_pressed["args"][0]]
	state.show_dialog = False
	return value


## Working directory
def change_work_dir_root(gui, new_root: StrPath = None):
	global work_dir_root
	if new_root:
		if os.path.isdir(new_root):
			work_dir_root = os.path.normpath(new_root)
		else:
			error(message=f"{new_root} is not a valid directory", error_type=ValueError)
	else:
		work_dir_root = gui._get_config("upload_folder", tempfile.gettempdir())


# File selection
def open_file_folder(
	save: bool = False, select_folder: bool = False, multiple: bool = True, **kwargs
):
	if save:
		return fd.asksaveasfilename(**kwargs)
	if select_folder:
		return fd.askdirectory(**kwargs)
	elif multiple:
		return fd.askopenfilenames(**kwargs)
	else:
		return fd.askopenfilename(**kwargs)


# Download
def download_directory(state, dir):
	for root, dirs, files in os.walk(dir):
		for file in files:
			download(state, content=os.path.join(root, file), name=os.path.basename(file))


def download_data_node_files(state, data_node_name, files_attribute: str = "scenario.data_nodes"):
	entries = get_attribute_recursive(state, files_attribute)
	if data_node_name:
		log("Ready for reading: " + str(entries[data_node_name].is_ready_for_reading))
		entries = entries[data_node_name].read()

	entries = entries if isinstance(entries, list) else [entries]
	for entry in entries:
		if os.path.isfile(entry):
			download(state, content=entry, name=os.path.basename(entry))
		elif os.path.isdir(entry):
			download_directory(state, entry)
