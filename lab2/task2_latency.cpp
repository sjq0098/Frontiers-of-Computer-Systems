#include <algorithm>
#include <chrono>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <random>
#include <string>
#include <vector>

#include "common.h"
#include "leveldb/db.h"
#include "leveldb/options.h"

namespace {

constexpr int kDefaultNumKeys = 32000000;
constexpr int kRawSampleEvery = 100;
constexpr int kProgressEvery = 100000;

void PrintUsage() {
    std::cerr << "Usage: ./task2 [--num_keys <N>]\n";
}

bool ParseArgs(int argc, char* argv[], int* num_keys) {
    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];
        if (arg == "--num_keys" && i + 1 < argc) {
            *num_keys = std::stoi(argv[++i]);
        } else {
            return false;
        }
    }
    return *num_keys > 0;
}

void EnsureWorkspaceDirs() {
    std::filesystem::create_directories(DB_BASE_PATH);
    std::filesystem::create_directories("results");
    std::filesystem::create_directories("figures");
}

std::string BuildDbPath() {
    return DB_BASE_PATH + "/task2_latency";
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

double PercentileFromSorted(const std::vector<double>& values, double p) {
    if (values.empty()) {
        return 0.0;
    }
    const double rank = p * static_cast<double>(values.size() - 1);
    const size_t low = static_cast<size_t>(rank);
    const size_t high = std::min(low + 1, values.size() - 1);
    const double fraction = rank - static_cast<double>(low);
    return values[low] + (values[high] - values[low]) * fraction;
}

void WritePercentilesCsv(double p50, double p90, double p99, double p999) {
    std::ofstream out("results/task2_percentiles.csv", std::ios::out);
    out << "percentile,latency_us\n";
    out << std::fixed << std::setprecision(2);
    out << "P50," << p50 << "\n";
    out << "P90," << p90 << "\n";
    out << "P99," << p99 << "\n";
    out << "P99.9," << p999 << "\n";
}

}  // namespace

int main(int argc, char* argv[]) {
    int num_keys = kDefaultNumKeys;
    if (!ParseArgs(argc, argv, &num_keys)) {
        PrintUsage();
        return 1;
    }

    EnsureWorkspaceDirs();

    const std::string db_path = BuildDbPath();
    const std::string value(VALUE_SIZE, 'x');

    leveldb::Options options;
    options.create_if_missing = true;

    DestroyDbOrExit(db_path, options);
    leveldb::DB* db = OpenDbOrExit(db_path, options);

    leveldb::WriteOptions write_options;
    write_options.sync = false;

    std::vector<double> latencies;
    latencies.reserve(static_cast<size_t>(num_keys));

    std::ofstream raw_out("results/task2_latency_raw.csv", std::ios::out);
    raw_out << "op_index,latency_us\n";
    raw_out << std::fixed << std::setprecision(2);

    std::mt19937 gen(std::random_device{}());
    std::uniform_int_distribution<int> key_dist(1, num_keys);

    std::cout << "task2 starting: num_keys=" << num_keys
              << ", raw_sample_every=" << kRawSampleEvery << "\n";

    Timer total_timer;
    for (int i = 1; i <= num_keys; ++i) {
        const std::string key = FormatKey(key_dist(gen));
        const auto start = std::chrono::steady_clock::now();
        const leveldb::Status status = db->Put(write_options, key, value);
        const auto end = std::chrono::steady_clock::now();

        if (!status.ok()) {
            std::cerr << "Put failed at op " << i << ": " << status.ToString() << "\n";
            delete db;
            return 1;
        }

        const double latency_us =
            std::chrono::duration<double, std::micro>(end - start).count();
        latencies.push_back(latency_us);

        if (i % kRawSampleEvery == 0) {
            raw_out << i << "," << latency_us << "\n";
        }
        if (i % kProgressEvery == 0) {
            std::cout << "  progress: " << i << "/" << num_keys << "\n";
        }
    }

    delete db;
    raw_out.close();

    std::sort(latencies.begin(), latencies.end());
    const double p50 = PercentileFromSorted(latencies, 0.50);
    const double p90 = PercentileFromSorted(latencies, 0.90);
    const double p99 = PercentileFromSorted(latencies, 0.99);
    const double p999 = PercentileFromSorted(latencies, 0.999);
    WritePercentilesCsv(p50, p90, p99, p999);

    std::cout << std::fixed << std::setprecision(2);
    std::cout << "\n=== Task2 Result ===\n";
    std::cout << "Elapsed seconds: " << total_timer.ElapsedSeconds() << "\n";
    std::cout << "P50: " << p50 << " us\n";
    std::cout << "P90: " << p90 << " us\n";
    std::cout << "P99: " << p99 << " us\n";
    std::cout << "P99.9: " << p999 << " us\n";
    std::cout << "CSV written: results/task2_percentiles.csv, results/task2_latency_raw.csv\n";

    return 0;
}
