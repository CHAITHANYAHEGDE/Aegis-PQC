#ifndef POLICY_ENGINE_HPP
#define POLICY_ENGINE_HPP

#include <string>
#include <vector>
#include <chrono>
#include <iostream>
#include <random>

enum class MitigationAction {
    NONE,
    DELAY,
    DUMMY_OP,
    THROTTLE,
    ALERT
};

struct PolicyDecision {
    MitigationAction action;
    int delay_us;
    std::string reason;
};

class PolicyEngine {
private:
    int detection_threshold_hits = 0;
    int required_hits_for_mitigation = 2; // Attack persistence
    
    std::chrono::time_point<std::chrono::steady_clock> last_mitigation_time;
    int cooldown_ms = 1000; // Cooldown timer in ms

    double confidence_threshold = 0.8;
    bool hardware_telemetry_trusted = true;

public:
    PolicyEngine(int hits = 2, int cooldown = 1000) 
        : required_hits_for_mitigation(hits), cooldown_ms(cooldown) {
        last_mitigation_time = std::chrono::steady_clock::now() - std::chrono::hours(1);
    }

    PolicyDecision evaluate(double anomaly_score, double confidence, bool hw_available) {
        PolicyDecision decision = {MitigationAction::NONE, 0, "Normal operation"};
        
        // If hardware telemetry isn't available, we might require higher confidence
        double effective_threshold = hw_available ? confidence_threshold : confidence_threshold + 0.1;
        
        if (anomaly_score > 0.5 && confidence >= effective_threshold) {
            detection_threshold_hits++;
        } else {
            // Decay hits if normal traffic resumes
            if (detection_threshold_hits > 0) detection_threshold_hits--;
        }

        if (detection_threshold_hits >= required_hits_for_mitigation) {
            auto now = std::chrono::steady_clock::now();
            auto time_since_last = std::chrono::duration_cast<std::chrono::milliseconds>(now - last_mitigation_time).count();
            
            if (time_since_last > cooldown_ms) {
                // Trigger mitigation
                decision.action = MitigationAction::DELAY;
                
                // Randomize delay to obfuscate timing further
                std::mt19937 rng(std::random_device{}());
                std::uniform_int_distribution<int> dist(5000, 20000); // 5ms to 20ms delay
                decision.delay_us = dist(rng);
                decision.reason = "Persistent attack detected. Injecting delay.";
                
                last_mitigation_time = now;
                // Reset hits after mitigation to avoid endless throttling if attack stops
                detection_threshold_hits = 0; 
            } else {
                decision.reason = "Attack detected but mitigation on cooldown.";
            }
        }

        return decision;
    }
};

#endif
