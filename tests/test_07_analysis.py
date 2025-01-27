#!/usr/bin/env python
"""
Testing the data analysis.
"""

from tests.common import *
from rampt.steps.analysis.analysis_pipe import *
from rampt.steps.analysis.analysis_pipe import main as analysis_pipe_main


platform = get_platform()
filepath = get_internal_filepath(__file__)
out_path, mock_path, example_path, batch_path, installs_path = contruct_common_paths(filepath)
make_out(out_path)
data_warning = "Data must contain at least 2 columns with peak information to calculate z-scores between samples. Returning unchanged."


def test_summary_check_io():
    analysis_runner = Analysis_Runner()
    assert "single" in analysis_runner.check_io(
        {
            "in_paths": {"summary_paths": join(mock_path, "empty_file")},
            "out_path": {"analysis_paths": out_path},
        }
    )

    assert "directory" in analysis_runner.check_io(
        {"in_paths": {"summary_paths": mock_path}, "out_path": {"analysis_paths": out_path}}
    )

    assert "nested" in analysis_runner.check_io(
        {"in_paths": {"summary_paths": [mock_path]}, "out_path": {"analysis_paths": out_path}}
    )


def test_analysis_search_check_peak_info():
    analysis_runner = Analysis_Runner()

    summary = analysis_runner.read_summary(file_path=join(example_path, "summary.tsv"))

    peak_columns = analysis_runner.search_check_peak_info(summary=summary)

    assert peak_columns["positive"] == [
        "acnA_R1_P3-C1_pos.mzML Peak area",
        "acnA_R1_P3-C2_pos.mzML Peak area",
        "acnA_R1_P3-C3_pos.mzML Peak area",
    ]
    assert peak_columns["negative"] == ["acnA_R1_P3-C1_neg.mzML Peak Area"]


def test_z_score(recwarn):
    analysis_runner = Analysis_Runner()
    summary = analysis_runner.read_summary(file_path=join(example_path, "summary.tsv"))
    peak_columns = analysis_runner.search_check_peak_info(summary=summary)

    analysis = analysis_runner.z_score(summary=summary, peak_mode_columns=peak_columns["negative"])
    assert len(recwarn) == 1
    assert recwarn[0].message.args[0].endswith(data_warning)
    assert analysis.shape[0] == summary.shape[0] and analysis.shape[1] == 1

    analysis = analysis_runner.z_score(summary=summary, peak_mode_columns=peak_columns["positive"])
    ic(analysis[0])
    assert np.all(np.isclose(analysis[0], np.array([np.nan, 1.0, -1.0]), equal_nan=True))
    assert np.all(np.isclose(analysis[1], np.array([np.nan, np.nan, np.nan]), equal_nan=True))
    assert np.all(np.isclose(analysis[2], np.array([-1.41419473, 0.7134186, 0.70077613])))


def test_complete_analysis():
    clean_out(out_path)

    analysis_runner = Analysis_Runner()

    analysis_runner.complete_analysis(
        in_out=dict(in_paths=join(example_path, "summary.tsv"), out_path=out_path)
    )

    assert os.path.isfile(join(out_path, "analysis.tsv"))
    assert os.path.isfile(join(out_path, "analysis_positive_mode.tsv"))
    assert os.path.isfile(join(out_path, "analysis_negative_mode.tsv"))


def test_analysis_pipe_run_single():
    clean_out(out_path)

    # Superficial testing of run_single
    analysis_runner = Analysis_Runner()

    analysis_runner.run_single(
        in_paths={"summary_paths": join(example_path, "summary.tsv")},
        out_path={"analysis_paths": out_path},
    )

    assert os.path.isfile(join(out_path, "analysis.tsv"))
    assert os.path.isfile(join(out_path, "analysis_positive_mode.tsv"))
    assert os.path.isfile(join(out_path, "analysis_negative_mode.tsv"))


def test_analysis_pipe_run_directory():
    clean_out(out_path)
    # Supoerficial testing of run_directory
    analysis_runner = Analysis_Runner(mzmine_log=example_path)

    analysis_runner.run_directory(
        in_paths={"summary_paths": example_path}, out_path={"analysis_paths": out_path}
    )

    assert os.path.isfile(join(out_path, "analysis.tsv"))
    assert os.path.isfile(join(out_path, "analysis_positive_mode.tsv"))
    assert os.path.isfile(join(out_path, "analysis_negative_mode.tsv"))


def test_analysis_pipe_run_nested():
    clean_out(out_path)
    # Superficial testing of run_nested
    analysis_runner = Analysis_Runner()

    analysis_runner.run_nested(example_path, out_path)

    assert os.path.isfile(join(out_path, "analysis.tsv"))
    assert os.path.isfile(join(out_path, "example_nested", "analysis.tsv"))


def test_analysis_pipe_run():
    clean_out(out_path)

    # Superficial testing of run
    analysis_runner = Analysis_Runner(workers=2)

    analysis_runner.run(
        [dict(in_paths={"summary_paths": example_path}, out_path={"analysis_paths": out_path})]
    )
    analysis_runner.compute_futures()

    assert analysis_runner.processed_ios == [
        {
            "in_paths": {"summary_paths": join(example_path, "summary.tsv")},
            "out_path": {"analysis_paths": out_path},
        }
    ]


def test_analysis_pipe_main():
    args = argparse.Namespace(
        in_dir=example_path,
        out_dir=out_path,
        nested=True,
        workers=1,
        save_log=True,
        verbosity=0,
        analysis_arguments=None,
    )

    analysis_pipe_main(args, unknown_args=[])

    assert os.path.isfile(join(out_path, "analysis.tsv"))
    assert os.path.isfile(join(out_path, "example_nested", "analysis.tsv"))


def test_clean():
    clean_out(out_path)
