"""
Counterfactual "What-If" Digital Twin Simulator
================================================
Enables clinicians to test clinical and lifestyle interventions on the
virtual patient replica BEFORE executing them in real life.

Supported Interventions:
1. Dietary Modification: Carb reduction (millets/high-fiber substitutions)
2. Physical Activity: Postprandial brisk walking (GLUT4 activation)
3. Pharmacotherapy: SGLT2i addition, Metformin dose escalation, Sulfonylurea de-escalation
"""

from typing import Dict, Any, List
from twin_engine.physiological_twin import PhysiologicalTwin


class WhatIfSimulator:
    """Simulates counterfactual clinical scenarios on the patient's digital twin."""

    def __init__(self):
        pass

    def simulate(
        self,
        patient_ehr: Dict[str, Any],
        current_glucose: float,
        # Baseline context
        baseline_carbs: float = 75.0,
        baseline_exercise: float = 0.0,
        baseline_meds: List[str] = None,
        # Counterfactual intervention parameters
        intervention_carbs: float = None,
        intervention_exercise: float = None,  # 0.0 to 1.0 (e.g. 0.6 = 20 min brisk walk)
        add_sglt2i: bool = False,
        reduce_su: bool = False,
        increase_metformin: bool = False,
        horizon_minutes: int = 120,
    ) -> Dict[str, Any]:
        """
        Runs dual simulations: Baseline vs Counterfactual Twin.
        Returns both trajectories and clinical delta metrics.
        """
        if baseline_meds is None:
            baseline_meds = patient_ehr.get("medications", [])

        # 1. Baseline Digital Twin Simulation
        baseline_twin = PhysiologicalTwin(patient_ehr)
        base_trajectory = baseline_twin.forecast_trajectory(
            initial_glucose=current_glucose,
            horizon_minutes=horizon_minutes,
            dt_minutes=5.0,
            planned_carbs=baseline_carbs,
            minutes_since_meal=10.0,
            exercise_intensity=baseline_exercise,
        )

        # 2. Configure Counterfactual Twin with Modified Parameters
        counter_ehr = dict(patient_ehr)
        counter_meds = list(baseline_meds)

        if add_sglt2i and not any("gliflozin" in m.lower() for m in counter_meds):
            counter_meds.append("Dapagliflozin 10mg OD (Simulated)")
        if reduce_su:
            counter_meds = [m for m in counter_meds if "glimepiride" not in m.lower() and "gliclazide" not in m.lower()]
            counter_meds.append("Glimepiride 1mg OD (De-escalated)")
        if increase_metformin and not any("1000mg" in m for m in counter_meds):
            counter_meds.append("Metformin 1000mg BD (Optimized)")

        counter_ehr["medications"] = counter_meds
        counter_twin = PhysiologicalTwin(counter_ehr)

        target_carbs = baseline_carbs if intervention_carbs is None else intervention_carbs
        target_exercise = baseline_exercise if intervention_exercise is None else intervention_exercise

        counter_trajectory = counter_twin.forecast_trajectory(
            initial_glucose=current_glucose,
            horizon_minutes=horizon_minutes,
            dt_minutes=5.0,
            planned_carbs=target_carbs,
            minutes_since_meal=10.0,
            exercise_intensity=target_exercise,
        )

        # 3. Calculate Clinical Comparative Metrics
        base_peak = max(pt["predicted_glucose"] for pt in base_trajectory)
        counter_peak = max(pt["predicted_glucose"] for pt in counter_trajectory)
        peak_delta = round(counter_peak - base_peak, 1)

        base_min = min(pt["predicted_glucose"] for pt in base_trajectory)
        counter_min = min(pt["predicted_glucose"] for pt in counter_trajectory)
        min_delta = round(counter_min - base_min, 1)

        # Time-in-Range (70-180 mg/dL) percentage
        base_tir_pts = sum(1 for pt in base_trajectory if 70.0 <= pt["predicted_glucose"] <= 180.0)
        base_tir = round((base_tir_pts / len(base_trajectory)) * 100, 1)

        counter_tir_pts = sum(1 for pt in counter_trajectory if 70.0 <= pt["predicted_glucose"] <= 180.0)
        counter_tir = round((counter_tir_pts / len(counter_trajectory)) * 100, 1)
        tir_delta = round(counter_tir - base_tir, 1)

        # 4. Generate Clinical Insights Summary
        insights = []
        if peak_delta <= -20.0:
            insights.append(
                f"Peak postprandial glucose reduced by {abs(peak_delta)} mg/dL ({base_peak} -> {counter_peak} mg/dL). "
                "Mitigates acute endothelial oxidative stress and glycemic variability."
            )
        if tir_delta > 0:
            insights.append(
                f"Time-in-Range (TIR 70-180 mg/dL) improves by +{tir_delta}%, reaching {counter_tir}%."
            )
        if base_min < 70.0 and counter_min >= 70.0:
            insights.append(
                "Successfully averts nocturnal hypoglycemic crash. Lowest projected nadir stabilized at "
                f"{counter_min} mg/dL."
            )

        if not insights:
            insights.append("Slight physiological modulation observed within acceptable homeostatic tolerances.")

        return {
            "patient_id": patient_ehr.get("patient_id"),
            "baseline_peak_glucose": base_peak,
            "counterfactual_peak_glucose": counter_peak,
            "peak_glucose_delta": peak_delta,
            "baseline_tir_pct": base_tir,
            "counterfactual_tir_pct": counter_tir,
            "tir_delta_pct": tir_delta,
            "insights": insights,
            "baseline_trajectory": base_trajectory,
            "counterfactual_trajectory": counter_trajectory,
        }
