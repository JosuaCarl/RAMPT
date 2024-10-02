#!/usr/bin/env python
"""
Testing the helper functions.
"""


import os
import pytest
from source.helpers.general import *

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