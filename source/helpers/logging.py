#!/usr/bin/env python
"""    
Make logging, warnings and error messages more consistent and expressive.
"""
from datetime import datetime
import warnings

from icecream import ic


program_name = "m2s"



def get_now() -> str:
    return str(datetime.now().replace(microsecond=0))



def debug_msg( *args, **kwargs ):
    """
    Icecream debugging.
    """
    ic(* args, **kwargs )


def log( message:str="Info", program:str=program_name, minimum_verbosity:int=0, verbosity:int=0, *args, **kwargs ):
    """
    Print a log message.

    :param message: Message, defaults to "Info"
    :type message: str, optional
    :param program: Name of the program to report for, defaults to program_name
    :type program: str, optional
    :param minimum_verbosity: Minimum required verbosity to show message, defaults to 0
    :type minimum_verbosity: int, optional
    :param verbosity: Current verbosity setting, defaults to 0
    :type verbosity: int, optional
    """
    if verbosity >= minimum_verbosity:
        print( f"[{get_now()}][{program}][INFO (V>={minimum_verbosity})]\t{message}", *args, **kwargs)



def warn( message:str="Warning", program:str=program_name, *args, **kwargs ):
    """
    Print a warning.

    :param message: Warning message, defaults to "Warning"
    :type message: str, optional
    :param program: Name of the program to report for, defaults to program_name
    :type program: str, optional
    """
    warnings.warn( f"[{get_now()}][{program}][WARNING]\t{message}", *args, **kwargs )



def error( message:str="Error", error=ValueError, program:str=program_name, *args, **kwargs ):
    """
    Raise an Error.
    
    :param message: Error message, defaults to "Error"
    :type message: str, optional
    :param error: Error class
    :type error: Error
    :param program: Name of the program to report for, defaults to program_name
    :type program: str, optional
    """
    raise( error( f"[{get_now()}][{program}][ERROR]\t{message}", *args, **kwargs ) )
