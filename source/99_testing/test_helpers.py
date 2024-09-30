import sys
sys.path.append( '..' )

import pytest
imort pkg

def test_change_case_str():
    assert change_case_str("abc", slice(1,3) , "upper") == "aBC"