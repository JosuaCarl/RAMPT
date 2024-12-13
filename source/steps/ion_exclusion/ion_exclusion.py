#!/usr/bin/env python3

"""
Write an exclusion list from MS2 precursors.
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
from source.steps.general import Pipe_Step, get_value
import source.helpers as helpers


def main(args:argparse.Namespace|dict, unknown_args:list[str]=[]):
    """
    Exclude ions.

    :param args: Command line arguments
    :type args: argparse.Namespace|dict
    :param unknown_args: Command line arguments that are not known.
    :type unknown_args: list[str]
    """
    # Extract arguments
    in_dir                      = get_value(args, "in_dir" )
    out_dir                     = get_value(args, "out_dir",                    in_dir)
    data_dir                    = get_value(args, "data_dir",                   out_dir)
    relative_tolerance          = get_value(args, "relative_tolerance",         1e-05) 
    absolute_tolerance          = get_value(args, "absolute_tolerance",         1e-08)
    retention_time_tolerance    = get_value(args, "retention_time_tolerance",   None)
    nested                      = get_value(args, "nested",                     False)
    n_workers                   = get_value(args, "workers",                    1)
    save_log                    = get_value(args, "save_log",                   False)
    verbosity                   = get_value(args, "verbosity",                  1)
    additional_args             = get_value(args, "ion_exclusion_args",         unknown_args)
    additional_args = additional_args if additional_args else unknown_args

    ion_exclusion_runner = Ion_exclusion_Runner( relative_tolerance=relative_tolerance, absolute_tolerance=absolute_tolerance,
                                                 retention_time_tolerance=retention_time_tolerance,
                                                 save_log=save_log, additional_args=additional_args, verbosity=verbosity )

    if nested:
        futures = ion_exclusion_runner.check_ms2_presences_nested( in_root_dir=in_dir, out_root_dir=out_dir, data_root_dir=data_dir )
        helpers.compute_scheduled( futures=futures, num_workers=n_workers, verbose=verbosity >= 1)
    else:
        ion_exclusion_runner.check_ms2_presence( in_dir=in_dir, out_dir=out_dir, data_dir=data_dir )

    return ion_exclusion_runner.processed_out



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
            spectrum.set_peaks( (exp_df["mz"], exp_df["inty"]) )
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
                raise ValueError("No file path found in experiment. Please provide alt_name.")


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
    def __init__( self, relative_tolerance:float=1e-5, absolute_tolerance:float=5e-3, retention_time_tolerance:float=10.0,
                  binary:bool=False, save_log:bool=False, additional_args:list=[], verbosity:int=1 ):
        """
        Initialize the ion exclusion runner.

        :param relative_tolerance: Relative m/z tolerance (1e-6 = 1ppm), defaults to 1e-5
        :type relative_tolerance: float, optional
        :param absolute_tolerance: Absolute m/z tolerance (1.0 = 1 Da), defaults to 5e-3
        :type absolute_tolerance: float, optional
        :param retention_time_tolerance: Retention time tolerance (s), defaults to 10.0
        :type retention_time_tolerance: float, optional
        :param binary: Output as in/out or count, defaults to False
        :type binary: bool, optional
        :param save_log: Save the log file, defaults to False
        :type save_log: bool, optional
        :param additional_args: Additional arguments, defaults to []
        :type additional_args: list, optional
        :param verbosity: Level of verbosity, defaults to 1
        :type verbosity: int, optional
        """
        super().__init__( save_log=save_log, additional_args=additional_args, verbosity=verbosity )
        self.relative_tolerance = relative_tolerance if isinstance(relative_tolerance, float) else relative_tolerance * 1e-6
        self.absolute_tolerance = absolute_tolerance
        self.retention_time_tolerance = retention_time_tolerance
        self.binary             = binary
        self.file_handler       = OpenMS_File_Handler()



    def check_ms2_presence( self, in_dir:StrPath, out_dir:StrPath, data_dir:StrPath, annotation_file:StrPath=None ):
        """
        Check for MS2 fractioning precursors in aligned features.

        :param in_dir: Path to input directory, including quantification file
        :type in_dir: StrPath
        :param out_dir: Path to output directory
        :type out_dir: StrPath
        :param data_dir: Path to data directory with raw spectra
        :type data_dir: StrPath
        :param annotation_file: Path to annotation file (as csv), defaults to None
        :type annotation_file: StrPath, optional
        """
        experiments = self.file_handler.load_experiments_df( data_dir, file_ending=".mzML")
    
        precursor_infos_files = {}
        for i, row in experiments.iterrows():
            experiment = row["experiment"]
            ms2_spectra = [ spectrum for spectrum in experiment.getSpectra() if spectrum.getMSLevel() >= 2 ]
            retention_times = []
            precursor_mzs = []
            for ms2_spectrum in ms2_spectra:
                for precursor in ms2_spectrum.getPrecursors():
                    retention_times.append( ms2_spectrum.getRT() )
                    precursor_mzs.append( precursor.getMZ() )
            precursor_infos_files[basename(experiment.getLoadedFilePath())] = pd.DataFrame( {"m/z": precursor_mzs, "rt": retention_times} )

        quantification_df  = pd.read_csv(f"{join(in_dir, basename(in_dir))}_iimn_fbmn_quant.csv")
        mz_in_ms2 = {}
        for file_name, precursor_infos in precursor_infos_files.items():
            for i, feature in quantification_df.iterrows():
                mz_matches = np.isclose( feature["row m/z"], precursor_infos["m/z"],
                                         rtol=self.relative_tolerance, atol=self.absolute_tolerance)
                if self.retention_time_tolerance is not None:
                    retention_time_matches = np.isclose( feature["row retention time"], precursor_infos["rt"],
                                                         rtol=0.0, atol=self.retention_time_tolerance)
                    all_matches = mz_matches & retention_time_matches
                else:
                    all_matches = mz_matches
                feature_found = int( np.any ( all_matches ) ) if self.binary else np.sum( all_matches ) 
                if file_name not in mz_in_ms2.keys():
                    mz_in_ms2[file_name] = [feature_found]
                else:
                    mz_in_ms2[file_name].append( feature_found )

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

        self.processed_in.append( in_dir )
        self.processed_out.append( out_dir )

        return out_dir


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
    parser.add_argument('-rt',       '--retention_time_tolerance', required=False)
    parser.add_argument('-n',       '--nested',             required=False,     action="store_true")
    parser.add_argument('-s',       '--save_log',           required=False,     action="store_true")
    parser.add_argument('-w',       '--workers',            required=False,     type=int)
    parser.add_argument('-v',       '--verbosity',          required=False,     type=int)
    parser.add_argument('-ion_ex',  '--ion_exclusion_args', required=False,     nargs=argparse.REMAINDER)

    args, unknown_args = parser.parse_known_args()

    main(args=args, unknown_args=unknown_args)