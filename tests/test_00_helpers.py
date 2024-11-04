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

def test_replace_file_ending():
    assert replace_file_ending( os.path.join("a", "b..", "c.anaconda"), "conda") == os.path.join("a", "b..", "c.conda")



def test_path_nester():
    path_nester = Path_Nester()
    result = path_nester.update_nested_paths( new_paths=["/a/c", "/a/b"] )

    expected = [{'id': 1, 'label': 'a', 'children': [{'id': 2, 'label': '/a/c', 'children': []}, {'id': 4, 'label': '/a/b', 'children': []}]}]

    assert result == expected



# CMD
def test_execute_verbose_command():
    execute_verbose_command(f"echo test4", verbosity=1)
    assert not os.path.isfile( construct_path(filepath, "..", "out/text.txt") )

    execute_verbose_command(f"echo test > {construct_path(filepath, "..", "out/text.txt")}", verbosity=3)
    assert os.path.isfile( construct_path(filepath, "..", "out/text.txt") )
    with open( construct_path(filepath, "..", "out/text.txt"), "r" ) as f:
        text = f.read()
        assert text == "test\n"

    execute_verbose_command(f"echo test2 > {construct_path(filepath, "..", "out/text.txt")}", verbosity=1)
    with open( construct_path(filepath, "..", "out/text.txt"), "r" ) as f:
        text = f.read()
        assert text == "test2\n"

    execute_verbose_command(f"echo test3", verbosity=1, out_path=construct_path(filepath, "..", "out/text.txt"))
    with open( construct_path(filepath, "..", "out/text.txt"), "r" ) as f:
        text = f.read()
        assert text == "out:\ntest3\n\n\n\nerr:\nNone"

    shutil.rmtree( construct_path(filepath, "..", "out") )
    make_new_dir( construct_path(filepath, "..", "out") )



# Webrequests
def test_check_for_str_request():
    url = "https://api.openstreetmap.org/api/0.6/relation/10000000/full.json"
    assert check_for_str_request(url=url, query='\"version\":\"0.6\"', retries=2, allowed_fails=1, expected_wait_time=1.0, timeout=5)
    assert not check_for_str_request(url=url, query='\"version\":\"0.sad\"', retries=2, allowed_fails=1, expected_wait_time=1.0, timeout=5)