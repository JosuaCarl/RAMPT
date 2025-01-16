#!/usr/bin/env python
"""
Testing the conversion functions.
"""

from tests.common import *
from rampt.steps.conversion.msconv_pipe import *
from rampt.steps.conversion.msconv_pipe import main as msconv_pipe_main
from bs4 import BeautifulSoup

platform = get_platform()
filepath = get_internal_filepath(__file__)
out_path, mock_path, example_path, batch_path, installs_path = contruct_common_paths(filepath)
make_out(out_path)


def test_msconv_pipe_run_single():
    clean_out(out_path)

    # Superficial testing of compute
    msconvert_runner = MSconvert_Runner(
        platform=platform,
        target_format=".mzML",
        save_log=False,
        verbosity=3,
        nested=False,
        workers=1,
    )

    msconvert_runner.run_single(in_path=join(mock_path, "minimal_file.mzML"), out_path=out_path)

    assert os.path.isfile(join(out_path, "minimal_file.mzML"))
    assert not os.path.exists(join(out_path, "nested_test_folder"))


def test_msconv_pipe_run_directory():
    clean_out(out_path)

    # Superficial testing of run_directory
    msconvert_runner = MSconvert_Runner(
        platform=platform,
        target_format=".mzML",
        pattern=".*",
        save_log=False,
        verbosity=3,
        nested=False,
        workers=1,
    )

    msconvert_runner.run_directory(in_path=mock_path, out_path=out_path)

    assert os.path.isfile(join(out_path, "minimal_file.mzML"))
    assert not os.path.exists(join(out_path, "nested_test_folder"))


def test_msconv_pipe_run_nested():
    clean_out(out_path)
    # Superficial testing of run_nested
    msconvert_runner = MSconvert_Runner(
        platform=platform,
        target_format=".mzML",
        suffix=".mzML",
        save_log=False,
        verbosity=1,
        nested=True,
        workers=1,
    )

    futures = msconvert_runner.run_nested(in_root_dir=mock_path, out_root_dir=out_path)
    compute_scheduled(
        futures=futures,
        num_workers=msconvert_runner.workers,
        verbose=msconvert_runner.verbosity >= 1,
    )

    assert msconvert_runner.processed_out == [
        join(out_path, "minimal_file.mzML"),
        join(out_path, "nested_test_folder", "minimal_file.mzML"),
    ]
    assert os.path.isfile(join(out_path, "minimal_file.mzML"))
    assert os.path.exists(join(out_path, "nested_test_folder"))
    assert os.path.isfile(join(out_path, "nested_test_folder", "minimal_file.mzML"))


def test_msconv_pipe_run():
    clean_out(out_path)

    # Superficial testing of run
    msconvert_runner = MSconvert_Runner(
        platform=platform,
        target_format=".mzML",
        suffix=".mzML",
        save_log=False,
        verbosity=3,
        overwrite=True,
        nested=False,
        workers=1,
    )

    msconvert_runner.run(in_paths=[mock_path], out_paths=[out_path])

    assert msconvert_runner.processed_in == [join(mock_path, "minimal_file.mzML")]
    assert msconvert_runner.processed_out == [join(out_path, "minimal_file.mzML")]
    assert os.path.isfile(join(out_path, "minimal_file.mzML"))

    clean_out(out_path)

    # Specific run
    msconvert_runner.run(in_paths=[join(mock_path, "minimal_file.mzML")], out_paths=[out_path])

    assert msconvert_runner.processed_in == [join(mock_path, "minimal_file.mzML")]
    assert msconvert_runner.processed_out == [join(out_path, "minimal_file.mzML")]
    assert os.path.isfile(join(out_path, "minimal_file.mzML"))


def test_msconv_pipe_run_cross():
    clean_out(out_path)
    # Superficial testing of nested run
    msconvert_runner = MSconvert_Runner(
        platform=platform,
        target_format=".mzXML",
        pattern=r".*\.mzML$",
        save_log=False,
        verbosity=3,
        nested=True,
        workers=1,
    )

    msconvert_runner.run(in_paths=[mock_path], out_paths=[out_path])

    assert msconvert_runner.processed_in == [
        join(mock_path, "minimal_file.mzML"),
        join(mock_path, "nested_test_folder", "minimal_file.mzML"),
    ]
    assert msconvert_runner.processed_out == [
        join(out_path, "minimal_file.mzXML"),
        join(out_path, "nested_test_folder", "minimal_file.mzXML"),
    ]
    assert os.path.isfile(join(out_path, "minimal_file.mzXML"))
    assert os.path.isfile(join(out_path, "nested_test_folder", "minimal_file.mzXML"))
    assert not os.path.exists(join(out_path, "empty_nested_test_folder"))


def test_msconv_pipe_main():
    clean_out(out_path)
    # Exact testing of main method
    args = argparse.Namespace(
        in_dir=mock_path,
        out_dir=out_path,
        pattern="",
        target_format="mzML",
        suffix=".mzML",
        prefix=None,
        contains=None,
        redo_threshold=0.0,
        overwrite=None,
        workers=4,
        nested=True,
        platform=platform,
        verbosity=3,
        msconv_arguments=None,
        save_log=False,
    )
    msconv_pipe_main(args, unknown_args=[])

    assert os.path.isfile(join(out_path, "minimal_file.mzML"))
    assert os.path.isfile(join(out_path, "nested_test_folder", "minimal_file.mzML"))

    with open(join(out_path, "minimal_file.mzML")) as f:
        data = f.read()
        data = BeautifulSoup(data, "xml")
        file = data.find("sourceFile")
        assert os.path.join(file.get("location"), file.get("name")) == "file:///" + join(
            mock_path, "minimal_file.mzML"
        )

    # Test XML
    clean_out(out_path)
    args.target_format = "mzXML"
    args.suffix = ".mzXML"
    msconv_pipe_main(args, unknown_args=[])

    assert os.path.isfile(join(out_path, "minimal file.mzXML"))
    assert os.path.isfile(join(out_path, "nested_test_folder", "minimal_file.mzXML"))

    with open(construct_path(filepath, "..", "out", "minimal file.mzXML")) as f:
        data = f.read()
        data = BeautifulSoup(data, "xml")
        file = data.find_all("parentFile")[-1]
        assert (
            file.get("fileName") == "file:///" + mock_path + "/" + "minimal file.mzXML"
        )  # <- mzXML path is wrong for windows (fault with msconvert)


def test_clean():
    clean_out(out_path)
