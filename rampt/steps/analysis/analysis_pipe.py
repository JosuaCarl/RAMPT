#!/usr/bin/env python

"""
Analysis of feature quantification and annotation.
"""

import os
import argparse

import pandas as pd

from os.path import join

from rampt.helpers.types import StrPath
from rampt.steps.general import Pipe_Step, get_value
from rampt.steps.analysis.statistics import *


def main(args: argparse.Namespace | dict, unknown_args: list[str] = []):
    """
    Execute the conversion.

    :param args: Command line arguments
    :type args: argparse.Namespace|dict
    :param unknown_args: Command line arguments that are not known.
    :type unknown_args: list[str]
    """
    # Extract arguments
    in_dir = get_value(args, "in_dir")
    out_dir = get_value(args, "out_dir")
    overwrite = get_value(args, "overwrite", False)
    nested = get_value(args, "nested", False)
    n_workers = get_value(args, "workers", 1)
    save_log = get_value(args, "save_log", False)
    verbosity = get_value(args, "verbosity", 1)
    additional_args = get_value(args, "analysis_arguments")
    additional_args = additional_args if additional_args else unknown_args

    # Conversion
    analysis_runner = Analysis_Runner(
        overwrite=overwrite,
        save_log=save_log,
        additional_args=additional_args,
        verbosity=verbosity,
        nested=nested,
        workers=n_workers,
    )
    analysis_runner.scheduled_ios = {
        "in_path": {"standard": in_dir},
        "out_path": {"standard": out_dir},
    }
    return analysis_runner.run()


class Analysis_Runner(Pipe_Step):
    """
    General class for file conversion along matched patterns.
    """

    def __init__(
        self,
        overwrite: bool = False,
        save_log=False,
        additional_args: list = [],
        verbosity=1,
        **kwargs,
    ):
        """
        Initializes the file converter.

        :param overwrite: Overwrite all, do not check whether file already exists, defaults to False
        :type overwrite: bool, optional
        :param save_log: Whether to save the output(s).
        :type save_log: bool, optional
        :param additional_args: Additional arguments for mzmine, defaults to []
        :type additional_args: list, optional
        :param verbosity: Level of verbosity, defaults to 1
        :type verbosity: int, optional
        """
        super().__init__(
            patterns={"in": r"^(.*[\\/])?summary\.tsv$"},
            save_log=save_log,
            additional_args=additional_args,
            verbosity=verbosity,
        )
        if kwargs:
            self.update(kwargs)
        self.overwrite = overwrite
        self.name = "analysis"
        self.analysis = None

    # Information extraction
    def read_summary(self, file_path: StrPath):
        """
        Read in summary file.

        :param file_path: Path to summary file
        :type file_path: StrPath
        """
        return pd.read_csv(file_path, sep="\t", index_col=0)

    def search_check_peak_info(
        self,
        summary: pd.DataFrame,
        keywords_peaks: list[str] = ["peak area", "peak height"],
        keywords_pos: list[str] = ["pos", "+"],
        keywords_neg: list[str] = ["neg", "-"],
    ) -> dict:
        """
        Search for peaks with information quantification information.

        :param summary: Summary dataframe
        :type summary: pd.DataFrame
        :param keywords_peaks: Keywords for peaks, defaults to ["peak area", "peak height"]
        :type keywords_peaks: list[str], optional
        :param keywords_pos: Keywords for positive mode, defaults to ["pos", "+"]
        :type keywords_pos: list[str], optional
        :param keywords_neg: Keywords for negative mode, defaults to ["neg", "-"]
        :type keywords_neg: list[str], optional
        :return: Dictionary of positive and negative peaks
        :rtype: dict
        """
        peak_columns = {"positive": [], "negative": [], "unknown": []}
        for column_name in summary.columns:
            keyword_peak_found = bool(
                [
                    column_name
                    for keyword in keywords_peaks
                    if keyword.lower() in column_name.lower()
                ]
            )
            if keyword_peak_found:
                if (
                    "float" in summary[column_name].dtype.name
                    or "int" in summary[column_name].dtype.name
                ):
                    keyword_pos_found = bool(
                        [
                            column_name
                            for keyword in keywords_pos
                            if keyword.lower() in column_name.lower()
                        ]
                    )
                    keyword_neg_found = bool(
                        [
                            column_name
                            for keyword in keywords_neg
                            if keyword.lower() in column_name.lower()
                        ]
                    )
                    if keyword_pos_found:
                        peak_columns["positive"].append(column_name)
                    elif keyword_neg_found:
                        peak_columns["negative"].append(column_name)
                    else:
                        peak_columns["unknown"].append(column_name)

        return {mode: mode_columns for mode, mode_columns in peak_columns.items() if mode_columns}

    # Analysis methods
    def z_score(self, summary: pd.DataFrame, peak_mode_columns: list) -> pd.DataFrame:
        if len(peak_mode_columns) < 2:
            logger.warn(
                "Data must contain at least 2 columns with peak information to calculate z-scores between samples. Returning unchanged."
            )
            return summary[peak_mode_columns]
        else:
            analysis = stats.zscore(summary[peak_mode_columns], axis=1, nan_policy="omit")
            return analysis

    # Export
    def export_results(self, analysis: pd.DataFrame, peak_columns: list, out_path: StrPath):
        if os.path.isfile(out_path):
            analysis.to_csv(out_path, sep="\t")
        else:
            analysis.to_csv(join(out_path, "analysis.tsv"), sep="\t")
            for mode, mode_columns in peak_columns.items():
                analysis[mode_columns].to_csv(join(out_path, f"analysis_{mode}_mode.tsv"), sep="\t")

    def complete_analysis(self, in_out: dict[str, StrPath]) -> pd.DataFrame:
        in_path, out_path = self.extract_standard(**in_out)
        summary = self.read_summary(file_path=in_path)

        peak_columns = self.search_check_peak_info(summary=summary)

        self.analysis = summary

        analyses = {
            mode: self.z_score(summary, mode_columns) for mode, mode_columns in peak_columns.items()
        }

        for mode, mode_columns in peak_columns.items():
            self.analysis[mode_columns] = analyses[mode]

        self.export_results(analysis=self.analysis, peak_columns=peak_columns, out_path=out_path)

        logger.log(
            f"Analyzed {in_path}, saved to {out_path}",
            minimum_verbosity=1,
            verbosity=self.verbosity,
        )

    # Distribution
    def distribute_scheduled(self, **scheduled_io):
        return super().distribute_scheduled(**scheduled_io)

    # RUN
    def run_single(self, in_path: dict[str, StrPath], out_path: dict[str, StrPath], **kwargs):
        """
        Add the annotations into a quantification file.

        :param in_path: Path to scheduled file.
        :type in_path: dict[str, StrPath]
        :param out_path: Path to output directory.
        :type out_path: dict[str, StrPath]
        """
        in_path, out_path = self.extract_standard(in_path=in_path, out_path=out_path)
        self.compute(
            step_function=capture_and_log,
            func=self.complete_analysis,
            in_out=dict(in_path=in_path, out_path=out_path),
            log_path=self.get_log_path(out_path=out_path),
        )

    def run_directory(self, in_path: dict[str, StrPath], out_path: dict[str, StrPath], **kwargs):
        """
        Convert all matching files in a folder.

        :param in_path: Path to scheduled file.
        :type in_path: dict[str, StrPath]
        :param out_path: Path to output directory.
        :type out_path: dict[str, StrPath]
        """
        in_path, out_path = self.extract_standard(in_path=in_path, out_path=out_path)
        for entry in os.listdir(in_path):
            if self.match_path(pattern=self.patterns["in"], path=entry):
                os.makedirs(out_path, exist_ok=True)
                self.run_single(in_path=join(in_path, entry), out_path=out_path, **kwargs)
                break

    def run_nested(
        self,
        in_path: dict[str, StrPath],
        out_path: dict[str, StrPath],
        recusion_level: int = 0,
        **kwargs,
    ):
        """
        Converts multiple files in multiple folders, found in in_path with msconvert and saves them
        to a location out_path again into their respective folders.

        :param in_path: Starting folder for descent.
        :type in_path: dict[str, StrPath]
        :param out_path: Folder where structure is mimiced and files are converted to
        :type out_path: dict[str, StrPath]
        :param recusion_level: Current level of recursion, important for determination of level of verbose output, defaults to 0
        :type recusion_level: int, optional
        """
        in_path, out_path = self.extract_standard(in_path=in_path, out_path=out_path)

        root, dirs, files = next(os.walk(in_path))

        for file in files:
            if self.match_path(pattern=self.patterns["in"], path=file):
                self.run_directory(in_path=in_path, out_path=out_path, **kwargs)

        for dir in dirs:
            self.run_nested(
                in_path=join(in_path, dir),
                out_path=join(out_path, dir),
                recusion_level=recusion_level + 1,
                **kwargs,
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="msconv_pipe.py",
        description="Conversion of manufacturer MS files to .mzML or .mzXML target_format.\
                                             The folder structure is mimiced at the place of the output.",
    )
    parser.add_argument("-in", "--in_dir", required=True)
    parser.add_argument("-out", "--out_dir", required=True)
    parser.add_argument("-o", "--overwrite", required=False, action="store_true")
    parser.add_argument("-n", "--nested", required=False, action="store_true")
    parser.add_argument("-w", "--workers", required=False, type=int)
    parser.add_argument("-s", "--save_log", required=False, action="store_true")
    parser.add_argument("-v", "--verbosity", required=False, type=int)
    parser.add_argument(
        "-analysis", "--analysis_arguments", required=False, nargs=argparse.REMAINDER
    )

    args, unknown_args = parser.parse_known_args()
    main(args=args, unknown_args=unknown_args)
