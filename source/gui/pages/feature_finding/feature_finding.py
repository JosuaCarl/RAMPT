#!/usr/bin/env python3

import taipy.gui.builder as tgb
from source.gui.helpers import *
from source.gui.pages.common_parts import *

from source.feature_finding.mzmine_pipe import MZmine_Runner


feature_finding_params = MZmine_Runner()

feature_finding_path_in = "."
feature_finding_selection_tree_in = []
feature_finding_select_folder_in = False

feature_finding_path_batch = "."
feature_finding_batch_path = ".mzbatch"
feature_finding_selection_list_batch = []



def create_feature_finding( process="feature_finding" ):  
    tgb.text( "###### File selection", mode="markdown")
    create_file_selection( process="feature_finding", out_node="processed_data" )

    tgb.html("br")

    tgb.text( "###### Batch selection", mode="markdown")
    create_batch_selection( process="feature_finding", extensions=".mzbatch,.xml" )

    # Advanced settings
    tgb.html("br")
    tgb.html("hr")
    tgb.text( "##### Advanced settings", mode="markdown")

    create_exec_selection( process="feature_finding", exec_name="mzmine_console" )
        
    tgb.html("br")
    with tgb.layout( columns="1 1", columns__mobile="1", gap="5%"):
        ## Login
        tgb.input( "{feature_finding_params.login}",
                    label="Login/user command",
                    hover_text="User command for online login" )


        ## Formats
        tgb.input( "{feature_finding_params.valid_formats}",
                    label="Valid formats",
                    hover_text="List of valid formats, separated by ','",
                    on_change=lambda state, var, val: set_attribute_recursive( state,
                                                                                "feature_finding_params.valid_formats",
                                                                                val.split(","),
                                                                                refresh=True ) )

    # Other
    tgb.text( "###### Other:", mode="markdown")
    with tgb.part():
        tgb.input( "{feature_finding_params.additional_args}",
                   label="Additional arguments",
                   hover_text="Additional arguments that can be given to the mzmine (works with command line interface).")
