#!/usr/bin/env python3

import taipy.gui.builder as tgb
from rampt.gui.pages.common_parts import *

from rampt.steps.analysis.summary_pipe import Summary_Runner

summary_params = Summary_Runner()


# TODO: Implement passing of two files to scheduled_in
def create_summary():
    tgb.text("###### File selection (quantification)", mode="markdown")
    create_file_selection(
        process="summary", execution_key_in="quantification", out_node="summary_data"
    )

    tgb.text("###### File selection (annotation)", mode="markdown")
    create_file_selection(process="summary", execution_key_in="annotation", out_node="summary_data")
