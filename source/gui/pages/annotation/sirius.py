#!/usr/bin/env python3

import taipy.gui.builder as tgb
from source.gui.pages.common_parts import *

from source.annotation.sirius_pipe import Sirius_Runner

sirius_params = Sirius_Runner()

sirius_path_in = "."
sirius_selection_tree_in = []
sirius_select_folder_in = False

sirius_path_batch = "."
sirius_batch_path = "config.txt"
sirius_selection_list_batch = []



def create_sirius():
    tgb.text( "###### File selection", mode="markdown")
    create_file_selection( process="sirius", out_node="sirius_annotations" )

    tgb.html("br")

    tgb.text( "###### MZmine log selection", mode="markdown")
    create_batch_selection( process="sirius", batch_attribute="config", extensions="*" )

    # Advanced settings
    tgb.html("br")
    tgb.html("hr")
    tgb.text( "##### Advanced settings", mode="markdown")

    create_exec_selection( process="sirius", exec_name="sirius" )
   
    tgb.html("br")

    create_batch_selection( process="sirius", batch_attribute="projectspace", batch_name="projectspace" )