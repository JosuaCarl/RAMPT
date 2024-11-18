#!/usr/bin/env python
"""
Testing the SIRIUS annotation.
"""

import os
import argparse
import shutil
import pandas as pd 

import source.helpers.general as helpers
from source.annotation.sirius_pipe import *
from source.annotation.sirius_pipe import main as sirius_pipe_main

import platform as pf

platform = pf.system()
filepath = helpers.get_internal_filepath(__file__)



def test_sirius_pipe_main():
    args = argparse.Namespace( sirius_path="sirius",
                               in_dir=helpers.construct_path(filepath, "..", "example_files"),
                               out_dir=helpers.construct_path(filepath, "..", "out"),
                               projectspace=helpers.construct_path(filepath, "..", "out"),
                               config=helpers.construct_path(filepath, "..", "batch_files", "config.txt"),
                               nested=True, workers=1, save_log=True,
                               verbosity=3, sirius_args=None )

    sirius_pipe_main( args, unknown_args=[] )
    
    assert os.path.isfile( helpers.construct_path(filepath, "..", "out", "projectspace.sirius") )
    assert os.path.isfile( helpers.construct_path(filepath, "..", "out", "example_nested", "projectspace.sirius") )

    df = pd.read_csv( helpers.construct_path(filepath, "..", "out", "formula_identifications.tsv") , sep="\t" )
    assert df.loc[0]["formulaRank"] == 1

    shutil.rmtree( helpers.construct_path(filepath, "..", "out") )
    helpers.make_new_dir( helpers.construct_path(filepath, "..", "out") )