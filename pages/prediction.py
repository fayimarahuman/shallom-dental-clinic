# pages/prediction.py
import streamlit as st
import joblib
import numpy as np
import pandas as pd
import os
import plotly.graph_objects as go
from utils.db import get_connection
from utils.audit import log_action
from utils.sanitize import esc


def show_prediction():
    st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
        .stApp { background: #F5F8FC !important; }
        #MainMenu, footer, header { display: none !important; }
        .block-container { padding: 1.5rem 2rem 2rem !important; max-width: 100% !important; }

        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: #E8EDF2; border-radius: 10px; }
        ::-webkit-scrollbar-thumb { background: #E88C30; border-radius: 10px; }

        /* ── Remove ALL horizontal lines & ghost boxes ── */
        hr,
        [data-testid="stForm"] hr,
        [data-testid="stVerticalBlock"] hr,
        .stMarkdown hr { display: none !important; border: none !important; height: 0 !important; }

        [data-testid="stForm"],
        [data-testid="stVerticalBlockBorderWrapper"],
        [data-testid="stVerticalBlockBorderWrapper"] > div {
            border: none !important; padding: 0 !important;
            background: transparent !important; box-shadow: none !important; outline: none !important;
        }
        .element-container:empty,
        [data-testid="stVerticalBlock"] > div:empty,
        [data-testid="stForm"] > div:empty { display: none !important; }

        /* ── PAGE HEADER ── */
        .page-header {
            background: linear-gradient(135deg, #1E4A76 0%, #2D6A9F 50%, #3A7CA5 100%);
            border-radius: 24px;
            padding: 28px 32px;
            margin-bottom: 28px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            box-shadow: 0 8px 24px rgba(30,74,118,0.12);
            position: relative;
            overflow: hidden;
        }
        .page-header::after {
            content: ''; position: absolute; right: 140px; top: -50px;
            width: 180px; height: 180px;
            background: radial-gradient(circle, rgba(255,255,255,0.06) 0%, transparent 70%);
            pointer-events: none;
        }
        .page-header::before {
            content: ''; position: absolute; right: -10px; bottom: -30px;
            width: 140px; height: 140px;
            background: radial-gradient(circle, rgba(232,140,48,0.12) 0%, transparent 70%);
            pointer-events: none;
        }
        .ph-left { display: flex; align-items: center; gap: 18px; z-index: 1; }
        .ph-icon {
            width: 54px; height: 54px;
            background: rgba(255,255,255,0.12);
            border-radius: 16px;
            display: flex;
            align-items: center;
            justify-content: center;
            border: 1px solid rgba(255,255,255,0.2);
            flex-shrink: 0;
        }
        .ph-title { color: #fff; font-size: 22px; font-weight: 800; margin: 0 0 4px; letter-spacing: -0.3px; }
        .ph-subtitle { color: rgba(255,255,255,0.65); font-size: 13px; margin: 0; }
        .ph-badge {
            background: rgba(232,140,48,0.2);
            border: 1px solid rgba(232,140,48,0.4);
            color: #F5BC6A;
            font-size: 12px;
            font-weight: 700;
            padding: 8px 18px;
            border-radius: 40px;
            z-index: 1;
            display: flex;
            align-items: center;
            gap: 8px;
            letter-spacing: 0.2px;
        }

        /* ── MODEL CHIPS ── */
        .model-row { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; margin-bottom: 24px; }
        .model-chip {
            background: #fff;
            border: 1.5px solid #E2E8F0;
            border-radius: 30px;
            padding: 6px 16px;
            font-size: 12px;
            font-weight: 600;
            color: #1E4A76;
            display: flex;
            align-items: center;
            gap: 6px;
            box-shadow: 0 2px 6px rgba(30,74,118,0.04);
        }

        /* ── SECTION LABELS ── */
        .sec-label {
            font-size: 11px;
            font-weight: 700;
            color: #6B8FAB;
            letter-spacing: 1.2px;
            text-transform: uppercase;
            margin: 0 0 14px 4px;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        /* ── STEP BADGE ── */
        .step-badge {
            display: inline-flex;
            align-items: center;
            gap: 10px;
            background: #EEF4FB;
            border: 1.5px solid #D6E6F5;
            border-radius: 30px;
            padding: 6px 18px;
            margin-bottom: 16px;
            font-size: 12px;
            font-weight: 700;
            color: #1E4A76;
        }
        .step-num {
            width: 22px; height: 22px;
            background: #1E4A76;
            border-radius: 50%;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            color: #fff;
            font-size: 11px;
            font-weight: 800;
        }

        /* ── PATIENT PREVIEW CARD ── */
        .patient-preview {
            background: #fff;
            border: 1.5px solid #E2E8F0;
            border-radius: 20px;
            padding: 24px;
            margin: 16px 0;
            box-shadow: 0 2px 12px rgba(30,74,118,0.05);
        }
        .preview-top {
            display: flex;
            align-items: center;
            gap: 16px;
            margin-bottom: 20px;
        }
        .preview-avatar {
            width: 52px; height: 52px;
            background: linear-gradient(135deg, #1E4A76, #2D6A9F);
            border-radius: 16px;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
            box-shadow: 0 4px 12px rgba(30,74,118,0.2);
        }
        .preview-name { font-size: 18px; font-weight: 700; color: #1A3A5C; margin: 0 0 4px; }
        .preview-meta { font-size: 12px; color: #6B8FAB; margin: 0; }
        .appt-fields { display: flex; flex-wrap: wrap; gap: 24px; }
        .appt-field { min-width: 140px; }
        .af-label { font-size: 10px; font-weight: 700; color: #6B8FAB; text-transform: uppercase; margin-bottom: 4px; }
        .af-val { font-size: 14px; font-weight: 600; color: #1A3A5C; }

        /* ── STAT TILES ── */
        .stat-tile {
            background: #fff;
            border: 1.5px solid #E2E8F0;
            border-radius: 14px;
            padding: 14px;
            text-align: center;
            box-shadow: 0 2px 8px rgba(30,74,118,0.04);
        }
        .st-val { font-size: 20px; font-weight: 800; color: #1E4A76; margin: 0; }
        .st-lbl { font-size: 10px; color: #6B8FAB; margin-top: 4px; font-weight: 600; letter-spacing: 0.2px; }

        /* ── INPUTS ── */
        .stTextInput label, .stSelectbox label {
            font-size: 12px !important;
            font-weight: 600 !important;
            color: #1A3A5C !important;
        }
        .stTextInput input {
            border: 1.5px solid #E2E8F0 !important;
            border-radius: 12px !important;
            font-size: 14px !important;
            color: #1A3A5C !important;
            background: #F8FAFD !important;
            padding: 12px 16px !important;
            transition: border-color 0.15s, box-shadow 0.15s !important;
        }
        .stTextInput input:focus {
            border-color: #E88C30 !important;
            box-shadow: 0 0 0 3px rgba(232,140,48,0.12) !important;
            background: #fff !important;
        }

        /* ── SELECTBOX — comprehensive fix for selected text visibility ── */
        .stSelectbox > div > div {
            border: 1.5px solid #E2E8F0 !important;
            border-radius: 12px !important;
            background: #F8FAFD !important;
            min-height: 46px !important;
        }
        .stSelectbox [data-baseweb="select"] *,
        .stSelectbox [data-baseweb="select"] span,
        .stSelectbox [data-baseweb="select"] div,
        .stSelectbox [data-baseweb="select"] p,
        .stSelectbox [data-baseweb="select"] input,
        .stSelectbox > div > div > div,
        .stSelectbox > div > div > div > div,
        .stSelectbox > div > div > div > div > div,
        .stSelectbox > div > div span {
            color: #1A3A5C !important;
            font-size: 14px !important;
            font-weight: 500 !important;
            -webkit-text-fill-color: #1A3A5C !important;
        }
        [data-baseweb="popover"] li,
        [data-baseweb="menu"] li,
        [role="option"] {
            font-size: 14px !important;
            color: #1A3A5C !important;
            padding: 10px 16px !important;
            font-family: 'Inter', sans-serif !important;
        }
        [data-baseweb="popover"] [aria-selected="true"],
        [data-baseweb="menu"] [aria-selected="true"],
        [role="option"]:hover {
            background: #EEF4FB !important;
            color: #1E4A76 !important;
            font-weight: 600 !important;
        }

        /* ── BUTTONS ── */
        .stButton button {
            background: linear-gradient(135deg, #1E4A76, #2D6A9F) !important;
            border: none !important;
            border-radius: 14px !important;
            padding: 0 28px !important;
            height: 50px !important;
            min-height: 50px !important;
            line-height: 50px !important;
            font-weight: 700 !important;
            font-size: 15px !important;
            color: #fff !important;
            box-shadow: 0 2px 12px rgba(30,74,118,0.22) !important;
            transition: all 0.2s ease !important;
            width: 100% !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
        }
        .stButton button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 8px 20px rgba(30,74,118,0.3) !important;
        }

        /* ── RESULT CARD ── */
        .result-card { border-radius: 20px; padding: 32px 28px; text-align: center; }
        .result-show { background: linear-gradient(135deg, #1E4A76, #2D6A9F); }
        .result-noshow { background: linear-gradient(135deg, #B5670F, #D98324); }
        .r-icon { margin-bottom: 12px; display: flex; justify-content: center; }
        .r-verdict { color: #fff; font-size: 24px; font-weight: 800; margin: 0 0 8px; }
        .r-conf { color: rgba(255,255,255,0.8); font-size: 14px; margin: 0 0 16px; }
        .r-risk-badge {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: rgba(255,255,255,0.15);
            border: 1px solid rgba(255,255,255,0.25);
            border-radius: 30px;
            padding: 6px 18px;
            color: #fff;
            font-size: 12px;
            font-weight: 700;
        }

        /* ── ACTION CARD ── */
        .action-card {
            background: #fff;
            border: 1.5px solid #E2E8F0;
            border-radius: 16px;
            padding: 20px;
            margin-top: 16px;
            box-shadow: 0 2px 10px rgba(30,74,118,0.05);
        }
        .action-title { font-size: 11px; font-weight: 700; color: #6B8FAB; text-transform: uppercase; margin-bottom: 12px; letter-spacing: 1px; }
        .action-item { display: flex; align-items: center; gap: 10px; font-size: 13px; color: #1A3A5C; margin-bottom: 8px; }
        .action-item:last-child { margin-bottom: 0; }

        /* ── FACTOR CARDS ── */
        .factor-card {
            background: #fff;
            border: 1.5px solid #E2E8F0;
            border-radius: 16px;
            padding: 18px;
            text-align: center;
            box-shadow: 0 2px 10px rgba(30,74,118,0.05);
        }
        .factor-label { font-size: 10px; font-weight: 700; color: #6B8FAB; text-transform: uppercase; margin-bottom: 6px; letter-spacing: 0.6px; }
        .factor-val { font-size: 20px; font-weight: 800; color: #1E4A76; margin-bottom: 6px; }
        .factor-tag {
            display: inline-flex;
            align-items: center;
            gap: 5px;
            font-size: 11px;
            font-weight: 700;
            padding: 4px 12px;
            border-radius: 30px;
        }
        .tag-blue  { background: #DBEAFE; color: #1E4A76; }
        .tag-amber { background: #FDEBD3; color: #B5670F; }
        .tag-neutral { background: #E2E8F0; color: #1A3A5C; }

        /* ── IDLE BOX ── */
        .idle-box {
            background: #fff;
            border: 1.5px dashed #CBD5E1;
            border-radius: 24px;
            padding: 60px 40px;
            text-align: center;
        }

        /* ── EXPANDER STYLING (key facts table) ── */
        .kf-table-wrap {
            background: #fff;
            border-radius: 16px;
            border: 1.5px solid #E2E8F0;
            overflow: hidden;
            margin-top: 8px;
        }
        .kf-table { width: 100%; border-collapse: collapse; }
        .kf-table thead tr { background: linear-gradient(135deg, #1E4A76 0%, #2D6A9F 100%); }
        .kf-table thead th {
            padding: 10px 16px; text-align: left; font-size: 10.5px; font-weight: 700;
            letter-spacing: 1px; text-transform: uppercase; color: rgba(255,255,255,0.8); border: none;
        }
        .kf-table tbody tr { border-bottom: 1px solid #F0F5FA; }
        .kf-table tbody tr:last-child { border-bottom: none; }
        .kf-table tbody td { padding: 10px 16px; font-size: 13px; color: #2D4A6B; border: none; }
        .kf-impact-highest { color: #B5670F; font-weight: 700; }
        .kf-impact-high { color: #1E4A76; font-weight: 600; }
        .kf-impact-medium { color: #6B8FAB; font-weight: 600; }
    </style>
    """, unsafe_allow_html=True)

    # Page Header
    st.markdown("""
    <div class="page-header">
        <div class="ph-left">
            <div class="ph-icon">
                <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="1.8">
                    <path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.5 1.5M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.5 1.5"/>
                    <path d="M12 4.5a2.5 2.5 0 0 0-4.5-1.5M12 4.5a2.5 2.5 0 0 1 4.5-1.5"/>
                </svg>
            </div>
            <div>
                <p class="ph-title">No-Show Prediction</p>
                <p class="ph-subtitle">Predict patient attendance before their appointment</p>
            </div>
        </div>
        <div class="ph-badge">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="1.8">
                <rect x="3" y="3" width="18" height="18" rx="2"/><line x1="9" y1="9" x2="15" y2="15"/><line x1="15" y1="9" x2="9" y2="15"/>
            </svg>
            Random Forest AI
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Model chips
    st.markdown("""
        <div class="model-row">
        <div class="model-chip"><span style="display:inline-flex;align-items:center;justify-content:center;width:18px;height:18px;border-radius:6px;background:#EEF4FB;color:#1E4A76;">◎</span> Random Forest</div>
        <div class="model-chip">Accuracy: 95%</div>
        <div class="model-chip">AUC: 0.971</div>
        <div class="model-chip">Precision: 100%</div>
        <div class="model-chip">Trained on 21,080 records</div>
    </div>
    """, unsafe_allow_html=True)

    # Load model
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    model = None
    scaler = None

    for rel_path in ['dental_no_show_model.pkl', 'attendance_model.pkl']:
        candidate = os.path.join(repo_root, rel_path)
        if os.path.exists(candidate):
            try:
                model = joblib.load(candidate)
                break
            except Exception:
                continue

    for rel_path in ['scaler.pkl', 'scaler_best.pkl']:
        candidate = os.path.join(repo_root, rel_path)
        if os.path.exists(candidate):
            try:
                scaler = joblib.load(candidate)
                break
            except Exception:
                continue

    if model is None:
        st.error("Model file not found. Expected one of: dental_no_show_model.pkl / attendance_model.pkl")
        st.info(f"Looked for model files under: {repo_root}")
        return

    # DB Connection
    conn = get_connection()
    if not conn:
        st.error("Database connection failed.")
        return
    cursor = conn.cursor()
    cursor.execute("SELECT patient_id, name, age FROM patients ORDER BY name")
    patients = cursor.fetchall()
    cursor.close()
    conn.close()

    if not patients:
        st.warning("No patients found. Please add patients first.")
        return

    patient_dict = {name: (pid, age) for pid, name, age in patients}

    # Step 1 - Select Patient
    st.markdown('<div class="step-badge"><span class="step-num">1</span> Select a Patient</div>', unsafe_allow_html=True)
    col_search, col_select = st.columns([2, 3])
    with col_search:
        search_term = st.text_input("Search", placeholder="Type name to filter...", label_visibility="collapsed", key="pred_search")
    with col_select:
        all_names = list(patient_dict.keys())
        filtered_names = [n for n in all_names if search_term.lower() in n.lower()] if search_term else all_names
        if not filtered_names:
            st.warning("No patients match your search.")
            return
        selected_patient = st.selectbox("Select", filtered_names, label_visibility="collapsed", key="pred_select")

    patient_id, patient_age = patient_dict[selected_patient]

    # Fetch patient history
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COALESCE(SUM(CASE WHEN status='Cancelled' THEN 1 ELSE 0 END), 0),
               COALESCE(SUM(CASE WHEN status='Rescheduled' THEN 1 ELSE 0 END), 0),
               COALESCE(SUM(CASE WHEN status='Completed' THEN 1 ELSE 0 END), 0),
               COALESCE(SUM(CASE WHEN status='No-show' THEN 1 ELSE 0 END), 0),
               COALESCE(SUM(CASE WHEN status='Scheduled' AND appointment_date < CURRENT_DATE THEN 1 ELSE 0 END), 0)
        FROM appointments WHERE patient_id = %s
    """, (patient_id,))
    history = cursor.fetchone()
    cancellations, rescheduled, success_appts, noshow_count, not_checkout = history

    cursor.execute("""
        SELECT appointment_id, appointment_date, appointment_time, treatment, expected_cost,
               EXTRACT(DOW FROM appointment_date), EXTRACT(WEEK FROM appointment_date) - EXTRACT(WEEK FROM DATE_TRUNC('month', appointment_date)) + 1,
               EXTRACT(MONTH FROM appointment_date), EXTRACT(HOUR FROM appointment_time), appointment_type,
               (appointment_date - CURRENT_DATE) AS days_until_appointment
        FROM appointments WHERE patient_id = %s AND status = 'Scheduled' AND appointment_date >= CURRENT_DATE
        ORDER BY appointment_date ASC LIMIT 1
    """, (patient_id,))
    next_appt = cursor.fetchone()
    cursor.close()
    conn.close()

    # Step 2 - Patient Preview
    st.markdown('<div class="step-badge" style="margin-top:20px;"><span class="step-num">2</span> Review Patient Info</div>', unsafe_allow_html=True)
    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

    # Escape user-supplied strings before any HTML interpolation
    safe_patient = esc(selected_patient)

    if not next_appt:
        st.markdown(f"""
        <div class="patient-preview">
            <div class="preview-top">
                <div class="preview-avatar">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="1.8">
                        <circle cx="12" cy="12" r="10"/><path d="M12 10a3 3 0 1 0 0-6 3 3 0 0 0 0 6z"/><path d="M12 14a7 7 0 0 0-7 7h14a7 7 0 0 0-7-7z"/>
                    </svg>
                </div>
                <div>
                    <p class="preview-name">{safe_patient}</p>
                    <p class="preview-meta">Age {patient_age or '—'} · {success_appts + noshow_count} total visits · {noshow_count} no-shows</p>
                </div>
            </div>
            <div style="text-align:center;padding:20px 0;">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#B0C8E8" stroke-width="1.5">
                    <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>
                </svg>
                <p style="font-size:15px;font-weight:600;color:#1A3A5C;margin:12px 0 4px;">No upcoming scheduled appointment</p>
                <p style="font-size:13px;color:#6B8FAB;">Please schedule an appointment first before running a prediction.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    (app_id, app_date, app_time, treatment, expected_cost, day_of_week, week_of_month,
     month, hour, appointment_type, days_until_appointment) = next_appt

    # Escape free-text fields from DB before HTML interpolation
    safe_treatment = esc(treatment or '—')

    lead_time = max(int(days_until_appointment), 0) if days_until_appointment is not None else 0
    time_str = app_time.strftime('%I:%M %p') if hasattr(app_time, 'strftime') else str(app_time)
    day_name = day_names[int(day_of_week)]
    appt_type_encoded = 0 if appointment_type == "Follow-up" else 1 if appointment_type == "New" else 2

    st.markdown(f"""
    <div class="patient-preview">
        <div class="preview-top">
            <div class="preview-avatar">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="1.8">
                    <circle cx="12" cy="12" r="10"/><path d="M12 10a3 3 0 1 0 0-6 3 3 0 0 0 0 6z"/><path d="M12 14a7 7 0 0 0-7 7h14a7 7 0 0 0-7-7z"/>
                </svg>
            </div>
            <div>
                <p class="preview-name">{safe_patient}</p>
                <p class="preview-meta">Age {patient_age or '—'} · {success_appts + noshow_count} total visits · {noshow_count} no-show(s)</p>
            </div>
        </div>
        <div class="appt-fields">
            <div class="appt-field"><div class="af-label">Treatment</div><div class="af-val">{safe_treatment}</div></div>
            <div class="appt-field"><div class="af-label">Date</div><div class="af-val">{app_date}</div></div>
            <div class="appt-field"><div class="af-label">Time</div><div class="af-val">{time_str}</div></div>
            <div class="appt-field"><div class="af-label">Type</div><div class="af-val">{appointment_type}</div></div>
            <div class="appt-field"><div class="af-label">Day</div><div class="af-val">{day_name}</div></div>
            <div class="appt-field"><div class="af-label">Cost</div><div class="af-val">UGX {expected_cost:,.0f}</div></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # History stats
    st.markdown('<div class="sec-label">Patient Visit History</div>', unsafe_allow_html=True)
    h1, h2, h3, h4, h5 = st.columns(5)
    with h1:
        st.markdown(f'<div class="stat-tile"><div class="st-val">{lead_time}d</div><div class="st-lbl">Days Until Appt</div></div>', unsafe_allow_html=True)
    with h2:
        st.markdown(f'<div class="stat-tile"><div class="st-val">{cancellations}</div><div class="st-lbl">Cancellations</div></div>', unsafe_allow_html=True)
    with h3:
        st.markdown(f'<div class="stat-tile"><div class="st-val">{rescheduled}</div><div class="st-lbl">Rescheduled</div></div>', unsafe_allow_html=True)
    with h4:
        st.markdown(f'<div class="stat-tile"><div class="st-val">{success_appts}</div><div class="st-lbl">Completed</div></div>', unsafe_allow_html=True)
    with h5:
        st.markdown(f'<div class="stat-tile"><div class="st-val">{noshow_count}</div><div class="st-lbl">No-Shows</div></div>', unsafe_allow_html=True)

    # Step 3 - Run Prediction
    st.markdown('<div class="step-badge" style="margin-top:24px;"><span class="step-num">3</span> Run Prediction</div>', unsafe_allow_html=True)
    run_col, _ = st.columns([2, 3])
    with run_col:
        run_clicked = st.button("Run No-Show Prediction", use_container_width=True, key="run_prediction_btn")

    if not run_clicked:
        st.markdown("""
        <div class="idle-box">
            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="#B0C8E8" stroke-width="1.5">
                <path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.5 1.5M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.5 1.5"/>
            </svg>
            <p style="font-size:18px;font-weight:700;color:#1A3A5C;margin-top:20px;">Ready to predict</p>
            <p style="font-size:14px;color:#6B8FAB;">Select a patient above, review their details, then click Run No-Show Prediction.</p>
        </div>
        """, unsafe_allow_html=True)
        return

    # Build features and predict
    # NOTE: dental_no_show_model.pkl (Random Forest) was trained and evaluated in the
    # notebook on RAW, unscaled features (X_balanced / X_test_log). scaler.pkl was only
    # ever fit/used there for the separate Logistic Regression comparison model -- it
    # was never applied before fitting/evaluating this Random Forest. Calling
    # scaler.transform() here before model.predict() caused a train/serve mismatch:
    # on a 200-row synthetic test, ~12% of predictions flipped (Y vs N) purely because
    # of this scaling step. Do NOT scale features before predicting with this model.
    #
    # Features are passed as a named DataFrame (not a bare numpy array) because the
    # model was originally fit on a pandas DataFrame with these exact column names.
    # Matching that avoids sklearn's "X does not have valid feature names" UserWarning.
    feature_names = [
        'LEAD_TIME', 'APPT_TYPE_STANDARDIZE', 'TOTAL_NUMBER_OF_CANCELLATIONS',
        'TOTAL_NUMBER_OF_RESCHEDULED', 'TOTAL_NUMBER_OF_NOT_CHECKOUT_APPOINTMENT',
        'TOTAL_NUMBER_OF_SUCCESS_APPOINTMENT', 'TOTAL_NUMBER_OF_NOSHOW',
        'DAY_OF_WEEK', 'WEEK_OF_MONTH', 'NUM_OF_MONTH', 'HOUR_OF_DAY', 'AGE'
    ]
    features = pd.DataFrame([[
        lead_time, appt_type_encoded, cancellations, rescheduled, not_checkout,
        success_appts, noshow_count, day_of_week, week_of_month, month, hour,
        patient_age if patient_age else 30
    ]], columns=feature_names)

    prediction = model.predict(features)[0]
    probabilities = model.predict_proba(features)[0]
    no_show_prob = probabilities[1]
    show_prob = probabilities[0]

    if no_show_prob < 0.3:
        risk_level, risk_icon, risk_desc = "LOW RISK", "●", "Patient likely to attend"
    elif no_show_prob < 0.7:
        risk_level, risk_icon, risk_desc = "MEDIUM RISK", "◐", "Send a reminder to be safe"
    else:
        risk_level, risk_icon, risk_desc = "HIGH RISK", "▲", "Call to confirm & request deposit"

    # Step 4 - Results
    st.markdown('<div class="step-badge" style="margin-top:24px;"><span class="step-num">4</span> Prediction Result</div>', unsafe_allow_html=True)

    res_col, gauge_col = st.columns([1, 1])

    with res_col:
        if prediction == 'Y' or prediction == 1:
            st.markdown(f"""
            <div class="result-card result-noshow">
                <div class="r-icon">
                    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                        <circle cx="12" cy="12" r="10"/>
                        <line x1="12" y1="8" x2="12" y2="12"/>
                        <circle cx="12" cy="16" r="0.5" fill="#FFFFFF"/>
                    </svg>
                </div>
                <p class="r-verdict">NO-SHOW PREDICTED</p>
                <p class="r-conf">Confidence: {no_show_prob:.1%}</p>
                <div class="r-risk-badge">{risk_icon} {risk_level} — {risk_desc}</div>
            </div>
            <div class="action-card">
                <div class="action-title">Recommended Actions</div>
                <div class="action-item">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#B5670F" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.8 19.8 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.08 4.18 2 2 0 0 1 4.05 2h3a2 2 0 0 1 2 1.72c.12.86.32 1.7.59 2.5a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.58-1.1a2 2 0 0 1 2.11-.45c.8.27 1.64.47 2.5.59A2 2 0 0 1 22 16.92z"/></svg>
                    Call patient to confirm attendance
                </div>
                <div class="action-item">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#1E4A76" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a4 4 0 0 1-4 4H8l-5 3V7a4 4 0 0 1 4-4h10a4 4 0 0 1 4 4z"/></svg>
                    Send SMS reminder 24 hrs before
                </div>
                <div class="action-item">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#1E4A76" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 3H8a2 2 0 0 0-2 2v2h12V5a2 2 0 0 0-2-2z"/></svg>
                    Request a deposit or prepayment
                </div>
                <div class="action-item">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#1E4A76" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
                    Consider double-booking the slot
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="result-card result-show">
                <div class="r-icon">
                    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M20 6L9 17l-5-5"/>
                    </svg>
                </div>
                <p class="r-verdict">SHOW PREDICTED</p>
                <p class="r-conf">Confidence: {show_prob:.1%}</p>
                <div class="r-risk-badge">{risk_icon} {risk_level} — {risk_desc}</div>
            </div>
            <div class="action-card">
                <div class="action-title">Preparation Checklist</div>
                <div class="action-item">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#1E4A76" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/></svg>
                    Prepare and review patient file
                </div>
                <div class="action-item">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#1E4A76" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 10h18"/><path d="M5 10V7a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v3"/><path d="M3 20h18"/><path d="M7 20v-6"/><path d="M17 20v-6"/></svg>
                    Ready the treatment room
                </div>
                <div class="action-item">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#B5670F" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l.6.6a1 1 0 0 0 1.4 0l2.1-2.1a1 1 0 0 0 0-1.4l-.6-.6a1 1 0 0 0-1.4 0z"/><path d="M2 22l7-7"/><path d="M8 8l8 8"/><path d="M15 3l6 6"/></svg>
                    Prepare required materials &amp; tools
                </div>
                <div class="action-item">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#1E4A76" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 7h18s-3 0-3-7"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>
                    Send a courtesy reminder anyway
                </div>
            </div>
            """, unsafe_allow_html=True)

    with gauge_col:
        gauge_color = "#D98324" if (prediction == 'Y' or prediction == 1) else "#1E4A76"
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=no_show_prob * 100,
            number={'suffix': '%', 'font': {'size': 32, 'color': gauge_color}},
            title={'text': "No-Show Risk", 'font': {'size': 14, 'color': '#1A3A5C'}},
            gauge={
                'axis': {'range': [0, 100], 'tickcolor': '#B0C8E8'},
                'bar': {'color': gauge_color, 'thickness': 0.28},
                'bgcolor': 'white',
                'steps': [
                    {'range': [0, 30], 'color': '#DBEAFE'},
                    {'range': [30, 70], 'color': '#FDEBD3'},
                    {'range': [70, 100], 'color': '#FCD9A8'},
                ],
                'threshold': {'line': {'color': '#1E4A76', 'width': 3}, 'thickness': 0.75, 'value': 50}
            }
        ))
        fig.update_layout(height=300, margin=dict(l=30, r=30, t=50, b=20), paper_bgcolor='white')
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    # Key Factors
    st.markdown('<div class="sec-label" style="margin-top:24px;">Key Factors</div>', unsafe_allow_html=True)
    f1, f2, f3 = st.columns(3)
    with f1:
        tag_cls = "tag-amber" if noshow_count > 0 else "tag-blue"
        tag_text = "Increases risk" if noshow_count > 0 else "No history of missing"
        st.markdown(f'<div class="factor-card"><div class="factor-label">Prev. No-Shows</div><div class="factor-val">{noshow_count}</div><div class="factor-tag {tag_cls}">{tag_text}</div></div>', unsafe_allow_html=True)
    with f2:
        if lead_time > 30:
            tag_cls, tag_text = "tag-amber", f"{lead_time}d — Long wait"
        elif lead_time > 14:
            tag_cls, tag_text = "tag-amber", f"{lead_time}d — Moderate"
        else:
            tag_cls, tag_text = "tag-blue", f"{lead_time}d — Short wait"
        st.markdown(f'<div class="factor-card"><div class="factor-label">Days Until Appointment</div><div class="factor-val">{lead_time} days</div><div class="factor-tag {tag_cls}">{tag_text}</div></div>', unsafe_allow_html=True)
    with f3:
        st.markdown(f'<div class="factor-card"><div class="factor-label">Appointment Day</div><div class="factor-val">{day_name}</div><div class="factor-tag tag-blue">{appointment_type} visit</div></div>', unsafe_allow_html=True)

    # Log action
    log_action("PREDICTION", table_name="appointments", record_id=app_id,
               new_data={"prediction": "No-Show" if (prediction == 'Y' or prediction == 1) else "Show", "confidence": float(no_show_prob), "patient": selected_patient},
               status="SUCCESS")

    with st.expander("How does this prediction work?"):
        st.markdown("**Model Details:** Random Forest Classifier trained on 21,080 historical appointment records.")
        st.markdown(f"""
        <div class="kf-table-wrap">
            <table class="kf-table">
                <thead>
                    <tr><th>Feature</th><th>Value</th><th>Impact</th></tr>
                </thead>
                <tbody>
                    <tr><td>Previous No-Shows</td><td>{noshow_count}</td><td class="kf-impact-highest">Highest</td></tr>
                    <tr><td>Appointment Success Rate</td><td>{success_appts}/{success_appts + noshow_count}</td><td class="kf-impact-high">High</td></tr>
                    <tr><td>Days Until Appointment</td><td>{lead_time} days</td><td class="kf-impact-medium">Medium</td></tr>
                    <tr><td>Appointment Type</td><td>{appointment_type}</td><td class="kf-impact-medium">Medium</td></tr>
                </tbody>
            </table>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("**Risk Thresholds:** LOW (<30%) — Patient likely to attend · MEDIUM (30–70%) — Send a reminder · HIGH (>70%) — Call to confirm")
        st.markdown("**Model Performance:** Accuracy 95% · AUC 0.971 · Precision 100% · Recall 99.7%")
        st.markdown("**Note:** This schema doesn't store a booking timestamp, so historical *average* lead time can't be calculated. \"Days Until Appointment\" instead reflects the live gap between today and the scheduled date for the appointment being predicted.")