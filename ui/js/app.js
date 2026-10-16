/**
 * Master Clinical Digital Twin Dashboard Application
 * Orchestrates real-time telemetry streaming, predictive analytics,
 * clinician decision support, and event injection.
 */

let currentPatientId = "IND-T2D-001";
let twinVisualizer = null;
let whatIfSimUI = null;
let telemetryChart = null;
let forecastChart = null;

document.addEventListener("DOMContentLoaded", () => {
  initApp();
});

async function initApp() {
  // Initialize child controllers
  twinVisualizer = new TwinVisualizer("twin-avatar-container");
  whatIfSimUI = new WhatIfSimulatorUI("whatif-chart");

  initTelemetryChart();
  initForecastChart();

  // Load patients and initial data
  await loadPatientRoster();
  await loadPatientData(currentPatientId);

  // Setup event listeners
  setupListeners();
}

function setupListeners() {
  // Slider inputs for What-If simulator
  ["slider-carbs", "slider-exercise", "toggle-sglt2i", "toggle-reducesu", "toggle-metformin"].forEach((id) => {
    const el = document.getElementById(id);
    if (el) {
      el.addEventListener("input", () => {
        whatIfSimUI.runSimulation(currentPatientId);
      });
    }
  });

  // Modal open/close
  document.getElementById("btn-generate-report")?.addEventListener("click", openClinicalReport);
  document.getElementById("btn-close-modal")?.addEventListener("click", closeClinicalReport);
}

function initTelemetryChart() {
  const ctx = document.getElementById("telemetry-chart")?.getContext("2d");
  if (!ctx) return;

  telemetryChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: [],
      datasets: [
        {
          label: "Continuous Glucose (CGM mg/dL)",
          data: [],
          borderColor: "#06b6d4",
          backgroundColor: "rgba(6, 182, 212, 0.12)",
          borderWidth: 2.2,
          pointRadius: 1,
          pointHoverRadius: 4,
          fill: true,
          tension: 0.3,
          yAxisID: "y",
        },
        {
          label: "Heart Rate (PPG bpm)",
          data: [],
          borderColor: "#f43f5e",
          borderWidth: 1.5,
          borderDash: [3, 3],
          pointRadius: 0,
          fill: false,
          tension: 0.2,
          yAxisID: "y1",
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      plugins: {
        legend: { labels: { color: "#94a3b8", font: { size: 10 } } },
        tooltip: {
          backgroundColor: "rgba(15, 23, 42, 0.95)",
          titleColor: "#38bdf8",
          bodyColor: "#f1f5f9",
          borderColor: "rgba(56, 189, 248, 0.3)",
          borderWidth: 1,
        },
      },
      scales: {
        x: {
          grid: { color: "rgba(51, 65, 85, 0.3)" },
          ticks: { color: "#64748b", font: { size: 9 }, maxTicksLimit: 12 },
        },
        y: {
          min: 40,
          max: 300,
          grid: { color: "rgba(51, 65, 85, 0.3)" },
          ticks: { color: "#06b6d4", font: { size: 10 } },
          title: { display: true, text: "Glucose (mg/dL)", color: "#06b6d4" },
        },
        y1: {
          position: "right",
          min: 40,
          max: 150,
          grid: { display: false },
          ticks: { color: "#f43f5e", font: { size: 10 } },
          title: { display: true, text: "HR (bpm)", color: "#f43f5e" },
        },
      },
    },
  });
}

function initForecastChart() {
  const ctx = document.getElementById("forecast-chart")?.getContext("2d");
  if (!ctx) return;

  forecastChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: [],
      datasets: [
        {
          label: "Projected Glucose Trajectory",
          data: [],
          borderColor: "#38bdf8",
          backgroundColor: "rgba(56, 189, 248, 0.2)",
          borderWidth: 2.8,
          pointRadius: 3,
          pointBackgroundColor: "#38bdf8",
          fill: false,
          tension: 0.3,
        },
        {
          label: "Upper 90% Confidence Bound",
          data: [],
          borderColor: "rgba(56, 189, 248, 0.35)",
          borderWidth: 1,
          borderDash: [4, 4],
          pointRadius: 0,
          fill: "+1",
          backgroundColor: "rgba(56, 189, 248, 0.08)",
        },
        {
          label: "Lower 90% Confidence Bound",
          data: [],
          borderColor: "rgba(56, 189, 248, 0.35)",
          borderWidth: 1,
          borderDash: [4, 4],
          pointRadius: 0,
          fill: false,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { labels: { color: "#94a3b8", font: { size: 10 } } },
      },
      scales: {
        x: {
          grid: { color: "rgba(51, 65, 85, 0.3)" },
          ticks: { color: "#64748b", font: { size: 9 } },
        },
        y: {
          min: 50,
          max: 300,
          grid: { color: "rgba(51, 65, 85, 0.3)" },
          ticks: { color: "#94a3b8", font: { size: 10 } },
          title: { display: true, text: "mg/dL", color: "#64748b" },
        },
      },
    },
  });
}

async function loadPatientRoster() {
  try {
    const res = await fetch("/api/patients");
    const patients = await res.json();

    const selector = document.getElementById("patient-select-bar");
    if (!selector) return;

    selector.innerHTML = patients
      .map((p) => {
        let badgeClass = "badge-stable";
        if (p.triage_level === "CRITICAL") badgeClass = "badge-critical";
        else if (p.triage_level === "HIGH RISK") badgeClass = "badge-high";
        else if (p.triage_level === "MODERATE") badgeClass = "badge-moderate";

        const isSelected = p.patient_id === currentPatientId;
        return `
          <button onclick="switchPatient('${p.patient_id}')" 
                  class="px-3 py-2 rounded-lg text-left transition-all border flex items-center justify-between min-w-[200px] 
                         ${isSelected ? "bg-slate-800/90 border-cyan-500 shadow-[0_0_12px_rgba(6,182,212,0.3)]" : "bg-slate-900/50 border-slate-700/60 hover:border-slate-500"}">
            <div>
              <div class="text-xs font-bold text-slate-100">${p.name}</div>
              <div class="text-[10px] text-slate-400">${p.patient_id} • HbA1c ${p.hba1c}%</div>
            </div>
            <span class="text-[10px] px-2 py-0.5 rounded-full font-semibold ${badgeClass}">
              ${p.triage_level}
            </span>
          </button>
        `;
      })
      .join("");
  } catch (err) {
    console.error("Failed to load patient roster:", err);
  }
}

async function switchPatient(patientId) {
  currentPatientId = patientId;
  await loadPatientRoster();
  await loadPatientData(patientId);
}

async function loadPatientData(patientId) {
  try {
    // 1. Fetch full EHR details
    const ehrRes = await fetch(`/api/patients/${patientId}`);
    const patient = await ehrRes.json();

    // 2. Fetch recent telemetry
    const telRes = await fetch(`/api/patients/${patientId}/telemetry?limit=96`);
    const telemetry = await telRes.json();
    const latestTel = telemetry[telemetry.length - 1];

    // 3. Run predictive assessment
    const predRes = await fetch(`/api/patients/${patientId}/predict`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ planned_carbs: 0.0 }),
    });
    const assessment = await predRes.json();

    // Update UI components
    updateEHRHeader(patient, latestTel, assessment);
    updateTelemetryChart(telemetry);
    updateForecastChart(assessment);
    updateExplainability(assessment);
    twinVisualizer.update(patient, latestTel, assessment);
    whatIfSimUI.runSimulation(patientId);
  } catch (err) {
    console.error("Error loading patient data:", err);
  }
}

function updateEHRHeader(patient, latestTel, assessment) {
  document.getElementById("p-name").innerText = patient.name;
  document.getElementById("p-demographics").innerText = `${patient.age} yrs • ${patient.gender} • ${patient.location}`;
  document.getElementById("p-hba1c").innerText = `${patient.hba1c}%`;
  document.getElementById("p-bmi").innerText = `${patient.bmi} kg/m²`;
  document.getElementById("p-t2d-duration").innerText = `${patient.duration_t2d_years} yrs`;
  document.getElementById("p-egfr").innerText = `${patient.egfr} mL/min`;
  document.getElementById("p-bp").innerText = `${patient.blood_pressure_systolic}/${patient.blood_pressure_diastolic} mmHg`;
  document.getElementById("p-lipid").innerText = `TG ${patient.lipid_panel.triglycerides} / HDL ${patient.lipid_panel.hdl}`;

  // Current Vitals
  document.getElementById("vital-cgm").innerText = `${latestTel?.glucose_cgm_mg_dl || "--"} mg/dL`;
  document.getElementById("vital-hr").innerText = `${latestTel?.heart_rate_bpm || "--"} bpm`;
  document.getElementById("vital-hrv").innerText = `${latestTel?.hrv_rmssd_ms || "--"} ms`;
  document.getElementById("vital-steps").innerText = `${latestTel?.steps || "--"}`;

  // Phenotype notes & Meds
  document.getElementById("p-phenotype").innerText = patient.phenotype_notes;
  const medsContainer = document.getElementById("p-medications");
  if (medsContainer) {
    medsContainer.innerHTML = patient.medications
      .map(
        (m) => `
        <span class="inline-flex items-center px-2 py-0.5 rounded text-[11px] bg-cyan-950/80 text-cyan-200 border border-cyan-800/80 mr-1.5 mb-1 font-mono">
          💊 ${m}
        </span>
      `
      )
      .join("");
  }

  // Triage Alert Banner
  const alertBanner = document.getElementById("triage-alert-banner");
  if (alertBanner) {
    let alertClass = "border-emerald-500/40 bg-emerald-950/30 text-emerald-300";
    if (assessment.triage_level === "CRITICAL") {
      alertClass = "border-rose-500/80 bg-rose-950/50 text-rose-200 animate-pulse";
    } else if (assessment.triage_level === "HIGH RISK") {
      alertClass = "border-amber-500/80 bg-amber-950/50 text-amber-200";
    } else if (assessment.triage_level === "MODERATE") {
      alertClass = "border-blue-500/80 bg-blue-950/50 text-blue-200";
    }

    alertBanner.className = `p-3 rounded-lg border flex items-start justify-between ${alertClass}`;
    alertBanner.innerHTML = `
      <div class="flex items-start space-x-3">
        <span class="text-xl">⚠️</span>
        <div>
          <div class="text-xs font-bold uppercase tracking-wider">${assessment.alert_title}</div>
          <div class="text-xs mt-1 opacity-90">${assessment.clinical_recommendation}</div>
        </div>
      </div>
      <div class="text-right pl-4">
        <div class="text-[10px] uppercase tracking-wide opacity-75">T+120m Projected</div>
        <div class="text-lg font-bold font-mono">${assessment.projected_glucose_120m} <span class="text-xs font-normal">mg/dL</span></div>
      </div>
    `;
  }
}

function updateTelemetryChart(telemetry) {
  if (!telemetryChart) return;

  const labels = telemetry.map((r) => {
    const d = new Date(r.timestamp);
    return `${d.getHours().toString().padStart(2, "0")}:${d.getMinutes().toString().padStart(2, "0")}`;
  });
  const cgmData = telemetry.map((r) => r.glucose_cgm_mg_dl);
  const hrData = telemetry.map((r) => r.heart_rate_bpm);

  telemetryChart.data.labels = labels;
  telemetryChart.data.datasets[0].data = cgmData;
  telemetryChart.data.datasets[1].data = hrData;
  telemetryChart.update();
}

function updateForecastChart(assessment) {
  if (!forecastChart || !assessment.trajectory_forecast) return;

  const trajectory = assessment.trajectory_forecast;
  const labels = trajectory.map((pt) => `+${pt.minute_offset}m`);
  const values = trajectory.map((pt) => pt.predicted_glucose);
  const upperBounds = trajectory.map((pt) => pt.upper_bound_90ci);
  const lowerBounds = trajectory.map((pt) => pt.lower_bound_90ci);

  forecastChart.data.labels = labels;
  forecastChart.data.datasets[0].data = values;
  forecastChart.data.datasets[1].data = upperBounds;
  forecastChart.data.datasets[2].data = lowerBounds;

  // Change line color based on severity
  if (assessment.triage_level === "CRITICAL") {
    forecastChart.data.datasets[0].borderColor = "#f43f5e";
    forecastChart.data.datasets[0].pointBackgroundColor = "#f43f5e";
  } else if (assessment.triage_level === "HIGH RISK") {
    forecastChart.data.datasets[0].borderColor = "#f59e0b";
    forecastChart.data.datasets[0].pointBackgroundColor = "#f59e0b";
  } else {
    forecastChart.data.datasets[0].borderColor = "#10b981";
    forecastChart.data.datasets[0].pointBackgroundColor = "#10b981";
  }

  forecastChart.update();

  // Update adverse event probability bars
  document.getElementById("prob-spike-val").innerText = `${assessment.spike_probability_pct}%`;
  document.getElementById("prob-spike-bar").style.width = `${assessment.spike_probability_pct}%`;

  document.getElementById("prob-hypo-val").innerText = `${assessment.hypo_probability_pct}%`;
  document.getElementById("prob-hypo-bar").style.width = `${assessment.hypo_probability_pct}%`;

  document.getElementById("cardio-strain-val").innerText = `${assessment.cardio_strain_index}/100`;
  document.getElementById("cardio-strain-bar").style.width = `${assessment.cardio_strain_index}%`;
}

function updateExplainability(assessment) {
  const container = document.getElementById("explainability-container");
  if (!container || !assessment.explainability) return;

  container.innerHTML = assessment.explainability
    .map(
      (item) => `
      <div class="mb-2">
        <div class="flex justify-between text-xs text-slate-300 mb-1">
          <span>${item.factor}</span>
          <span class="font-mono font-semibold text-cyan-400">${item.contribution_pct}%</span>
        </div>
        <div class="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
          <div class="bg-gradient-to-r from-cyan-500 to-blue-500 h-1.5 rounded-full" style="width: ${item.contribution_pct}%"></div>
        </div>
      </div>
    `
    )
    .join("");
}

// Live demonstration event injection
async function injectEvent(eventType, description, carbs = 0, steps = 0) {
  try {
    const res = await fetch(`/api/patients/${currentPatientId}/inject-event`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        event_type: eventType,
        description: description,
        carbs_g: carbs,
        steps: steps,
      }),
    });

    if (res.ok) {
      await loadPatientData(currentPatientId);
      showToast(`Simulated: ${description}`);
    }
  } catch (err) {
    console.error("Event injection error:", err);
  }
}

function showToast(msg) {
  const toast = document.createElement("div");
  toast.className = "fixed bottom-5 right-5 bg-cyan-600 text-white px-4 py-2 rounded-lg shadow-xl text-xs z-50 animate-bounce";
  toast.innerText = msg;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 2800);
}

// Clinical Report Modal
async function openClinicalReport() {
  try {
    const res = await fetch(`/api/patients/${currentPatientId}/clinical-report`);
    const report = await res.json();

    const content = document.getElementById("report-modal-body");
    content.innerHTML = `
      <div class="border-b border-slate-700 pb-3 mb-4 flex justify-between items-center">
        <div>
          <h2 class="text-base font-bold text-slate-100">AIIMS / Narayana Health Clinical Consultation Summary</h2>
          <p class="text-xs text-slate-400">Research Society for the Study of Diabetes in India (RSSDI) & ICMR Guideline Protocol</p>
        </div>
        <div class="text-right text-xs text-slate-400 font-mono">
          <div>Report: ${report.report_id}</div>
          <div>${report.generated_at}</div>
        </div>
      </div>

      <div class="grid grid-cols-2 gap-4 text-xs mb-4">
        <div class="bg-slate-900/80 p-3 rounded border border-slate-800">
          <div class="font-bold text-slate-200 mb-1">Patient Profile</div>
          <div>Name: <b class="text-slate-100">${report.patient_name}</b></div>
          <div>Age/Gender: <b class="text-slate-100">${report.age_gender}</b></div>
          <div>Baseline HbA1c: <b class="text-cyan-400">${report.hba1c}</b></div>
          <div class="mt-2 text-slate-400 italic">${report.phenotype}</div>
        </div>

        <div class="bg-slate-900/80 p-3 rounded border border-slate-800">
          <div class="font-bold text-slate-200 mb-1">Ambulatory Glucose Profile (AGP)</div>
          <div>Mean Glucose: <b class="text-slate-100">${report.ambulatory_glucose_profile_agp.mean_glucose_mg_dl} mg/dL</b></div>
          <div>Glucose Management Indicator (GMI): <b class="text-slate-100">${report.ambulatory_glucose_profile_agp.glucose_management_indicator_gmi}%</b></div>
          <div>Glycemic Variability (CV): <b class="text-amber-400">${report.ambulatory_glucose_profile_agp.glycemic_variability_cv_pct}%</b> (${report.ambulatory_glucose_profile_agp.target_cv_threshold})</div>
          <div>Time-In-Range (70-180 mg/dL): <b class="text-emerald-400">${report.ambulatory_glucose_profile_agp.time_in_range_70_180}</b></div>
        </div>
      </div>

      <div class="bg-cyan-950/30 border border-cyan-800/60 p-3 rounded mb-4 text-xs">
        <div class="font-bold text-cyan-300 mb-1">Digital Twin 2-Hour Algorithmic Forecast</div>
        <div class="grid grid-cols-3 gap-2 text-slate-300 mb-2">
          <div>T+120m Projected: <b class="text-slate-100 font-mono">${report.digital_twin_predictive_horizon.projected_glucose} mg/dL</b></div>
          <div>Spike Risk: <b class="text-amber-400">${report.digital_twin_predictive_horizon.spike_probability}</b></div>
          <div>Hypo Crash Risk: <b class="text-rose-400">${report.digital_twin_predictive_horizon.hypo_probability}</b></div>
        </div>
      </div>

      <div class="mb-4">
        <h4 class="text-xs font-bold text-slate-200 uppercase tracking-wider mb-2">Actionable Clinical Recommendations (RSSDI / ICMR)</h4>
        <ul class="space-y-1.5 text-xs text-slate-300">
          ${report.rssdi_icmr_clinical_recommendations.map((r) => `<li class="flex items-start"><span class="text-cyan-400 mr-2">▶</span>${r}</li>`).join("")}
        </ul>
      </div>
    `;

    document.getElementById("report-modal").classList.remove("hidden");
  } catch (err) {
    console.error("Report generation error:", err);
  }
}

function closeClinicalReport() {
  document.getElementById("report-modal")?.classList.add("hidden");
}
