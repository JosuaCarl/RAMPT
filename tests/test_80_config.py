#!/usr/bin/env python
"""
Testing the configuration of taipy scenario.
"""

from tests.common import *
from source.gui.configuration.config import *

from source.steps.general import Pipe_Step


platform = get_platform()
filepath = get_internal_filepath(__file__)
out_path, mock_path, example_path, batch_path = contruct_common_paths(filepath)
make_out(out_path)


def test_generic_step():
	try:
		generic_step(step_class=Pipe_Step, step_params={}, global_params={})
	except TypeError:
		assert True

	try:
		generic_step(
			step_class=Pipe_Step, step_params={"scheduled_in": "fake/path"}, global_params={}
		)
	except TypeError:
		assert True


def test_convert_files():
	clean_out(out_path)

	convert_files(
		raw_data=join(example_path, "minimal.mzML"),
		conversion_out=out_path,
		step_params={},
		global_params={},
	)
	assert os.path.isfile(join(out_path, "minimal.mzML"))


def test_find_features():
	clean_out(out_path)

	find_features(
		community_formatted_data=join(example_path, "minimal.mzML"),
		feature_finding_out=out_path,
		step_params={},
		global_params={},
	)

	assert os.path.isfile(join(out_path, "out_iimn_fbmn_quant.csv"))


def test_annotate_gnps():
	clean_out(out_path)

	annotate_gnps(
		processed_data=join(example_path, "example_files_iimn_fbmn.mgf"),
		mzmine_log=join(example_path, "mzmine_log.txt"),
		gnps_out=out_path,
		step_params={},
		global_params={},
	)

	assert os.path.isfile(join(out_path, "out_gnps_all_db_annotations.json"))


def test_annotate_sirius():
	clean_out(out_path)

	annotate_sirius(
		processed_data=join(example_path, "example_files_sirius.mgf"),
		sirius_out=out_path,
		config=join(batch_path, "sirius_config.txt"),
		step_params={},
		global_params={},
	)

	assert os.path.isfile(join(out_path, "out_gnps_all_db_annotations.json"))


def test_summarize_annotations():
	clean_out(out_path)

	summarize_annotations(
		processed_data=example_path,
		gnps_annotated_data=example_path,
		sirius_annotated_data=example_path,
		summary_out=out_path,
		step_params={},
		global_params={},
	)

	assert os.path.isfile(join(out_path, "out_gnps_all_db_annotations.json"))


def test_analyze_difference():
	analyze_difference()
	pass
