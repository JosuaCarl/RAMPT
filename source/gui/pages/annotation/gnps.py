#!/usr/bin/env python3

import taipy.gui.builder as tgb
from source.gui.pages.common_parts import *

from source.annotation.gnps_pipe import GNPS_Runner

gnps_params = GNPS_Runner()

gnps_path_in = "."
gnps_selection_tree_in = []
gnps_select_folder_in = False

gnps_batch_selection = "."
gnps_batch_path = "mzmine_log.txt"
gnps_batch_selection_list = []



def create_gnps():
    tgb.text( "###### File selection", mode="markdown")
    create_file_selection( process="gnps", out_node="gnps_annotations" )

    tgb.html("br")

    tgb.text( "###### MZmine log selection", mode="markdown")
    create_list_selection( process="gnps", attribute="mzmine_log", extensions="*", name="MZmine log file" )
