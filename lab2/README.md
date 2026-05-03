# lab2

基于 `LevelDB` 的性能实验工程，包含 3 个任务：

- 任务一：参数调优与性能对比
- 任务二：写入延迟分位数与毛刺观察
- 任务三：`Block Cache` 与应用层 `KV Cache` 对比

## 环境要求

- `g++`，支持 `C++17`
- 已安装 `LevelDB` 开发库，并可通过 `-lleveldb` 链接
- Python 3
- Python 包：`pandas`、`matplotlib`

安装 Python 依赖：

```bash
python3 -m pip install pandas matplotlib
```

## 编译

在 `lab2` 目录下执行：

```bash
make clean && make
make lru_cache_test
```

## 单项运行

### 任务一

```bash
./task1 --param write_buffer_size --value 4
./task1 --param block_size --value 16
./task1 --param bloom_filter --value 0 --num_keys 32000000
./task1 --param bloom_filter --value 10 --num_keys 32000000
python3 plot_task1.py
```

其中 `bloom_filter` 场景测的是随机负查询：先写入已有数据，再重新打开数据库，随机读取一批不存在的 key，用来观察 Bloom Filter 对 negative lookup 的加速效果。`task1` 支持额外的 `--num_keys` 参数，默认值是 `2000000`；如果希望 Bloom 实验单独使用约 `32GB` 数据，可传 `--num_keys 32000000`。

输出：

- `results/task1_write_buffer_size.csv`
- `results/task1_block_size.csv`
- `results/task1_bloom_filter.csv`
- `figures/task1_write_buffer_size.png`
- `figures/task1_block_size.png`
- `figures/task1_bloom_filter.png`

### 任务二

完整规模建议：

```bash
./task2 --num_keys 32000000
python3 plot_task2.py
```

输出：

- `results/task2_percentiles.csv`
- `results/task2_latency_raw.csv`
- `figures/task2_percentiles.png`
- `figures/task2_latency_timeline.png`

### 任务三

先运行单元测试：

```bash
./lru_cache_test
```

默认参数会使用：

- `--num_keys 2000000`
- `--num_ops 500000`
- `--num_scans 10000`

例如跑完整的 `point_get` 对比：

```bash
./task3 --mode block_cache --workload point_get
./task3 --mode kv_cache --workload point_get
python3 plot_task3.py
```

输出：

- `results/task3_point_get.csv`
- `results/task3_range_scan.csv`
- `results/task3_mixed.csv`
- `figures/task3_point_get.png`
- `figures/task3_range_scan.png`
- `figures/task3_mixed.png`

## 一键运行

默认会：

- 重新编译全部程序
- 清空旧的 `results/*.csv`
- 按设计文档顺序运行任务一、任务二、任务三
- 生成全部图表

直接运行：

```bash
bash run_all.sh
```

`run_all.sh` 默认已经是完整测试参数：

- `TASK1_BLOOM_NUM_KEYS=32000000`
- `TASK2_NUM_KEYS=32000000`
- `TASK3_NUM_KEYS=2000000`
- `TASK3_NUM_OPS=500000`
- `TASK3_NUM_SCANS=10000`

如果你想覆盖默认值，再在命令前临时传环境变量：

```bash
TASK1_BLOOM_NUM_KEYS=32000000 \
TASK2_NUM_KEYS=32000000 \
TASK3_NUM_KEYS=2000000 \
TASK3_NUM_OPS=500000 \
TASK3_NUM_SCANS=10000 \
bash run_all.sh
```

## Makefile 目标

- `make`：编译 `task1`、`task2`、`task3`
- `make lru_cache_test`：编译 `LRU Cache` 单元测试
- `make clean`：删除可执行文件
