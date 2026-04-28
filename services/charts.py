from __future__ import annotations

import base64
import io
from typing import Iterable, Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_theme(style="whitegrid")


def _encode_figure(fig) -> str:
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", bbox_inches="tight", facecolor=fig.get_facecolor())
    buffer.seek(0)
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    plt.close(fig)
    return encoded


def bar_chart(labels: Sequence[str], values: Sequence[float], *, title: str, xlabel: str, ylabel: str) -> str | None:
    if not labels:
        return None

    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor("#f7f8fc")
    ax.set_facecolor("#ffffff")
    sns.barplot(x=list(labels), y=list(values), ax=ax, color="#2563eb")
    ax.set_title(title, fontsize=15, fontweight="bold")
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.tick_params(axis="x", rotation=35)
    return _encode_figure(fig)


def line_chart(labels: Sequence[str], values: Sequence[float], *, title: str, xlabel: str, ylabel: str, ymin: float | None = None, ymax: float | None = None) -> str | None:
    if not labels:
        return None

    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor("#f7f8fc")
    ax.set_facecolor("#ffffff")
    sns.lineplot(x=list(labels), y=list(values), ax=ax, color="#0f766e", marker="o")
    ax.set_title(title, fontsize=15, fontweight="bold")
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.tick_params(axis="x", rotation=35)
    if ymin is not None or ymax is not None:
        ax.set_ylim(ymin, ymax)
    return _encode_figure(fig)


def scatter_chart(labels: Sequence[str], x_values: Sequence[float], y_values: Sequence[float], *, title: str, xlabel: str, ylabel: str) -> str | None:
    if not labels:
        return None

    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor("#f7f8fc")
    ax.set_facecolor("#ffffff")
    sns.scatterplot(x=list(labels), y=list(x_values), size=list(y_values), hue=list(y_values), palette="viridis", sizes=(40, 180), ax=ax, legend=False)
    ax.set_title(title, fontsize=15, fontweight="bold")
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.tick_params(axis="x", rotation=35)
    return _encode_figure(fig)

