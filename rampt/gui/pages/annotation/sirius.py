#!/usr/bin/env python3

import taipy.gui.builder as tgb
from rampt.gui.pages.common_parts import *

from rampt.steps.annotation.sirius_pipe import Sirius_Runner


sirius_params = Sirius_Runner()
sirius_params.config = os.path.join(ROOT_DIR, "statics", "batch_files", "sirius_default_config.txt")


def create_sirius():
    tgb.text("###### File selection", mode="markdown")
    create_file_selection(process="sirius", out_node="sirius_annotation_paths", )

    tgb.html("br")

    tgb.text("###### Config selection", mode="markdown")
    create_list_selection(
        process="sirius", attribute="config", extensions="*", name="configuration"
    )

    create_advanced_settings()

    create_exec_selection(process="sirius", exec_name="sirius")

    tgb.html("br")

    create_list_selection(
        process="sirius",
        attribute="projectspace",
        name="projectspace",
        default_value="projectspace",
    )
