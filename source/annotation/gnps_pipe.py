#!/usr/bin/env python3

"""
Use GNPS for anntating compounds.
"""

# Imports
import warnings
import json
from os.path import join
from source.helpers.general import check_for_str_request
from source.helpers.types import StrPath


def main(args, unknown_args):
    """
    Execute the conversion.

    :param args: Command line arguments
    :type args: any
    :param unknown_args: Command line arguments that are not known.
    :type unknown_args: any
    """
    # Extract arguments
    mzmine_path     = args.mzmine_path      if args.mzmine_path else None
    in_dir          = args.in_dir
    out_dir         = args.out_dir
    batch_path      = args.batch_path
    valid_formats   = args.valid_formats    if args.valid_formats else ["mzML", "mzXML", "imzML"]
    user            = args.user             if args.user else None
    nested          = args.nested           if args.nested else False
    platform        = args.platform         if args.platform else "windows"
    gnps_pipe       = args.gnps_pipe        if args.gnps_pipe else False
    verbosity       = args.verbosity        if args.verbosity else 1
    additional_args = args.mzmine_arguments if args.mzmine_arguments else unknown_args


def filter_cmd_output(out_path:StrPath, query:str) -> dict:
    with open( join(out_path, "out.txt"), "r") as f:
        for line in f.readlines():
            if query in line:
                response_json = line.split(query)[-1]
                return json.loads(response_json)

def check_task_finished(out_path=StrPath):
    gnps_response = filter_cmd_output(out_path=out_path, query="io.github.mzmine.modules.io.export_features_gnps.GNPSUtils submitFbmnJob GNPS FBMN/IIMN response:")
    if gnps_response["status"] == "Success":
        task_id = gnps_response["task_id"]
    else:
        warnings.warn(f"{join(out_path, "out.txt")} reports an unsuccessful job submission to GNPS by mzmine.", UserWarning)
        print("The job will be resubmitted to ")
    url = f"https://gnps.ucsd.edu/ProteoSAFe/status_json.jsp?task={task_id}"
    return check_for_str_request(url=url, query='\"status\":\"DONE\"', retries=100, allowed_fails=10, expected_wait_time=600.0, timeout=5)


def 



