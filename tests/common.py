#!/usr/bin/env python
"""
Common helpers for tests
"""
import platform as pf
import shutil
import source.helpers.general as helpers


from icecream import ic as ic

def get_platform():
    return pf.system()

def contruct_common_paths(filepath):
    out_path = helpers.construct_path(filepath, "..", "out")
    test_path = helpers.construct_path(filepath, "..", "test_files")
    example_path = helpers.construct_path(filepath, "..", "example_files")
    batch_path = helpers.construct_path(filepath, "..", "batch_files")

    return out_path, test_path, example_path, batch_path

def clean_out( out_path ):
    shutil.rmtree( out_path )
    helpers.make_new_dir( out_path )