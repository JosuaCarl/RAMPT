#!/usr/bin/env python

"""
Defining useful types.
"""
import os 
import pandas as pd
import numpy as np
import typing

StrPath = typing.Optional[os.PathLike | str]

Array = typing.Optional[pd.Series | np.ndarray | pd.DataFrame | list | tuple]