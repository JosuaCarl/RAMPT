#!/usr/bin/env python

"""
Conversion of manufacturer MS files to .mzML or .mzXMLtarget_format. The folder structure is mimiced at the place of the output.
"""
import os
import argparse
import regex

from os.path import join
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
    in_dir          = args.in_dir
    out_dir         = args.out_dir
    target_format   = args.target_format    if args.target_format else "mzML"
    pattern         = args.pattern          if args.pattern else r""
    suffix          = args.suffix           if args.suffix else None
    prefix          = args.prefix           if args.prefix else None
    contains        = args.contains         if args.contains else None
    redo_threshold  = args.redo_threshold   if args.redo_threshold else 1e8
    overwrite       = args.overwrite        if args.overwrite else False
    nested          = args.nested           if args.nested else False
    n_workers       = args.workers          if args.workers else 1
    save_log        = args.save_log         if args.save_log else False
    platform        = args.platform         if args.platform else "windows"
    verbosity       = args.verbosity        if args.verbosity else 1
    additional_args = args.msconv_arguments if args.msconv_arguments else unknown_args
    
    # Conversion
    file_converter = File_Converter( platform=platform, target_format=target_format,
                                     pattern=pattern, suffix=suffix, prefix=prefix, contains=contains, 
                                     redo_threshold=redo_threshold, overwrite=overwrite,
                                     save_log=save_log, additional_args=additional_args, verbosity=verbosity )
    if nested:
        futures = file_converter.convert_files_nested( in_root_dir=in_dir, out_root_dir=out_dir )
        computation_complete = helpers.compute_scheduled( futures=futures, num_workers=n_workers, verbose=verbosity >= 1)
    else:
        file_converter.convert_file( in_path=in_dir, out_path=out_dir )



class File_Converter(Pipe_Step):
    """
    General class for file conversion along matched patterns.
    """
    def __init__( self, platform:str="windows", target_format:str="mzML",
                  pattern:str=r"", suffix:str=None, prefix:str=None, contains:str=None,
                  redo_threshold:float=1e8, overwrite:bool=False,
                  save_log = False, additional_args = ..., verbosity = 1 ):
        """
        Initializes the file converter.

        :param platform: Operational system/platform of computation, defaults to "windows"
        :type platform: str, optional
        :param target_format: _description_, defaults to "mzML"
        :type target_format: str, optional
        :param pattern: Pattern for folder matching, defaults to ""
        :type pattern: str, optional
        :param suffix: Suffix for folder matching, defaults to None
        :type suffix: str, optional
        :param prefix: Prefix for folder matching, defaults to None
        :type prefix: str, optional
        :param contains: Contained strings for folder matching, defaults to None
        :type contains: str, optional
        :param redo_threshold: Threshold in bytess for a target file to be considered as incomplete and scheduled for re running the conversion, defaults to 1e8
        :type redo_threshold: float, optional
        :param overwrite: Overwrite all, do not check whether file already exists, defaults to False
        :type overwrite: bool, optional
        :param save_log: Whether to save the output(s).
        :type save_log: bool, optional
        :param additional_args: Additional arguments for mzmine, defaults to []
        :type additional_args: list, optional
        :param verbosity: Level of verbosity, defaults to 1
        :type verbosity: int, optional
        """
        super().__init__( patterns={"in": pattern}, save_log=save_log, additional_args=additional_args, verbosity=verbosity)
        if contains:
            self.patterns["in"] = rf"{pattern}.*{contains}.*"
        if suffix:
            self.patterns["in"] = rf"{pattern}.*{suffix}$"
        if prefix:
            self.patterns["in"] = rf"^{prefix}.*{pattern}"
        
        self.redo_threshold = redo_threshold
        self.overwrite      = overwrite
        self.platform       = platform
        self.target_format  = target_format



    def select_for_conversion( self, in_path:str, out_path:str ) -> bool:
        """
        Convert one file with msconvert.

        :param in_path: Path to scheduled file.
        :type in_path: str
        :param out_path: Path to output directory.
        :type out_path: str
        :return: Whether the file was converted
        :rtype: bool
        """
        # Check origin
        in_valid =  super().match_file_name( pattern=self.patterns["in"], file_name=in_path )
        # Check target
        out_valid = self.overwrite or ( not os.path.isfile(out_path) )       or \
                    os.path.getsize( out_path ) < float(self.redo_threshold) or \
                    not regex.search( "^</.*>$", helpers.open_last_line_with_content(filepath=out_path) )

        return in_valid, out_valid
            

    def convert_file( self, in_path:str, out_path:str ) -> bool:
        """
        Convert one file with msconvert.

        :param in_path: Path to scheduled file.
        :type in_path: str
        :param out_path: Path to output directory.
        :type out_path: str
        :return: Whether the file was converted
        :rtype: bool
        """
        target_format = self.target_format.replace(".", "")
        target_format = helpers.change_case_str(s=target_format, range=slice(2, len(target_format)), conversion="upper")

        cmd = f'msconvert --{target_format} --64 -o {out_path} {in_path} {" ".join(self.additional_args)}'

        out, err =  helpers.execute_verbose_command( cmd=cmd, verbosity=self.verbosity,
                                                     out_path=join(out_path, "msconv_log.txt") if self.save_log else None)
        self.processed_in.append( in_path )
        self.processed_out.append( out_path )
        self.outs.append( out )
        self.errs.append( err )


    def convert_files_nested( self, in_root_dir:StrPath, out_root_dir:StrPath,
                              futures:list=[], recusion_level:int=0 ) -> list:
        """
        Converts multiple files in multiple folders, found in in_root_dir with msconvert and saves them
        to a location out_root_dir again into their respective folders.

        :param in_root_dir: Starting folder for descent.
        :type in_root_dir: StrPath
        :param out_root_dir: Folder where structure is mimiced and files are converted to
        :type out_root_dir: StrPath
        :param futures: Future computations for parallelization, defaults to []
        :type futures: list, optional
        :param recusion_level: Current level of recursion, important for determination of level of verbose output, defaults to 0
        :type recusion_level: int, optional
        :return: List of future computations
        :rtype: list
        """
        verbose_tqdm = self.verbosity >= recusion_level + 2
        for entry in tqdm(os.listdir(in_root_dir), disable=verbose_tqdm, desc="Schedule conversions"):
            entry_path = join( in_root_dir, entry )
            out_path = join( out_root_dir, helpers.replace_file_ending( entry, self.target_format ) )
            in_valid, out_valid = self.select_for_conversion( in_path=entry_path, out_path=out_path)

            if in_valid and out_valid:
                futures.append( dask.delayed(self.convert_file)( in_path=entry_path, out_path=out_root_dir ) )
            elif os.path.isdir( entry_path ) and not in_valid:
                futures = self.convert_files_nested( in_root_dir=entry_path, out_root_dir=join(out_root_dir, entry),
                                                     futures=futures, recusion_level=recusion_level+1 )
            
        if futures:
            helpers.make_new_dir( out_root_dir )

        return futures



if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='msconv_pipe.py',
                                description='Conversion of manufacturer MS files to .mzML or .mzXML target_format.\
                                             The folder structure is mimiced at the place of the output.')
    parser.add_argument('-in',      '--in_dir',             required=True)
    parser.add_argument('-out',     '--out_dir',            required=True)
    parser.add_argument('-tf',      '--target_format',      required=False)
    parser.add_argument('-pat',     '--pattern',            required=False)
    parser.add_argument('-suf',     '--suffix',             required=False)
    parser.add_argument('-pre',     '--prefix',             required=False)
    parser.add_argument('-con',     '--contains',           required=False)
    parser.add_argument('-rt',      '--redo_threshold',     required=False)
    parser.add_argument('-o',       '--overwrite',          required=False,     action="store_true")
    parser.add_argument('-n',       '--nested',             required=False,     action="store_true")
    parser.add_argument('-w',       '--workers',            required=False,     type=int)
    parser.add_argument('-s',       '--save_log',           required=False,     action="store_true")
    parser.add_argument('-plat',    '--platform',           required=False)
    parser.add_argument('-v',       '--verbosity',          required=False,     type=int)
    parser.add_argument('-msconv',  '--msconv_arguments',   required=False,     nargs=argparse.REMAINDER)

    
    args, unknown_args = parser.parse_known_args()
    main(args=args, unknown_args=unknown_args)
