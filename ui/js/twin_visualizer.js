/**
 * Virtual Human Digital Twin Organ Visualizer
 * Renders interactive SVG anatomical avatar and maps real-time
 * physiological compartment states to visual organ indicators.
 */

class TwinVisualizer {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    this.selectedOrgan = "pancreas";
    this.currentData = null;
    this.init();
  }

  init() {
    if (!this.container) return;
    this.render();
  }

  update(patient, telemetryLatest, assessment) {
    this.currentData = { patient, telemetryLatest, assessment };
    this.updateOrganValues();
  }

  render() {
    this.container.innerHTML = `
      <div class="flex flex-col h-full justify-between">
        <div class="flex items-center justify-between pb-2 border-b border-slate-700/60 mb-2">
          <div class="flex items-center space-x-2">
            <span class="relative flex h-2.5 w-2.5">
              <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
              <span class="relative inline-flex rounded-full h-2.5 w-2.5 bg-cyan-500"></span>
            </span>
            <h3 class="text-xs font-semibold tracking-wider text-slate-300 uppercase">Virtual Twin Physiological Map</h3>
          </div>
          <span class="text-[11px] text-cyan-400 font-mono" id="twin-sync-status">Bergman-Hovorka ODE Active</span>
        </div>

        <!-- Interactive Anatomical Representation -->
        <div class="relative w-full flex items-center justify-center py-2">
          <svg viewBox="0 0 240 380" class="w-48 h-64 filter drop-shadow-[0_0_15px_rgba(6,182,212,0.15)]">
            <!-- Stylized Human Silhouette Body -->
            <path d="M120 20 C130 20 140 28 140 42 C140 54 132 62 120 62 C108 62 100 54 100 42 C100 28 110 20 120 20 Z" 
                  fill="#1e293b" stroke="#38bdf8" stroke-width="1.5" stroke-dasharray="2 2" opacity="0.8"/>
            <!-- Torso -->
            <path d="M96 68 C80 82 72 105 70 145 C68 185 75 220 85 240 L90 350 L108 350 L115 250 L125 250 L132 350 L150 350 L155 240 C165 220 172 185 170 145 C168 105 160 82 144 68 Z" 
                  fill="#0f172a" stroke="#38bdf8" stroke-width="1.8" opacity="0.85"/>
            <!-- Arms outline -->
            <path d="M72 105 L50 170 L55 230 M168 105 L190 170 L185 230" 
                  fill="none" stroke="#38bdf8" stroke-width="1.2" stroke-dasharray="3 3" opacity="0.6"/>

            <!-- Organ Indicator Nodes (Interactive Glowing Circles) -->
            <!-- 1. Brain / Autonomic Tone -->
            <g class="organ-node cursor-pointer" onclick="twinVisualizer.selectOrgan('brain')">
              <circle cx="120" cy="42" r="8" fill="#06b6d4" fill-opacity="0.25" stroke="#06b6d4" stroke-width="2"/>
              <circle cx="120" cy="42" r="3" fill="#38bdf8"/>
              <text x="135" y="45" font-size="9" fill="#94a3b8" font-family="sans-serif">Autonomic</text>
            </g>

            <!-- 2. Heart / Cardiovascular -->
            <g class="organ-node cursor-pointer" onclick="twinVisualizer.selectOrgan('heart')">
              <circle id="node-heart" cx="128" cy="115" r="9" fill="#f43f5e" fill-opacity="0.3" stroke="#f43f5e" stroke-width="2"/>
              <circle cx="128" cy="115" r="4" fill="#fb7185"/>
              <text x="145" y="118" font-size="9" fill="#fda4af" font-weight="bold" font-family="sans-serif">Heart / HRV</text>
            </g>

            <!-- 3. Pancreas / Beta-Cells -->
            <g class="organ-node cursor-pointer" onclick="twinVisualizer.selectOrgan('pancreas')">
              <circle id="node-pancreas" cx="118" cy="148" r="9" fill="#f59e0b" fill-opacity="0.3" stroke="#f59e0b" stroke-width="2"/>
              <circle cx="118" cy="148" r="4" fill="#fde68a"/>
              <text x="135" y="152" font-size="9" fill="#fde68a" font-weight="bold" font-family="sans-serif">Pancreas β</text>
            </g>

            <!-- 4. Liver / Hepatic EGP -->
            <g class="organ-node cursor-pointer" onclick="twinVisualizer.selectOrgan('liver')">
              <circle id="node-liver" cx="102" cy="138" r="8" fill="#8b5cf6" fill-opacity="0.25" stroke="#8b5cf6" stroke-width="1.8"/>
              <circle cx="102" cy="138" r="3.5" fill="#a78bfa"/>
              <text x="45" y="142" font-size="9" fill="#c4b5fd" font-family="sans-serif">Liver (EGP)</text>
            </g>

            <!-- 5. Kidneys / Renal Clearance -->
            <g class="organ-node cursor-pointer" onclick="twinVisualizer.selectOrgan('kidneys')">
              <circle id="node-kidneys" cx="120" cy="178" r="8" fill="#10b981" fill-opacity="0.25" stroke="#10b981" stroke-width="1.8"/>
              <circle cx="120" cy="178" r="3.5" fill="#34d399"/>
              <text x="136" y="182" font-size="9" fill="#6ee7b7" font-family="sans-serif">Kidneys (eGFR)</text>
            </g>
          </svg>
        </div>

        <!-- Selected Organ Live Diagnostics Box -->
        <div id="organ-detail-box" class="bg-slate-900/90 border border-slate-700/70 rounded-md p-2.5 text-xs">
          <!-- Dynamically populated -->
        </div>
      </div>
    `;

    this.selectOrgan("pancreas");
  }

  selectOrgan(organKey) {
    this.selectedOrgan = organKey;
    this.updateOrganValues();
  }

  updateOrganValues() {
    const box = document.getElementById("organ-detail-box");
    if (!box) return;

    if (!this.currentData) {
      box.innerHTML = `<span class="text-slate-400">Loading physiological telemetry...</span>`;
      return;
    }

    const { patient, telemetryLatest, assessment } = this.currentData;

    if (this.selectedOrgan === "pancreas") {
      box.innerHTML = `
        <div class="flex items-center justify-between mb-1">
          <span class="font-bold text-amber-400 flex items-center">
            <span class="w-2 h-2 rounded-full bg-amber-400 mr-1.5"></span> Pancreas (Endocrine Beta-Cells)
          </span>
          <span class="text-[10px] bg-amber-950 text-amber-300 px-1.5 py-0.5 rounded border border-amber-800">
            Sensitivity: Impaired
          </span>
        </div>
        <div class="grid grid-cols-2 gap-1 text-[11px] text-slate-300 mt-1.5">
          <div>Insulin Sensitivity S_I: <b class="text-slate-100 font-mono">0.0000035</b></div>
          <div>Active Insulin Action X: <b class="text-slate-100 font-mono">${telemetryLatest?.insulin_action_x || 0.002}</b></div>
          <div>Baseline Fasting Gb: <b class="text-slate-100 font-mono">${patient.fasting_glucose_mg_dl} mg/dL</b></div>
          <div>Beta-Cell Reserve: <b class="text-amber-300">${patient.duration_t2d_years > 8 ? "Diminished" : "Compensating"}</b></div>
        </div>
      `;
    } else if (this.selectedOrgan === "heart") {
      box.innerHTML = `
        <div class="flex items-center justify-between mb-1">
          <span class="font-bold text-rose-400 flex items-center">
            <span class="w-2 h-2 rounded-full bg-rose-500 animate-heartbeat mr-1.5"></span> Heart & Autonomic Tone
          </span>
          <span class="text-[10px] bg-rose-950 text-rose-300 px-1.5 py-0.5 rounded border border-rose-800">
            Strain: ${assessment?.cardio_strain_index || 45}/100
          </span>
        </div>
        <div class="grid grid-cols-2 gap-1 text-[11px] text-slate-300 mt-1.5">
          <div>Wearable Heart Rate: <b class="text-slate-100 font-mono">${telemetryLatest?.heart_rate_bpm || 76} bpm</b></div>
          <div>HRV (RMSSD): <b class="text-slate-100 font-mono">${telemetryLatest?.hrv_rmssd_ms || 28} ms</b></div>
          <div>Blood Pressure: <b class="text-slate-100 font-mono">${patient.blood_pressure_systolic}/${patient.blood_pressure_diastolic}</b></div>
          <div>Arrhythmia Vulnerability: <b class="text-rose-300">${assessment?.cardio_strain_index > 65 ? "Elevated" : "Low"}</b></div>
        </div>
      `;
    } else if (this.selectedOrgan === "kidneys") {
      box.innerHTML = `
        <div class="flex items-center justify-between mb-1">
          <span class="font-bold text-emerald-400 flex items-center">
            <span class="w-2 h-2 rounded-full bg-emerald-400 mr-1.5"></span> Renal Glucose Clearance
          </span>
          <span class="text-[10px] bg-emerald-950 text-emerald-300 px-1.5 py-0.5 rounded border border-emerald-800">
            eGFR: ${patient.egfr} mL/min
          </span>
        </div>
        <div class="grid grid-cols-2 gap-1 text-[11px] text-slate-300 mt-1.5">
          <div>Glycosuria Threshold: <b class="text-slate-100 font-mono">195 mg/dL</b></div>
          <div>Urine ACR: <b class="text-slate-100 font-mono">${patient.urine_acr_mg_g} mg/g</b></div>
          <div>SGLT2 Transport State: <b class="text-emerald-300 font-mono">Intact</b></div>
          <div>Drug Clearance Half-Life: <b class="text-slate-100 font-mono">${patient.egfr < 60 ? "Prolonged" : "Normal"}</b></div>
        </div>
      `;
    } else if (this.selectedOrgan === "liver") {
      box.innerHTML = `
        <div class="flex items-center justify-between mb-1">
          <span class="font-bold text-purple-400 flex items-center">
            <span class="w-2 h-2 rounded-full bg-purple-400 mr-1.5"></span> Hepatic Glucose Output (EGP)
          </span>
          <span class="text-[10px] bg-purple-950 text-purple-300 px-1.5 py-0.5 rounded border border-purple-800">
            Metformin Target
          </span>
        </div>
        <div class="grid grid-cols-2 gap-1 text-[11px] text-slate-300 mt-1.5">
          <div>Basal EGP Rate: <b class="text-slate-100 font-mono">1.25 mg/dL/min</b></div>
          <div>Metformin Suppression: <b class="text-emerald-400">Active (-28%)</b></div>
          <div>Lipid Profile: <b class="text-slate-100 font-mono">TG ${patient.lipid_panel.triglycerides} / HDL ${patient.lipid_panel.hdl}</b></div>
          <div>Hepatic Steatosis Risk: <b class="text-purple-300">${patient.bmi > 26 ? "High" : "Moderate"}</b></div>
        </div>
      `;
    } else {
      box.innerHTML = `
        <div class="flex items-center justify-between mb-1">
          <span class="font-bold text-cyan-400 flex items-center">
            <span class="w-2 h-2 rounded-full bg-cyan-400 mr-1.5"></span> Autonomic & Circadian Rhythms
          </span>
          <span class="text-[10px] bg-cyan-950 text-cyan-300 px-1.5 py-0.5 rounded border border-cyan-800">
            State: ${telemetryLatest?.activity_state || 'sedentary'}
          </span>
        </div>
        <div class="grid grid-cols-2 gap-1 text-[11px] text-slate-300 mt-1.5">
          <div>Circadian Window: <b class="text-slate-100 font-mono">${telemetryLatest?.activity_state === 'sleep' ? 'Nocturnal Sleep' : 'Active Daytime'}</b></div>
          <div>Sympathovagal Balance: <b class="text-slate-100 font-mono">LF/HF 2.1</b></div>
          <div>Step Cadence: <b class="text-slate-100 font-mono">${telemetryLatest?.steps || 0} steps/5m</b></div>
          <div>Dawn Phenomenon Risk: <b class="text-cyan-300">Moderate</b></div>
        </div>
      `;
    }
  }
}
