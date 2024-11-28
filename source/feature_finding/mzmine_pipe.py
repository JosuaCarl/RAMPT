#!/usr/bin/env python3

"""
Use mzmine for feature finding.
"""

# Imports
import os
import asyncio
import argparse

from os.path import join
from tqdm.auto import tqdm
import dask.multiprocessing

import source.helpers.general as helpers
from source.helpers.types import StrPath
from source.helpers.classes import Pipe_Step, get_value, set_value

import regex

def main(args:argparse.Namespace|dict, unknown_args:list[str]=[]):
    """
    Find features with mzmine.

    :param args: Command line arguments
    :type args: argparse.Namespace|dict
    :param unknown_args: Command line arguments that are not known.
    :type unknown_args: list[str]
    """
    # Extract arguments
    exec_path       = get_value(args, "exec_path",        None )
    in_dir          = get_value(args, "in_dir" )
    out_dir         = get_value(args, "out_dir" )
    batch_path      = get_value(args, "batch_path" )
    valid_formats   = get_value(args, "valid_formats",      ["mzML", "mzXML", "imzML"])
    user            = get_value(args, "user",               None )
    nested          = get_value(args, "nested",             False )
    platform        = get_value(args, "platform",           "windows" )
    save_log        = get_value(args, "save_log",           False )
    verbosity       = get_value(args, "verbosity",          1 )
    additional_args = get_value(args, "mzmine_arguments",   unknown_args )
    additional_args = additional_args if additional_args else unknown_args
    
    if not exec_path:
        match helpers.Substring(platform.lower()):
            case "linux":
                exec_path = r'/opt/mzmine-linux-installer/bin/mzmine' 
            case "windows":
                exec_path = r'C:\Program Files\mzmine\mzmine_console.exe'
            case "mac":
                exec_path = r'/Applications/mzmine.app/Contents/MacOS/mzmine'
            case _:
                exec_path = r"mzmine"
    
    if platform.lower() == "windows":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    if user:
        if user == "console":
            login = "--login-console"
        else:
            login = f"--user {user}"
    else:
        print("You did not provide a user. You will be prompted to login by mzmine.\
               For future use please find your user file under $USER/.mzmine/users/ after completing the login.")
        login = "--login"

    mzmine_runner = MZmine_Runner( exec_path=exec_path, batch_path=batch_path, login=login,
                                   valid_formats=valid_formats, save_log=save_log,
                                   additional_args=additional_args, verbosity=verbosity,
                                   nested=nested,
                                   scheduled_in=in_dir, scheduled_out=out_dir )
    return mzmine_runner.run()



class MZmine_Runner(Pipe_Step):
    """
    A runner for mzmine operations. Collects processed files and console outputs/errors.
    """
    def __init__( self, exec_path:StrPath="mzmine_console", batch_path:StrPath="", login:str="-login", valid_formats:list=["mzML", "mzXML", "imzML"],
                  save_log:bool=False, additional_args:list=[], verbosity:int=1, **kwargs):
        """
        Initialize the MZmine_runner.

        :param exec_path: Path to mzmine executable, defaults to "mzmine"
        :type exec_path: StrPath
        :param batch_path: Path to mzmine batch file, defaults to ""
        :type batch_path: StrPath
        :param login: Login or user command, defaults to "-login"
        :type login: str, optional
        :param valid_formats: Formats to search for as valid endings, defaults to ["mzML", "mzXML", "imzML"]
        :type valid_formats: list, optional
        :param save_log: Whether to save the output(s).
        :type save_log: bool, optional
        :param additional_args: Additional arguments for mzmine, defaults to []
        :type additional_args: list, optional
        :param verbosity: Level of verbosity, defaults to 1
        :type verbosity: int, optional
        """
        super().__init__( patterns={"in": rf".*({r'|'.join(valid_formats)})$"}, 
                          save_log=save_log, additional_args=additional_args, verbosity=verbosity )
        if kwargs:
            self.update(kwargs)
        self.exec_path          = exec_path
        self.login              = login
        self.batch_path         = batch_path
        self.valid_formats      = valid_formats


    def check_attributes( self ):
        if not os.path.isfile(self.batch_path):
            raise( ValueError(f"Batch path {self.batch_path} is no file. Please point to a valid mzbatch file."))



    def compute( self, in_path:StrPath, out_path:StrPath, batch_path:StrPath=None ) -> bool:
        """
        Run a single mzmine batch.

        :param in_path: Path to in files (as a .txt with filepaths or glob string)
        :type in_path: StrPath
        :param out_path: Output directory
        :type out_path: StrPath
        :param out_path: Batch file
        :type out_path: StrPath
        :return: Success of the command
        :rtype: bool
        """
        batch_path = batch_path if batch_path else self.batch_path
        cmd = rf'"{self.exec_path}" {self.login} --batch {batch_path} --input {in_path} --output {out_path}\
                {" ".join(self.additional_args)}'
        
        log_path = join(out_path, "mzmine_log.txt") if self.save_log else None
        out, err = helpers.execute_verbose_command( cmd=cmd, verbosity=self.verbosity,
                                                    out_path=log_path )
        self.processed_in.append( in_path )
        self.processed_out.append( out_path )
        self.outs.append( out )
        self.errs.append( err )
        self.log_paths.append( log_path )

        out_path


    def compute_nested( self, in_root_dir:StrPath, out_root_dir:StrPath,
                        futures:list=[], recusion_level:int=0 ) -> list:
        """
        Run a mzmine batch on a nested structure.

        :param in_root_dir: Root directory for descending the structure
        :type in_root_dir: StrPath
        :param out_root_dir: Root directory for output
        :type out_root_dir: StrPath
        :param futures: Future computations for parallelization, defaults to []
        :type futures: list, optional
        :param recusion_level: Current level of recursion, important for determination of level of verbose output, defaults to 0
        :type recusion_level: int, optional
        :return: Open computations from found valid files
        :rtype: list
        """
        verbose_tqdm = self.verbosity >= recusion_level + 2
        found_files = []
        batch_path = None
        for entry in tqdm( os.listdir(in_root_dir), disable=verbose_tqdm, desc="Schedule feature_finding" ):
            entry_path = join(in_root_dir, entry)

            if self.match_file_name( pattern=self.patterns["in"], file_name=entry ):
                found_files.append( entry_path )
            elif self.match_file_name( pattern=r".*mzbatch$", file_name=entry):
                batch_path = entry_path if not self.batch_path else None
            elif os.path.isdir( entry_path ):
                futures = self.compute_nested( in_root_dir=entry_path,
                                                          out_root_dir=join( out_root_dir, entry ),
                                                          futures=futures, recusion_level=recusion_level+1)

        source_paths_file = join( out_root_dir, "source_files.txt" )
        if found_files:
            os.makedirs(out_root_dir, exist_ok=True)
            with open(source_paths_file , "w", encoding="utf8" ) as f:
                f.write( "\n".join(found_files) )
            futures.append( dask.delayed( self.compute )( in_path=source_paths_file, out_path=out_root_dir, batch_path=batch_path ) )

        return futures

    
    def run(self, in_paths:list=[], out_paths:list=[], batch_path:StrPath=None, **kwargs ):
        return super().run( in_paths=in_paths, out_paths=out_paths, batch_path=batch_path, **kwargs )


if __name__ == "__main__":
    parser = argparse.ArgumentParser( prog='mzmine_pipe.py',
                                      description='Use MZmine batch to process the given spectra.\
                                                   A batch file can be created via the MZmine GUI.')
    parser.add_argument('-mz',      '--exec_path',        required=False)
    parser.add_argument('-in',      '--in_dir',             required=True)
    parser.add_argument('-out',     '--out_dir',            required=True)
    parser.add_argument('-batch',   '--batch_path',         required=True)
    parser.add_argument('-formats', '--valid_formats',      required=False,     nargs='+')
    parser.add_argument('-u',       '--user',               required=False)
    parser.add_argument('-n',       '--nested',             required=False,     action="store_true")
    parser.add_argument('-p',       '--platform',           required=False)
    parser.add_argument('-s',       '--save_log',           required=False,     action="store_true")
    parser.add_argument('-v',       '--verbosity',          required=False,     type=int)
    parser.add_argument('-mzmine',  '--mzmine_arguments',   required=False,     nargs=argparse.REMAINDER)

    args, unknown_args = parser.parse_known_args()

    main(args=args, unknown_args=unknown_args)
