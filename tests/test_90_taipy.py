#!/usr/bin/env python
"""
Testing the SIRIUS annotation.
"""
from tests.common import *
import source.helpers.general as helpers
from source.gui.pages.root import *

from taipy.gui import Gui
from taipy.core.submission.submission_status import SubmissionStatus


platform = get_platform()
filepath = helpers.get_internal_filepath(__file__)
out_path, test_path, example_path, batch_path, taipy_work_path = contruct_common_paths( filepath, taipy=True )

pages = { "/": '<|toggle|theme|><center><|navbar|lov={[("/", "Application"), ("https://josuacarl.github.io/mine2sirius_pipe", "Documentation")]}|></center>',
          "configuration": root }



def test_taipy_simple_scenario():
    gui = Gui( pages=pages )
    ic(gui)
    ic(gui.state)
    gui.run(title="test", design=False, run_browser=False, port=5009 )
    
    ic(gui)
    ic(gui.state)

    load_params(state=gui.state, path=os.path.join(batch_path, "Example_parameters.json") )
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



def test_taipy_nested_parallel_scenario():
    gui = Gui( pages=pages )
    gui.run(title="test", design=False, run_browser=False, port=5009 )

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