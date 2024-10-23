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

from source.helpers.general import Substring, execute_verbose_command, compute_scheduled
from source.helpers.types import StrPath
from source.helpers.classes import Pipe_Step


def main(args, unknown_args):
    """
    Execute the conversion.

    :param args: Command line arguments
    :type args: any
    :param unknown_args: Command line arguments that are not known.
    :type unknown_args: any
    """
    # Extract arguments
    mzmine_path     = args.mzmine_path      if args.mzmine_path else None
    in_dir          = args.in_dir
    out_dir         = args.out_dir
    batch_path      = args.batch_path
    valid_formats   = args.valid_formats    if args.valid_formats else ["mzML", "mzXML", "imzML"]
    user            = args.user             if args.user else None
    nested          = args.nested           if args.nested else False
    platform        = args.platform         if args.platform else "windows"
    save_log        = args.save_log         if args.save_log else False
    verbosity       = args.verbosity        if args.verbosity else 1
    additional_args = args.mzmine_arguments if args.mzmine_arguments else unknown_args
    
    if not mzmine_path:
        match Substring(platform.lower()):
            case "linux":
                mzmine_path = r'/opt/mzmine-linux-installer/bin/mzmine' 
            case "windows":
                mzmine_path = r'C:\"Program Files"\mzmine\mzmine_console.exe'
            case "mac":
                mzmine_path = r'/Applications/mzmine.app/Contents/MacOS/mzmine'
            case _:
                mzmine_path = r"mzmine"
    
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

    mzmine_runner = MZmine_Runner( mzmine_path=mzmine_path, batch_path=batch_path, login=login,
                                   valid_formats=valid_formats, save_log=save_log,
                                   additional_args=additional_args, verbosity=verbosity)
    if nested:
        futures = mzmine_runner.run_mzmine_batches_nested( root_dir=in_dir, out_root_dir=out_dir )
        computation_complete = compute_scheduled( futures=futures, num_workers=1, verbose=verbosity >= 1)
    else:
        mzmine_runner.run_mzmine_batch( in_path=in_dir, out_path=out_dir )


class MZmine_Runner(Pipe_Step):
    """
    A runner for mzmine operations. Collects processed files and console outputs/errors.
    """
    def __init__( self, mzmine_path:StrPath, batch_path:StrPath, login:str="-login", valid_formats:list=["mzML", "mzXML", "imzML"],
                  save_log:bool=False, additional_args:list=[], verbosity:int=1 ):
        """
        Initialize the MZmine_runner.

        :param mzmine_path: Path to mzmine executable
        :type mzmine_path: StrPath
        :param batch_path: Path to mzmine batch file
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
        super().__init__( save_log=save_log, additional_args=additional_args, verbosity=verbosity )
        self.mzmine_path        = mzmine_path
        self.login              = login
        self.batch_path         = batch_path
        self.valid_formats      = valid_formats



    def run_mzmine_batch( self, in_path:StrPath, out_path:StrPath ) -> bool:
        """
        Run a single mzmine batch.

        :param in_path: Path to in files (as a .txt with filepaths or glob string)
        :type in_path: StrPath
        :param out_path: Output directory
        :type out_path: StrPath
        :return: Success of the command
        :rtype: bool
        """
        cmd = f'\"{self.mzmine_path}\" {self.login} --batch {self.batch_path} --input {in_path} --output {out_path}\
                {" ".join(self.additional_args)}'
              
        out, err = execute_verbose_command( cmd=cmd, verbosity=self.verbosity,
                                            out_path=join(out_path, "mzmine_log.txt") if self.save_log else None )
        self.processed_in.append( in_path )
        self.processed_out.append( out_path )
        self.outs.append( out )
        self.errs.append( err )


    def run_mzmine_batches_nested( self, root_dir:StrPath, out_root_dir:StrPath,
                                   futures:list=[], recusion_level:int=0) -> list:
        """
        Run a mzmine batch on a nested structure.

        :param root_dir: Root directory for descending the structure
        :type root_dir: StrPath
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
        in_paths_file = join(out_root_dir, "source_files.txt")

        for root, dirs, files in os.walk(root_dir):
            found_files = [join(root_dir, file) for file in files if file.split(".")[-1] in self.valid_formats]
            
            if found_files:
                os.makedirs(out_root_dir, exist_ok=True)
                with open(in_paths_file , "w" ) as f:
                    f.write( "\n".join(found_files) )
                futures.append( dask.delayed(self.run_mzmine_batch)( in_path=in_paths_file, out_path=out_root_dir ) )

            for dir in tqdm(dirs, disable=verbose_tqdm, desc="Directories"):
                futures = self.run_mzmine_batches_nested( root_dir=join(root_dir, dir),
                                                          out_root_dir=join(out_root_dir, dir),
                                                          futures=futures, recusion_level=recusion_level+1)
            
            return futures



if __name__ == "__main__":
    parser = argparse.ArgumentParser( prog='mzmine_pipe.py',
                                      description='Use MZmine batch to process the given spectra.\
                                                   A batch file can be created via the MZmine GUI.')
    parser.add_argument('-mz',      '--mzmine_path',        required=False)
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
