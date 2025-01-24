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
        annotation_file=join(example_path, "example_files_fbmn_all_db_annotations.json"),
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

    # Prepare annotation data
    in_path = {"annotation": example_path, "quantification": example_path}
    if "annotation" in in_path:
        for annotation_type in summary_runner.ordered_annotations:
            if annotation_type not in in_path:
                in_path[annotation_type] = in_path["annotation"]
        in_path.pop("annotation")

    matched_in_paths = {}
    for file_type, path in in_path.items():
        for entry in os.listdir(path):
            if summary_runner.match_path(pattern=summary_runner.patterns[file_type], path=entry):
                matched_in_paths[file_type] = join(path, entry)
                break
    
    summary = summary_runner.add_quantification(matched_in_paths.pop("quantification"), summary=None)
    summary = summary_runner.add_annotations(matched_in_paths, summary=summary)

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
        in_path={
            "quantification": join(example_path, "example_files_iimn_fbmn_quant.csv"),
            "gnps_annotations": join(example_path, "example_files_fbmn_all_db_annotations.json"),
        },
        out_path=out_path,
        annotation_file_type="gnps_annotations",
    )

    assert os.path.isfile(join(out_path, "summary.tsv"))


def test_summary_pipe_run_directory():
    clean_out(out_path)

    # Superficial testing of run_single
    summary_runner = Summary_Runner()

    summary_runner.run_directory(
        in_path={"quantification": example_path, "annotation": example_path},
        out_path=out_path
    )

    assert os.path.isfile(join(out_path, "summary.tsv"))


def test_summary_pipe_run_nested():
    clean_out(out_path)

    # Superficial testing of run_single
    summary_runner = Summary_Runner()

    summary_runner.run_nested(example_path, out_path)

    assert os.path.isfile(join(out_path, "summary.tsv"))


def test_summary_pipe_run():
    clean_out(out_path)

    # Superficial testing of run
    summary_runner = Summary_Runner(workers=2)

    summary_runner.run([dict(in_path={"quantification": example_path, "annotation": example_path}, out_path=out_path)])
    summary_runner.compute_futures()

    assert summary_runner.processed_ios == [
        {
            "in_path": {
                    'canopus_formula_summary': join(example_path, 'canopus_formula_summary.tsv'),
                    'canopus_structure_summary': join(example_path, 'canopus_structure_summary.tsv'),
                    'denovo_structure_identifications': join(example_path, 'denovo_structure_identifications.tsv'),
                    'formula_identifications': join(example_path, 'formula_identifications.tsv'),
                    'gnps_annotations': join(example_path, 'example_files_fbmn_all_db_annotations.json'),
                    'quantification': join(example_path, 'example_files_iimn_fbmn_quant.csv'),
                    'structure_identifications': join(example_path, 'structure_identifications.tsv'),
                },
            "out_path": join(out_path, "summary.tsv")
        }
    ]


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
