#!/usr/bin/env python3

import taipy.gui.builder as tgb
from rampt.gui.pages.common_parts import *

from rampt.steps.annotation.gnps_pipe import GNPS_Runner

gnps_params = GNPS_Runner()


def create_gnps():
    with tgb.part(render="{'annot' in entrypoint.lower()}"):
        tgb.text("#### GNPS", mode="markdown")

        tgb.text("###### Select feature quantification (.csv)", mode="markdown")
        create_file_selection(process="gnps", io_key="feature_quantification")

        tgb.text("###### Select MS2 spectra (.mgf)", mode="markdown")
        create_file_selection(process="gnps", io_key="feature_ms2")

        tgb.text("###### Select sample metadata", mode="markdown")
        create_file_selection(process="gnps", io_key="sample_metadata")

        tgb.text("###### Select additional pairs", mode="markdown")
        create_file_selection(process="gnps", io_key="additional_pairs")

    # TODO: Select quant file, metadata  (+ additional pairs)


def create_gnps_advanced():
    tgb.text("###### Select mzmine log", mode="markdown")
    create_file_selection(process="gnps", io_key="mzmine_log")
