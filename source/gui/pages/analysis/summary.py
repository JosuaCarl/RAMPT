#!/usr/bin/env python3

import taipy.gui.builder as tgb
from source.gui.pages.common_parts import *

from source.steps.analysis.summary_pipe import Summary_Runner

summary_params = Summary_Runner()

summary_path_quantification_in = "."
summary_selection_tree_quantification_in = []
summary_select_folder_in = False


summary_path_annotation_in = "."
summary_selection_tree_annotation_in = []
summary_select_folder_in = False


# TODO: Implement passing of two files to scheduled_in
def create_summary():
	tgb.text("###### File selection (quantification)", mode="markdown")
	create_file_selection(process="summary", out_node="summary_data")

	tgb.text("###### File selection (annotation)", mode="markdown")
	create_file_selection(process="summary", out_node="summary_data")

	tgb.html("br")

	tgb.text("###### MZmine log selection", mode="markdown")
	create_list_selection(
		process="summary", attribute="mzmine_log", extensions="*", name="MZmine log file"
	)
