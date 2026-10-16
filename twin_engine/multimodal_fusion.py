"""
Multimodal Data Fusion Engine
==============================
Fuses static Electronic Health Record (EHR) features with dynamic
continuous wearable IoT telemetry streams (CGM, PPG HR, HRV, Accelerometer)
to produce unified multimodal feature vectors for physiological prediction.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple


# Feature column definitions
STATIC_FEATURE_NAMES = [
    "age",
    "bmi",
    "hba1c",
    "duration_t2d",
    "egfr",
    "on_sulfonylurea",
    "on_metformin",
    "on_sglt2i",
]

DYNAMIC_FEATURE_NAMES = [
    "cgm_current",
    "cgm_roc_15m",
    "cgm_acceleration",
    "recent_carbs_g",
    "mins_post_meal",
    "steps_last_30m",
    "heart_rate_bpm",
    "hrv_rmssd_ms",
    "is_nocturnal",
]

ALL_FEATURE_NAMES = STATIC_FEATURE_NAMES + DYNAMIC_FEATURE_NAMES


class MultimodalFusionEngine:
    """Combines heterogeneous static EHR and dynamic IoT time-series streams."""

    def __init__(self):
        self.feature_names = ALL_FEATURE_NAMES

    def extract_static_features(self, patient_ehr: Dict[str, Any]) -> Dict[str, float]:
        """Extracts and normalizes clinical markers from EHR JSON."""
        meds_text = " ".join(patient_ehr.get("medications", [])).lower()
        
        return {
            "age": float(patient_ehr.get("age", 50)),
            "bmi": float(patient_ehr.get("bmi", 25.0)),
            "hba1c": float(patient_ehr.get("hba1c", 7.0)),
            "duration_t2d": float(patient_ehr.get("duration_t2d_years", 5)),
            "egfr": float(patient_ehr.get("egfr", 80.0)),
            "on_sulfonylurea": 1.0 if any(m in meds_text for m in ["glimepiride", "gliclazide"]) else 0.0,
            "on_metformin": 1.0 if "metformin" in meds_text else 0.0,
            "on_sglt2i": 1.0 if any(m in meds_text for m in ["dapagliflozin", "empagliflozin", "sglt2"]) else 0.0,
        }

    def compute_time_series_derivatives(
        self, cgm_history: List[float], dt_minutes: float = 5.0
    ) -> Tuple[float, float]:
        """
        Calculates rate of change (dG/dt) and acceleration (d^2G/dt^2)
        from recent sliding window of CGM readings.
        """
        if not cgm_history or len(cgm_history) < 2:
            return 0.0, 0.0

        if len(cgm_history) >= 4:
            # 15-minute rate of change (3 intervals of 5 min)
            roc = (cgm_history[-1] - cgm_history[-4]) / (3 * dt_minutes)
            # Acceleration over past 15 mins vs prior 15 mins
            prev_roc = (cgm_history[-4] - cgm_history[-7]) / (3 * dt_minutes) if len(cgm_history) >= 7 else 0.0
            acc = (roc - prev_roc) / (3 * dt_minutes)
        else:
            roc = (cgm_history[-1] - cgm_history[0]) / (len(cgm_history) * dt_minutes)
            acc = 0.0

        return float(roc), float(acc)

    def fuse(
        self,
        patient_ehr: Dict[str, Any],
        recent_telemetry: List[Dict[str, Any]],
        current_meal: Dict[str, Any] = None,
    ) -> np.ndarray:
        """
        Fuses static EHR and the latest dynamic telemetry buffer
        into a unified feature vector for the ML predictor.
        """
        static_feats = self.extract_static_features(patient_ehr)

        if not recent_telemetry:
            # Fallback default values
            current_cgm = float(patient_ehr.get("fasting_glucose_mg_dl", 130.0))
            cgm_roc = 0.0
            cgm_acc = 0.0
            steps_30m = 100
            hr = 75.0
            hrv = 30.0
            is_nocturnal = 0.0
        else:
            latest = recent_telemetry[-1]
            current_cgm = float(latest.get("glucose_cgm_mg_dl", 130.0))
            cgm_window = [r.get("glucose_cgm_mg_dl", 130.0) for r in recent_telemetry[-12:]]
            cgm_roc, cgm_acc = self.compute_time_series_derivatives(cgm_window)

            # Sum steps over last 6 epochs (30 mins)
            steps_window = [r.get("steps", 0) for r in recent_telemetry[-6:]]
            steps_30m = sum(steps_window)

            hr = float(latest.get("heart_rate_bpm", 74))
            hrv = float(latest.get("hrv_rmssd_ms", 30))
            
            activity = latest.get("activity_state", "sedentary")
            is_nocturnal = 1.0 if activity == "sleep" else 0.0

        # Meal ingestion parameters
        recent_carbs = 0.0
        mins_post_meal = 0.0

        if current_meal:
            recent_carbs = float(current_meal.get("carbs_g", 0.0))
            mins_post_meal = float(current_meal.get("mins_ago", 0.0))
        else:
            # Check recent telemetry buffer for meal tags
            for idx, r in enumerate(reversed(recent_telemetry[-12:])):
                if r.get("meal_event"):
                    recent_carbs = float(r["meal_event"].get("carbs_g", 0.0))
                    mins_post_meal = idx * 5.0
                    break

        dynamic_feats = {
            "cgm_current": current_cgm,
            "cgm_roc_15m": cgm_roc,
            "cgm_acceleration": cgm_acc,
            "recent_carbs_g": recent_carbs,
            "mins_post_meal": mins_post_meal,
            "steps_last_30m": float(steps_30m),
            "heart_rate_bpm": hr,
            "hrv_rmssd_ms": hrv,
            "is_nocturnal": is_nocturnal,
        }

        # Pack into ordered vector matching ALL_FEATURE_NAMES
        vector = []
        for feat in STATIC_FEATURE_NAMES:
            vector.append(static_feats[feat])
        for feat in DYNAMIC_FEATURE_NAMES:
            vector.append(dynamic_feats[feat])

        return np.array(vector, dtype=float).reshape(1, -1)
