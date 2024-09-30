#!/usr/bin/env python

import pytest
from source.helpers.general import *

def test_change_case_str():
    assert change_case_str("abc", slice(1,3) , "upper") == "aBC"

    with pytest.raises(ValueError):
        change_case_str("abc", slice(1,3), "lowa")