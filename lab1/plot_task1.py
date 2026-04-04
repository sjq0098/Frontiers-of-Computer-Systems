#!/usr/bin/env python3
# ============================================================
# plot_task1.py — 任务1：基础性能测试结果可视化
# ============================================================
#
# 【功能】
#   读取 task1_results.csv，生成两张图：
#     1. 四种读写模式的 IOPS 和带宽 柱状图
#     2. 四种读写模式的 平均延迟 柱状图
#
# 【使用方法】
#   先运行 task1_test.sh 生成 CSV 文件，然后：
#   python3 plot_task1.py
#
# 【依赖】
#   pip install matplotlib pandas
# ============================================================

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# ---- 读取数据 ----
# CSV 格式: rw,iops,bw_KBps,lat_us
df = pd.read_csv("task1_results.csv")

# Human-readable English labels for each R/W mode
label_map = {
    "read":      "Sequential Read\n(read)",
    "write":     "Sequential Write\n(write)",
    "randread":  "Random Read\n(randread)",
    "randwrite": "Random Write\n(randwrite)",
}
# Order: sequential read, sequential write, random read, random write
order = ["read", "write", "randread", "randwrite"]
df["order"] = df["rw"].map({v: i for i, v in enumerate(order)})
df = df.sort_values("order").reset_index(drop=True)
labels = [label_map[rw] for rw in df["rw"]]

# 把带宽从 KB/s 转换为 MB/s，更直观
df["bw_MBps"] = df["bw_KBps"] / 1024.0

# ---- 配置 matplotlib 显示 ----
# 如果你的系统支持中文字体，可以取消下面的注释
# plt.rcParams['font.sans-serif'] = ['SimHei', 'WenQuanYi Micro Hei']
# plt.rcParams['axes.unicode_minus'] = False

# ============================================================
# 图1：IOPS 和 带宽 的双轴柱状图
# ============================================================
# 【为什么用双轴？】
#   IOPS 的数量级可能是几千到几万，而带宽可能是几百MB/s，
#   两者量级差别大，放在同一个Y轴会导致其中一个几乎看不见。
#   所以左Y轴画IOPS，右Y轴画带宽。

fig, ax1 = plt.subplots(figsize=(10, 6))

x = np.arange(len(labels))    # X轴位置: [0, 1, 2, 3]
width = 0.35                   # 柱子宽度

# 左Y轴: IOPS（蓝色柱子）
bars1 = ax1.bar(x - width/2, df["iops"], width, label="IOPS", color="#4C72B0", alpha=0.85)
ax1.set_xlabel("Read/Write Mode", fontsize=12)
ax1.set_ylabel("IOPS", fontsize=12, color="#4C72B0")
ax1.tick_params(axis='y', labelcolor="#4C72B0")
ax1.set_xticks(x)
ax1.set_xticklabels(labels, fontsize=10)

# 在柱子上方标注具体数值
for bar in bars1:
    height = bar.get_height()
    ax1.annotate(f'{height:.0f}',
                 xy=(bar.get_x() + bar.get_width()/2, height),
                 xytext=(0, 4), textcoords="offset points",
                 ha='center', va='bottom', fontsize=8, color="#4C72B0")

# 右Y轴: 带宽（橙色柱子）
ax2 = ax1.twinx()  # 创建共享X轴的第二个Y轴
bars2 = ax2.bar(x + width/2, df["bw_MBps"], width, label="BW (MB/s)", color="#DD8452", alpha=0.85)
ax2.set_ylabel("Bandwidth (MB/s)", fontsize=12, color="#DD8452")
ax2.tick_params(axis='y', labelcolor="#DD8452")

for bar in bars2:
    height = bar.get_height()
    ax2.annotate(f'{height:.1f}',
                 xy=(bar.get_x() + bar.get_width()/2, height),
                 xytext=(0, 4), textcoords="offset points",
                 ha='center', va='bottom', fontsize=8, color="#DD8452")

# 合并图例
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper right", fontsize=10)

plt.title("Task 1: IOPS & Bandwidth by R/W Mode\n(bs=4k, ioengine=psync, numjobs=1, iodepth=1)", fontsize=13)
plt.tight_layout()
plt.savefig("task1_iops_bw.png", dpi=150)
print("Saved: task1_iops_bw.png")

# ============================================================
# 图2：平均延迟柱状图
# ============================================================

fig, ax = plt.subplots(figsize=(8, 5))

bars = ax.bar(labels, df["lat_us"], color=["#4C72B0", "#55A868", "#C44E52", "#8172B2"], alpha=0.85)
ax.set_xlabel("Read/Write Mode", fontsize=12)
ax.set_ylabel("Average Latency (us)", fontsize=12)

# 标注数值
for bar in bars:
    height = bar.get_height()
    ax.annotate(f'{height:.1f} us',
                xy=(bar.get_x() + bar.get_width()/2, height),
                xytext=(0, 4), textcoords="offset points",
                ha='center', va='bottom', fontsize=9)

plt.title("Task 1: Average Latency by R/W Mode\n(bs=4k, ioengine=psync, numjobs=1, iodepth=1)", fontsize=13)
plt.tight_layout()
plt.savefig("task1_latency.png", dpi=150)
print("Saved: task1_latency.png")

print("\nAll charts generated.")
