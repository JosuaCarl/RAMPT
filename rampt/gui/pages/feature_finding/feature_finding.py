#!/usr/bin/env python3

import taipy.gui.builder as tgb
from ..common_parts import *

from rampt.steps.feature_finding.mzmine_pipe import MZmine_Runner


feature_finding_params = MZmine_Runner()

mzmine_default_folder = os.path.join(Path.home(), ".mzmine", "users")


def create_feature_finding():
    tgb.text("###### File selection", mode="markdown")
    create_file_selection(process="feature_finding", out_node="processed_data_paths")

    tgb.html("br")

    tgb.text("###### Batch selection", mode="markdown")
    create_list_selection(process="feature_finding", extensions=".mzbatch,.xml")

    tgb.html("br")

    tgb.text("###### User file selection", mode="markdown")
    create_list_selection(
        process="feature_finding",
        attribute="user",
        extensions=".mzuser",
        default_value=mzmine_default_folder,
    )

    with tgb.expandable(
        title="Advanced", hover_text="Advanced settings for feature finding", expanded=False
    ):
        create_advanced_settings()

        create_exec_selection(process="feature_finding", exec_name="mzmine_console")

        tgb.html("br")
        with tgb.layout(columns="1 1", columns__mobile="1", gap="5%"):
            ## Login
            tgb.input(
                "{feature_finding_params.login}",
                label="Login command",
                hover_text="User command for (online) login: Overwritten by delection of user.",
            )

            ## Formats
            tgb.input(
                "{feature_finding_params.valid_formats}",
                label="Valid formats",
                hover_text="List of valid formats, separated by ','",
                on_change=lambda state, var, val: set_attribute_recursive(
                    state, "feature_finding_params.valid_formats", val.split(","), refresh=True
                ),
            )

        # Other
        tgb.text("###### Other:", mode="markdown")
        with tgb.part():
            tgb.input(
                "{feature_finding_params.additional_args}",
                label="Additional arguments",
                hover_text="Additional arguments that can be given to the mzmine (works with command line interface).",
            )
