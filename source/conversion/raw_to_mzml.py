#!/usr/bin/env python

"""
Conversion of manufacturer MS files to .mzML or .mzXML format. The folder structure is mimiced at the place of the output.
"""
import os
import argparse

from os import listdir
from os.path import join
from tqdm.auto import tqdm
from tqdm.dask import TqdmCallback
import dask.multiprocessing

from source.helpers.general import change_case_str
from source.helpers.types import StrPath


def main(args):
    """
    Execute the conversion.

    :param args: Command line arguments
    :type args: any
    """
    # Extract arguments
    in_dir      = args.in_dir
    out_dir     = args.out_dir
    format      = args.format       if args.format else "mzML"
    suffix      = args.suffix       if args.suffix else None
    prefix      = args.prefix       if args.prefix else None
    contains    = args.contains     if args.contains else None
    overwrite   = args.overwrite    if args.overwrite else False
    n_workers   = args.workers      if args.workers else 1
    platform    = args.platform     if args.platform else "windows"
    verbosity   = args.verbosity    if args.verbosity else 1
    
    # Conversion
    convert_files( root_folder=in_dir, out_root_folder=join( out_dir ),
                   suffix=suffix, prefix=prefix, contains=contains, 
                   format=format, n_workers=n_workers, overwrite=overwrite,
                   platform=platform, verbosity=verbosity )



def convert_file(in_path:str, out_folder:str, format:str="mzML", platform:str="windows", verbosity:int=0):
    """
    Convert one file with msconvert.

    :param in_path: Path to scheduled file.
    :type in_path: str
    :param out_dir: Path to output directory.
    :type out_dir: str
    :param format: Format for conversion.
    :type out_dir: str
    :param platform: platform on which operated, defaults to windows
    :type platform: str, optional
    :param verbosity: Verbosity, defaults to 0
    :type verbosity: int, optional
    """
    format = format.replace(".", "")
    format = change_case_str(s=format, range=slice(2, len(format)), conversion="upper")
    if verbosity >= 2:
        os.system( f'msconvert --{format} --64 -o {out_folder} {in_path}')
    elif platform.lower() == "windows":
        os.system( f'msconvert --{format} --64 -o {out_folder} {in_path} > nul')
    else:
        os.system( f'msconvert --{format} --64 -o {out_folder} {in_path} > /dev/null')


def convert_files(root_folder:StrPath, out_root_folder:StrPath,
                  suffix:str=None, prefix:str=None, contains:str=None,
                  format:str="mzML", n_workers=1, overwrite:bool=False,
                  platform:str="windows", verbosity:int=0):
    """
    Converts multiple files in multiple folders, found in root_folder with msconvert and saves them
    to a location out_root_folder again into their respective folders.

    :param root_folder: Starting folder for descent.
    :type root_folder: StrPath
    :param out_root_folder: Folder where structure is mimiced and files are converted to.
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
    :param overwrite: Overwrite all, do not check whether file already exists, defaults to False
    :type overwrite: bool, optional
    :param platform: platform on which operated, defaults to windows
    :type platform: str, optional
    :param verbosity: Verbosity, defaults to 0
    :type verbosity: int, optional
    """
    # Outer loop over all files in root folder
    for entry in listdir(root_folder):

        folder = join(root_folder, entry)

        if entry == "System Volume Information":
            continue

        # Conditions for selecting folder for conversion
        if os.path.isdir(folder) and \
           (not suffix or listdir(folder)[0].endswith(suffix)) and \
           (not prefix or listdir(folder)[0].startswith(prefix)) and \
           (not contains or contains in listdir(folder)[0]):
            
            folder = join(root_folder, folder)    

            # Inner loop to convert all files in the folder
            dask.config.set(scheduler='processes', num_workers=n_workers)
            futures = []
            for file in listdir(folder):

                # Make a new folder in the out_root_folder with the same name as the folder with MS entries
                if not entry in list( listdir(out_root_folder) ):
                    os.mkdir( join(out_root_folder, entry) )

                in_path = join( folder, file )
                out_folder = join( out_root_folder, entry )
                out_path = join( out_folder, f'{".".join(file.split(".")[:-1])}.{format}' )
                
            
                # Check whether overwrite is set orfor existing files at the path
                if overwrite or \
                   ( not os.path.isfile(out_path) ) or \
                   os.path.getsize( out_path ) < 1e8 :
                    futures.append( dask.delayed(convert_file)(in_path=in_path, out_folder=out_folder, 
                                                               platform=platform, format=format,
                                                               verbosity=verbosity) )
            if verbosity >=1:
                with TqdmCallback(desc="compute"):
                    dask.compute(futures)
            else:
                dask.compute(futures)  



if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='raw_to_mzml.py',
                                description='Conversion of manufacturer MS files to .mzML or .mzXML format. The folder structure is mimiced at the place of the output.')
    parser.add_argument('-in',  '--in_dir',     required=True)
    parser.add_argument('-out', '--out_dir',    required=True)
    parser.add_argument('-f',   '--format',     required=False)
    parser.add_argument('-s',   '--suffix',     required=False)
    parser.add_argument('-p',   '--prefix',     required=False)
    parser.add_argument('-c',   '--contains',   required=False)
    parser.add_argument('-o',   '--overwrite',  required=False,     action="store_true")
    parser.add_argument('-w',   '--workers',    required=False,     type=int)
    parser.add_argument('-plat', '--platform',  required=False)
    parser.add_argument('-v',   '--verbosity',  required=False,     type=int)

    
    args = parser.parse_args()
    main(args=args)
