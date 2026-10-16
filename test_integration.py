"""
Automated Integration & Clinical Validation Tests
==================================================
Tests all REST endpoints, ML inference pipelines, and What-If simulations.
"""

from fastapi.testclient import TestClient
from server.app import app

client = TestClient(app)


def test_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"
    print("[OK] Health endpoint OK")


def test_patients():
    res = client.get("/api/patients")
    assert res.status_code == 200
    patients = res.json()
    assert len(patients) == 4
    assert patients[0]["patient_id"] == "IND-T2D-001"
    print(f"[OK] Patients roster OK ({len(patients)} patients found)")


def test_telemetry():
    res = client.get("/api/patients/IND-T2D-001/telemetry?limit=48")
    assert res.status_code == 200
    tel = res.json()
    assert len(tel) == 48
    assert "glucose_cgm_mg_dl" in tel[0]
    assert "heart_rate_bpm" in tel[0]
    print(f"[OK] Wearable Telemetry stream OK ({len(tel)} 5-min epochs retrieved)")


def test_predict():
    res = client.post(
        "/api/patients/IND-T2D-001/predict",
        json={"planned_carbs": 75.0, "mins_since_meal": 15.0, "exercise_intensity": 0.0},
    )
    assert res.status_code == 200
    data = res.json()
    assert "projected_glucose_120m" in data
    assert "spike_probability_pct" in data
    assert "trajectory_forecast" in data
    assert len(data["trajectory_forecast"]) == 25  # 0 to 120m in 5m steps
    print(f"[OK] 120-min Predictive Horizon OK: Projected Glucose = {data['projected_glucose_120m']} mg/dL, Spike Risk = {data['spike_probability_pct']}%")


def test_what_if():
    res = client.post(
        "/api/patients/IND-T2D-001/what-if",
        json={
            "baseline_carbs": 85.0,
            "baseline_exercise": 0.0,
            "intervention_carbs": 40.0,
            "intervention_exercise": 0.6,
            "add_sglt2i": True,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert "counterfactual_peak_glucose" in data
    assert "peak_glucose_delta" in data
    assert data["peak_glucose_delta"] < 0  # Intervention should reduce glucose peak
    print(f"[OK] Counterfactual What-If Simulation OK: Peak delta = {data['peak_glucose_delta']} mg/dL")


def test_clinical_report():
    res = client.get("/api/patients/IND-T2D-001/clinical-report")
    assert res.status_code == 200
    data = res.json()
    assert "ambulatory_glucose_profile_agp" in data
    assert "rssdi_icmr_clinical_recommendations" in data
    print("[OK] RSSDI / ICMR Clinical Decision Support Report OK")


def test_index_html():
    res = client.get("/")
    assert res.status_code == 200
    assert "PRANA-TWIN" in res.text
    print("[OK] Web Dashboard UI Index OK")


if __name__ == "__main__":
    print("\nRunning End-to-End Clinical Digital Twin Integration Tests...\n")
    test_health()
    test_patients()
    test_telemetry()
    test_predict()
    test_what_if()
    test_clinical_report()
    test_index_html()
    print("\n" + "=" * 60)
    print("ALL 7 INTEGRATION TESTS PASSED WITH 100% SUCCESS!")
    print("=" * 60 + "\n")
