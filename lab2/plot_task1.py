#!/usr/bin/env python3

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


RESULTS_DIR = Path("results")
FIGURES_DIR = Path("figures")


def load_csv(name: str) -> pd.DataFrame:
    path = RESULTS_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"missing input CSV: {path}")
    return pd.read_csv(path)


def plot_grouped_qps(df: pd.DataFrame, x_col: str, title: str, output_name: str) -> None:
    df = df.sort_values(x_col).reset_index(drop=True)
    labels = df[x_col].astype(str).tolist()
    x = np.arange(len(labels))
    width = 0.25

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(x - width, df["seq_write_qps"], width, label="Sequential Write")
    ax.bar(x, df["rand_write_qps"], width, label="Random Write")
    ax.bar(x + width, df["rand_read_qps"], width, label="Random Read")

    ax.set_title(title)
    ax.set_xlabel("Parameter Value")
    ax.set_ylabel("QPS")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.legend()
    ax.grid(axis="y", linestyle="--", alpha=0.3)

    fig.tight_layout()
    fig.savefig(FIGURES_DIR / output_name, dpi=150)
    plt.close(fig)


def plot_bloom_qps(df: pd.DataFrame, output_name: str) -> None:
    df = df.sort_values("bloom_bits").reset_index(drop=True)
    labels = ["Off" if bits == 0 else f"{bits} bits/key" for bits in df["bloom_bits"]]

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(labels, df["rand_read_qps"], color=["#4C72B0", "#55A868"])
    ax.set_title("Task1 Bloom Filter vs Negative Lookup QPS")
    ax.set_xlabel("Bloom Filter")
    ax.set_ylabel("Negative Lookup QPS")
    ax.grid(axis="y", linestyle="--", alpha=0.3)

    for bar in bars:
        height = bar.get_height()
        ax.annotate(
            f"{height:.0f}",
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 4),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=9,
        )

    fig.tight_layout()
    fig.savefig(FIGURES_DIR / output_name, dpi=150)
    plt.close(fig)


def main() -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    write_buffer_df = load_csv("task1_write_buffer_size.csv")
    plot_grouped_qps(
        write_buffer_df,
        "param_value_mb",
        "Task1 Write Buffer Size vs QPS",
        "task1_write_buffer_size.png",
    )

    block_size_df = load_csv("task1_block_size.csv")
    plot_grouped_qps(
        block_size_df,
        "param_value_kb",
        "Task1 Block Size vs QPS",
        "task1_block_size.png",
    )

    bloom_df = load_csv("task1_bloom_filter.csv")
    plot_bloom_qps(bloom_df, "task1_bloom_filter.png")

    print("Generated:")
    print("  figures/task1_write_buffer_size.png")
    print("  figures/task1_block_size.png")
    print("  figures/task1_bloom_filter.png")


if __name__ == "__main__":
    main()
