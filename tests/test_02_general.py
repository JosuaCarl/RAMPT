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

    # Initialization test
    step_configuration = Step_Configuration("test")
    assert step_configuration.name == "test"
    assert step_configuration.patterns == {"in": ".*"}

    # Update test
    step_configuration = Step_Configuration("test")
    step_configuration.update({"overwrite": False, "verbosity": 3})
    step_configuration.update({"pattern": ".*", "prefix": "Chuck", "suffix": "Norris"})
    assert not step_configuration.overwrite
    assert step_configuration.verbosity == 3
    assert step_configuration.prefix == "Chuck"
    assert step_configuration.patterns["in"] == r"^Chuck.*.*.*Norris$"

    # Saving test
    step_configuration.save(os.path.join(out_path, "step_config.json"))
    assert os.path.isfile(os.path.join(out_path, "step_config.json"))
    with open(os.path.join(out_path, "step_config.json"), "r") as file:
        step_config_dict = json.load(file)
        assert step_config_dict == step_configuration.dict_representation()

    # Loading test
    ## Check for pre load configuration
    step_configuration = Step_Configuration("test")
    assert step_configuration.name == "test"
    assert step_configuration.verbosity == 1
    assert step_configuration.overwrite

    ## Check post load configuration
    step_configuration.load(os.path.join(out_path, "step_config.json"))
    assert step_configuration.verbosity == 3
    assert not step_configuration.overwrite



def test_pipe_step():
    clean_out(out_path)
    pipe_step = Pipe_Step(
        "test",
        exec_path="echo",
    )
    assert pipe_step.name == "test"

    # Test storing
    pipe_step.store_progress({"in_path": "/mnt/x/bar", "out_path": "/mnt/y/bar"}, results={"hello": "all"})
    assert pipe_step.processed_ios == [{"in_path": "/mnt/x/bar", "out_path": "/mnt/y/bar"}]
    assert pipe_step.results == [{"hello": "all"}]

    # Test computation with same input
    pipe_step.reset_progress()
    pipe_step.compute("echo Hello!", in_out={"in_path": "/mnt/x/bar", "out_path": "/mnt/y/foo"})
    assert pipe_step.processed_ios == [{"in_path": "/mnt/x/bar", "out_path": "/mnt/y/foo"}]
    assert pipe_step.results == [None]
    assert pipe_step.outs[0].startswith("Hello!")

    # Test parallel execution
    pipe_step.reset_progress()
    pipe_step.workers = 2
    pipe_step.compute("echo Hello", in_out={"in_path": "/mnt/x/bar", "out_path": "/mnt/y/foo"})
    pipe_step.compute("echo all!", in_out={"in_path": "/mnt/x/foo", "out_path": "/mnt/y/foo"})
    pipe_step.compute_futures()
    assert pipe_step.processed_ios == [
        {"in_path": "/mnt/x/bar", "out_path": "/mnt/y/foo"},
        {"in_path": "/mnt/x/foo", "out_path": "/mnt/y/foo"},
    ]
    assert pipe_step.results == [None, None]
    assert pipe_step.outs[0].startswith("Hello") and pipe_step.outs[1].startswith("all!")

    # Run is tested for each individual step

def test_pattern_matching():
    clean_out(out_path)
    # Update regex
    step_configuration = Step_Configuration("test")
    step_configuration.update({"pattern": ".*", "prefix": "Chuck", "suffix": "Norris"})
    assert step_configuration.prefix == "Chuck"
    assert step_configuration.patterns["in"] == r"^Chuck.*.*.*Norris$"
    
    # Matching
    pipe_step = Pipe_Step(
        "test",
        exec_path="echo",
        pattern="",
        prefix="This",
        contains="bunny",
        mandatory_patterns={"in": ".*nice$"},
    )
    assert pipe_step.name == "test"

    # Test matching
    assert pipe_step.match_path(r"\.mzXML$", "a.mzXML")
    assert not pipe_step.match_path(r"\.XML", "a.mzXML")
    
    # Test filled pattern handling
    assert pipe_step.match_path(pipe_step.patterns["in"], "This bunny seems nice")
    assert pipe_step.match_path(pipe_step.patterns["in"], "Thisbunnynice")

    assert not pipe_step.match_path(pipe_step.patterns["in"], "Thisbunnynic")
    assert not pipe_step.match_path(pipe_step.patterns["in"], "thisbunnynice")
    assert not pipe_step.match_path(pipe_step.patterns["in"], "This bunny seems nice.")
    assert not pipe_step.match_path(pipe_step.patterns["in"], "This rabbit seems nice")

    # Test regex updating
    pipe_step.prefix = "The"
    assert not pipe_step.match_path(pipe_step.patterns["in"], "The bunny seems nice")
    
    pipe_step.update_regexes()
    assert pipe_step.match_path(pipe_step.patterns["in"], "The bunny seems nice")


def test_get_log_path():
    pipe_step = Pipe_Step("test")
    assert pipe_step.get_log_path(out_path) is None

    pipe_step.save_log = True
    assert pipe_step.get_log_path(out_path) == join(out_path, "test_log.txt")


def test_extract():
    pipe_step = Pipe_Step("test")
    dictionary = {"in": {"standard": 1}}

    # Extract standard
    assert pipe_step.extract_standard(**dictionary) == 1
    assert pipe_step.extract_standard(standard_value="arbritrary", some_arbitrary_key=1) == 1
    
    dictionary = {"in": {"wildcard": 1}}
    assert pipe_step.extract_standard(standard_value="wildcard", **dictionary) == 1

    # Extract optional
    assert pipe_step.extract_optional({}, keys=["in", "out"]) == [None, None]
    assert pipe_step.extract_optional(dictionary, keys=["in", "out"]) == [{"wildcard": 1}, None]
    assert pipe_step.extract_optional(dictionary, keys=["in"]) == {"wildcard": 1}


def test_link_additional_args():
    pipe_step = Pipe_Step("test")
    assert pipe_step.link_additional_args() == ""

    dictionary = {"in": 1}
    assert pipe_step.link_additional_args(**dictionary) == "--in \"1\""

    pipe_step.additional_args = ["--out", "2"]
    assert pipe_step.link_additional_args(**dictionary) == "--out 2 --in \"1\""


def test_clean():
    clean_out(out_path)
