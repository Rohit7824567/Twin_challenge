"""
1-Click Launcher for PRANA-TWIN Clinical Dashboard
===================================================
Digital Twin Challenge 2026 - Happiest Health Summit, Bengaluru

Usage:
    python run_demo.py
"""

import sys
import os
import time
import webbrowser
import uvicorn


def print_banner():
    banner = r"""
  +=============================================================================+
  |   PRANA-TWIN : Cardio-Metabolic Digital Twin for Type 2 Diabetes           |
  |   Dual Data Stream Fusion (EHR + Dynamic Wearable Telemetry)                |
  |   Happiest Health Reimagining & Reforming Healthcare in India Summit 2026   |
  +=============================================================================+
    """
    print(banner)


def check_and_initialize_assets():
    """Ensure data files and models are ready before launching server."""
    print("[*] Step 1: Checking clinical datasets and trained models...")

    cohort_file = os.path.join("data", "synthetic_cohort.csv")
    if not os.path.exists(cohort_file):
        print("  --> Generating synthetic Indian T2D cohort dataset...")
        from twin_engine.synthetic_generator import SyntheticDataEngine
        gen = SyntheticDataEngine()
        gen.build_synthetic_cohort_dataset(samples_per_patient=1200)
        print("  [OK] Synthetic cohort created successfully.")

    model_file = os.path.join("models", "twin_ml_models.pkl")
    if not os.path.exists(model_file):
        print("  --> Training Multimodal Digital Twin ML models...")
        from twin_engine.train_and_evaluate import run_evaluation
        metrics = run_evaluation()
        print(f"  [OK] Models trained! Clarke Grid Zone A+B: {metrics['clarke_error_grid_analysis']['zone_ab_total_pct']}%")
    else:
        print("  [OK] Pre-trained models and clinical cohorts verified.")


def main():
    print_banner()
    check_and_initialize_assets()

    host = "127.0.0.1"
    port = 8000
    url = f"http://{host}:{port}"

    print(f"\n[*] Step 2: Starting High-Performance Digital Twin Server at {url}")
    print("  [OK] REST API Endpoints active at /api/*")
    print("  [OK] Doctor UI Dashboard mounted at /")
    print("  [OK] Interactive Counterfactual 'What-If' Simulator ready")
    print("\nOpening web browser automatically in 2 seconds... (Press Ctrl+C to terminate)\n")

    # Open browser after a brief delay
    def open_browser():
        time.sleep(1.8)
        try:
            webbrowser.open(url)
        except Exception:
            pass

    import threading
    threading.Thread(target=open_browser, daemon=True).start()

    # Start Uvicorn ASGI server
    uvicorn.run("server.app:app", host=host, port=port, log_level="info", reload=False)


if __name__ == "__main__":
    main()
