#!/usr/bin/env python
"""
Testing the GNPS annotation.
"""

from tests.common import *
from source.steps.annotation.gnps_pipe import *
from source.steps.annotation.gnps_pipe import main as gnps_pipe_main


platform = get_platform()
filepath = get_internal_filepath(__file__)
out_path, test_path, example_path, batch_path = contruct_common_paths(filepath)
make_out(out_path)


def test_gnps_submit():
	gnps_runner = GNPS_Runner(mzmine_log=join(example_path, "mzmine_log.txt"))

	task_id, status = gnps_runner.submit_to_gnps(
		feature_ms2_file=join(example_path, "example_files_iimn_fbmn.mgf"),
		feature_quantification_file=join(example_path, "example_files_iimn_fbmn_quant.csv"),
	)

	assert status
	assert isinstance(task_id, str) and task_id != ""


def test_gnps_pipe_run_single():
	clean_out(out_path)

	# Superficial testing of run_single
	gnps_runner = GNPS_Runner(mzmine_log=join(example_path, "mzmine_log.txt"))

	gnps_runner.run_single(in_path=join(example_path, "mzmine_log.txt"), out_path=out_path)

	assert os.path.isfile(join(out_path, f"{basename(example_path)}_gnps_all_db_annotations.json"))


def test_gnps_pipe_run_directory():
	clean_out(out_path)
	# Supoerficial testing of run_directory
	gnps_runner = GNPS_Runner(mzmine_log=example_path)

	gnps_runner.run_directory(in_path=example_path, out_path=out_path)

	assert os.path.isfile(join(out_path, f"{basename(example_path)}_gnps_all_db_annotations.json"))


def test_gnps_pipe_run_nested():
	clean_out(out_path)
	# Superficial testing of run_nested
	gnps_runner = GNPS_Runner()

	gnps_runner.run_nested(example_path, out_path)

	assert os.path.isfile(join(out_path, f"{basename(example_path)}_gnps_all_db_annotations.json"))
	assert os.path.isfile(
		join(out_path, "example_nested", "example_nested_gnps_all_db_annotations.json")
	)


def test_gnps_pipe_run():
	clean_out(out_path)

	# Superficial testing of run
	gnps_runner = GNPS_Runner(workers=2)

	gnps_runner.run(in_paths=[example_path], out_paths=[out_path])
	gnps_runner.compute_futures()

	assert gnps_runner.processed_in == [example_path]
	assert gnps_runner.processed_out == [
		join(out_path, f"{basename(example_path)}_gnps_all_db_annotations.json")
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

	assert os.path.isfile(join(out_path, "example_files_gnps_all_db_annotations.json"))
	assert os.path.isfile(
		join(out_path, "example_nested", "example_nested_gnps_all_db_annotations.json")
	)


def test_clean():
	clean_out(out_path)
