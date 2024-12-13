#!/usr/bin/env python
"""
Testing the feature finding functions.
"""
from tests.common import *
import source.helpers as helpers
from source.steps.feature_finding.mzmine_pipe import *
from source.steps.feature_finding.mzmine_pipe import main as mzmine_pipe_main

import pandas as pd

platform = get_platform()
filepath = helpers.get_internal_filepath(__file__)
out_path, test_path, example_path, batch_path = contruct_common_paths( filepath )
make_out( out_path )

user = "joca" # NEEDS TO BE EDITED FOR TESTING TO WORK
login = f"--user {user}"



def test_mzmine_pipe_run_single():
    clean_out( out_path )

    # Superficial testing of run_single
    mzmine_runner = MZmine_Runner( batch=join( batch_path, "minimal.mzbatch" ), login=login )
    
    mzmine_runner.run_single( in_path=join(example_path, "example_pos.mzML"), out_path=out_path )
    
    assert os.path.isfile( join( out_path, "out_iimn_fbmn_quant.csv") )
    assert os.path.isfile( join( out_path, "out_sirius.mgf") )



def test_mzmine_pipe_run_directory():
    clean_out( out_path )
    # Supoerficial testing of run_directory
    mzmine_runner = MZmine_Runner( batch=join( batch_path, "minimal.mzbatch" ), login=login )
    
    mzmine_runner.run_directory( in_path=example_path, out_path=out_path )

    assert os.path.isfile( join( out_path, "out_iimn_fbmn_quant.csv") )
    assert os.path.isfile( join( out_path, "out_sirius.mgf") )



def test_mzmine_pipe_run_nested():
    clean_out( out_path )
    # Superficial testing of run_nested
    mzmine_runner = MZmine_Runner( batch=join( batch_path, "minimal.mzbatch" ), login=login )
    
    mzmine_runner.run_nested( example_path, out_path )
    
    with open( join( out_path, "source_files.txt"), "r") as file:
        source_files = file.read().split("\n")
        assert source_files[0].endswith( "example_neg.mzXML" )
        assert source_files[1].endswith( "example_pos.mzML" )
    
    with open( join( out_path, "example_nested", "source_files.txt"), "r") as file:
        source_files = file.read().split("\n")
        assert source_files[0].endswith( join( "example_nested", "example_neg.mzML" ) )
        
    assert os.path.isfile( join( out_path, "out_iimn_fbmn_quant.csv") ) 
    assert os.path.isfile( join( out_path, "example_nested", "example_nested_iimn_fbmn_quant.csv") ) 
    


def test_mzmine_pipe_run():
    clean_out( out_path )

    # Superficial testing of run
    mzmine_runner = MZmine_Runner( batch=join( batch_path, "minimal.mzbatch" ), login=login, workers=2 )
    
    mzmine_runner.run( in_paths=[example_path], out_paths=[out_path] )
    mzmine_runner.compute_futures()

    assert mzmine_runner.processed_in == [ join(example_path, "example_neg.mzXML"), join(example_path, "example_pos.mzML") ]
    assert mzmine_runner.processed_out == [ out_path, out_path ]



def test_mzmine_pipe_main():
    clean_out( out_path )
    args = argparse.Namespace( mzmine_path=None,
                               in_dir=example_path,
                               out_dir=out_path,
                               batch=join( batch_path, "minimal.mzbatch" ),
                               valid_formats=["mzML"],
                               user=user, nested=True, platform=platform, save_log=False,
                               verbosity=3, mzmine_arguments=None)
    mzmine_pipe_main(args, unknown_args=[])
    
    assert os.path.isfile( join( out_path, "source_files.txt") )
    assert os.path.isfile( join( out_path, "example_nested", "source_files.txt") )

    with open( join( out_path, "source_files.txt"), "r" ) as f:
        text = f.read()
        assert text == str( join( example_path, "example_pos.mzML") )

    assert os.path.isfile( join( out_path, "example_nested", "example_nested_iimn_fbmn_quant.csv") )
    df = pd.read_csv( join( out_path, "example_nested", "example_nested_iimn_fbmn_quant.csv") )
    assert "row retention time" in df.columns

    del df
    del text



def test_clean():
    clean_out( out_path )