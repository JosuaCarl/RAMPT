#!/usr/bin/env python
"""
Provide super classed for steps in program to ensure transition of intermediate results.
"""
import regex

from source.helpers.types import StrPath



class Pipe_Step:
    """
    Class for steps in the pipeline.
    """
    def __init__( self, patterns:dict[str,str]=None, save_log:bool=False, additional_args:list=[], verbosity:int=1 ):
        """
        Initialize the pipeline step. Used for pattern matching.
        Provides additional variables for saving processed input and out_locations, its output, and errors.
        
        :param patterns: Matching patterns for finding appropriate folders, defaults to None
        :type patterns: dict[str,str], optional
        :param save_log: Whether to save the output(s).
        :type save_log: bool, optional
        :param additional_args: Additional arguments for mzmine, defaults to []
        :type additional_args: list, optional
        :param verbosity: Level of verbosity, defaults to 1
        :type verbosity: int, optional
        """
        self.patterns           = patterns
        self.additional_args    = additional_args
        self.verbosity          = verbosity
        self.save_log           = save_log
        self.processed_in       = []
        self.processed_out      = []
        self.outs               = []
        self.errs               = []



    def match_file_name( self, pattern:str, file_name:StrPath ) -> bool:
        """
        Match a file_name against a regex expression

        :param pattern: Pattern
        :type pattern: str
        :param file_name: _description_
        :type file_name: StrPath
        :return: _description_
        :rtype: bool
        """
        return bool( regex.search( pattern=pattern, string=str(file_name) ) )
            
    