#!/usr/bin/env python

"""
Analysis of feature quantification and annotation.
"""

import os
import argparse

import pandas as pd
import numpy as np

from os.path import join
from tqdm.auto import tqdm

import source.helpers as helpers
from source.helpers.types import StrPath
from source.steps.general import Pipe_Step, get_value
from source.steps.analysis.statistics import *

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
		scheduled_in=in_dir,
		scheduled_out=out_dir,
	)
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
		super().__init__(save_log=save_log, additional_args=additional_args, verbosity=verbosity)
		if kwargs:
			self.update(kwargs)
		self.overwrite = overwrite
		self.name = "analysis"
		self.analysis = None



	def build_z_score(self, summary: pd.DataFrame):
		pass


	def analyze_difference(self, summary: pd.DataFrame):
		pass


	def complete_analysis(self, summary: pd.DataFrame, analysis: pd.DataFrame):
		pass



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
		"""
		summary = summary if summary else self.summary
		in_path_quantification, in_path_annotation = self.sort_in_paths(in_paths=in_path)
		out_path = join(out_path, "summary.tsv") if os.path.isdir(out_path) else out_path

		summary = self.add_quantification(
			quantification_file=in_path_quantification, summary=summary
		)
		summary = self.add_annotation(
			annotation_file=in_path_annotation,
			annotation_file_type=annotation_file_type,
			summary=summary,
		)

		summary.to_csv(out_path, sep="\t")

		cmd = f"echo 'Added annotation from {in_path_annotation} to {in_path_quantification}'"

		super().compute(
			cmd=cmd, in_path=(in_path_quantification, in_path_annotation), out_path=out_path
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
		"""
		summary = summary if summary else self.summary
		in_path_quantification, in_path_annotation = self.sort_in_paths(in_paths=in_path)
		out_path = join(out_path, "summary.tsv") if os.path.isdir(out_path) else out_path

		if not quantification_file:
			quantification_file = self.search_quantification_file(dir=in_path_quantification)
		if not annotation_files:
			annotation_files = self.search_annotation_files(dir=in_path_annotation)

		summary = self.add_quantification(quantification_file=quantification_file, summary=summary)
		summary = self.add_annotations(annotation_files=annotation_files, summary=summary)

		summary.to_csv(out_path, sep="\t")

		cmd = f"echo 'Added annotation from {in_path_annotation} to {in_path_quantification}'"

		super().compute(
			cmd=cmd, in_path=(in_path_quantification, in_path_annotation), out_path=out_path
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
	parser.add_argument("-msconv", "--analysis_arguments", required=False, nargs=argparse.REMAINDER)

	args, unknown_args = parser.parse_known_args()
	main(args=args, unknown_args=unknown_args)
