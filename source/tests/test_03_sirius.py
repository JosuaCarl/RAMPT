#!/usr/bin/env python
"""
Testing the SIRIUS annotation.
"""

import os
import argparse
import shutil

import source.helpers.general as helpers
from source.annotation.sirius_pipe import *
from source.annotation.sirius_pipe import main as sirius_pipe_main

import platform as pf

platform = pf.system()
filepath = helpers.get_internal_filepath(__file__)



def test_sirius_pipe_main():
    # TODO
    args = argparse.Namespace( in_dir=helpers.construct_path(filepath, "..", "example_files"),
                               out_dir=helpers.construct_path(filepath, "..", "out"),
                               nested=True, workers=1, save_log=True,
                               verbosity=0, gnps_args=None )
    
    sirius_pipe_main( args, unknown_args=[] )
    
    assert os.path.isfile( helpers.construct_path(filepath, "..", "out/example_files_gnps_all_db_annotations.json") )
    assert os.path.isfile( helpers.construct_path(filepath, "..", "out/example_nested/example_nested_gnps_all_db_annotations.json") )


    shutil.rmtree( helpers.construct_path(filepath, "..", "out") )
    helpers.make_new_dir( helpers.construct_path(filepath, "..", "out") )