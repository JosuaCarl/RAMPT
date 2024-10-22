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
from source.helpers.classes import Pipe_Step


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
    out_dir         = args.out_dir          if args.out_dir else args.in_dir
    nested          = args.nested           if args.nested else False
    n_workers       = args.workers          if args.workers else 1
    save_out        = args.save_out         if args.save_out else False
    verbosity       = args.verbosity        if args.verbosity else 1
    additional_args = args.gnps_args        if args.gnps_args else unknown_args

    gnps_runner = GNPS_Runner( save_out=save_out, additional_args=additional_args)

    if nested:
        futures = gnps_runner.get_nested_gnps_results( root_dir=in_dir, out_root_dir=out_dir )
        computation_complete = compute_scheduled( futures=futures, num_workers=n_workers, verbose=verbosity >= 1)
    else:
        futures = gnps_runner.get_gnps_results( in_dir=in_dir, out_dir=out_dir )
    


class GNPS_Runner(Pipe_Step):
    def __init__( self, save_out:bool=False, additional_args:list=[], verbosity:int=1 ):
        super.__init__( save_out=save_out, additional_args=additional_args, verbosity=verbosity)
        self.mzmine_log_query   = "io.github.mzmine.modules.io.export_features_gnps.GNPSUtils submitFbmnJob GNPS FBMN/IIMN response: "



    def extract_json_from_output( self, work_path:StrPath, query:str, mzmine_log:str=None ) -> dict:
        if mzmine_log:
            for line in mzmine_log.split("\n"):
                if query in line:
                    response_json = line.split(query)[-1]
                    return json.loads(response_json) 
        else:
            with open( join(work_path, "mzmine_log.txt"), "r") as f:
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



    def check_task_finished( self, work_path:StrPath, mzmine_log:str=None ) -> tuple[str, bool]:
        gnps_response = self.extract_json_from_output( work_path=work_path,
                                                       query=self.mzmine_log_query, 
                                                       mzmine_log=mzmine_log )
            
        if gnps_response["status"] == "Success":
            task_id = gnps_response["task_id"]
        else:
            warnings.warn(f"{join(work_path, 'mzmine_log.txt')} reports an unsuccessful job submission to GNPS by mzmine.", UserWarning)
            self.post_gnps_request(work_path=work_path)
            
        url = f"https://gnps.ucsd.edu/ProteoSAFe/status_json.jsp?task={task_id}"
        return task_id, check_for_str_request( url=url, query='\"status\":\"DONE\"',
                                               retries=100, allowed_fails=10, expected_wait_time=600.0,
                                               timeout=5)


    def fetch_results( self, task_id:str, out_path:StrPath=None ):
        response = requests.get(f"https://gnps.ucsd.edu/ProteoSAFe/result_json.jsp?task={task_id}&view=view_all_annotations_DB")

        if out_path:
            with open(out_path, "w") as file:
                file.write(response.text)

        return json.loads(response.text)


    def check_dir_files( self, dir:StrPath ) -> tuple[bool, bool]:
        feature_ms2_found = False
        feature_quantification_found = False
        for root, dirs, files in os.walk(dir):
            for file in files:
                feature_ms2_found |= file.endswith("_iimn_fbmn.mgf")
                feature_quantification_found |= file.endswith("_iimn_fbmn_quant.csv")
        return feature_ms2_found, feature_quantification_found



    def get_gnps_results( self, in_dir:StrPath, out_dir:StrPath, mzmine_log:str=None):
        task_id, status = self.check_task_finished( work_path=in_dir,
                                                    mzmine_log=mzmine_log )
        if status:
            self.processed_in.append( in_dir )
            self.processed_in.append( out_dir )
            results_dict = self.fetch_results( task_id=task_id,
                                               out_path=join(out_dir, f"{basename(in_dir)}_gnps_all_db_annotations.json") )
            self.outs.append(results_dict)
            if self.verbosity >= 3:
                print(f"GNPS results {basename(in_dir)}:\n")
                print(f"task_id:{task_id}\n")
                print(results_dict)
            return results_dict

        else:
            raise BrokenPipeError(f"Status of {task_id} was not marked DONE.")


    def get_nested_gnps_results( self, root_dir:StrPath, out_root_dir:StrPath,
                                 futures:list=[], recusion_level:int=0) -> list:
        verbose_tqdm = self.verbosity >= recusion_level + 2
        for root, dirs, files in os.walk(root_dir):
            feature_ms2_found, feature_quantification_found = self.check_dir_files(dir=root)
            if feature_ms2_found and feature_quantification_found:
                os.makedirs(out_root_dir, exist_ok=True)
                futures.append( dask.delayed(self.get_gnps_results)( in_dir=root_dir, out_dir=out_root_dir ) )

            for dir in tqdm(dirs, disable=verbose_tqdm, desc="Directories"):
                futures = self.get_gnps_results( root_dir=join(root_dir, dir),
                                                    out_root_dir=join(out_root_dir, dir),
                                                    futures=futures, recusion_level=recusion_level+1 )
                    
            return futures



if __name__ == "__main__":
    parser = argparse.ArgumentParser( prog='gnps_pipe.py',
                                      description='Obtain anntations from MS2 feature networking by GNPS.')
    parser.add_argument('-in',      '--in_dir',             required=True)
    parser.add_argument('-out',     '--out_dir',            required=False)
    parser.add_argument('-n',       '--nested',             required=False,     action="store_true")
    parser.add_argument('-s',       '--save_out',           required=False,     action="store_true")
    parser.add_argument('-w',       '--workers',            required=False,     type=int)
    parser.add_argument('-v',       '--verbosity',          required=False,     type=int)
    parser.add_argument('-gnps',    '--gnps_args',          required=False,     nargs=argparse.REMAINDER)

    args, unknown_args = parser.parse_known_args()

    main(args=args, unknown_args=unknown_args)
