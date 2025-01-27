#!/usr/bin/env python3

import taipy.gui.builder as tgb

from rampt.gui.helpers import *


def create_expandable_setting(
    create_methods: dict, title: str, hover_text: str = "", expanded=False, **kwargs
):
    with tgb.expandable(title=title, hover_text=hover_text, expanded=expanded, **kwargs):
        with tgb.layout(columns="0.02 1 0.02", gap="2%"):
            tgb.part()
            with tgb.part():
                for title, create_method in create_methods.items():
                    with tgb.part(class_name="segment-box"):
                        if title:
                            tgb.text(f"##### {title}", mode="markdown")
                        create_method()
                    tgb.html("br")
            tgb.part()



## File selection
uploaded_paths = {}
select_folders = {}

selection_trees_pruned = {}
selection_trees_full = {}

selected = {}

run_styles = {}
run_style = {}

possible_inputs = {}
selected_input = {}
locked_inputs = {}


def create_file_selection(
    process: str,
    pipe_step,
    param_attribute_in: str = "scheduled_ios",
    file_dialog_kwargs: dict = {},
):
    naming_list = [process, param_attribute_in]

    # Construct intermediary dicts
    selector_id = "_".join(naming_list)

    selection_trees_pruned.update({selector_id: []})
    selection_trees_full.update({selector_id: []})
    uploaded_paths.update({selector_id: "."})
    select_folders.update({selector_id: False})
    selected.update({selector_id: []})

    
    run_styles.update({selector_id: [list(run.keys())[0] for run in pipe_step.valid_runs]})
    run_style.update({selector_id: ""})

    possible_inputs.update({selector_id: []})
    selected_input.update({selector_id: ""})
    locked_inputs.update({selector_id: []})

    def construct_selection_tree(state, new_path: StrPath = None):
        """
        Make the selection tree

        :param state: State of taipy
        :type state: State
        :param new_path: Added path (selected in file_selector), defaults to None
        :type new_path: StrPath, optional
        """
        new_path = (
            new_path
            if new_path
            else get_attribute_recursive(state, f"uploaded_paths.{selector_id}")
        )

        if new_path != ".":
            selection_trees_full[selector_id] = path_nester.update_nested_paths(
                selection_trees_full[selector_id], new_paths=new_path
            )
            pruned_tree = path_nester.prune_lca(nested_paths=selection_trees_full[selector_id])
            set_attribute_recursive(state, f"selection_trees_pruned.{selector_id}", pruned_tree)

    def update_selection(state, name, value):
        """
        Merge values of selection with I/O dictionary

        :param state: State of taipy application
        :type state: State
        :param name: Name of variable
        :type name: str
        :param value: Selected value (usually dict)
        :type value: Any
        """
        # Extract selected path from value-dict
        selected_labels = [
            element.get("label") if isinstance(element, dict) else element for element in value
        ]
        
        # Get selected input
        selected_input = get_attribute_recursive(state, f"selected_input.{selector_id}")
        if selected_input:
            in_paths_key = "_".join(selected_input.split(" "))
            
            in_paths_list = get_attribute_recursive(state, f"{process}_params.{param_attribute_in}")
            if in_paths_list:
                in_paths_dictionary = in_paths_list[-1]
                pipe_step = get_attribute_recursive(state, f"{process}_params")
                valid_runs = [
                    {
                        key: {"in_paths": value["in_paths"]}
                        for key, value in vr.copy().items()
                    }
                    for vr in pipe_step.valid_runs
                ]
                if get_attribute_recursive(state, f"run_style.{selector_id}") in pipe_step.check_io(io={"in_paths": in_paths_dictionary}, valid_runs=valid_runs):
                    in_paths_list.append({in_paths_key: selected_labels})
                else:
                    in_paths_dictionary.update({in_paths_key: selected_labels})
                    in_paths_list[-1] = in_paths_dictionary
            else:
                in_paths_list = [{in_paths_key: selected_labels}]
            
            if in_paths_list[-1]:
                set_attribute_recursive(state, f"locked_inputs.{selector_id}", list(in_paths_list[-1].keys()))
            set_attribute_recursive(
                state, f"{process}_params.{param_attribute_in}", in_paths_list, refresh=True
            )
        else:
            logger.log("No input selected.")

    def reset_package(state, *args):
        in_paths_list = get_attribute_recursive(state, f"{process}_params.{param_attribute_in}")
        if in_paths_list:
            in_paths_list[-1] = {}

        set_attribute_recursive(state, f"locked_inputs.{selector_id}", [])
        set_attribute_recursive(
            state, f"{process}_params.{param_attribute_in}", in_paths_list, refresh=True
        )

    def make_input_selector(state):
        run_style = get_attribute_recursive(state, f"run_style.{selector_id}")
        valid_runs = get_attribute_recursive(state, f"{process}_params.valid_runs")
        valid_run = [vr.get(run_style) for vr in valid_runs if list(vr.keys())[0] == run_style][0]
        in_paths_keys = list(valid_run["in_paths"].keys())

        set_attribute_recursive(state, f"possible_inputs.{selector_id}", in_paths_keys)

    # Run_style
    tgb.text("What data do you want to select for your run ?", mode="markdown")
    with tgb.part():
        tgb.selector(
            f"{{run_style.{selector_id}}}",
            lov=f"{{run_styles.{selector_id}}}",
            label="Select run style",
            filter=True,
            dropdown=True,
            on_change=lambda state, name, val: make_input_selector(state)
    )
        
    # Input type
    with tgb.layout(columns="2 2 1", columns__mobile="1", gap="5%"):
        tgb.selector(
            f"{{selected_input.{selector_id}}}",
            lov=f"{{possible_inputs.{selector_id}}}",
            label="Select input type",
            filter=True,
            dropdown=True
        )
        tgb.selector(
            f"{{locked_inputs.{selector_id}}}",
            lov=f"{{possible_inputs.{selector_id}}}",
            label="In execution package",
            mode="check",
            multiple=True,
            active=False,
        )
        tgb.button(
            label="Reset package",
            on_action=lambda state, id, payload: reset_package(state)
        )


    with tgb.layout(columns="1 4", columns__mobile="1", gap="5%"):
        # Selector
        with tgb.part():
            tgb.toggle(f"{{select_folders.{selector_id}}}", label="Select folder")
            with tgb.part(render="{local}"):
                tgb.button(
                    "Select in",
                    on_action=lambda state: construct_selection_tree(
                        state,
                        open_file_folder(
                            select_folder=get_attribute_recursive(
                                state, f"select_folders.{selector_id}"
                            ),
                            **file_dialog_kwargs,
                        ),
                    ),
                )
            with tgb.part(render="{not local}"):
                tgb.file_selector(
                    f"{{uploaded_paths.{selector_id}}}",
                    label="Select in",
                    extensions="*",
                    drop_message=f"Drop files/folders for {process} here:",
                    multiple=True,
                    on_action=lambda state: construct_selection_tree(state),
                )

        # Selection tree
        tgb.tree(
            f"{{selected.{selector_id}}}",
            lov=f"{{selection_trees_pruned.{selector_id}}}",
            label=f"Select in for {process}",
            filter=True,
            multiple=process in ["conversion", "feature_finding"],
            expanded=True,
            on_change=lambda state, name, value: update_selection(state, name, value),
        )


# List selectors
list_options = {}
list_uploaded = {}
list_selected = {}


def create_list_selection(
    process: str,
    attribute: str = "batch",
    extensions: str = "*",
    name: str = "batch file",
    default_value=str(Path.home()),
    file_dialog_kwargs: dict = {},
):
    selector_id = f"{process}_{attribute}"
    list_options.update({selector_id: []})
    list_uploaded.update({selector_id: ""})
    list_selected.update({selector_id: default_value})

    def construct_selection_list(state, new_path: StrPath = None):
        new_path = (
            new_path if new_path else get_attribute_recursive(state, f"list_uploaded.{selector_id}")
        )

        if new_path:
            if new_path not in list_options:
                list_options[selector_id].append(new_path)
            set_attribute_recursive(state, f"list_options.{selector_id}", list_options[selector_id])

    def update_selection(state, name, value):
        set_attribute_recursive(state, f"{process}_params.{attribute}", value, refresh=True)

    with tgb.layout(columns="1 4", columns__mobile="1", gap="5%"):
        with tgb.part(render="{local}"):
            tgb.button(
                f"Select {name}",
                on_action=lambda state: construct_selection_list(
                    state,
                    open_file_folder(
                        multiple=False,
                        filetypes=[
                            (f"{ext[1:]} files", f"*{ext}") for ext in extensions.split(",")
                        ],
                        initialdir=get_directory(default_value),
                        **file_dialog_kwargs,
                    ),
                ),
            )
        with tgb.part(render="{not local}"):
            tgb.file_selector(
                f"{{list_uploaded.{selector_id}}}",
                label=f"Select {name}",
                extensions=extensions,
                drop_message=f"Drop {name} for {process} here:",
                multiple=False,
                on_action=lambda state: construct_selection_list(state),
            )

        tgb.selector(
            f"{{list_selected.{selector_id}}}",
            lov=f"{{list_options.{selector_id}}}",
            label=f"Select a {name} for {process}",
            filter=True,
            multiple=False,
            mode="radio",
            on_change=lambda state, name, value: update_selection(state, name, value),
        )


def set_if_chosen(state, attribute: str):
    selected_path = open_file_folder(multiple=False)
    if selected_path:
        set_attribute_recursive(state, attribute, refresh=True)


def create_exec_selection(
    process: str, exec_name: str, exec_attribute="exec_path", render: str = True
):
    with tgb.part(render=render):
        with tgb.layout(columns="1 1 1 1", columns__mobile="1", gap="5%"):
            tgb.button(
                "Select executable",
                active="{local}",
                on_action=lambda state: set_if_chosen(state, f"{process}_params.exec_path"),
            )
            tgb.input(
                f"{{{process}_params.{exec_attribute}}}",
                active="{local}",
                label=f"`{exec_name}` executable",
                hover_text=f"You may enter the path to {exec_name}.",
            )
            tgb.part()
            tgb.part()
