#!/usr/bin/env python3

"""
Use Sirius to annotate compounds and extract matching formulae and chemical classes.
"""


# Imports
import os
import argparse

from os.path import join
from tqdm.auto import tqdm

from source.helpers.types import StrPath

from source.steps.general import Pipe_Step, get_value


def main(args:argparse.Namespace|dict, unknown_args:list[str]=[]):
    """
    Execute the conversion.

    :param args: Command line arguments
    :type args: argparse.Namespace|dict
    :param unknown_args: Command line arguments that are not known.
    :type unknown_args: list[str]
    """
    # Extract arguments
    exec_path       = get_value(args, "exec_path", "sirius")
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

    sirius_runner = Sirius_Runner( exec_path=exec_path, config=config, save_log=save_log,
                                   additional_args=additional_args, verbosity=verbosity,
                                   nested=nested, workers=n_workers,
                                   scheduled_in=in_dir, scheduled_out=out_dir )
    return sirius_runner.run( projectspace=projectspace)
    
    

class Sirius_Runner(Pipe_Step):
    """
    A runner for SIRIUS annotation.
    """
    def __init__( self, exec_path:StrPath="sirius", config:StrPath="", projectspace:StrPath=None,
                  save_log:bool=False, additional_args:list=[], verbosity:int=1, **kwargs ):
        """
        Initialize the GNPS_Runner.

        :param exec_path: Path to SIRIUS executable, defaults to "sirius"
        :type exec_path: StrPath
        :param config: Path to SIRIS configuration file or direct configuration string, defaults to "config.txt"
        :type config: StrPath
        :param projectspace: Path to SIRIUS projectspace, defaults to None
        :type projectspace: StrPath
        :param save_log: Whether to save the output(s).
        :type save_log: bool, optional
        :param additional_args: Additional arguments for mzmine, defaults to []
        :type additional_args: list, optional
        :param verbosity: Level of verbosity, defaults to 1
        :type verbosity: int, optional
        """
        super().__init__( name="sirius", patterns={"in": r"_sirius.mgf$"},
                          save_log=save_log, additional_args=additional_args, verbosity=verbosity)
        if kwargs:
            self.update(kwargs)
        self.exec_path = exec_path if exec_path else "sirius"
        self.config = self.extract_config(config)
        self.projectspace = projectspace

    
    
    def extract_config( self, config:StrPath ):
        if os.path.isdir(config):
            if os.path.isfile( join(config, "sirius_config.txt") ):
                config = join(config, "sirius_config.txt")
            else:
                raise(ValueError(f"{config} directory does not contain sirius_config.txt"))
        if os.path.isfile(config):
            with open( config, "r" ) as config_file:
                config = config_file.read()
            config = config[6:] if config.startswith("config") else config
        return config.strip()


    def run_single( self, in_path:StrPath, out_path:StrPath, projectspace:StrPath=None, config:StrPath=None ) -> bool:
        """
        Run a single SIRIUS configuration.

        :param in_path: Path to in file
        :type in_path: StrPath
        :param out_path: Output directory
        :type out_path: StrPath
        :param projectspace: Path to projectspace file / directory, defaults to out_path
        :type projectspace: StrPath
        :param config: Path to configuration file / directory or configuration as string, defaults to None
        :type config: StrPath, optional
        :return: Success of the command
        :rtype: bool
        """
        if projectspace is None:
            projectspace = self.projectspace if self.projectspace else out_path
        if config is None:
            config = self.config
        config = self.extract_config( config=config )

        cmd = rf'"{self.exec_path}" --project {join(projectspace, "projectspace")} --input {in_path} config {config} write-summaries --output {out_path} {" ".join(self.additional_args)}'
        
        super().compute( cmd=cmd, in_path=in_path, out_path=out_path, results=None, log_path=None, decode_text=False )


    def run_directory( self, in_path:StrPath, out_path:StrPath, projectspace:StrPath=None, config:str=None  ):
        """
        Compute a sirius run on a folder. When no config is defined, it will search in the folder for config.txt.

        :param in_dir: Path to in folder
        :type in_dir: StrPath
        :param out_dir: Output directory
        :type out_dir: StrPath
        :param projectspace: Path to projectspace file / directory, defaults to out_path
        :type projectspace: StrPath
        :param config: Configuration (file), defaults to None
        :type config: StrPath, optional
        """
        if config is None and self.config is None:
            for entry in os.listdir(in_path):
                if self.match_file_name( pattern=r"config\.txt$", file_name=entry):
                    config = join(in_path, entry)

        for entry in os.listdir(in_path):
            if self.match_file_name( pattern=self.patterns["in"], file_name=entry ):
                self.run_single( in_path=join(in_path, entry), out_path=out_path, projectspace=projectspace, config=config )


    def run_nested( self, in_root_dir:StrPath, out_root_dir:StrPath, recusion_level:int=0 ):
        """
        Run SIRIUS Pipeline in nested directories.

        :param in_root_dir: Root input directory
        :type in_root_dir: StrPath
        :param out_root_dir: Root output directory
        :type out_root_dir: StrPath
        :param recusion_level: Current level of recursion, important for determination of level of verbose output, defaults to 0
        :type recusion_level: int, optional
        """
        verbose_tqdm = self.verbosity >= recusion_level + 2
        made_out_root_dir = False
        
        for entry in tqdm( os.listdir(in_root_dir), disable=verbose_tqdm, desc="Schedule Sirius annotation" ):
            entry_path = join(in_root_dir, entry)

            if self.match_file_name( pattern=self.patterns["in"], file_name=entry ):
                if not made_out_root_dir:
                    os.makedirs( out_root_dir, exist_ok=True )
                    made_out_root_dir = True
                self.run_single( in_path=entry_path, out_path=out_root_dir )
            elif os.path.isdir( entry_path ):
                self.run_nested( in_root_dir=entry_path,
                                 out_root_dir=join( out_root_dir, entry ),
                                 recusion_level=recusion_level+1 )



    def run(self, in_paths:list=[], out_paths:list=[], projectspace:StrPath=None, **kwargs ):
        return super().run( in_paths=in_paths, out_paths=out_paths, projectspace=projectspace, **kwargs )



if __name__ == "__main__":
    parser = argparse.ArgumentParser( prog='sirius_pipe.py',
                                      description='Obtain anntations from MS1 & MS2 feature annotation by SIRIUS.')
    parser.add_argument('-si',      '--exec_path',          required=False)
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
