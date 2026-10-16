"""
FastAPI Server for Healthcare Digital Twin
===========================================
Serves REST APIs for:
- Patient EHR Management & Triage Status
- Wearable IoT Telemetry Ingestion & Streaming
- 120-Minute Forward Prediction & Adverse Event Detection
- Counterfactual "What-If" Simulation Engine
- RSSDI / ICMR Clinical Decision Support & Audit Reports
- Live Event Injection for Demonstrations
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from twin_engine.synthetic_generator import SyntheticDataEngine
from twin_engine.predictor import TwinPredictor
from twin_engine.what_if_simulator import WhatIfSimulator


# Initialize FastAPI app
app = FastAPI(
    title="Cardio-Metabolic Digital Twin Engine (India Summit 2026)",
    description="Multimodal Digital Twin predicting 2-hour adverse glucose events and simulating clinical interventions.",
    version="1.0.0",
)

# CORS middleware for development flexibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Base directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
UI_DIR = os.path.join(BASE_DIR, "ui")

# In-memory storage and engine instances
data_engine = SyntheticDataEngine(data_dir=DATA_DIR)
predictor = TwinPredictor(models_dir=os.path.join(BASE_DIR, "models"), data_dir=DATA_DIR)
what_if_sim = WhatIfSimulator()

# Cache generated 24h telemetry per patient
PATIENT_TELEMETRY_CACHE: Dict[str, List[Dict[str, Any]]] = {}


def get_patient_ehr(patient_id: str) -> Dict[str, Any]:
    """Retrieve patient EHR profile by ID."""
    for p in data_engine.patients:
        if p.get("patient_id") == patient_id:
            return p
    raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found in EHR database")


def get_or_create_telemetry(patient_id: str) -> List[Dict[str, Any]]:
    """Retrieve or generate 24h dynamic telemetry buffer."""
    if patient_id not in PATIENT_TELEMETRY_CACHE:
        patient = get_patient_ehr(patient_id)
        telemetry = data_engine.generate_patient_day_telemetry(patient)
        PATIENT_TELEMETRY_CACHE[patient_id] = telemetry
    return PATIENT_TELEMETRY_CACHE[patient_id]


# Pydantic schemas for requests
class PredictRequest(BaseModel):
    planned_carbs: float = 0.0
    mins_since_meal: float = 0.0
    exercise_intensity: float = 0.0
    custom_cgm_override: Optional[float] = None


class WhatIfRequest(BaseModel):
    baseline_carbs: float = 75.0
    baseline_exercise: float = 0.0
    intervention_carbs: Optional[float] = None
    intervention_exercise: Optional[float] = None
    add_sglt2i: bool = False
    reduce_su: bool = False
    increase_metformin: bool = False


class InjectEventRequest(BaseModel):
    event_type: str  # "high_carb_meal", "fasting_skip_meal", "exercise_walk", "stress_spike"
    description: str
    carbs_g: Optional[float] = 0.0
    steps: Optional[int] = 0


# API Endpoints
@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Cardio-Metabolic Digital Twin Engine",
        "summit": "Happiest Health Reimagining & Reforming Healthcare in India Summit 2026",
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/api/patients")
def list_patients():
    """Returns roster of patients with clinical triage badges."""
    roster = []
    for p in data_engine.patients:
        telemetry = get_or_create_telemetry(p["patient_id"])
        latest = telemetry[-1] if telemetry else {}
        assessment = predictor.predict_full_assessment(
            patient_ehr=p,
            recent_telemetry=telemetry[-24:],
        )
        roster.append({
            "patient_id": p["patient_id"],
            "name": p["name"],
            "age": p["age"],
            "gender": p["gender"],
            "location": p["location"],
            "hba1c": p["hba1c"],
            "latest_cgm": latest.get("glucose_cgm_mg_dl"),
            "latest_hr": latest.get("heart_rate_bpm"),
            "latest_hrv": latest.get("hrv_rmssd_ms"),
            "triage_level": assessment["triage_level"],
            "alert_title": assessment["alert_title"],
            "primary_risk": p["risk_profile"]["primary_risk"],
            "projected_glucose_120m": assessment["projected_glucose_120m"],
            "spike_probability_pct": assessment["spike_probability_pct"],
            "hypo_probability_pct": assessment["hypo_probability_pct"],
        })
    return roster


@app.get("/api/patients/{patient_id}")
def get_patient_details(patient_id: str):
    """Returns full EHR record and baseline organ twin parameters."""
    patient = get_patient_ehr(patient_id)
    return patient


@app.get("/api/patients/{patient_id}/telemetry")
def get_patient_telemetry(patient_id: str, limit: int = Query(288, ge=12, le=500)):
    """Returns dynamic time-series wearable telemetry buffer."""
    telemetry = get_or_create_telemetry(patient_id)
    return telemetry[-limit:]


@app.post("/api/patients/{patient_id}/predict")
def run_prediction(patient_id: str, req: PredictRequest):
    """Runs 120-minute forward trajectory and adverse event prediction."""
    patient = get_patient_ehr(patient_id)
    telemetry = get_or_create_telemetry(patient_id)

    # Optional override for real-time testing
    buffer = list(telemetry)
    if req.custom_cgm_override is not None and buffer:
        last_item = dict(buffer[-1])
        last_item["glucose_cgm_mg_dl"] = req.custom_cgm_override
        buffer[-1] = last_item

    assessment = predictor.predict_full_assessment(
        patient_ehr=patient,
        recent_telemetry=buffer[-24:],
        planned_carbs=req.planned_carbs,
        mins_since_meal=req.mins_since_meal,
        exercise_intensity=req.exercise_intensity,
    )
    return assessment


@app.post("/api/patients/{patient_id}/what-if")
def run_what_if_simulation(patient_id: str, req: WhatIfRequest):
    """Simulates counterfactual clinical or lifestyle interventions on the digital twin."""
    patient = get_patient_ehr(patient_id)
    telemetry = get_or_create_telemetry(patient_id)
    current_glucose = telemetry[-1]["glucose_cgm_mg_dl"] if telemetry else patient.get("fasting_glucose_mg_dl", 130.0)

    result = what_if_sim.simulate(
        patient_ehr=patient,
        current_glucose=current_glucose,
        baseline_carbs=req.baseline_carbs,
        baseline_exercise=req.baseline_exercise,
        intervention_carbs=req.intervention_carbs,
        intervention_exercise=req.intervention_exercise,
        add_sglt2i=req.add_sglt2i,
        reduce_su=req.reduce_su,
        increase_metformin=req.increase_metformin,
        horizon_minutes=120,
    )
    return result


@app.post("/api/patients/{patient_id}/inject-event")
def inject_telemetry_event(patient_id: str, req: InjectEventRequest):
    """
    Injects a live physiological perturbation into the patient's twin stream
    for interactive doctor demonstration.
    """
    patient = get_patient_ehr(patient_id)
    telemetry = get_or_create_telemetry(patient_id)
    last_record = telemetry[-1]

    # Generate new timestamp +5 mins
    last_dt = datetime.fromisoformat(last_record["timestamp"])
    new_dt = last_dt + (datetime.now() - datetime.now())  # keeps format

    new_glucose = last_record["glucose_cgm_mg_dl"]
    new_hr = last_record["heart_rate_bpm"]
    new_hrv = last_record["hrv_rmssd_ms"]
    new_steps = last_record["steps"]
    meal_tag = None

    if req.event_type == "high_carb_meal":
        meal_tag = {
            "description": req.description,
            "carbs_g": req.carbs_g or 85,
            "gi": 80,
        }
        new_glucose += 25.0
        new_hr += 8
    elif req.event_type == "fasting_skip_meal":
        new_glucose = max(55.0, new_glucose - 35.0)
        new_hr += 12  # autonomic response
        new_hrv = max(12.0, new_hrv - 8.0)
    elif req.event_type == "exercise_walk":
        new_steps = req.steps or 1800
        new_glucose = max(80.0, new_glucose - 20.0)
        new_hr = 115
        new_hrv = 18.0
    elif req.event_type == "stress_spike":
        new_hr += 22
        new_hrv = max(10.0, new_hrv - 14.0)
        new_glucose += 18.0

    new_record = {
        "patient_id": patient_id,
        "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "glucose_cgm_mg_dl": round(new_glucose, 1),
        "heart_rate_bpm": int(new_hr),
        "hrv_rmssd_ms": round(new_hrv, 1),
        "steps": int(new_steps),
        "activity_state": "active" if req.event_type == "exercise_walk" else "sedentary",
        "meal_event": meal_tag,
        "insulin_action_x": last_record.get("insulin_action_x", 0.002),
    }

    telemetry.append(new_record)
    return {
        "success": True,
        "injected_event": req.description,
        "latest_telemetry": new_record,
    }


@app.get("/api/patients/{patient_id}/clinical-report")
def generate_clinical_report(patient_id: str):
    """
    Generates a structured clinical consultation note adhering to
    RSSDI (Research Society for the Study of Diabetes in India)
    and ICMR guidelines for T2D management.
    """
    patient = get_patient_ehr(patient_id)
    telemetry = get_or_create_telemetry(patient_id)
    assessment = predictor.predict_full_assessment(patient, telemetry[-24:])

    cgm_values = [r["glucose_cgm_mg_dl"] for r in telemetry]
    mean_glucose = sum(cgm_values) / len(cgm_values)
    tir_count = sum(1 for g in cgm_values if 70 <= g <= 180)
    tar_count = sum(1 for g in cgm_values if g > 180)
    tbr_count = sum(1 for g in cgm_values if g < 70)
    tir_pct = round((tir_count / len(cgm_values)) * 100, 1)
    tar_pct = round((tar_count / len(cgm_values)) * 100, 1)
    tbr_pct = round((tbr_count / len(cgm_values)) * 100, 1)

    # Glycemic Variability (CV = SD / Mean * 100)
    std_glucose = (sum((g - mean_glucose) ** 2 for g in cgm_values) / len(cgm_values)) ** 0.5
    cv_pct = round((std_glucose / mean_glucose) * 100, 1)

    report = {
        "report_id": f"REP-DT-{patient_id}-{datetime.now().strftime('%Y%m%d%H%M')}",
        "patient_name": patient["name"],
        "age_gender": f"{patient['age']}Y / {patient['gender']}",
        "hba1c": f"{patient['hba1c']}%",
        "phenotype": patient["phenotype_notes"],
        "ambulatory_glucose_profile_agp": {
            "mean_glucose_mg_dl": round(mean_glucose, 1),
            "glucose_management_indicator_gmi": round(3.31 + 0.02392 * mean_glucose, 1),
            "glycemic_variability_cv_pct": cv_pct,
            "target_cv_threshold": "< 36% (RSSDI Standard)",
            "time_in_range_70_180": f"{tir_pct}% (Goal > 70%)",
            "time_above_range_gt_180": f"{tar_pct}% (Goal < 25%)",
            "time_below_range_lt_70": f"{tbr_pct}% (Goal < 4%)",
        },
        "digital_twin_predictive_horizon": {
            "horizon": "2 Hours (120 min)",
            "projected_glucose": assessment["projected_glucose_120m"],
            "triage_urgency": assessment["triage_level"],
            "spike_probability": f"{assessment['spike_probability_pct']}%",
            "hypo_probability": f"{assessment['hypo_probability_pct']}%",
            "cardio_autonomic_strain": f"{assessment['cardio_strain_index']}/100",
        },
        "rssdi_icmr_clinical_recommendations": [
            assessment["clinical_recommendation"],
            "Encourage replacement of high-GI refined grains with regional whole millets (Ragi, Jowar, Bajra).",
            "Target postprandial physical activity: 10-15 minute walk within 30 minutes of principal meal.",
            "Review sulfonylurea dosage if Time-Below-Range exceeds 4% to prevent neuroglycopenic nocturnal events.",
        ],
        "generated_at": datetime.now().strftime("%d %B %Y, %I:%M %p IST"),
    }
    return report


# Serve UI static files
if os.path.exists(UI_DIR):
    app.mount("/static", StaticFiles(directory=UI_DIR), name="static")

@app.get("/")
def serve_index():
    index_file = os.path.join(UI_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "Digital Twin Engine active. UI directory not yet initialized."}
