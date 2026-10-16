/**
 * Interactive What-If Counterfactual Digital Twin Simulator
 * Handles UI interactions, API communications, and comparative chart rendering.
 */

class WhatIfSimulatorUI {
  constructor(chartCanvasId) {
    this.canvasId = chartCanvasId;
    this.chart = null;
    this.patientId = null;
    this.currentData = null;
    this.initChart();
  }

  initChart() {
    const ctx = document.getElementById(this.canvasId)?.getContext("2d");
    if (!ctx) return;

    this.chart = new Chart(ctx, {
      type: "line",
      data: {
        labels: [],
        datasets: [
          {
            label: "Baseline (Current Care Plan)",
            data: [],
            borderColor: "#f43f5e",
            backgroundColor: "rgba(244, 63, 94, 0.08)",
            borderWidth: 2.5,
            borderDash: [5, 5],
            pointRadius: 0,
            fill: false,
            tension: 0.35,
          },
          {
            label: "Counterfactual Digital Twin (With Intervention)",
            data: [],
            borderColor: "#10b981",
            backgroundColor: "rgba(16, 185, 129, 0.15)",
            borderWidth: 3,
            pointRadius: 2,
            pointBackgroundColor: "#10b981",
            fill: true,
            tension: 0.35,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            labels: { color: "#cbd5e1", font: { size: 11, family: "Inter" } },
          },
          tooltip: {
            mode: "index",
            intersect: false,
            callbacks: {
              label: function (context) {
                return `${context.dataset.label}: ${context.parsed.y} mg/dL`;
              },
            },
          },
        },
        scales: {
          x: {
            grid: { color: "rgba(51, 65, 85, 0.4)" },
            ticks: { color: "#94a3b8", font: { size: 10 } },
            title: { display: true, text: "Forward Prediction Timeline", color: "#64748b" },
          },
          y: {
            min: 50,
            max: 280,
            grid: { color: "rgba(51, 65, 85, 0.4)" },
            ticks: { color: "#94a3b8", font: { size: 10 } },
            title: { display: true, text: "Plasma Glucose (mg/dL)", color: "#64748b" },
          },
        },
      },
    });
  }

  async runSimulation(patientId) {
    this.patientId = patientId;

    const carbsVal = parseFloat(document.getElementById("slider-carbs")?.value || 75);
    const exerciseMins = parseFloat(document.getElementById("slider-exercise")?.value || 0);
    const addSglt2i = document.getElementById("toggle-sglt2i")?.checked || false;
    const reduceSu = document.getElementById("toggle-reducesu")?.checked || false;
    const incMetformin = document.getElementById("toggle-metformin")?.checked || false;

    // Convert exercise minutes to intensity (0.0 to 1.0)
    const exerciseIntensity = exerciseMins / 30.0;

    // Update slider label numbers
    document.getElementById("val-carbs").innerText = `${carbsVal} g`;
    document.getElementById("val-exercise").innerText = `${exerciseMins} mins`;

    try {
      const resp = await fetch(`/api/patients/${patientId}/what-if`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          baseline_carbs: 85.0,
          baseline_exercise: 0.0,
          intervention_carbs: carbsVal,
          intervention_exercise: exerciseIntensity,
          add_sglt2i: addSglt2i,
          reduce_su: reduceSu,
          increase_metformin: incMetformin,
        }),
      });

      if (!resp.ok) throw new Error("Simulation endpoint failed");
      const data = await resp.json();
      this.currentData = data;
      this.renderResults(data);
    } catch (err) {
      console.error("Simulation error:", err);
    }
  }

  renderResults(data) {
    if (!this.chart) return;

    const labels = data.baseline_trajectory.map((pt) => `+${pt.minute_offset}m`);
    const basePoints = data.baseline_trajectory.map((pt) => pt.predicted_glucose);
    const counterPoints = data.counterfactual_trajectory.map((pt) => pt.predicted_glucose);

    this.chart.data.labels = labels;
    this.chart.data.datasets[0].data = basePoints;
    this.chart.data.datasets[1].data = counterPoints;
    this.chart.update();

    // Update delta readout metrics
    const peakDeltaElem = document.getElementById("delta-peak-glucose");
    const tirDeltaElem = document.getElementById("delta-tir");
    const insightsElem = document.getElementById("sim-insights-list");

    if (peakDeltaElem) {
      const isNegative = data.peak_glucose_delta < 0;
      peakDeltaElem.className = isNegative ? "text-emerald-400 font-bold" : "text-amber-400 font-bold";
      peakDeltaElem.innerHTML = `
        ${data.counterfactual_peak_glucose} mg/dL 
        <span class="text-xs font-normal">(${isNegative ? "" : "+"}${data.peak_glucose_delta} mg/dL)</span>
      `;
    }

    if (tirDeltaElem) {
      tirDeltaElem.className = data.tir_delta_pct >= 0 ? "text-emerald-400 font-bold" : "text-rose-400 font-bold";
      tirDeltaElem.innerHTML = `
        ${data.counterfactual_tir_pct}% 
        <span class="text-xs font-normal">(+${data.tir_delta_pct}%)</span>
      `;
    }

    if (insightsElem && data.insights) {
      insightsElem.innerHTML = data.insights
        .map(
          (text) => `
          <li class="flex items-start text-xs text-slate-300">
            <span class="text-emerald-400 mr-2 mt-0.5">✓</span>
            <span>${text}</span>
          </li>
        `
        )
        .join("");
    }
  }
}
