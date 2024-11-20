#!/usr/bin/env python3

import os 
import tempfile

import tkinter.filedialog as fd

from source.helpers.general import *
from source.helpers.types import StrPath

### Trees
path_nester = Path_Nester()

def get_selection_labels( state, state_attribute:str ):
    selection_labels = [ selection.get("label") for selection in get_attribute_recursive( state, state_attribute ) ]
    return selection_labels

def add_path_to_tree( local_tree, paths ):
    local_tree = path_nester.update_nested_paths( new_paths=paths )
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


# File selection
def open_file_folder( select_folder:bool=False, multiple:bool=True, **kwargs ):
    if select_folder:
        return fd.askdirectory( **kwargs )
    elif multiple:
        return fd.askopenfilenames( **kwargs )
    else:
        return fd.askopenfilename( **kwargs )