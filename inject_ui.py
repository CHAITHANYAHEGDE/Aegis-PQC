import re

with open("templates/index.html", "r") as f:
    html = f.read()

# Inject into the top System State Panel
system_state_addition = """
                    <div style="display: flex; gap: 2rem; margin-top: 1rem;">
                        <div>
                            <div style="font-size: 0.6rem; color: #8e939e; letter-spacing: 0.1em; font-weight: 800;">THREAT LEVEL</div>
                            <div id="threat-level-val" style="font-size: 1.2rem; color: #10b981; font-weight: 800;">LOW</div>
                        </div>
                        <div>
                            <div style="font-size: 0.6rem; color: #8e939e; letter-spacing: 0.1em; font-weight: 800;">MITIGATION ACTION</div>
                            <div id="mitigation-action-val" style="font-size: 1.2rem; color: #8e939e; font-weight: 800;">NONE</div>
                        </div>
                    </div>
"""
html = html.replace('<span id="sys-status" class="stat-value status-safe">SAFE</span>', '<span id="sys-status" class="stat-value status-safe">SAFE</span>' + system_state_addition)

# Add defense metrics to the stats grid
stats_addition = """
                    <div class="stat-card">
                        <span class="stat-label">DETECTION LATENCY</span>
                        <span id="latency-ml-val" class="stat-value">--- ms</span>
                    </div>
                    <div class="stat-card">
                        <span class="stat-label">MITIGATION LATENCY</span>
                        <span id="latency-mitigation-val" class="stat-value">--- ms</span>
                    </div>
                    <div class="stat-card">
                        <span class="stat-label">TOTAL LATENCY</span>
                        <span id="latency-total-val" class="stat-value">--- ms</span>
                    </div>
                    <div class="stat-card">
                        <span class="stat-label">MITIGATIONS / FALSE MIT.</span>
                        <span id="mitigation-count-val" class="stat-value">0 / 0</span>
                    </div>
"""
html = html.replace('</div>\n            </div>\n\n            <!-- Timing Chart -->', '</div>\n' + stats_addition + '\n            </div>\n\n            <!-- Timing Chart -->')

# Add the Active Defenses card to the right panel
defense_card = """
            <div class="card">
                <div class="card-title">Active Response Policies</div>
                <div class="action-group">
                    <label style="display:flex; align-items:center; gap: 0.5rem; color: white;">
                        <input type="checkbox" id="toggle-random-delay" checked onchange="updateDefenseConfig()"> Randomized Delay
                    </label>
                    <label style="display:flex; align-items:center; gap: 0.5rem; color: white;">
                        <input type="checkbox" id="toggle-throttling" checked onchange="updateDefenseConfig()"> Request Throttling
                    </label>
                    <label style="display:flex; align-items:center; gap: 0.5rem; color: white;">
                        <input type="checkbox" id="toggle-forensic-logger" checked onchange="updateDefenseConfig()"> Forensic Logging
                    </label>
                    <label style="display:flex; align-items:center; gap: 0.5rem; color: white;">
                        <input type="checkbox" id="toggle-alerting" checked onchange="updateDefenseConfig()"> Alert Generation
                    </label>
                    <label style="display:flex; align-items:center; gap: 0.5rem; color: white;">
                        <input type="checkbox" id="toggle-key-rotation" checked onchange="updateDefenseConfig()"> Key Rotation (Stub)
                    </label>
                    <button class="btn btn-outline" style="margin-top:1rem;" onclick="window.open('/api/defense/logs', '_blank')">
                        View Forensic Defense Logs
                    </button>
                </div>
            </div>
"""
html = html.replace('<!-- Command Center & Simulator Panel -->', '<!-- Active Defense -->\n' + defense_card + '\n            <!-- Command Center & Simulator Panel -->')

# Update JS to handle mitigation logic
js_additions = """
        let mitigationCount = 0;
        let falseMitigationCount = 0;

        async function loadDefenseConfig() {
            try {
                const res = await fetch('/api/defense/config');
                const cfg = await res.json();
                document.getElementById('toggle-random-delay').checked = cfg.randomized_delay;
                document.getElementById('toggle-throttling').checked = cfg.throttling;
                document.getElementById('toggle-forensic-logger').checked = cfg.forensic_logger;
                document.getElementById('toggle-alerting').checked = cfg.alerting;
                document.getElementById('toggle-key-rotation').checked = cfg.key_rotation;
            } catch(e) {}
        }
        
        async function updateDefenseConfig() {
            const cfg = {
                randomized_delay: document.getElementById('toggle-random-delay').checked,
                throttling: document.getElementById('toggle-throttling').checked,
                forensic_logger: document.getElementById('toggle-forensic-logger').checked,
                alerting: document.getElementById('toggle-alerting').checked,
                key_rotation: document.getElementById('toggle-key-rotation').checked
            };
            await fetch('/api/defense/config', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(cfg)
            });
        }
"""
html = html.replace('function handleTelemetryEvent(data) {', js_additions + '\n        function handleTelemetryEvent(data) {')

# Inside handleTelemetryEvent
event_update = """
            if (data.performance) {
                document.getElementById('latency-ml-val').innerText = (data.performance.ml_inference_latency_s * 1000).toFixed(2) + " ms";
                document.getElementById('latency-total-val').innerText = (data.performance.total_latency_s * 1000).toFixed(2) + " ms";
            }
            if (data.defense) {
                document.getElementById('latency-mitigation-val').innerText = (data.defense.mitigation_overhead_s * 1000).toFixed(2) + " ms";
                document.getElementById('mitigation-action-val').innerText = data.defense.mitigation_action;
                
                if (data.defense.mitigation_action !== "Allow" && data.defense.mitigation_action !== "Enhanced Monitoring" && data.defense.mitigation_action !== "None") {
                    mitigationCount++;
                    if (!isAnomaly) {
                        falseMitigationCount++;
                    }
                }
                document.getElementById('mitigation-count-val').innerText = mitigationCount + " / " + falseMitigationCount;
                
                if (data.confidence < 30) {
                    document.getElementById('threat-level-val').innerText = "LOW";
                    document.getElementById('threat-level-val').style.color = "#10b981";
                } else if (data.confidence < 60) {
                    document.getElementById('threat-level-val').innerText = "MEDIUM";
                    document.getElementById('threat-level-val').style.color = "#f97316";
                } else if (data.confidence < 80) {
                    document.getElementById('threat-level-val').innerText = "HIGH";
                    document.getElementById('threat-level-val').style.color = "#ef4444";
                } else {
                    document.getElementById('threat-level-val').innerText = "CRITICAL";
                    document.getElementById('threat-level-val').style.color = "#ef4444";
                }
            }
            
            const mitigationActionStr = data.defense ? " | Mitigation: " + data.defense.mitigation_action : "";
"""
html = html.replace('const timing = data.measured.execution_time_us;', event_update + '\n            const timing = data.measured.execution_time_us;')

html = html.replace('appendLog(`[ALERT] Anomaly Detected! Profile: ${data.attack_profile} | Score: ${score.toFixed(3)} | Confidence: ${data.confidence.toFixed(1)}%`, \'log-alert\', true);', 'appendLog(`[ALERT] Anomaly Detected! Profile: ${data.attack_profile} | Score: ${score.toFixed(3)} | Confidence: ${data.confidence.toFixed(1)}%${mitigationActionStr}`, \'log-alert\', true);')

html = html.replace('appendLog(`[SAFE] Simulated attack cleared. Score: ${score.toFixed(3)}`, \'log-safe\', false);', 'appendLog(`[SAFE] Simulated attack cleared. Score: ${score.toFixed(3)}${mitigationActionStr}`, \'log-safe\', false);')

html = html.replace('appendLog(`[NORMAL] timing: ${timing.toFixed(3)} µs | Score: ${score.toFixed(3)} | Status: CLEAR`, \'log-safe\', false);', 'appendLog(`[NORMAL] timing: ${timing.toFixed(3)} µs | Score: ${score.toFixed(3)} | Status: CLEAR${mitigationActionStr}`, \'log-safe\', false);')

html = html.replace('await fetch(\'/api/stats\');', 'await fetch(\'/api/stats\');\n                await loadDefenseConfig();')

with open("templates/index.html", "w") as f:
    f.write(html)
