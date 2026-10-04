#include "algorithms/palindrome.hpp"
#include "generator/data_generator.hpp"
#include <iostream>
#include <iomanip>
#include <chrono>

int main() {
    std::cout << "\n======================================================\n";
    std::cout << " BENCHMARK: MANACHER O(N) VS NAIVE O(N^2) PALINDROME\n";
    std::cout << "======================================================\n";

    dc::generator::DataGenerator gen(42);

    std::cout << std::left << std::setw(12) << "Length (N)"
              << std::setw(20) << "Manacher O(N)"
              << std::setw(20) << "Naive O(N^2)"
              << "Speedup\n";
    std::cout << "------------------------------------------------------\n";

    for (int n : {100, 500, 1000, 2000, 5000}) {
        std::string stream = gen.generate_random(n);

        auto t0 = std::chrono::high_resolution_clock::now();
        auto m_res = dc::algorithms::find_longest_palindrome(stream);
        auto t1 = std::chrono::high_resolution_clock::now();
        double m_us = std::chrono::duration<double, std::micro>(t1 - t0).count();

        auto t2 = std::chrono::high_resolution_clock::now();
        auto n_res = dc::algorithms::naive_longest_palindrome(stream);
        auto t3 = std::chrono::high_resolution_clock::now();
        double n_us = std::chrono::duration<double, std::micro>(t3 - t2).count();

        double speedup = (m_us > 0.0) ? (n_us / m_us) : 1.0;

        std::cout << std::left << std::setw(12) << n
                  << std::setw(20) << (std::to_string(static_cast<int>(m_us)) + " us")
                  << std::setw(20) << (std::to_string(static_cast<int>(n_us)) + " us")
                  << std::fixed << std::setprecision(1) << speedup << "x\n";
    }

    std::cout << "======================================================\n\n";
    return 0;
}
