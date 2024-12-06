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
import dask.multiprocessing


from source.helpers.general import check_for_str_request
from source.helpers.types import StrPath
from source.steps.general import Pipe_Step, get_value


def main(args:argparse.Namespace|dict, unknown_args:list[str]=[]):
    """
    Execute GNPS annotation.

    :param args: Command line arguments
    :type args: argparse.Namespace|dict
    :param unknown_args: Command line arguments that are not known.
    :type unknown_args: list[str]
    """
    # Extract arguments
    in_dir          = get_value(args, "in_dir")
    out_dir         = get_value(args, "out_dir",    in_dir)
    mzmine_log      = get_value(args, "mzmine_log", in_dir)
    nested          = get_value(args, "nested",     False) 
    n_workers       = get_value(args, "workers",    1 )
    save_log        = get_value(args, "save_log",   False )
    verbosity       = get_value(args, "verbosity",  1 )
    additional_args = get_value(args, "gnps_args",  unknown_args )
    additional_args = additional_args if additional_args else unknown_args

    gnps_runner = GNPS_Runner( mzmine_log=mzmine_log,
                               save_log=save_log, additional_args=additional_args, verbosity=verbosity,
                               nested=nested, workers=n_workers,
                               scheduled_in=in_dir, scheduled_out=out_dir )
    return gnps_runner.run()
    


class GNPS_Runner(Pipe_Step):
    """
    A runner for checking on the GNPS process and subsequently saving the results.
    """
    def __init__( self, mzmine_log:list[StrPath]=None, save_log:bool=False, additional_args:list=[], verbosity:int=1, **kwargs ):
        """
        Initialize the GNPS_Runner.

        :param mzmine_log: Logfile from mzmine, defaults to None.
        :type mzmine_log: list[StrPath], optional
        :param save_log: Whether to save the output(s), defaults to False.
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
        self.mzmine_log         = mzmine_log



    def query_response_iterator( self, query:str, iterator ) -> dict:
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

        raise(ValueError(f"Query <{query}> was not found in mzmine_log: Please provide a valid string or path."))

    def extract_task_info( self, query:str, mzmine_log:StrPath=None ) -> dict:
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
        if os.path.isfile( mzmine_log ):
            with open( mzmine_log, "r") as f:
                return self.query_response_iterator( query=query, iterator=f.readlines())
        else:
            return self.query_response_iterator( query=query, iterator=mzmine_log.split("\n"))


    def check_task_finished( self, mzmine_log:str=None, gnps_response:dict=None ) -> tuple[str, bool]:
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
            gnps_response = self.extract_task_info( query=self.mzmine_log_query, 
                                                    mzmine_log=mzmine_log )

        if gnps_response["status"] == "Success":
            task_id = gnps_response["task_id"]
        else:
            raise(ValueError("mzmine_log reports an unsuccessful job submission to GNPS by mzmine."))

        url = f"https://gnps.ucsd.edu/ProteoSAFe/status_json.jsp?task={task_id}"
        return task_id, check_for_str_request( url=url, query='\"status\":\"DONE\"',
                                               retries=100, allowed_fails=10, expected_wait_time=600.0,
                                               timeout=5 )


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



    def compute( self, in_path:StrPath, out_path:StrPath=None, mzmine_log:str=None, gnps_response:dict=None ) -> dict:
        """
        Get the GNPS results from a single path, mzmine_log or GNPS response.

        :param in_path: Input directory
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
        if not mzmine_log:
            mzmine_log = self.mzmine_log if self.mzmine_log else in_path
        task_id, status = self.check_task_finished( mzmine_log=mzmine_log,
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


    def run(self, in_paths:list=[], out_paths:list=[], mzmine_log:list=[], **kwargs ):
        return super().run( in_paths=in_paths, out_paths=out_paths, mzmine_log=mzmine_log, **kwargs )




if __name__ == "__main__":
    parser = argparse.ArgumentParser( prog='gnps_pipe.py',
                                      description='Obtain anntations from MS2 feature networking by GNPS.')
    parser.add_argument('-in',      '--in_dir',             required=True)
    parser.add_argument('-out',     '--out_dir',            required=False)
    parser.add_argument('-log',     '--mzmine_log',         required=False)
    parser.add_argument('-n',       '--nested',             required=False,     action="store_true")
    parser.add_argument('-s',       '--save_log',           required=False,     action="store_true")
    parser.add_argument('-w',       '--workers',            required=False,     type=int)
    parser.add_argument('-v',       '--verbosity',          required=False,     type=int)
    parser.add_argument('-gnps',    '--gnps_args',          required=False,     nargs=argparse.REMAINDER)

    args, unknown_args = parser.parse_known_args()

    main(args=args, unknown_args=unknown_args)
