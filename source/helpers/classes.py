#!/usr/bin/env python
"""
Provide super classed for steps in program to ensure transition of intermediate results.
"""

class Pipe_Step:
    def __init__( self, save_out:bool=False, additional_args:list=[], verbosity:int=1 ):
        self.additional_args    = additional_args
        self.verbosity          = verbosity
        self.save_out           = save_out
        self.processed_in       = []
        self.processed_out      = []
        self.outs               = []
        self.errs               = []