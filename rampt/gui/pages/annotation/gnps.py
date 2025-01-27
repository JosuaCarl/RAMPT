#!/usr/bin/env python3

import taipy.gui.builder as tgb
from rampt.gui.pages.common_parts import *

from rampt.steps.annotation.gnps_pipe import GNPS_Runner

gnps_params = GNPS_Runner()


def create_gnps():
    with tgb.part(render="{'annot' in entrypoint.lower()}"):
        tgb.text("#### GNPS/FBMN", mode="markdown")

        tgb.text("###### Select GNPS/FBMN input", mode="markdown")
        create_file_selection(process="gnps", pipe_step=gnps_params)


def create_gnps_advanced():
    pass
