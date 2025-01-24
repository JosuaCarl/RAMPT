#!/usr/bin/env python

"""
Analysis of feature quantification and annotation.
"""

import os
import argparse

from os.path import join

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

    # Summary
    summary_runner = Summary_Runner(
        overwrite=overwrite,
        save_log=save_log,
        additional_args=additional_args,
        verbosity=verbosity,
        nested=nested,
        workers=n_workers,
    )
    summary_runner.scheduled_ios = {
        "in_path": {"quantification": in_dir_quantification, "annotation": in_dir_annotations},
        "out_path": {"standard": out_dir},
    }
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
        super().__init__(
            patterns={
                "quantification": r".*_quant\.csv$",
                "formula_identifications": r".*formula_identifications\.tsv$",
                "canopus_formula_summary": r".*canopus_formula_summary\.tsv$",
                "structure_identifications": r".*structure_identifications\.tsv$",
                "canopus_structure_summary": r".*canopus_structure_summary\.tsv$",
                "denovo_structure_identifications": r".*denovo_structure_identifications\.tsv$",
                "gnps_annotations": r".*fbmn_all_db_annotations\.json$",
            },
            save_log=save_log,
            additional_args=additional_args,
            verbosity=verbosity,
        )
        if kwargs:
            self.update(kwargs)
        self.overwrite = overwrite
        self.name = "summary"
        self.summary = None

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
        self, quantification_path: StrPath, summary: pd.DataFrame = None
    ) -> pd.DataFrame:
        df = pd.read_csv(quantification_path)
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

    def add_annotations(
        self, annotation_files: dict[str, StrPath], summary: pd.DataFrame
    ) -> pd.DataFrame:
        # Order the annotations
        order_list = [
            "formula_identifications",
            "canopus_formula_summary",
            "structure_identifications",
            "canopus_structure_summary",
            "denovo_structure_identifications",
            "gnps_annotations",
        ]
        annotation_files_ordered = {}
        for key in order_list:
            if key in annotation_files:
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

    def summarize_info(self, in_path: dict, out_path: StrPath, summary: pd.DataFrame = None):
        # Make quantification table as base
        summary = self.add_quantification(
            quantification_path=in_path.pop("quantification"), summary=summary
        )

        # Add annotations
        summary = self.add_annotations(annotation_files=in_path, summary=summary)

        # Export summary
        summary.to_csv(out_path, sep="\t")

        logger.log(
            f"Added given annotations {list(in_path.keys())} to quantifications. Exported to {out_path}.",
            minimum_verbosity=1,
            verbosity=self.verbosity,
        )

    # Distribution
    def distribute_scheduled(self, **scheduled_io):
        return super().distribute_scheduled(standard_value="quantification", **scheduled_io)

    # RUN
    def run_single(
        self,
        in_path: dict[str, StrPath],
        out_path: dict[str, StrPath],
        summary: pd.DataFrame = None,
        **kwargs,
    ):
        """
        Add the annotations into a quantification file.

        :param in_path: Path to scheduled file.
        :type in_path: dict[str, StrPath]
        :param out_path: Path to output directory.
        :type out_path: dict[str, StrPath]
        :param summary: Summary to write to, defaults to None
        :type summary: pd.DataFrame, optional
        """
        in_path, out_path, summary = self.extract_standard(
            in_path=in_path, out_path=out_path, summary=summary
        )
        out_path = join(out_path, "summary.tsv") if os.path.isdir(out_path) else out_path

        # Propagate summary of instance (can be used to annotate with multiple annotation files in a row)
        summary = summary if summary else self.summary

        self.compute(
            step_function=capture_and_log,
            func=self.summarize_info,
            in_path=in_path,
            out_path=out_path,
            log_path=self.get_log_path(out_path=out_path),
        )

    def run_directory(
        self,
        in_path: dict[str, StrPath],
        out_path: dict[str, StrPath],
        summary: pd.DataFrame = None,
        **kwargs,
    ):
        """
        Summarize all annpotation and files in the given folders.

        :param in_path: Path to scheduled file.
        :type in_path: dict[str, StrPath]
        :param out_path: Path to output directory.
        :type out_path: dict[str, StrPath]
        :param summary: Summary to write to, defaults to None
        :type summary: pd.DataFrame, optional
        """
        summary = summary if summary else self.summary
        in_path, out_path, summary = self.extract_standard(
            in_path=in_path, out_path=out_path, summary=summary
        )

        matched_in_paths = {}
        for file_type, path in in_path:
            for entry in os.listdir(path):
                if self.match_path(pattern=self.patterns[file_type], path=entry):
                    matched_in_paths[file_type] = join(path, entry)
                    break

        if "quantification" in matched_in_paths:
            os.makedirs(out_path, exist_ok=True)
            self.run_single(in_path=matched_in_paths, out_path=out_path, summary=summary, **kwargs)
        else:
            logger.error(
                message=f"Found no quantification information in matched_in_paths={matched_in_paths}, inferred from in_paths={in_path}",
                error_type=ValueError,
            )

    def run_nested(
        self,
        in_path: dict[str, StrPath],
        out_path: dict[str, StrPath],
        recusion_level: int = 0,
        **kwargs,
    ):
        """
        Summarize all annotation files with quantification files in the matching folders.

        :param in_path: Starting folder for descent.
        :type in_path: dict[str, StrPath]
        :param out_path: Folder where structure is mimiced and files are converted to
        :type out_path: dict[str, StrPath]
        :param recusion_level: Current level of recursion, important for determination of level of verbose output, defaults to 0
        :type recusion_level: int, optional
        """
        in_path, out_path = self.extract_standard(in_path=in_path, out_path=out_path)

        for root, dirs, files in os.walk(in_path):
            dirs_with_matches = {}
            for dir in dirs:
                for file_type, pattern in self.patterns:
                    for entry in os.listdir(in_path, dir):
                        if self.match_path(pattern=pattern, path=entry):
                            dirs_with_matches[file_type] = join(in_path, dir)
                            break

            if dirs_with_matches:
                self.run_directory(in_path=dirs_with_matches, out_path=out_path, **kwargs)
            else:
                for dir in dirs:
                    self.run_nested(
                        in_path=join(in_path, dir),
                        out_path=join(out_path, dir),
                        recusion_level=recusion_level + 1,
                        **kwargs,
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
