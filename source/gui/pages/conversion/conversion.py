#!/usr/bin/env python3

import taipy.gui.builder as tgb
from source.gui.helpers import *
from source.gui.pages.common_parts import *

from source.conversion.msconv_pipe import File_Converter


conversion_params = File_Converter()

conversion_path_in = "."
conversion_selection_tree_in = []
conversion_select_folder_in = False

selections.update( { "conversion_in": [] })




def create_conversion():
    tgb.text( "###### File selection", mode="markdown")
    create_file_selection( process="conversion", out_node="community_formatted_data" )        
    
    # Advanced settings
    tgb.html("br")
    tgb.html("hr")
    tgb.text( "##### Advanced settings", mode="markdown")
    
    with tgb.layout( columns="1 1 1 1", columns__mobile="1",gap="5%"):
        tgb.button( "Select executable", active="{local}",
                    on_action=lambda state: set_attribute_recursive( state,
                                                                     "conversion_params.msconvert_path",
                                                                     open_file_folder( multiple=False ),
                                                                     refresh=True ) )
        tgb.input( "{conversion_params.msconvert_path}", active="{local}",
                    label="`msconvert` executable",
                    hover_text="You may enter the path to msconvert if it is not accessible via \"msconvert\"" )
        tgb.part()
        tgb.part()
    tgb.html("br")
    tgb.selector( "{conversion_params.target_format}",
            label="Target format", lov="mzML;mzXML", dropdown=True, hover_text="The target format for the conversion. mzML is recommended.", width="100px")




    # Pattern matching
    tgb.html("br")
    tgb.text( "###### Pattern matching:", mode="markdown")
    with tgb.layout( columns="1 1 1 1", columns__mobile="1", gap="5%"):
        tgb.input( "{conversion_params.pattern}",
                    label="Regular Expression:",
                    hover_text="Regular expression to filter file (e.g. my_experiment_.*[.]mzML)" )
        tgb.input( "{conversion_params.contains}",
                    label="Contains:",
                    hover_text="String that must be contained in file (e.g. experiment)" )
        tgb.input( "{conversion_params.prefix}",
                    label="Prefix:",
                    hover_text="Prefix to filter file (e.g. my_experiment)" )
        tgb.input( "{conversion_params.suffix}",
                    label="Suffix:",
                    hover_text="Suffix  to filter file (e.g. .mzML)" )

    # Other
    tgb.html("br")
    tgb.text( "###### Other:", mode="markdown")
    with tgb.layout( columns="1 1", columns__mobile="1", gap="5%"):
        with tgb.part():
            tgb.number(  "{conversion_params.redo_threshold}",
                        label="Redo-threshold",
                        hover_text="File size threshold for repeating the conversion." )
        with tgb.part():
            tgb.input( "{conversion_params.additional_args}",
                        label="Additional arguments",
                        hover_text="Additional arguments that can be given to the msconvert (works with command line interface).")
