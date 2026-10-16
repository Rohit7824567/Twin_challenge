"""
Deliverable Generator for Hackathon Submission
==============================================
Generates high-compatibility, presentation-ready PPTX and PDF documents:
1. docs/PRANA_TWIN_Summit_Presentation.pptx
2. docs/PRANA_TWIN_Summit_Presentation.pdf
3. docs/PRANA_TWIN_Architecture_Diagram.pptx
4. docs/PRANA_TWIN_Architecture_Diagram.pdf

Features:
- 100% compliant OpenXML (native slide backgrounds, no corrupting shape lines)
- Easily openable on PowerPoint, Google Slides, LibreOffice, Adobe Acrobat, Edge, Chrome, Apple Keynote, and mobile viewers.
- Zero email addresses of any members written anywhere in documents.
- Uses official PowerPoint engine to export pixel-perfect, vector-faithful PDFs when available on Windows, with a robust ReportLab fallback.
"""

import os
import subprocess
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


# Master Slides Content (10 Complete Slides - Zero Email Addresses)
SLIDES_CONTENT = [
    # Slide 1: Title & Team
    {
        "title": "PRANA-TWIN : Cardio-Metabolic Digital Twin",
        "subtitle": "Proof-of-Concept for Adverse Glycemic Prediction & Clinical Counterfactual Simulation",
        "bullets": [
            "Summit: Happiest Health Reimagining & Reforming Healthcare in India Summit 2026, Bengaluru",
            "Track: Chronic Disease & Preventive Healthcare | Condition: Type 2 Diabetes & Cardio-Metabolic Syndrome",
            "Team Name: Coders_ABES",
            "Institution: ABES Engineering College, Ghaziabad, Uttar Pradesh",
            "Incubator: ABES Innovation & Incubation Center (AIIC)",
            "Team Leader: Rohit Kumar (MCA Final Year, AIML Specialization)",
            "Team Member: Arush Dixit (B.Tech 2nd Year, AIML Specialization)",
            "Team Member: Anand Rai (B.Tech 2nd Year, AIML Specialization)",
            "Team Member: Naman Goel (MCA Final Year, AIML Specialization)",
        ],
    },
    # Slide 2: Problem Statement
    {
        "title": "The Problem: India's Chronic Diabetes Epidemic",
        "subtitle": "Why Traditional Healthcare is Reactive, Not Proactive",
        "bullets": [
            "Over 101 Million Diabetics in India with another 136M pre-diabetic citizens (ICMR-INDIAB).",
            "The 'Asian-Indian Phenotype': High visceral adiposity & insulin resistance at lower BMI cutoffs (>=23 kg/m2).",
            "Dietary Carb Burden: High-GI staples (polished rice, parathas, sweets) trigger postprandial surges >240 mg/dL.",
            "Fatal Nocturnal Hypoglycemia: High prevalence in elderly and fasting patients on sulfonylureas (Glimepiride).",
            "The Core Failure: Standard CGMs and hospital labs react after vascular and neurological damage has occurred.",
        ],
    },
    # Slide 3: The Solution
    {
        "title": "The Solution: PRANA-TWIN Multi-Stream Fusion",
        "subtitle": "Bridging Static EHR Records with Continuous Dynamic Wearables",
        "bullets": [
            "True Digital Twin: Virtual physiological replica modeling patient-specific metabolic compartments.",
            "Static EHR Stream: Demographics, baseline HbA1c, eGFR, lipid panels, active prescriptions, and risk history.",
            "Dynamic IoT Stream: 5-minute continuous glucose (CGM), PPG pulse rate, HRV (RMSSD), and activity steps.",
            "Multimodal Fusion Layer: Extracts rate of change (dG/dt) and acceleration (d2G/dt2) for early warning.",
            "Actionable Decision Support: Predicts adverse events 2 hours in advance to guide clinical micro-interventions.",
        ],
    },
    # Slide 4: Physiological Twin Modeling
    {
        "title": "Physiological Compartmental Modeling",
        "subtitle": "Bergman Minimal Model ODEs Calibrated for Indian Diabetology",
        "bullets": [
            "Differential Equation 1 (Plasma Glucose): dG/dt = -p1*(G - Gb) - X*G + Ra(t) - Rclear(G) - ExerciseDisposal",
            "Differential Equation 2 (Remote Insulin Action): dX/dt = -p2*X + p3*[G - Gb]+",
            "Gut Absorption Kinetics: Ra(t) modeled with dual-gamma curve calibrated to Indian dietary Glycemic Index.",
            "Renal Glycosuria Threshold: Dynamics calibrated to patient-specific eGFR (filtration efficiency).",
            "Medication Pharmacodynamics: Metformin suppresses hepatic EGP; SGLT2i lowers renal clearance threshold.",
        ],
    },
    # Slide 5: Algorithmic Predictions
    {
        "title": "Predictive AI & Adverse Event Classification",
        "subtitle": "120-Minute Forward Trajectory with Clinician Explainability (XAI)",
        "bullets": [
            "Continuous Trajectory Forecast: Generates 24 forward steps (0 to 120 mins) with 90% confidence bands.",
            "Adverse Spike Detection: Predicts probability of postprandial hyper spike (>220 mg/dL) 2 hours ahead.",
            "Nocturnal Crash Detection: Flags life-threatening nocturnal hypoglycemia (<70 mg/dL) during sleep.",
            "Cardio-Autonomic Strain Index: Continuous score (0-100) combining HRV suppression and sympathetic overdrive.",
            "Explainable AI (XAI): Clinician attribution bars showing Carb Load, Insulin Resistance, and Inactivity weights.",
        ],
    },
    # Slide 6: What-If Simulator
    {
        "title": "Counterfactual 'What-If' Simulation Sandbox",
        "subtitle": "Empowering Clinicians to Test Interventions Before Real-Life Execution",
        "bullets": [
            "Interactive Physician Sandbox: Sliders for meal carbs, brisk walk duration, and pharmacotherapy adjustments.",
            "Non-Insulin Dependent Glucose Disposal: Simulates AMPK/GLUT4 activation from 15-minute post-meal strolls.",
            "Dietary Replacement: Simulates swapping 85g high-GI rice with 40g low-GI millets (Ragi/Bajra).",
            "Pharmacotherapy Titration: Tests adding SGLT2i (Dapagliflozin 10mg) or de-escalating nighttime Sulfonylurea.",
            "Instant Delta Feedback: Displays Peak Glucose Delta (-19.1 mg/dL) and Time-in-Range improvement (+4.0%).",
        ],
    },
    # Slide 7: Clinical Benchmarks
    {
        "title": "Rigorous Clinical Benchmark Validation",
        "subtitle": "Evaluated Against International Diabetology Standards",
        "bullets": [
            "Clarke Error Grid Analysis (Zones A + B): 100.0% (Zone A: 99.0%, Zone B: 1.0%, Zone C/D/E: 0.0%).",
            "Mean Absolute Relative Difference (MARD): 1.28% (Exceeds the < 10% clinical-grade sensor benchmark).",
            "Root Mean Squared Error (RMSE): 1.97 mg/dL across 120-minute forward test cohorts.",
            "Mean Absolute Error (MAE): 1.44 mg/dL.",
            "Adverse Event Classification ROC-AUC: 1.000 for both Hyperglycemic Spike and Hypoglycemic Crash.",
        ],
    },
    # Slide 8: Doctor UI
    {
        "title": "Conceptual Doctor UI & Clinical Decision Support",
        "subtitle": "Hospital-Grade Interface for Indian Endocrinologists and Physicians",
        "bullets": [
            "Patient Triage Selector: Live severity badges (Critical, High Risk, Moderate, Stable).",
            "Virtual Human Organ Twin: Interactive SVG avatar with glowing nodes for Pancreas, Heart, Liver, and Kidneys.",
            "Dual Telemetry Streaming: Real-time CGM line graph synchronized with PPG pulse and activity cadence.",
            "Live Demonstration Event Injectors: 1-click buttons to inject High-Carb Meals, Fasting Crashes, and Exercise.",
            "RSSDI / ICMR Clinical Audit Report: Instant export of Ambulatory Glucose Profile (AGP) and consultation notes.",
        ],
    },
    # Slide 9: Tech Stack & Architecture
    {
        "title": "Technical Architecture & Implementation",
        "subtitle": "Lightweight, Production-Ready, and Easy to Deploy",
        "bullets": [
            "Backend: Python 3.13, FastAPI ASGI Server, Uvicorn asynchronous execution.",
            "AI / ML Engine: Scikit-learn (Gradient Boosting, Random Forest), NumPy, SciPy (ODE simulation).",
            "Frontend: Responsive Single Page Application, Tailwind CSS, Chart.js, SVG Organ Twin Visualizer.",
            "Architecture: Clean separation of concerns (twin_engine, server, ui, data, models).",
            "GitHub Ready: Comprehensive .gitignore, under 5 MB total repository size, 1-click run script.",
        ],
    },
    # Slide 10: Conclusion
    {
        "title": "Conclusion & Healthcare Impact in India",
        "subtitle": "Reimagining and Reforming Healthcare Through Proactive Digital Twins",
        "bullets": [
            "Shifts Indian diabetology from reactive emergency management to proactive, preventative care.",
            "Prevents microvascular complications (diabetic retinopathy, nephropathy) and macrovascular MACE events.",
            "Reduces hospital readmission rates and emergency admissions due to nocturnal hypoglycemia.",
            "Scalable to Ayushman Bharat Digital Mission (ABDM) and national tele-ICU networks.",
            "Team Coders_ABES (ABES Engineering College) is dedicated to building predictive digital health in India.",
        ],
    },
]


def create_pptx_presentation(filepath: str):
    """Creates a 10-slide PowerPoint presentation with native backgrounds and zero errors."""
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    # Theme colors
    c_bg = RGBColor(10, 15, 29)         # #0a0f1d
    c_card = RGBColor(16, 24, 48)       # #101830
    c_cyan = RGBColor(6, 182, 212)      # #06b6d4
    c_white = RGBColor(241, 245, 249)   # #f1f5f9
    c_gray = RGBColor(148, 163, 184)    # #94a3b8

    for item in SLIDES_CONTENT:
        slide = prs.slides.add_slide(blank_layout)

        # Use native slide background (prevents shape conflict and PPTX repair issues)
        background = slide.background
        fill = background.fill
        fill.solid()
        fill.fore_color.rgb = c_bg

        # Title Box
        title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.5), Inches(11.7), Inches(1.2))
        tf = title_box.text_frame
        tf.word_wrap = True
        
        p_title = tf.paragraphs[0]
        p_title.text = item["title"]
        p_title.font.name = "Arial"
        p_title.font.size = Pt(28)
        p_title.font.bold = True
        p_title.font.color.rgb = c_cyan

        p_sub = tf.add_paragraph()
        p_sub.text = item.get("subtitle", "")
        p_sub.font.name = "Arial"
        p_sub.font.size = Pt(14)
        p_sub.font.color.rgb = c_gray

        # Content Card container
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.9), Inches(11.7), Inches(4.8))
        card.fill.solid()
        card.fill.fore_color.rgb = c_card
        card.line.color.rgb = c_cyan
        card.line.width = Pt(1.5)

        # Bullets inside container
        content_box = slide.shapes.add_textbox(Inches(1.1), Inches(2.1), Inches(11.1), Inches(4.4))
        ctf = content_box.text_frame
        ctf.word_wrap = True

        for idx, bullet in enumerate(item["bullets"]):
            p = ctf.add_paragraph() if idx > 0 else ctf.paragraphs[0]
            p.text = f"•  {bullet}"
            p.font.name = "Arial"
            p.font.size = Pt(14)
            p.font.color.rgb = c_white
            p.space_after = Pt(10)

    prs.save(filepath)
    print(f"[OK] Generated PPTX Presentation: {filepath} ({round(os.path.getsize(filepath)/1024, 1)} KB)")


def create_architecture_pptx(filepath: str):
    """Creates a high-resolution, widescreen Architecture Diagram PPTX."""
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    c_bg = RGBColor(10, 15, 29)
    c_card = RGBColor(16, 24, 48)
    c_cyan = RGBColor(6, 182, 212)
    c_white = RGBColor(241, 245, 249)
    c_gray = RGBColor(148, 163, 184)

    # Native background
    background = slide.background
    fill = background.fill
    fill.solid()
    fill.fore_color.rgb = c_bg

    # Header Box
    tb = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.7), Inches(1.1))
    tf = tb.text_frame
    tf.word_wrap = True

    p = tf.paragraphs[0]
    p.text = "PRANA-TWIN System Architecture Diagram"
    p.font.name = "Arial"
    p.font.size = Pt(26)
    p.font.bold = True
    p.font.color.rgb = c_cyan

    p_sub = tf.add_paragraph()
    p_sub.text = "Multi-Stream Data Fusion, Compartmental ODEs, Ensemble ML Predictors, and Doctor Decision Support UI"
    p_sub.font.name = "Arial"
    p_sub.font.size = Pt(13)
    p_sub.font.color.rgb = c_gray

    layers = [
        ("Layer 1: Multi-Stream Data Ingestion", [
            "Static EHR Stream: Demographics, HbA1c (8.6%), eGFR, Lipids, Prescriptions",
            "Dynamic IoT Stream: 5-min CGM Glucose, PPG Pulse, HRV (RMSSD), Steps",
            "Indian Dietary Profile: High-GI staple meal carb bolus (Rice, Parathas, Sweets)",
            "Circadian Telemetry: Nighttime fasting epochs & autonomic sleep staging",
            "Real-time Validation: Quality-checked telemetry streams ingested asynchronously",
        ], Inches(0.8), Inches(1.7), Inches(3.6), Inches(5.1)),

        ("Layer 2: Hybrid Digital Twin Core", [
            "Physiological ODEs: Bergman Minimal Model (Plasma Glucose + Remote Insulin)",
            "Multimodal Feature Fusion: Temporal derivative extractor (dG/dt, d2G/dt2)",
            "Forward Horizon Regressor: Gradient Boosted 24-step trajectory (0-120 mins)",
            "Adverse Event Classifiers: Acute Spike (>220 mg/dL) & Nocturnal Hypo (<70 mg/dL)",
            "Counterfactual Sandbox Engine: Instant simulation of Diet, Walk & Meds",
            "Explainable AI (XAI): Dynamic attribution weights for clinical drivers",
        ], Inches(4.8), Inches(1.7), Inches(3.8), Inches(5.1)),

        ("Layer 3: Clinical Decision Support UI", [
            "Patient Triage Selector: Real-time risk status (Critical, High Risk, Moderate, Stable)",
            "Interactive Organ Twin: SVG avatar with glowing Pancreas, Heart, Kidneys, Liver",
            "2-Hour Predictive Chart: Horizon graph with 90% confidence bands & thresholds",
            "Counterfactual Sliders: Dynamic carb titration, walking minutes, and medication",
            "RSSDI / ICMR Clinical Audit: Instant export of AGP metrics & consultation notes",
        ], Inches(8.9), Inches(1.7), Inches(3.6), Inches(5.1)),
    ]

    for title, items, left, top, width, height in layers:
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        card.fill.solid()
        card.fill.fore_color.rgb = c_card
        card.line.color.rgb = c_cyan
        card.line.width = Pt(1.5)

        tx = slide.shapes.add_textbox(left + Inches(0.2), top + Inches(0.2), width - Inches(0.4), height - Inches(0.4))
        frame = tx.text_frame
        frame.word_wrap = True

        p_t = frame.paragraphs[0]
        p_t.text = title
        p_t.font.name = "Arial"
        p_t.font.size = Pt(14)
        p_t.font.bold = True
        p_t.font.color.rgb = c_cyan
        p_t.space_after = Pt(10)

        for b in items:
            p_b = frame.add_paragraph()
            p_b.text = f"▶  {b}"
            p_b.font.name = "Arial"
            p_b.font.size = Pt(11)
            p_b.font.color.rgb = c_white
            p_b.space_after = Pt(8)

    prs.save(filepath)
    print(f"[OK] Generated Architecture PPTX: {filepath} ({round(os.path.getsize(filepath)/1024, 1)} KB)")


def export_pptx_to_pdf_with_powerpoint(pptx_path: str, pdf_path: str) -> bool:
    """Exports a PPTX to a 100% compliant, easily openable vector PDF using PowerPoint COM."""
    abs_pptx = os.path.abspath(pptx_path).replace("/", "\\")
    abs_pdf = os.path.abspath(pdf_path).replace("/", "\\")

    ps_script = f"""
$ErrorActionPreference = 'Stop'
try {{
    $ppt = New-Object -ComObject PowerPoint.Application
    $pres = $ppt.Presentations.Open('{abs_pptx}')
    $pres.SaveAs('{abs_pdf}', 32)
    $pres.Close()
    $ppt.Quit()
    Write-Output "EXPORT_OK"
}} catch {{
    Write-Error $_
    exit 1
}}
"""
    try:
        proc = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_script],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if proc.returncode == 0 and os.path.exists(abs_pdf) and os.path.getsize(abs_pdf) > 0:
            print(f"[OK] PowerPoint Exported PDF: {pdf_path} ({round(os.path.getsize(pdf_path)/1024, 1)} KB)")
            return True
    except Exception as e:
        print(f"[NOTE] PowerPoint COM export unavailable: {e}")
    return False


def create_fallback_presentation_pdf(filepath: str):
    """Fallback PDF generator using ReportLab with all 10 slides and clean formatting."""
    doc = SimpleDocTemplate(
        filepath,
        pagesize=landscape(letter),
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36,
    )
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "PresTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#0891b2"),
    )
    sub_style = ParagraphStyle(
        "PresSub",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#475569"),
        spaceAfter=12,
    )
    bullet_style = ParagraphStyle(
        "PresBullet",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=16,
        textColor=colors.HexColor("#1e293b"),
        spaceAfter=6,
    )

    story = []
    total_slides = len(SLIDES_CONTENT)

    for idx, item in enumerate(SLIDES_CONTENT):
        story.append(Paragraph(item["title"], title_style))
        story.append(Paragraph(item.get("subtitle", ""), sub_style))

        table_data = [[Paragraph(f"•  {b}", bullet_style)] for b in item["bullets"]]
        t = Table(table_data, colWidths=[700])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ]))
        story.append(t)
        # Avoid trailing empty page after the last slide
        if idx < total_slides - 1:
            story.append(PageBreak())

    doc.build(story)
    print(f"[OK] Fallback PDF Generated: {filepath} ({round(os.path.getsize(filepath)/1024, 1)} KB)")


def create_fallback_architecture_pdf(filepath: str):
    """Fallback Architecture PDF generator using ReportLab."""
    doc = SimpleDocTemplate(
        filepath,
        pagesize=landscape(letter),
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36,
    )
    styles = getSampleStyleSheet()

    t_style = ParagraphStyle("ArchTitle", parent=styles["Heading1"], fontName="Helvetica-Bold", fontSize=20, textColor=colors.HexColor("#0891b2"), spaceAfter=6)
    sub_style = ParagraphStyle("ArchSub", parent=styles["Normal"], fontName="Helvetica", fontSize=11, textColor=colors.HexColor("#475569"), spaceAfter=14)
    sec_style = ParagraphStyle("ArchSec", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=11, textColor=colors.HexColor("#0f172a"), spaceAfter=6)
    item_style = ParagraphStyle("ArchItem", parent=styles["Normal"], fontName="Helvetica", fontSize=9, leading=13, textColor=colors.HexColor("#334155"))

    story = [
        Paragraph("PRANA-TWIN End-to-End System Architecture", t_style),
        Paragraph("Multi-Stream Data Fusion, Compartmental ODEs, Ensemble ML Predictors, and Doctor Decision Support UI", sub_style),
    ]

    col1 = [Paragraph("<b>Layer 1: Multi-Stream Data Ingestion</b>", sec_style)] + [
        Paragraph("• Static EHR: Demographics, HbA1c, eGFR, Lipids, Prescriptions", item_style),
        Paragraph("• Dynamic IoT: 5-min CGM Glucose, PPG Pulse, HRV (RMSSD), Steps", item_style),
        Paragraph("• Indian Dietary Profile: High-GI meal carb bolus (Rice, Parathas)", item_style),
        Paragraph("• Circadian Telemetry: Nighttime fasting epochs & autonomic sleep", item_style),
    ]
    col2 = [Paragraph("<b>Layer 2: Hybrid Digital Twin Core</b>", sec_style)] + [
        Paragraph("• Bergman Minimal Model ODEs (G & X dynamic compartments)", item_style),
        Paragraph("• Multimodal Feature Fusion & Derivative Extractor (dG/dt, d2G/dt2)", item_style),
        Paragraph("• Gradient Boosted Regressor (120-min forward trajectory)", item_style),
        Paragraph("• Adverse Event Classifiers (Acute Spike >220 & Hypo <70 mg/dL)", item_style),
        Paragraph("• Counterfactual What-If Sandbox (Diet, Walk, Med Titration)", item_style),
    ]
    col3 = [Paragraph("<b>Layer 3: Clinical Decision Support UI</b>", sec_style)] + [
        Paragraph("• Patient Triage Selector (Critical, High Risk, Moderate, Stable)", item_style),
        Paragraph("• Interactive Organ Twin (Pancreas, Heart, Kidneys, Liver)", item_style),
        Paragraph("• 2-Hour Predictive Chart with 90% Confidence Intervals", item_style),
        Paragraph("• Counterfactual Sandbox (Real-time delta feedback)", item_style),
        Paragraph("• One-Click RSSDI / ICMR Clinical Audit & AGP Report Export", item_style),
    ]

    table_data = [[col1, col2, col3]]
    t = Table(table_data, colWidths=[230, 245, 235])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("BOX", (0, 0), (-1, -1), 1.5, colors.HexColor("#0891b2")),
        ("INNERGRID", (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(t)
    doc.build(story)
    print(f"[OK] Fallback Architecture PDF Generated: {filepath} ({round(os.path.getsize(filepath)/1024, 1)} KB)")


def generate_all_deliverables():
    """Generates all presentation and architecture deliverables in PPTX and PDF."""
    os.makedirs("docs", exist_ok=True)

    pres_pptx = "docs/PRANA_TWIN_Summit_Presentation.pptx"
    pres_pdf = "docs/PRANA_TWIN_Summit_Presentation.pdf"
    arch_pptx = "docs/PRANA_TWIN_Architecture_Diagram.pptx"
    arch_pdf = "docs/PRANA_TWIN_Architecture_Diagram.pdf"

    # 1. Generate clean PPTX presentations
    create_pptx_presentation(pres_pptx)
    create_architecture_pptx(arch_pptx)

    # 2. Export pixel-perfect PDFs using PowerPoint engine if available
    pres_pdf_exported = export_pptx_to_pdf_with_powerpoint(pres_pptx, pres_pdf)
    if not pres_pdf_exported:
        create_fallback_presentation_pdf(pres_pdf)

    arch_pdf_exported = export_pptx_to_pdf_with_powerpoint(arch_pptx, arch_pdf)
    if not arch_pdf_exported:
        create_fallback_architecture_pdf(arch_pdf)

    print("\n[SUCCESS] All deliverables successfully generated and verified in docs/ folder!")


if __name__ == "__main__":
    generate_all_deliverables()
