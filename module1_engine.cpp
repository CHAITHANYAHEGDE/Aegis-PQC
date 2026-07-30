#include <iostream>
#include <array>
#include <chrono>
#include <random>
#include <fstream>

// Kyber-768 Parameters
constexpr size_t KYBER_N = 256;
constexpr int16_t KYBER_Q = 3329;

struct Polynomial {
    std::array<int16_t, KYBER_N> coeffs{};

    static int16_t reduce(int32_t val) {
        int16_t r = val % KYBER_Q;
        return (r < 0) ? (r + KYBER_Q) : r;
    }

    Polynomial multiply(const Polynomial& other) const {
        Polynomial res{};
        std::array<int32_t, 2 * KYBER_N> temp{};

        for (size_t i = 0; i < KYBER_N; ++i) {
            for (size_t j = 0; j < KYBER_N; ++j) {
                temp[i + j] += static_cast<int32_t>(this->coeffs[i]) * other.coeffs[j];
            }
        }
        for (size_t i = 0; i < KYBER_N; ++i) {
            int32_t val = temp[i] - temp[i + KYBER_N];
            res.coeffs[i] = reduce(val);
        }
        return res;
    }
};

int main() {
    std::cout << "----------------------------------------------\n";
    std::cout << "  Module 1: C++20 Post-Quantum Kyber Engine   \n";
    std::cout << "----------------------------------------------\n";

    Polynomial polyA, polyB;
    std::mt19937 rng(1337);
    std::uniform_int_distribution<int16_t> dist(0, KYBER_Q - 1);

    for (size_t i = 0; i < KYBER_N; ++i) {
        polyA.coeffs[i] = dist(rng);
        polyB.coeffs[i] = dist(rng);
    }

    // Measure microsecond execution time
    auto start = std::chrono::high_resolution_clock::now();
    Polynomial result = polyA.multiply(polyB);
    auto end = std::chrono::high_resolution_clock::now();

    double elapsed_us = std::chrono::duration<double, std::micro>(end - start).count();

    std::cout << "✅ Kyber Polynomial Multiplication Completed!\n";
    std::cout << "⏱️ Execution Time: " << elapsed_us << " microseconds\n";

    // Save timing trace to a file for Module 2 (Python AI)
    std::ofstream outfile("timing_trace.txt");
    outfile << elapsed_us << "\n";
    outfile.close();

    std::cout << "📁 Saved timing trace to 'timing_trace.txt'\n";

    return 0;
}
