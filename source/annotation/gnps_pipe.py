#!/usr/bin/env python3

"""
Use GNPS for anntating compounds.
"""

# Imports
import os
import argparse
import warnings
import json
import requests

from os.path import join, basename
from tqdm.auto import tqdm
from tqdm.dask import TqdmCallback
import dask.multiprocessing


from source.helpers.general import check_for_str_request, compute_scheduled
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
    in_dir          = args.in_dir
    out_dir         = args.out_dir
    nested          = args.nested           if args.nested else False
    n_workers       = args.workers          if args.workers else 1
    verbosity       = args.verbosity        if args.verbosity else 1
    additional_args = args.gnps_args        if args.gnps_args else unknown_args

    gnps_runner = GNPS_Runner()

    futures = gnps_runner.get_nested_gnps_results()
    computation_complete = compute_scheduled( futures=futures, num_workers=n_workers, verbose=verbosity >= 1)
    


class GNPS_Runner:
    def __init__(self, save_out:bool=False, additional_args:list=[], verbosity:int=1):
        self.additional_args    = additional_args
        self.verbosity          = verbosity
        self.save_out           = save_out
        self.mzmine_log_query   = "io.github.mzmine.modules.io.export_features_gnps.GNPSUtils\
                                   submitFbmnJob GNPS FBMN/IIMN response:"
        self.processed_in       = []
        self.processed_out      = []
        self.outs               = []
        self.errs               = []



    def extract_json_from_output( self, out_path:StrPath, query:str, mzmine_log:str=None ) -> dict:
        if mzmine_log:
            for line in mzmine_log.split("\n"):
                if query in line:
                    response_json = line.split(query)[-1]
                    return json.loads(response_json) 
        else:
            with open( join(out_path, "mzmine_log.txt"), "r") as f:
                for line in f.readlines():
                    if query in line:
                        response_json = line.split(query)[-1]
                        return json.loads(response_json)


    def post_gnps_request( self, out_path:StrPath ):
        # TODO: Add own version of POST request to GNPS
        """
        print("The job will be resubmitted to https://gnps-quickstart.ucsd.edu/uploadanalyzefeaturenetworking")
        requests.post( "https://gnps-quickstart.ucsd.edu/uploadanalyzefeaturenetworking",
                    data={ "featurems2": join(out_path, f"{os.path.basename(out_path)}_iimn_fbmn.mgf"),
                            "featurequantification": join(out_path, f"{os.path.basename(out_path)}_iimn_fbmn_quant.csv")})
        """
        pass



    def check_task_finished( self, out_path:StrPath, mzmine_log:str=None ) -> tuple[str, bool]:
        gnps_response = self. extract_json_from_output( out_path=out_path,
                                                        query=self.mzmine_log_query, 
                                                        mzmine_log=mzmine_log )
            
        if gnps_response["status"] == "Success":
            task_id = gnps_response["task_id"]
        else:
            warnings.warn(f"{join(out_path, 'mzmine_log.txt')} reports an unsuccessful job submission to GNPS by mzmine.", UserWarning)
            self.post_gnps_request(out_path=out_path)
            
        url = f"https://gnps.ucsd.edu/ProteoSAFe/status_json.jsp?task={task_id}"
        return task_id, check_for_str_request( url=url, query='\"status\":\"DONE\"',
                                               retries=100, allowed_fails=10, expected_wait_time=600.0,
                                               timeout=5)


    def fetch_results( self, task_id:str, out_path:StrPath=None ):
        response = requests.get(f"https://gnps.ucsd.edu/ProteoSAFe/result_json.jsp?task={task_id}&view=view_all_annotations_DB")
        
        if out_path:
            with open(out_path, "w") as file:
                file.write(response)

        return json.loads(response)


    def check_dir_files(dir:StrPath) -> tuple[bool, bool]:
        feature_ms2_found = False
        feature_quantification_found = False
        for root, dirs, files in os.walk(dir):
            for file in files:
                feature_ms2_found |= file.endswith("_iimn_fbmn.mgf")
                feature_quantification_found |= file.endswith("_iimn_fbmn_quant.csv")
        return feature_ms2_found, feature_quantification_found



    def get_gnps_results( self, out_path:StrPath, mzmine_log:str=None):
        task_id, status = self.check_task_finished( out_path=out_path,
                                                    mzmine_log=mzmine_log )
        if status:
            return self.fetch_results( task_id=task_id,
                                       out_path=join(out_path, f"{basename(out_path)}_gnps_all_db_annotations.json") )
        else:
            raise BrokenPipeError(f"Status of {task_id} was not marked DONE.")


    def get_nested_gnps_results( self, root_dir:StrPath, out_root_dir:StrPath,
                                 futures:list=[], original:bool=True) -> list:
        verbose_tqdm = self.verbosity < 2 if original else self.verbosity < 3

        for root, dirs, files in os.walk(root_dir):
            for dir in tqdm(dirs, disable=verbose_tqdm, desc="Directories"):
                feature_ms2_found, feature_quantification_found = self.check_dir_files(dir=dir)

                if feature_ms2_found and feature_quantification_found:
                    futures.append( dask.delayed(self.get_gnps_results)( out_path=join(out_root_dir, dir) ) )
                else:
                    futures = self.get_gnps_results( root_dir=join(root_dir, dir),
                                                     out_root_dir=join(out_root_dir, dir),
                                                     futures=futures, original=False )

            return futures



if __name__ == "__main__":
    parser = argparse.ArgumentParser( prog='mzmine_pipe.py',
                                      description='Obtain anntations from MS2 feature networking by GNPS.')
    parser.add_argument('-in',      '--in_dir',             required=True)
    parser.add_argument('-out',     '--out_dir',            required=True)
    parser.add_argument('-n',       '--nested',             required=False,     action="store_true")
    parser.add_argument('-s',       '--save_out',           required=False,     action="store_true")
    parser.add_argument('-w',       '--workers',            required=False,     type=int)
    parser.add_argument('-v',       '--verbosity',          required=False,     type=int)
    parser.add_argument('-gnps',    '--gnps_arguments',     required=False,     nargs=argparse.REMAINDER)

    args, unknown_args = parser.parse_known_args()

    main(args=args, unknown_args=unknown_args)
