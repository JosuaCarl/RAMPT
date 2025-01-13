#!/usr/bin/env python3

import taipy.gui.builder as tgb
from source.gui.pages.common_parts import *

from source.steps.annotation.gnps_pipe import GNPS_Runner

gnps_params = GNPS_Runner()

gnps_path_scheduled_in = "."
gnps_selection_tree_scheduled_in = []
gnps_select_folder_scheduled_in = False

gnps_mzmine_log_selected = "."
gnps_mzmine_log_path = "mzmine_log.txt"
gnps_mzmine_log_selection_list = []


def create_gnps():
	tgb.text("###### File selection", mode="markdown")
	create_file_selection(process="gnps", out_node="gnps_annotations")

	tgb.html("br")

	tgb.text("###### MZmine log selection", mode="markdown")
	create_list_selection(
		process="gnps", attribute="mzmine_log", extensions="*", name="MZmine log file"
	)
