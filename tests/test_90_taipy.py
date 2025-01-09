#!/usr/bin/env python
"""
Testing final Taipy integration.
"""

from tests.common import *
from source.gui.pages.root import *

from taipy.core.submission.submission_status import SubmissionStatus


platform = get_platform()
filepath = get_internal_filepath(__file__)
(
	out_path,
	mock_path,
	example_path,
	batch_path,
) = contruct_common_paths(filepath)
make_out(out_path)


def load_params(path: StrPath = None):
	with open(path, "r") as file:
		params = json.load(file)
	return params


match_data_node = {  # IO Data
	"raw_data": ["conversion_params.scheduled_in"],
	"community_formatted_data": [
		"feature_finding_params.scheduled_in",
		"conversion_params.processed_out",
	],
	"processed_data": [
		"gnps_params.scheduled_in",
		"sirius_params.scheduled_in",
		"feature_finding_params.processed_out",
	],
	"gnps_annotations": ["analysis_params.scheduled_in", "gnps_params.processed_out"],
	"sirius_annotations": ["analysis_params.scheduled_in", "sirius_params.processed_out"],
	"results": ["analysis_params.processed_out"],
	# Batches and more
	"mzmine_batch": ["feature_finding_params.batch"],
	"mzmine_log": ["feature_finding_params.log_paths", "gnps_params.mzmine_log"],
	"sirius_config": ["sirius_params.config"],
	"sirius_projectspace": ["sirius_params.projectspace"],
}


def update_scenario(scenario, params):
	data_nodes = params.copy()

	for data_node_key, attribute_keys in match_data_node.items():
		for state_attribute in attribute_keys:
			attribute_split = state_attribute.split(".")
			value = params.get(attribute_split[0]).get(attribute_split[1])
			if value:
				data_nodes[data_node_key] = value

	for key, data_node in scenario.data_nodes.items():
		if data_nodes.get(key):
			data_node.write(data_nodes.get(key))

	return scenario


def check_submission(entity, counter: int, time: float | int, unit: str):
	submission = tp.submit(entity)

	if submission.submission_status == SubmissionStatus.BLOCKED:
		for id, task in scenario.tasks.items():
			ic(f"Task: {id} Properties: {task.properties}, Context: {task._is_in_context}")
			ic(task.input)
			ic(task.output)
			for node_id, data_node in task.data_nodes.items():
				ic(f"Node: {node_id}, Content: {data_node}")

	for i in tqdm(range(counter)):
		if submission.submission_status in [SubmissionStatus.RUNNING] or (
			submission.submission_status in [SubmissionStatus.SUBMITTED, SubmissionStatus.PENDING]
			and i < 1
		):
			wait(time, unit)

	assert submission.submission_status == SubmissionStatus.COMPLETED


def prepare_out():
	clean_out(out_path)
	os.mkdir(os.path.join(out_path, "raw"))
	shutil.copyfile(
		os.path.join(example_path, "minimal.mzML"), os.path.join(out_path, "raw", "minimal.mzML")
	)


###### TESTS ######


def test_start_orchestrator():
	orchestrator = tp.Orchestrator()
	orchestrator.run(force_restart=True)


@pytest.mark.dependency(depends=["test_start_orchestrator"])
def test_taipy_simple_scenario():
	prepare_out()

	scenario = tp.create_scenario(ms_analysis_config)

	params = load_params(os.path.join(batch_path, "Example_parameters.json"))
	scenario = update_scenario(scenario=scenario, params=params)

	# write relevant nodes
	scenario.data_nodes.get("raw_data").write([os.path.join(out_path, "raw", "minimal.mzML")])
	scenario.data_nodes.get("mzmine_batch").write([os.path.join(batch_path, "minimal.mzbatch")])
	scenario.data_nodes.get("sirius_config").write([os.path.join(batch_path, "sirius_config.txt")])

	# write out nodes
	scenario.data_nodes.get("conversion_out").write(None)
	scenario.data_nodes.get("feature_finding_out").write(None)
	scenario.data_nodes.get("gnps_out").write(None)
	scenario.data_nodes.get("sirius_out").write(None)
	scenario.data_nodes.get("results_out").write(None)

	# Submit steps
	check_submission(
		entity=scenario.sequences.get("conversion"), counter=30, time=5.0, unit="seconds"
	)
	assert os.path.isfile(os.path.join(out_path, "raw", "converted", "minimal.mzML"))
	assert os.path.isfile(os.path.join(out_path, "raw", "converted", "msconvert_log.txt"))

	check_submission(
		entity=scenario.sequences.get("feature finding"), counter=60, time=5.0, unit="seconds"
	)
	assert os.path.isfile(
		os.path.join(out_path, "raw", "converted", "processed", "processed_iimn_fbmn_quant.csv")
	)
	assert os.path.isfile(
		os.path.join(out_path, "raw", "converted", "processed", "processed_iimn_fbmn.mgf")
	)
	assert os.path.isfile(
		os.path.join(out_path, "raw", "converted", "processed", "processed_sirius.mgf")
	)
	assert os.path.isfile(os.path.join(out_path, "raw", "converted", "processed", "mzmine_log.txt"))

	check_submission(entity=scenario.sequences.get("gnps"), counter=30, time=1, unit="minute")
	assert os.path.isfile(
		os.path.join(
			out_path,
			"raw",
			"converted",
			"processed",
			"annotated",
			"processed_gnps_all_db_annotations.json",
		)
	)

	check_submission(entity=scenario.sequences.get("sirius"), counter=30, time=1, unit="minute")
	assert os.path.isfile(
		os.path.join(
			out_path, "raw", "converted", "processed", "annotated", "formula_identifications.tsv"
		)
	)
	assert os.path.isfile(
		os.path.join(
			out_path, "raw", "converted", "processed", "annotated", "structure_identifications.tsv"
		)
	)
	assert os.path.isfile(
		os.path.join(
			out_path,
			"raw",
			"converted",
			"processed",
			"annotated",
			"denovo_structure_identifications.tsv",
		)
	)
	assert os.path.isfile(
		os.path.join(
			out_path, "raw", "converted", "processed", "annotated", "canopus_structure_summary.tsv"
		)
	)
	assert os.path.isfile(
		os.path.join(out_path, "raw", "converted", "processed", "annotated", "sirius_log.txt")
	)

	check_submission(
		entity=scenario.sequences.get("analysis"), counter=30, time=5.0, unit="seconds"
	)
	# assert os.path.isfile( os.path.join( out_path, "raw", "converted", "processed", "annotated", "results", "analysis_log.txt" ) )


@pytest.mark.dependency(depends=["test_taipy_simple_scenario"])
def test_taipy_scenario_out_change():
	prepare_out()

	scenario = tp.create_scenario(ms_analysis_config)

	params = load_params(os.path.join(batch_path, "Example_parameters_nested_parallel.json"))
	scenario = update_scenario(scenario=scenario, params=params)

	# write relevant nodes
	scenario.data_nodes.get("raw_data").write([os.path.join(out_path, "raw", "minimal.mzML")])
	scenario.data_nodes.get("mzmine_batch").write([os.path.join(batch_path, "minimal.mzbatch")])
	scenario.data_nodes.get("sirius_config").write([os.path.join(batch_path, "sirius_config.txt")])

	# write out nodes
	scenario.data_nodes.get("conversion_out").write([os.path.join(out_path, "converted_explicit")])
	scenario.data_nodes.get("feature_finding_out").write([os.path.join(out_path, "")])
	scenario.data_nodes.get("gnps_out").write([os.path.join(out_path, "annotated_explicit")])
	scenario.data_nodes.get("sirius_out").write([os.path.join(out_path, "annotated_explicit")])
	scenario.data_nodes.get("results_out").write([os.path.join(out_path, "results_explicit")])

	# Submit steps
	check_submission(
		entity=scenario.sequences.get("conversion"), counter=30, time=5.0, unit="seconds"
	)
	assert os.path.isfile(os.path.join(out_path, "converted_explicit", "minimal.mzML"))
	assert os.path.isfile(os.path.join(out_path, "converted_explicit", "msconvert_log.txt"))

	check_submission(
		entity=scenario.sequences.get("feature finding"), counter=60, time=5.0, unit="seconds"
	)
	assert os.path.isfile(
		os.path.join(out_path, "processed_explicit", "processed_explicit_iimn_fbmn_quant.csv")
	)
	assert os.path.isfile(
		os.path.join(out_path, "processed_explicit", "processed_explicit_iimn_fbmn.mgf")
	)
	assert os.path.isfile(
		os.path.join(out_path, "processed_explicit", "processed_explicit_sirius.mgf")
	)
	assert os.path.isfile(os.path.join(out_path, "processed_explicit", "mzmine_log.txt"))

	check_submission(entity=scenario.sequences.get("gnps"), counter=30, time=1, unit="minute")
	assert os.path.isfile(
		os.path.join(
			out_path, "annotated_explicit", "processed_explicit_gnps_all_db_annotations.json"
		)
	)

	check_submission(entity=scenario.sequences.get("sirius"), counter=30, time=1, unit="minute")
	assert os.path.isfile(
		os.path.join(out_path, "annotated_explicit", "formula_identifications.tsv")
	)
	assert os.path.isfile(
		os.path.join(out_path, "annotated_explicit", "structure_identifications.tsv")
	)
	assert os.path.isfile(
		os.path.join(out_path, "annotated_explicit", "denovo_structure_identifications.tsv")
	)
	assert os.path.isfile(
		os.path.join(out_path, "annotated_explicit", "canopus_structure_summary.tsv")
	)
	assert os.path.isfile(os.path.join(out_path, "annotated_explicit", "sirius_log.txt"))

	check_submission(
		entity=scenario.sequences.get("analysis"), counter=30, time=5.0, unit="seconds"
	)
	# assert os.path.isfile( os.path.join( out_path, "results_explicit", "analysis_log.txt" ) )


@pytest.mark.dependency(depends=["test_taipy_scenario_out_change"])
def test_taipy_nested_parallel_scenario():
	prepare_out()

	scenario = tp.create_scenario(ms_analysis_config)

	params = load_params(os.path.join(batch_path, "Example_parameters_nested_parallel.json"))
	scenario = update_scenario(scenario=scenario, params=params)

	# write relevant nodes
	scenario.data_nodes.get("raw_data").write([os.path.join(out_path, "raw", "minimal.mzML")])
	scenario.data_nodes.get("mzmine_batch").write([os.path.join(batch_path, "minimal.mzbatch")])
	scenario.data_nodes.get("sirius_config").write([os.path.join(batch_path, "sirius_config.txt")])

	# write out nodes
	scenario.data_nodes.get("conversion_out").write(None)
	scenario.data_nodes.get("feature_finding_out").write(None)
	scenario.data_nodes.get("gnps_out").write(None)
	scenario.data_nodes.get("sirius_out").write(None)
	scenario.data_nodes.get("results_out").write(None)

	# Submit scenario
	check_submission(entity=scenario, counter=60, time=1, unit="minutes")


@pytest.mark.dependency(depends=["test_taipy_nested_parallel_scenario"])
def test_clean():
	clean_out(out_path)
