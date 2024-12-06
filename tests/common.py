#!/usr/bin/env python
"""
Common helpers for tests
"""
import platform as pf
import shutil
import source.helpers.general as helpers

def get_platform():
    return pf.system()

def contruct_common_paths(filepath):
    out_path = helpers.construct_path(filepath, "..", "out")
    test_path = helpers.construct_path(filepath, "..", "test_files")
    example_path = helpers.construct_path(filepath, "..", "example_files")

    return out_path, test_path, example_path

def clean_out( out_path ):
    shutil.rmtree( out_path )
    helpers.make_new_dir( out_path )