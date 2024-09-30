from typing import SupportsIndex

def change_case_str(s:str, range:SupportsIndex, conversion:str) -> str:
    """
    Change the case of part of a string.

    :param s: Input string.
    :type s: str
    :param range: Range of string that is to be changed
    :type range: SupportsIndex
    :param conversion: conversion
    :type conversion: str
    :return: Output string.
    :rtype: str
    """
    str_list = list(s)
    selection = s[range]

    match conversion:
        case "upper":
            selection = selection.upper()
        case "lower":
            selection = selection.lower()
        case _:
            raise(ValueError(f"conversion {conversion} is invalid. Choose upper/lower as a valid conversion."))

    str_list[range] =  selection

    return "".join(str_list)