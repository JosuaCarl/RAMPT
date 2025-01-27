#!/usr/bin/env python
"""
Testing the configuration of taipy scenario.
"""

from tests.common import *
from rampt.gui.configuration.config import *

from rampt.steps.general import Pipe_Step


platform = get_platform()
filepath = get_internal_filepath(__file__)
out_path, mock_path, example_path, batch_path, installs_path = contruct_common_paths(filepath)
make_out(out_path)

minimal_global_patterns = {"patterns": None, "additional_args": None}

# TODO: FIX tests


def test_generic_step():
    try:
        generic_step(
            step_class=Pipe_Step, step_params={}, global_params=minimal_global_patterns.copy()
        )
    except TypeError:
        assert True

    try:
        generic_step(
            step_class=Pipe_Step,
            step_params={},
            global_params=minimal_global_patterns.copy(),
            entrypoint=True,
            in_outs=[{"in_path": mock_path}],
        )
    except NotImplementedError:
        assert True


def test_convert_files():
    clean_out(out_path)

    convert_files(
        raw_data_paths=join(example_path, "minimal.mzML"),
        conversion_out_paths=out_path,
        step_params={},
        global_params=minimal_global_patterns.copy(),
    )
    assert os.path.isfile(join(out_path, "minimal.mzML"))


def test_find_features():
    clean_out(out_path)

    find_features(
        community_formatted_data_paths=join(example_path, "example_neg.mzXML"),
        feature_finding_out_paths=out_path,
        mzmine_batch=join(batch_path, "minimal.mzbatch"),
        step_params={"verbosity": 4, "login": "--user joca"},
        global_params=minimal_global_patterns.copy(),
    )

    assert os.path.isfile(join(out_path, "out_iimn_fbmn_quant.csv"))


def test_annotate_gnps():
    clean_out(out_path)

    annotate_gnps(
        processed_data_paths=join(example_path, "example_files_iimn_fbmn.mgf"),
        mzmine_log=join(example_path, "mzmine_log.txt"),
        gnps_out_paths=out_path,
        step_params={},
        global_params=minimal_global_patterns.copy(),
    )

    assert os.path.isfile(join(out_path, "example_files_gnps_all_db_annotations.json"))


def test_annotate_sirius():
    clean_out(out_path)

    annotate_sirius(
        processed_data_paths=join(example_path, "example_files_sirius.mgf"),
        sirius_out_paths=out_path,
        config=join(batch_path, "sirius_config.txt"),
        step_params={},
        global_params=minimal_global_patterns.copy(),
    )

    assert os.path.isfile(join(out_path, "projectspace.sirius"))


def test_summarize_annotations():
    clean_out(out_path)

    summarize_annotations(
        processed_data_paths=example_path,
        gnps_annotated_data_paths=example_path,
        sirius_annotated_data_paths=example_path,
        summary_out_paths=out_path,
        step_params={},
        global_params=minimal_global_patterns.copy(),
    )

    assert os.path.isfile(join(out_path, "summary.tsv"))


def test_analyze_difference():
    analyze_difference(
        summary_data_paths=example_path,
        analysis_out_paths=out_path,
        step_params={},
        global_params=minimal_global_patterns.copy(),
    )

    assert os.path.isfile(join(out_path, "analysis.tsv"))


def test_clean():
    clean_out(out_path)
