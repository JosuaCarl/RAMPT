#!/usr/bin/env python3

import taipy.gui.builder as tgb

import source.gui.helpers as helpers

from source.conversion.msconv_pipe import File_Converter


conv_path = "."
conv_tree_paths = []
conv_selection = ""
conv_ask = False
conv_progress = 0


def construct_conversion_selection_tree( state ):
    global conv_tree_paths
    conv_tree_paths = helpers.add_path_to_tree( conv_tree_paths, state, "conv_path")

    pruned_tree = helpers.path_nester.prune_lca( nested_paths=conv_tree_paths )
    helpers.set_attribute_recursive( state, "conv_tree_paths", pruned_tree )


def download_converted( state ):
    # GREY OUT, WHEN converted IS NOT PRESENT
    pass
    

conversion_params = File_Converter()


with tgb.Page() as conversion:
    with tgb.layout( columns="4 1", columns__mobile="1"):
        with tgb.part():
            with tgb.layout( columns="1 1", columns__mobile="1"):
                tgb.file_selector( "{conv_path}",
                                    label="Select File", extensions="*", drop_message="Drop files for conversion here:", multiple=True,
                                    on_action=construct_conversion_selection_tree )
                tgb.tree( "{conversion_params.scheduled_in}",
                            lov="{conv_tree_paths}", label="Select for conversion", filter=True, multiple=True, expanded=True )
            with tgb.layout( columns="1 0.1 1", columns__mobile=1):
                with tgb.part():
                    with tgb.layout( columns="1 1", columns__mobile="1"):
                        tgb.text( "`msconvert`\nexecutable: ", multiline=True, mode="markdown")
                        tgb.input( "{conversion_params.msconvert_path}", hover_text="You may enter the path to msconvert if it is not accessible via \"msconvert\"" )
                tgb.part()
                with tgb.part():
                    tgb.selector( "{conversion_params.target_format}",
                                label="Target_format", lov="mzML;mzXML", dropdown=True, hover_text="The target format for the conversion. mzML is recommended.", width="100px")
            
            # Pattern matching
            tgb.text( "**Pattern matching:**", mode="markdown")
            with tgb.layout( columns="1 0.1 1", columns__mobile="1"):
                with tgb.part():
                    with tgb.layout( columns="1 1", columns__mobile="1"):
                        tgb.text( "Contains:")
                        tgb.input( "{conversion_params.contains}",
                                    hover_text="String that must be contained in file (e.g. experiment)" )
                    with tgb.layout( columns="1 1", columns__mobile="1"):
                        tgb.text( "RegEx:")
                        tgb.input( "{conversion_params.pattern}",
                                    hover_text="Regular expression to filter file (e.g. my_experiment_.*[.]mzML)" )
                tgb.part()
                with tgb.part():
                    with tgb.layout( columns="1 1", columns__mobile="1"):
                        tgb.text( "Prefix:")
                        tgb.input( "{conversion_params.prefix}",
                                    hover_text="Prefix to filter file (e.g. my_experiment)" )
                    with tgb.layout( columns="1 1", columns__mobile="1"):
                        tgb.text( "Suffix:")
                        tgb.input( "{conversion_params.suffix}",
                                    hover_text="Suffix  to filter file (e.g. .mzML)" )

            # Pattern matching
            tgb.text( "**Other:**", mode="markdown")
            with tgb.layout( columns="1 0.1 1", columns__mobile="1"):
                with tgb.part():
                    tgb.text( "Redo-threshold", multiline=True, mode="markdown")
                    tgb.number(  "{conversion_params.redo_threshold}",
                                hover_text="File size threshold for repeating the conversion." )
                tgb.part()
                with tgb.part():
                    tgb.text( "Additional arguments", multiline=True, mode="markdown")
                    tgb.input( "{conversion_params.additional_args}",
                                hover_text="Additional arguments that can be given to the msconvert (works with command line interface).")
        with tgb.part():
            tgb.progress( "{conv_progress}" )