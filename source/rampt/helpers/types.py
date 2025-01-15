#!/usr/bin/env python

"""
Defining useful types.
"""

import os
import pandas as pd
import numpy as np

StrPath = os.PathLike | str

Array = pd.Series | np.ndarray | pd.DataFrame | list | tuple
