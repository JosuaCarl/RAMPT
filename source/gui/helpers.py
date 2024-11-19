#!/usr/bin/env python3

import os 
import tempfile

from source.helpers.general import *
from source.helpers.types import StrPath

### Trees
path_nester = Path_Nester()

def get_selection_labels( state, state_attribute:str ):
    selection_labels = [ selection.get("label") for selection in get_attribute_recursive( state, state_attribute ) ]
    return selection_labels

def add_path_to_tree( local_tree, state, path_state_attribute ):
    local_tree = path_nester.update_nested_paths( new_paths=get_attribute_recursive( state, path_state_attribute) )
    return local_tree


### Dialogs
def evaluate_dialog( state, payload_pressed, option_list ):
    value = option_list[payload_pressed["args"][0]]
    state.show_dialog = False
    return value


## Working directory
def change_work_dir_root( gui, new_root:StrPath=None ):
    global work_dir_root
    if new_root:
        if os.path.isdir( new_root ):
            work_dir_root = os.path.normpath( new_root )
        else:
            raise( ValueError(f"{new_root} is not a valid directory") )
    else:
        work_dir_root = gui._get_config("upload_folder", tempfile.gettempdir())