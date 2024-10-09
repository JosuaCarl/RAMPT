#!/usr/bin/env python3

"""
Analyze the statistical significance of the population of annotations (i.e. compounds or formlae).
"""

# Imports
from typing import Callable
import pandas as pd
from scipy import stats
from statsmodels.sandbox.stats.multicomp import multipletests



def choose_test(X:pd.DataFrame, Y:pd.DataFrame=None, paired:bool=False) -> Callable:
    # Check for normality
    normality_X = stats.shapiro(X).pvalue > 0.05
    if Y:
        normality_Y = stats.shapiro(Y).pvalue > 0.05


def execute_test(X:pd.DataFrame, Y:pd.DataFrame, test:str) -> bool:
    match test:
        case "ttest_ind":
            stats.ttest_ind(X, Y, equal_var=False)


def p_val_to_star(p:float) -> str:
    """
    Generate star notation from p-value.

    :param p: p-value
    :type p: float
    :return: Star notation of p-value
    :rtype: str
    """
    if p < 1e-4:
        return "****"
    elif p < 1e-3:
        return "***"
    elif p < 1e-2:
        return "**"
    elif p < 5e-2:
        return "*"
    else:
        return "ns"
    
