#!/usr/bin/env python
"""
Testing the GNPS annotation.
"""

from tests.common import *
from rampt.steps.annotation.gnps_pipe import *
from rampt.steps.annotation.gnps_pipe import main as gnps_pipe_main


platform = get_platform()
filepath = get_internal_filepath(__file__)
out_path, mock_path, example_path, batch_path, installs_path = contruct_common_paths(filepath)
make_out(out_path)


def test_gnps_check_io():
    gnps_runner = GNPS_Runner()
    assert "single from log" in gnps_runner.check_io(
        {
            "in_paths": {"mzmine_log": join(mock_path, "empty_file")},
            "out_path": {"gnps_annotated_data_paths": out_path},
        }
    )

    assert "single from data all" in gnps_runner.check_io(
        {
            "in_paths": {
                "feature_quantification": join(mock_path, "empty_file"),
                "feature_ms2": join(mock_path, "empty_file"),
                "additional_pairs": join(mock_path, "empty_file"),
                "sample_metadata": join(mock_path, "empty_file"),
            },
            "out_path": {"gnps_annotated_data_paths": out_path},
        }
    )

    assert "single from data minimum" in gnps_runner.check_io(
        {
            "in_paths": {
                "feature_quantification": join(mock_path, "empty_file"),
                "feature_ms2": join(mock_path, "empty_file"),
            },
            "out_path": {"gnps_annotated_data_paths": out_path},
        }
    )

    assert "directory" in gnps_runner.check_io(
        {
            "in_paths": {"processed_data_paths": mock_path},
            "out_path": {"gnps_annotated_data_paths": out_path},
        }
    )

    assert "multiple directories from log" in gnps_runner.check_io(
        {"in_paths": {"mzmine_log": mock_path}, "out_path": {"gnps_annotated_data_paths": out_path}}
    )

    assert "multiple directories from data all" in gnps_runner.check_io(
        {
            "in_paths": {
                "feature_quantification": mock_path,
                "feature_ms2": mock_path,
                "additional_pairs": mock_path,
                "sample_metadata": mock_path,
            },
            "out_path": {"gnps_annotated_data_paths": out_path},
        }
    )

    assert "multiple directories from  minimum" in gnps_runner.check_io(
        {
            "in_paths": {"feature_quantification": mock_path, "feature_ms2": mock_path},
            "out_path": {"gnps_annotated_data_paths": out_path},
        }
    )

    assert "nested" in gnps_runner.check_io(
        {
            "in_paths": {"processed_data_paths": [mock_path]},
            "out_path": {"gnps_annotated_data_paths": out_path},
        }
    )


def test_gnps_submit():
    gnps_runner = GNPS_Runner(verbosity=3)

    task_id, status = gnps_runner.submit_to_gnps(
        feature_ms2=join(example_path, "example_files_iimn_fbmn.mgf"),
        feature_quantification=join(example_path, "example_files_iimn_fbmn_quant.csv"),
    )

    if not status:
        logger.warn(
            "GNPS is probably down (again)."
            + f"Try reaching https://gnps.ucsd.edu/ProteoSAFe/status_json.jsp?task={task_id} to check task."
            + "Debugging is recommended via graphical web interface, to get meaningful errors."
        )
    assert isinstance(task_id, str) and task_id != ""


def test_gnps_pipe_run_single():
    clean_out(out_path)

    # Superficial testing of run_single
    gnps_runner = GNPS_Runner(verbosity=3)

    gnps_runner.run_single(
        in_paths={"mzmine_log": join(example_path, "mzmine_log.txt")},
        out_path={"gnps_annotated_data_paths": out_path},
    )

    assert os.path.isfile(join(out_path, "fbmn_all_db_annotations.json"))


def test_gnps_pipe_run_directory():
    clean_out(out_path)
    # Supoerficial testing of run_directory
    gnps_runner = GNPS_Runner(verbosity=3)

    gnps_runner.run_directory(in_paths={"mzmine_log": example_path}, out_path=out_path)

    assert os.path.isfile(join(out_path, "fbmn_all_db_annotations.json"))


def test_gnps_pipe_run_nested():
    clean_out(out_path)
    # Superficial testing of run_nested
    gnps_runner = GNPS_Runner(verbosity=3)

    gnps_runner.run_nested(example_path, out_path)

    assert os.path.isfile(join(out_path, "fbmn_all_db_annotations.json"))
    assert os.path.isfile(join(out_path, "example_nested", "fbmn_all_db_annotations.json"))


def test_gnps_pipe_run():
    clean_out(out_path)

    # Superficial testing of run
    gnps_runner = GNPS_Runner(verbosity=3, workers=2)

    gnps_runner.run([dict(in_paths={"mzmine_log": example_path}, out_path=out_path)])
    gnps_runner.compute_futures()

    assert gnps_runner.processed_ios == [
        {
            "in_paths": {"mzmine_log": join(example_path, "mzmine_log.txt")},
            "out_path": {
                "gnps_annotated_data_paths": join(out_path, "fbmn_all_db_annotations.json")
            },
        }
    ]


def test_gnps_pipe_main():
    args = argparse.Namespace(
        in_dir=example_path,
        out_dir=out_path,
        nested=True,
        workers=1,
        save_log=True,
        verbosity=0,
        gnps_args=None,
    )

    gnps_pipe_main(args, unknown_args=[])

    assert os.path.isfile(join(out_path, "fbmn_all_db_annotations.json"))
    assert os.path.isfile(join(out_path, "example_nested", "fbmn_all_db_annotations.json"))


def test_clean():
    clean_out(out_path)
