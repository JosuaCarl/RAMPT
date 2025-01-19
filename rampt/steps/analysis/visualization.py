#!/usr/bin/env python3
"""
Visualize metabolomic data
"""

from rampt.helpers.general import *
from rampt.helpers.logging import *

import pandas as pd
import numpy as np


import plotly.express as px
import plotly.graph_objects as go


def read_df(path: StrPath) -> pd.DataFrame:
    if str(path).endswith("tsv"):
        df = pd.read_csv(path, sep="\t")
    elif str(path).endswith("csv"):
        df = pd.read_csv(path)
    else:
        df = pd.read_excel(path)

    df = df[[col for col in df.columns if "Unnamed: " not in col]]
    return df


def get_peaks_df(df: pd.DataFrame, index_col=None) -> pd.DataFrame:
    peaks_df = df[
        [col for col in df.columns if "peak area" in col.lower() or "peak height" in col.lower()]
    ]
    if index_col and index_col in df.columns:
        peaks_df.index = df[index_col].sort_values()
    return peaks_df


# Plotting
def plot_quantification_heatmap(quantifications_df: pd.DataFrame, **kwargs) -> go.Figure:
    figure = go.Figure()
    figure.add_trace(
        go.Heatmap(
            x=quantifications_df.columns,
            y=quantifications_df.index,
            z=quantifications_df,
            colorscale="Inferno",
            **kwargs,
        )
    )
    figure.update_layout({"height": 800})
    return figure


def plot_signal_intensity_distribution(quantifications_df: pd.DataFrame, **kwargs) -> go.Figure:
    summed_signals = pd.DataFrame({"Signal intensity": quantifications_df.sum()})
    figure = px.histogram(summed_signals, x="Signal intensity", nbins=20, **kwargs)
    figure.update_layout(yaxis_title="Number of strains (#)")
    return figure


def plot_heatmap(df, range: tuple[float] = None, **kwargs):
    figure = go.Figure()
    figure.add_trace(
        go.Heatmap(
            z=df,
            zmin=range[0] if range else None,
            zmax=range[1] if range else None,
            colorscale="Tropic",
            **kwargs,
        )
    )
    figure.update_layout({"height": 800})
    return figure


def plot_cutoff_accumulation(
    zscores: pd.DataFrame,
    cutoff_range: tuple,
    axis: int = 0,
    sample_marker=None,
    jitter: float = 0.5,
    marker_size: int = 6,
    template: str = "seaborn",
    **kwargs,
):
    score_cutoffs = pd.DataFrame(
        {i: np.sum((zscores > i) | (zscores < -i), axis=axis) for i in range(*cutoff_range)}
    )
    names = score_cutoffs.index
    if sample_marker:
        marked_samples = [sample_marker in name for name in names]
        score_cutoffs[sample_marker] = marked_samples
        figure = px.strip(
            score_cutoffs, color=sample_marker, hover_name=names, template=template, **kwargs
        )
    else:
        figure = px.strip(score_cutoffs, hover_name=names, template=template, **kwargs)
    figure.update_layout(
        xaxis_title="z-score cutoff",
        yaxis_title="Strains per metabolites" if axis else "Metabolites per strain",
        hovermode="x",
    )
    figure.update_traces(jitter=jitter, marker={"size": marker_size})
    # fig.data[0].update(span = (0, None), spanmode='manual')
    figure.show()
