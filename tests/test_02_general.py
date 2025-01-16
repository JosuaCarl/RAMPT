#!/usr/bin/env python
"""
Testing the conversion functions.
"""

from rampt.steps.general import *
from tests.common import *

platform = get_platform()
filepath = get_internal_filepath(__file__)
out_path, mock_path, example_path, batch_path, installs_path = contruct_common_paths(filepath)
make_out(out_path)


def test_step_configuration():
	clean_out(out_path)
	step_configuration = Step_Configuration("test")
	assert step_configuration.name == "test"
	assert step_configuration.patterns == {"in": ".*"}

	step_configuration = Step_Configuration("test")
	step_configuration.update({"overwrite": False, "verbosity": 3})
	assert not step_configuration.overwrite
	assert step_configuration.verbosity == 3

	step_configuration.save(os.path.join(out_path, "step_config.json"))
	assert os.path.isfile(os.path.join(out_path, "step_config.json"))
	with open(os.path.join(out_path, "step_config.json"), "r") as file:
		step_config_dict = json.load(file)
		assert step_config_dict == step_configuration.dict_representation()

	step_configuration = Step_Configuration("test")
	assert step_configuration.name == "test"
	assert step_configuration.verbosity == 1
	assert step_configuration.overwrite

	step_configuration.load(os.path.join(out_path, "step_config.json"))
	assert step_configuration.verbosity == 3
	assert not step_configuration.overwrite


def test_pipe_step():
	clean_out(out_path)
	pipe_step = Pipe_Step("test", exec_path="echo")
	assert pipe_step.name == "test"

	# Test matching
	assert not pipe_step.match_file_name(r"\.XML", "a.mzXML")
	assert pipe_step.match_file_name(r"\.mzXML$", "a.mzXML")

	# Test storing
	pipe_step.store_progress("/mnt/x/bar", "/mnt/y/bar", results={"hello": "all"})
	assert pipe_step.processed_in == ["/mnt/x/bar"]
	assert pipe_step.processed_out == ["/mnt/y/bar"]
	assert pipe_step.results == [{"hello": "all"}]

	# Test computation with same input
	pipe_step.compute("echo Hello!", in_path="/mnt/x/bar", out_path="/mnt/y/foo")
	assert pipe_step.processed_in == ["/mnt/x/bar"]
	assert pipe_step.processed_out == ["/mnt/y/foo"]
	assert pipe_step.results == [None]
	assert pipe_step.outs[0].startswith("Hello!")

	# Test parallel execution
	pipe_step.workers = 2
	pipe_step.compute("echo Hello", in_path="/mnt/x/bar", out_path="/mnt/y/foo")
	pipe_step.compute("echo all!", in_path="/mnt/x/foo", out_path="/mnt/y/foo")
	pipe_step.compute_futures()
	assert pipe_step.processed_in == ["/mnt/x/bar", "/mnt/x/foo"]
	assert pipe_step.processed_out == ["/mnt/y/foo", "/mnt/y/foo"]
	assert pipe_step.results == [None, None]
	assert pipe_step.outs[0].startswith("Hello") and pipe_step.outs[1].startswith("all!")

	# Run is tested for each individual step


def test_clean():
	clean_out(out_path)
