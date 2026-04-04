#!/bin/bash
# ============================================================
# task1_test.sh — 任务1：基础性能测试（四种读写模式）
# ============================================================
#
# 【实验目的】
#   用相同的参数（bs=4k, ioengine=psync, numjobs=1, iodepth=1），
#   分别测试四种读写模式，观察性能差异。
#
# 【输出文件】
#   task1_results.csv —— 包含每种模式的 IOPS、带宽、延迟
#
# 【使用方法】
#   chmod +x task1_test.sh
#   ./task1_test.sh
#
# 【安全提示】
#   脚本只会在当前目录创建一个测试文件 fio_test_file，
#   绝不会操作裸设备，数据安全无忧。
# ============================================================

# ----- 全局参数（基准配置） -----
BS="4k"              # 块大小：每次I/O读写4KB
IOENGINE="psync"     # I/O引擎：psync是最基本的同步I/O方式
NUMJOBS=1            # 线程数：1个线程
IODEPTH=1            # I/O队列深度：1（同步模式下只能是1）
SIZE="1G"            # 测试文件大小：1GB
RUNTIME=60           # 每次测试运行时长：60秒
FILENAME="fio_test_file"  # 测试文件名（在当前目录创建）

# ----- 输出文件 -----
CSV_FILE="task1_results.csv"

# 写入CSV的表头
# rw: 读写模式, iops: 每秒I/O次数, bw_KBps: 带宽(KB/s), lat_us: 平均延迟(微秒)
echo "rw,iops,bw_KBps,lat_us" > "$CSV_FILE"

# ----- 定义四种读写模式 -----
# read      = 顺序读（从头到尾按地址顺序读）
# write     = 顺序写（从头到尾按地址顺序写）
# randread  = 随机读（随机跳到某个地址去读）
# randwrite = 随机写（随机跳到某个地址去写）
RW_MODES=("read" "write" "randread" "randwrite")

# ----- 友好的中文名称（用于屏幕输出） -----
declare -A MODE_NAMES
MODE_NAMES["read"]="顺序读 (Sequential Read)"
MODE_NAMES["write"]="顺序写 (Sequential Write)"
MODE_NAMES["randread"]="随机读 (Random Read)"
MODE_NAMES["randwrite"]="随机写 (Random Write)"

echo "========================================"
echo " 任务1：基础性能测试"
echo " 基准参数: bs=$BS, ioengine=$IOENGINE, numjobs=$NUMJOBS, iodepth=$IODEPTH"
echo "========================================"

for RW in "${RW_MODES[@]}"; do
    echo ""
    echo ">>> 正在测试: ${MODE_NAMES[$RW]} ($RW) ..."
    echo "    预计耗时 ${RUNTIME} 秒，请耐心等待..."

    # ---- 运行 fio 测试 ----
    # 关键参数解释：
    #   --name=test          测试任务的名字（随便起）
    #   --rw=$RW             读写模式（本轮循环的变量）
    #   --bs=$BS             块大小
    #   --ioengine=$IOENGINE I/O引擎
    #   --numjobs=$NUMJOBS   并发线程数
    #   --iodepth=$IODEPTH   I/O队列深度
    #   --size=$SIZE         测试文件总大小
    #   --runtime=$RUNTIME   最长运行时间（秒）
    #   --time_based         强制跑满runtime秒（即使文件已经读/写完一遍也继续循环）
    #   --group_reporting    多线程时合并报告（这里只有1个线程，但养成好习惯）
    #   --output-format=json 输出JSON格式，方便程序解析
    #   --filename=$FILENAME 指定测试文件路径（安全！不碰裸设备）
    #   --direct=1           绕过操作系统的文件缓存，直接读写磁盘
    #                        （如果不加这个，测的可能是内存缓存速度而非磁盘真实速度）

    OUTPUT=$(fio \
        --name=test \
        --rw="$RW" \
        --bs="$BS" \
        --ioengine="$IOENGINE" \
        --numjobs="$NUMJOBS" \
        --iodepth="$IODEPTH" \
        --size="$SIZE" \
        --runtime="$RUNTIME" \
        --time_based \
        --group_reporting \
        --output-format=json \
        --filename="$FILENAME" \
        --direct=1 \
    )

    # ---- 从JSON输出中提取关键指标 ----
    # fio 的 JSON 结构大致是：
    #   { "jobs": [ { "read": { "iops": ..., "bw": ..., "lat_ns": { "mean": ... } },
    #                  "write": { ... } } ] }
    #
    # 读操作的数据在 .jobs[0].read 里，写操作在 .jobs[0].write 里
    # 我们根据模式判断取 read 还是 write 的字段

    if [[ "$RW" == *"read"* ]]; then
        # 如果是读模式（read 或 randread），从 .jobs[0].read 取数据
        IOPS=$(echo "$OUTPUT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(data['jobs'][0]['read']['iops'])
")
        BW=$(echo "$OUTPUT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(data['jobs'][0]['read']['bw'])
")
        # 延迟单位是纳秒(ns)，除以1000转换为微秒(us)，更直观
        LAT=$(echo "$OUTPUT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(data['jobs'][0]['read']['lat_ns']['mean'] / 1000)
")
    else
        # 如果是写模式（write 或 randwrite），从 .jobs[0].write 取数据
        IOPS=$(echo "$OUTPUT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(data['jobs'][0]['write']['iops'])
")
        BW=$(echo "$OUTPUT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(data['jobs'][0]['write']['bw'])
")
        LAT=$(echo "$OUTPUT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(data['jobs'][0]['write']['lat_ns']['mean'] / 1000)
")
    fi

    # 在终端打印结果，让你实时看到
    echo "    结果: IOPS=$IOPS, BW=${BW} KB/s, Latency=${LAT} us"

    # 写入CSV文件（追加模式 >>）
    echo "$RW,$IOPS,$BW,$LAT" >> "$CSV_FILE"
done

# ---- 清理测试文件 ----
echo ""
echo ">>> 清理测试文件..."
rm -f "$FILENAME"

echo ""
echo "========================================"
echo " 测试完成！结果已保存到: $CSV_FILE"
echo "========================================"
echo ""
echo "CSV 内容预览："
cat "$CSV_FILE"
