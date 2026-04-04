#!/bin/bash
# ============================================================
# task2_test.sh — 任务2：多维度参数影响分析
# ============================================================
#
# 【实验目的】
#   在"随机读"和"随机写"两种模式下，用控制变量法分别探究：
#     实验A：块大小(bs)对性能的影响
#     实验B：并发线程数(numjobs)和队列深度(iodepth)对性能的影响
#     实验C：I/O引擎(ioengine)对性能的影响
#
# 【控制变量法】
#   每次只改变一个参数，其他参数保持不变（基准值）。
#   这样才能确定性能变化是由哪个参数引起的。
#
# 【输出文件】
#   task2_bs.csv       —— 实验A的结果
#   task2_jobs_depth.csv —— 实验B的结果
#   task2_ioengine.csv —— 实验C的结果
#
# 【使用方法】
#   chmod +x task2_test.sh
#   ./task2_test.sh
# ============================================================

# =====================
# 全局基准参数
# =====================
SIZE="1G"
RUNTIME=60
FILENAME="fio_test_file"

# 我们选择"随机读"和"随机写"来做对比
# （这两种模式对参数变化更敏感，更能看出差异）
RW_MODES=("randread" "randwrite")

# =====================
# 辅助函数：运行单次fio测试并提取结果
# =====================
# 参数: $1=rw模式, $2=bs, $3=ioengine, $4=numjobs, $5=iodepth
# 输出: 打印 "iops,bw_KBps,lat_us" 到标准输出
run_fio_test() {
    local rw="$1"
    local bs="$2"
    local ioengine="$3"
    local numjobs="$4"
    local iodepth="$5"

    # 运行fio，输出JSON格式
    local output
    output=$(fio \
        --name=test \
        --rw="$rw" \
        --bs="$bs" \
        --ioengine="$ioengine" \
        --numjobs="$numjobs" \
        --iodepth="$iodepth" \
        --size="$SIZE" \
        --runtime="$RUNTIME" \
        --time_based \
        --group_reporting \
        --output-format=json \
        --filename="$FILENAME" \
        --direct=1 \
    )

    # 根据读/写模式选择从JSON中提取哪个字段
    local rw_field
    if [[ "$rw" == *"read"* ]]; then
        rw_field="read"
    else
        rw_field="write"
    fi

    # 用python3解析JSON，一次性提取三个指标
    echo "$output" | python3 -c "
import sys, json
data = json.load(sys.stdin)
job = data['jobs'][0]['$rw_field']
iops = job['iops']
bw = job['bw']                         # 单位: KB/s
lat = job['lat_ns']['mean'] / 1000     # 纳秒 -> 微秒
print(f'{iops},{bw},{lat}')
"
}


# ============================================================
# 实验A：块大小(bs)的影响
# ============================================================
# 【思路】
#   固定: ioengine=psync, numjobs=1, iodepth=1
#   变化: bs = 4k, 16k, 64k, 256k, 1m
#
# 【预期现象】
#   bs增大 → 每次搬运更多数据 → 带宽(BW)上升
#   bs增大 → 每次操作耗时更长 → IOPS下降
#   因为 BW = IOPS × bs，所以两者此消彼长

echo "========================================"
echo " 实验A：块大小(bs)的影响"
echo " 固定: ioengine=psync, numjobs=1, iodepth=1"
echo "========================================"

BS_VALUES=("4k" "16k" "64k" "256k" "1m")
CSV_BS="task2_bs.csv"

# 写CSV表头
echo "rw,bs,iops,bw_KBps,lat_us" > "$CSV_BS"

for RW in "${RW_MODES[@]}"; do
    for BS in "${BS_VALUES[@]}"; do
        echo "  测试: rw=$RW, bs=$BS ..."
        RESULT=$(run_fio_test "$RW" "$BS" "psync" 1 1)
        echo "$RW,$BS,$RESULT" >> "$CSV_BS"
        echo "    -> $RESULT"
    done
done

rm -f "$FILENAME"
echo "实验A完成，结果保存到 $CSV_BS"
echo ""


# ============================================================
# 实验B：并发线程数(numjobs)和队列深度(iodepth)的影响
# ============================================================
# 【思路】
#   固定: bs=4k
#   变化: numjobs = 1, 4, 8  ×  iodepth = 1, 16, 64
#
# 【重要】
#   这里 ioengine 用 libaio（Linux异步I/O），而不是 psync！
#   原因：psync是同步引擎，每次只能处理1个请求，
#   即使你设 iodepth=64，实际也只有1。
#   libaio 是异步的，能真正同时发多个请求，iodepth才有意义。
#
# 【预期现象】
#   SSD: iodepth增大 → IOPS大幅提升（SSD内部有多通道并行）
#   HDD: iodepth增大 → 提升有限（只有一个磁头，无法真正并行）
#   numjobs增大 → 类似效果，通过多线程增加并发

echo "========================================"
echo " 实验B：并发(numjobs)与队列深度(iodepth)的影响"
echo " 固定: bs=4k, ioengine=libaio"
echo "========================================"

NUMJOBS_VALUES=(1 4 8)
IODEPTH_VALUES=(1 16 64)
CSV_JOBS="task2_jobs_depth.csv"

echo "rw,numjobs,iodepth,iops,bw_KBps,lat_us" > "$CSV_JOBS"

for RW in "${RW_MODES[@]}"; do
    for NJ in "${NUMJOBS_VALUES[@]}"; do
        for ID in "${IODEPTH_VALUES[@]}"; do
            echo "  测试: rw=$RW, numjobs=$NJ, iodepth=$ID ..."
            RESULT=$(run_fio_test "$RW" "4k" "libaio" "$NJ" "$ID")
            echo "$RW,$NJ,$ID,$RESULT" >> "$CSV_JOBS"
            echo "    -> $RESULT"
        done
    done
done

rm -f "$FILENAME"
echo "实验B完成，结果保存到 $CSV_JOBS"
echo ""


# ============================================================
# 实验C：I/O引擎(ioengine)的对比
# ============================================================
# 【思路】
#   固定: bs=4k, numjobs=1, iodepth=1（先测同步基线）
#   然后 iodepth=32（测异步引擎的真实能力）
#   变化: ioengine = psync, libaio, io_uring, mmap
#
# 【各引擎简介】
#   psync:    同步I/O，最基础，一个一个请求排队处理
#   libaio:   Linux异步I/O，能同时提交多个请求
#   io_uring: 新一代异步I/O（Linux 5.1+），通过环形缓冲区减少系统调用开销
#   mmap:     内存映射I/O，把文件映射到虚拟内存，通过内存操作来读写文件
#
# 【注意】
#   io_uring 需要 Linux 5.1 以上内核，如果你的系统不支持，fio会报错，
#   脚本会跳过该引擎继续执行。

echo "========================================"
echo " 实验C：I/O引擎(ioengine)的对比"
echo " 固定: bs=4k, numjobs=1"
echo "========================================"

IOENGINES=("psync" "libaio" "io_uring" "mmap")
# 测两组iodepth：1（公平对比同步能力）和 32（展示异步引擎优势）
IODEPTH_FOR_ENGINE=(1 32)
CSV_ENGINE="task2_ioengine.csv"

echo "rw,ioengine,iodepth,iops,bw_KBps,lat_us" > "$CSV_ENGINE"

for RW in "${RW_MODES[@]}"; do
    for ENGINE in "${IOENGINES[@]}"; do
        for ID in "${IODEPTH_FOR_ENGINE[@]}"; do
            # psync 和 mmap 是同步引擎，iodepth>1 没有意义，跳过
            if [[ ("$ENGINE" == "psync" || "$ENGINE" == "mmap") && "$ID" -gt 1 ]]; then
                echo "  跳过: rw=$RW, engine=$ENGINE, iodepth=$ID (同步引擎不支持深队列)"
                continue
            fi

            echo "  测试: rw=$RW, engine=$ENGINE, iodepth=$ID ..."

            # 尝试运行，如果引擎不被支持则跳过
            RESULT=$(run_fio_test "$RW" "4k" "$ENGINE" 1 "$ID" 2>/dev/null)

            if [ -z "$RESULT" ]; then
                echo "    -> 该引擎不被当前系统支持，跳过"
                continue
            fi

            echo "$RW,$ENGINE,$ID,$RESULT" >> "$CSV_ENGINE"
            echo "    -> $RESULT"
        done
    done
done

rm -f "$FILENAME"
echo "实验C完成，结果保存到 $CSV_ENGINE"
echo ""

echo "========================================"
echo " 全部测试完成！生成了以下文件："
echo "   $CSV_BS"
echo "   $CSV_JOBS"
echo "   $CSV_ENGINE"
echo " 请运行 plot_task2.py 来生成图表"
echo "========================================"
