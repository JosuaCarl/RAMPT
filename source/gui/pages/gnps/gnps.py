#!/usr/bin/env python3

import taipy.gui.builder as tgb

from source.annotation.gnps_pipe import GNPS_Runner

gnps_params = GNPS_Runner()

with tgb.Page() as gnps:
    tgb.part()