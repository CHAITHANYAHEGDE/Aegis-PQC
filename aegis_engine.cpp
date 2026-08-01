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
#include <thread>
#include "onnx_inference.hpp"
#include "policy_engine.hpp"
#ifdef __linux__
#include <linux/perf_event.h>
#include <sys/syscall.h>
#include <sys/ioctl.h>
#include <unistd.h>
#include <string.h>

class PerfCounter {
private:
    int fd;
public:
    PerfCounter(uint32_t type, uint64_t config) : fd(-1) {
        struct perf_event_attr pe;
        memset(&pe, 0, sizeof(struct perf_event_attr));
        pe.type = type;
        pe.size = sizeof(struct perf_event_attr);
        pe.config = config;
        pe.disabled = 1;
        pe.exclude_kernel = 1;
        pe.exclude_hv = 1;

        fd = syscall(__NR_perf_event_open, &pe, 0, -1, -1, 0);
    }

    ~PerfCounter() {
        if (fd != -1) {
            close(fd);
        }
    }

    bool is_valid() const {
        return fd != -1;
    }

    void start() {
        if (fd != -1) {
            ioctl(fd, PERF_EVENT_IOC_RESET, 0);
            ioctl(fd, PERF_EVENT_IOC_ENABLE, 0);
        }
    }

    void stop() {
        if (fd != -1) {
            ioctl(fd, PERF_EVENT_IOC_DISABLE, 0);
        }
    }

    long long read_val() {
        if (fd == -1) return -1;
        long long count = -1;
        if (read(fd, &count, sizeof(long long)) != sizeof(long long)) {
            return -1;
        }
        return count;
    }
};

class PerfGroup {
public:
    PerfCounter cycles;
    PerfCounter instructions;
    PerfCounter cache_refs;
    PerfCounter cache_misses;
    PerfCounter branches;
    PerfCounter branch_misses;
    PerfCounter page_faults;
    PerfCounter ctx_switches;
    PerfCounter cpu_migrations;
    bool valid;

    PerfGroup() :
        cycles(PERF_TYPE_HARDWARE, PERF_COUNT_HW_CPU_CYCLES),
        instructions(PERF_TYPE_HARDWARE, PERF_COUNT_HW_INSTRUCTIONS),
        cache_refs(PERF_TYPE_HARDWARE, PERF_COUNT_HW_CACHE_REFERENCES),
        cache_misses(PERF_TYPE_HARDWARE, PERF_COUNT_HW_CACHE_MISSES),
        branches(PERF_TYPE_HARDWARE, PERF_COUNT_HW_BRANCH_INSTRUCTIONS),
        branch_misses(PERF_TYPE_HARDWARE, PERF_COUNT_HW_BRANCH_MISSES),
        page_faults(PERF_TYPE_SOFTWARE, PERF_COUNT_SW_PAGE_FAULTS),
        ctx_switches(PERF_TYPE_SOFTWARE, PERF_COUNT_SW_CONTEXT_SWITCHES),
        cpu_migrations(PERF_TYPE_SOFTWARE, PERF_COUNT_SW_CPU_MIGRATIONS)
    {
        // If at least cycles works, we consider HW telemetry somewhat available
        valid = cycles.is_valid();
    }

    void start() {
        if(!valid) return;
        cycles.start(); instructions.start(); cache_refs.start(); cache_misses.start();
        branches.start(); branch_misses.start(); page_faults.start(); ctx_switches.start(); cpu_migrations.start();
    }

    void stop() {
        if(!valid) return;
        cycles.stop(); instructions.stop(); cache_refs.stop(); cache_misses.stop();
        branches.stop(); branch_misses.stop(); page_faults.stop(); ctx_switches.stop(); cpu_migrations.stop();
    }
    
    void populate_telemetry(std::map<std::string, double>& t) {
        if (valid) {
            t["hw_telemetry_available"] = 1.0;
            t["hw_cpu_cycles"] = cycles.read_val();
            t["hw_instructions"] = instructions.read_val();
            t["hw_cache_references"] = cache_refs.read_val();
            t["hw_cache_misses"] = cache_misses.read_val();
            t["hw_branch_instructions"] = branches.read_val();
            t["hw_branch_misses"] = branch_misses.read_val();
            t["sw_page_faults"] = page_faults.read_val();
            t["sw_context_switches"] = ctx_switches.read_val();
            t["sw_cpu_migrations"] = cpu_migrations.read_val();
        } else {
            set_unsupported(t);
        }
    }
    
    static void set_unsupported(std::map<std::string, double>& t) {
        t["hw_telemetry_available"] = 0.0;
        t["hw_cpu_cycles"] = -1.0;
        t["hw_instructions"] = -1.0;
        t["hw_cache_references"] = -1.0;
        t["hw_cache_misses"] = -1.0;
        t["hw_branch_instructions"] = -1.0;
        t["hw_branch_misses"] = -1.0;
        t["sw_page_faults"] = -1.0;
        t["sw_context_switches"] = -1.0;
        t["sw_cpu_migrations"] = -1.0;
    }
};

#else
class PerfGroup {
public:
    void start() {}
    void stop() {}
    void populate_telemetry(std::map<std::string, double>& t) {
        set_unsupported(t);
    }
    static void set_unsupported(std::map<std::string, double>& t) {
        t["hw_telemetry_available"] = 0.0;
        t["hw_cpu_cycles"] = -1.0;
        t["hw_instructions"] = -1.0;
        t["hw_cache_references"] = -1.0;
        t["hw_cache_misses"] = -1.0;
        t["hw_branch_instructions"] = -1.0;
        t["hw_branch_misses"] = -1.0;
        t["sw_page_faults"] = -1.0;
        t["sw_context_switches"] = -1.0;
        t["sw_cpu_migrations"] = -1.0;
    }
};
#endif

namespace py = pybind11;

// Global Singletons for Model and Policy
static ONNXModel* g_model = nullptr;
static PolicyEngine* g_policy = nullptr;

void init_defense_subsystem() {
    if (!g_model) {
        g_model = new ONNXModel("rf_model.onnx");
    }
    if (!g_policy) {
        g_policy = new PolicyEngine(2, 1000);
    }
}

std::map<std::string, double> run_crypto(const std::string& algo_name, const std::string& attack_profile) {
    init_defense_subsystem();

    std::map<std::string, double> telemetry;
    
    // Legacy Software Telemetry structs
    struct rusage usage_start, usage_end;
    getrusage(RUSAGE_SELF, &usage_start);
    
    PerfGroup hw_perf;
    
    auto t_start = std::chrono::high_resolution_clock::now();
    
    hw_perf.start();
    
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
    
    hw_perf.stop();
    
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
    
    // Core telemetry
    telemetry["execution_time_us"] = elapsed_us;
    telemetry["context_switches"] = ctx_switches;
    telemetry["max_rss_kb"] = max_rss;
    telemetry["cpu_usage"] = utime + stime;
    telemetry["synthetic_cache_proxy"] = synthetic_cache_proxy;
    telemetry["synthetic_branch_proxy"] = synthetic_branch_proxy;
    
    // Populate Hardware Telemetry
    hw_perf.populate_telemetry(telemetry);
    
    // Evaluate Anomaly using Native Runtime ONNX Model
    if (g_model && g_model->loaded()) {
        std::vector<float> features;
        // Software features
        features.push_back(telemetry["execution_time_us"]);
        features.push_back(telemetry["max_rss_kb"]);
        features.push_back(telemetry["context_switches"]);
        features.push_back(telemetry["cpu_usage"]);
        features.push_back(telemetry["synthetic_cache_proxy"]);
        features.push_back(telemetry["synthetic_branch_proxy"]);
        
        // Hardware features
        features.push_back(telemetry["hw_cpu_cycles"]);
        features.push_back(telemetry["hw_instructions"]);
        features.push_back(telemetry["hw_cache_references"]);
        features.push_back(telemetry["hw_cache_misses"]);
        features.push_back(telemetry["hw_branch_instructions"]);
        features.push_back(telemetry["hw_branch_misses"]);
        features.push_back(telemetry["sw_page_faults"]);
        
        double prediction = g_model->predict(features);
        double anomaly_score = (prediction > 0.5) ? 1.0 : 0.0;
        double confidence = (prediction > 0.5) ? 0.9 : 0.1;
        bool hw_available = (telemetry["hw_telemetry_available"] > 0.5);
        
        PolicyDecision decision = g_policy->evaluate(anomaly_score, confidence, hw_available);
        
        telemetry["mitigation_action"] = static_cast<double>(decision.action);
        telemetry["mitigation_delay_us"] = decision.delay_us;
        
        if (decision.action == MitigationAction::DELAY && decision.delay_us > 0) {
            std::this_thread::sleep_for(std::chrono::microseconds(decision.delay_us));
        }
    } else {
        telemetry["mitigation_action"] = 0.0;
        telemetry["mitigation_delay_us"] = 0.0;
    }
    
    return telemetry;
}

PYBIND11_MODULE(aegis_engine, m) {
    m.doc() = "Aegis PQC native crypto engine via pybind11 and liboqs (with Linux perf hw telemetry)";
    m.def("run_crypto", &run_crypto, "Execute PQC algorithm and return telemetry",
          py::arg("algo_name"), py::arg("attack_profile") = "none");
}
