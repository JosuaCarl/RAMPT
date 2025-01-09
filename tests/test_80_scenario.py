#!/usr/bin/env python
"""
Testing the configuration of taipy scenario.
"""
from tests.common import *
from source.gui.pages.root import *

from taipy.core.submission.submission_status import SubmissionStatus


platform = get_platform()
filepath = get_internal_filepath(__file__)
out_path, mock_path, example_path, batch_path = contruct_common_paths(filepath)
make_out(out_path)


def test_search_files():
	clean_out(out_path)

	# Superficial testing of run_single
	summary_runner = Summary_Runner()