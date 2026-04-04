#!/usr/bin/env python3
# ============================================================
# plot_task2.py — 任务2：多维度参数影响分析 可视化
# ============================================================
#
# 【功能】
#   读取 task2 的三个 CSV 文件，生成以下图表：
#     图A: 块大小(bs) vs IOPS 和带宽 —— 折线图
#     图B: numjobs × iodepth 组合 vs IOPS —— 热力图 + 柱状图
#     图C: I/O引擎对比 —— 分组柱状图
#
# 【使用方法】
#   先运行 task2_test.sh 生成 CSV 文件，然后：
#   python3 plot_task2.py
#
# 【依赖】
#   pip install matplotlib pandas numpy
# ============================================================

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# ============================================================
# 图A：块大小(bs)对性能的影响
# ============================================================
# 【读取数据】
# CSV格式: rw,bs,iops,bw_KBps,lat_us
df_bs = pd.read_csv("task2_bs.csv")

# 为了让X轴按大小正确排序，给bs值赋一个数字顺序
bs_order = ["4k", "16k", "64k", "256k", "1m"]
df_bs["bs"] = pd.Categorical(df_bs["bs"], categories=bs_order, ordered=True)
df_bs = df_bs.sort_values(["rw", "bs"]).reset_index(drop=True)
df_bs["bw_MBps"] = df_bs["bw_KBps"] / 1024.0

# 【画图：每种rw模式画两条线（IOPS和BW）】
# 使用双Y轴：左边IOPS，右边带宽
for rw in df_bs["rw"].unique():
    subset = df_bs[df_bs["rw"] == rw]

    fig, ax1 = plt.subplots(figsize=(9, 5))

    # 左Y轴: IOPS (蓝色折线 + 圆点标记)
    ax1.plot(subset["bs"].astype(str), subset["iops"], 'b-o', linewidth=2,
             markersize=8, label="IOPS", zorder=3)
    ax1.set_xlabel("Block Size (bs)", fontsize=12)
    ax1.set_ylabel("IOPS", fontsize=12, color="blue")
    ax1.tick_params(axis='y', labelcolor="blue")

    # 在每个数据点旁边标注数值
    for i, row in subset.iterrows():
        ax1.annotate(f'{row["iops"]:.0f}',
                     xy=(row["bs"], row["iops"]),
                     xytext=(5, 8), textcoords="offset points",
                     fontsize=8, color="blue")

    # 右Y轴: 带宽 (红色折线 + 方形标记)
    ax2 = ax1.twinx()
    ax2.plot(subset["bs"].astype(str), subset["bw_MBps"], 'r-s', linewidth=2,
             markersize=8, label="BW (MB/s)", zorder=3)
    ax2.set_ylabel("Bandwidth (MB/s)", fontsize=12, color="red")
    ax2.tick_params(axis='y', labelcolor="red")

    for i, row in subset.iterrows():
        ax2.annotate(f'{row["bw_MBps"]:.1f}',
                     xy=(row["bs"], row["bw_MBps"]),
                     xytext=(5, -12), textcoords="offset points",
                     fontsize=8, color="red")

    # 合并图例
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="center right", fontsize=10)

    rw_label = {"randread": "Random Read", "randwrite": "Random Write",
                "read": "Sequential Read", "write": "Sequential Write"}.get(rw, rw)
    plt.title(f"Experiment A: Block Size Impact — {rw_label}\n"
              f"(ioengine=psync, numjobs=1, iodepth=1)", fontsize=13)
    ax1.grid(axis='y', alpha=0.3)
    plt.tight_layout()

    filename = f"task2_bs_{rw}.png"
    plt.savefig(filename, dpi=150)
    print(f"Saved: {filename}")


# ============================================================
# 图B：numjobs × iodepth 对性能的影响
# ============================================================
# CSV格式: rw,numjobs,iodepth,iops,bw_KBps,lat_us
df_jd = pd.read_csv("task2_jobs_depth.csv")

for rw in df_jd["rw"].unique():
    subset = df_jd[df_jd["rw"] == rw]

    # --- 图B-1: 热力图 ---
    # 【什么是热力图？】
    #   把 numjobs 和 iodepth 作为两个维度，
    #   颜色深浅代表 IOPS 高低，一眼就能看出哪种组合性能最好。
    #
    # 将数据整理成矩阵形式：行=numjobs, 列=iodepth, 值=IOPS
    pivot = subset.pivot_table(index="numjobs", columns="iodepth", values="iops")

    fig, ax = plt.subplots(figsize=(8, 5))
    im = ax.imshow(pivot.values, cmap="YlOrRd", aspect="auto")

    # 设置坐标轴标签
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns)
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index)
    ax.set_xlabel("I/O Depth (iodepth)", fontsize=12)
    ax.set_ylabel("Thread Count (numjobs)", fontsize=12)

    # 在每个格子里写上具体的IOPS数值
    for i in range(len(pivot.index)):
        for j in range(len(pivot.columns)):
            val = pivot.values[i, j]
            ax.text(j, i, f'{val:.0f}', ha="center", va="center",
                    fontsize=10, fontweight="bold",
                    color="white" if val > pivot.values.max() * 0.6 else "black")

    plt.colorbar(im, label="IOPS")

    rw_label = {"randread": "Random Read", "randwrite": "Random Write"}.get(rw, rw)
    plt.title(f"Experiment B: Heatmap — {rw_label} IOPS\n"
              f"(bs=4k, ioengine=libaio)", fontsize=13)
    plt.tight_layout()
    filename = f"task2_heatmap_{rw}.png"
    plt.savefig(filename, dpi=150)
    print(f"Saved: {filename}")

    # --- 图B-2: 分组柱状图 ---
    # 【为什么还要柱状图？】
    #   热力图看整体趋势，柱状图看具体数值对比。
    #   每组柱子代表一个 numjobs 值，组内不同颜色代表不同 iodepth。

    fig, ax = plt.subplots(figsize=(10, 6))

    numjobs_vals = sorted(subset["numjobs"].unique())
    iodepth_vals = sorted(subset["iodepth"].unique())
    x = np.arange(len(numjobs_vals))
    width = 0.25  # 每组内每根柱子的宽度
    colors = ["#4C72B0", "#DD8452", "#55A868"]

    for idx, depth in enumerate(iodepth_vals):
        data = subset[subset["iodepth"] == depth].sort_values("numjobs")
        bars = ax.bar(x + idx * width, data["iops"], width,
                      label=f"iodepth={depth}", color=colors[idx], alpha=0.85)
        # 标注数值
        for bar in bars:
            height = bar.get_height()
            ax.annotate(f'{height:.0f}',
                        xy=(bar.get_x() + bar.get_width()/2, height),
                        xytext=(0, 3), textcoords="offset points",
                        ha='center', fontsize=7)

    ax.set_xlabel("Thread Count (numjobs)", fontsize=12)
    ax.set_ylabel("IOPS", fontsize=12)
    ax.set_xticks(x + width)
    ax.set_xticklabels([f"numjobs={v}" for v in numjobs_vals])
    ax.legend(fontsize=10)
    ax.grid(axis='y', alpha=0.3)

    plt.title(f"Experiment B: Concurrency Impact — {rw_label} IOPS\n"
              f"(bs=4k, ioengine=libaio)", fontsize=13)
    plt.tight_layout()
    filename = f"task2_concurrency_{rw}.png"
    plt.savefig(filename, dpi=150)
    print(f"Saved: {filename}")


# ============================================================
# 图C：I/O引擎(ioengine)对比
# ============================================================
# CSV格式: rw,ioengine,iodepth,iops,bw_KBps,lat_us
df_eng = pd.read_csv("task2_ioengine.csv")

for rw in df_eng["rw"].unique():
    subset = df_eng[df_eng["rw"] == rw]

    fig, ax = plt.subplots(figsize=(10, 6))

    # 将数据按 ioengine + iodepth 组合成标签
    # 例如: "psync\n(depth=1)", "libaio\n(depth=1)", "libaio\n(depth=32)"
    bar_labels = []
    iops_vals = []
    colors = []
    # 颜色方案: 不同引擎用不同颜色，depth=1 较浅，depth=32 较深
    engine_colors = {
        "psync":    ("#7FB3D8", "#2878B5"),
        "libaio":   ("#F5C37D", "#E8862A"),
        "io_uring": ("#95D4A4", "#2CA02C"),
        "mmap":     ("#D4A5D0", "#9B59B6"),
    }

    for _, row in subset.iterrows():
        eng = row["ioengine"]
        depth = int(row["iodepth"])
        bar_labels.append(f'{eng}\n(depth={depth})')
        iops_vals.append(row["iops"])
        # depth=1 用浅色(索引0)，depth>1 用深色(索引1)
        color_pair = engine_colors.get(eng, ("#AAAAAA", "#555555"))
        colors.append(color_pair[0] if depth == 1 else color_pair[1])

    bars = ax.bar(bar_labels, iops_vals, color=colors, alpha=0.9, edgecolor="gray", linewidth=0.5)

    # 标注数值
    for bar in bars:
        height = bar.get_height()
        ax.annotate(f'{height:.0f}',
                    xy=(bar.get_x() + bar.get_width()/2, height),
                    xytext=(0, 4), textcoords="offset points",
                    ha='center', fontsize=9, fontweight='bold')

    ax.set_xlabel("I/O Engine (ioengine)", fontsize=12)
    ax.set_ylabel("IOPS", fontsize=12)
    ax.grid(axis='y', alpha=0.3)

    rw_label = {"randread": "Random Read", "randwrite": "Random Write"}.get(rw, rw)
    plt.title(f"Experiment C: I/O Engine Comparison — {rw_label}\n"
              f"(bs=4k, numjobs=1)", fontsize=13)
    plt.tight_layout()
    filename = f"task2_ioengine_{rw}.png"
    plt.savefig(filename, dpi=150)
    print(f"Saved: {filename}")


print("\nAll charts generated.")
print("Generated image files:")
print("  task2_bs_randread.png / task2_bs_randwrite.png")
print("  task2_heatmap_randread.png / task2_heatmap_randwrite.png")
print("  task2_concurrency_randread.png / task2_concurrency_randwrite.png")
print("  task2_ioengine_randread.png / task2_ioengine_randwrite.png")
