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

lru_cache_test: lru_cache_test.cpp lru_cache.cpp lru_cache.h
	$(CXX) $(CXXFLAGS) -o lru_cache_test lru_cache_test.cpp lru_cache.cpp

clean:
	rm -f task1 task2 task3 lru_cache_test

.PHONY: all clean
