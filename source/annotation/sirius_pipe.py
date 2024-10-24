#!/usr/bin/env python3

"""
Use Sirius to annotate compounds and extract matching formulae and chemical classes.
"""


# Imports
import os
import argparse
import warnings
import json

from os.path import join, basename
from tqdm.auto import tqdm
from tqdm.dask import TqdmCallback
import dask.multiprocessing


import source.helpers.general as helpers
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
    sirius_path     = args.sirius_path      if args.sirius_path else None
    in_dir          = args.in_dir
    out_dir         = args.out_dir          if args.out_dir else args.in_dir
    projectspace    = args.projectspace     if args.projectspace else out_dir
    config          = args.config           if args.config else None
    nested          = args.nested           if args.nested else False
    n_workers       = args.workers          if args.workers else 1
    save_log        = args.save_log         if args.save_log else False
    verbosity       = args.verbosity        if args.verbosity else 1
    additional_args = args.gnps_args        if args.gnps_args else unknown_args

    sirius_runner = Sirius_Runner( sirius_path=sirius_path, config=config, save_log=save_log, additional_args=additional_args, verbosity=verbosity )

    if nested:
        futures = sirius_runner.run_nested_sirius( in_root_dir=in_dir, out_root_dir=out_dir )
        computation_complete = helpers.compute_scheduled( futures=futures, num_workers=n_workers, verbose=verbosity >= 1)
    else:
        futures = sirius_runner.run_sirius( in_dir=in_dir, out_dir=out_dir, projectspace=projectspace )
    


class Sirius_Runner(Pipe_Step):
    """
    A runner for SIRIUS annotation.
    """
    def __init__( self, sirius_path:StrPath=None, config:StrPath=None, save_log:bool=False, additional_args:list=[], verbosity:int=1 ):
        """
        Initialize the GNPS_Runner.

        :param sirius_path: Path to SIRIUS executable
        :type sirius_path: StrPath
        :param config: Path to SIRIS configuration file or direct configuration string
        :type config: StrPath
        :param save_log: Whether to save the output(s).
        :type save_log: bool, optional
        :param additional_args: Additional arguments for mzmine, defaults to []
        :type additional_args: list, optional
        :param verbosity: Level of verbosity, defaults to 1
        :type verbosity: int, optional
        """
        super().__init__( patterns={"in": r"_sirius.mgf$"},
                          save_log=save_log, additional_args=additional_args, verbosity=verbosity)
        self.sirius_path = sirius_path if sirius_path else "sirius"
        if os.path.isfile(config):
            with open( config, "r") as config_file:
                config = config_file.read()
        config = config[6:] if config.startswith("config") else config
        self.config = config.strip()



    def run_sirius( self, in_path:StrPath, out_path:StrPath, projectspace:StrPath ) -> bool:
        """
        Run a single SIRIUS configuration.

        :param in_path: Path to in file
        :type in_path: StrPath
        :param out_path: Output directory
        :type out_path: StrPath
        :param out_path: Path to projectspace file / directory
        :type out_path: StrPath
        :return: Success of the command
        :rtype: bool
        """
        cmd = f'\"{self.sirius_path}\" config {self.config} --project {projectspace} --input {in_path}\
                 formulas zodiac fingerprints structures denovo-structures classes write-summaries --output {out_path}\
                {" ".join(self.additional_args)}'
              
        out, err = helpers.execute_verbose_command( cmd=cmd, verbosity=self.verbosity,
                                                    out_path=join(out_path, "sirius_log.txt") if self.save_log else None )
        
        self.processed_in.append( in_path )
        self.processed_out.append( out_path )
        self.outs.append( out )
        self.errs.append( err )


    def run_sirius_nested( self, in_root_dir:StrPath, out_root_dir:StrPath,
                           futures:list=[], recusion_level:int=0 ) -> list:
        """
        Run SIRIUS Pipeline in nested directories.

        :param in_root_dir: Root input directory
        :type in_root_dir: StrPath
        :param out_root_dir: Root output directory
        :type out_root_dir: StrPath
        :param futures: Future computations for parallelization, defaults to []
        :type futures: list, optional
        :param recusion_level: Current level of recursion, important for determination of level of verbose output, defaults to 0
        :type recusion_level: int, optional
        :return: Future computations
        :rtype: list
        """
        verbose_tqdm = self.verbosity >= recusion_level + 2
        for entry in tqdm( os.listdir(in_root_dir), disable=verbose_tqdm, desc="Schedule Sirius annotation" ):
            entry_path = join(in_root_dir, entry)

            if self.match_file_name( pattern=self.patterns["in"], file_name=entry ):
                futures.append( dask.delayed(self.run_sirius)( in_path=entry_path,
                                                               out_path=out_root_dir,
                                                               projectspace=out_root_dir ) )
            elif os.path.isdir( entry_path ):
                futures = self.run_sirius_nested( in_root_dir=entry_path,
                                                  out_root_dir=join( out_root_dir, entry ),
                                                  futures=futures, recusion_level=recusion_level+1)
        if futures:
            os.makedirs(out_root_dir, exist_ok=True)

        return futures



if __name__ == "__main__":
    parser = argparse.ArgumentParser( prog='sirius_pipe.py',
                                      description='Obtain anntations from MS1 & MS2 feature annotation by SIRIUS.')
    parser.add_argument('-si',      '--sirius_path',        required=False)
    parser.add_argument('-in',      '--in_dir',             required=True)
    parser.add_argument('-out',     '--out_dir',            required=False)
    parser.add_argument('-p',       '--projectspace',       required=True)
    parser.add_argument('-c',       '--config',             required=False)
    parser.add_argument('-n',       '--nested',             required=False,     action="store_true")
    parser.add_argument('-s',       '--save_log',           required=False,     action="store_true")
    parser.add_argument('-w',       '--workers',            required=False,     type=int)
    parser.add_argument('-v',       '--verbosity',          required=False,     type=int)
    parser.add_argument('-sirius',  '--sirius_args',        required=False,     nargs=argparse.REMAINDER)

    args, unknown_args = parser.parse_known_args()

    main(args=args, unknown_args=unknown_args)
