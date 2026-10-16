"""
Synthetic Telemetry & Cohort Generator
======================================
Generates realistic, physiologically synchronized time-series data
mirroring consumer wearables (CGM, PPG Smartwatch, Accelerometer)
coupled with historical Electronic Health Records for Indian T2D patients.
"""

import json
import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any
from twin_engine.physiological_twin import PhysiologicalTwin


class SyntheticDataEngine:
    """Generates physiologically consistent wearable telemetry paired with EHR."""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        self.ehr_path = os.path.join(data_dir, "ehr_patients.json")
        self.patients = self._load_patients()

    def _load_patients(self) -> List[Dict[str, Any]]:
        if os.path.exists(self.ehr_path):
            with open(self.ehr_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def generate_patient_day_telemetry(
        self, patient: Dict[str, Any], start_time: datetime = None
    ) -> List[Dict[str, Any]]:
        """
        Generates 24 hours of 5-minute telemetry (288 timesteps)
        driven by the Physiological Twin ODE and wearable sensor noise.
        """
        if start_time is None:
            # Anchor to yesterday 00:00 to today 23:55
            now = datetime.now()
            start_time = datetime(now.year, now.month, now.day, 0, 0, 0) - timedelta(days=1)

        twin = PhysiologicalTwin(patient)
        patient_id = patient.get("patient_id")

        # Distinct meal schedules and behaviors based on patient clinical case
        if patient_id == "IND-T2D-001":
            # Rajesh Sharma: High carb dinner, late night spike
            meals = [
                {"hour": 8.5, "carbs": 55, "gi": 72, "desc": "Breakfast: Masala Dosa + Filter Coffee"},
                {"hour": 13.5, "carbs": 70, "gi": 75, "desc": "Lunch: Rice, Sambar, Curd, Papad"},
                {"hour": 17.5, "carbs": 25, "gi": 65, "desc": "Snack: Samosa + Chai"},
                {"hour": 21.0, "carbs": 95, "gi": 82, "desc": "Dinner: Paneer Makhani + 3 Butter Roti + Gulab Jamun"},
            ]
            exercise_events = [
                {"hour": 7.0, "duration_mins": 20, "intensity": 0.5, "steps_per_epoch": 300}
            ]
        elif patient_id == "IND-T2D-002":
            # Sunita Patel: Skipping dinner or low carb, severe nocturnal crash on Glimepiride
            meals = [
                {"hour": 9.0, "carbs": 40, "gi": 65, "desc": "Breakfast: Poha + Milk"},
                {"hour": 13.0, "carbs": 45, "gi": 60, "desc": "Lunch: 2 Phulka Roti + Dal + Bhindi"},
                {"hour": 19.5, "carbs": 15, "gi": 50, "desc": "Fast/Light Dinner: Warm milk + roasted makhana"},
            ]
            exercise_events = [
                {"hour": 6.5, "duration_mins": 30, "intensity": 0.4, "steps_per_epoch": 250}
            ]
        elif patient_id == "IND-T2D-003":
            # Amit Verma: High stress, elevated HR, high TG/HDL
            meals = [
                {"hour": 9.0, "carbs": 60, "gi": 75, "desc": "Breakfast: Aloo Paratha with Curd"},
                {"hour": 14.0, "carbs": 80, "gi": 78, "desc": "Lunch: Biryani Bowl from cafeteria"},
                {"hour": 20.5, "carbs": 65, "gi": 70, "desc": "Dinner: Rajma Chawal + Salad"},
            ]
            exercise_events = []
        else:
            # Priya Nair: Balanced moderate profile
            meals = [
                {"hour": 8.0, "carbs": 40, "gi": 55, "desc": "Breakfast: Idli (3) + Sambar"},
                {"hour": 13.0, "carbs": 50, "gi": 60, "desc": "Lunch: Red rice + Fish curry + Thoran"},
                {"hour": 20.0, "carbs": 45, "gi": 58, "desc": "Dinner: 2 Chapati + Mixed Veg"},
            ]
            exercise_events = [
                {"hour": 17.5, "duration_mins": 35, "intensity": 0.6, "steps_per_epoch": 450}
            ]

        # Initial conditions
        G = float(patient.get("fasting_glucose_mg_dl", 130.0))
        X = 0.002
        records = []

        total_epochs = 288  # 24 hours * 12 (5-min intervals)

        # Baseline vitals
        base_hr = 74 if patient["gender"] == "Male" else 76
        if patient_id == "IND-T2D-003":
            base_hr = 84  # High sympathetic stress
        base_rmssd = 35.0 - (patient["hba1c"] - 6.0) * 4.0 - (patient["age"] - 40) * 0.3
        base_rmssd = max(18.0, base_rmssd)

        for step in range(total_epochs):
            curr_time = start_time + timedelta(minutes=step * 5)
            hour_of_day = curr_time.hour + curr_time.minute / 60.0

            # 1. Check for meal absorption
            active_carbs_rate = 0.0
            meal_tag = None
            for m in meals:
                time_since_meal = (hour_of_day - m["hour"]) * 60.0
                if 0 <= time_since_meal <= 240:
                    Ra = twin.simulate_gut_absorption(m["carbs"], time_since_meal, m["gi"])
                    active_carbs_rate += Ra
                    if 0 <= time_since_meal < 5:
                        meal_tag = {
                            "description": m["desc"],
                            "carbs_g": m["carbs"],
                            "gi": m["gi"],
                        }

            # 2. Check for exercise
            exercise_intensity = 0.0
            steps = np.random.randint(5, 40)  # ambient movement
            activity_state = "sedentary"

            # Sleep window (23:00 to 06:30)
            is_sleep = hour_of_day >= 23.0 or hour_of_day < 6.5
            if is_sleep:
                steps = np.random.randint(0, 5)
                activity_state = "sleep"

            for ex in exercise_events:
                ex_start = ex["hour"]
                ex_end = ex["hour"] + (ex["duration_mins"] / 60.0)
                if ex_start <= hour_of_day < ex_end:
                    exercise_intensity = ex["intensity"]
                    steps = int(ex["steps_per_epoch"] + np.random.normal(0, 30))
                    activity_state = "active"

            # Advance physiological twin
            G, X = twin.step(
                G_current=G,
                X_current=X,
                carbs_absorbed_rate=active_carbs_rate,
                exercise_intensity=exercise_intensity,
                dt_minutes=5.0,
            )

            # Add sensor noise (interstitial lag + sensor Gaussian jitter ~ +/- 2.5 mg/dL)
            sensor_jitter = np.random.normal(0, 2.2)
            cgm_reading = max(42.0, G + sensor_jitter)

            # Wearable PPG Heart Rate & HRV correlation with metabolic stress
            # Glucose spikes or hypoglycemia both trigger catecholamine release -> higher HR, lower HRV
            metabolic_stress = 0.0
            if cgm_reading > 200.0:
                metabolic_stress = (cgm_reading - 200.0) * 0.12
            elif cgm_reading < 70.0:
                metabolic_stress = (70.0 - cgm_reading) * 0.45  # Sympathoadrenal surge

            if is_sleep:
                epoch_hr = (base_hr - 12.0) + metabolic_stress + np.random.normal(0, 1.8)
                epoch_rmssd = (base_rmssd + 10.0) - metabolic_stress * 0.8 + np.random.normal(0, 2.5)
            elif activity_state == "active":
                epoch_hr = base_hr + 45.0 * exercise_intensity + np.random.normal(0, 3.5)
                epoch_rmssd = max(10.0, base_rmssd - 15.0 + np.random.normal(0, 2.0))
            else:
                epoch_hr = base_hr + metabolic_stress + np.random.normal(0, 2.5)
                epoch_rmssd = max(12.0, base_rmssd - metabolic_stress * 0.4 + np.random.normal(0, 3.0))

            records.append({
                "patient_id": patient_id,
                "timestamp": curr_time.strftime("%Y-%m-%dT%H:%M:%S"),
                "glucose_cgm_mg_dl": round(float(cgm_reading), 1),
                "heart_rate_bpm": int(round(epoch_hr)),
                "hrv_rmssd_ms": round(float(max(8.0, epoch_rmssd)), 1),
                "steps": int(max(0, steps)),
                "activity_state": activity_state,
                "meal_event": meal_tag,
                "insulin_action_x": round(float(X * 1000), 3),
            })

        return records

    def build_synthetic_cohort_dataset(self, samples_per_patient: int = 1500) -> pd.DataFrame:
        """
        Creates a multimodal tabular dataset combining EHR static markers
        with sliding time-series windows to train the predictive ML models.
        """
        rows = []
        for patient in self.patients:
            twin = PhysiologicalTwin(patient)
            base_glucose = patient.get("fasting_glucose_mg_dl", 130.0)
            is_su = 1 if any("glimepiride" in m.lower() for m in patient.get("medications", [])) else 0

            samples_for_this = samples_per_patient // len(self.patients)
            for i in range(samples_for_this):
                # 3 archetypes: (1) Postprandial meal scenario, (2) Fasting/Nocturnal, (3) Normal baseline
                scenario_type = i % 3

                if scenario_type == 0:
                    # Postprandial high carb scenario
                    curr_g = np.random.uniform(110.0, 220.0)
                    recent_carbs = np.random.choice([45, 60, 75, 95, 110])
                    mins_post_meal = np.random.uniform(10, 45)
                    steps_last_30m = np.random.randint(20, 400)  # sedentary post-meal
                    rate_of_change = np.random.uniform(0.8, 3.2)
                    acceleration = np.random.uniform(-0.05, 0.15)
                    is_nocturnal = 0
                elif scenario_type == 1:
                    # Nocturnal / Fasting scenario (high risk for sulfonylureas)
                    curr_g = np.random.uniform(65.0, 140.0)
                    recent_carbs = 0
                    mins_post_meal = np.random.uniform(180, 480)
                    steps_last_30m = np.random.randint(0, 50)
                    rate_of_change = np.random.uniform(-1.8, 0.2)
                    acceleration = np.random.uniform(-0.08, 0.04)
                    is_nocturnal = 1
                else:
                    # Daytime ambient / exercise scenario
                    curr_g = np.random.uniform(90.0, 180.0)
                    recent_carbs = np.random.choice([0, 20, 35])
                    mins_post_meal = np.random.uniform(60, 200) if recent_carbs > 0 else 0
                    steps_last_30m = np.random.randint(300, 2500)
                    rate_of_change = np.random.uniform(-1.0, 1.2)
                    acceleration = np.random.uniform(-0.06, 0.06)
                    is_nocturnal = 0

                hr = np.random.normal(78 if is_nocturnal == 0 else 66, 10)
                hrv = max(10, np.random.normal(26 if is_nocturnal == 0 else 38, 8))

                # Run twin forward to compute true label at t+120 minutes
                forecast = twin.forecast_trajectory(
                    initial_glucose=curr_g,
                    horizon_minutes=120,
                    dt_minutes=5.0,
                    planned_carbs=recent_carbs,
                    minutes_since_meal=mins_post_meal,
                    exercise_intensity=steps_last_30m / 3500.0,
                )
                
                g_120 = forecast[-1]["predicted_glucose"]
                max_g = max(pt["predicted_glucose"] for pt in forecast)
                min_g = min(pt["predicted_glucose"] for pt in forecast)

                # Clinical adverse event definition:
                # Spike: Glucose exceeds 200 mg/dL or surges by >60 mg/dL
                spike_flag = 1 if (g_120 >= 200.0 or max_g >= 220.0) else 0
                # Hypo: Glucose crashes below 70 mg/dL (especially on sulfonylureas during sleep/fasting)
                if is_su and is_nocturnal and curr_g < 95.0:
                    min_g = min(min_g, curr_g - np.random.uniform(20, 35))
                    g_120 = min(g_120, curr_g - np.random.uniform(15, 30))
                hypo_flag = 1 if (g_120 < 70.0 or min_g < 70.0) else 0

                rows.append({
                    # Static EHR features
                    "patient_id": patient["patient_id"],
                    "age": patient["age"],
                    "bmi": patient["bmi"],
                    "hba1c": patient["hba1c"],
                    "duration_t2d": patient["duration_t2d_years"],
                    "egfr": patient["egfr"],
                    "on_sulfonylurea": is_su,
                    "on_metformin": 1 if any("metformin" in m.lower() for m in patient.get("medications", [])) else 0,
                    "on_sglt2i": 1 if any("gliflozin" in m.lower() for m in patient.get("medications", [])) else 0,
                    # Dynamic Wearable features
                    "cgm_current": curr_g,
                    "cgm_roc_15m": rate_of_change,
                    "cgm_acceleration": acceleration,
                    "recent_carbs_g": recent_carbs,
                    "mins_post_meal": mins_post_meal,
                    "steps_last_30m": steps_last_30m,
                    "heart_rate_bpm": hr,
                    "hrv_rmssd_ms": hrv,
                    "is_nocturnal": is_nocturnal,
                    # Targets for 120-minute forward horizon
                    "glucose_t120": g_120,
                    "target_hyper_spike_120": spike_flag,
                    "target_hypo_crash_120": hypo_flag,
                })

        df = pd.DataFrame(rows)
        save_path = os.path.join(self.data_dir, "synthetic_cohort.csv")
        df.to_csv(save_path, index=False)
        return df


if __name__ == "__main__":
    engine = SyntheticDataEngine()
    df = engine.build_synthetic_cohort_dataset(samples_per_patient=1200)
    print(f"Generated synthetic cohort dataset with {len(df)} records at {engine.data_dir}/synthetic_cohort.csv")
