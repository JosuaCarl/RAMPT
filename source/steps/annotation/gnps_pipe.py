#!/usr/bin/env python3

"""
Use GNPS for anntating compounds.
"""

# Imports
import os
import argparse
import re
import json
import requests

from os.path import join, basename
from tqdm.auto import tqdm

from source.steps.general import *


def main(args: argparse.Namespace | dict, unknown_args: list[str] = []):
	"""
	Execute GNPS annotation.

	:param args: Command line arguments
	:type args: argparse.Namespace|dict
	:param unknown_args: Command line arguments that are not known.
	:type unknown_args: list[str]
	"""
	# Extract arguments
	in_dir = get_value(args, "in_dir")
	out_dir = get_value(args, "out_dir", in_dir)
	mzmine_log = get_value(args, "mzmine_log", in_dir)
	nested = get_value(args, "nested", False)
	n_workers = get_value(args, "workers", 1)
	save_log = get_value(args, "save_log", False)
	verbosity = get_value(args, "verbosity", 1)
	additional_args = get_value(args, "gnps_args", unknown_args)
	additional_args = additional_args if additional_args else unknown_args

	gnps_runner = GNPS_Runner(
		mzmine_log=mzmine_log,
		save_log=save_log,
		additional_args=additional_args,
		verbosity=verbosity,
		nested=nested,
		workers=n_workers,
		scheduled_in=in_dir,
		scheduled_out=out_dir,
	)
	return gnps_runner.run()


class GNPS_Runner(Pipe_Step):
	"""
	A runner for checking on the GNPS process and subsequently saving the results.
	"""

	def __init__(
		self,
		mzmine_log: list[StrPath] = None,
		resubmit: bool = True,
		save_log: bool = False,
		additional_args: list = [],
		verbosity: int = 1,
		**kwargs,
	):
		"""
		Initialize the GNPS_Runner.

		:param mzmine_log: Logfile from mzmine, defaults to None.
		:type mzmine_log: list[StrPath], optional
		:param resubmit: Whether to submit a GNPS feature networking, when not already done, defaults to True.
		:type resubmit: bool, optional
		:param save_log: Whether to save the output(s), defaults to False.
		:type save_log: bool, optional
		:param additional_args: Additional arguments for mzmine, defaults to []
		:type additional_args: list, optional
		:param verbosity: Level of verbosity, defaults to 1
		:type verbosity: int, optional
		"""
		super().__init__(save_log=save_log, additional_args=additional_args, verbosity=verbosity)
		if kwargs:
			self.update(kwargs)
		self.mzmine_log_query = "io.github.mzmine.modules.io.export_features_gnps.GNPSUtils submitFbmnJob GNPS FBMN/IIMN response: "
		self.mzmine_log = mzmine_log
		self.resubmit = resubmit
		self.name = "gnps"

	def query_response_iterator(self, query: str, iterator) -> dict:
		"""
		Query a response iterator for a query.

		:param query: Query to search for
		:type query: str
		:param iterator: Iterator to iterate through
		:type iterator: any
		:return: Loaded json of hit without query and filtered for first {} group
		:rtype: dict
		"""
		for line in iterator:
			if query in line:
				response_json = re.search(r"{.*}", line.replace(query, ""))[0]
				return json.loads(response_json)
		error(
			message=f"Query <{query}> was not found in mzmine_log: Please provide a valid string or path.",
			error=ValueError,
		)

	def extract_task_info(self, query: str, mzmine_log: StrPath = None) -> dict:
		"""
		Extract the information about the started GNPS task from the mzmin_log.

		:param query: Query to match the info against.
		:type query: str
		:param mzmine_log: Output of mzmine including GNPS POST request, or path to the file/including folder with standard naming (mzmine_log.txt), defaults to None
		:type mzmine_log: str, optional
		:return: Response from GNPS as a dictionary.
		:rtype: dict
		"""
		mzmine_log = join(mzmine_log, "mzmine_log.txt") if os.path.isdir(mzmine_log) else mzmine_log
		if os.path.isfile(mzmine_log):
			with open(mzmine_log, "r") as f:
				return self.query_response_iterator(query=query, iterator=f.readlines())
		else:
			return self.query_response_iterator(query=query, iterator=mzmine_log.split("\n"))

	def submit_to_gnps(
		self, feature_ms2_file: StrPath, feature_quantification_file: StrPath
	) -> str:
		# Read files
		files = {
			"featurems2": open(feature_ms2_file, "r"),
			"featurequantification": open(feature_quantification_file, "r"),
		}

		# enter parameters
		parameters = {
			"title": "Cool title",
			"featuretool": "MZMINE2",
			"description": "Job from mine2sirius",
		}
		# Submit job
		url = "https://gnps-quickstart.ucsd.edu/uploadanalyzefeaturenetworking"

		log(message=f"POSTing request to  {url}", minimum_verbosity=2, verbosity=self.verbosity)

		response = requests.api.post(url, data=parameters, files=files)

		log(
			message=f"POST request {response.request.url} returned status code {response.status_code}",
			minimum_verbosity=2,
			verbosity=self.verbosity,
		)

		# Check for finish
		task_id, status = self.check_task_finished(gnps_response=response.json())

		return task_id, status

	def check_task_finished(
		self, mzmine_log: str = None, gnps_response: dict = None
	) -> tuple[str, bool]:
		"""
		Check GNPS API for the status of the task.

		:param mzmine_log: Output of mzmine including GNPS POST request, defaults to None
		:type mzmine_log: str, optional
		:param gnps_response: Resonse from GNPS, defaults to None
		:type gnps_response: dict, optional
		:return: Task ID and whether the task was completed during search time
		:rtype: tuple[str, bool]
		"""
		if not gnps_response:
			gnps_response = self.extract_task_info(
				query=self.mzmine_log_query, mzmine_log=mzmine_log
			)

		if gnps_response["status"] == "Success":
			task_id = gnps_response["task_id"]
		else:
			error(
				message="mzmine_log reports an unsuccessful job submission to GNPS by mzmine.",
				error=ValueError,
			)

		url = f"https://gnps.ucsd.edu/ProteoSAFe/status_json.jsp?task={task_id}"
		return task_id, check_for_str_request(
			url=url,
			query='"status":"DONE"',
			retries=100,
			allowed_fails=10,
			expected_wait_time=600.0,
			timeout=5,
		)

	def fetch_results(self, task_id: str, out_path: StrPath = None) -> dict:
		"""
		Fetch all resulting annotations from a GNSP Task and optionally save it.

		:param task_id: Task ID from GNPS
		:type task_id: str
		:param out_path: Path for saving the output json, defaults to None
		:type out_path: StrPath, optional
		:return: Result as a dictionary
		:rtype: dict
		"""
		response = requests.get(
			f"https://gnps.ucsd.edu/ProteoSAFe/result_json.jsp?task={task_id}&view=view_all_annotations_DB"
		)

		if out_path:
			with open(out_path, "w") as file:
				file.write(response.text)

		return json.loads(response.text)

	def check_dir_files(
		self,
		dir: StrPath,
		feature_ms2_file: StrPath = None,
		feature_quantification_file: str = None,
	) -> tuple[StrPath, StrPath]:
		"""
		Check whether the needed files for GNPS POST request are present, according to mzmine naming scheme.

		:param dir: Directory to search in
		:type dir: StrPath
		:param feature_ms2_file: File with ms2 spectra (in .mgf format), defaults to None
		:type feature_ms2_file: StrPath, optional
		:param feature_quantification_file: File with quantification table (in .csv format), defaults to None
		:type feature_quantification_file: StrPath, optional
		:return: MS2 feature and feature quantification file
		:rtype: tuple[StrPath, StrPath]
		"""
		for root, dirs, files in os.walk(dir):
			for file in files:
				if not feature_ms2_file and file.endswith("_iimn_fbmn.mgf"):
					feature_ms2_file = join(root, file)
				elif not feature_quantification_file and file.endswith("_iimn_fbmn_quant.csv"):
					feature_quantification_file = join(root, file)
		return feature_ms2_file, feature_quantification_file

	def run_single(
		self,
		in_path: StrPath,
		out_path: StrPath = None,
		feature_ms2_file: StrPath = None,
		feature_quantification_file: str = None,
		mzmine_log: str = None,
		gnps_response: dict = None,
	):
		"""
		Get the GNPS results from a single path, mzmine_log or GNPS response.

		:param in_path: Input directory
		:type in_path: StrPath
		:param out_path: Output directory of result, defaults to None
		:type out_path: StrPath, optional
		:param feature_ms2_file: File with ms2 spectra (in .mgf format), defaults to None
		:type feature_ms2_file: StrPath, optional
		:param feature_quantification_file: File with quantification table (in .csv format), defaults to None
		:type feature_quantification_file: StrPath, optional
		:param mzmine_log: mzmine_log String containing GNPS response, defaults to None
		:type mzmine_log: str, optional
		:param gnps_response: GNPS response to POST request, defaults to None
		:type gnps_response: dict, optional
		:raises BrokenPipeError: When the task does not complete in the expected time
		"""
		if not mzmine_log:
			mzmine_log = self.mzmine_log if self.mzmine_log else in_path
		try:
			task_id, status = self.check_task_finished(
				mzmine_log=mzmine_log, gnps_response=gnps_response
			)
		except ValueError as ve:
			if self.resubmit:
				feature_ms2_file, feature_quantification_file = self.check_dir_files(
					dir=in_path,
					feature_ms2_file=feature_ms2_file,
					feature_quantification_file=feature_quantification_file,
				)
				gnps_response = self.submit_to_gnps(feature_ms2_file, feature_quantification_file)
				task_id, status = self.check_task_finished(
					mzmine_log=mzmine_log, gnps_response=gnps_response
				)
			else:
				error(message=str(ve), error=ValueError)

		if status:
			dir_name = (
				basename(in_path) if os.path.isdir(in_path) else basename(os.path.split(in_path)[0])
			)
			out_path = (
				join(out_path, f"{dir_name}_gnps_all_db_annotations.json") if out_path else None
			)
			results_dict = self.fetch_results(task_id=task_id, out_path=out_path)

			log(
				message=f"GNPS results {basename(in_path)}:\ntask_id:{task_id}\n{results_dict}",
				minimum_verbosity=3,
				verbosity=self.verbosity,
			)

			in_path = gnps_response if gnps_response else mzmine_log if mzmine_log else in_path

			cmd = f"echo 'fetched gnps results from {in_path}'"
			super().compute(cmd=cmd, in_path=in_path, out_path=out_path, results=results_dict)

		else:
			raise BrokenPipeError(f"Status of {task_id} was not marked DONE.")

	def run_directory(self, **kwargs):
		"""
		Pass on the directory to single case.
		"""
		self.run_single(**kwargs)

	def run_nested(self, in_root_dir: StrPath, out_root_dir: StrPath, recusion_level: int = 0):
		"""
		Construct a list of necessary computations for getting the GNPS results from a nested scheme of mzmine results.

		:param in_root_dir: Root input directory
		:type in_root_dir: StrPath
		:param out_root_dir: Root output directory
		:type out_root_dir: StrPath
		:param recusion_level: Current level of recursion, important for determination of level of verbose output, defaults to 0
		:type recusion_level: int, optional
		:return: Future computations
		:rtype: list
		"""
		verbose_tqdm = self.verbosity >= recusion_level + 2
		made_out_root_dir = False

		for root, dirs, files in os.walk(in_root_dir):
			feature_ms2_file, feature_quantification_file = self.check_dir_files(dir=root)
			if feature_ms2_file and feature_quantification_file:
				if not made_out_root_dir:
					os.makedirs(out_root_dir, exist_ok=True)
					made_out_root_dir = True
				self.run_single(
					in_path=in_root_dir,
					out_path=out_root_dir,
					feature_ms2_file=feature_ms2_file,
					feature_quantification_file=feature_quantification_file,
				)

			for dir in tqdm(dirs, disable=verbose_tqdm, desc="Directories"):
				self.run_nested(
					in_root_dir=join(in_root_dir, dir),
					out_root_dir=join(out_root_dir, dir),
					recusion_level=recusion_level + 1,
				)

	def run(self, in_paths: list = [], out_paths: list = [], mzmine_log: list = [], **kwargs):
		return super().run(in_paths=in_paths, out_paths=out_paths, mzmine_log=mzmine_log, **kwargs)


if __name__ == "__main__":
	parser = argparse.ArgumentParser(
		prog="gnps_pipe.py", description="Obtain anntations from MS2 feature networking by GNPS."
	)
	parser.add_argument("-in", "--in_dir", required=True)
	parser.add_argument("-out", "--out_dir", required=False)
	parser.add_argument("-log", "--mzmine_log", required=False)
	parser.add_argument("-n", "--nested", required=False, action="store_true")
	parser.add_argument("-s", "--save_log", required=False, action="store_true")
	parser.add_argument("-w", "--workers", required=False, type=int)
	parser.add_argument("-v", "--verbosity", required=False, type=int)
	parser.add_argument("-gnps", "--gnps_args", required=False, nargs=argparse.REMAINDER)

	args, unknown_args = parser.parse_known_args()

	main(args=args, unknown_args=unknown_args)
