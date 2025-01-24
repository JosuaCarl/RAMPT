#!/usr/bin/env python3

import taipy.gui.builder as tgb
from rampt.gui.pages.common_parts import *

from rampt.steps.analysis.summary_pipe import Summary_Runner

summary_params = Summary_Runner()


# TODO: Implement passing of two files to scheduled_ios
def create_summary():
    with tgb.part(render="{'summ' in entrypoint.lower()}"):
        tgb.text("###### Select quantification table (.csv)", mode="markdown")
        create_file_selection(process="summary", io_key="quantification")

    with tgb.part(render="{'summ' in entrypoint.lower()}"):
        tgb.text("###### Select annotation data", mode="markdown")
        create_file_selection(process="summary", io_key="annotation")


def create_summary_advanced():
    pass
