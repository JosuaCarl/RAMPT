#!/usr/bin/env python3

import taipy.gui.builder as tgb

from source.gui.helpers import *



def create_file_selection( process:str, out_node:str="" ):
    
    def construct_selection_tree( state, path:StrPath=None ):
        path = path if path else get_attribute_recursive( state, f"{process}_path")

        if path != ".":
            globals()[f"{process}_select_tree_paths"] = add_path_to_tree( globals()[f"{process}_select_tree_paths"], path )

            pruned_tree = path_nester.prune_lca( nested_paths=globals()[f"{process}_select_tree_paths"] )
            set_attribute_recursive( state, f"{process}_select_tree_paths", pruned_tree )

    # File Selection
    tgb.toggle( "{local}",
                label="Process locally", hover_text="Whether to use the server functionality of taipy to upload files and process them,\
                                                      or to use files that are present on the local machine.")
    tgb.html("br")
    with tgb.layout( columns="1 2 2", columns__mobile="1", gap="5%"):
        with tgb.part():
            with tgb.part( render="{local}" ):
                tgb.button( "Select in",
                            on_action=lambda state: construct_selection_tree( state,
                                                                              open_file_folder( select_folder=
                                                                                                get_attribute_recursive(state, f"{process}_select_folder_in") )
                                                                            ) )
            with tgb.part( render="{not local}"):
                tgb.file_selector( f"{{{process}_path}}",
                                    label="Select in", extensions="*", drop_message=f"Drop files/folders for {process} here:", multiple=True,
                                    on_action=construct_selection_tree )
            tgb.toggle( f"{{{process}_select_folder_in}}", label="Select folder")
        tgb.tree( f"{{{process}_params.scheduled_in}}",
                    lov=f"{{{process}_select_tree_paths}}", label=f"Select for {process}", filter=True, multiple=True, expanded=True, mode="check" )
        with tgb.part():
            with tgb.part():
                with tgb.part( render="{local}" ):
                    tgb.button( "Select out",
                                on_action=lambda state: set_attribute_recursive( state,
                                                                                f"{process}_params.scheduled_out",
                                                                                open_file_folder( select_folder=True ),
                                                                                refresh=True) )
                with tgb.part( render="{not local}"):
                    tgb.file_download( "{None}", active=f"{{scenario.data_nodes['{out_node}'].is_ready_for_reading}}",
                                        label="Download results",
                                        on_action=lambda state, id, payload: download_data_node_files( state,
                                                                                                        out_node) )