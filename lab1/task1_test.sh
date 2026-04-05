#!/bin/bash

BS="4k"
IOENGINE="psync"
NUMJOBS=1
IODEPTH=1
SIZE="1G"
RUNTIME=60
FILENAME="fio_test_file"

CSV_FILE="task1_results.csv"

echo "rw,iops,bw_KBps,lat_us" > "$CSV_FILE"

RW_MODES=("read" "write" "randread" "randwrite")

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

    if [[ "$RW" == *"read"* ]]; then
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
        LAT=$(echo "$OUTPUT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(data['jobs'][0]['read']['lat_ns']['mean'] / 1000)
")
    else
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

    echo "    结果: IOPS=$IOPS, BW=${BW} KB/s, Latency=${LAT} us"

    echo "$RW,$IOPS,$BW,$LAT" >> "$CSV_FILE"
done

echo ""
echo ">>> 清理测试文件..."
rm -f "$FILENAME"

echo ""
echo "========================================"
echo " 测试完成！结果已保存到: $CSV_FILE"
echo "========================================"
echo ""

