#!/usr/bin/env python
"""
Testing the ion exclusion list creation.
"""

import os
import shutil

import source.helpers.general as helpers
from source.steps.ion_exclusion.ion_exclusion import *
from source.steps.ion_exclusion.ion_exclusion import main as ion_exclusion_pipe_main
import pandas as pd

import platform as pf

platform = pf.system()
filepath = helpers.get_internal_filepath(__file__)



def test_ion_exclusion_pipe_main():
    args = argparse.Namespace( in_dir=helpers.construct_path(filepath, "..", "example_files"),
                               out_dir=helpers.construct_path(filepath, "..", "out"),
                               data_dir=helpers.construct_path(filepath, "..", "example_files"),
                               relative_tolerance=1e-05, absolute_tolerance=1e-08,
                               nested=True, workers=1, save_log=False,
                               verbosity=0, ion_exclusion_args=None )

    ion_exclusion_pipe_main( args, unknown_args=[] )
    
    assert os.path.isfile( helpers.construct_path(filepath, "..", "out/example_files_ms2_presence.tsv") )
    df = pd.read_csv( helpers.construct_path(filepath, "..", "out/example_files_ms2_presence.tsv"), sep="\t")
    
    print(df.loc[0])
    assert df.loc[0]["rt"] == 0.25856668

    assert os.path.isfile( helpers.construct_path(filepath, "..", "out/example_nested/example_nested_ms2_presence.tsv") )


    shutil.rmtree( helpers.construct_path(filepath, "..", "out") )
    helpers.make_new_dir( helpers.construct_path(filepath, "..", "out") )