#!/usr/bin/env python3

import taipy.gui.builder as tgb

from source.helpers.classes import Pipe_Step

class Analysis_Runner(Pipe_Step):
    pass

analysis_params = Analysis_Runner()

def create_analysis():
    tgb.part()