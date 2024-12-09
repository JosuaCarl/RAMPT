#!/usr/bin/env python
"""
Testing the conversion functions.
"""
from tests.common import *
from source.steps.conversion.msconv_pipe import *
from source.steps.conversion.msconv_pipe import main as msconv_pipe_main
from bs4 import BeautifulSoup

platform = get_platform()
filepath = helpers.get_internal_filepath(__file__)
out_path, test_path, example_path = contruct_common_paths( filepath )



def test_msconv_pipe_compute():
    clean_out( out_path )

    # Superficial testing of compute
    file_converter = File_Converter( platform=platform, target_format=".mzML",
                                     save_log=False, verbosity=3,
                                     nested=False, workers=1 )
    
    file_converter.compute( in_path=join(test_path, "minimal_file.mzML"),
                            out_path=out_path )
    
    assert os.path.isfile( join(out_path, "minimal_file.mzML") )
    assert not os.path.exists( join(out_path, "nested_test_folder") )



def test_msconv_pipe_compute_directory():
    clean_out( out_path )

    # Superficial testing of compute_directory
    file_converter = File_Converter( platform=platform, target_format=".mzML",
                                     pattern=".*", save_log=False, verbosity=3,
                                     nested=False, workers=1 )
    
    file_converter.compute_directory( in_path=test_path,
                                      out_path=out_path )
    
    assert os.path.isfile( join(out_path, "minimal_file.mzML") )
    assert not os.path.exists( join(out_path, "nested_test_folder") )



def test_msconv_pipe_compute_nested():
    clean_out( out_path )
    # Superficial testing of compute_nested
    file_converter = File_Converter( platform=platform, target_format=".mzML",
                                     suffix=".mzML", save_log=False, verbosity=1,
                                     nested=True, workers=1 )
    
    futures = file_converter.compute_nested( in_root_dir=test_path,
                                               out_root_dir=out_path )
    helpers.compute_scheduled( futures=futures, num_workers=file_converter.workers, verbose=file_converter.verbosity >= 1)
    
    assert file_converter.processed_out == [ join(out_path, "minimal_file.mzML"), join(out_path, "nested_test_folder", "minimal_file.mzML") ]
    assert os.path.isfile( join(out_path, "minimal_file.mzML") )
    assert os.path.exists( join(out_path, "nested_test_folder") )
    assert os.path.isfile( join(out_path, "nested_test_folder", "minimal_file.mzML") )



def test_msconv_pipe_run():
    clean_out( out_path )

    # Superficial testing of run
    file_converter = File_Converter( platform=platform, target_format=".mzML",
                                     suffix=".mzML", save_log=False, verbosity=3,
                                     overwrite=True, nested=False, workers=1 )
    
    file_converter.run( in_paths=[test_path],
                        out_paths=[out_path] )
    
    assert file_converter.processed_in == [join(test_path, "minimal_file.mzML")]
    assert file_converter.processed_out == [join(out_path, "minimal_file.mzML")]
    assert os.path.isfile( join(out_path, "minimal_file.mzML") )

    clean_out( out_path )

    print("specific RUN")
    # Specific run
    file_converter.run( in_paths=[join(test_path, "minimal_file.mzML")],
                        out_paths=[out_path] )
    
    assert file_converter.processed_in == [join(test_path, "minimal_file.mzML")]
    assert file_converter.processed_out == [join(out_path, "minimal_file.mzML")]
    assert os.path.isfile( join(out_path, "minimal_file.mzML") )


def test_msconv_pipe_run_nested():
    clean_out( out_path )
    # Superficial testing of nested run
    file_converter = File_Converter( platform=platform, target_format=".mzXML",
                                     pattern=r".*\.mzML$", save_log=False, verbosity=3,
                                     nested=True, workers=1 )
    
    file_converter.run( in_paths=[test_path],
                        out_paths=[out_path] )

    assert file_converter.processed_in == [join(test_path, "minimal_file.mzML"), join(test_path, "nested_test_folder", "minimal_file.mzML")]
    assert file_converter.processed_out == [join(out_path, "minimal_file.mzXML"), join(out_path, "nested_test_folder", "minimal_file.mzXML")]
    assert os.path.isfile( join(out_path, "minimal_file.mzXML") )
    assert os.path.isfile( join(out_path, "nested_test_folder", "minimal_file.mzXML") )
    assert not os.path.exists( join(out_path, "empty_nested_test_folder") )



def test_msconv_pipe_main():
    clean_out( out_path )
    # Exact testing of main method
    args = argparse.Namespace(in_dir=test_path, out_dir=out_path,
                              pattern="", target_format="mzML", suffix=".mzML", prefix=None, contains=None,
                              redo_threshold=0.0, overwrite=None, workers=4, nested=True,
                              platform=platform, verbosity=1, msconv_arguments=None, save_log=False)
    msconv_pipe_main( args, unknown_args=[] )
    
    assert os.path.isfile( join(out_path, "minimal_file.mzML") )
    assert os.path.isfile( join(out_path, "nested_test_folder", "minimal_file.mzML") )

    with open( join(out_path, "minimal_file.mzML") ) as f:
        data = f.read()
        data = BeautifulSoup(data, "xml")
        file = data.find("sourceFile")
        assert os.path.join( file.get('location'),  file.get('name') ) ==  "file:///" + helpers.construct_path(filepath, "..", "test_files", "minimal_file.mzML")
    
    args.target_format = "mzXML"
    args.suffix = ".mzX?ML"
    msconv_pipe_main(args, unknown_args=[])
    
    assert os.path.isfile( join(out_path, "minimal_file.mzXML") )
    assert os.path.isfile( join(out_path, "nested_test_folder", "minimal_file.mzXML") )

    with open(helpers.construct_path(filepath, "..", "out", "minimal_file.mzXML")) as f:
        data = f.read()
        data = BeautifulSoup(data, "xml")
        file = data.find("parentFile")
        assert file.get('fileName') ==  "file:///" + test_path + "/" + "minimal_file.mzXML" # <- mzXML path is wrong for windows (fault with msconvert)


def test_clean_out():
    """
    Clean out leftover data in output folder.
    """
    clean_out( out_path )