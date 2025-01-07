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

import source.helpers as helpers
from source.helpers.types import StrPath
from source.steps.general import Pipe_Step, get_value


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
	additional_args = get_value(args, "analysis_arguments")
	additional_args = additional_args if additional_args else unknown_args

	# Conversion
	analysis_runner = Summary_Runner(
		overwrite=overwrite,
		save_log=save_log,
		additional_args=additional_args,
		verbosity=verbosity,
		nested=nested,
		workers=n_workers,
		scheduled_in=(in_dir_quantification, in_dir_annotations),
		scheduled_out=out_dir,
	)
	return analysis_runner.run()


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
		self.name = "analysis"
		self.summary = pd.DataFrame()


	def search_quantification_file(
		self,
		dir: StrPath,
		quantification_file: StrPath = None,
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
		gnps_annotations: StrPath = None,
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
		:param gnps_annotations: Annotations of GNPS molecular feature finding, defaults to None
		:type gnps_annotations: StrPath, optional
		:return: Paths to files
		:rtype:  dict[str, StrPath]
		"""
		for root, dirs, files in os.walk(dir):
			for file in files:
				if not canopus_formula_summary_file and file == "canopus_formula_summary.tsv":
					canopus_formula_summary_file = join(root, file)
				elif not canopus_structure_summary_file and file == "canopus_structure_summary.tsv":
					canopus_structure_summary_file = join(root, file)
				elif (
					not denovo_structure_identifications_file
					and file == "denovo_structure_identifications.tsv"
				):
					denovo_structure_identifications_file = join(root, file)
				elif not formula_identifications_file and file == "formula_identifications.tsv":
					formula_identifications_file = join(root, file)
				elif not structure_identifications_file and file == "structure_identifications.tsv":
					structure_identifications_file = join(root, file)
				elif not gnps_annotations and file.endswith("_gnps_all_db_annotations.json"):
					gnps_annotations = join(root, file)
		return {
			"canopus_formula_summary_file": canopus_formula_summary_file,
			"canopus_structure_summary_file": canopus_structure_summary_file,
			"denovo_structure_identifications_file": denovo_structure_identifications_file,
			"formula_identifications_file": formula_identifications_file,
			"structure_identifications_file": structure_identifications_file,
			"gnps_annotations": gnps_annotations,
		}



	def read_sirius_df(self, file_path: StrPath, filter_columns: list|str) -> pd.DataFrame:
		df = pd.read_csv(file_path, sep="\t")
		df.replace("-Infinity", -np.inf, inplace=True)
		df.rename(columns={'mappingFeatureId': 'ID'})

		if isinstance(filter_columns, str):
			filter_columns = [column for column in df.columns if filter_columns in column]
		for filter_column in filter_columns:
			df[filter_column] = df[filter_column].replace(r",", r".", regex=True).astype(float)

		return df
	#

	def add_quantification(self, quantification_file: StrPath, summary: pd.DataFrame = None):
		df = pd.read_csv(quantification_file)
		df.columns = [column.replace("row ", "") for column in df.columns]
		
		if summary:
			summary.merge( df, how="outer" )
		else:
			summary = df

		summary = summary.sort_values("retention time", ascending=True)

		return summary


	def add_annotation(self, annotation_file: StrPath, annotation_file_type: str, summary: pd.DataFrame):
		match annotation_file_type:
			case "formula_identifications_file":
				df = self.read_sirius_df(file_path=annotation_file, filter_columns=["ZodiacScore"])
				df = df[["molecularFormula", "ZodiacScore"]]
				df.rename(columns={'molecularFormula': 'Sirius_formula',
					   			   "ZodiacScore": "Sirius_formula_confidence"})
				
			case "canopus_formula_summary_file":
				df = self.read_sirius_df(file_path=annotation_file, filter_columns=["Probability"])
				df = df[[column for column in df.columns
			 			 if (column.startswith("NPC") or column.startswith("ClassyFire"))
						    and not column.endswith("all classifications")]]
				
				rename_dict = {}
				for column in df.columns:
					tool, name = column.split("#", maxsplit=1)
					name = name.lower().replace(" ", "_").replace("probability", "confidence")
					rename_dict[column] = f"Sirius_formula_{tool}_{name}"
				df.rename(columns=rename_dict)

			case "structure_identifications_file":
				df = self.read_sirius_df(file_path=annotation_file, filter_columns=["ConfidenceScoreExact", "ConfidenceScoreApproximate"])
				df = df[["smiles", "links", "ConfidenceScoreExact", "ConfidenceScoreApproximate", "CSI:FingerIDScore"]]
				df.rename(columns={'smiles': 'Sirius_structure_smiles',
					   			   "links": "Sirius_structure_links",
					   			   "ConfidenceScoreExact": "Sirius_structure_confidence",
								   "ConfidenceScoreApproximate": "Sirius_approximate_structure_confidence",
								   "CSI:FingerIDScore": "Sirius_structure_CSI:FingerIDScore"})
				
			case "canopus_structure_summary_file":
				df = self.read_sirius_df(file_path=annotation_file, filter_columns=["Probability"])
				df = df[[column for column in df.columns
			 			 if (column.startswith("NPC") or column.startswith("ClassyFire"))
						    and not column.endswith("all classifications")]]
				
				rename_dict = {}
				for column in df.columns:
					tool, name = column.split("#", maxsplit=1)
					name = name.lower().replace(" ", "_").replace("probability", "confidence")
					rename_dict[column] = f"Sirius_structure_{tool}_{name}"
				df.rename(columns=rename_dict)

			case "denovo_structure_identifications_file":
				df = self.read_sirius_df(file_path=annotation_file, filter_columns=["ConfidenceScoreExact", "ConfidenceScoreApproximate"])
				df = df[["smiles", "CSI:FingerIDScore"]]
				df.rename(columns={'smiles': 'Sirius_structure_smiles',
								   "CSI:FingerIDScore": "Sirius_denovo_structure_CSI:FingerIDScore"})

			case "gnps_annotations":
				pass
		
		summary.merge( df, how="outer", on="ID")
		return summary



	def run_single(
		self,
		in_path_quantification: StrPath,
		in_path_annotation: StrPath,
		annotation_file_type: str,
		out_path: StrPath
		):
		"""
		Add the annotations into a quantification file.

		:param in_path: Path to scheduled file.
		:type in_path: str
		:param out_path: Path to output directory.
		:type out_path: str
		"""

		
		out_file_name = ".".join(os.path.basename(in_path).split(".")[:-1]) + self.target_format

		cmd = (
			rf'"{self.exec_path}" --{self.target_format[1:]} -e {self.target_format} --64 '
			+ rf'-o "{out_path}" --outfile "{out_file_name}" "{in_path}" {" ".join(self.additional_args)}'
		)

		if not os.path.isfile(out_path):
			out_path = os.path.join(out_path, out_file_name)

		super().compute(cmd=cmd, in_path=in_path, out_path=out_path)

	def run_directory(self, in_path_annotation: StrPath, in_path_quantification: StrPath, out_path: StrPath):
		"""
		Convert all matching files in a folder.

		:param in_path: Path to scheduled file.
		:type in_path: str
		:param out_path: Path to output directory.
		:type out_path: str
		"""
		quantification_file = self.search_quantification_file(dir=in_path_quantification)
		annotation_files = self.search_annotation_files(dir=in_path_annotation)

		for annotation_file_type, annotation_path in annotation_files.items():
			if annotation_path:
				self.run_single(in_path_quantification=quantification_file,
								in_path_annotation=annotation_path,
								annotation_file_type=annotation_file_type)


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

		for entry in tqdm(
			os.listdir(in_root_dir), disable=verbose_tqdm, desc="Schedule conversions"
		):
			entry_path = join(in_root_dir, entry)
			hypothetical_out_path = join(
				out_root_dir, helpers.replace_file_ending(entry, self.target_format)
			)
			in_valid, out_valid = self.select_for_conversion(
				in_path=entry_path, out_path=hypothetical_out_path
			)

			if in_valid and out_valid:
				if not made_out_root_dir:
					os.makedirs(out_root_dir, exist_ok=True)
					made_out_root_dir = True
				self.run_single(in_path=entry_path, out_path=out_root_dir)
			elif os.path.isdir(entry_path) and not in_valid:
				self.run_nested(
					in_root_dir=entry_path,
					out_root_dir=join(out_root_dir, entry),
					recusion_level=recusion_level + 1,
				)


if __name__ == "__main__":
	parser = argparse.ArgumentParser(
		prog="msconv_pipe.py",
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
	parser.add_argument("-msconv", "--analysis_arguments", required=False, nargs=argparse.REMAINDER)

	args, unknown_args = parser.parse_known_args()
	main(args=args, unknown_args=unknown_args)
