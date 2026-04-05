SIZE="1G"
RUNTIME=60
FILENAME="fio_test_file"

RW_MODES=("randread" "randwrite")


run_fio_test() {
    local rw="$1"
    local bs="$2"
    local ioengine="$3"
    local numjobs="$4"
    local iodepth="$5"


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




echo " 实验A：块大小(bs)的影响"
echo " 固定: ioengine=psync, numjobs=1, iodepth=1"


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



echo " 实验B：并发(numjobs)与队列深度(iodepth)的影响"
echo " 固定: bs=4k, ioengine=libaio"


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



echo " 实验C：I/O引擎(ioengine)的对比"
echo " 固定: bs=4k, numjobs=1"

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

