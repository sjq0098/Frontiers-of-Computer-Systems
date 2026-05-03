# LevelDB 性能测试作业 — 设计文档

## 一、项目概述

本项目为 LevelDB 性能测试课程作业，包含三个实验任务：

1. **任务一**：核心参数调优与性能对比
2. **任务二**：长尾延迟测量与 Compaction 写毛刺观察
3. **任务三**：应用层 KV Cache 与底层 Block Cache 的设计与对比

项目采用 C++ 编写压测程序，输出 CSV 格式结果，再用 Python 脚本可视化生成图表。

---

## 二、项目目录结构

```
leveldb_homework/
│
├── Makefile                        # 一键编译所有 C++ 程序
├── README.md                       # 编译运行说明
│
├── common.h                        # 公共工具代码（FormatKey、ZipfGenerator、Timer）
│
├── task1_benchmark.cpp             # 任务一：参数调优压测主程序
├── task2_latency.cpp               # 任务二：写毛刺延迟测量主程序
├── task3_cache.cpp                 # 任务三：缓存对比主程序
├── lru_cache.h                     # 任务三：LRU Cache 头文件
├── lru_cache.cpp                   # 任务三：LRU Cache 实现
│
├── run_all.sh                      # 一键运行所有实验的 bash 脚本
│
├── plot_task1.py                   # 任务一可视化脚本
├── plot_task2.py                   # 任务二可视化脚本
├── plot_task3.py                   # 任务三可视化脚本
│
├── results/                        # 实验输出的 CSV 数据（程序自动生成）
│   ├── task1_write_buffer_size.csv
│   ├── task1_block_size.csv
│   ├── task1_bloom_filter.csv
│   ├── task2_percentiles.csv
│   ├── task2_latency_raw.csv
│   ├── task3_point_get.csv
│   ├── task3_range_scan.csv
│   └── task3_mixed.csv
│
├── figures/                        # Python 脚本生成的图表（脚本自动生成）
│   ├── task1_write_buffer_size.png
│   ├── task1_block_size.png
│   ├── task1_bloom_filter.png
│   ├── task2_percentiles.png
│   ├── task2_latency_timeline.png
│   ├── task3_point_get.png
│   ├── task3_range_scan.png
│   └── task3_mixed.png
│
├── leveldb_test.cpp                # 老师提供的原始示例（不参与编译，仅供参考）
│
└── report/
    └── report.pdf                  # 最终实验报告
```

---

## 三、文件依赖关系

```
common.h ──────────┬──→ task1_benchmark.cpp ──→ task1（可执行）
                   ├──→ task2_latency.cpp   ──→ task2（可执行）
                   └──→ task3_cache.cpp     ──→ task3（可执行）
                              ↑
lru_cache.h ──→ lru_cache.cpp─┘

run_all.sh ──→ 依次调用 task1, task2, task3，输出 CSV 到 results/

plot_task1.py ──→ 读取 results/task1_*.csv ──→ 输出 figures/task1_*.png
plot_task2.py ──→ 读取 results/task2_*.csv ──→ 输出 figures/task2_*.png
plot_task3.py ──→ 读取 results/task3_*.csv ──→ 输出 figures/task3_*.png
```

---

## 四、数据流

```
C++ 压测程序 ──→ CSV 文件（results/） ──→ Python 脚本 ──→ PNG 图表（figures/）
```

所有 C++ 程序只负责跑实验、输出数据到 CSV。所有可视化都由 Python 脚本完成。

---

## 五、建议开发顺序（小步快跑）

### 第 0 步：搭骨架
- [ ] 创建项目目录 `lab2`，把 `leveldb_test.cpp` 放进去
- [ ] 创建 `common.h`（从 leveldb_test.cpp 中提取 FormatKey、ZipfGenerator，新增 Timer 类）
- [ ] 创建 `Makefile`（先只写 task1 的编译规则）
- [ ] 创建 `results/` 和 `figures/` 空目录
- [ ] 验证：写一个最简单的 task1_benchmark.cpp，只打开 LevelDB 写入 10 条数据，`make && ./task1` 能跑通

### 第 1 步：完成任务一
- [ ] 1a. 实现 task1_benchmark.cpp 的数据加载功能（200 万条，1KB Value）
- [ ] 1b. 实现顺序写场景，输出 QPS 到终端
- [ ] 1c. 实现随机写场景
- [ ] 1d. 实现随机读场景
- [ ] 1e. 添加命令行参数解析（--param, --value），支持切换 write_buffer_size / block_size / filter_policy
- [ ] 1f. 将结果追加写入 CSV 文件（results/task1_xxx.csv）
- [ ] 1g. 编写 plot_task1.py，读取 CSV 画柱状图
- [ ] 验证：跑几组参数，看 CSV 和图表是否正确

### 第 2 步：完成任务二
- [ ] 2a. 实现 task2_latency.cpp 的持续随机写入（每次 Put 单独计时）
- [ ] 2b. 计算并输出 P50/P90/P99/P99.9 到 task2_percentiles.csv
- [ ] 2c. 将每次操作的原始延迟输出到 task2_latency_raw.csv（列：op_index, latency_us）
- [ ] 2d. 编写 plot_task2.py，画分位数柱状图 + 延迟时间线散点图
- [ ] 验证：用较小数据量先验证程序逻辑，再用完整数据量跑

### 第 3 步：完成任务三
- [ ] 3a. 实现 lru_cache.h / lru_cache.cpp（LRU Cache 类）
- [ ] 3b. 写一个简单的单元测试验证 LRU Cache 的正确性（Put/Get/淘汰）
- [ ] 3c. 实现 task3_cache.cpp 的情景 A（纯 Block Cache）点查测试
- [ ] 3d. 实现情景 B（纯 KV Cache）点查测试，对比情景 A
- [ ] 3e. 添加范围查询（Range Scan）测试
- [ ] 3f. 添加读写混合测试
- [ ] 3g. 所有结果输出到 CSV
- [ ] 3h. 编写 plot_task3.py，画对比柱状图
- [ ] 验证：对比两种情景的 QPS 差异是否符合预期

### 第 4 步：收尾
- [ ] 编写 run_all.sh（整合所有实验，含清 Page Cache）
- [ ] 编写 README.md
- [ ] 完善 Makefile（确保 make clean && make && bash run_all.sh 能一键跑通）
- [ ] 撰写实验报告

---

## 六、各文件详细设计

---

### 6.1 `common.h`

公共头文件，三个任务共享。包含以下组件：

#### FormatKey(int num) → string
- 将整数转为定长字符串 Key："user_key_0001234"
- `snprintf(buf, sizeof(buf), "user_key_%07d", num)`

#### class ZipfGenerator
- 构造函数：ZipfGenerator(int N, double s)
  - N = Key 总数，s = 倾斜度（默认 0.99，任务三建议用 1.2）
  - 预计算离散概率分布
- Next() → int：返回 1~N 的随机编号

#### class Timer
- Start()：记录开始时间
- ElapsedSeconds() → double：返回经过的秒数
- ElapsedMicros() → double：返回经过的微秒数

#### 常量建议
```cpp
const int NUM_KEYS = 2000000;         // 200 万条（约 2GB，1KB Value）
const int VALUE_SIZE = 1024;          // 1KB
const std::string DB_BASE_PATH = "/tmp/leveldb_homework";
```

---

### 6.2 `task1_benchmark.cpp` — 任务一：参数调优

#### 功能
在不同参数配置下，分别测试顺序写、随机写、随机读的 QPS 和平均延迟。

#### 命令行接口
```bash
./task1 --param <param_name> --value <param_value> [--num_keys <N>]
```
- `--param` 可选值：`write_buffer_size` | `block_size` | `bloom_filter`
- `--value` 含义：
  - write_buffer_size: 4 / 16 / 64（单位 MB）
  - block_size: 4 / 16 / 64（单位 KB）
  - bloom_filter: 0（关闭）/ 10（开启，10 bits/key）
- `--num_keys` 默认值：`2000000`
- 建议：`write_buffer_size` / `block_size` 保持默认值；`bloom_filter` 为了放大效果，可单独设为 `32000000`（约 32GB 数据）

#### 程序流程
```
1. 解析命令行参数
2. 根据参数设置 leveldb::Options
3. 删除旧数据库目录（确保每次从空库开始）
4. 打开 LevelDB

5. 测试顺序写：
   - for i in 1..NUM_KEYS: Put(FormatKey(i), value_1kb)
   - 记录总耗时，算 QPS

6. 关闭数据库，删除目录，重新打开（确保独立测试）

7. 测试随机写：
   - 打乱 1..NUM_KEYS 的顺序
   - for each key: Put(FormatKey(key), value_1kb)
   - 记录总耗时，算 QPS

8. 不删库，直接测试随机读（在随机写的数据上读）：
   - 打乱顺序，取前 N 个 key 做 Get
   - 记录总耗时，算 QPS

9. 如果当前参数是 `bloom_filter`，则随机读场景改为：
   - 写入完成后先关闭数据库，再重新打开
   - 随机查询一批**不存在**的 Key（例如 `num_keys+1 .. 2*num_keys`）
   - 记录负查询的总耗时，算 QPS

10. 输出结果到终端 + 追加到 CSV 文件
```

#### CSV 输出格式

**results/task1_write_buffer_size.csv**
```csv
param_value_mb,seq_write_qps,rand_write_qps,rand_read_qps,seq_write_avg_us,rand_write_avg_us,rand_read_avg_us
4,xxxxx,xxxxx,xxxxx,xx.xx,xx.xx,xx.xx
16,xxxxx,xxxxx,xxxxx,xx.xx,xx.xx,xx.xx
64,xxxxx,xxxxx,xxxxx,xx.xx,xx.xx,xx.xx
```

**results/task1_block_size.csv**
```csv
param_value_kb,seq_write_qps,rand_write_qps,rand_read_qps,seq_write_avg_us,rand_write_avg_us,rand_read_avg_us
4,xxxxx,xxxxx,xxxxx,xx.xx,xx.xx,xx.xx
16,xxxxx,xxxxx,xxxxx,xx.xx,xx.xx,xx.xx
64,xxxxx,xxxxx,xxxxx,xx.xx,xx.xx,xx.xx
```

**results/task1_bloom_filter.csv**
```csv
bloom_bits,rand_read_qps,rand_read_avg_us
0,xxxxx,xx.xx
10,xxxxx,xx.xx
```

#### 注意事项
- 每次测试前必须删除旧的数据库目录（`leveldb::DestroyDB(path, options)` 或 `rm -rf`），否则旧数据影响结果
- 随机读测试应该在已有数据的库上跑（先随机写灌数据，再随机读）
- CSV 用追加模式写入，方便多次运行不同参数值时逐行追加
- 布隆过滤器实验不要复用“命中查询”的随机读场景，应单独测**不存在 key 的随机负查询**
- 为了减少写后热缓存的干扰，布隆过滤器读测试前应先关闭并重新打开数据库

---

### 6.3 `task2_latency.cpp` — 任务二：写毛刺

#### 功能
持续高速随机写入 LevelDB，记录每次 Put 操作的延迟，统计分位数并导出原始数据。

#### 命令行接口
```bash
./task2 [--num_keys <N>]
```
- `--num_keys` 默认值：根据机器内存决定，目标是总数据量 > 2×物理内存
- 例如 8GB 内存的机器，总数据量要 > 16GB，即 NUM_KEYS > 16,000,000（1600 万条 × 1KB）
- 当前开发机实测：`free -h` 显示 `Mem: total = 15Gi, available ≈ 13Gi`
- 因此本机完整实验建议：`--num_keys >= 32000000`，对应约 32GiB 的 Value 数据量，满足“总数据量 > 2×物理内存”的要求
- 调试时可先用较小值（如 `100000` 或 `1000000`）验证程序逻辑，再跑完整规模

#### 程序流程
```
1. 打开 LevelDB（使用默认参数即可）
2. 准备 1KB 的 Value
3. 创建一个 vector<double> latencies 用于存储每次延迟

4. 主循环 for i in 1..NUM_KEYS:
   a. key = FormatKey(随机编号)
   b. 记录 t1 = now()
   c. db->Put(write_opts, key, value)
   d. 记录 t2 = now()
   e. latencies.push_back(t2 - t1 的微秒数)
   f. 可选：每 10 万次打印进度

5. 排序 latencies
6. 计算 P50, P90, P99, P99.9
7. 输出到终端 + 写入 CSV
```

#### CSV 输出格式

**results/task2_percentiles.csv**
```csv
percentile,latency_us
P50,xx.xx
P90,xx.xx
P99,xx.xx
P99.9,xxxxx.xx
```

**results/task2_latency_raw.csv**
```csv
op_index,latency_us
1,3.21
2,2.87
3,4.15
...
100000,45123.67
```

#### 注意事项
- latency_raw.csv 可能会非常大（1600 万行）。两种处理方式：
  - 方案 A：全部输出（文件可能几百 MB，Python 画图时用采样）
  - 方案 B：程序里每 N 次记录一条（比如每 100 次记一条，减小文件体积）
  - **建议采用方案 B**，比如每 100 次采样一条，或者只记录前 N 万条
- 确保数据量足够大以触发多次 Compaction，否则看不到写毛刺
- `write_opts.sync = false`（默认值），不要设为 true，否则每次写入都等磁盘落盘，延迟会非常高且均匀，看不到毛刺

---

### 6.4 `lru_cache.h` — LRU Cache 头文件

```cpp
#pragma once
#include <string>
#include <list>
#include <unordered_map>

class LRUCache {
public:
    // 构造函数：指定缓存最大条目数
    explicit LRUCache(size_t capacity);

    // 查找：命中返回 true 并把 value 写入 *value_out，同时将该条目提升到最近使用
    bool Get(const std::string& key, std::string* value_out);

    // 插入/更新：如果容量已满，淘汰最久未使用的条目
    void Put(const std::string& key, const std::string& value);

    // 删除指定 key（写入时保持缓存一致性用）
    void Erase(const std::string& key);

    // 统计信息
    size_t Size() const;
    size_t HitCount() const;
    size_t MissCount() const;
    double HitRate() const;  // hit / (hit + miss)

    // 重置统计
    void ResetStats();

private:
    size_t capacity_;
    size_t hit_count_;
    size_t miss_count_;

    // 双向链表：front = 最近使用，back = 最久未使用
    // pair<key, value>
    std::list<std::pair<std::string, std::string>> order_;

    // 哈希表：key → 链表中对应节点的迭代器
    std::unordered_map<std::string, 
        std::list<std::pair<std::string, std::string>>::iterator> map_;
};
```

#### 核心逻辑

- **Get(key)**：在 map_ 中查找 → 未找到则 miss_count_++, return false → 找到则把节点 splice 到链表头部, hit_count_++, 写出 value, return true
- **Put(key, value)**：在 map_ 中查找 → 已存在则更新 value 并 splice 到头部 → 不存在则检查容量，满了就删尾部节点（从 map_ 和 order_ 中同时删除），然后在头部插入新节点
- **Erase(key)**：从 map_ 和 order_ 中删除指定 key 的节点

---

### 6.5 `lru_cache.cpp` — LRU Cache 实现

按照 lru_cache.h 的接口逐个实现。关键点：

- `std::list::splice` 是 O(1) 的移动操作，不涉及内存分配
- `std::unordered_map` 的查找是平均 O(1)
- 整个 Get/Put 操作都是 O(1) 时间复杂度

---

### 6.6 `task3_cache.cpp` — 任务三：缓存对比

#### 功能
在两种缓存情景下，分别测试点查、范围查询、读写混合的 QPS。

#### 命令行接口
```bash
./task3 --mode <block_cache|kv_cache> --workload <point_get|range_scan|mixed>
```
也可以不用命令行参数，直接在程序内跑完所有组合。

#### 程序流程
```
1. 解析命令行参数（或硬编码跑所有组合）
2. 根据 mode 设置 LevelDB Options：
   - block_cache 模式：
     options.block_cache = leveldb::NewLRUCache(8 * 1024 * 1024); // 8MB
     不使用 LRUCache
   - kv_cache 模式：
     options.block_cache = leveldb::NewLRUCache(0);  // 关闭
     read_opts.fill_cache = false;
     创建 LRUCache kv_cache(缓存条目数)

3. Load 阶段：灌入数据（200 万条 × 1KB）

4. 根据 workload 执行测试：

   [point_get] 高频随机读：
   - 用 Zipf 分布生成 Key
   - for i in 1..NUM_OPS:
       如果 kv_cache 模式：先查 kv_cache.Get()
       未命中：db->Get()，命中后 kv_cache.Put()
   - 记录 QPS

   [range_scan] 范围查询：
   - 用 Zipf 分布生成起始 Key
   - for i in 1..NUM_SCANS:
       auto* it = db->NewIterator(read_opts)
       it->Seek(start_key)
       读取连续 100 条（it->Next() 循环 100 次）
       delete it
   - 记录 QPS（按 scan 次数算，或按总读取条数算）
   - 注意：KV Cache 模式下，每条结果也要 kv_cache.Put()

   [mixed] 读写混合（80% 读 + 20% 写）：
   - 用 Zipf 分布生成 Key
   - for i in 1..NUM_OPS:
       dice < 0.80 → Get（同 point_get 逻辑）
       dice >= 0.80 → Put（同时更新 kv_cache）
   - 记录 QPS

5. 输出到终端 + 写入 CSV
```

#### CSV 输出格式

**results/task3_point_get.csv**
```csv
mode,qps,avg_latency_us,cache_hit_rate
block_cache,xxxxx,xx.xx,N/A
kv_cache,xxxxx,xx.xx,0.85
```

**results/task3_range_scan.csv**
```csv
mode,qps,avg_latency_us,cache_hit_rate
block_cache,xxxxx,xx.xx,N/A
kv_cache,xxxxx,xx.xx,0.45
```

**results/task3_mixed.csv**
```csv
mode,qps,avg_latency_us,cache_hit_rate
block_cache,xxxxx,xx.xx,N/A
kv_cache,xxxxx,xx.xx,0.78
```

#### 注意事项
- 两种模式的缓存总内存应尽量对等，以便公平对比
  - Block Cache: 8MB
  - KV Cache: 8MB / (单条 KV 平均大小) ≈ 8MB / (16+1024) ≈ 约 7700 条
- KV Cache 模式下，Put 写入时必须同步更新缓存（kv_cache.Put 或 kv_cache.Erase），否则会读到脏数据
- Range Scan 的 kv_cache 模式下，逐条 Put 进缓存意义不大（可以做，但不会太有效），这正好说明了 KV Cache 对 Scan 不友好的结论

---

### 6.7 `plot_task1.py` — 任务一可视化

#### 输入
- `results/task1_write_buffer_size.csv`
- `results/task1_block_size.csv`
- `results/task1_bloom_filter.csv`

#### 输出
- `figures/task1_write_buffer_size.png`：分组柱状图，X 轴=参数值，Y 轴=QPS，三组柱子=顺序写/随机写/随机读
- `figures/task1_block_size.png`：同上格式
- `figures/task1_bloom_filter.png`：双柱对比图（开/关），Y 轴=随机读 QPS

#### 依赖
- matplotlib
- pandas

---

### 6.8 `plot_task2.py` — 任务二可视化

#### 输入
- `results/task2_percentiles.csv`
- `results/task2_latency_raw.csv`

#### 输出
- `figures/task2_percentiles.png`：柱状图，X 轴=P50/P90/P99/P99.9，Y 轴=延迟（微秒），建议 Y 轴用对数刻度
- `figures/task2_latency_timeline.png`：散点图，X 轴=操作编号，Y 轴=延迟（微秒），建议 Y 轴用对数刻度。正常操作在底部密集，毛刺在上方形成尖刺

---

### 6.9 `plot_task3.py` — 任务三可视化

#### 输入
- `results/task3_point_get.csv`
- `results/task3_range_scan.csv`
- `results/task3_mixed.csv`

#### 输出
- `figures/task3_point_get.png`：双柱对比图（Block Cache vs KV Cache），Y 轴=QPS
- `figures/task3_range_scan.png`：同上
- `figures/task3_mixed.png`：同上
- 可选：合并成一张大图，三个子图并排

---

### 6.10 `run_all.sh` — 一键实验脚本

```bash
#!/bin/bash
set -e  # 任何命令失败就停止

echo "===== 编译 ====="
make clean && make

mkdir -p results figures

# 清空旧结果
rm -f results/*.csv

echo ""
echo "===== 任务一：参数调优 ====="

# write_buffer_size: 4MB, 16MB, 64MB
for val in 4 16 64; do
    echo "  >> write_buffer_size = ${val}MB"
    sudo sh -c 'echo 3 > /proc/sys/vm/drop_caches'
    ./task1 --param write_buffer_size --value $val
done

# block_size: 4KB, 16KB, 64KB
for val in 4 16 64; do
    echo "  >> block_size = ${val}KB"
    sudo sh -c 'echo 3 > /proc/sys/vm/drop_caches'
    ./task1 --param block_size --value $val
done

# bloom_filter: 关闭(0) vs 开启(10)
for val in 0 10; do
    echo "  >> bloom_filter = ${val} bits"
    sudo sh -c 'echo 3 > /proc/sys/vm/drop_caches'
    ./task1 --param bloom_filter --value $val
done

echo ""
echo "===== 任务二：写毛刺 ====="
sudo sh -c 'echo 3 > /proc/sys/vm/drop_caches'
./task2

echo ""
echo "===== 任务三：缓存对比 ====="

for workload in point_get range_scan mixed; do
    for mode in block_cache kv_cache; do
        echo "  >> ${workload} / ${mode}"
        sudo sh -c 'echo 3 > /proc/sys/vm/drop_caches'
        ./task3 --mode $mode --workload $workload
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
```

---

### 6.11 `Makefile`

```makefile
CXX = g++
CXXFLAGS = -std=c++17 -O2 -Wall
LIBS = -lleveldb -lpthread

all: task1 task2 task3

task1: task1_benchmark.cpp common.h
	$(CXX) $(CXXFLAGS) -o task1 task1_benchmark.cpp $(LIBS)

task2: task2_latency.cpp common.h
	$(CXX) $(CXXFLAGS) -o task2 task2_latency.cpp $(LIBS)

task3: task3_cache.cpp lru_cache.cpp lru_cache.h common.h
	$(CXX) $(CXXFLAGS) -o task3 task3_cache.cpp lru_cache.cpp $(LIBS)

clean:
	rm -f task1 task2 task3

.PHONY: all clean
```

---

## 七、关键参数速查

### LevelDB Options

| 参数 | 默认值 | 作业要求测试的值 | 影响 |
|------|--------|-----------------|------|
| write_buffer_size | 4MB | 4MB, 16MB, 64MB | MemTable 大小，影响 flush 频率和写入吞吐 |
| block_size | 4KB | 4KB, 16KB, 64KB | SSTable 数据块大小，影响点查 vs 扫描的效率 |
| filter_policy | nullptr | nullptr, Bloom(10) | 布隆过滤器，影响随机读是否跳过无用文件 |
| block_cache | 8MB LRU | 8MB / 0 | SSTable Block 缓存 |
| create_if_missing | false | 设为 true | 数据库不存在时自动创建 |

### WriteOptions

| 参数 | 默认值 | 建议 |
|------|--------|------|
| sync | false | 保持 false，否则性能极差 |

### ReadOptions

| 参数 | 默认值 | 任务三用到 |
|------|--------|-----------|
| fill_cache | true | KV Cache 模式下设为 false |

---

## 八、预期实验结论（供报告参考）

### 任务一预期结论

- **write_buffer_size 增大** → 写入 QPS 提升（flush 频率降低）、读取影响不大
- **block_size 增大** → 顺序读/扫描可能提升、随机读可能下降（读放大增大）
- **Bloom Filter 开启** → 随机读 QPS 显著提升（减少无效磁盘 IO）

### 任务二预期结论

- P50 很低（几微秒到几十微秒）
- P99.9 比 P50 高 100~10000 倍（毛刺）
- 毛刺原因：Compaction 抢占 IO → L0 堆积 → 写入被阻塞

### 任务三预期结论

- 点查：KV Cache 优于 Block Cache（O(1) 哈希查找 vs 多层 SSTable 查找）
- 范围查询：Block Cache 优于 KV Cache（块级缓存天然支持连续读取）
- 混合负载：取决于读写比例和热点集中度
```
