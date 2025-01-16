#!/usr/bin/env python
"""
Testing the data summary.
"""

from tests.common import *
from rampt.steps.analysis.summary_pipe import *
from rampt.steps.analysis.summary_pipe import main as summary_pipe_main


platform = get_platform()
filepath = get_internal_filepath(__file__)
out_path, mock_path, example_path, batch_path, installs_path = contruct_common_paths(filepath)
make_out(out_path)


def test_search_files():
    clean_out(out_path)

    # Superficial testing of run_single
    summary_runner = Summary_Runner()

    quantification_file = summary_runner.search_quantification_file(
        example_path, quantification_file="X"
    )
    assert quantification_file == "X"

    quantification_file = summary_runner.search_quantification_file(example_path)
    assert quantification_file == join(example_path, "example_files_iimn_fbmn_quant.csv")

    annotation_files = summary_runner.search_annotation_files(example_path)
    assert annotation_files == {
        "formula_identifications_file": join(example_path, "formula_identifications.tsv"),
        "canopus_formula_summary_file": join(example_path, "canopus_formula_summary.tsv"),
        "structure_identifications_file": join(example_path, "structure_identifications.tsv"),
        "canopus_structure_summary_file": join(example_path, "canopus_structure_summary.tsv"),
        "denovo_structure_identifications_file": join(
            example_path, "denovo_structure_identifications.tsv"
        ),
        "gnps_annotations": join(example_path, "example_files_gnps_all_db_annotations.json"),
    }


def test_summary_add_quantification():
    clean_out(out_path)

    # Superficial testing of run_single
    summary_runner = Summary_Runner()

    summary = summary_runner.add_quantification(
        join(example_path, "example_files_iimn_fbmn_quant.csv"), summary=None
    )

    assert (
        "ID" in summary.columns and "m/z" in summary.columns and "retention time" in summary.columns
    )
    assert summary["ID"].dtype.name == "object"


def test_summary_add_annotation():
    clean_out(out_path)

    # Superficial testing of run_single
    summary_runner = Summary_Runner()

    summary = summary_runner.add_quantification(
        join(example_path, "example_files_iimn_fbmn_quant.csv"), summary=None
    )
    summary = summary_runner.add_annotation(
        annotation_file=join(example_path, "example_files_gnps_all_db_annotations.json"),
        annotation_file_type="gnps_annotations",
        summary=summary,
    )

    assert (
        "ID" in summary.columns
        and "m/z" in summary.columns
        and "retention time" in summary.columns
        and "FBMN_m/z_error(ppm)" in summary.columns
    )
    assert summary[summary["ID"] == "2"]["FBMN_compound_name"][0] == "GLUTATHIONE - 40.0 eV"


def test_summary_add_annotations():
    clean_out(out_path)

    # Superficial testing of run_single
    summary_runner = Summary_Runner()

    quantification_file = summary_runner.search_quantification_file(example_path)
    annotation_files = summary_runner.search_annotation_files(example_path)

    summary = summary_runner.add_quantification(quantification_file, summary=None)
    summary = summary_runner.add_annotations(annotation_files, summary=summary)

    assert summary[summary["ID"] == "2"]["m/z"][0] == 267.12273020717777
    assert summary[summary["ID"] == "2"]["Sirius_formula"][0] == "C14H18O5"
    assert summary[summary["ID"] == "2"]["Sirius_formula_NPC_pathway"][0] == "Polyketides"
    assert (
        summary[summary["ID"] == "2"]["Sirius_structure_smiles"][0]
        == "CC(C=CC=CC1(C(=C(C(=O)O1)C(=O)C)OC)C)O"
    )
    assert (
        summary[summary["ID"] == "2"]["Sirius_structure_ClassyFire_most_specific_class"][0]
        == "Carboxylic acid esters"
    )
    assert (
        summary[summary["ID"] == "2"]["Sirius_denovo_structure_smiles"][0]
        == "CC=C(OC)C(C)OC(=O)C=CC1=CC(C)OC1=O"
    )
    assert summary[summary["ID"] == "2"]["FBMN_compound_name"][0] == "GLUTATHIONE - 40.0 eV"


def test_summary_pipe_run_single():
    clean_out(out_path)

    # Superficial testing of run_single
    summary_runner = Summary_Runner()

    summary_runner.run_single(
        in_path=(
            join(example_path, "example_files_iimn_fbmn_quant.csv"),
            join(example_path, "example_files_gnps_all_db_annotations.json"),
        ),
        out_path=out_path,
        annotation_file_type="gnps_annotations",
    )

    assert os.path.isfile(join(out_path, "summary.tsv"))


def test_summary_pipe_run_directory():
    clean_out(out_path)

    # Superficial testing of run_single
    summary_runner = Summary_Runner()

    summary_runner.run_directory(in_path=example_path, out_path=out_path)

    assert os.path.isfile(join(out_path, "summary.tsv"))


def test_summary_pipe_run_nested():
    clean_out(out_path)

    # Superficial testing of run_single
    summary_runner = Summary_Runner()

    summary_runner.run_nested(in_root_dir=example_path, out_root_dir=out_path)

    assert os.path.isfile(join(out_path, "summary.tsv"))
    assert os.path.isfile(join(out_path, "example_nested", "summary.tsv"))


def test_summary_pipe_run():
    clean_out(out_path)

    # Superficial testing of run
    summary_runner = Summary_Runner(workers=2)

    summary_runner.run(in_paths=[example_path], out_paths=[out_path])
    summary_runner.compute_futures()

    assert summary_runner.processed_in == [
        {"quantification": example_path, "annotation": example_path}
    ]
    assert summary_runner.processed_out == [join(out_path, "summary.tsv")]


def test_summary_pipe_main():
    args = argparse.Namespace(
        in_dir_annotations=example_path,
        in_dir_quantification=example_path,
        out_dir=out_path,
        nested=False,
        workers=1,
        save_log=True,
        verbosity=0,
        summary_arguments=None,
    )

    summary_pipe_main(args, unknown_args=[])

    assert os.path.isfile(join(out_path, "summary.tsv"))


def test_clean():
    clean_out(out_path)
