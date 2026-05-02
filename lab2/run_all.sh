#!/bin/bash
set -e

TASK2_NUM_KEYS="${TASK2_NUM_KEYS:-32000000}"
TASK3_NUM_KEYS="${TASK3_NUM_KEYS:-2000000}"
TASK3_NUM_OPS="${TASK3_NUM_OPS:-500000}"
TASK3_NUM_SCANS="${TASK3_NUM_SCANS:-10000}"
SKIP_DROP_CACHES="${SKIP_DROP_CACHES:-0}"

drop_caches() {
    if [ "$SKIP_DROP_CACHES" = "1" ]; then
        echo "  >> 跳过清理 Page Cache"
        return
    fi

    if command -v sudo >/dev/null 2>&1; then
        sudo sh -c 'echo 3 > /proc/sys/vm/drop_caches'
    else
        echo "  >> 未找到 sudo，跳过清理 Page Cache"
    fi
}

echo "===== 编译 ====="
make clean && make

mkdir -p results figures

rm -f results/*.csv

echo ""
echo "===== 任务一：参数调优 ====="

for val in 4 16 64; do
    echo "  >> write_buffer_size = ${val}MB"
    drop_caches
    ./task1 --param write_buffer_size --value "$val"
done

for val in 4 16 64; do
    echo "  >> block_size = ${val}KB"
    drop_caches
    ./task1 --param block_size --value "$val"
done

for val in 0 10; do
    echo "  >> bloom_filter = ${val} bits"
    drop_caches
    ./task1 --param bloom_filter --value "$val"
done

echo ""
echo "===== 任务二：写毛刺 ====="
drop_caches
./task2 --num_keys "$TASK2_NUM_KEYS"

echo ""
echo "===== 任务三：缓存对比 ====="
for workload in point_get range_scan mixed; do
    for mode in block_cache kv_cache; do
        echo "  >> ${workload} / ${mode}"
        drop_caches
        ./task3 --mode "$mode" --workload "$workload" \
            --num_keys "$TASK3_NUM_KEYS" \
            --num_ops "$TASK3_NUM_OPS" \
            --num_scans "$TASK3_NUM_SCANS"
    done
done

echo ""
echo "===== 生成图表 ====="
python3 plot_task1.py
python3 plot_task2.py
python3 plot_task3.py

echo ""
echo "===== 全部完成！====="
echo "CSV 数据在 results/ 目录"
echo "图表在 figures/ 目录"
