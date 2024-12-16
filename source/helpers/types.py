#!/usr/bin/env python

"""
Defining useful types.
"""
import os 
import pandas as pd
import numpy as np

type StrPath = os.PathLike | str

type Array = pd.Series | np.ndarray | pd.DataFrame | list | tuple