#!/usr/bin/env python3

"""
Use mzmine for feature finding.
"""

# Imports
import os
import argparse

from os.path import join
from tqdm.auto import tqdm
from tqdm.dask import TqdmCallback
import dask.multiprocessing

from source.helpers.general import Substring, execute_verbose_command
from source.helpers.types import StrPath



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
    gnps_pipe       = args.gnps_pipe        if args.gnps_pipe else False
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

    if user:
        if user == "console":
            login = "-login-console"
        else:
            login = f"-user {user}"
    else:
        print("You did not provide a user. You will be prompted to login by mzmine.\
               For future use please find your user file under $USER/.mzmine/users/ after completing the login.")
        login = "-login"

    mzmine_runner = MZmine_runner( mzmine_path=mzmine_path, batch_path=batch_path, platform=platform, login=login,
                                   valid_formats=valid_formats, gnps_pipe=gnps_pipe,
                                   additional_args=additional_args, verbosity=verbosity)
    if nested:
        mzmine_runner.run_nested_mzmine_batches( root_dir=in_dir, out_root_dir=out_dir )
    else:
        mzmine_runner.run_mzmine_batch( in_path=in_dir, out_path=out_dir )


class MZmine_runner:
    """
    A runner for mzmine operations.
    """
    def __init__( self, mzmine_path:StrPath, batch_path:StrPath, platform:str, login:str="-login", valid_formats:list=["mzML", "mzXML", "imzML"],
                  gnps_pipe:bool=False, additional_args:list=[], verbosity:int=1):
        """
        Initialize the MZmine_runner.

        :param mzmine_path: Path to mzmine executable
        :type mzmine_path: StrPath
        :param batch_path: Path to mzmine batch file
        :type batch_path: StrPath
        :param platform: Operating system platform
        :type platform: str
        :param login: Login or user command, defaults to "-login"
        :type login: str, optional
        :param valid_formats: Formats to search for as valid endings, defaults to ["mzML", "mzXML", "imzML"]
        :type valid_formats: list, optional
        :param additional_args: Additional arguments for mzmine, defaults to []
        :type additional_args: list, optional
        :param verbosity: Level of verbosity, defaults to 1
        :type verbosity: int, optional
        """
        self.mzmine_path        = mzmine_path
        self.login              = login
        self.batch_path         = batch_path
        self.valid_formats      = valid_formats
        self.platform           = platform
        self.additional_args    = additional_args
        self.verbosity          = verbosity
        self.gnps_pipe          = gnps_pipe


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
        
        if self.gnps_pipe:
            cmd = f"{cmd} | "
        return execute_verbose_command( cmd=cmd, platform=self.platform, verbosity=self.verbosity,
                                        outpath=join(out_path, "out.txt") if self.gnps_pipe else None )


    def run_nested_mzmine_batches( self, root_dir:StrPath, out_root_dir:StrPath,
                                   futures:list=[], original:bool=True) -> list:
        """
        Run a mzmine batch on a nested structure

        :param root_dir: Root directory for descending the structure
        :type root_dir: StrPath
        :param out_root_dir: Root directory for output
        :type out_root_dir: StrPath
        :param futures: Open computations, defaults to []
        :type futures: list, optional
        :param original: Recursion instance is original or not, defaults to True
        :type original: bool, optional
        :return: Open computations from found valid files
        :rtype: list
        """
        verbose_tqdm = self.verbosity < 2 if original else self.verbosity < 3
        in_paths_file = join(out_root_dir, "source_files.txt")

        for root, dirs, files in os.walk(root_dir):
            found_files = [join(root_dir, file) for file in files if file.split(".")[-1] in self.valid_formats]
            
            if found_files:
                os.makedirs(out_root_dir, exist_ok=True)
                with open(in_paths_file , "w" ) as f:
                    f.write( "\n".join(found_files) )
                futures.append( dask.delayed(self.run_mzmine_batch)( in_path=in_paths_file, out_path=out_root_dir ) )

            for dir in tqdm(dirs, disable=verbose_tqdm, desc="Directories"):
                scheduled = self.run_nested_mzmine_batches( root_dir=join(root_dir, dir),
                                                            out_root_dir=join(out_root_dir, dir),
                                                            futures=futures, original=False )
                
                for i in range( len(scheduled) ): # I dont know why, but list comprehension loops endlessly if done by direct element aquisition
                    if scheduled[i] is not None:
                        futures.append( scheduled[i] )

            if original:
                dask.config.set(scheduler='processes', num_workers=1)
                if self.verbosity >= 1:
                    with TqdmCallback(desc="Compute"):
                        dask.compute(futures)
                else:
                    dask.compute(futures)
            
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
    parser.add_argument('-gnps',    '--gnps_pipe',          required=False)
    parser.add_argument('-v',       '--verbosity',          required=False,     type=int)
    parser.add_argument('-mzmine',  '--mzmine_arguments',   required=False,     nargs=argparse.REMAINDER)

    args, unknown_args = parser.parse_known_args()

    main(args=args, unknown_args=unknown_args)
