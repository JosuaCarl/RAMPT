#!/usr/bin/env python3

"""
Use Sirius to annotate compounds and extract matching formulae and chemical classes.
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



class Sirius_Runner(Pipe_Step):
    """
    A runner for SIRIUS annotation.
    """
    def __init__( self, save_out:bool=False, additional_args:list=[], verbosity:int=1 ):
        """
        Initialize the GNPS_Runner.

        :param save_out: Whether to save the output(s).
        :type save_out: bool, optional
        :param additional_args: Additional arguments for mzmine, defaults to []
        :type additional_args: list, optional
        :param verbosity: Level of verbosity, defaults to 1
        :type verbosity: int, optional
        """
        super().__init__( save_out=save_out, additional_args=additional_args, verbosity=verbosity)
        self.mzmine_log_query   = "io.github.mzmine.modules.io.export_features_gnps.GNPSUtils submitFbmnJob GNPS FBMN/IIMN response: "


if __name__ == "__main__":
    parser = argparse.ArgumentParser( prog='sirius_pipe.py',
                                      description='Obtain anntations from MS1 & MS2 feature annotation by SIRIUS.')
    parser.add_argument('-in',      '--in_dir',             required=True)
    parser.add_argument('-out',     '--out_dir',            required=False)
    parser.add_argument('-n',       '--nested',             required=False,     action="store_true")
    parser.add_argument('-s',       '--save_out',           required=False,     action="store_true")
    parser.add_argument('-w',       '--workers',            required=False,     type=int)
    parser.add_argument('-v',       '--verbosity',          required=False,     type=int)
    parser.add_argument('-gnps',    '--gnps_args',          required=False,     nargs=argparse.REMAINDER)

    args, unknown_args = parser.parse_known_args()

    main(args=args, unknown_args=unknown_args)
