#include "lru_cache.h"

LRUCache::LRUCache(size_t capacity)
    : capacity_(capacity), hit_count_(0), miss_count_(0) {}

bool LRUCache::Get(const std::string& key, std::string* value_out) {
    auto it = map_.find(key);
    if (it == map_.end()) {
        ++miss_count_;
        return false;
    }

    order_.splice(order_.begin(), order_, it->second);
    *value_out = it->second->second;
    ++hit_count_;
    return true;
}

void LRUCache::Put(const std::string& key, const std::string& value) {
    if (capacity_ == 0) {
        return;
    }

    auto it = map_.find(key);
    if (it != map_.end()) {
        it->second->second = value;
        order_.splice(order_.begin(), order_, it->second);
        return;
    }

    if (order_.size() == capacity_) {
        const auto& evicted = order_.back();
        map_.erase(evicted.first);
        order_.pop_back();
    }

    order_.emplace_front(key, value);
    map_[key] = order_.begin();
}

void LRUCache::Erase(const std::string& key) {
    auto it = map_.find(key);
    if (it == map_.end()) {
        return;
    }
    order_.erase(it->second);
    map_.erase(it);
}

size_t LRUCache::Size() const {
    return order_.size();
}

size_t LRUCache::HitCount() const {
    return hit_count_;
}

size_t LRUCache::MissCount() const {
    return miss_count_;
}

double LRUCache::HitRate() const {
    const size_t total = hit_count_ + miss_count_;
    if (total == 0) {
        return 0.0;
    }
    return static_cast<double>(hit_count_) / static_cast<double>(total);
}

void LRUCache::ResetStats() {
    hit_count_ = 0;
    miss_count_ = 0;
}
