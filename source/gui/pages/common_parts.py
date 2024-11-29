#!/usr/bin/env python3

import taipy.gui.builder as tgb

from source.gui.helpers import *

selections = {}



def create_expandable_setting( create_methods:dict, title:str, hover_text:str="", expanded=False, **kwargs ):
    with tgb.expandable( title=title, hover_text=hover_text, expanded=expanded, **kwargs):
        with tgb.layout( columns="0.02 1 0.02", gap="2%"):
            tgb.part()
            with tgb.part():
                for title, create_method in create_methods.items():
                    with tgb.part( class_name="segment-box" ):
                        if title:
                            tgb.text( f"##### {title}", mode="markdown")
                        create_method()
                    tgb.html("br")
            tgb.part()



def create_advanced_settings():
    tgb.html("br")
    tgb.html("hr")
    tgb.text( "###### Advanced settings", mode="markdown")



def create_file_selection( process:str, out_node:str="" ):
    selections.update( { f"{process}_in": [] })
    def construct_selection_tree( state, path:StrPath=None, tree_id:str=f"{process}_in" ):
        path = path if path else get_attribute_recursive( state, f"{process}_path_in")

        if path != ".":
            selections[tree_id] = add_path_to_tree( selections[tree_id] , path)

            pruned_tree = path_nester.prune_lca( nested_paths=selections[tree_id] )
            set_attribute_recursive( state, f"{process}_selection_tree_in", pruned_tree )

    with tgb.layout( columns="1 2 2", columns__mobile="1", gap="5%"):
        # In
        with tgb.part():
            with tgb.part( render="{local}" ):
                tgb.button( "Select in",
                            on_action=lambda state: construct_selection_tree( 
                                                        state,
                                                        open_file_folder( 
                                                            select_folder=
                                                            get_attribute_recursive(state, f"{process}_select_folder_in") )
                                                    )
                        )
            with tgb.part( render="{not local}"):
                tgb.file_selector( f"{{{process}_path_in}}",
                                    label="Select in", extensions="*", drop_message=f"Drop files/folders for {process} here:", multiple=True,
                                    on_action=lambda state: construct_selection_tree( state ) )
            tgb.toggle( f"{{{process}_select_folder_in}}", label="Select folder")
        tgb.tree( f"{{{process}_params.scheduled_in}}",
                    lov=f"{{{process}_selection_tree_in}}",
                    label=f"Select in for {process}",
                    filter=True, multiple=True, expanded=True, mode="check" )
        
        # Out
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



def create_list_selection( process:str, attribute:str="batch", extensions:str="*", name:str="batch file" ):
    selections.update( { f"{process}_{attribute}": [] })
    def construct_selection_list( state, path:StrPath=None, list_id:str=f"{process}_{attribute}" ):
        path = path if path else get_attribute_recursive( state, f"{process}_{attribute}_selected")

        if path != ".":
            if path not in selections:
                selections[list_id].append(path)
            set_attribute_recursive( state, f"{process}_{attribute}_selection_list", selections[list_id]  )

    with tgb.layout( columns="1 1", columns__mobile="1", gap="5%"):
        with tgb.part( render="{local}" ):
            tgb.button( f"Select {name}",
                        on_action=lambda state: construct_selection_list( 
                                                    state,
                                                    open_file_folder( 
                                                        multiple=False,
                                                        filetypes=[ (f"{ext[1:]} files", f"*{ext}")
                                                                    for ext in extensions.split(",") ] 
                                                    )
                                                )
                    )
        with tgb.part( render="{not local}"):
            tgb.file_selector( f"{{{process}_{attribute}_selected}}",
                                label=f"Select {name}", extensions=extensions,
                                drop_message=f"Drop {name} for {process} here:",
                                multiple=False,
                                on_action=lambda state: construct_selection_list( state ) )
            
        tgb.selector( f"{{{process}_params.{attribute}}}",
                        lov=f"{{{process}_{attribute}_selection_list}}",
                        label=f"Select a {name} for {process}",
                        filter=True, multiple=False, mode="radio" )


def create_exec_selection( process:str, exec_name:str, exec_attribute="exec_path"):
    with tgb.layout( columns="1 1 1 1", columns__mobile="1",gap="5%"):
        tgb.button( "Select executable", active="{local}",
                    on_action=lambda state: set_attribute_recursive( state,
                                                                     f"{process}_params.exec_path",
                                                                     open_file_folder( multiple=False ),
                                                                     refresh=True ) )
        tgb.input( f"{{{process}_params.{exec_attribute}}}", active="{local}",
                   label=f"`{exec_name}` executable",
                    hover_text=f"You may enter the path to {exec_name}." )
        tgb.part()
        tgb.part()