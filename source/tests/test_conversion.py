#!/usr/bin/env python
"""
Testing the conversion functions.
"""

import os
import shutil

from source.helpers.general import construct_path, get_internal_filepath
from source.conversion.msconv_pipe import *
from source.conversion.msconv_pipe import main as msconv_pipe_main
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup

import platform as pf

platform = pf.system()
filepath = get_internal_filepath(__file__)

def test_msconv_pipe_main():
    args = argparse.Namespace(in_dir=construct_path(filepath, "..", "test_files"),
                               out_dir=construct_path(filepath, "..", "out"),
                               format="mzML", suffix=".mzML",
                               prefix=None, contains=None, redo_threshold=None, overwrite=None, workers=None,
                               platform=platform, verbosity=2, msconv_arguments=None)
    msconv_pipe_main(args, unknown_args=[])

    args = argparse.Namespace(in_dir=construct_path(filepath, "..", "test_files"),
                               out_dir=construct_path(filepath, "..", "out"),
                               format="mzXML", suffix=".mzXML",
                               prefix=None, contains=None, redo_threshold=None, overwrite=None, workers=None,
                               platform=platform, verbosity=2, msconv_arguments=None)
    msconv_pipe_main(args, unknown_args=[])
    
    assert os.path.isfile( construct_path(filepath, "..", "out/minimal_file.mzML") )
    assert os.path.isfile( construct_path(filepath, "..", "out/nested_test_folder/minimal_file.mzML") )
    assert os.path.isfile( construct_path(filepath, "..", "out/minimal_file.mzXML") )
    assert os.path.isfile( construct_path(filepath, "..", "out/nested_test_folder/minimal_file.mzXML") )

    with open(construct_path(filepath, "..", "out/minimal_file.mzXML")) as f:
        data = f.read()
        data = BeautifulSoup(data, "xml")
        file = data.find("parentFile")
        assert file.get('fileName') ==  "file:///" + construct_path(filepath, "..", "test_files/minimal_file.mzXML")
    
    with open(construct_path(filepath, "..", "out/minimal_file.mzML")) as f:
        data = f.read()
        data = BeautifulSoup(data, "xml")
        file = data.find("sourceFile")
        assert file.get('location') + "/" +  file.get('name') ==  "file:///" + construct_path(filepath, "..", "test_files/minimal_file.mzML")

    shutil.rmtree( construct_path(filepath, "..", "out") )
    make_new_dir( construct_path(filepath, "..", "out") )
