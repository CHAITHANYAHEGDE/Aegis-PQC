#include <iostream>
#include <fstream>
#include <chrono>
#include <random>
#include <string>
#include <vector>
#include <cstring>
#include <oqs/oqs.h>

int main(int argc, char** argv) {
    bool attack_mode = false;
    if (argc > 1 && std::string(argv[1]) == "--attack") {
        attack_mode = true;
    }

    OQS_KEM *kem = OQS_KEM_new(OQS_KEM_alg_ml_kem_512);
    if (kem == NULL) {
        return 1;
    }

    uint8_t *public_key = (uint8_t *)malloc(kem->length_public_key);
    uint8_t *secret_key = (uint8_t *)malloc(kem->length_secret_key);
    uint8_t *ciphertext = (uint8_t *)malloc(kem->length_ciphertext);
    uint8_t *shared_secret_e = (uint8_t *)malloc(kem->length_shared_secret);
    
    OQS_KEM_keypair(kem, public_key, secret_key);

    std::ofstream outfile("timing_trace.txt");
    
    std::mt19937 rng(std::random_device{}());
    std::uniform_int_distribution<int> delay_dist(100, 300);

    for(int i=0; i<16; i++) {
        auto start = std::chrono::high_resolution_clock::now();
        OQS_KEM_encaps(kem, ciphertext, shared_secret_e, public_key);
        
        if (attack_mode) {
            volatile int sum = 0;
            int target = delay_dist(rng);
            for(int j = 0; j < target * 100; j++) {
                sum += j; // busy wait cache eviction simulation
            }
        }
        auto end = std::chrono::high_resolution_clock::now();
        double elapsed_us = std::chrono::duration<double, std::micro>(end - start).count();
        outfile << elapsed_us << (i == 15 ? "" : ",");
    }

    outfile.close();

    OQS_KEM_free(kem);
    free(public_key);
    free(secret_key);
    free(ciphertext);
    free(shared_secret_e);

    return 0;
}
