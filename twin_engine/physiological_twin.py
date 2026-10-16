"""
Physiological Digital Twin Engine
===================================
Implementation of a compartmental physiological model based on the
Bergman Minimal Model and Hovorka dynamics, specifically calibrated
for the Asian-Indian Type 2 Diabetes Phenotype.

Characteristics of Asian-Indian T2D Phenotype:
- High insulin resistance at lower BMI ("thin-fat" phenotype)
- Accelerated beta-cell exhaustion
- Exaggerated postprandial glucose excursions due to high-carbohydrate diet
- Elevated hepatic glucose output (EGP)
"""

import numpy as np
from typing import Dict, Any, List, Tuple


class PhysiologicalTwin:
    """
    Virtual physiological replica of a patient's metabolic compartment.
    Simulates:
    1. Plasma Glucose Concentration: G(t) [mg/dL]
    2. Remote Insulin Action: X(t) [min^-1]
    3. Gut Glucose Absorption: Ra(t) [mg/dL/min]
    4. Endogenous Glucose Production: EGP(t) [mg/dL/min]
    5. Renal Glucose Clearance: R_clear(t) [mg/dL/min]
    """

    def __init__(self, patient_profile: Dict[str, Any]):
        """
        Calibrate physiological parameters based on patient EHR.
        """
        self.profile = patient_profile
        self.patient_id = patient_profile.get("patient_id", "P-UNKNOWN")
        self.name = patient_profile.get("name", "Unknown")
        self.age = patient_profile.get("age", 50)
        self.bmi = patient_profile.get("bmi", 26.5)
        self.hba1c = patient_profile.get("hba1c", 7.8)
        self.duration_t2d_years = patient_profile.get("duration_t2d_years", 6)
        self.egfr = patient_profile.get("egfr", 85.0)  # Kidney function
        self.medications = patient_profile.get("medications", [])

        # Calibrate physiological constants to patient phenotype
        self._calibrate_parameters()

    def _calibrate_parameters(self):
        """
        Calibrate patient-specific differential equation parameters.
        Adjusts for insulin sensitivity, beta-cell reserve, and medication effects.
        """
        # Baseline glucose (fasting setpoint in mg/dL)
        # Elevated with higher HbA1c and disease duration
        self.Gb = 100.0 + (self.hba1c - 5.5) * 18.0

        # Insulin sensitivity index S_I (min^-1 / (uU/mL))
        # Indian phenotype: higher visceral fat reduces S_I
        bmi_factor = max(0.4, 1.0 - (self.bmi - 23.0) * 0.04)
        hba1c_factor = max(0.35, 1.0 - (self.hba1c - 6.0) * 0.10)
        
        # In T2D, glucose effectiveness p1 is impaired (0.008 - 0.014 min^-1)
        self.p1 = 0.010 * hba1c_factor
        self.p2 = 0.014  # Insulin clearance rate
        self.p3 = 0.0000045 * bmi_factor * hba1c_factor  # Impaired beta-cell gain in T2D

        # Endogenous Hepatic Glucose Production basal rate
        self.EGP_basal = 1.2 + (self.hba1c - 6.0) * 0.20

        # Renal glucose threshold (default ~180 mg/dL in healthy, ~200 mg/dL in chronic T2D)
        self.renal_threshold = 195.0
        self.renal_clearance_rate = 0.012 * min(1.0, self.egfr / 90.0)

        # Apply Pharmacodynamic adjustments based on EHR medications
        self._apply_medication_pharmacodynamics()

    def _apply_medication_pharmacodynamics(self):
        """Modulate physiological ODE parameters based on active prescriptions."""
        meds_lower = [m.lower() for m in self.medications]

        # Metformin: Decreases hepatic gluconeogenesis (EGP) by ~25-35%
        if any("metformin" in m for m in meds_lower):
            self.EGP_basal *= 0.72

        # SGLT2 Inhibitor (Dapagliflozin/Empagliflozin): Lowers renal threshold to ~120 mg/dL
        if any(sglt in " ".join(meds_lower) for sglt in ["dapagliflozin", "empagliflozin", "sglt2"]):
            self.renal_threshold = 125.0
            self.renal_clearance_rate = 0.035 * min(1.0, self.egfr / 90.0)

        # Sulfonylurea (Glimepiride/Gliclazide): Increases basal insulin secretion
        if any(su in " ".join(meds_lower) for su in ["glimepiride", "gliclazide", "sulfonylurea"]):
            self.p3 *= 1.35  # Higher active insulin response

        # DPP-4i (Teneligliptin/Sitagliptin/Vildagliptin): Increases postprandial incretin response
        if any(dpp in " ".join(meds_lower) for dpp in ["teneligliptin", "sitagliptin", "vildagliptin", "dpp4"]):
            self.p3 *= 1.20

    def step(
        self,
        G_current: float,
        X_current: float,
        carbs_absorbed_rate: float,
        exercise_intensity: float = 0.0,
        dt_minutes: float = 5.0,
    ) -> Tuple[float, float]:
        """
        Advance the physiological differential equations by dt_minutes.
        
        dG/dt = -p1*(G - Gb) - X*G + Ra - R_clear - Exercise_Disposal
        dX/dt = -p2*X + p3*Insulin_Stimulus
        """
        # 1. Renal glucose excretion if above threshold
        renal_loss = 0.0
        if G_current > self.renal_threshold:
            renal_loss = self.renal_clearance_rate * (G_current - self.renal_threshold)

        # 2. Exercise-induced non-insulin dependent glucose disposal (GLUT4 translocation via AMPK)
        # 1.0 intensity = brisk walking / 120 steps/min
        exercise_disposal = 0.85 * exercise_intensity * (G_current / 100.0)

        # 3. Glucose derivative dG/dt
        dG_dt = (
            -self.p1 * (G_current - self.Gb)
            - (X_current * G_current)
            + carbs_absorbed_rate
            - renal_loss
            - exercise_disposal
        )

        # 4. Insulin action derivative dX/dt
        # Pancreatic beta cells respond to hyperglycemia: [G - Gb]^+
        beta_cell_stimulus = max(0.0, G_current - self.Gb)
        dX_dt = -self.p2 * X_current + self.p3 * beta_cell_stimulus

        # Euler step
        G_next = max(40.0, G_current + dG_dt * dt_minutes)
        X_next = max(0.0, X_current + dX_dt * dt_minutes)

        return G_next, X_next

    def simulate_gut_absorption(
        self, carbs_grams: float, time_elapsed_mins: float, glycemic_index: float = 70.0
    ) -> float:
        """
        Calculate instantaneous glucose appearance rate Ra(t) from meal ingestion.
        Uses a dual-gamma / log-normal gut absorption curve.
        
        Indian diets (white rice, maida, parathas) have high GI (>75), causing rapid peaks.
        Millet/high-fiber diets have lower GI (<55) with protracted, flatter absorption.
        """
        if carbs_grams <= 0 or time_elapsed_mins < 0:
            return 0.0

        # Time to peak absorption T_max (mins)
        # High GI foods peak at 40-50 mins; low GI at 75-90 mins
        t_peak = 40.0 + (100.0 - glycemic_index) * 0.75
        
        # Shape parameter k
        k = 1.0 / t_peak
        
        # Total bioavailable glucose in mg (1g carb ~ 1000mg, bioavailable fraction ~ 0.85)
        # Distributed into extracellular volume Vd ~ 12 Liters (120 dL)
        Vd = 120.0  # dL
        total_mg_per_dl = (carbs_grams * 1000.0 * 0.82) / Vd

        # Instantaneous rate Ra(t)
        # Curve: Ra(t) = total * k^2 * t * exp(-k*t)
        Ra = total_mg_per_dl * (k**2) * time_elapsed_mins * np.exp(-k * time_elapsed_mins)
        return float(Ra)

    def forecast_trajectory(
        self,
        initial_glucose: float,
        horizon_minutes: int = 120,
        dt_minutes: float = 5.0,
        planned_carbs: float = 0.0,
        minutes_since_meal: float = 0.0,
        glycemic_index: float = 70.0,
        exercise_intensity: float = 0.0,
    ) -> List[Dict[str, Any]]:
        """
        Generate forward simulation trajectory for 120 minutes.
        Returns timestamped glucose, insulin action, and risk flags.
        """
        steps = int(horizon_minutes / dt_minutes)
        trajectory = []

        G = initial_glucose
        # Initialize insulin action proportional to recent glucose elevation
        X = max(0.0, (initial_glucose - self.Gb) * self.p3 * 8.0)

        for step_idx in range(steps + 1):
            t_min = step_idx * dt_minutes
            
            # Record current state
            trajectory.append({
                "minute_offset": int(t_min),
                "predicted_glucose": round(float(G), 1),
                "insulin_action": round(float(X * 1000), 3),
                "is_hyperglycemic_spike": bool(G >= 200.0),
                "is_severe_hyper": bool(G >= 240.0),
                "is_hypoglycemic": bool(G < 70.0),
                "is_severe_hypo": bool(G < 54.0),
            })

            # Calculate meal absorption for next step
            total_elapsed = minutes_since_meal + t_min
            Ra = self.simulate_gut_absorption(planned_carbs, total_elapsed, glycemic_index)

            # Step forward
            G, X = self.step(
                G_current=G,
                X_current=X,
                carbs_absorbed_rate=Ra,
                exercise_intensity=exercise_intensity,
                dt_minutes=dt_minutes,
            )

        return trajectory
