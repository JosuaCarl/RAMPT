#!/usr/bin/env python3

"""
Use Sirius to annotate compounds and extract matching formulae and chemical classes.
"""


# Imports
import os
import gc
from tqdm import tqdm
import argparse
import dask
from typing import Union, Sequence, Optional, List
from os.path import join, basename

import pyopenms as oms
import numpy as np
import pandas as pd

from source.helpers.types import StrPath
from source.helpers.classes import Pipe_Step
import source.helpers.general as helpers


def main(args, unknown_args):
    """
    Execute the conversion.

    :param args: Command line arguments
    :type args: any
    :param unknown_args: Command line arguments that are not known.
    :type unknown_args: any
    """    
    # Extract arguments
    in_dir              = args.in_dir
    out_dir             = args.out_dir              if args.out_dir else args.in_dir
    data_dir            = args.data_dir             if args.data_dir else out_dir
    relative_tolerance  = args.relative_tolerance   if args.relative_tolerance else 1e-05
    absolute_tolerance  = args.absolute_tolerance   if args.absolute_tolerance else 1e-08
    nested              = args.nested               if args.nested else False
    n_workers           = args.workers              if args.workers else 1
    save_log            = args.save_log             if args.save_log else False
    verbosity           = args.verbosity            if args.verbosity else 1
    additional_args     = args.ion_exclusion_args   if args.ion_exclusion_args else unknown_args

    ion_exclusion_runner = Ion_exclusion_Runner( relative_tolerance=relative_tolerance, absolute_tolerance=absolute_tolerance,
                                                 save_log=save_log, additional_args=additional_args, verbosity=verbosity )

    if nested:
        futures = ion_exclusion_runner.check_ms2_presences_nested( in_root_dir=in_dir, out_root_dir=out_dir, data_root_dir=data_dir )
        computation_complete = helpers.compute_scheduled( futures=futures, num_workers=n_workers, verbose=verbosity >= 1)
    else:
        futures = ion_exclusion_runner.check_ms2_presence( in_dir=in_dir, out_dir=out_dir, data_dir=data_dir )



class OpenMS_File_Handler:
    def check_ending_experiment( self, file:StrPath ) -> bool:
        """
        Check whether the file has a mzML or mzXML ending.

        :param file: Path to file
        :type file: StrPath
        :return: Ending is mzML or mzXML
        :rtype: bool
        """    
        return file.endswith(".mzML") or file.endswith(".MzML") or file.endswith(".mzXML") or file.endswith(".MzXML")



    def read_experiment( self, experiment_path:StrPath, separator:str="\t") -> oms.MSExperiment:
        """
        Read in MzXML or MzML File as a pyopenms experiment. If the file is in tabular format,
        assumes that is is in long form with two columns ["mz", "inty"]

        :param experiment_path: Path to experiment
        :type experiment_path: StrPath
        :param separator: Separator of data, defaults to "\t"
        :type separator: str, optional
        :raises ValueError: The experiment must end with a valid ending.
        :return: Experiment
        :rtype: pyopenms.MSExperiment
        """    
        experiment = oms.MSExperiment()
        if experiment_path.endswith(".mzML") or experiment_path.endswith(".MzML"):
            file = oms.MzMLFile()
            file.load(experiment_path, experiment)
        elif experiment_path.endswith(".mzXML") or experiment_path.endswith(".MzXML"):
            file = oms.MzXMLFile()
            file.load(experiment_path, experiment)
        elif experiment_path.endswith(".tsv") or experiment_path.endswith(".csv") or experiment_path.endswith(".txt"):
            exp_df = pd.read_csv(experiment_path, sep=separator)
            spectrum = oms.MSSpectrum()
            spectrum.set_peaks( (exp_df["mz"], exp_df["inty"]) ) # type: ignore
            experiment.addSpectrum(spectrum)
        else: 
            raise ValueError(f'Invalid ending of {experiment_path}. Must be in [".MzXML", ".mzXML", ".MzML", ".mzML", ".tsv", ".csv", ".txt"]')
        return experiment



    def load_experiment( self, experiment:Union[oms.MSExperiment, StrPath], separator:str="\t" ) -> oms.MSExperiment:
        """
        If no experiment is given, loads and returns it from either .mzML or .mzXML file.
        Collects garbage with gc.collect() to ensure space in the RAM.

        :param experiment: Experiment, or Path to experiment
        :type experiment: Union[oms.MSExperiment, StrPath]
        :param separator: Separator of data, defaults to "\t"
        :type separator: str, optional
        :return: Experiment
        :rtype: pyopenms.MSExperiment
        """
        gc.collect()
        if isinstance(experiment, oms.MSExperiment):
            return experiment
        else:
            return self.read_experiment(experiment, separator=separator)
        

    def load_experiments( self, experiments:Union[Sequence[Union[oms.MSExperiment,StrPath]], StrPath], file_ending:Optional[str]=None,
                          separator:str="\t", data_load:bool=True) -> Sequence[Union[oms.MSExperiment, StrPath]]:
        """
        Load a batch of experiments.

        :param experiments: Experiments, either described by a list of paths or one path as base directory,
        or an existing experiment.
        :type experiments: Union[Sequence[Union[oms.MSExperiment,str]], str]
        :param file_ending: Ending of experiment file, defaults to None
        :type file_ending: Optional[str], optional
        :param separator: Separator of data, defaults to "\t"
        :type separator: str, optional
        :param data_load: Load the data or just combine the base string to a list of full filepaths, defaults to True
        :type data_load: bool, optional
        :return: Experiments
        :rtype: Sequence[Union[oms.MSExperiment,str]]
        """
        if isinstance(experiments, str):
            if file_ending:
                experiments = [os.path.join(experiments, file) for file in os.listdir(experiments) if file.endswith(file_ending)]
            else:
                experiments = [os.path.join(experiments, file) for file in os.listdir(experiments) if self.check_ending_experiment(file)]
        if data_load:
            experiments = [self.load_experiment(experiment, separator=separator) for experiment in tqdm(experiments)]
        return experiments
    


    def load_name( self, experiment:Union[oms.MSExperiment, str], alt_name:Optional[str]=None, file_ending:Optional[str]=None ) -> str:
        """
        Load the name of an experiment.

        :param experiment: Experiment
        :type experiment: Union[oms.MSExperiment, str]
        :param alt_name: Alternative Name if none is found, defaults to None
        :type alt_name: Optional[str], optional
        :param file_ending: Ending of experiment file, defaults to None
        :type file_ending: Optional[str], optional
        :raises ValueError: Raises error if no file name is found and no alt_name is given.
        :return: Name of experiment or alternative name
        :rtype: str
        """    
        if isinstance(experiment, str):
            return "".join(experiment.split(".")[:-1])
        else:
            if experiment.getLoadedFilePath():
                return "".join(os.path.basename(experiment.getLoadedFilePath()).split(".")[:-1])
            elif alt_name:
                return alt_name
            else:
                raise ValueError(f"No file path found in experiment. Please provide alt_name.")


    def load_names_batch( self, experiments:Union[Sequence[Union[oms.MSExperiment,str]], str], file_ending:str=".mzML") -> List[str]:
        """
        If no experiment is given, loads and returns it from either .mzML or .mzXML file.

        :param experiments: Experiments
        :type experiments: Union[Sequence[Union[oms.MSExperiment,str]], str]
        :param file_ending: Ending of experiment file, defaults to ".mzML"
        :type file_ending: str, optional
        :return: List of experiment names
        :rtype: List[str]
        """    
        if isinstance(experiments, str):
            if file_ending:
                return [self.load_name(file) for file in tqdm(os.listdir(experiments)) if file.endswith(file_ending)]
            else:
                return [self.load_name(file) for file in tqdm(os.listdir(experiments)) if self.check_ending_experiment(file)]
        else:
            if isinstance(experiments[0], str):
                return [self.load_name(experiment) for experiment in tqdm(experiments)] 
            else:
                return [self.load_name(experiment, str(i)) for i, experiment in enumerate(tqdm(experiments))]
    


    def load_experiments_df( self, data_dir:str, file_ending:str, separator:str="\t", data_load:bool=True, table_backend=pd) -> pd.DataFrame:
        """
        Load a Flow injection analysis dataframe, defining important properties.

        :param data_dir: Data directorsy
        :type data_dir: str
        :param file_ending: Ending of file
        :type file_ending: str
        :param separator: Separator for file, defaults to "\t"
        :type separator: str, optional
        :param data_load: Load data or only return list of experiments, defaults to True
        :type data_load: bool, optional
        :param table_backend: Use pandas or polars as backend, defaults to pd
        :type table_backend: _type_, optional
        :return: _description_
        :rtype: Union[pandas.DataFrame]
        """    
        print("Loading names:")
        names = self.load_names_batch(data_dir, file_ending)
        samples = [name.split("_")[:-1] for name in names]
        polarities = [{"pos": 1, "neg": -1}.get(name.split("_")[-1]) for name in names]
        print("Loading experiments:")
        experiments = self.load_experiments(data_dir, file_ending, separator=separator, data_load=data_load)
        fia_df = table_backend.DataFrame([samples, polarities, experiments])
        fia_df = fia_df.transpose()
        fia_df.columns = ["sample", "polarity", "experiment"]
        return fia_df

    


class Ion_exclusion_Runner(Pipe_Step):
    """
    Select abundant MS2 fragmented m/z for exclusion.
    """
    def __init__( self, relative_tolerance:float|int=1e-5, absolute_tolerance:float=5e-3, save_log:bool=False, additional_args:list=[], verbosity:int=1 ):
        super().__init__( save_log=save_log, additional_args=additional_args, verbosity=verbosity )
        self.relative_tolerance = relative_tolerance if isinstance(relative_tolerance, float) else relative_tolerance * 1e-6
        self.absolute_tolerance = absolute_tolerance
        self.file_handler       = OpenMS_File_Handler()



    def check_ms2_presence( self, in_dir:StrPath, out_dir:StrPath, data_dir:StrPath, annotation_file:StrPath=None ):
        experiments = self.file_handler.load_experiments_df( data_dir, file_ending=".mzML")
    
        ms2_in_files = {}
        for i, row in experiments.iterrows():
            experiment = row["experiment"]
            ms2_spectra = [ spectrum for spectrum in experiment.getSpectra() if spectrum.getMSLevel() >= 2 ]
            precursor_mzs = list( set( [ precursor.getMZ() for ms2_spectrum in ms2_spectra for precursor in ms2_spectrum.getPrecursors() ] ) )
            ms2_in_files[basename(experiment.getLoadedFilePath())] = precursor_mzs

        quantification_df  = pd.read_csv(f"{join(in_dir, basename(in_dir))}_iimn_fbmn_quant.csv")
        mz_in_ms2 = {}
        for file_name, ms2_mzs in ms2_in_files.items():
            for mz_val in quantification_df["row m/z"]:
                mz_found = int( np.any( np.isclose( mz_val, ms2_mzs, rtol=1e-5, atol=5e-3) ) )
                if file_name not in mz_in_ms2.keys():
                    mz_in_ms2[file_name] = [mz_found]
                else:
                    mz_in_ms2[file_name].append( mz_found )

        row_info = pd.DataFrame( { "id": quantification_df["row ID"],
                                   "m/z": quantification_df["row m/z"],
                                   "rt": quantification_df["row retention time"] } )
        ms2_presence_df = pd.DataFrame( mz_in_ms2 )
        ms2_presence_df = row_info.join(ms2_presence_df)
        
        if annotation_file:
            local_annotations = pd.read_csv( annotation_file )
            annotated_ms2_presence = pd.merge(ms2_presence_df, local_annotations, left_on="id", right_on="id", how="inner")

            annotated_ms2_presence.to_csv( f"{join(out_dir, basename(in_dir))}_ms2_presence_annotated.tsv", sep="\t" )
        else:
            ms2_presence_df.to_csv( f"{join(out_dir, basename(in_dir))}_ms2_presence.tsv", sep="\t")


    def check_ms2_presences_nested( self, in_root_dir:StrPath, data_root_dir:StrPath, out_root_dir:StrPath,
                                   futures:list=[], recusion_level:int=0 ) -> list:
        """
        Check for MS2 presence in a nested fashion.

        :param root_dir: Root input directory
        :type root_dir: StrPath
        :param ms_conv_root_dir: Root msconv output directory
        :type ms_conv_root_dir: StrPath
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
        quant_file, annot_file = (None, None)
        for entry in tqdm( os.listdir(in_root_dir), disable=verbose_tqdm, desc="Schedule ion exclusion" ):
            entry_path = join(in_root_dir, entry)
                 
            if os.path.isfile( entry_path ):
                if entry == f"{basename(in_root_dir)}_annotations":
                        annot_file = entry_path
                elif entry == f"{basename(in_root_dir)}_iimn_fbmn_quant.csv":
                    quant_file = entry_path
                
                
            elif os.path.isdir( entry_path ):
                futures = self.check_ms2_presences_nested( in_root_dir=entry_path,
                                                           out_root_dir=join( out_root_dir, entry ),
                                                           data_root_dir=join( data_root_dir, entry ),
                                                           futures=futures, recusion_level=recusion_level+1 )
                
        if quant_file:
            futures.append( dask.delayed(self.check_ms2_presence)( in_dir=in_root_dir,
                                                                   out_dir=out_root_dir, 
                                                                   data_dir=data_root_dir,
                                                                   annotation_file=annot_file ) )
        if futures:
            os.makedirs(out_root_dir, exist_ok=True)

        return futures



if __name__ == "__main__":
    parser = argparse.ArgumentParser( prog='ion_exclusion.py',
                                      description='Select ions for exclusion, based on MS2.')
    parser.add_argument('-in',      '--in_dir',             required=True)
    parser.add_argument('-out',     '--out_dir',            required=False)
    parser.add_argument('-data',    '--data_dir',           required=False)
    parser.add_argument('-r',       '--relative_tolerance', required=False)
    parser.add_argument('-a',       '--absolute_tolerance', required=False)
    parser.add_argument('-n',       '--nested',             required=False,     action="store_true")
    parser.add_argument('-s',       '--save_log',           required=False,     action="store_true")
    parser.add_argument('-w',       '--workers',            required=False,     type=int)
    parser.add_argument('-v',       '--verbosity',          required=False,     type=int)
    parser.add_argument('-ion_ex',  '--ion_exclusion_args', required=False,     nargs=argparse.REMAINDER)

    args, unknown_args = parser.parse_known_args()

    main(args=args, unknown_args=unknown_args)