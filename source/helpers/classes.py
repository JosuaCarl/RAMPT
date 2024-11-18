#!/usr/bin/env python
"""
Provide super classed for steps in program to ensure transition of intermediate results.
"""
import regex
from multipledispatch import dispatch

from source.helpers.types import StrPath
import source.helpers.general as helpers


# Helper methods for classes / namespaces
@dispatch(object, object)
def get_value( instance:object|dict, key ):
    """
    Extract an attribute of a class or dictionary.

    :param instance: Instance of a class or dictionary
    :type instance: object | dict
    :param key: Attribute or key
    :type key: any
    :return: Value of given key
    :rtype: any
    """
    if isinstance( instance, dict ):
        if key in instance:
            return instance.get( key )
    else:
        return getattr( instance, key )

@dispatch(object, object, object)
def get_value( instance:object|dict, key, default ):
    """
    Extract an attribute of a class or dictionary. If none is present, return default.

    :param instance: Instance of a class or dictionary
    :type instance: object | dict
    :param key: Attribute or key
    :type key: any
    :param default: Default if entry is not found
    :type default: any
    :return: Value of given key
    :rtype: any
    """
    if isinstance( instance, dict ):
        if key in instance:
            return instance.get( key, default )
    else:
        if hasattr( instance, key ):
            return getattr( instance, key )
        else:
            return default


def set_value( instance:object|dict, key, new_value, add_key:bool ):
    """
    Set the value of an attribute or dictionary entry.

    :param instance: Instance of a class or dictionary.
    :type instance: object | dict
    :param key: Attribute or key.
    :type key: any
    :param new_value: Value to link to entry.
    :type new_value: any
    :param add_key: Adds the key, if it is not already present.
    :type add_key: bool
    :return: Instance with updated value.
    :rtype: any
    """
    if isinstance( instance, dict ):
        if add_key:
            instance.update( {key: new_value} )
        else:
            instance[ key ] = new_value
    else:
        if hasattr( instance, key ):
            setattr( instance, key, new_value )
        elif add_key:
            setattr( instance, key, new_value )
        else:
            raise( ValueError(f"The key={key} is not found in instance={instance} and add_key={add_key}."))

    return instance



class Pipe_Step:
    """
    Class for steps in the pipeline.
    """
    def __init__( self, nested:bool=False, workers:int=1, patterns:dict[str,str]=None, save_log:bool=False, additional_args:list=[], verbosity:int=1 ):
        """
        Initialize the pipeline step. Used for pattern matching.
        Provides additional variables for saving processed input and out_locations, its output, and errors.
        
        :param nested: Execute step in a nested fashion, defaults to False
        :type nested: bool, optional
        :param workers: Number of workers to use for parallel execution, defaults to 1
        :type workers: int, optional
        :param patterns: Matching patterns for finding appropriate folders, defaults to None
        :type patterns: dict[str,str], optional
        :param save_log: Whether to save the output(s).
        :type save_log: bool, optional
        :param additional_args: Additional arguments for mzmine, defaults to []
        :type additional_args: list, optional
        :param verbosity: Level of verbosity, defaults to 1
        :type verbosity: int, optional
        """
        self.nested             = nested
        self.workers            = workers
        self.patterns           = patterns
        self.additional_args    = additional_args
        self.verbosity          = verbosity
        self.save_log           = save_log
        self.scheduled_in       = []
        self.scheduled_out       = []
        self.processed_in       = []
        self.processed_out      = []
        self.outs               = []
        self.errs               = []


    def update( self, attributions:dict ):
        """
        Update an attribute of this object.

        :param attributions: Key value pair of attribute name and value
        :type attributions: str
        """
        self.__dict__.update(attributions)


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


    def run( self, **kwargs ):
        if self.nested:
            futures = self.compute_nested( in_root_dir=self.scheduled_in, out_root_dir=self.scheduled_out )
            helpers.compute_scheduled( futures=futures, num_workers=self.workers, verbose=self.verbosity >= 1)
        else:
            self.compute( in_path=self.scheduled_in, out_path=self.scheduled_out, **kwargs )
        return self.processed_out