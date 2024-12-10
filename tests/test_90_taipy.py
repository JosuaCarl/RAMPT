#!/usr/bin/env python
"""
Testing the SIRIUS annotation.
"""
from tests.common import *
import source.helpers.general as helpers
from source.gui.main import *


platform = get_platform()
filepath = helpers.get_internal_filepath(__file__)
out_path, test_path, example_path, batch_path = contruct_common_paths( filepath )

def test_gui_main():
    orchestrator = tp.Orchestrator()
    orchestrator.run(force_restart=True)
