#!/usr/bin/env python3

"""
Openms File Handling.
"""

# Imports
import gc
from typing import Union, Sequence, Optional, List
from tqdm import tqdm

import pyopenms as oms

from rampt.helpers.types import *
from rampt.helpers.logging import *


class OpenMS_File_Handler:
    """
    File handler with OpenMS.
    """

    def __init__(self, verbosity: int = 1):
        """
        Initalize OpenMS_File_Handler

        :param verbosity: Verbosity level, defaults to 1
        :type verbosity: int, optional
        """
        self.verbosity = verbosity

    def check_ending_experiment(self, file: StrPath) -> bool:
        """
        Check whether the file has a mzML or mzXML ending.

        :param file: Path to file
        :type file: StrPath
        :return: Ending is mzML or mzXML
        :rtype: bool
        """
        return (
            file.endswith(".mzML")
            or file.endswith(".MzML")
            or file.endswith(".mzXML")
            or file.endswith(".MzXML")
        )

    def read_experiment(self, experiment_path: StrPath, separator: str = "\t") -> oms.MSExperiment:
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
        elif (
            experiment_path.endswith(".tsv")
            or experiment_path.endswith(".csv")
            or experiment_path.endswith(".txt")
        ):
            exp_df = pd.read_csv(experiment_path, sep=separator)
            spectrum = oms.MSSpectrum()
            spectrum.set_peaks((exp_df["mz"], exp_df["inty"]))
            experiment.addSpectrum(spectrum)
        else:
            raise ValueError(
                f'Invalid ending of {experiment_path}. Must be in [".MzXML", ".mzXML", ".MzML", ".mzML", ".tsv", ".csv", ".txt"]'
            )
        return experiment

    def load_experiment(
        self, experiment: Union[oms.MSExperiment, StrPath], separator: str = "\t"
    ) -> oms.MSExperiment:
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

    def load_experiments(
        self,
        experiments: Union[Sequence[Union[oms.MSExperiment, StrPath]], StrPath],
        file_ending: Optional[str] = None,
        separator: str = "\t",
        data_load: bool = True,
    ) -> Sequence[Union[oms.MSExperiment, StrPath]]:
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
                experiments = [
                    os.path.join(experiments, file)
                    for file in os.listdir(experiments)
                    if file.endswith(file_ending)
                ]
            else:
                experiments = [
                    os.path.join(experiments, file)
                    for file in os.listdir(experiments)
                    if self.check_ending_experiment(file)
                ]
        if data_load:
            experiments = [
                self.load_experiment(experiment, separator=separator)
                for experiment in tqdm(experiments)
            ]
        return experiments

    def load_name(
        self,
        experiment: Union[oms.MSExperiment, str],
        alt_name: Optional[str] = None,
        file_ending: Optional[str] = None,
    ) -> str:
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

    def load_names_batch(
        self,
        experiments: Union[Sequence[Union[oms.MSExperiment, str]], str],
        file_ending: str = ".mzML",
    ) -> List[str]:
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
                return [
                    self.load_name(file)
                    for file in tqdm(os.listdir(experiments))
                    if file.endswith(file_ending)
                ]
            else:
                return [
                    self.load_name(file)
                    for file in tqdm(os.listdir(experiments))
                    if self.check_ending_experiment(file)
                ]
        else:
            if isinstance(experiments[0], str):
                return [self.load_name(experiment) for experiment in tqdm(experiments)]
            else:
                return [
                    self.load_name(experiment, str(i))
                    for i, experiment in enumerate(tqdm(experiments))
                ]

    def load_experiments_df(
        self,
        data_dir: str,
        file_ending: str,
        separator: str = "\t",
        data_load: bool = True,
        table_backend=pd,
    ) -> pd.DataFrame:
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
        log("Loading names:", minimum_verbosity=2, verbosity=self.verbosity)
        names = self.load_names_batch(data_dir, file_ending)
        samples = [name.split("_")[:-1] for name in names]
        polarities = [{"pos": 1, "neg": -1}.get(name.split("_")[-1]) for name in names]
        log("Loading experiments:", minimum_verbosity=2, verbosity=self.verbosity)
        experiments = self.load_experiments(
            data_dir, file_ending, separator=separator, data_load=data_load
        )
        fia_df = table_backend.DataFrame([samples, polarities, experiments])
        fia_df = fia_df.transpose()
        fia_df.columns = ["sample", "polarity", "experiment"]
        return fia_df
