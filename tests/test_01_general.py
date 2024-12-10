#!/usr/bin/env python
"""
Testing the conversion functions.
"""
from tests.common import *
from source.steps.general import *

platform = get_platform()
filepath = helpers.get_internal_filepath(__file__)
out_path, test_path, example_path = contruct_common_paths( filepath )



def test_step_configuration():
    clean_out( out_path )
    step_configuration = Step_Configuration( "test" )
    assert step_configuration.name == "test"
    assert step_configuration.patterns == {"in": ".*"}

    step_configuration = Step_Configuration( "test" )
    step_configuration.update( { "overwrite": False, "verbosity": 3 } )
    assert not step_configuration.overwrite
    assert step_configuration.verbosity == 3

    step_configuration.save( os.path.join(out_path, "step_config.json") )
    assert os.path.isfile( os.path.join(out_path, "step_config.json") )
    with open( os.path.join(out_path, "step_config.json"), "r" ) as file:
        step_config_dict = json.load( file )
        assert step_config_dict == step_configuration.dict_representation()
    
    step_configuration = Step_Configuration( "test" )
    assert step_configuration.name == "test"
    assert step_configuration.verbosity == 1
    assert step_configuration.overwrite

    step_configuration.load( os.path.join(out_path, "step_config.json") )
    assert step_configuration.verbosity == 3
    assert not step_configuration.overwrite



def test_pipe_step():
    clean_out( out_path )
    pipe_step = Pipe_Step( "test", exec_path="echo" )
    assert pipe_step.name == "test"

    assert not pipe_step.match_file_name(r"\.XML", "a.mzXML")




clean_out( out_path )