#!/usr/bin/env python3

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


RESULTS_DIR = Path("results")
FIGURES_DIR = Path("figures")


def load_csv(name: str) -> pd.DataFrame:
    path = RESULTS_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"missing input CSV: {path}")
    return pd.read_csv(path)


def plot_percentiles(df: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(df["percentile"], df["latency_us"], color="#4C72B0")
    ax.set_title("Task2 Write Latency Percentiles")
    ax.set_xlabel("Percentile")
    ax.set_ylabel("Latency (us)")
    ax.set_yscale("log")
    ax.grid(axis="y", linestyle="--", alpha=0.3)

    for bar in bars:
        height = bar.get_height()
        ax.annotate(
            f"{height:.2f}",
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 4),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=9,
        )

    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "task2_percentiles.png", dpi=150)
    plt.close(fig)


def plot_timeline(df: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.scatter(df["op_index"], df["latency_us"], s=4, alpha=0.6, color="#C44E52")
    ax.set_title("Task2 Write Latency Timeline")
    ax.set_xlabel("Operation Index")
    ax.set_ylabel("Latency (us)")
    ax.set_yscale("log")
    ax.grid(True, linestyle="--", alpha=0.3)

    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "task2_latency_timeline.png", dpi=150)
    plt.close(fig)


def main() -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    percentiles_df = load_csv("task2_percentiles.csv")
    raw_df = load_csv("task2_latency_raw.csv")

    plot_percentiles(percentiles_df)
    plot_timeline(raw_df)

    print("Generated:")
    print("  figures/task2_percentiles.png")
    print("  figures/task2_latency_timeline.png")


if __name__ == "__main__":
    main()
