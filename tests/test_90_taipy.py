#!/usr/bin/env python
"""
Testing the SIRIUS annotation.
"""
from tests.common import *
import source.helpers.general as helpers
from source.gui.pages.root import *

from taipy.gui import Gui, State
from taipy.core.submission.submission_status import SubmissionStatus


platform = get_platform()
filepath = helpers.get_internal_filepath(__file__)
out_path, test_path, example_path, batch_path, taipy_work_path = contruct_common_paths( filepath, taipy=True )

pages = { "/": '<|toggle|theme|><center><|navbar|lov={[("/", "Application"), ("https://josuacarl.github.io/mine2sirius_pipe", "Documentation")]}|></center>',
          "configuration": root }


# TODO: Set namespace instead of state
def load_params( state, path:StrPath=None, scenario_name:str="Default" ):
    path = path if path else os.path.join(work_dir_root, f"{scenario_name}_config.json")
    with open( path, "r" ) as file:
       params = json.loads( file.read() )

    for segment_name, segment_params in params.items():
        for attribute, param in segment_params.items():
            set_attribute_recursive(state, f"{segment_name}.{attribute}", param, refresh=True)

# TODO: Set namespace instead of state
def construct_params_dict( state, param_segment_names:list=param_segment_names ):
    params = {}
    for segment_name in param_segment_names:
        segment_params = get_attribute_recursive(state, f"{segment_name}_params")
        params[f"{segment_name}_params"] = segment_params.dict_representation()
    return params

match_data_node = { # IO Data
                    "raw_data": [ "conversion_params.scheduled_in" ],
                   
                    "community_formatted_data": [ "feature_finding_params.scheduled_in",
                                                  "conversion_params.processed_out" ],

                    "processed_data": [ "gnps_params.scheduled_in",
                                        "sirius_params.scheduled_in",
                                        "feature_finding_params.processed_out" ],

                    "gnps_annotations": [ "analysis_params.scheduled_in",
                                          "gnps_params.processed_out" ],

                    "sirius_annotations": [ "analysis_params.scheduled_in",
                                            "sirius_params.processed_out" ],

                    "results": [ "analysis_params.processed_out" ],

                    # Batches and more
                    "mzmine_batch": [ "feature_finding_params.batch" ],

                    "mzmine_log": [ "feature_finding_params.log_paths",
                                    "gnps_params.mzmine_log" ] ,

                    "sirius_config": [ "sirius_params.config" ],

                    "sirius_projectspace": [ "sirius_params.projectspace" ],  }


def update_scenario( state, scenario ):

    params = construct_params_dict( state )
    
    data_nodes = params.copy()

    for data_node_key, attribute_keys in match_data_node.items():
        for state_attribute in attribute_keys:
            attribute_split = state_attribute.split(".")
            value = params.get(attribute_split[0]).get(attribute_split[1])
            if value:
                for state_attribute in attribute_keys:
                    set_attribute_recursive( state, state_attribute, value, refresh=True)
                data_nodes[data_node_key] = value

    for key, data_node in scenario.data_nodes.items():
        if data_nodes.get(key):
            data_node.write( data_nodes.get(key) )

    return scenario



def test_taipy_simple_scenario():
    gui = Gui( pages=pages )
    ic(gui.get_state())
    flask_instance = gui.run(title="test", run_server=False )

    ic(gui.get_state())

    state = flask_instance.__getstate__()
    ic(state)

    state = load_params( state=state, path=os.path.join(batch_path, "Example_parameters.json") )
    scenario = update_scenario( state=state, scenario=scenario )

    orchestrator = tp.Orchestrator()
    orchestrator.run(force_restart=True)
    
    scenario.data_nodes.get("raw_data").write( os.path.join( taipy_work_path, "raw", "example_pos.mzML" ) )

    scenario.data_nodes.get("mzmine_batch").write( os.path.join( batch_path, "minmal.mzbatch" ) )
    scenario.data_nodes.get("sirius_config").write( os.path.join( batch_path, "sirius_config.txt" ) )

    submission = tp.submit(scenario)
    for i in range(30):
        if submission.submission_status == SubmissionStatus.COMPLETED:
            break
        wait( 1, "minute")

    assert submission.submission_status == SubmissionStatus.COMPLETED



def test_taipy_nested_parallel_scenario():
    gui = Gui( pages=pages )
    gui.run(title="test", design=False, run_browser=False, run_server=False )

    load_params(state=gui.state, path=os.path.join(batch_path, "Example_parameters_nested_parallel.json") )
    lock_scenario( state=gui.state )
    
    scenario = gui.state.scenario

    orchestrator = tp.Orchestrator()
    orchestrator.run(force_restart=True)
    
    scenario.data_nodes.get("raw_data").write( os.path.join( taipy_work_path, "raw", "example_pos.mzML" ) )

    scenario.data_nodes.get("mzmine_batch").write( os.path.join( batch_path, "minmal.mzbatch" ) )
    scenario.data_nodes.get("sirius_config").write( os.path.join( batch_path, "sirius_config.txt" ) )

    submission = tp.submit(scenario)
    for i in range(30):
        if submission.submission_status == SubmissionStatus.COMPLETED:
            break
        wait( 1, "minute")

    assert submission.submission_status == SubmissionStatus.COMPLETED



def test_clean():
    clean_out( taipy_work_path )
    os.mkdir( os.path.join( taipy_work_path, "raw") )
    shutil.copyfile( os.path.join( example_path, "example_pos.mzML"), os.path.join( taipy_work_path, "raw", "example_pos.mzML" ) )