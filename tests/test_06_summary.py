#!/usr/bin/env python
"""
Testing the data summary.
"""

from tests.common import *
from source.steps.analysis.summary_pipe import *
from source.steps.analysis.summary_pipe import main as summary_pipe_main


platform = get_platform()
filepath = get_internal_filepath(__file__)
out_path, test_path, example_path, batch_path = contruct_common_paths(filepath)
make_out(out_path)


def test_summary_add_quantification():
	clean_out(out_path)

	# Superficial testing of run_single
	summary_runner = Summary_Runner()

	summary = summary_runner.add_quantification(join(example_path, "example_files_iimn_fbmn_quant.csv"), summary=None)

	ic(summary)

	assert os.path.isfile(
		join(out_path, f"{basename(example_path)}_analysis_all_db_annotations.json")
	)

def test_summary_pipe_run_single():
	clean_out(out_path)

	# Superficial testing of run_single
	summary_runner = Summary_Runner()

	summary_runner.run_single(
		in_path_quantification=join(example_path, "example_files_iimn_fbmn_quant.csv"),
		in_path_annotation=join(example_path, "example_files_gnps_all_db_annotations.json"),
		out_path=out_path
	)

	assert os.path.isfile(
		join(out_path, f"summary.tsv")
	)


def test_summary_pipe_run_directory():
	clean_out(out_path)
	# Supoerficial testing of run_directory
	summary_runner = summary_runner(mzmine_log=example_path)

	summary_runner.run_directory(in_path=example_path, out_path=out_path)

	assert os.path.isfile(
		join(out_path, f"{basename(example_path)}_summary_all_db_annotations.json")
	)


def test_summary_pipe_run_nested():
	clean_out(out_path)
	# Superficial testing of run_nested
	summary_runner = summary_runner()

	summary_runner.run_nested(example_path, out_path)

	assert os.path.isfile(
		join(out_path, f"{basename(example_path)}_summary_all_db_annotations.json")
	)
	assert os.path.isfile(
		join(out_path, "example_nested", "example_nested_summary_all_db_annotations.json")
	)


def test_summary_pipe_run():
	clean_out(out_path)

	# Superficial testing of run
	summary_runner = summary_runner(workers=2)

	summary_runner.run(in_paths=[example_path], out_paths=[out_path])
	summary_runner.compute_futures()

	assert summary_runner.processed_in == [example_path]
	assert summary_runner.processed_out == [
		join(out_path, f"{basename(example_path)}_summary_all_db_annotations.json")
	]


def test_summary_pipe_main():
	args = argparse.Namespace(
		in_dir=example_path,
		out_dir=out_path,
		nested=True,
		workers=1,
		save_log=True,
		verbosity=0,
		summary_args=None,
	)

	summary_pipe_main(args, unknown_args=[])

	assert os.path.isfile(join(out_path, "example_files_summary_all_db_annotations.json"))
	assert os.path.isfile(
		join(out_path, "example_nested", "example_nested_summary_all_db_annotations.json")
	)


def test_clean():
	clean_out(out_path)
