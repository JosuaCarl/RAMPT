#!/usr/bin/env python
"""
Testing the conversion functions.
"""

import os
import shutil

import source.helpers.general as helpers
from source.conversion.msconv_pipe import *
from source.conversion.msconv_pipe import main as msconv_pipe_main
from bs4 import BeautifulSoup

import platform as pf

platform = pf.system()
filepath = helpers.get_internal_filepath(__file__)

def test_msconv_pipe_main():
    args = argparse.Namespace(in_dir=helpers.construct_path(filepath, "..", "test_files"),
                              out_dir=helpers.construct_path(filepath, "..", "out"),
                              pattern="", target_format="mzML", suffix=".mzML", prefix=None, contains=None,
                              redo_threshold=0.0, overwrite=None, workers=None, nested=True,
                              platform=platform, verbosity=2, msconv_arguments=None, save_log=False)
    msconv_pipe_main( args, unknown_args=[] )
    
    assert os.path.isfile( helpers.construct_path(filepath, "..", "out", "minimal_file.mzML") )
    assert os.path.isfile( helpers.construct_path(filepath, "..", "out", "nested_test_folder", "minimal_file.mzML") )

    with open( helpers.construct_path(filepath, "..", "out", "minimal_file.mzML") ) as f:
        data = f.read()
        data = BeautifulSoup(data, "xml")
        file = data.find("sourceFile")
        assert os.path.join( file.get('location'),  file.get('name') ) ==  "file:///" + helpers.construct_path(filepath, "..", "test_files", "minimal_file.mzML")
    
    args.target_format = "mzXML"
    args.suffix = ".mzXML"
    msconv_pipe_main(args, unknown_args=[])
    
    assert os.path.isfile( helpers.construct_path(filepath, "..", "out", "minimal_file.mzXML") )
    assert os.path.isfile( helpers.construct_path(filepath, "..", "out", "nested_test_folder", "minimal_file.mzXML") )

    with open(helpers.construct_path(filepath, "..", "out", "minimal_file.mzXML")) as f:
        data = f.read()
        data = BeautifulSoup(data, "xml")
        file = data.find("parentFile")
        print( helpers.construct_path(filepath, "..", "test_files/minimal_file.mzXML") )
        assert file.get('fileName') ==  "file:///" + helpers.construct_path(filepath, "..", "test_files") + "/" + "minimal_file.mzXML" # <- mzXML path is wrong for windows

    shutil.rmtree( helpers.construct_path(filepath, "..", "out") )
    helpers.make_new_dir( helpers.construct_path(filepath, "..", "out") )
