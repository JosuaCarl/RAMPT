#!/usr/bin/env python3

import taipy.gui.builder as tgb
from source.gui.pages.common_parts import *

from source.steps.annotation.sirius_pipe import Sirius_Runner

sirius_params = Sirius_Runner()

sirius_path_in = "."
sirius_selection_tree_in = []
sirius_select_folder_in = False

sirius_config_selected = "."
sirius_config_path = ""
sirius_config_selection_list = []

sirius_projectspace_selected = "."
sirius_projectspace_path = "projectspace"
sirius_projectspace_selection_list = []



def create_sirius():
    tgb.text( "###### File selection", mode="markdown")
    create_file_selection( process="sirius", out_node="sirius_annotations" )

    tgb.html("br")

    tgb.text( "###### Config selection", mode="markdown")
    create_list_selection( process="sirius", attribute="config", extensions="*", name="configuration" )

    create_advanced_settings()

    create_exec_selection( process="sirius", exec_name="sirius" )
   
    tgb.html("br")

    create_list_selection( process="sirius", attribute="projectspace", name="projectspace" )