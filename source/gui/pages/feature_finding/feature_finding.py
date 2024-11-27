#!/usr/bin/env python3

import taipy.gui.builder as tgb
from source.gui.helpers import *
from source.gui.pages.common_parts import *

from source.feature_finding.mzmine_pipe import MZmine_Runner


feature_finding_params = MZmine_Runner()

feature_finding_path = "."
feature_finding_select_tree_paths = []
feature_finding_selection = ""
feature_finding_select_folder_in = False



def create_feature_finding():
    create_file_selection( process="feature_finding")
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
