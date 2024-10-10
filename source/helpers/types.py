#!/usr/bin/env python

"""
Defining useful types.
"""
import typing
import os 
import pandas as pd
import numpy as np

from typing import SupportsIndex

type StrPath = os.PathLike | str

type Array = pd.Series | np.ndarray | pd.DataFrame | list | tuple