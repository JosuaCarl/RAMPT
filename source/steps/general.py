#!/usr/bin/env python
"""
Provide super classed for steps in program to ensure transition of intermediate results.
"""
import os
import regex
import json
from multipledispatch import dispatch

import dask.multiprocessing

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
def get_value( instance:object|dict, key, default ):  # noqa: F811
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
            value = getattr( instance, key, default )
            if value is None:
                return default
            else:
                return value
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


class Step_Configuration:
    """
    Class configuration of pipeline steps in the pipeline.
    """
    def __init__( self, name:str=None, platform:str="Linux", overwrite:bool=True, nested:bool=False, workers:int=1,
                  patterns:dict[str,str]={"in": ".*"}, save_log:bool=True, verbosity:int=1, additional_args:list=[] ):
        """
        Initialize the pipeline step configuration. Used for pattern matching.
        Provides additional variables for saving processed input and out_locations, its output, and errors.
        
        :param name: Name of the step, defaults to None
        :type name: str, optional
        :param platform: Computation platform, defaults to "Linux"
        :type platform: str, optional
        :param overwrite: overwrite previous results, defaults to True
        :type overwrite: bool, optional
        :param workers: Number of workers to use for parallel execution, defaults to 1
        :type workers: int, optional
        :param patterns: Matching patterns for finding appropriate folders, defaults to None
        :type patterns: dict[str,str], optional
        :param save_log: Whether to save the output(s), defaults to True.
        :type save_log: bool, optional
        :param additional_args: Additional arguments for mzmine, defaults to []
        :type additional_args: list, optional
        :param verbosity: Level of verbosity, defaults to 1
        :type verbosity: int, optional
        """
        self.name               = name
        self.platform           = platform
        self.overwrite          = overwrite
        self.nested             = nested
        self.workers            = workers
        self.patterns           = patterns
        self.save_log           = save_log
        self.verbosity          = verbosity
        self.additional_args    = additional_args

    def update( self, attributions:dict ):
        """
        Update an attribute of this object.

        :param attributions: Key value pair of attribute name and value
        :type attributions: str
        """
        self.__dict__.update( attributions )



    def dict_representation( self, attribute=None ):
        attribute = attribute if attribute is not None else self
        attributes_dict = {}
        for attribute, value in attribute.__dict__.items():
            if hasattr( value, "__dict__" ):
                attributes_dict[attribute] = self.dict_representation( value )
            else:
                attributes_dict[attribute] = value
        return attributes_dict
    

    def save( self, location ):
        with open( location, "w") as f:
            json.dump( self.dict_representation( self ), f, indent=4 )


    def load( self, location ):
        with open( location, "r") as f:
            config = json.loads( f.read() )
        self.__init__( **config )



class Pipe_Step(Step_Configuration):
    """
    Class for steps in the pipeline.
    """
    def __init__( self, name:str=None, exec_path:StrPath=None, platform:str="Linux", overwrite:bool=True, nested:bool=False, workers:int=1,
                  patterns:dict[str,str]={"in": ".*"}, save_log:bool=False, verbosity:int=1, additional_args:list=[] ):
        """
        Initialize the pipeline step. Used for pattern matching.
        Provides additional variables for saving processed input and out_locations, its output, and errors.
        
        :param name: Name of the step, defaults to None
        :type name: str, optional
        :param exec_path: Path of executive
        :type exec_path: StrPath
        :param platform: Computational platform/OS, defaults to Linux
        :type platform: str, optional
        :param overwrite: Whether to overwrite previous runs, defaults to True
        :type overwrite: bool, optional
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
        super().__init__( name=name, platform=platform, overwrite=overwrite, nested=nested, workers=workers, patterns=patterns,
                        save_log=save_log, verbosity=verbosity, additional_args=additional_args )

        self.exec_path          = exec_path
        self.futures            = []
        self.scheduled_in       = []
        self.scheduled_out      = []
        self.processed_in       = []
        self.processed_out      = []
        self.outs               = []
        self.errs               = []
        self.log_paths          = []
        self.results            = []



    def match_file_name( self, pattern:str, file_name:StrPath ) -> bool:
        """
        Match a file_name against a regex expression

        :param pattern: Pattern
        :type pattern: str
        :param file_name: Name of the file
        :type file_name: StrPath
        :return: Whether the patter is in the file name
        :rtype: bool
        """
        return bool( regex.search( pattern=pattern, string=str(file_name) ) )



    def store_progress( self, in_path:StrPath, out_path:StrPath, results=None, future=None, out:str="", err:str="", log_path:str="" ):
        """
        Store progress in PipeStep variables. Ensures a match between reprocessed in_paths and out_paths.

        :param in_path: Path to scheduled file.
        :type in_path: StrPath
        :param out_path: Path to output directory.
        :type out_path: StrPath
        :param results: Results of computation in pythonic form.
        :type results: any
        :param out: Output of run, defaults to ""
        :type out: str, optional
        :param err: Error messages of run, defaults to ""
        :type err: str, optional
        :param log_path: Path to log file, defaults to ""
        :type log_path: str, optional
        """
        if in_path in self.processed_in:
            i = self.processed_in.index( in_path )
            self.processed_out[i] = out_path
            self.log_paths[i] = log_path
            self.outs[i] = out
            self.errs[i] = err
            self.results[i] = results
            self.futures[i] = future
        else:
            self.processed_in.append( in_path )
            self.processed_out.append( out_path )
            self.outs.append( out )
            self.errs.append( err )
            self.log_paths.append( log_path )
            self.results.append( results )
            self.futures.append( future )



    def compute( self, cmd:str|list, in_path:StrPath, out_path:StrPath, results=None, log_path:StrPath=None, **kwargs ):
        """
        Execute a computation of a command with or without parallelization.

        :param cmd: Command
        :type cmd: str | list
        :param in_path: Path to in files
        :type in_path: StrPath
        :param out_path: Output path
        :type out_path: StrPath
        :param results: Results of computation
        :type results: any
        :param log_path: Path to logfile, defaults to None
        :type log_path: StrPath, optional
        """
        if not log_path:
            log_path = os.path.join(helpers.get_directory(out_path), f"{self.name}_log.txt") if self.save_log else None
        if self.workers > 1:
            out, err = (None, None)
            future =  dask.delayed(helpers.execute_verbose_command)(cmd=cmd, verbosity=self.verbosity, out_path=log_path, in_path=in_path, **kwargs)
        else:
            out, err = helpers.execute_verbose_command( cmd=cmd, verbosity=self.verbosity, out_path=log_path, **kwargs )
            future = None
        
        self.store_progress(in_path=in_path, out_path=out_path, results=results, future=future, out=out, err=err, log_path=log_path)


    def compute_futures( self ):
        """
        Compute scheduled operations (futures).
        """
        futures = []
        in_paths = []
        for in_path, future in zip(self.processed_in, self.futures):
            if future is not None:
                in_paths.append( in_path )
                futures.append( future )

        results = helpers.compute_scheduled( futures=futures, num_workers=self.workers, verbose=self.verbosity >= 1)

        for in_path, (out, err) in zip(in_paths, results[0]):
            i = self.processed_in.index( in_path )
            self.outs[i] = out
            self.errs[i] = err



    def run_single( self, **kwargs ):
        """
        Compute a single instance of the runner

        :param kwargs: Dictionary of additional arguments for computation
        :type kwargs: ...
        """
        raise(NotImplementedError("The compute function seems to be missing in local implementation"))
    

    def run_directory( self, **kwargs ):
        """
        Compute a folder with the runner

        :param kwargs: Dictionary of additional arguments for computation
        :type kwargs: ...
        """
        raise(NotImplementedError("The run_nested function seems to be missing in local implementation"))
    

    def run_nested( self, **kwargs ):
        """
        Schedule the computation of files in nested folders

        :param kwargs: Dictionary of additional arguments for computation
        :type kwargs: ...
        """
        raise(NotImplementedError("The run_nested function seems to be missing in local implementation"))
    


    def run( self, in_paths:list|StrPath=[], out_paths:list|StrPath=[], **kwargs ) -> list:
        """
        Run the instance step with the given in_paths and out_paths. Constructs a new out_target_folder for each directory, if given.

        :param in_paths: Input paths
        :type in_paths: list|StrPath
        :param out_paths: Output paths
        :type out_paths: list|StrPath
        :param kwargs: Dictionary of additional arguments for computation
        :type kwargs: ...
        :return: Output that was processed
        :rtype: list
        """
        if self.verbosity >= 2:
            print(f"Started {self.__class__.__name__} step")

        # Extend scheduled paths
        self.scheduled_in   = helpers.extend_list( self.scheduled_in, in_paths )
        self.scheduled_out  = helpers.extend_list( self.scheduled_out, out_paths )

        # Handle empty output paths by choosing input direcotory as base
        self.scheduled_out = self.scheduled_out if self.scheduled_out\
                                                else [ os.path.dirname(in_path) for in_path in self.scheduled_in ]

        # Handle smaller scheduled out list by extending with last element
        size_diff = len(self.scheduled_in) - len(self.scheduled_out)
        if size_diff > 0:
            self.scheduled_out += [self.scheduled_out[-1]]*size_diff


        # Loop over all in/out combinations
        for i, (in_path, out_path) in enumerate(zip(self.scheduled_in, self.scheduled_out)):
            in_path = in_path["label"] if isinstance(in_path, dict) else in_path
            out_path = out_path["label"] if isinstance(out_path, dict) else out_path

            # Skip already processed files/folders
            if in_path in self.processed_in and not self.overwrite:
                continue
            
            # Construct out directory if not existent
            os.makedirs( out_path, exist_ok=True )

            # Verbose output
            if self.verbosity >= 3:
                print(f"Processing {in_path} -> {out_path}")

            # Ensure that further passed down lists are processed in parallel with in_path
            additional_arguments = { }
            for argument, value in kwargs.items():
                if isinstance(value, list) and len(value) == len(self.scheduled_in):
                    additional_arguments[argument] = value[i]
                else:
                    additional_arguments[argument] = value
            
            # Activate right computation function
            if self.nested:
                self.run_nested( in_root_dir=in_path, out_root_dir=out_path )
            elif os.path.isdir( in_path ):
                self.run_directory( in_path=in_path, out_path=out_path, **additional_arguments )
            else:
                self.run_single( in_path=in_path, out_path=out_path, **additional_arguments )

            if self.verbosity >= 3:
                print(f"Processed {in_path} -> {out_path}")

        # Compute futures
        if self.futures:
            self.compute_futures()

        # Clear schedules
        self.scheduled_in  = []
        self.scheduled_out = []

        if self.verbosity >= 2:
            print(f"Finished {self.__class__.__name__} step")

        return self.processed_out
