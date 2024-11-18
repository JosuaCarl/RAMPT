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
from source.helpers.classes import Pipe_Step, get_value, set_value


def main(args:argparse.Namespace|dict, unknown_args:list[str]=[]):
    """
    Execute the conversion.

    :param args: Command line arguments
    :type args: argparse.Namespace|dict
    :param unknown_args: Command line arguments that are not known.
    :type unknown_args: list[str]
    """
    # Extract arguments
    in_dir          = get_value(args, "in_dir")
    out_dir         = get_value(args, "out_dir",    in_dir)
    nested          = get_value(args, "nested",     False) 
    n_workers       = get_value(args, "workers",    1 )
    save_log        = get_value(args, "save_log",   False )
    verbosity       = get_value(args, "verbosity",  1 )
    additional_args = get_value(args, "gnps_args",  unknown_args )
    additional_args = additional_args if additional_args else unknown_args

    gnps_runner = GNPS_Runner( save_log=save_log, additional_args=additional_args, verbosity=verbosity,
                               nested=nested, workers=n_workers,
                               scheduled_in=in_dir, scheduled_out=out_dir )
    return gnps_runner.run()
    


class GNPS_Runner(Pipe_Step):
    """
    A runner for checking on the GNPS process and subsequently saving the results.
    """
    def __init__( self, save_log:bool=False, additional_args:list=[], verbosity:int=1, **kwargs ):
        """
        Initialize the GNPS_Runner.

        :param save_log: Whether to save the output(s).
        :type save_log: bool, optional
        :param additional_args: Additional arguments for mzmine, defaults to []
        :type additional_args: list, optional
        :param verbosity: Level of verbosity, defaults to 1
        :type verbosity: int, optional
        """
        super().__init__( save_log=save_log, additional_args=additional_args, verbosity=verbosity)
        if kwargs:
            self.update(kwargs)
        self.mzmine_log_query   = "io.github.mzmine.modules.io.export_features_gnps.GNPSUtils submitFbmnJob GNPS FBMN/IIMN response: "


    def extract_task_info( self, query:str, work_path:StrPath=None, mzmine_log:str=None ) -> dict:
        """
        Extract the information about the started GNPS task from the mzmin_log.

        :param query: Query to match the info against.
        :type query: str
        :param work_path: Path where mzmine.log can be found (only needed if no mzmin_log is provided).
        :type work_path: StrPath
        :param mzmine_log: Output of mzmine including GNPS POST request, defaults to None
        :type mzmine_log: str, optional
        :return: Response from GNPS as a dictionary.
        :rtype: dict
        """
        if mzmine_log:
            for line in mzmine_log.split("\n"):
                if query in line:
                    response_json = line.split(query)[-1]
                    return json.loads(response_json) 
        elif work_path:
            log_path = work_path if os.path.isfile(work_path) else join(work_path, "mzmine_log.txt")
            with open( log_path, "r") as f:
                for line in f.readlines():
                    if query in line:
                        response_json = line.split(query)[-1]
                        return json.loads(response_json)
        else:
            raise(ValueError("You must provide either a work_path with mzmine_log.txt or mzmine_log as a string."))
        
        raise(ValueError(f"Query <{query}> was not found at the path {work_path} or in mzmine_log"))


    def post_gnps_request( self, work_path:StrPath ):
        # TODO: Add own version of POST request to GNPS
        # print("The job will be resubmitted to https://gnps-quickstart.ucsd.edu/uploadanalyzefeaturenetworking")
        # requests.post( "https://gnps-quickstart.ucsd.edu/uploadanalyzefeaturenetworking",
        #             data={ "featurems2": join(out_path, f"{os.path.basename(out_path)}_iimn_fbmn.mgf"),
        #                     "featurequantification": join(out_path, f"{os.path.basename(out_path)}_iimn_fbmn_quant.csv")})
        pass



    def check_task_finished( self, work_path:StrPath, mzmine_log:str=None, gnps_response:dict=None ) -> tuple[str, bool]:
        """
        Check GNPS API for the status of the task.

        :param work_path: Path where mzmine.log can be found (only needed if no mzmin_log is provided)
        :type work_path: StrPath
        :param mzmine_log: Output of mzmine including GNPS POST request, defaults to None
        :type mzmine_log: str, optional
        :param gnps_response: Resonse from GNPS, defaults to None
        :type gnps_response: dict, optional
        :return: Task ID and whether the task was completed during search time
        :rtype: tuple[str, bool]
        """
        if not gnps_response:
            gnps_response = self.extract_task_info( work_path=work_path,
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


    def fetch_results( self, task_id:str, out_path:StrPath=None ) -> dict:
        """
        Fetch all resulting annotations from a GNSP Task and optionally save it.

        :param task_id: Task ID from GNPS
        :type task_id: str
        :param out_path: Path for saving the output json, defaults to None
        :type out_path: StrPath, optional
        :return: Result as a dictionary
        :rtype: dict
        """
        response = requests.get(f"https://gnps.ucsd.edu/ProteoSAFe/result_json.jsp?task={task_id}&view=view_all_annotations_DB")

        if out_path:
            with open(out_path, "w") as file:
                file.write(response.text)

        return json.loads(response.text)


    def check_dir_files( self, dir:StrPath ) -> tuple[bool, bool]:
        """
        Check whether the needed files for GNPS POST request are present, according to mzmine naming scheme.

        :param dir: Directory to search in
        :type dir: StrPath
        :return: MS2 feature and feature quantification file presence
        :rtype: tuple[bool, bool]
        """
        feature_ms2_found = False
        feature_quantification_found = False
        for root, dirs, files in os.walk(dir):
            for file in files:
                feature_ms2_found |= file.endswith("_iimn_fbmn.mgf")
                feature_quantification_found |= file.endswith("_iimn_fbmn_quant.csv")
        return feature_ms2_found, feature_quantification_found



    def compute( self, in_path:StrPath=None, out_path:StrPath=None, mzmine_log:str=None, gnps_response:dict=None) -> dict:
        """
        Get the GNPS results from a single path, mzmine_log or GNPS response.

        :param in_path: Input directory, defaults to None
        :type in_path: StrPath, optional
        :param out_path: Output directory of result
        :type out_path: StrPath
        :param mzmine_log: mzmine_log String containing GNPS response, defaults to None
        :type mzmine_log: str, optional
        :param gnps_response: GNPS response to POST request, defaults to None
        :type gnps_response: dict, optional
        :raises BrokenPipeError: When the task does not complete in the expected time
        :return: Resulting anntations dictionary
        :rtype: dict
        """
        task_id, status = self.check_task_finished( work_path=in_path,
                                                    mzmine_log=mzmine_log,
                                                    gnps_response=gnps_response )
        if status:
            out_path = join(out_path, f"{basename(in_path)}_gnps_all_db_annotations.json") if out_path else None
            results_dict = self.fetch_results( task_id=task_id,
                                               out_path=out_path )
            self.outs.append( results_dict )
            if self.verbosity >= 3:
                print(f"GNPS results {basename(in_path)}:\n")
                print(f"task_id:{task_id}\n")
                print(results_dict)
            
            self.processed_in.append( gnps_response if gnps_response else mzmine_log if mzmine_log else in_path )
            self.processed_out.append( out_path )

            return results_dict

        else:
            raise BrokenPipeError(f"Status of {task_id} was not marked DONE.")


    def compute_nested( self, in_root_dir:StrPath, out_root_dir:StrPath,
                        futures:list=[], recusion_level:int=0) -> list:
        """
        Construct a list of necessary computations for getting the GNPS results from a nested scheme of mzmine results.

        :param in_root_dir: Root input directory
        :type in_root_dir: StrPath
        :param out_root_dir: Root output directory
        :type out_root_dir: StrPath
        :param futures: Future computations for parallelization, defaults to []
        :type futures: list, optional
        :param recusion_level: Current level of recursion, important for determination of level of verbose output, defaults to 0
        :type recusion_level: int, optional
        :return: Future computations
        :rtype: list
        """
        verbose_tqdm = self.verbosity >= recusion_level + 2
        for root, dirs, files in os.walk(in_root_dir):
            feature_ms2_found, feature_quantification_found = self.check_dir_files(dir=root)
            if feature_ms2_found and feature_quantification_found:
                os.makedirs(out_root_dir, exist_ok=True)
                futures.append( dask.delayed(self.compute)( in_path=in_root_dir, out_path=out_root_dir ) )

            for dir in tqdm(dirs, disable=verbose_tqdm, desc="Directories"):
                futures = self.compute_nested( in_root_dir=join(in_root_dir, dir),
                                               out_root_dir=join(out_root_dir, dir),
                                               futures=futures, recusion_level=recusion_level+1 )
                    
        return futures



if __name__ == "__main__":
    parser = argparse.ArgumentParser( prog='gnps_pipe.py',
                                      description='Obtain anntations from MS2 feature networking by GNPS.')
    parser.add_argument('-in',      '--in_dir',             required=True)
    parser.add_argument('-out',     '--out_dir',            required=False)
    parser.add_argument('-n',       '--nested',             required=False,     action="store_true")
    parser.add_argument('-s',       '--save_log',           required=False,     action="store_true")
    parser.add_argument('-w',       '--workers',            required=False,     type=int)
    parser.add_argument('-v',       '--verbosity',          required=False,     type=int)
    parser.add_argument('-gnps',    '--gnps_args',          required=False,     nargs=argparse.REMAINDER)

    args, unknown_args = parser.parse_known_args()

    main(args=args, unknown_args=unknown_args)
