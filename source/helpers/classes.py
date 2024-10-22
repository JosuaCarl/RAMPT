#!/usr/bin/env python
"""
Provide super classed for steps in program to ensure transition of intermediate results.
"""

class Pipe_Step:
    """
    Class for steps in the pipeline.
    """
    def __init__( self, save_out:bool=False, additional_args:list=[], verbosity:int=1 ):
        """
        Initialize the step. Provides additional variables for saving processed input and out_locations, its output, and errors.

        :param save_out: Whether to save the output(s).
        :type save_out: bool, optional
        :param additional_args: Additional arguments for mzmine, defaults to []
        :type additional_args: list, optional
        :param verbosity: Level of verbosity, defaults to 1
        :type verbosity: int, optional
        """
        self.additional_args    = additional_args
        self.verbosity          = verbosity
        self.save_out           = save_out
        self.processed_in       = []
        self.processed_out      = []
        self.outs               = []
        self.errs               = []