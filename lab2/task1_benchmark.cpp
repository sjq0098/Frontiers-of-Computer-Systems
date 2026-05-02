#include <algorithm>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <memory>
#include <numeric>
#include <random>
#include <string>
#include <vector>

#include "common.h"
#include "leveldb/db.h"
#include "leveldb/filter_policy.h"
#include "leveldb/options.h"

namespace {

struct Metrics {
    double qps = 0.0;
    double avg_us = 0.0;
};

struct Task1Result {
    Metrics seq_write;
    Metrics rand_write;
    Metrics rand_read;
};

void PrintUsage() {
    std::cerr
        << "Usage: ./task1 --param <write_buffer_size|block_size|bloom_filter> "
        << "--value <value>\n";
}

bool IsAllowedValue(const std::string& param, int value) {
    if (param == "write_buffer_size" || param == "block_size") {
        return value == 4 || value == 16 || value == 64;
    }
    if (param == "bloom_filter") {
        return value == 0 || value == 10;
    }
    return false;
}

bool ParseArgs(int argc, char* argv[], std::string* param, int* value) {
    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];
        if (arg == "--param" && i + 1 < argc) {
            *param = argv[++i];
        } else if (arg == "--value" && i + 1 < argc) {
            *value = std::stoi(argv[++i]);
        } else {
            return false;
        }
    }

    if (*param == "filter_policy") {
        *param = "bloom_filter";
    }

    return !param->empty() && IsAllowedValue(*param, *value);
}

std::string BuildDbPath(const std::string& param, int value) {
    return DB_BASE_PATH + "/task1_" + param + "_" + std::to_string(value);
}

std::string CsvPathForParam(const std::string& param) {
    return "results/task1_" + param + ".csv";
}

std::string HeaderForParam(const std::string& param) {
    if (param == "write_buffer_size") {
        return "param_value_mb,seq_write_qps,rand_write_qps,rand_read_qps,"
               "seq_write_avg_us,rand_write_avg_us,rand_read_avg_us\n";
    }
    if (param == "block_size") {
        return "param_value_kb,seq_write_qps,rand_write_qps,rand_read_qps,"
               "seq_write_avg_us,rand_write_avg_us,rand_read_avg_us\n";
    }
    return "bloom_bits,rand_read_qps,rand_read_avg_us\n";
}

void EnsureCsvHasHeader(const std::string& path, const std::string& header) {
    if (!std::filesystem::exists(path) || std::filesystem::file_size(path) == 0) {
        std::ofstream out(path, std::ios::out);
        out << header;
    }
}

void DestroyDbOrExit(const std::string& db_path, const leveldb::Options& options) {
    leveldb::Status status = leveldb::DestroyDB(db_path, options);
    if (!status.ok() && !status.IsNotFound()) {
        std::cerr << "DestroyDB failed: " << status.ToString() << "\n";
        std::exit(1);
    }
}

leveldb::DB* OpenDbOrExit(const std::string& db_path, const leveldb::Options& options) {
    leveldb::DB* db = nullptr;
    leveldb::Status status = leveldb::DB::Open(options, db_path, &db);
    if (!status.ok()) {
        std::cerr << "Open failed: " << status.ToString() << "\n";
        std::exit(1);
    }
    return db;
}

std::vector<int> BuildRandomKeys() {
    std::vector<int> keys(NUM_KEYS);
    std::iota(keys.begin(), keys.end(), 1);
    std::mt19937 gen(std::random_device{}());
    std::shuffle(keys.begin(), keys.end(), gen);
    return keys;
}

Metrics RunWriteTest(leveldb::DB* db,
                     const std::vector<int>& keys,
                     const std::string& value,
                     const std::string& label) {
    leveldb::WriteOptions write_options;
    Timer timer;

    for (size_t i = 0; i < keys.size(); ++i) {
        leveldb::Status status = db->Put(write_options, FormatKey(keys[i]), value);
        if (!status.ok()) {
            std::cerr << label << " Put failed at key " << keys[i] << ": "
                      << status.ToString() << "\n";
            std::exit(1);
        }
        if ((i + 1) % 500000 == 0) {
            std::cout << "  [" << label << "] progress: " << (i + 1) << "/" << keys.size()
                      << "\n";
        }
    }

    const double elapsed = timer.ElapsedSeconds();
    Metrics metrics;
    metrics.qps = static_cast<double>(keys.size()) / elapsed;
    metrics.avg_us = elapsed * 1e6 / static_cast<double>(keys.size());
    return metrics;
}

Metrics RunReadTest(leveldb::DB* db, const std::vector<int>& keys) {
    leveldb::ReadOptions read_options;
    std::string value;
    Timer timer;

    for (size_t i = 0; i < keys.size(); ++i) {
        leveldb::Status status = db->Get(read_options, FormatKey(keys[i]), &value);
        if (!status.ok()) {
            std::cerr << "random_read Get failed at key " << keys[i] << ": "
                      << status.ToString() << "\n";
            std::exit(1);
        }
        if ((i + 1) % 500000 == 0) {
            std::cout << "  [random_read] progress: " << (i + 1) << "/" << keys.size()
                      << "\n";
        }
    }

    const double elapsed = timer.ElapsedSeconds();
    Metrics metrics;
    metrics.qps = static_cast<double>(keys.size()) / elapsed;
    metrics.avg_us = elapsed * 1e6 / static_cast<double>(keys.size());
    return metrics;
}

leveldb::Options BuildOptions(const std::string& param,
                              int value,
                              std::unique_ptr<const leveldb::FilterPolicy>* filter_policy) {
    leveldb::Options options;
    options.create_if_missing = true;

    if (param == "write_buffer_size") {
        options.write_buffer_size = value * 1024 * 1024;
    } else if (param == "block_size") {
        options.block_size = value * 1024;
    } else if (param == "bloom_filter") {
        if (value > 0) {
            filter_policy->reset(leveldb::NewBloomFilterPolicy(value));
            options.filter_policy = filter_policy->get();
        }
    }

    return options;
}

Task1Result RunFullBenchmark(const std::string& db_path,
                             const leveldb::Options& options,
                             const std::string& value,
                             const std::vector<int>& random_keys) {
    Task1Result result;

    std::cout << "[1/3] sequential write\n";
    DestroyDbOrExit(db_path, options);
    leveldb::DB* db = OpenDbOrExit(db_path, options);
    std::vector<int> sequential_keys(NUM_KEYS);
    std::iota(sequential_keys.begin(), sequential_keys.end(), 1);
    result.seq_write = RunWriteTest(db, sequential_keys, value, "sequential_write");
    delete db;

    std::cout << "[2/3] random write\n";
    DestroyDbOrExit(db_path, options);
    db = OpenDbOrExit(db_path, options);
    result.rand_write = RunWriteTest(db, random_keys, value, "random_write");

    std::cout << "[3/3] random read\n";
    result.rand_read = RunReadTest(db, random_keys);
    delete db;

    return result;
}

Metrics RunBloomReadBenchmark(const std::string& db_path,
                              const leveldb::Options& options,
                              const std::string& value,
                              const std::vector<int>& random_keys) {
    std::cout << "[bloom] preload random write dataset\n";
    DestroyDbOrExit(db_path, options);
    leveldb::DB* db = OpenDbOrExit(db_path, options);
    RunWriteTest(db, random_keys, value, "bloom_preload");

    std::cout << "[bloom] random read benchmark\n";
    Metrics metrics = RunReadTest(db, random_keys);
    delete db;
    return metrics;
}

void AppendCsvRow(const std::string& param, int value, const Task1Result& result) {
    const std::string path = CsvPathForParam(param);
    EnsureCsvHasHeader(path, HeaderForParam(param));

    std::ofstream out(path, std::ios::app);
    out << std::fixed << std::setprecision(2);
    out << value << "," << result.seq_write.qps << "," << result.rand_write.qps << ","
        << result.rand_read.qps << "," << result.seq_write.avg_us << ","
        << result.rand_write.avg_us << "," << result.rand_read.avg_us << "\n";
}

void AppendBloomCsvRow(int value, const Metrics& rand_read) {
    const std::string path = CsvPathForParam("bloom_filter");
    EnsureCsvHasHeader(path, HeaderForParam("bloom_filter"));

    std::ofstream out(path, std::ios::app);
    out << std::fixed << std::setprecision(2);
    out << value << "," << rand_read.qps << "," << rand_read.avg_us << "\n";
}

void PrintFullResult(const std::string& param, int value, const Task1Result& result) {
    std::cout << std::fixed << std::setprecision(2);
    std::cout << "\n=== Task1 Result (" << param << "=" << value << ") ===\n";
    std::cout << "Sequential write: QPS=" << result.seq_write.qps
              << ", avg_us=" << result.seq_write.avg_us << "\n";
    std::cout << "Random write:     QPS=" << result.rand_write.qps
              << ", avg_us=" << result.rand_write.avg_us << "\n";
    std::cout << "Random read:      QPS=" << result.rand_read.qps
              << ", avg_us=" << result.rand_read.avg_us << "\n";
}

void PrintBloomResult(int value, const Metrics& rand_read) {
    std::cout << std::fixed << std::setprecision(2);
    std::cout << "\n=== Task1 Result (bloom_filter=" << value << ") ===\n";
    std::cout << "Random read: QPS=" << rand_read.qps
              << ", avg_us=" << rand_read.avg_us << "\n";
}

}  // namespace

int main(int argc, char* argv[]) {
    std::string param;
    int value = -1;
    if (!ParseArgs(argc, argv, &param, &value)) {
        PrintUsage();
        return 1;
    }

    std::filesystem::create_directories(DB_BASE_PATH);
    std::filesystem::create_directories("results");
    std::filesystem::create_directories("figures");

    const std::string db_path = BuildDbPath(param, value);
    const std::string value_1kb(VALUE_SIZE, 'x');
    const std::vector<int> random_keys = BuildRandomKeys();

    std::unique_ptr<const leveldb::FilterPolicy> filter_policy;
    leveldb::Options options = BuildOptions(param, value, &filter_policy);

    if (param == "bloom_filter") {
        Metrics rand_read = RunBloomReadBenchmark(db_path, options, value_1kb, random_keys);
        AppendBloomCsvRow(value, rand_read);
        PrintBloomResult(value, rand_read);
    } else {
        Task1Result result = RunFullBenchmark(db_path, options, value_1kb, random_keys);
        AppendCsvRow(param, value, result);
        PrintFullResult(param, value, result);
    }

    return 0;
}
