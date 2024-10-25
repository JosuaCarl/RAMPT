#!/usr/bin/env python
"""
Testing the GNPS annotation.
"""

import os
import shutil

import source.helpers.general as helpers
from source.annotation.gnps_pipe import *
from source.annotation.gnps_pipe import main as gnps_pipe_main
import pandas as pd

import platform as pf

platform = pf.system()
filepath = helpers.get_internal_filepath(__file__)



def test_gnps_pipe_main():
    args = argparse.Namespace( in_dir=helpers.construct_path(filepath, "..", "example_files"),
                               out_dir=helpers.construct_path(filepath, "..", "out"),
                               nested=True, workers=1, save_log=True,
                               verbosity=0, gnps_args=None )
    
    gnps_pipe_main( args, unknown_args=[] )
    
    assert os.path.isfile( helpers.construct_path(filepath, "..", "out/example_files_gnps_all_db_annotations.json") )
    assert os.path.isfile( helpers.construct_path(filepath, "..", "out/example_nested/example_nested_gnps_all_db_annotations.json") )


    shutil.rmtree( helpers.construct_path(filepath, "..", "out") )
    helpers.make_new_dir( helpers.construct_path(filepath, "..", "out") )