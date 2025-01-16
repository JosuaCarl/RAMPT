#!/usr/bin/env python
"""
Common helpers for tests
"""

from os.path import join as join
from os.path import basename as basename
import time
import platform as pf
import shutil

from rampt.helpers.general import *

from tqdm import tqdm as tqdm

import pytest as pytest


# Platform
def get_platform():
    return pf.system()


# Out dir
def make_out(out_path):
    make_new_dir(out_path)


def clean_out(out_path):
    shutil.rmtree(out_path)
    make_new_dir(out_path)


# Pathing
def contruct_common_paths(filepath):
    out_path = construct_path(filepath, "..", "statics", "out")
    mock_path = construct_path(filepath, "..", "statics", "mock_files")
    example_path = construct_path(filepath, "..", "statics", "example_files")
    batch_path = construct_path(filepath, "..", "statics", "batch_files")
    installs_path = construct_path(filepath, "..", "statics", "installs")

    return out_path, mock_path, example_path, batch_path, installs_path


# Timing
def wait(counter: float, unit: str = "s"):
    if unit == "s" or unit.startswith("second"):
        time.sleep(counter)
    elif unit == "m" or unit.startswith("min"):
        time.sleep(counter * 60)
    elif unit == "h" or unit.startswith("hour"):
        time.sleep(counter * 60 * 60)
    elif unit == "d" or unit.startswith("day"):
        time.sleep(counter * 60 * 60 * 24)
    else:
        error(
            message=f"unit {unit} is invalid, please choose between d/h/m/s.", error_type=ValueError
        )
