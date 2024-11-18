#!/usr/bin/env python3

"""
Use Sirius to annotate compounds and extract matching formulae and chemical classes.
"""


# Imports
import os
import argparse

from os.path import join
from tqdm.auto import tqdm
import dask.multiprocessing


import source.helpers.general as helpers
from source.helpers.types import StrPath
from source.helpers.classes import Pipe_Step, get_value, set_value


def main(args:argparse.Namespace|dict, unknown_args:list[str]=[]):
    """
    Execute the conversion.

    :param args: Command line arguments
    :type args: argparse.Namespace|dict
    :param unknown_args: Command line arguments that are not known.
    :type unknown_args: list[str]
    """
    # Extract arguments
    sirius_path     = get_value(args, "sirius_path", "sirius")
    in_dir          = get_value(args, "in_dir")
    out_dir         = get_value(args, "out_dir",        in_dir)
    projectspace    = get_value(args, "projectspace",   out_dir)
    config          = get_value(args, "config",         None)
    nested          = get_value(args, "nested",         False)
    n_workers       = get_value(args, "workers",        1)
    save_log        = get_value(args, "save_log",       False)
    verbosity       = get_value(args, "verbosity",      1)
    additional_args = get_value(args, "sirius_args",    unknown_args)
    additional_args = additional_args if additional_args else unknown_args

    sirius_runner = Sirius_Runner( sirius_path=sirius_path, config=config, save_log=save_log,
                                   additional_args=additional_args, verbosity=verbosity,
                                   nested=nested, workers=n_workers,
                                   scheduled_in=in_dir, scheduled_out=out_dir )
    sirius_runner.run( projectspace=projectspace)

    return sirius_runner.processed_out
    
    


class Sirius_Runner(Pipe_Step):
    """
    A runner for SIRIUS annotation.
    """
    def __init__( self, sirius_path:StrPath="sirius", config:StrPath="config.txt",
                  save_log:bool=False, additional_args:list=[], verbosity:int=1, **kwargs ):
        """
        Initialize the GNPS_Runner.

        :param sirius_path: Path to SIRIUS executable, defaults to "sirius"
        :type sirius_path: StrPath
        :param config: Path to SIRIS configuration file or direct configuration string, defaults to "config.txt"
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
        if kwargs:
            self.update(kwargs)
        self.sirius_path = sirius_path if sirius_path else "sirius"
        if os.path.isfile(config):
            with open( config, "r") as config_file:
                config = config_file.read()
        config = config[6:] if config.startswith("config") else config
        self.config = config.strip()


    def compute( self, in_path:StrPath, out_path:StrPath, projectspace:StrPath=None ) -> bool:
        """
        Run a single SIRIUS configuration.

        :param in_path: Path to in file
        :type in_path: StrPath
        :param out_path: Output directory
        :type out_path: StrPath
        :param projectspace: Path to projectspace file / directory, defaults to out_path
        :type projectspace: StrPath
        :return: Success of the command
        :rtype: bool
        """
        projectspace = projectspace if projectspace is not None else out_path
        cmd = rf'"{self.sirius_path}" --project {join(projectspace, "projectspace")} --input {in_path} config {self.config} write-summaries --output {out_path} {" ".join(self.additional_args)}'
              
        out, err = helpers.execute_verbose_command( cmd=cmd, verbosity=self.verbosity,
                                                    out_path=join(out_path, "sirius_log.txt") if self.save_log else None,
                                                    decode_text=False )
        
        self.processed_in.append( in_path )
        self.processed_out.append( out_path )
        self.outs.append( out )
        self.errs.append( err )

        return out_path


    def compute_nested( self, in_root_dir:StrPath, out_root_dir:StrPath,
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
                futures.append( dask.delayed(self.compute)( in_path=entry_path,
                                                               out_path=out_root_dir ) )
            elif os.path.isdir( entry_path ):
                futures = self.compute_nested( in_root_dir=entry_path,
                                                  out_root_dir=join( out_root_dir, entry ),
                                                  futures=futures, recusion_level=recusion_level+1)
        if futures:
            os.makedirs(out_root_dir, exist_ok=True)

        return futures


    def run(self, projectspace:StrPath=None):
        return super().run( projectspace=projectspace)

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
