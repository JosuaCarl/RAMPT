#!/usr/bin/env python
"""
Testing the data analysis.
"""
from tests.common import *
import source.helpers as helpers
from source.steps.analysis.analysis_pipe import *
from source.steps.analysis.analysis_pipe  import main as analysis_pipe_main


platform = get_platform()
filepath = helpers.get_internal_filepath(__file__)
out_path, test_path, example_path, batch_path = contruct_common_paths( filepath )
make_out( out_path )



def test_analysis_pipe_run_single():
    clean_out( out_path )

    # Superficial testing of run_single
    analysis_runner = Analysis_Runner( mzmine_log=join( example_path, "mzmine_log.txt") )
    
    analysis_runner.run_single( in_path=join( example_path, "mzmine_log.txt"), out_path=out_path )
    
    assert os.path.isfile( join(out_path, f"{basename(example_path)}_analysis_all_db_annotations.json") )



def test_analysis_pipe_run_directory():
    clean_out( out_path )
    # Supoerficial testing of run_directory
    analysis_runner = Analysis_Runner( mzmine_log=example_path )
    
    analysis_runner.run_directory( in_path=example_path, out_path=out_path )

    assert os.path.isfile( join(out_path, f"{basename(example_path)}_analysis_all_db_annotations.json") )



def test_analysis_pipe_run_nested():
    clean_out( out_path )
    # Superficial testing of run_nested
    analysis_runner = Analysis_Runner()
    
    analysis_runner.run_nested( example_path, out_path )
    
    assert os.path.isfile( join( out_path, f"{basename(example_path)}_analysis_all_db_annotations.json") )
    assert os.path.isfile( join( out_path, "example_nested", "example_nested_analysis_all_db_annotations.json") ) 
    


def test_analysis_pipe_run():
    clean_out( out_path )

    # Superficial testing of run
    analysis_runner = Analysis_Runner( workers=2 )
    
    analysis_runner.run( in_paths=[example_path], out_paths=[out_path] )
    analysis_runner.compute_futures()

    assert analysis_runner.processed_in == [ example_path ]
    assert analysis_runner.processed_out == [ join( out_path, f"{basename(example_path)}_analysis_all_db_annotations.json") ]



def test_analysis_pipe_main():
    args = argparse.Namespace( in_dir=example_path,
                               out_dir=out_path,
                               nested=True, workers=1, save_log=True,
                               verbosity=0, analysis_args=None )
    
    analysis_pipe_main( args, unknown_args=[] )
    
    assert os.path.isfile( join( out_path, "example_files_analysis_all_db_annotations.json" ) )
    assert os.path.isfile( join( out_path, "example_nested", "example_nested_analysis_all_db_annotations.json" ) )



def test_clean():
    clean_out( out_path )
