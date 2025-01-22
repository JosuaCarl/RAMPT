#!/usr/bin/env python3

import taipy.gui.builder as tgb
from rampt.gui.pages.common_parts import *

from rampt.steps.annotation.gnps_pipe import GNPS_Runner

gnps_params = GNPS_Runner()


def create_gnps():
    tgb.text("###### File selection", mode="markdown")
    create_file_selection(process="gnps", out_node="gnps_annotation_paths", )

    tgb.html("br")

    tgb.text("###### MZmine log selection", mode="markdown")
    create_list_selection(
        process="gnps",
        attribute="mzmine_log",
        extensions="*",
        name="MZmine log file",
        default_value="mzmine_log.txt",
    )
