#pragma once

#include <list>
#include <string>
#include <unordered_map>
#include <utility>

class LRUCache {
public:
    explicit LRUCache(size_t capacity);

    bool Get(const std::string& key, std::string* value_out);
    void Put(const std::string& key, const std::string& value);
    void Erase(const std::string& key);

    size_t Size() const;
    size_t HitCount() const;
    size_t MissCount() const;
    double HitRate() const;

    void ResetStats();

private:
    using ListIt = std::list<std::pair<std::string, std::string>>::iterator;

    size_t capacity_;
    size_t hit_count_;
    size_t miss_count_;

    std::list<std::pair<std::string, std::string>> order_;
    std::unordered_map<std::string, ListIt> map_;
};
