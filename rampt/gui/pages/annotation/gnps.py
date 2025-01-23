#!/usr/bin/env python3

import taipy.gui.builder as tgb
from rampt.gui.pages.common_parts import *

from rampt.steps.annotation.gnps_pipe import GNPS_Runner

gnps_params = GNPS_Runner()


def create_gnps():
    with tgb.part(render="{'annot' in entrypoint.lower()}"):
        tgb.text("###### Select MS2 spectra (.mgf)", mode="markdown")
        create_file_selection(process="gnps", out_node="gnps_annotation_paths")

    # TODO: Select quant file, metadata  (+ additional pairs)


def create_gnps_advanced():
    tgb.text("###### Select mzmine log", mode="markdown")
    create_list_selection(
        process="gnps",
        attribute="mzmine_log",
        extensions="*",
        name="MZmine log file",
        default_value="mzmine_log.txt",
    )
