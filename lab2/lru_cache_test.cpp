#include <cassert>
#include <iostream>
#include <string>

#include "lru_cache.h"

int main() {
    LRUCache cache(2);
    std::string value;

    cache.Put("a", "1");
    cache.Put("b", "2");
    assert(cache.Size() == 2);

    assert(cache.Get("a", &value));
    assert(value == "1");
    assert(cache.HitCount() == 1);

    cache.Put("c", "3");
    assert(cache.Size() == 2);
    assert(!cache.Get("b", &value));
    assert(cache.MissCount() == 1);

    cache.Put("a", "10");
    assert(cache.Get("a", &value));
    assert(value == "10");

    cache.Erase("a");
    assert(!cache.Get("a", &value));

    cache.ResetStats();
    assert(cache.HitCount() == 0);
    assert(cache.MissCount() == 0);

    std::cout << "lru_cache_test passed\n";
    return 0;
}
