#ifndef LAB2_COMMON_H
#define LAB2_COMMON_H

#include <chrono>
#include <cmath>
#include <cstdio>
#include <random>
#include <string>
#include <vector>

inline std::string FormatKey(int num) {
    char buffer[32];
    std::snprintf(buffer, sizeof(buffer), "user_key_%07d", num);
    return std::string(buffer);
}

class ZipfGenerator {
public:
    ZipfGenerator(int n, double s = 0.99) : gen_(std::random_device{}()) {
        std::vector<double> weights(n);
        for (int i = 1; i <= n; ++i) {
            weights[i - 1] = 1.0 / std::pow(static_cast<double>(i), s);
        }
        dist_ = std::discrete_distribution<int>(weights.begin(), weights.end());
    }

    int Next() {
        return dist_(gen_) + 1;
    }

private:
    std::mt19937 gen_;
    std::discrete_distribution<int> dist_;
};

class Timer {
public:
    Timer() {
        Start();
    }

    void Start() {
        start_ = std::chrono::steady_clock::now();
    }

    double ElapsedSeconds() const {
        return std::chrono::duration<double>(
                   std::chrono::steady_clock::now() - start_)
            .count();
    }

    double ElapsedMicros() const {
        return std::chrono::duration<double, std::micro>(
                   std::chrono::steady_clock::now() - start_)
            .count();
    }

private:
    std::chrono::steady_clock::time_point start_;
};

inline constexpr int NUM_KEYS = 2000000;
inline constexpr int VALUE_SIZE = 1024;
inline const std::string DB_BASE_PATH = "/tmp/leveldb_homework";

#endif  // LAB2_COMMON_H
