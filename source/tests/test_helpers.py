#!/usr/bin/env python
"""
Testing the helper functions.
"""


import shutil
import pytest
from source.helpers.general import *
import platform as pf

platform = pf.system()
filepath = get_internal_filepath(__file__)


# Tests
def test_change_case_str():
    assert change_case_str("abc", slice(1,3) , "upper") == "aBC"

    with pytest.raises(ValueError):
        change_case_str("abc", slice(1,3), "lowa")


def test_open_last_n_line():
    assert open_last_n_line(filepath= construct_path(filepath, "..", "test_files/example_text.txt"), n=1) == "Didididididididi"
    assert open_last_n_line(filepath= construct_path(filepath, "..", "test_files/example_text.txt"), n=2) == "Huhuhuhuhu\n"
    with pytest.raises(OSError):
        open_last_n_line(filepath= construct_path(filepath, "..", "test_files/example_text.txt"), n=5)

def test_open_last_line_with_content():
    assert open_last_line_with_content(filepath= construct_path(filepath, "..", "test_files/example_text.txt")) == "Didididididididi"
    with pytest.raises(ValueError):
        open_last_line_with_content(filepath= construct_path(filepath, "..", "test_files/empty_file"))
    with pytest.raises(ValueError):
        open_last_line_with_content(filepath= construct_path(filepath, "..", "test_files/empty_text.txt"))


def test_execute_verbose_command():
    execute_verbose_command(f"echo test > {construct_path(filepath, "..", "out/text.txt")}", platform=platform, verbosity=3)
    
    assert os.path.isfile( construct_path(filepath, "..", "out/text.txt") )

    with open( construct_path(filepath, "..", "out/text.txt"), "r" ) as f:
        text = f.read()
        assert text == "test\n"

    execute_verbose_command(f"echo test > {construct_path(filepath, "..", "out/text.txt")}", platform=platform, verbosity=1)
    
    assert os.path.isfile( construct_path(filepath, "..", "out/text.txt") )
    with open( construct_path(filepath, "..", "out/text.txt"), "r" ) as f:
        text = f.read()
        assert text == ""

    shutil.rmtree( construct_path(filepath, "..", "out") )
    make_new_dir( construct_path(filepath, "..", "out") )