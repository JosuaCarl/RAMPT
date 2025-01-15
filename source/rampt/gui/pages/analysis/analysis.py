#!/usr/bin/env python3

import taipy.gui.builder as tgb
from ..common_parts import *

from ....steps.analysis.analysis_pipe import Analysis_Runner

analysis_params = Analysis_Runner()


# TODO: Implement analysis
def create_analysis():
	tgb.text("###### File selection", mode="markdown")
	create_file_selection(process="analysis", out_node="analysis_data")
