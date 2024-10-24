#!/usr/bin/env python
"""
Testing the feature finding functions.
"""

import os
import shutil

import source.helpers.general as helpers
from source.feature_finding.mzmine_pipe import *
from source.feature_finding.mzmine_pipe import main as mzmine_pipe_main
import pandas as pd

import platform as pf

platform = pf.system()
filepath = helpers.get_internal_filepath(__file__)



def test_mzmine_pipe_main():
    args = argparse.Namespace( mzmine_path=None,
                               in_dir=helpers.construct_path(filepath, "..", "example_files"),
                               out_dir=helpers.construct_path(filepath, "..", "out"),
                               batch_path=helpers.construct_path(filepath, "..", "batch_files/minimal.mzbatch"),
                               valid_formats=["mzML"],
                               user="joca", nested=True, platform=platform, save_log=False,
                               verbosity=0, mzmine_arguments=None)
    mzmine_pipe_main(args, unknown_args=[])
    
    assert os.path.isfile( helpers.construct_path(filepath, "..", "out/source_files.txt") )
    assert os.path.isfile( helpers.construct_path(filepath, "..", "out/example_nested/source_files.txt") )

    with open( helpers.construct_path(filepath, "..", "out/source_files.txt"), "r" ) as f:
        text = f.read()
        assert text == str( helpers.construct_path(filepath, "..", "example_files/acnA_R1_P3-C1_pos.mzML") )

    df = pd.read_csv( helpers.construct_path(filepath, "..", "out/example_nested/example_nested_iimn_fbmn_quant.csv") )
    assert "row retention time" in df.columns

    del df
    del text

    shutil.rmtree( helpers.construct_path(filepath, "..", "out") )
    helpers.make_new_dir( helpers.construct_path(filepath, "..", "out") )