#!/usr/bin/env python
"""
Testing the conversion functions.
"""
from tests.common import *
from source.conversion.msconv_pipe import *
from source.conversion.msconv_pipe import main as msconv_pipe_main
from bs4 import BeautifulSoup

platform = get_platform()
filepath = helpers.get_internal_filepath(__file__)
out_path, test_path, example_path = contruct_common_paths( filepath )



def test_msconv_pipe_compute():
    # Superficial testing of compute
    file_converter = File_Converter( platform=platform, target_format=".mzML",
                                     pattern=".*", save_log=False, verbosity=3,
                                     nested=False, workers=1 )
    
    file_converter.compute( in_path=join(test_path, "minimal_file.mzML"),
                            out_path=out_path )
    
    assert os.path.isfile( join(out_path, "minimal_file.mzML") )
    assert not os.path.exists( join(out_path, "nested_test_folder") )

    clean_out( out_path )

    # Second test with concrete path
    file_converter.compute( in_path=join(test_path, "minimal_file.mzML"),
                            out_path=join(out_path, "minimal_file.mzML") )
    
    assert os.path.isfile( join(out_path, "minimal_file.mzML") )

    clean_out( out_path )


def test_msconv_pipe_compute_directory():
    # Superficial testing of compute_directory
    file_converter = File_Converter( platform=platform, target_format=".mzML",
                                     pattern=".*", save_log=False, verbosity=3,
                                     nested=False, workers=1 )
    
    file_converter.compute_directory( in_path=test_path,
                                      out_path=out_path )
    
    assert os.path.isfile( join(out_path, "minimal_file.mzML") )
    assert not os.path.exists( join(out_path, "nested_test_folder") )

    clean_out( out_path )


def test_msconv_pipe_compute_nested():
    # Superficial testing of compute_nested
    file_converter = File_Converter( platform=platform, target_format=".mzML",
                                     pattern=".*", save_log=False, verbosity=3,
                                     nested=False, workers=1 )
    
    file_converter.compute_nested( in_path=test_path,
                                   out_path=out_path )
    
    assert os.path.isfile( join(out_path, "minimal_file.mzML") )
    assert os.path.exists( join(out_path, "nested_test_folder") )
    assert os.path.isfile( join(out_path, "nested_test_folder", "minimal_file.mzML") )

    clean_out( out_path )


def test_msconv_pipe_run():
    # Superficial testing of run
    file_converter = File_Converter( platform=platform, target_format=".mzML",
                                     pattern=".*", save_log=False, verbosity=3,
                                     nested=False, workers=1 )
    
    file_converter.run( in_path=[test_path],
                        out_path=[out_path] )
    
    assert file_converter.processed_in == [test_path]
    assert file_converter.processed_out == [out_path]
    assert os.path.isfile( join(out_path, "minimal_file.mzML") )

    clean_out( out_path )


    file_converter.run( in_path=[test_path],
                        out_path=[out_path] )
    
    assert file_converter.processed_in == [test_path]
    assert file_converter.processed_out == [out_path]
    assert os.path.isfile( join(out_path, "minimal_file.mzML") )

    clean_out( out_path )


def test_msconv_pipe_run_nested():
    # Superficial testing of run
    file_converter = File_Converter( platform=platform, target_format=".mzML",
                                     pattern=".*", save_log=False, verbosity=3,
                                     nested=False, workers=1 )
    
    file_converter.run( in_path=[test_path],
                        out_path=[out_path] )
    
    assert file_converter.processed_in == [test_path]
    assert file_converter.processed_out == [out_path]
    assert os.path.isfile( join(out_path, "minimal_file.mzML") )

    clean_out( out_path )


    file_converter.run( in_path=[test_path],
                        out_path=[out_path] )
    
    assert file_converter.processed_in == [test_path]
    assert file_converter.processed_out == [out_path]
    assert os.path.isfile( join(out_path, "minimal_file.mzML") )

    clean_out( out_path )


def test_msconv_pipe_main():
    # Exact testing of main method
    args = argparse.Namespace(in_dir=test_path,
                              out_dir=out_path,
                              pattern="", target_format="mzML", suffix=".mzML", prefix=None, contains=None,
                              redo_threshold=0.0, overwrite=None, workers=None, nested=True,
                              platform=platform, verbosity=3, msconv_arguments=None, save_log=False)
    msconv_pipe_main( args, unknown_args=[] )
    
    assert os.path.isfile( join(out_path, "minimal_file.mzML") )
    assert os.path.isfile( join(out_path, "nested_test_folder", "minimal_file.mzML") )

    with open( join(out_path, "minimal_file.mzML") ) as f:
        data = f.read()
        data = BeautifulSoup(data, "xml")
        file = data.find("sourceFile")
        assert os.path.join( file.get('location'),  file.get('name') ) ==  "file:///" + helpers.construct_path(filepath, "..", "test_files", "minimal_file.mzML")
    
    args.target_format = "mzXML"
    args.suffix = ".mzXML"
    msconv_pipe_main(args, unknown_args=[])
    
    assert os.path.isfile( join(out_path, "minimal_file.mzXML") )
    assert os.path.isfile( join(out_path, "nested_test_folder", "minimal_file.mzXML") )

    with open(helpers.construct_path(filepath, "..", "out", "minimal_file.mzXML")) as f:
        data = f.read()
        data = BeautifulSoup(data, "xml")
        file = data.find("parentFile")
        print( helpers.construct_path(filepath, "..", "test_files/minimal_file.mzXML") )
        assert file.get('fileName') ==  "file:///" + test_path + "/" + "minimal_file.mzXML" # <- mzXML path is wrong for windows

    clean_out( out_path )