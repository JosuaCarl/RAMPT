#!/usr/bin/env python

"""
Conversion of manufacturer MS files to .mzML or .mzXML format. The folder structure is mimiced at the place of the output.
"""
import os
import argparse
import regex

from os.path import join
from tqdm.auto import tqdm
from tqdm.dask import TqdmCallback
import dask.multiprocessing

from source.helpers.general import change_case_str, open_last_line_with_content, make_new_dir, execute_verbose_command
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
    in_dir          = args.in_dir
    out_dir         = args.out_dir
    format          = args.format           if args.format else "mzML"
    suffix          = args.suffix           if args.suffix else None
    prefix          = args.prefix           if args.prefix else None
    contains        = args.contains         if args.contains else None
    redo_threshold  = args.redo_threshold   if args.redo_threshold else 1e8
    overwrite       = args.overwrite        if args.overwrite else False
    n_workers       = args.workers          if args.workers else 1
    platform        = args.platform         if args.platform else "windows"
    verbosity       = args.verbosity        if args.verbosity else 1
    additional_args = args.msconv_arguments if args.msconv_arguments else unknown_args
    
    # Conversion
    convert_files( root_folder=in_dir, out_root_folder=join( out_dir ),
                   suffix=suffix, prefix=prefix, contains=contains, 
                   format=format, n_workers=n_workers, 
                   redo_threshold=redo_threshold, overwrite=overwrite,
                   additional_args=additional_args,
                   platform=platform, verbosity=verbosity )



def check_entry(  in_path:str, out_path:str,
                  suffix:str=None, prefix:str=None, contains:str=None,
                  redo_threshold:float=1e8, overwrite:bool=False) -> bool:
    """
    Convert one file with msconvert.

    :param in_path: Path to scheduled file.
    :type in_path: str
    :param out_path: Path to output directory.
    :type out_path: str
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
    :return: Whether the file was converted
    :rtype: bool
    """
    # Check origin
    origin_valid = (not suffix or in_path.endswith(suffix)) and \
                   (not prefix or in_path.startswith(prefix)) and \
                   (not contains or contains in in_path)
    # Check target
    target_valid = overwrite or ( not os.path.isfile(out_path) ) or \
                   os.path.getsize( out_path ) < float(redo_threshold) or \
                   not regex.search( "^</.*>$", open_last_line_with_content(filepath=out_path) )

    return origin_valid, target_valid
        

def convert_file( in_path:str, out_path:str,
                  format:str="mzML",
                  additional_args:list=[],
                  platform:str="windows", verbosity:int=0) -> bool:
    """
    Convert one file with msconvert.

    :param in_path: Path to scheduled file.
    :type in_path: str
    :param out_path: Path to output directory.
    :type out_path: str
    :param format: Format for conversion.
    :type format: str
    :param additional_args: Additional arguments for msconvert, defaults to []
    :type additional_args: list, optional
    :param platform: platform on which operated, defaults to windows
    :type platform: str, optional
    :param verbosity: Verbosity, defaults to 0
    :type verbosity: int, optional
    :return: Whether the file was converted
    :rtype: bool
    """
    format = format.replace(".", "")
    format = change_case_str(s=format, range=slice(2, len(format)), conversion="upper")

    cmd = f'msconvert --{format} --64 -o {out_path} {in_path} {" ".join(additional_args)}'

    return execute_verbose_command(cmd=cmd, platform=platform, verbosity=verbosity)



def convert_files(root_folder:StrPath, out_root_folder:StrPath,
                  suffix:str=None, prefix:str=None, contains:str=None,
                  format:str="mzML", n_workers=1,
                  redo_threshold:float=1e8, overwrite:bool=False,
                  additional_args:list=[],
                  platform:str="windows", verbosity:int=0,
                  futures:list=[], original:bool=True) -> list:
    """
    Converts multiple files in multiple folders, found in root_folder with msconvert and saves them
    to a location out_root_folder again into their respective folders.

    :param root_folder: Starting folder for descent.
    :type root_folder: StrPath
    :param out_root_folder: Folder where structure is mimiced and files are converted to
    :type out_root_folder: StrPath
    :param suffix: Suffix for folder matching, defaults to None
    :type suffix: str, optional
    :param prefix: Prefix for folder matching, defaults to None
    :type prefix: str, optional
    :param contains: Contained strings for folder matching, defaults to None
    :type contains: str, optional
    :param format: Target format, defaults to "mzML"
    :type format: str, optional
    :param n_workers: Number of workers, defaults to 1
    :type n_workers: int, optional
    :param redo_threshold: Threshold in bytess for a target file to be considered as incomplete and scheduled for re running the conversion, defaults to 1e8
    :type redo_threshold: float, optional
    :param overwrite: Overwrite all, do not check whether file already exists, defaults to False
    :type overwrite: bool, optional
    :param additional_args: Additional arguments for msconvert, defaults to []
    :type additional_args: list, optional
    :param platform: platform on which operated, defaults to windows
    :type platform: str, optional
    :param verbosity: Verbosity, defaults to 0
    :type verbosity: int, optional
    :return: List of future computations
    :rtype: list
    """
    # Outer loop over all files in root folder
    verbose_tqdm = verbosity < 2 if original else verbosity < 3
    for root, dirs, files in os.walk(root_folder):
        for dir in tqdm(dirs, disable=verbose_tqdm, desc="Directories"):
            origin_valid, target_valid = check_entry( in_path=join( root_folder, dir ),
                                                      out_path=join( out_root_folder, f'{".".join(dir.split(".")[:-1])}.{format}' ),
                                                      suffix=suffix, prefix=prefix, contains=contains,
                                                      redo_threshold=redo_threshold, overwrite=overwrite )
            if origin_valid and target_valid:
                futures.append( dask.delayed(convert_file)( in_path=join( root_folder, dir ),
                                                            out_path=join( out_root_folder ), 
                                                            format=format, additional_args=additional_args,
                                                            platform=platform, verbosity=verbosity ) )
            elif not origin_valid:
                scheduled = convert_files( root_folder=join(root_folder, dir), out_root_folder=join(out_root_folder, dir),
                                           suffix=suffix, prefix=prefix, contains=contains,
                                           format=format, n_workers=n_workers,
                                           redo_threshold=redo_threshold, overwrite=overwrite,
                                           additional_args=additional_args,
                                           platform=platform, verbosity=verbosity,
                                           futures=futures, original=False )
                for i in range( len(scheduled) ): # I dont know why, but list comprehension loops endlessly if done by direct element aquisition
                    if scheduled[i] is not None:
                        futures.append( scheduled[i] ) 

        for file in tqdm(files, disable=verbose_tqdm, desc="Files"):
            origin_valid, target_valid = check_entry( in_path=join( root_folder, file ),
                                                      out_path=join( out_root_folder, f'{".".join(file.split(".")[:-1])}.{format}' ),
                                                      suffix=suffix, prefix=prefix, contains=contains,
                                                      redo_threshold=redo_threshold, overwrite=overwrite )
            if origin_valid and target_valid:
                futures.append( dask.delayed(convert_file)( in_path=join( root_folder, file ),
                                                            out_path=join( out_root_folder ),
                                                            format=format, additional_args=additional_args,
                                                            platform=platform, verbosity=verbosity ) )
                
        if futures and os.path.isdir(root_folder):
            make_new_dir( join(out_root_folder, root) )
            
        if original:
            dask.config.set(scheduler='processes', num_workers=n_workers)
            if verbosity >= 1:
                with TqdmCallback(desc="Compute"):
                    dask.compute(futures)
            else:
                dask.compute(futures)
        
        return futures



if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='raw_to_mzml.py',
                                description='Conversion of manufacturer MS files to .mzML or .mzXML format.\
                                             The folder structure is mimiced at the place of the output.')
    parser.add_argument('-in',      '--in_dir',             required=True)
    parser.add_argument('-out',     '--out_dir',            required=True)
    parser.add_argument('-f',       '--format',             required=False)
    parser.add_argument('-s',       '--suffix',             required=False)
    parser.add_argument('-p',       '--prefix',             required=False)
    parser.add_argument('-c',       '--contains',           required=False)
    parser.add_argument('-rt',      '--redo_threshold',     required=False)
    parser.add_argument('-o',       '--overwrite',          required=False,     action="store_true")
    parser.add_argument('-w',       '--workers',            required=False,     type=int)
    parser.add_argument('-plat',    '--platform',           required=False)
    parser.add_argument('-v',       '--verbosity',          required=False,     type=int)
    parser.add_argument('-msconv',  '--msconv_arguments',   required=False,     nargs=argparse.REMAINDER)

    
    args, unknown_args = parser.parse_known_args()
    main(args=args, unknown_args=unknown_args)
