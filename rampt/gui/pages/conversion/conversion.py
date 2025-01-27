#!/usr/bin/env python3

import taipy.gui.builder as tgb
from rampt.gui.pages.common_parts import *

from rampt.steps.conversion.msconv_pipe import MSconvert_Runner


conversion_params = MSconvert_Runner()


def create_conversion():
    with tgb.part(render="{'conv' in entrypoint.lower()}"):
        tgb.text("###### Select raw data", mode="markdown")
        create_file_selection(
            process="conversion",
            pipe_step=conversion_params, file_dialog_kwargs={"multiple": True} # Activate if open mutiple dir found
        )


def create_conversion_advanced():
    create_exec_selection(process="conversion", exec_name="msconvert")

    tgb.html("br")
    tgb.selector(
        "{conversion_params.target_format}",
        label="Target format",
        lov="mzML;mzXML",
        dropdown=True,
        hover_text="The target format for the conversion. mzML is recommended.",
        width="100px",
    )

    # Other
    tgb.html("br")
    tgb.text("###### Other:", mode="markdown")
    with tgb.layout(columns="1 1", columns__mobile="1", gap="5%"):
        with tgb.part():
            tgb.number(
                "{conversion_params.redo_threshold}",
                label="Redo-threshold",
                hover_text="File size threshold for repeating the conversion.",
            )
        with tgb.part():
            tgb.input(
                "{conversion_params.additional_args}",
                label="Additional arguments",
                hover_text="Additional arguments that can be given to the msconvert (works with command line interface).",
            )
