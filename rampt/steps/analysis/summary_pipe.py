#!/usr/bin/env python

"""
Analysis of feature quantification and annotation.
"""

import os
import argparse

from os.path import join
from tqdm.auto import tqdm

import pandas as pd
import numpy as np
import json

from rampt.helpers.general import *
from rampt.helpers.logging import *
from rampt.helpers.types import StrPath
from rampt.steps.general import Pipe_Step, get_value


def main(args: argparse.Namespace | dict, unknown_args: list[str] = []):
    """
    Execute the conversion.

    :param args: Command line arguments
    :type args: argparse.Namespace|dict
    :param unknown_args: Command line arguments that are not known.
    :type unknown_args: list[str]
    """
    # Extract arguments
    in_dir_annotations = get_value(args, "in_dir_annotations")
    in_dir_quantification = get_value(args, "in_dir_quantification")
    out_dir = get_value(args, "out_dir")
    overwrite = get_value(args, "overwrite", False)
    nested = get_value(args, "nested", False)
    n_workers = get_value(args, "workers", 1)
    save_log = get_value(args, "save_log", False)
    verbosity = get_value(args, "verbosity", 1)
    additional_args = get_value(args, "summary_arguments")
    additional_args = additional_args if additional_args else unknown_args

    # Conversion
    summary_runner = Summary_Runner(
        overwrite=overwrite,
        save_log=save_log,
        additional_args=additional_args,
        verbosity=verbosity,
        nested=nested,
        workers=n_workers,
        scheduled_in=[{"quantification": in_dir_quantification, "annotation": in_dir_annotations}],
        scheduled_out=out_dir,
    )
    return summary_runner.run()


class Summary_Runner(Pipe_Step):
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
        super().__init__(save_log=save_log, additional_args=additional_args, verbosity=verbosity)
        if kwargs:
            self.update(kwargs)
        self.overwrite = overwrite
        self.name = "summary"
        self.summary = None

    def search_quantification_file(
        self, dir: StrPath, quantification_file: StrPath = None
    ) -> StrPath:
        """
        Check for quantification file.

        :param dir: Directory to search in
        :type dir: StrPath
        :param quantification_file: Quantification table path, defaults to None
        :type quantification_file: StrPath, optional
        :return: Paths to file
        :rtype:  StrPath
        """
        if os.path.isfile(dir):
            return dir
        for root, dirs, files in os.walk(dir):
            for file in files:
                if not quantification_file and file.endswith("_quant.csv"):
                    quantification_file = join(root, file)

        return quantification_file

    def search_annotation_files(
        self,
        dir: StrPath,
        canopus_formula_summary_file: StrPath = None,
        canopus_structure_summary_file: StrPath = None,
        denovo_structure_identifications_file: StrPath = None,
        formula_identifications_file: StrPath = None,
        structure_identifications_file: StrPath = None,
        gnps_annotations_path: StrPath = None,
    ) -> dict[str, StrPath]:
        """
        Check for annotation files.

        :param dir: Directory to search in
        :type dir: StrPath
        :param canopus_formula_summary_file: Canopus formula table path, defaults to None
        :type canopus_formula_summary_file: StrPath, optional
        :param canopus_structure_summary_file: Canopus structure table path, defaults to None
        :type canopus_structure_summary_file: StrPath, optional
        :param denovo_structure_identifications_file: DeNovo structure table path, defaults to None
        :type denovo_structure_identifications_file: StrPath, optional
        :param formula_identifications_file: Formula identifications table path, defaults to None
        :type formula_identifications_file: StrPath, optional
        :param structure_identifications_file: Structure identifications table path, defaults to None
        :type structure_identifications_file: StrPath, optional
        :param gnps_annotations_path: Annotations of GNPS molecular feature finding, defaults to None
        :type gnps_annotations_path: StrPath, optional
        :return: Paths to files
        :rtype:  dict[str, StrPath]
        """
        dirs = dir if isinstance(dir, list) or isinstance(dir, tuple) else [dir]
        for dir in dirs:
            if not dir:
                continue
            for root, dirs, files in os.walk(dir):
                for file in files:
                    if not canopus_formula_summary_file and file == "canopus_formula_summary.tsv":
                        canopus_formula_summary_file = join(root, file)
                    elif (
                        not canopus_structure_summary_file
                        and file == "canopus_structure_summary.tsv"
                    ):
                        canopus_structure_summary_file = join(root, file)
                    elif (
                        not denovo_structure_identifications_file
                        and file == "denovo_structure_identifications.tsv"
                    ):
                        denovo_structure_identifications_file = join(root, file)
                    elif not formula_identifications_file and file == "formula_identifications.tsv":
                        formula_identifications_file = join(root, file)
                    elif (
                        not structure_identifications_file
                        and file == "structure_identifications.tsv"
                    ):
                        structure_identifications_file = join(root, file)
                    elif not gnps_annotations_path and file.endswith(
                        "_gnps_all_db_annotations.json"
                    ):
                        gnps_annotations_path = join(root, file)
        return {
            "formula_identifications_file": formula_identifications_file,
            "canopus_formula_summary_file": canopus_formula_summary_file,
            "structure_identifications_file": structure_identifications_file,
            "canopus_structure_summary_file": canopus_structure_summary_file,
            "denovo_structure_identifications_file": denovo_structure_identifications_file,
            "gnps_annotations_path": gnps_annotations_path,
        }

    def read_sirius_df(self, file_path: StrPath, filter_columns: list | str) -> pd.DataFrame:
        df = pd.read_csv(file_path, sep="\t")
        df.replace("-Infinity", -np.inf, inplace=True)
        df.rename(columns={"mappingFeatureId": "ID"})

        if isinstance(filter_columns, str):
            filter_columns = [column for column in df.columns if filter_columns in column]
        for filter_column in filter_columns:
            df[filter_column] = df[filter_column].replace(r",", r".", regex=True).astype(float)

        return df

    # TODO: Add documentation & Testing
    def add_quantification(
        self, quantification_file: StrPath, summary: pd.DataFrame = None
    ) -> pd.DataFrame:
        df = pd.read_csv(quantification_file)
        df.columns = [column.replace("row ", "") for column in df.columns]

        if summary is not None:
            summary.merge(df, how="outer")
        else:
            summary = df

        summary = summary.dropna(how="all", axis=1)
        summary = summary.astype({"ID": str})
        summary = summary.sort_values("retention time", ascending=True)

        return summary

    def add_annotation(
        self, annotation_file: StrPath, annotation_file_type: str, summary: pd.DataFrame
    ) -> pd.DataFrame:
        match annotation_file_type:
            case "formula_identifications_file":
                df = self.read_sirius_df(file_path=annotation_file, filter_columns=["ZodiacScore"])
                df = df[["mappingFeatureId", "molecularFormula", "ZodiacScore"]]
                df = df.rename(
                    columns={
                        "mappingFeatureId": "ID",
                        "molecularFormula": "Sirius_formula",
                        "ZodiacScore": "Sirius_formula_confidence",
                    }
                )

            case "canopus_formula_summary_file":
                df = self.read_sirius_df(file_path=annotation_file, filter_columns="Probability")
                df = df[
                    [
                        column
                        for column in df.columns
                        if column == "mappingFeatureId"
                        or (column.startswith("NPC") or column.startswith("ClassyFire"))
                        and not column.endswith("all classifications")
                    ]
                ]

                rename_dict = {}
                for column in df.columns:
                    if "#" in column:
                        tool, name = column.split("#", maxsplit=1)
                        name = name.lower().replace(" ", "_").replace("probability", "confidence")
                        rename_dict[column] = f"Sirius_formula_{tool}_{name}"
                rename_dict.update({"mappingFeatureId": "ID"})
                df = df.rename(columns=rename_dict)

            case "structure_identifications_file":
                df = self.read_sirius_df(
                    file_path=annotation_file,
                    filter_columns=["ConfidenceScoreExact", "ConfidenceScoreApproximate"],
                )
                df = df[
                    [
                        "mappingFeatureId",
                        "smiles",
                        "links",
                        "ConfidenceScoreExact",
                        "ConfidenceScoreApproximate",
                        "CSI:FingerIDScore",
                    ]
                ]
                df = df.rename(
                    columns={
                        "mappingFeatureId": "ID",
                        "smiles": "Sirius_structure_smiles",
                        "links": "Sirius_structure_links",
                        "ConfidenceScoreExact": "Sirius_structure_confidence",
                        "ConfidenceScoreApproximate": "Sirius_approximate_structure_confidence",
                        "CSI:FingerIDScore": "Sirius_structure_CSI:FingerIDScore",
                    }
                )

            case "canopus_structure_summary_file":
                df = self.read_sirius_df(file_path=annotation_file, filter_columns="Probability")
                df = df[
                    [
                        column
                        for column in df.columns
                        if column == "mappingFeatureId"
                        or (column.startswith("NPC") or column.startswith("ClassyFire"))
                        and not column.endswith("all classifications")
                    ]
                ]

                rename_dict = {}
                for column in df.columns:
                    if "#" in column:
                        tool, name = column.split("#", maxsplit=1)
                        name = name.lower().replace(" ", "_").replace("probability", "confidence")
                        rename_dict[column] = f"Sirius_structure_{tool}_{name}"
                rename_dict.update({"mappingFeatureId": "ID"})
                df = df.rename(columns=rename_dict)

            case "denovo_structure_identifications_file":
                df = self.read_sirius_df(
                    file_path=annotation_file, filter_columns=["CSI:FingerIDScore"]
                )
                df = df[["mappingFeatureId", "smiles", "CSI:FingerIDScore"]]
                df = df.rename(
                    columns={
                        "mappingFeatureId": "ID",
                        "smiles": "Sirius_denovo_structure_smiles",
                        "CSI:FingerIDScore": "Sirius_denovo_structure_CSI:FingerIDScore",
                    }
                )

            case "gnps_annotations_path":
                with open(annotation_file, "r") as file:
                    hit_dicts = json.load(file)["blockData"]
                df = pd.DataFrame(hit_dicts)[
                    ["#Scan#", "Compound_Name", "MQScore", "MZErrorPPM", "SharedPeaks"]
                ]
                df = df.rename(
                    columns={
                        "#Scan#": "ID",
                        "Compound_Name": "FBMN_compound_name",
                        "MQScore": "FBMN_MQ_score(cosine)",
                        "MZErrorPPM": "FBMN_m/z_error(ppm)",
                        "SharedPeaks": "FBMN_shared_peaks",
                    }
                )

        df = df.astype({"ID": str})
        summary = summary.merge(df, how="left", on="ID")
        return summary

    def add_annotations(self, annotation_files: StrPath, summary: pd.DataFrame):
        # Order the annotations
        order_list = [
            "formula_identifications_file",
            "canopus_formula_summary_file",
            "structure_identifications_file",
            "canopus_structure_summary_file",
            "denovo_structure_identifications_file",
            "gnps_annotations_path",
        ]
        annotation_files_ordered = dict()
        for key in order_list:
            annotation_files_ordered[key] = annotation_files[key]

        # Append all annotations
        for annotation_file_type, annotation_path in annotation_files_ordered.items():
            if annotation_path:
                summary = self.add_annotation(
                    annotation_file=annotation_path,
                    annotation_file_type=annotation_file_type,
                    summary=summary,
                )

        return summary

    def sort_in_paths(
        self, in_paths: tuple[StrPath] | list[StrPath] | dict[str, StrPath] | StrPath
    ) -> tuple[StrPath]:
        if isinstance(in_paths, dict):
            return (in_paths["quantification"], in_paths["annotation"])
        elif isinstance(in_paths, StrPath):
            return in_paths, in_paths
        else:
            return in_paths[0], in_paths[1]

    def add_quantification_annotation_s(
        self,
        in_path: dict,
        out_path: StrPath,
        annotation_file_type: str = None,
        quantification_file: StrPath = None,
        annotation_files: dict[str, StrPath] = None,
        summary: pd.DataFrame = None,
    ):
        # Separate arguments of in_path
        in_paths_annotation = None
        if isinstance(in_path, dict):
            in_path_quantification = in_path.get("quantification")
            in_paths_annotation = in_path.get("annotation")
        elif isinstance(in_path, str):
            in_path_quantification = in_path
        else:
            in_path_quantification = in_path[0]
            in_paths_annotation = in_path[1]

        # Make quantification table as base
        if not quantification_file:
            quantification_file = self.search_quantification_file(dir=in_path_quantification)
        summary = self.add_quantification(quantification_file=quantification_file, summary=summary)

        # Add annotations
        if annotation_files:
            summary = self.add_annotations(annotation_files=annotation_files, summary=summary)
        else:
            # Filter out duplicates and None
            for in_path_annotation in [ipa for ipa in set(to_list(in_paths_annotation)) if ipa]:
                annotation_files = self.search_annotation_files(dir=in_path_annotation)

                # Case run_single
                if annotation_file_type:
                    summary = self.add_annotation(
                        annotation_file=in_path_annotation,
                        annotation_file_type=annotation_file_type,
                        summary=summary,
                    )
                else:
                    summary = self.add_annotations(
                        annotation_files=annotation_files, summary=summary
                    )

        # Export summary
        summary.to_csv(out_path, sep="\t")

        if in_paths_annotation:
            logger.log(
                f"Added annotation from {in_paths_annotation} to {in_path_quantification}.Exported to {out_path}.",
                minimum_verbosity=1,
                verbosity=self.verbosity,
            )
        else:
            logger.log(
                f"No annotation received. {in_path_quantification} exported to {out_path}.",
                minimum_verbosity=1,
                verbosity=self.verbosity,
            )

    def run_single(
        self,
        in_path: StrPath,
        out_path: StrPath,
        annotation_file_type: str,
        summary: pd.DataFrame = None,
    ):
        """
        Add the annotations into a quantification file.

        :param in_path: Path to scheduled file.
        :type in_path: str
        :param out_path: Path to output directory.
        :type out_path: str
        :param annotation_file_type: File type of annotation
        :type annotation_file_type: str
        :param summary: Summary to write to, defaults to None
        :type summary: pd.DataFrame, optional
        """
        summary = summary if summary else self.summary

        # Determine paths
        in_path_quantification, in_path_annotation = self.sort_in_paths(in_paths=in_path)
        out_path = join(out_path, "summary.tsv") if os.path.isdir(out_path) else out_path

        self.compute(
            step_function=capture_and_log,
            func=self.add_quantification_annotation_s,
            in_path={"quantification": in_path_quantification, "annotation": in_path_annotation},
            out_path=out_path,
            annotation_file_type=annotation_file_type,
            log_path=self.get_log_path(out_path=out_path),
        )

    def run_directory(
        self,
        in_path: StrPath,
        out_path: StrPath,
        summary: pd.DataFrame = None,
        quantification_file: StrPath = None,
        annotation_files: dict[str, StrPath] = None,
    ):
        """
        Convert all matching files in a folder.

        :param in_path: Path to scheduled file.
        :type in_path: str
        :param out_path: Path to output directory.
        :type out_path: str
        :param summary: Summary to write to, defaults to None
        :type summary: pd.DataFrame, optional
        """
        summary = summary if summary else self.summary

        # Determine paths
        in_path_quantification, in_paths_annotation = self.sort_in_paths(in_paths=in_path)
        out_path = join(out_path, "summary.tsv") if os.path.isdir(out_path) else out_path

        self.compute(
            step_function=capture_and_log,
            func=self.add_quantification_annotation_s,
            in_path={"quantification": in_path_quantification, "annotation": in_paths_annotation},
            out_path=out_path,
            quantification_file=quantification_file,
            annotation_files=annotation_files,
            log_path=self.get_log_path(out_path=out_path),
        )

    def run_nested(self, in_root_dir: StrPath, out_root_dir: StrPath, recusion_level: int = 0):
        """
        Converts multiple files in multiple folders, found in in_root_dir with msconvert and saves them
        to a location out_root_dir again into their respective folders.

        :param in_root_dir: Starting folder for descent.
        :type in_root_dir: StrPath
        :param out_root_dir: Folder where structure is mimiced and files are converted to
        :type out_root_dir: StrPath
        :param recusion_level: Current level of recursion, important for determination of level of verbose output, defaults to 0
        :type recusion_level: int, optional
        """
        verbose_tqdm = self.verbosity >= recusion_level + 2
        made_out_root_dir = False

        for root, dirs, files in os.walk(in_root_dir):
            quantification_file = self.search_quantification_file(dir=root)
            annotation_files = self.search_annotation_files(dir=root)

            if quantification_file and [
                val for val in annotation_files.values() if val is not None
            ]:
                if not made_out_root_dir:
                    os.makedirs(out_root_dir, exist_ok=True)
                    made_out_root_dir = True

                self.run_directory(in_path=root, out_path=out_root_dir)

            for dir in tqdm(dirs, disable=verbose_tqdm, desc="Directories"):
                self.run_nested(
                    in_root_dir=join(in_root_dir, dir),
                    out_root_dir=join(out_root_dir, dir),
                    recusion_level=recusion_level + 1,
                )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="summary_pipe.py",
        description="Conversion of manufacturer MS files to .mzML or .mzXML target_format.\
                                             The folder structure is mimiced at the place of the output.",
    )
    parser.add_argument("-ina", "--in_dir_annotations", required=True)
    parser.add_argument("-inq", "--in_dir_quantification", required=True)
    parser.add_argument("-out", "--out_dir", required=True)
    parser.add_argument("-o", "--overwrite", required=False, action="store_true")
    parser.add_argument("-n", "--nested", required=False, action="store_true")
    parser.add_argument("-w", "--workers", required=False, type=int)
    parser.add_argument("-s", "--save_log", required=False, action="store_true")
    parser.add_argument("-v", "--verbosity", required=False, type=int)
    parser.add_argument("-summary", "--summary_arguments", required=False, nargs=argparse.REMAINDER)

    args, unknown_args = parser.parse_known_args()
    main(args=args, unknown_args=unknown_args)
