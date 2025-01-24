#!/usr/bin/env python
"""
Testing the feature finding functions.
"""

from tests.common import *
from rampt.steps.feature_finding.mzmine_pipe import *
from rampt.steps.feature_finding.mzmine_pipe import main as mzmine_pipe_main

from rampt.installer import *

import pandas as pd

platform = get_platform()
filepath = get_internal_filepath(__file__)
out_path, mock_path, example_path, batch_path, installs_path = contruct_common_paths(filepath)
make_out(out_path)
make_out(installs_path)

user = "joca"  # NEEDS TO BE EDITED FOR TESTING TO WORK


def test_installation():
    clean_out(installs_path)
    root = tk.Tk()
    installer = InstallerApp(root, local_only=True)
    installer.install_path = installs_path

    installer.install_components(["MZmine"], standalone=True)
    assert tool_available(["mzmine", "mzmine_console"])


def test_mzmine_pipe_run_single():
    clean_out(out_path)

    # Superficial testing of run_single
    mzmine_runner = MZmine_Runner(batch=join(batch_path, "minimal.mzbatch"), user=user, verbosity=3)

    mzmine_runner.run_single(in_path=join(example_path, "minimal.mzML"), out_path=out_path)

    assert os.path.isfile(join(out_path, "out_iimn_fbmn_quant.csv"))
    assert os.path.isfile(join(out_path, "out_sirius.mgf"))


def test_mzmine_pipe_run_directory():
    clean_out(out_path)
    # Supoerficial testing of run_directory
    mzmine_runner = MZmine_Runner(batch=join(batch_path, "minimal.mzbatch"), user=user)

    mzmine_runner.run_directory(in_path=example_path, out_path=out_path)

    assert os.path.isfile(join(out_path, "out_iimn_fbmn_quant.csv"))
    assert os.path.isfile(join(out_path, "out_sirius.mgf"))


def test_mzmine_pipe_run_nested():
    clean_out(out_path)
    # Superficial testing of run_nested
    mzmine_runner = MZmine_Runner(batch=join(batch_path, "minimal.mzbatch"), user=user)

    mzmine_runner.run_nested(example_path, out_path)

    with open(join(out_path, "source_files.txt"), "r") as file:
        source_files = file.read().split("\n")
        assert source_files[0].endswith("example_neg.mzXML")
        assert source_files[1].endswith("minimal.mzML")

    with open(join(out_path, "example_nested", "source_files.txt"), "r") as file:
        source_files = file.read().split("\n")
        assert source_files[0].endswith(join("example_nested", "minimal.mzML"))

    assert os.path.isfile(join(out_path, "out_iimn_fbmn_quant.csv"))
    assert os.path.isfile(join(out_path, "example_nested", "example_nested_iimn_fbmn_quant.csv"))


def test_mzmine_pipe_run():
    clean_out(out_path)

    # Superficial testing of run
    mzmine_runner = MZmine_Runner(batch=join(batch_path, "minimal.mzbatch"), user=user, workers=2)

    mzmine_runner.run([dict(in_path=example_path, out_path=out_path)])
    mzmine_runner.compute_futures()

    assert mzmine_runner.processed_ios == [
        {"in_path": join(out_path, "source_files.txt"), "out_path": out_path}
    ]
    with open(join(out_path, "source_files.txt"), "r") as f:
        lines = f.readlines()
        assert lines[0].strip() == str(join(example_path, "example_neg.mzXML"))
        assert lines[1].strip() == str(join(example_path, "minimal.mzML"))


def test_mzmine_pipe_main():
    clean_out(out_path)
    args = argparse.Namespace(
        mzmine_path=None,
        in_dir=example_path,
        out_dir=out_path,
        batch=join(batch_path, "minimal.mzbatch"),
        user=user,
        nested=True,
        platform=platform,
        save_log=False,
        verbosity=3,
        mzmine_arguments=None,
    )
    mzmine_pipe_main(args, unknown_args=[])

    assert os.path.isfile(join(out_path, "source_files.txt"))
    assert os.path.isfile(join(out_path, "example_nested", "source_files.txt"))

    with open(join(out_path, "source_files.txt"), "r") as f:
        lines = f.readlines()
        assert lines[0].strip() == str(join(example_path, "example_neg.mzXML"))
        assert lines[1].strip() == str(join(example_path, "minimal.mzML"))

    assert os.path.isfile(join(out_path, "example_nested", "example_nested_iimn_fbmn_quant.csv"))
    df = pd.read_csv(join(out_path, "example_nested", "example_nested_iimn_fbmn_quant.csv"))
    assert "row retention time" in df.columns


def test_clean():
    clean_out(out_path)
