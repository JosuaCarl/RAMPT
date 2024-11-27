#!/usr/bin/env python3

import taipy.gui.builder as tgb
from source.gui.helpers import *

from source.conversion.msconv_pipe import File_Converter


conversion_params = File_Converter()

conv_path = "."
conv_select_tree_paths = []
conv_selection = ""
conv_select_folder_in = False


def construct_selection_tree( state, path:StrPath=None ):
    path = path if path else get_attribute_recursive( state, "conv_path")

    if path != ".":
        global conv_select_tree_paths
        conv_select_tree_paths = add_path_to_tree( conv_select_tree_paths, path )

        pruned_tree = path_nester.prune_lca( nested_paths=conv_select_tree_paths )
        set_attribute_recursive( state, "conv_select_tree_paths", pruned_tree )



def create_conversion():
    # File Selection
    with tgb.part():
        tgb.toggle( "{local}",
                    label="Process locally", hover_text="Whether to use the server functionality of taipy to upload files and process them,\
                                                                or to use files that are present on the local machine.")
        tgb.html("br")
        with tgb.layout( columns="1 2 2", columns__mobile="1", gap="5%"):
            with tgb.part():
                with tgb.part( render="{local}" ):
                    tgb.button( "Select in",
                                on_action=lambda state: construct_selection_tree(state, open_file_folder( select_folder=state.conv_select_folder_in)) )
                with tgb.part( render="{not local}"):
                    tgb.file_selector( "{conv_path}",
                                        label="Select in", extensions="*", drop_message="Drop files/folders for conversion here:", multiple=True,
                                        on_action=construct_selection_tree )
                tgb.toggle( "{conv_select_folder_in}", label="Select folder")
            tgb.tree( "{conversion_params.scheduled_in}",
                        lov="{conv_select_tree_paths}", label="Select for conversion", filter=True, multiple=True, expanded=True, mode="check" )
            with tgb.part():
                with tgb.layout(columns="1 1", columns__mobile="1", gap="5%"):
                    with tgb.part():
                        with tgb.part( render="{local}" ):
                            tgb.button( "Select out",
                                        on_action=lambda state: set_attribute_recursive( state,
                                                                                        "conversion_params.scheduled_out",
                                                                                        open_file_folder( select_folder=True ),
                                                                                        refresh=True) )
                        with tgb.part( render="{not local}"):
                            tgb.file_download( "{None}", active="{scenario.data_nodes['community_formatted_data'].is_ready_for_reading}",
                                               label="Download results",
                                               on_action=lambda state, id, payload: download_data_node_files( state,
                                                                                                              "community_formatted_data") )
                    tgb.selector( "{conversion_params.target_format}",
                            label="Target_format", lov="mzML;mzXML", dropdown=True, hover_text="The target format for the conversion. mzML is recommended.", width="100px")
            
        
        tgb.html("br")
        tgb.html("hr")
        tgb.text( "##### Advanced settings", mode="markdown")
        with tgb.layout( columns="1 1 1", columns__mobile="1",gap="5%"):
            tgb.text( "`msconvert`\nexecutable: ", multiline=True, mode="markdown")
            tgb.input( "{conversion_params.msconvert_path}", active="{local}",
                        hover_text="You may enter the path to msconvert if it is not accessible via \"msconvert\"" )
            tgb.button( "Select executable", active="{local}",
                        on_action=lambda state: set_attribute_recursive( state,
                                                                            "conversion_params.msconvert_path",
                                                                            open_file_folder( multiple=False ),
                                                                            refresh=True ) )
            
        
            
        # Pattern matching
        tgb.html("br")
        tgb.text( "###### Pattern matching:", mode="markdown")
        with tgb.layout( columns="1 1", columns__mobile="1", gap="5%"):
            with tgb.part():
                with tgb.layout( columns="1 1", columns__mobile="1"):
                    tgb.text( "Contains:")
                    tgb.input( "{conversion_params.contains}",
                                hover_text="String that must be contained in file (e.g. experiment)" )
                with tgb.layout( columns="1 1", columns__mobile="1"):
                    tgb.text( "RegEx:")
                    tgb.input( "{conversion_params.pattern}",
                                hover_text="Regular expression to filter file (e.g. my_experiment_.*[.]mzML)" )
            with tgb.part():
                with tgb.layout( columns="1 1", columns__mobile="1"):
                    tgb.text( "Prefix:")
                    tgb.input( "{conversion_params.prefix}",
                                hover_text="Prefix to filter file (e.g. my_experiment)" )
                with tgb.layout( columns="1 1", columns__mobile="1"):
                    tgb.text( "Suffix:")
                    tgb.input( "{conversion_params.suffix}",
                                hover_text="Suffix  to filter file (e.g. .mzML)" )

        # Other
        tgb.html("br")
        tgb.text( "###### Other:", mode="markdown")
        with tgb.layout( columns="1 1", columns__mobile="1", gap="5%"):
            with tgb.part():
                tgb.text( "Redo-threshold", multiline=True, mode="markdown")
                tgb.number(  "{conversion_params.redo_threshold}",
                            hover_text="File size threshold for repeating the conversion." )
            with tgb.part():
                tgb.text( "Additional arguments", multiline=True, mode="markdown")
                tgb.input( "{conversion_params.additional_args}",
                            hover_text="Additional arguments that can be given to the msconvert (works with command line interface).")
