#!/usr/bin/env python3

import taipy.gui.builder as tgb
from rampt.gui.pages.common_parts import *

from rampt.steps.analysis.analysis_pipe import Analysis_Runner

analysis_params = Analysis_Runner()


def create_analysis():
    with tgb.part(render="{'anal' in entrypoint.lower()}"):
        tgb.text("###### Select summary (.tsv)", mode="markdown")
        create_file_selection(process="analysis", out_node="analysis_data_paths")


def create_analysis_advanced():
    pass
