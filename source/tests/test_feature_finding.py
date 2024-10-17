#!/usr/bin/env python
"""
Testing the feature finding functions.
"""

import os
import shutil

from source.helpers.general import construct_path, get_internal_filepath
from source.conversion.raw_to_mzml import *
from source.feature_finding.mzmine_pipe import main as mzmine_pipe_main
import pandas as pd

import platform as pf

platform = pf.system()
filepath = get_internal_filepath(__file__)



def test_mzmine_pipe_main():
    args = argparse.Namespace( mzmine_path=None,
                               in_dir=construct_path(filepath, "..", "example_files"),
                               out_dir=construct_path(filepath, "..", "out"),
                               batch_path=construct_path(filepath, "..", "batch_files/minimal.mzbatch"),
                               valid_formats=["mzML"],
                               user="joca", nested=True, platform=platform, gnps_pipe=False,
                               verbosity=0, mzmine_arguments=None)
    mzmine_pipe_main(args, unknown_args=[])
    
    assert os.path.isfile( construct_path(filepath, "..", "out/source_files.txt") )
    assert os.path.isfile( construct_path(filepath, "..", "out/example_nested/source_files.txt") )

    with open( construct_path(filepath, "..", "out/source_files.txt"), "r" ) as f:
        text = f.read()
        assert text == str(construct_path(filepath, "..", "example_files/acnA_R1_P3-C1_pos.mzML"))

    df = pd.read_csv( construct_path(filepath, "..", "out/example_nested/example_nested_iimn_fbmn_quant.csv") )
    assert "row retention time" in df.columns

    del df
    del text

    shutil.rmtree( construct_path(filepath, "..", "out") )
    make_new_dir( construct_path(filepath, "..", "out") )