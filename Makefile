CXX ?= g++
CXXFLAGS ?= -std=c++20 -O2 -Wall -Wextra -Iinclude

COMMON_SRCS = \
	src/algorithms/palindrome.cpp \
	src/generator/data_generator.cpp \
	src/line_coding/base.cpp \
	src/line_coding/encoders.cpp \
	src/scrambling/b8zs.cpp \
	src/scrambling/hdb3.cpp \
	src/decoder/signal_decoder.cpp \
	src/analog/continuous_signal.cpp \
	src/analog/sampling.cpp \
	src/analog/quantization.cpp \
	src/analog/delta_modulation.cpp \
	src/analog/plotter.cpp \
	src/pipeline/bridge.cpp

APP_SRCS = $(COMMON_SRCS) src/cli/menu.cpp src/cli/report.cpp src/main.cpp
TEST_SRCS = $(COMMON_SRCS) tests/test_runner.cpp
BENCH_SRCS = src/algorithms/palindrome.cpp src/generator/data_generator.cpp benchmarks/benchmark_palindrome.cpp

all: bin/dc_system bin/run_tests bin/benchmark

bin:
	mkdir -p bin

bin/dc_system: $(APP_SRCS) | bin
	$(CXX) $(CXXFLAGS) $(APP_SRCS) -o bin/dc_system

bin/run_tests: $(TEST_SRCS) | bin
	$(CXX) $(CXXFLAGS) $(TEST_SRCS) -o bin/run_tests

bin/benchmark: $(BENCH_SRCS) | bin
	$(CXX) $(CXXFLAGS) $(BENCH_SRCS) -o bin/benchmark

test: bin/run_tests
	./bin/run_tests

benchmark: bin/benchmark
	./bin/benchmark

clean:
	rm -rf bin

.PHONY: all test benchmark clean
