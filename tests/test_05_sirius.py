#!/usr/bin/env python
"""
Testing the SIRIUS annotation.
"""

from tests.common import *
from rampt.steps.annotation.sirius_pipe import *
from rampt.steps.annotation.sirius_pipe import main as sirius_pipe_main

from rampt.installer import *

import pandas as pd

platform = get_platform()
filepath = get_internal_filepath(__file__)
out_path, mock_path, example_path, batch_path, installs_path = contruct_common_paths(filepath)
make_out(out_path)
make_out(installs_path)


def test_installation():
    clean_out(installs_path)
    root = tk.Tk()
    installer = InstallerApp(root, local_only=True)
    installer.install_path = installs_path

    installer.install_components(["Sirius"], standalone=True)
    assert tool_available("sirius")

    # TODO: DEBUG SIRIUS TESTING
    ic(os.environ.get("SIRIUS_USER", ""))
    ic(os.environ.get("SIRIUS_PASSWORD", ""))
    process = subprocess.Popen(
        ["sirius", "login", f'--user=\"{os.environ.get("SIRIUS_USER", "")}\"', f'--password=\"{os.environ.get("SIRIUS_PASSWORD", "")}\"'],
        text=True
    )
    process.wait()


def test_sirius_pipe_run_single():
    clean_out(out_path)

    # Superficial testing of run_single
    sirius_runner = Sirius_Runner(config=join(batch_path, "sirius_config.txt"))

    sirius_runner.run_single(
        in_path=join(example_path, "example_files_sirius.mgf"), out_path=out_path
    )

    assert os.path.isfile(join(out_path, "projectspace.sirius"))
    assert os.path.isfile(join(out_path, "structure_identifications.tsv"))


def test_sirius_pipe_run_directory():
    clean_out(out_path)
    # Supoerficial testing of run_directory
    sirius_runner = Sirius_Runner(config=example_path)

    sirius_runner.run_directory(in_path=example_path, out_path=out_path)

    assert os.path.isfile(join(out_path, "projectspace.sirius"))
    assert os.path.isfile(join(out_path, "structure_identifications.tsv"))


def test_sirius_pipe_run_nested():
    clean_out(out_path)
    # Superficial testing of run_nested
    sirius_runner = Sirius_Runner()

    sirius_runner.run_nested(example_path, out_path)

    assert os.path.isfile(join(out_path, "projectspace.sirius"))
    assert os.path.isfile(join(out_path, "structure_identifications.tsv"))
    assert os.path.isfile(join(out_path, "example_nested", "projectspace.sirius"))
    assert os.path.isfile(join(out_path, "example_nested", "structure_identifications.tsv"))


def test_sirius_pipe_run():
    clean_out(out_path)

    # Superficial testing of run
    sirius_runner = Sirius_Runner(workers=2)

    sirius_runner.run(in_paths=[example_path], out_paths=[out_path])
    sirius_runner.compute_futures()

    assert sirius_runner.processed_in == [join(example_path, "example_files_sirius.mgf")]
    assert sirius_runner.processed_out == [out_path]


def test_sirius_pipe_main():
    args = argparse.Namespace(
        sirius_path="sirius",
        in_dir=example_path,
        out_dir=out_path,
        projectspace=out_path,
        config=join(example_path, "sirius_config.txt"),
        nested=True,
        workers=1,
        save_log=True,
        verbosity=3,
        sirius_args=None,
    )

    sirius_pipe_main(args, unknown_args=[])

    assert os.path.isfile(join(out_path, "projectspace.sirius"))
    assert os.path.isfile(join(out_path, "example_nested", "projectspace.sirius"))

    df = pd.read_csv(join(out_path, "formula_identifications.tsv"), sep="\t")
    assert df.loc[0]["formulaRank"] == 1


def test_clean():
    clean_out(out_path)
