#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <stdexcept>
#include <oqs/oqs.h>
#include <chrono>
#include <random>
#include <vector>
#include <string>
#include <sys/resource.h>
#include <map>

namespace py = pybind11;

std::map<std::string, double> run_crypto(const std::string& algo_name, const std::string& attack_profile) {
    std::map<std::string, double> telemetry;
    
    // Telemetry structs
    struct rusage usage_start, usage_end;
    getrusage(RUSAGE_SELF, &usage_start);
    
    auto t_start = std::chrono::high_resolution_clock::now();
    
    // KEM or SIG
    if (algo_name.find("ML-KEM") != std::string::npos) {
        // Convert Python string to liboqs string (e.g. ML-KEM-512)
        OQS_KEM *kem = OQS_KEM_new(algo_name.c_str());
        if (kem != NULL) {
            uint8_t *public_key = (uint8_t *)malloc(kem->length_public_key);
            uint8_t *secret_key = (uint8_t *)malloc(kem->length_secret_key);
            uint8_t *ciphertext = (uint8_t *)malloc(kem->length_ciphertext);
            uint8_t *shared_secret = (uint8_t *)malloc(kem->length_shared_secret);
            
            if (public_key && secret_key && ciphertext && shared_secret) {
                OQS_KEM_keypair(kem, public_key, secret_key);
                OQS_KEM_encaps(kem, ciphertext, shared_secret, public_key);
            }
            
            free(public_key);
            free(secret_key);
            free(ciphertext);
            free(shared_secret);
            OQS_KEM_free(kem);
        } else {
            throw std::runtime_error("Unsupported KEM algorithm: " + algo_name);
        }
    } else if (algo_name.find("ML-DSA") != std::string::npos || algo_name.find("Falcon") != std::string::npos || algo_name.find("SPHINCS") != std::string::npos) {
        OQS_SIG *sig = OQS_SIG_new(algo_name.c_str());
        if (sig != NULL) {
            uint8_t *public_key = (uint8_t *)malloc(sig->length_public_key);
            uint8_t *secret_key = (uint8_t *)malloc(sig->length_secret_key);
            uint8_t *message = (uint8_t *)"Aegis-PQC Signature Test Message";
            size_t message_len = 32;
            uint8_t *signature = (uint8_t *)malloc(sig->length_signature);
            size_t signature_len;
            
            if (public_key && secret_key && signature) {
                OQS_SIG_keypair(sig, public_key, secret_key);
                OQS_SIG_sign(sig, signature, &signature_len, message, message_len, secret_key);
            }
            
            free(public_key);
            free(secret_key);
            free(signature);
            OQS_SIG_free(sig);
        } else {
            throw std::runtime_error("Unsupported Signature algorithm: " + algo_name);
        }
    } else {
        throw std::runtime_error("Unknown algorithm type or missing prefix (ML-KEM, ML-DSA, Falcon, SPHINCS): " + algo_name);
    }
    
    // Emulate attacks
    double synthetic_cache_proxy = 0.0;
    double synthetic_branch_proxy = 0.0;
    
    if (attack_profile != "none") {
        std::mt19937 rng(std::random_device{}());
        volatile int sum = 0;
        
        if (attack_profile == "timing") {
            std::uniform_int_distribution<int> dist(50, 150);
            int iters = dist(rng);
            for(int i=0; i<iters*100; i++) sum += i;
            synthetic_cache_proxy += iters * 0.5;
        } else if (attack_profile == "cache_pressure") {
            std::uniform_int_distribution<int> dist(200, 500);
            int iters = dist(rng);
            // Thrash cache mock
            std::vector<int> thrash(10000);
            for(int i=0; i<10000; i++) thrash[i] = i;
            for(int i=0; i<iters*10; i++) sum += thrash[(i*64) % 10000];
            synthetic_cache_proxy += iters * 12.0;
        } else if (attack_profile == "cpu_contention") {
            std::uniform_int_distribution<int> dist(100, 300);
            int iters = dist(rng);
            for(int i=0; i<iters*200; i++) sum += (i * i);
            synthetic_branch_proxy += iters * 5.0;
        } else if (attack_profile == "thermal") {
            std::uniform_int_distribution<int> dist(300, 800);
            int iters = dist(rng);
            for(int i=0; i<iters*50; i++) sum += i;
        }
    }
    
    auto t_end = std::chrono::high_resolution_clock::now();
    getrusage(RUSAGE_SELF, &usage_end);
    
    double elapsed_us = std::chrono::duration<double, std::micro>(t_end - t_start).count();
    
    long ctx_switches = (usage_end.ru_nvcsw - usage_start.ru_nvcsw) + (usage_end.ru_nivcsw - usage_start.ru_nivcsw);
    long max_rss = usage_end.ru_maxrss;
    
    double utime = (usage_end.ru_utime.tv_sec - usage_start.ru_utime.tv_sec) * 1e6 + (usage_end.ru_utime.tv_usec - usage_start.ru_utime.tv_usec);
    double stime = (usage_end.ru_stime.tv_sec - usage_start.ru_stime.tv_sec) * 1e6 + (usage_end.ru_stime.tv_usec - usage_start.ru_stime.tv_usec);
    
    telemetry["execution_time_us"] = elapsed_us;
    telemetry["context_switches"] = ctx_switches;
    telemetry["max_rss_kb"] = max_rss;
    telemetry["cpu_usage"] = utime + stime;
    telemetry["synthetic_cache_proxy"] = synthetic_cache_proxy;
    telemetry["synthetic_branch_proxy"] = synthetic_branch_proxy;
    
    return telemetry;
}

PYBIND11_MODULE(aegis_engine, m) {
    m.doc() = "Aegis PQC native crypto engine via pybind11 and liboqs";
    m.def("run_crypto", &run_crypto, "Execute PQC algorithm and return telemetry",
          py::arg("algo_name"), py::arg("attack_profile") = "none");
}
