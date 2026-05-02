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


def plot_qps(csv_name: str, title: str, output_name: str) -> None:
    df = load_csv(csv_name)
    order = {"block_cache": 0, "kv_cache": 1}
    df["order"] = df["mode"].map(order)
    df = df.sort_values("order").reset_index(drop=True)

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(df["mode"], df["qps"], color=["#4C72B0", "#55A868"])
    ax.set_title(title)
    ax.set_xlabel("Mode")
    ax.set_ylabel("QPS")
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

    plot_qps("task3_point_get.csv", "Task3 Point Get QPS", "task3_point_get.png")
    plot_qps("task3_range_scan.csv", "Task3 Range Scan QPS", "task3_range_scan.png")
    plot_qps("task3_mixed.csv", "Task3 Mixed Workload QPS", "task3_mixed.png")

    print("Generated:")
    print("  figures/task3_point_get.png")
    print("  figures/task3_range_scan.png")
    print("  figures/task3_mixed.png")


if __name__ == "__main__":
    main()
