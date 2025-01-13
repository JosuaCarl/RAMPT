#!/usr/bin/env python3

import taipy.gui.builder as tgb
from source.gui.pages.common_parts import *

from source.steps.analysis.analysis_pipe import Analysis_Runner

analysis_params = Analysis_Runner()

analysis_path_scheduled_in = "."
analysis_selection_tree_scheduled_in = []
analysis_select_folder_scheduled_in = False


# TODO: Implement passing of two files to scheduled_in
def create_analysis():
	tgb.text("###### File selection", mode="markdown")
	create_file_selection(process="analysis", out_node="analysis_data")
