"""
Conversion of manufacturer MS files to .mzML or .mzXML format. The folder structure is mimiced at the place of the output.
"""

import os
import platform
import argparse

from tqdm import tqdm
import dask.multiprocessing


 
def main(args):
    """
    Execute the conversion.

    :param args: Command line arguments
    :type args: any
    """
    # Extract arguments
    in_dir = args.in_dir
    out_dir = args.out_dir
    overwrite = args.overwrite if args.overwrite else False
    n_workers = args.workers if args.workers else 1
    verbosity = args.verbosity if args.verbosity else 1
    
    # Conversion
    convert_files(root_folder=start, out_root_folder=join(start, "Out_msconv"), verbosity=0)


def convert_file(in_path:str, out_dir:str, format:str="mzML"):
    """
    Convert one file with msconvert.

    :param in_path: Path to scheduled file.
    :type in_path: str
    :param out_dir: Path to output directory.
    :type out_dir: str
    """
    format 

    os.system( f'msconvert --{format} --64 -o {out_dir} {in_path}' )

def convert_files(root_folder, out_root_folder, verbosity:int=0):
    """
    Converts multiple files in multiple folders, found in root_folder with msconvert and saves them
    to a location out_root_folder again into their respective folders.
    """
    # Outer loop over all files in root folder
    for entry in tqdm( listdir(root_folder) ):
        folder = join(root_folder, entry)

        if entry == "System Volume Information":
            continue
        # Conditions for selecting folder for conversion
        if os.path.isdir(folder) and listdir(folder) and listdir(folder)[0].endswith(".d"):          # When the first entry ends with .d in the folder, it is seen as having MS entries
            folder = join(root_folder, folder)    

            # Inner loop to convert all files in the folder
            dask.config.set(scheduler='processes', num_workers=workers)
            futures = []
            for file in listdir(folder):
                # Make a new folder in the out_root_folder with the same name as the folder with MS entries
                if not entry in list( listdir(out_root_folder)):
                    os.mkdir( join(out_root_folder, entry) )

                in_path = join(folder, file)
                out_folder = join(out_root_folder, entry)
                out_path = join(out_folder, f'{".".join(file.split(".")[:-1])}.mzXML')
                
            
                # Check for existing files at the path
                if (not os.path.isfile(out_path)) or os.path.getsize(out_path) < 1e8 :
                    futures.append(dask.delayed(convert_file)(in_path=in_path, out_folder=out_folder))
            dask.compute(futures)
                

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='raw_to_mzml.py',
                                description='Conversion of manufacturer MS files to .mzML or .mzXML format. The folder structure is mimiced at the place of the output.')
    parser.add_argument('-i', '--in_dir', required=True)
    parser.add_argument('-r', '--out_dir', required=True)
    parser.add_argument('-o', '--overwrite', action="store_true", required=False)
    parser.add_argument('-w', '--workers', type=int, required=False)
    parser.add_argument('-v', '--verbosity', type=int, required=False)

    
    args = parser.parse_args()
    main(args=args)
