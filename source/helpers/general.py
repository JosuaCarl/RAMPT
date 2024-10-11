#!/usr/bin/env python
"""
Methods that are helpful for general processing.
"""
import os
import regex
from source.helpers.types import *



# File opeations
def get_internal_filepath(file:str) -> StrPath:
    """
    Return the filepath of a passed file.

    :param file: file
    :type file: str
    :return: path of file on system
    :rtype: StrPath
    """
    return os.path.abspath(file)


def construct_path(*args:list[StrPath]) -> StrPath:
    """
    Construct a path from the given list of paths

    :return: Combine path
    :rtype: StrPath
    """
    return os.path.abspath(os.path.join(*args))


def make_new_dir(dir:StrPath) -> bool:
    """
    Make a directory, if one does not already exist in its place.

    :param dir: path to directory
    :type dir: StrPath
    :return: whether a new directory has been
    :rtype: bool
    """
    if not os.path.isdir( dir ):
        os.mkdir( dir )
        return True
    return False



# String operations
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


class Substring(str):
    """
    Class for matching substrings, rather than strings

    :param str: string
    :type str: str-type
    """
    def __eq__(self, other) -> bool:
        """
        Define == as containing the string

        :param other: other String
        :type other: Any
        :return: Whether the string is contained in the Substring
        :rtype: bool
        """
        return other in self



def open_last_n_line(filepath:str, n:int=1) -> str:
    """
    Open the n-th line from the back of a file

    :param filepath: Path to the file
    :type filepath: str
    :param n: position from the back, defaults to 1
    :type n: int, optional
    :return: n-th last line
    :rtype: str
    """
    num_newlines = 0
    with open(filepath, 'rb') as f:
        # catch OSError in case of a one line file
        f.seek(-2, os.SEEK_END)
        while num_newlines < n :
            f.seek(-2, os.SEEK_CUR)
            if f.read(1) == b'\n':
                num_newlines += 1
        return f.readline().decode()

def open_last_line_with_content(filepath:str) -> str:
    """
    Extract the last line which does not only contain whitespace from a file.

    :param filepath: Path to the file
    :type filepath: str
    :return: Last line with content (not only whitespaces)
    :rtype: str
    """
    n = 1
    while n < 1e3:
        try:
            line = open_last_n_line(filepath=filepath, n=n)
        except OSError:
            raise(ValueError(f"File {filepath} does not contain a line with content"))
        if regex.search(r".*\S.*", line):
            return line
        n += 1
    raise(ValueError(f"File {filepath} does not contain a line with content for 1000 lines"))



# Command methods
def execute_verbose_command(cmd:str, platform:str, verbosity:int=1) -> bool:
    """
    Execute a command with the adequate verbosity.

    :param cmd: Command as a string
    :type cmd: str
    :param platform: Current OS platform
    :type platform: str
    :param verbosity: Verbosity level, defaults to 1
    :type verbosity: int, optional
    :return: Success of execution
    :rtype: bool
    """
    if verbosity >= 3:
        os.system( cmd )
    elif platform.lower() == "windows":
        os.system( cmd + ' > NUL')
    else:
        os.system( cmd + ' > /dev/null')
    return True