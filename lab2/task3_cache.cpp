#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <memory>
#include <random>
#include <sstream>
#include <string>
#include <vector>

#include "common.h"
#include "lru_cache.h"
#include "leveldb/cache.h"
#include "leveldb/db.h"
#include "leveldb/options.h"

namespace {

constexpr size_t kBlockCacheBytes = 8 * 1024 * 1024;
constexpr size_t kKvCacheEntries = 7700;
constexpr int kDefaultNumOps = 500000;
constexpr int kDefaultNumScans = 10000;
constexpr int kScanLength = 100;
constexpr int kProgressEvery = 100000;

struct ResultRow {
    double qps = 0.0;
    double avg_latency_us = 0.0;
    std::string cache_hit_rate = "N/A";
};

struct Config {
    std::string mode;
    std::string workload;
    int num_keys = NUM_KEYS;
    int num_ops = kDefaultNumOps;
    int num_scans = kDefaultNumScans;
};

struct RuntimeContext {
    leveldb::Options options;
    leveldb::ReadOptions read_options;
    std::unique_ptr<leveldb::Cache> block_cache;
    std::unique_ptr<LRUCache> kv_cache;
};

void PrintUsage() {
    std::cerr << "Usage: ./task3 --mode <block_cache|kv_cache> "
              << "--workload <point_get|range_scan|mixed> "
              << "[--num_keys N] [--num_ops N] [--num_scans N]\n";
}

bool IsValidMode(const std::string& mode) {
    return mode == "block_cache" || mode == "kv_cache";
}

bool IsValidWorkload(const std::string& workload) {
    return workload == "point_get" || workload == "range_scan" || workload == "mixed";
}

bool ParseArgs(int argc, char* argv[], Config* config) {
    for (int i = 1; i < argc; ++i) {
        const std::string arg = argv[i];
        if (arg == "--mode" && i + 1 < argc) {
            config->mode = argv[++i];
        } else if (arg == "--workload" && i + 1 < argc) {
            config->workload = argv[++i];
        } else if (arg == "--num_keys" && i + 1 < argc) {
            config->num_keys = std::stoi(argv[++i]);
        } else if (arg == "--num_ops" && i + 1 < argc) {
            config->num_ops = std::stoi(argv[++i]);
        } else if (arg == "--num_scans" && i + 1 < argc) {
            config->num_scans = std::stoi(argv[++i]);
        } else {
            return false;
        }
    }

    return IsValidMode(config->mode) && IsValidWorkload(config->workload) &&
           config->num_keys > 0 && config->num_ops > 0 && config->num_scans > 0;
}

void EnsureWorkspaceDirs() {
    std::filesystem::create_directories(DB_BASE_PATH);
    std::filesystem::create_directories("results");
    std::filesystem::create_directories("figures");
}

std::string BuildDbPath(const Config& config) {
    return DB_BASE_PATH + "/task3_" + config.mode + "_" + config.workload;
}

void DestroyDbOrExit(const std::string& db_path, const leveldb::Options& options) {
    const leveldb::Status status = leveldb::DestroyDB(db_path, options);
    if (!status.ok() && !status.IsNotFound()) {
        std::cerr << "DestroyDB failed: " << status.ToString() << "\n";
        std::exit(1);
    }
}

leveldb::DB* OpenDbOrExit(const std::string& db_path, const leveldb::Options& options) {
    leveldb::DB* db = nullptr;
    const leveldb::Status status = leveldb::DB::Open(options, db_path, &db);
    if (!status.ok()) {
        std::cerr << "Open failed: " << status.ToString() << "\n";
        std::exit(1);
    }
    return db;
}

RuntimeContext BuildRuntime(const Config& config) {
    RuntimeContext runtime;
    runtime.options.create_if_missing = true;

    if (config.mode == "block_cache") {
        runtime.block_cache.reset(leveldb::NewLRUCache(kBlockCacheBytes));
        runtime.options.block_cache = runtime.block_cache.get();
    } else {
        runtime.block_cache.reset(leveldb::NewLRUCache(0));
        runtime.options.block_cache = runtime.block_cache.get();
        runtime.read_options.fill_cache = false;
        runtime.kv_cache = std::make_unique<LRUCache>(kKvCacheEntries);
    }

    return runtime;
}

void LoadDataset(leveldb::DB* db, int num_keys, const std::string& value) {
    leveldb::WriteOptions write_options;
    std::cout << "load dataset: " << num_keys << " keys\n";
    for (int i = 1; i <= num_keys; ++i) {
        const leveldb::Status status = db->Put(write_options, FormatKey(i), value);
        if (!status.ok()) {
            std::cerr << "Load Put failed at key " << i << ": " << status.ToString() << "\n";
            std::exit(1);
        }
        if (i % kProgressEvery == 0) {
            std::cout << "  load progress: " << i << "/" << num_keys << "\n";
        }
    }
}

bool ReadWithOptionalKvCache(leveldb::DB* db,
                             const leveldb::ReadOptions& read_options,
                             LRUCache* kv_cache,
                             const std::string& key,
                             std::string* value_out) {
    if (kv_cache != nullptr && kv_cache->Get(key, value_out)) {
        return true;
    }

    const leveldb::Status status = db->Get(read_options, key, value_out);
    if (!status.ok()) {
        std::cerr << "Get failed for key " << key << ": " << status.ToString() << "\n";
        std::exit(1);
    }

    if (kv_cache != nullptr) {
        kv_cache->Put(key, *value_out);
    }
    return false;
}

ResultRow RunPointGet(leveldb::DB* db, const Config& config, RuntimeContext* runtime) {
    ZipfGenerator zipf(config.num_keys, 1.2);
    std::string value;
    Timer timer;

    for (int i = 1; i <= config.num_ops; ++i) {
        ReadWithOptionalKvCache(db,
                                runtime->read_options,
                                runtime->kv_cache.get(),
                                FormatKey(zipf.Next()),
                                &value);
        if (i % kProgressEvery == 0) {
            std::cout << "  point_get progress: " << i << "/" << config.num_ops << "\n";
        }
    }

    ResultRow row;
    const double elapsed = timer.ElapsedSeconds();
    row.qps = static_cast<double>(config.num_ops) / elapsed;
    row.avg_latency_us = elapsed * 1e6 / static_cast<double>(config.num_ops);
    if (runtime->kv_cache != nullptr) {
        std::ostringstream oss;
        oss << std::fixed << std::setprecision(4) << runtime->kv_cache->HitRate();
        row.cache_hit_rate = oss.str();
    }
    return row;
}

bool TryServeRangeFromKvCache(LRUCache* kv_cache, int start_id, int num_keys) {
    if (kv_cache == nullptr) {
        return false;
    }

    std::string value;
    for (int offset = 0; offset < kScanLength; ++offset) {
        const int key_id = start_id + offset;
        if (key_id > num_keys) {
            break;
        }
        if (!kv_cache->Get(FormatKey(key_id), &value)) {
            return false;
        }
    }
    return true;
}

ResultRow RunRangeScan(leveldb::DB* db, const Config& config, RuntimeContext* runtime) {
    ZipfGenerator zipf(config.num_keys - kScanLength, 1.2);
    Timer timer;

    for (int i = 1; i <= config.num_scans; ++i) {
        const int start_id = zipf.Next();
        if (!TryServeRangeFromKvCache(runtime->kv_cache.get(), start_id, config.num_keys)) {
            std::unique_ptr<leveldb::Iterator> it(db->NewIterator(runtime->read_options));
            for (it->Seek(FormatKey(start_id)); it->Valid() && it->key().ToString() <= FormatKey(start_id + kScanLength - 1); it->Next()) {
                if (runtime->kv_cache != nullptr) {
                    runtime->kv_cache->Put(it->key().ToString(), it->value().ToString());
                }
            }
            if (!it->status().ok()) {
                std::cerr << "Iterator error: " << it->status().ToString() << "\n";
                std::exit(1);
            }
        }

        if (i % kProgressEvery == 0) {
            std::cout << "  range_scan progress: " << i << "/" << config.num_scans << "\n";
        }
    }

    ResultRow row;
    const double elapsed = timer.ElapsedSeconds();
    row.qps = static_cast<double>(config.num_scans) / elapsed;
    row.avg_latency_us = elapsed * 1e6 / static_cast<double>(config.num_scans);
    if (runtime->kv_cache != nullptr) {
        std::ostringstream oss;
        oss << std::fixed << std::setprecision(4) << runtime->kv_cache->HitRate();
        row.cache_hit_rate = oss.str();
    }
    return row;
}

ResultRow RunMixed(leveldb::DB* db, const Config& config, RuntimeContext* runtime) {
    ZipfGenerator zipf(config.num_keys, 1.2);
    std::mt19937 gen(std::random_device{}());
    std::uniform_real_distribution<double> op_dist(0.0, 1.0);
    leveldb::WriteOptions write_options;
    std::string read_value;
    Timer timer;

    for (int i = 1; i <= config.num_ops; ++i) {
        const int key_id = zipf.Next();
        const std::string key = FormatKey(key_id);
        if (op_dist(gen) < 0.80) {
            ReadWithOptionalKvCache(db, runtime->read_options, runtime->kv_cache.get(), key, &read_value);
        } else {
            const std::string value = "mixed_update_" + std::to_string(i);
            const leveldb::Status status = db->Put(write_options, key, value);
            if (!status.ok()) {
                std::cerr << "Mixed Put failed at op " << i << ": " << status.ToString() << "\n";
                std::exit(1);
            }
            if (runtime->kv_cache != nullptr) {
                runtime->kv_cache->Put(key, value);
            }
        }

        if (i % kProgressEvery == 0) {
            std::cout << "  mixed progress: " << i << "/" << config.num_ops << "\n";
        }
    }

    ResultRow row;
    const double elapsed = timer.ElapsedSeconds();
    row.qps = static_cast<double>(config.num_ops) / elapsed;
    row.avg_latency_us = elapsed * 1e6 / static_cast<double>(config.num_ops);
    if (runtime->kv_cache != nullptr) {
        std::ostringstream oss;
        oss << std::fixed << std::setprecision(4) << runtime->kv_cache->HitRate();
        row.cache_hit_rate = oss.str();
    }
    return row;
}

std::string CsvPathForWorkload(const std::string& workload) {
    return "results/task3_" + workload + ".csv";
}

void EnsureCsvHeader(const std::string& path) {
    if (!std::filesystem::exists(path) || std::filesystem::file_size(path) == 0) {
        std::ofstream out(path, std::ios::out);
        out << "mode,qps,avg_latency_us,cache_hit_rate\n";
    }
}

void AppendCsvRow(const std::string& workload, const std::string& mode, const ResultRow& row) {
    const std::string path = CsvPathForWorkload(workload);
    EnsureCsvHeader(path);

    std::ofstream out(path, std::ios::app);
    out << std::fixed << std::setprecision(2);
    out << mode << "," << row.qps << "," << row.avg_latency_us << "," << row.cache_hit_rate
        << "\n";
}

}  // namespace

int main(int argc, char* argv[]) {
    Config config;
    if (!ParseArgs(argc, argv, &config)) {
        PrintUsage();
        return 1;
    }

    EnsureWorkspaceDirs();

    const std::string db_path = BuildDbPath(config);
    const std::string initial_value(VALUE_SIZE, 'x');

    RuntimeContext runtime = BuildRuntime(config);
    DestroyDbOrExit(db_path, runtime.options);
    leveldb::DB* db = OpenDbOrExit(db_path, runtime.options);
    LoadDataset(db, config.num_keys, initial_value);
    if (runtime.kv_cache != nullptr) {
        runtime.kv_cache->ResetStats();
    }

    std::cout << "run workload: mode=" << config.mode
              << ", workload=" << config.workload << "\n";

    ResultRow row;
    if (config.workload == "point_get") {
        row = RunPointGet(db, config, &runtime);
    } else if (config.workload == "range_scan") {
        row = RunRangeScan(db, config, &runtime);
    } else {
        row = RunMixed(db, config, &runtime);
    }

    AppendCsvRow(config.workload, config.mode, row);

    std::cout << std::fixed << std::setprecision(2);
    std::cout << "\n=== Task3 Result ===\n";
    std::cout << "Mode: " << config.mode << "\n";
    std::cout << "Workload: " << config.workload << "\n";
    std::cout << "QPS: " << row.qps << "\n";
    std::cout << "Avg latency: " << row.avg_latency_us << " us\n";
    std::cout << "Cache hit rate: " << row.cache_hit_rate << "\n";
    std::cout << "CSV written: " << CsvPathForWorkload(config.workload) << "\n";

    delete db;
    return 0;
}
