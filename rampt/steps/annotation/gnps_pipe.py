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

from os.path import join

from ..general import *


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
    )
    if nested:
        gnps_runner.scheduled_ios = {
            "in_paths": {"processed_data_paths": in_dir},
            "out_path": {"gnps_annotated_data_paths": out_dir},
            "run_style": "nested",
        }
    else:
        gnps_runner.scheduled_ios = {
            "in_paths": {"processed_data_paths": in_dir},
            "out_path": {"gnps_annotated_data_paths": out_dir},
        }
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
        self.data_ids = {
            "in_paths": [
                "mzmine_log",
                "feature_quantification",
                "feature_ms2",
                "additional_pairs",
                "sample_metadata",
            ],
            "out_path": ["gnps_annotated_data_paths"],
            "standard": ["processed_data_paths"],
        }
        super().__init__(
            patterns={
                self.data_ids["in_paths"][0]: r".*mzmine_log",
                self.data_ids["in_paths"][1]: r".*fbmn_quant",
                self.data_ids["in_paths"][2]: r".*fbmn",
                self.data_ids["in_paths"][3]: r".*fbmn_edges_msannotation",
                self.data_ids["in_paths"][4]: r".*metadata",
            },
            mandatory_patterns={
                self.data_ids["in_paths"][0]: r".*\.txt$",
                self.data_ids["in_paths"][1]: r".*\.csv$",
                self.data_ids["in_paths"][2]: r".*\.mgf$",
                self.data_ids["in_paths"][3]: r".*\.csv$",
                self.data_ids["in_paths"][4]: r".*\.csv$",
            },
            valid_runs=[
                {
                    "single from log": {
                        "in_paths": {
                            "mzmine_log": lambda val: isinstance(val, str)
                            and os.path.isfile(val)
                            or (isinstance(val, list) and len(val) == 1 and os.path.isfile(val[0]))
                        },
                        "out_path": {"gnps_annotated_data_paths": lambda val: isinstance(val, str)},
                    }
                },
                {
                    "single from data all": {
                        "in_paths": {
                            "feature_quantification": lambda val: isinstance(val, str)
                            and os.path.isfile(val)
                            or (isinstance(val, list) and len(val) == 1 and os.path.isfile(val[0])),
                            "feature_ms2": lambda val: isinstance(val, str)
                            and os.path.isfile(val)
                            or (isinstance(val, list) and len(val) == 1 and os.path.isfile(val[0])),
                            "additional_pairs": lambda val: (not val)
                            or isinstance(val, str)
                            and os.path.isfile(val)
                            or (isinstance(val, list) and len(val) == 1 and os.path.isfile(val[0])),
                            "sample_metadata": lambda val: (not val)
                            or isinstance(val, str)
                            and os.path.isfile(val)
                            or (isinstance(val, list) and len(val) == 1 and os.path.isfile(val[0])),
                        },
                        "out_path": {"gnps_annotated_data_paths": lambda val: isinstance(val, str)},
                    }
                },
                {
                    "single from data minimum": {
                        "in_paths": {
                            "feature_quantification": lambda val: isinstance(val, str)
                            and os.path.isfile(val)
                            or (isinstance(val, list) and len(val) == 1 and os.path.isfile(val[0])),
                            "feature_ms2": lambda val: isinstance(val, str)
                            and os.path.isfile(val)
                            or (isinstance(val, list) and len(val) == 1 and os.path.isfile(val[0])),
                        },
                        "out_path": {"gnps_annotated_data_paths": lambda val: isinstance(val, str)},
                    }
                },
                {
                    "directory": {
                        "in_paths": {
                            "processed_data_paths": lambda val: isinstance(val, str)
                            and os.path.isdir(val)
                            or (isinstance(val, list) and len(val) == 1 and os.path.isdir(val[0]))
                        },
                        "out_path": {"gnps_annotated_data_paths": lambda val: isinstance(val, str)},
                    }
                },
                {
                    "multiple directories from log": {
                        "in_paths": {
                            "mzmine_log": lambda val: isinstance(val, str)
                            and os.path.isdir(val)
                            or (isinstance(val, list) and len(val) == 1 and os.path.isdir(val[0]))
                        },
                        "out_path": {"gnps_annotated_data_paths": lambda val: isinstance(val, str)},
                    }
                },
                {
                    "multiple directories from data all": {
                        "in_paths": {
                            "feature_quantification": lambda val: isinstance(val, str)
                            and os.path.isdir(val)
                            or (isinstance(val, list) and len(val) == 1 and os.path.isdir(val[0])),
                            "feature_ms2": lambda val: isinstance(val, str)
                            and os.path.isdir(val)
                            or (isinstance(val, list) and len(val) == 1 and os.path.isdir(val[0])),
                            "additional_pairs": lambda val: (not val)
                            or isinstance(val, str)
                            and os.path.isdir(val)
                            or (isinstance(val, list) and len(val) == 1 and os.path.isdir(val[0])),
                            "sample_metadata": lambda val: (not val)
                            or isinstance(val, str)
                            and os.path.isdir(val)
                            or (isinstance(val, list) and len(val) == 1 and os.path.isdir(val[0])),
                        },
                        "out_path": {"gnps_annotated_data_paths": lambda val: isinstance(val, str)},
                    }
                },
                {
                    "multiple directories from  minimum": {
                        "in_paths": {
                            "feature_quantification": lambda val: isinstance(val, str)
                            and os.path.isdir(val)
                            or (isinstance(val, list) and len(val) == 1 and os.path.isdir(val[0])),
                            "feature_ms2": lambda val: isinstance(val, str)
                            and os.path.isdir(val)
                            or (isinstance(val, list) and len(val) == 1 and os.path.isdir(val[0])),
                        },
                        "out_path": {"gnps_annotated_data_paths": lambda val: isinstance(val, str)},
                    }
                },
                {
                    "nested": {
                        "in_paths": {
                            "processed_data_paths": lambda val: (
                                isinstance(val, list) and all([os.path.isdir(v) for v in val])
                            )
                            or (isinstance(val, str) and os.path.isdir(val))
                        },
                        "out_path": {"gnps_annotated_data_paths": lambda val: isinstance(val, str)},
                    }
                },
            ],
            save_log=save_log,
            additional_args=additional_args,
            verbosity=verbosity,
        )
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
        logger.log(
            message=f"Query <{query}> was not found in mzmine_log: Please provide a valid string or path.",
            minimum_verbosity=2,
            verbosity=self.verbosity,
        )
        return None

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

        if gnps_response and gnps_response["status"] == "Success":
            task_id = gnps_response["task_id"]
        else:
            logger.log(
                message="mzmine_log reports an unsuccessful job submission to GNPS by mzmine.",
                minimum_verbosity=2,
                verbosity=self.verbosity,
            )
            return None, None

        url = f"https://gnps.ucsd.edu/ProteoSAFe/status_json.jsp?task={task_id}"
        return task_id, check_for_str_request(
            url=url,
            query_success='"status":"DONE"',
            query_failed='"status":"FAILED"',
            query_running='"status":"RUNNING"',
            retries=180,
            allowed_fails=5,
            retry_time=20.0,
            timeout=5,
            verbosity=self.verbosity,
        )

    def fetch_results(self, task_id: str) -> dict:
        """
        Fetch all resulting annotations from a GNSP Task and optionally save it.

        :param task_id: Task ID from GNPS
        :type task_id: str
        :return: Result as a dictionary
        :rtype: dict
        """
        response = requests.get(
            f"https://gnps.ucsd.edu/ProteoSAFe/result_json.jsp?task={task_id}&view=view_all_annotations_DB"
        )

        return response.json()

    def submit_to_gnps(self, **paths) -> str:
        # Open files and adjust naming
        files = {name.replace("_", ""): open(path, "r") for name, path in paths.items() if path}

        if "featurems2" not in files or "featurequantification" not in files:
            logger.error(
                message=f"{files} did not contain featurems2 and featurequantification.",
                error_type=ValueError,
            )

        # Enter parameters
        parameters = {
            "title": "Cool title",
            "featuretool": "MZMINE2",
            "description": "Job from RAMPT",
        }

        # Submit job
        url = "https://gnps-quickstart.ucsd.edu/uploadanalyzefeaturenetworking"

        logger.log(
            message=f"POSTing request to {url}", minimum_verbosity=2, verbosity=self.verbosity
        )

        response = requests.api.post(url, data=parameters, files=files, timeout=120.0)

        # Close opened files after upload
        for file in files.values():
            file.close()

        # Logging
        if response.status_code == 200:
            logger.log(
                message=f"POST request {response.request.url} returned status code {response.status_code}",
                minimum_verbosity=2,
                verbosity=self.verbosity,
            )
        else:
            logger.error(
                message=f"POST request {response.request.url} returned status code {response.status_code}",
                error_type=ConnectionError,
            )

        # Check for finish
        task_id, status = self.check_task_finished(gnps_response=response.json())

        return task_id, status

    def gnps_check_resubmit(self, in_out: dict[str, StrPath]):
        """
        Get the GNPS results from a single path, mzmine_log or GNPS response.

        :param in_out: Input directory
        :type in_out: dict[str, StrPath]
        :raises BrokenPipeError: When the task does not complete in the expected time
        """
        in_paths = in_out["in_paths"]
        out_path = get_if_dict(in_out["out_path"], self.data_ids["out_path"])

        # Use MZmine GNPS submit, if existent
        mzmine_log, gnps_response = self.extract_optional(
            in_paths, keys=["mzmine_log", "gnps_response"]
        )
        if mzmine_log or gnps_response:
            task_id, status = self.check_task_finished(
                mzmine_log=mzmine_log, gnps_response=gnps_response
            )
        # Own GNPS FBMN submission
        if not status:
            if self.resubmit:
                if self.data_ids["standard"][0] in in_paths:
                    standard_dir = self.extract_standard(
                        in_paths=in_paths, standard_value=self.data_ids["standard"][0]
                    )
                    in_files = self.match_dir_paths(dir=standard_dir)
                else:
                    in_files = self.extract_optional(
                        in_paths,
                        [
                            "feature_ms2",
                            "feature_quantification",
                            "additional_pairs",
                            "sample_metadata",
                        ],
                        return_dict=True,
                    )
                if any(in_files):
                    task_id, status = self.submit_to_gnps(**in_files)
                else:
                    logger.warn(f"No files found in {in_paths}.")

        if status:
            # Obtain results
            results_dict = self.fetch_results(task_id=task_id)

            # Save file
            out_path = self.extract_standard(out_path=out_path)
            if os.path.isdir(out_path):
                out_path = join(out_path, "fbmn_all_db_annotations.json")
            with open(out_path, "w") as file:
                json.dump(results_dict, file)

            logger.log(
                f"Successful FBMN run with data from {gnps_response if gnps_response else mzmine_log if mzmine_log else in_paths}",
                minimum_verbosity=2,
                verbosity=self.verbosity,
            )

        else:
            logger.warn(f"Status of {task_id} was not marked DONE. The FBMN run was unsuccessful.")

    # RUN
    def run_single(self, in_paths: dict[str, StrPath], out_path: dict[str, StrPath], **kwargs):
        """
        Get the GNPS results from a single path, mzmine_log or GNPS response.

        :param in_paths: Input directory
        :type in_paths: dict[str, StrPath]
        :param out_path: Output directory of result, defaults to None
        :type out_path: dict[str, StrPath], optional
        """
        out_path = get_if_dict(out_path, self.data_ids["out_path"])
        if os.path.isdir(out_path):
            out_path = join(out_path, "fbmn_all_db_annotations.json")

        self.compute(
            step_function=capture_and_log,
            func=self.gnps_check_resubmit,
            in_out=dict(in_paths=in_paths, out_path={self.data_ids["out_path"][0]: out_path}),
            log_path=self.get_log_path(out_path=out_path),
        )

    def run_directory(self, in_paths: dict[str, StrPath], out_path: dict[str, StrPath], **kwargs):
        """
        Pass on the directory to single case.
        """
        out_path = get_if_dict(out_path, self.data_ids["out_path"])

        # Special case "standard" as summary of file_types
        in_paths = self.fill_dict_standards(
            dictionary=in_paths,
            replacement_keys=self.data_ids["in_paths"],
            standards_key=self.data_ids["standard"][0],
        )

        # Search for valid files
        matched_in_paths = {}
        for file_type, path in in_paths.items():
            path = to_list(path)[0]
            if file_type in self.data_ids["in_paths"]:
                # Catch files
                if os.path.isfile(path):
                    matched_in_paths[file_type] = path
                else:
                    # Search directories
                    for entry in os.listdir(path):
                        if self.match_path(pattern=file_type, path=entry):
                            matched_in_paths[file_type] = join(path, entry)

        if matched_in_paths:
            os.makedirs(out_path, exist_ok=True)
            self.run_single(in_paths=matched_in_paths, out_path=out_path, **kwargs)
        else:
            logger.warn(
                message=f"Found no matched_in_paths={matched_in_paths}, inferred from in_paths={in_paths}"
            )

    def run_nested(
        self,
        in_paths: dict[str, StrPath],
        out_path: dict[str, StrPath],
        recusion_level: int = 0,
        **kwargs,
    ):
        """
        Construct a list of necessary computations for getting the GNPS results from a nested scheme of mzmine results.

        :param in_paths: Root input directory
        :type in_paths: dict[str, StrPath]
        :param out_path: Root output directory
        :type out_path: dict[str, StrPath]
        :param recusion_level: Current level of recursion, important for determination of level of verbose output, defaults to 0
        :type recusion_level: int, optional
        :return: Future computations
        :rtype: list
        """
        in_paths = to_list(get_if_dict(in_paths, self.data_ids["standard"]))
        out_path = get_if_dict(out_path, self.data_ids["out_path"])

        for in_path in in_paths:
            root, dirs, files = next(os.walk(in_path))

            dirs_with_matches = {}
            for file_type, pattern in self.patterns.items():
                for file in files:
                    if self.match_path(pattern=file_type, path=file):
                        dirs_with_matches[file_type] = in_path

            if dirs_with_matches:
                self.run_directory(in_paths=dirs_with_matches, out_path=out_path, **kwargs)

            for dir in dirs:
                self.run_nested(
                    in_paths=join(in_path, dir),
                    out_path=join(out_path, dir),
                    recusion_level=recusion_level + 1,
                    **kwargs,
                )


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
