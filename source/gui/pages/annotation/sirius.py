#!/usr/bin/env python3

import taipy.gui.builder as tgb
from source.gui.pages.common_parts import *

from source.annotation.sirius_pipe import Sirius_Runner

sirius_params = Sirius_Runner()

sirius_path_in = "."
sirius_select_folder_in = False

sirius_path_batch = "."
sirius_batch_path = "config.txt"
sirius_selection_list_batch = []

selections.update( { "sirius_in": [],
                     "sirius_batch": [] })


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

    with tgb.layout( columns="1 1 1 1", columns__mobile="1",gap="5%"):
        tgb.button( "Select executable", active="{local}",
                    on_action=lambda state: set_attribute_recursive( state,
                                                                     "sirius_params.mzmine_path",
                                                                     open_file_folder( multiple=False ),
                                                                     refresh=True ) )
        tgb.input( "{feature_finding_params.mzmine_path}", active="{local}",
                   label="`mzmine` executable",
                    hover_text="You may enter the path to mzmine if it is not accessible via \"mzmine\"" )
        tgb.part()
        tgb.part()
    sirius_path:StrPath="sirius",  projectspace:StrPath=None