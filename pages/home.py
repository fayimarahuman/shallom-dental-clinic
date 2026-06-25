# pages/home.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from utils.db import get_connection
from utils.sanitize import esc


def show_dashboard():
    st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        /* ============================================
           PROFESSIONAL DASHBOARD - BLUE + AMBER THEME
           ============================================ */
        * { margin: 0; padding: 0; box-sizing: border-box; }
        html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }

        .stApp { background: #F5F8FC !important; }
        #MainMenu, footer, header { display: none !important; }
        .block-container { padding: 1.5rem 2rem 2rem !important; max-width: 100% !important; }

        div[data-testid="stVerticalBlock"] { border: none !important; background: transparent !important; box-shadow: none !important; }
        div[data-testid="column"] > div { border: none !important; background: transparent !important; box-shadow: none !important; }
        div[data-testid="stHorizontalBlock"] { border: none !important; background: transparent !important; }
        .element-container { border: none !important; background: transparent !important; box-shadow: none !important; }
        div[data-testid="stForm"] { border: none !important; background: transparent !important; box-shadow: none !important; padding: 0 !important; }
        hr { display: none !important; }
        div[data-testid="stPlotlyChart"] { border: none !important; background: transparent !important; box-shadow: none !important; }
        iframe { border: none !important; }

        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: #E8EDF2; border-radius: 10px; }
        ::-webkit-scrollbar-thumb { background: #E88C30; border-radius: 10px; }
        ::-webkit-scrollbar-thumb:hover { background: #1E4A76; }

        /* ── Dashboard Header ── */
        .dash-header {
            background: linear-gradient(135deg, #1E4A76 0%, #2D6A9F 50%, #3A7CA5 100%);
            border-radius: 24px; padding: 28px 32px; margin-bottom: 28px;
            display: flex; align-items: center; justify-content: space-between;
            box-shadow: 0 8px 24px rgba(30,74,118,0.15);
        }
        .dash-header-left { display: flex; align-items: center; gap: 18px; }
        .dash-header-icon {
            width: 54px; height: 54px; background: rgba(255,255,255,0.12);
            border-radius: 16px; display: flex; align-items: center; justify-content: center;
            border: 1px solid rgba(255,255,255,0.2);
        }
        .dash-title { color: #fff; font-size: 22px; font-weight: 800; margin: 0 0 4px; letter-spacing: -0.3px; }
        .dash-sub { color: rgba(255,255,255,0.65); font-size: 13px; margin: 0; }
        .dash-badge {
            background: rgba(255,255,255,0.12); border: 1px solid rgba(255,255,255,0.2);
            color: rgba(255,255,255,0.85); font-size: 12px; font-weight: 600;
            padding: 8px 18px; border-radius: 40px;
            display: flex; align-items: center; gap: 8px;
        }
        .live-dot {
            width: 8px; height: 8px; background: #4ADE80; border-radius: 50%;
            box-shadow: 0 0 8px rgba(74,222,128,0.8); animation: pulse 2s infinite;
        }
        @keyframes pulse { 0%,100% { opacity:1; } 50% { opacity:0.5; } }

        /* ── Section Heading ── */
        .sec-heading {
            font-size: 12px; font-weight: 700; color: #6B8FAB;
            letter-spacing: 1.2px; text-transform: uppercase; margin: 0 0 16px 4px;
        }

        /* ── KPI Cards ── */
        .kpi-card {
            background: #FFFFFF; border-radius: 20px; padding: 22px 20px;
            transition: all 0.25s ease; border: 1px solid #E8EDF2;
            position: relative; overflow: hidden;
        }
        .kpi-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 12px 28px rgba(30,74,118,0.12); border-color: #E88C30;
        }
        .kpi-card::before {
            content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px;
            background: linear-gradient(90deg, #E88C30, #F5B87A);
        }
        .kpi-icon { width: 48px; height: 48px; border-radius: 14px; display: flex; align-items: center; justify-content: center; margin-bottom: 16px; }
        .kpi-val { font-size: 28px; font-weight: 800; color: #1E4A76; line-height: 1.2; margin-bottom: 6px; }
        .kpi-label { font-size: 12px; color: #6B8FAB; font-weight: 500; }
        .kpi-tag {
            display: inline-flex; align-items: center; gap: 6px;
            font-size: 11px; font-weight: 600; padding: 4px 12px; border-radius: 24px; margin-top: 12px;
        }
        .tag-blue  { background: #EBF3FB; color: #1E4A76; }
        .tag-green { background: #E8F5E9; color: #2E7D32; }
        .tag-red   { background: #FEF0EE; color: #D32F2F; }
        .tag-amber { background: #FFF8E1; color: #E88C30; }

        /* ── Quick Action Cards ── */
        .qa-card {
            background: #FFFFFF; border-radius: 18px; padding: 20px 12px; text-align: center;
            border: 1px solid #E8EDF2; transition: all 0.25s ease; cursor: pointer;
        }
        .qa-card:hover { transform: translateY(-5px); border-color: #E88C30; box-shadow: 0 8px 20px rgba(232,140,48,0.15); }
        .qa-icon { width: 54px; height: 54px; border-radius: 16px; display: flex; align-items: center; justify-content: center; margin: 0 auto 14px; }
        .qa-label { font-size: 13px; font-weight: 600; color: #1E4A76; margin-bottom: 8px; }
        .qa-arrow { font-size: 11px; color: #E88C30; opacity: 0; transition: opacity 0.2s ease; }
        .qa-card:hover .qa-arrow { opacity: 1; }

        /* ── Modern Appointments Table ── */
        .appt-section { background: #FFFFFF; border-radius: 20px; border: 1px solid #E8EDF2; overflow: hidden; margin-bottom: 24px; }
        .appt-header { padding: 20px 24px 16px; display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid #F0F4F8; }
        .appt-header-left { display: flex; align-items: center; gap: 12px; }
        .appt-header-icon { width: 38px; height: 38px; background: #EBF3FB; border-radius: 12px; display: flex; align-items: center; justify-content: center; }
        .appt-header-title { font-size: 15px; font-weight: 700; color: #1E4A76; margin: 0; }
        .appt-header-sub { font-size: 12px; color: #8FA8BF; margin: 2px 0 0; }
        .appt-count-badge { background: #EBF3FB; color: #1E4A76; font-size: 12px; font-weight: 700; padding: 4px 14px; border-radius: 20px; }
        .appt-table { width: 100%; border-collapse: collapse; }
        .appt-table thead tr { background: #F8FAFE; }
        .appt-table thead th { padding: 12px 20px; text-align: left; font-size: 11px; font-weight: 700; color: #8FA8BF; letter-spacing: 0.8px; text-transform: uppercase; border-bottom: 1px solid #EEF2F7; }
        .appt-table tbody tr { border-bottom: 1px solid #F4F7FA; transition: background 0.15s ease; }
        .appt-table tbody tr:last-child { border-bottom: none; }
        .appt-table tbody tr:hover { background: #F8FAFE; }
        .appt-table td { padding: 14px 20px; vertical-align: middle; }
        .appt-date-col { display: flex; flex-direction: column; gap: 2px; }
        .appt-date { font-size: 13px; font-weight: 600; color: #1E4A76; }
        .appt-time { font-size: 11px; color: #8FA8BF; }
        .appt-patient { display: flex; align-items: center; gap: 10px; }
        .appt-avatar { width: 34px; height: 34px; border-radius: 10px; background: linear-gradient(135deg, #1E4A76, #3A7CA5); display: flex; align-items: center; justify-content: center; font-size: 13px; font-weight: 700; color: #fff; flex-shrink: 0; }
        .appt-patient-name { font-size: 13px; font-weight: 600; color: #1A3A5C; }
        .appt-treatment { font-size: 12px; color: #1E4A76; font-weight: 600; background: #EBF3FB; display: inline-block; padding: 4px 12px; border-radius: 8px; }
        .status-pill { display: inline-flex; align-items: center; gap: 6px; padding: 5px 14px; border-radius: 20px; font-size: 11px; font-weight: 700; letter-spacing: 0.3px; }
        .status-dot { width: 6px; height: 6px; border-radius: 50%; }
        .s-completed { background: #E8F5E9; color: #2E7D32; }
        .s-completed .status-dot { background: #2E7D32; }
        .s-scheduled { background: #EBF3FB; color: #1E4A76; }
        .s-scheduled .status-dot { background: #1E4A76; }
        .s-noshow { background: #FEF0EE; color: #D32F2F; }
        .s-noshow .status-dot { background: #D32F2F; }
        .s-cancelled { background: #F5F5F5; color: #6B8FAB; }
        .s-cancelled .status-dot { background: #9E9E9E; }
        .appt-empty { text-align: center; padding: 48px 24px; color: #8FA8BF; font-size: 14px; }
    </style>
    """, unsafe_allow_html=True)

    # ── Greeting — time-based using server clock, name from session ───────────
    now      = datetime.now()
    hour     = now.hour
    minute   = now.minute
    if hour < 12:
        greeting = "Good morning"
    elif hour < 17:
        greeting = "Good afternoon"
    else:
        greeting = "Good evening"

    # Use logged-in username from session state if available
    username = st.session_state.get("username", None)
    if username:
        # Capitalise first letter, strip trailing whitespace
        display_name = username.strip().capitalize()
    else:
        display_name = "Staff"

    # Live clock string e.g. "Wednesday, June 25, 2026  •  09:42 AM"
    time_str  = now.strftime("%I:%M %p").lstrip("0")   # e.g. "9:42 AM"
    today_str = now.strftime("%A, %B %d, %Y")

    # ── Fetch Data ────────────────────────────────────────────────────────────
    conn = get_connection()
    if not conn:
        st.error("Database connection failed.")
        return

    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM patients")
    total_patients = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM appointments")
    total_appointments = cursor.fetchone()[0]
    cursor.execute("SELECT COALESCE(SUM(amount_paid), 0) FROM payments")
    total_revenue = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM appointments WHERE status = 'No-show'")
    noshow_count = cursor.fetchone()[0]
    noshow_rate = (noshow_count / total_appointments * 100) if total_appointments > 0 else 0
    cursor.execute("SELECT COUNT(*) FROM appointments WHERE appointment_date = CURRENT_DATE")
    today_appointments = cursor.fetchone()[0]
    cursor.execute("SELECT COALESCE(SUM(amount_paid), 0) FROM payments WHERE payment_date = CURRENT_DATE")
    today_revenue = cursor.fetchone()[0]
    cursor.execute("""
        SELECT
            (SELECT COALESCE(SUM(expected_cost), 0) FROM appointments) -
            (SELECT COALESCE(SUM(amount_paid), 0) FROM payments)
    """)
    total_balance = cursor.fetchone()[0] or 0
    cursor.execute("SELECT status, COUNT(*) FROM appointments GROUP BY status")
    status_data = cursor.fetchall()

    cursor.execute("""
        SELECT label, total FROM (
            SELECT TO_CHAR(appointment_date, 'Mon') AS label,
                   TO_CHAR(appointment_date, 'YYYY-MM') AS sort_key,
                   COUNT(*) AS total
            FROM appointments GROUP BY label, sort_key
            ORDER BY sort_key DESC LIMIT 6
        ) recent ORDER BY sort_key ASC
    """)
    monthly_appt_rows = cursor.fetchall()

    # Revenue: raw UGX amounts — no division
    cursor.execute("""
        SELECT label, revenue FROM (
            SELECT TO_CHAR(payment_date, 'Mon') AS label,
                   TO_CHAR(payment_date, 'YYYY-MM') AS sort_key,
                   COALESCE(SUM(amount_paid), 0) AS revenue
            FROM payments GROUP BY label, sort_key
            ORDER BY sort_key DESC LIMIT 6
        ) recent ORDER BY sort_key ASC
    """)
    monthly_rev_rows = cursor.fetchall()

    cursor.execute("""
        SELECT treatment, COUNT(*) AS count FROM appointments
        WHERE treatment IS NOT NULL AND treatment != ''
        GROUP BY treatment ORDER BY count DESC LIMIT 5
    """)
    top_treatment_rows = cursor.fetchall()

    cursor.close()
    conn.close()

    # ── Header ────────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="dash-header">
        <div class="dash-header-left">
            <div class="dash-header-icon">
                <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="1.8">
                    <path d="M4 4h6v8H4V4zm10 0h6v4h-6V4zm0 8h6v8h-6v-8zM4 16h6v4H4v-4z"/>
                </svg>
            </div>
            <div>
                <p class="dash-title">{greeting}, {esc(display_name)} &nbsp;<span style="font-size:18px;">👋</span></p>
                <p class="dash-sub">Shallom Dental Clinic &middot; {today_str} &middot; {time_str}</p>
            </div>
        </div>
        <div class="dash-badge"><div class="live-dot"></div>Live Dashboard</div>
    </div>
    """, unsafe_allow_html=True)

    # ── KPI Row 1 ─────────────────────────────────────────────────────────────
    st.markdown('<div class="sec-heading">KEY METRICS</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    rev_display = f"UGX {total_revenue/1_000_000:.1f}M" if total_revenue >= 1_000_000 else f"UGX {total_revenue:,.0f}"

    with c1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-icon" style="background:#EBF3FB;">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#1E4A76" stroke-width="1.8">
                    <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                    <circle cx="9" cy="7" r="4"/>
                    <path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/>
                </svg>
            </div>
            <div class="kpi-val">{total_patients:,}</div>
            <div class="kpi-label">Total Patients</div>
            <div class="kpi-tag tag-blue">All time</div>
        </div>""", unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-icon" style="background:#EBF3FB;">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#1E4A76" stroke-width="1.8">
                    <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
                    <line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/>
                    <line x1="3" y1="10" x2="21" y2="10"/>
                </svg>
            </div>
            <div class="kpi-val">{total_appointments:,}</div>
            <div class="kpi-label">Total Appointments</div>
            <div class="kpi-tag tag-blue">Today: {today_appointments}</div>
        </div>""", unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-icon" style="background:#EBF3FB;">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#1E4A76" stroke-width="1.8">
                    <rect x="1" y="4" width="22" height="16" rx="2" ry="2"/>
                    <line x1="1" y1="10" x2="23" y2="10"/>
                </svg>
            </div>
            <div class="kpi-val" style="font-size:22px;">{rev_display}</div>
            <div class="kpi-label">Total Revenue</div>
            <div class="kpi-tag tag-amber">Today: UGX {today_revenue:,.0f}</div>
        </div>""", unsafe_allow_html=True)

    with c4:
        ns_tag   = "tag-green" if noshow_rate <= 8 else "tag-amber" if noshow_rate <= 15 else "tag-red"
        ns_label = "Excellent"  if noshow_rate <= 8 else "Moderate"  if noshow_rate <= 15 else "Critical"
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-icon" style="background:#FEF0EE;">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#D32F2F" stroke-width="1.8">
                    <circle cx="12" cy="12" r="10"/>
                    <line x1="12" y1="8" x2="12" y2="12"/>
                    <line x1="12" y1="16" x2="12.01" y2="16"/>
                </svg>
            </div>
            <div class="kpi-val">{noshow_rate:.1f}%</div>
            <div class="kpi-label">No-Show Rate</div>
            <div class="kpi-tag {ns_tag}">{ns_label}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)

    # ── KPI Row 2 ─────────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    completed       = next((c for s, c in status_data if s == 'Completed'), 0)
    scheduled       = next((c for s, c in status_data if s == 'Scheduled'), 0)
    completion_rate = round(completed / total_appointments * 100, 1) if total_appointments else 0
    avg_rev         = round(total_revenue / total_appointments) if total_appointments else 0

    with c1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-icon" style="background:#FFF8E1;">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#E88C30" stroke-width="1.8">
                    <circle cx="12" cy="12" r="10"/>
                    <line x1="12" y1="16" x2="12" y2="12"/>
                    <circle cx="12" cy="8" r="0.5" fill="#E88C30"/>
                </svg>
            </div>
            <div class="kpi-val" style="font-size:20px;">UGX {total_balance:,.0f}</div>
            <div class="kpi-label">Outstanding Balance</div>
            <div class="kpi-tag tag-amber">Needs follow-up</div>
        </div>""", unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-icon" style="background:#E8F5E9;">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#2E7D32" stroke-width="1.8">
                    <path d="M20 6L9 17l-5-5"/>
                </svg>
            </div>
            <div class="kpi-val">{completion_rate}%</div>
            <div class="kpi-label">Completion Rate</div>
            <div class="kpi-tag tag-green">On track</div>
        </div>""", unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-icon" style="background:#EBF3FB;">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#1E4A76" stroke-width="1.8">
                    <circle cx="12" cy="12" r="10"/>
                    <polyline points="12 6 12 12 16 14"/>
                </svg>
            </div>
            <div class="kpi-val">{scheduled}</div>
            <div class="kpi-label">Upcoming Scheduled</div>
            <div class="kpi-tag tag-blue">Active bookings</div>
        </div>""", unsafe_allow_html=True)

    with c4:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-icon" style="background:#EBF3FB;">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#1E4A76" stroke-width="1.8">
                    <path d="M21 12a9 9 0 0 1-9 9m9-9a9 9 0 0 0-9-9m9 9H3m9 9a9 9 0 0 1-9-9m9 9c1.66 0 3-4 3-9s-1.34-9-3-9m0 18c-1.66 0-3-4-3-9s1.34-9 3-9"/>
                </svg>
            </div>
            <div class="kpi-val" style="font-size:18px;">UGX {avg_rev:,.0f}</div>
            <div class="kpi-label">Avg Revenue / Visit</div>
            <div class="kpi-tag tag-blue">Per appointment</div>
        </div>""", unsafe_allow_html=True)

    # ── Quick Actions ─────────────────────────────────────────────────────────
    st.markdown('<div class="sec-heading" style="margin-top:28px;">QUICK ACTIONS</div>', unsafe_allow_html=True)
    qa_items = [
        ("New Patient",      "Patients",           "#EBF3FB", "#1E4A76",
         '<path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="8.5" cy="7" r="4"/><line x1="20" y1="8" x2="20" y2="14"/><line x1="23" y1="11" x2="17" y2="11"/>'),
        ("New Appointment",  "Appointments",        "#EBF3FB", "#1E4A76",
         '<rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>'),
        ("Record Payment",   "Payments",            "#FFF8E1", "#E88C30",
         '<rect x="1" y="4" width="22" height="16" rx="2" ry="2"/><line x1="1" y1="10" x2="23" y2="10"/>'),
        ("Predict No-Show",  "No-Show Predictor",   "#FFF8E1", "#E88C30",
         '<circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>'),
        ("View Reports",     "Reports",             "#EBF3FB", "#1E4A76",
         '<line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>'),
    ]
    QA_CARD_H = 148

    st.markdown(f"""
    <style>
        .stButton > button {{
            background:transparent!important; border:none!important;
            box-shadow:none!important; color:transparent!important;
            height:{QA_CARD_H}px!important; box-sizing:border-box!important;
            width:100%!important; padding:0!important; cursor:pointer!important;
            opacity:0!important;
        }}
        .stButton > button:hover {{ background:transparent!important; }}
    </style>
    """, unsafe_allow_html=True)

    qa_cols = st.columns(5)
    for col, (label, page, bg, color, path) in zip(qa_cols, qa_items):
        with col:
            st.markdown(f"""
            <div class="qa-card" style="pointer-events:none;margin-bottom:-{QA_CARD_H}px;">
                <div class="qa-icon" style="background:{bg};">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.8">{path}</svg>
                </div>
                <div class="qa-label">{label}</div>
                <div class="qa-arrow">→</div>
            </div>""", unsafe_allow_html=True)
            if st.button(label, key=f"qa_{page}", use_container_width=True):
                st.session_state.page = page
                st.rerun()

    # ── Performance Trends ────────────────────────────────────────────────────
    st.markdown('<div class="sec-heading" style="margin-top:28px;">PERFORMANCE TRENDS</div>', unsafe_allow_html=True)
    months    = [row[0] for row in monthly_appt_rows]
    appt_vals = [int(row[1]) for row in monthly_appt_rows]
    rev_months = [row[0] for row in monthly_rev_rows]
    rev_vals   = [float(row[1]) for row in monthly_rev_rows]   # raw UGX — no division

    CARD_BG = '#FFFFFF'
    BORDER  = '#E8EDF2'
    BLUE    = '#1E4A76'
    AMBER   = '#E88C30'
    GRID    = '#F0F4F8'
    MUTED   = '#8FA8BF'

    def card_layout(height=300, title="", t_margin=52):
        return dict(
            plot_bgcolor=CARD_BG, paper_bgcolor=CARD_BG,
            height=height, margin=dict(l=16, r=16, t=t_margin, b=16),
            showlegend=False,
            font=dict(family='Inter, sans-serif', color=MUTED),
            title=dict(text=title, font=dict(size=14, color=BLUE, family='Inter, sans-serif'),
                       x=0.01, y=0.97, xanchor='left', yanchor='top'),
            shapes=[
                dict(type='rect', xref='paper', yref='paper', x0=0, y0=0, x1=1, y1=1,
                     line=dict(color=BORDER, width=1), fillcolor=CARD_BG, layer='below'),
                dict(type='line', xref='paper', yref='paper', x0=0, y0=1, x1=1, y1=1,
                     line=dict(color=AMBER, width=3)),
            ]
        )

    def fmt_ugx(v):
        if v >= 1_000_000:
            return f"{v/1_000_000:.1f}M"
        elif v >= 1_000:
            return f"{v/1_000:.0f}K"
        else:
            return f"{v:,.0f}"

    cc1, cc2 = st.columns(2)
    with cc1:
        if months:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=months, y=appt_vals, mode='lines+markers',
                line=dict(color=BLUE, width=3),
                marker=dict(color=AMBER, size=9),
                fill='tozeroy', fillcolor='rgba(30,74,118,0.05)'
            ))
            fig.update_layout(**card_layout(title="📅  Monthly Appointments"))
            fig.update_xaxes(showgrid=False, color=MUTED, linecolor=BORDER)
            fig.update_yaxes(showgrid=True, gridcolor=GRID, color=MUTED, linecolor=BORDER)
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info("No appointment data yet to chart.")

    with cc2:
        if rev_months:
            fig = go.Figure(go.Bar(
                x=rev_months, y=rev_vals,
                marker=dict(color=AMBER, opacity=0.9, line=dict(color=BLUE, width=1)),
                text=[fmt_ugx(v) for v in rev_vals],
                textposition='outside',
                textfont=dict(color=BLUE, size=11)
            ))
            fig.update_layout(**card_layout(title="💰  Revenue Trend (UGX)", t_margin=60))
            fig.update_xaxes(showgrid=False, color=MUTED, linecolor=BORDER)
            fig.update_yaxes(showgrid=True, gridcolor=GRID, color=MUTED, linecolor=BORDER,
                             tickformat=",")
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info("No payment data yet to chart.")

    # ── Clinical Analytics ────────────────────────────────────────────────────
    st.markdown('<div class="sec-heading">CLINICAL ANALYTICS</div>', unsafe_allow_html=True)
    cc1, cc2 = st.columns(2)

    with cc1:
        status_df     = pd.DataFrame(status_data, columns=['Status', 'Count'])
        status_colors = {'Completed': '#2E7D32', 'Scheduled': BLUE, 'No-show': '#D32F2F', 'Cancelled': MUTED}
        fig = go.Figure(data=[go.Pie(
            labels=status_df['Status'], values=status_df['Count'],
            hole=0.58,
            marker=dict(colors=[status_colors.get(s, BLUE) for s in status_df['Status']],
                        line=dict(color='white', width=2)),
            textinfo='label+percent',
            textfont=dict(size=12, color=BLUE)
        )])
        fig.update_layout(**card_layout(title="🔵  Appointment Status", height=320))
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    with cc2:
        if top_treatment_rows:
            treatments = [row[0] for row in top_treatment_rows]
            counts     = [int(row[1]) for row in top_treatment_rows]
            bar_colors = [AMBER if i == 0 else '#F5B87A' if i == 1 else '#FAD49A' for i in range(len(treatments))]
            fig = go.Figure(go.Bar(
                x=counts, y=treatments, orientation='h',
                marker=dict(color=bar_colors, line=dict(color=BLUE, width=0.5)),
                text=counts, textposition='outside',
                textfont=dict(color=BLUE, size=11)
            ))
            fig.update_layout(**card_layout(title="🦷  Top Treatments", height=320, t_margin=56))
            fig.update_xaxes(showgrid=True, gridcolor=GRID, color=MUTED)
            fig.update_yaxes(showgrid=False, color=BLUE, tickfont=dict(size=12))
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info("No treatment data yet to chart.")

    # ── Recent Appointments ───────────────────────────────────────────────────
    st.markdown('<div class="sec-heading">RECENT APPOINTMENTS</div>', unsafe_allow_html=True)

    conn   = get_connection()
    recent = []
    if conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT TO_CHAR(a.appointment_date, 'Mon DD, YYYY') AS date,
                   TO_CHAR(a.appointment_time, 'HH12:MI AM')   AS time,
                   p.name      AS patient,
                   a.treatment AS treatment,
                   a.status    AS status
            FROM appointments a
            JOIN patients p ON a.patient_id = p.patient_id
            ORDER BY a.appointment_date DESC, a.appointment_time DESC
            LIMIT 10
        """)
        recent = cursor.fetchall()
        cursor.close()
        conn.close()

    status_cls = {
        'Completed': 's-completed',
        'Scheduled': 's-scheduled',
        'No-show':   's-noshow',
        'Cancelled': 's-cancelled',
    }

    if recent:
        rows_html = ""
        for date, time_val, patient, treatment, status in recent:
            initials  = esc("".join(w[0].upper() for w in patient.split()[:2]))
            patient, treatment = esc(patient), esc(treatment)
            pill_cls  = status_cls.get(status, 's-scheduled')
            rows_html += f"""
            <tr>
                <td><div class="appt-date-col"><span class="appt-date">{date}</span><span class="appt-time">{time_val}</span></div></td>
                <td><div class="appt-patient"><div class="appt-avatar">{initials}</div><span class="appt-patient-name">{patient}</span></div></td>
                <td><span class="appt-treatment">{treatment}</span></td>
                <td><span class="status-pill {pill_cls}"><span class="status-dot"></span>{status}</span></td>
            </tr>"""

        st.markdown(f"""
        <div class="appt-section">
            <div class="appt-header">
                <div class="appt-header-left">
                    <div class="appt-header-icon">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#1E4A76" stroke-width="1.8">
                            <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
                            <line x1="16" y1="2" x2="16" y2="6"/>
                            <line x1="8" y1="2" x2="8" y2="6"/>
                            <line x1="3" y1="10" x2="21" y2="10"/>
                        </svg>
                    </div>
                    <div>
                        <p class="appt-header-title">Recent Appointments</p>
                        <p class="appt-header-sub">Last 10 visits across all patients</p>
                    </div>
                </div>
                <span class="appt-count-badge">{len(recent)} records</span>
            </div>
            <table class="appt-table">
                <thead><tr><th>Date &amp; Time</th><th>Patient</th><th>Treatment</th><th>Status</th></tr></thead>
                <tbody>{rows_html}</tbody>
            </table>
        </div>""", unsafe_allow_html=True)

    else:
        st.markdown("""
        <div class="appt-section">
            <div class="appt-header">
                <div class="appt-header-left">
                    <div class="appt-header-icon">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#1E4A76" stroke-width="1.8">
                            <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
                            <line x1="16" y1="2" x2="16" y2="6"/>
                            <line x1="8" y1="2" x2="8" y2="6"/>
                            <line x1="3" y1="10" x2="21" y2="10"/>
                        </svg>
                    </div>
                    <div>
                        <p class="appt-header-title">Recent Appointments</p>
                        <p class="appt-header-sub">Last 10 visits across all patients</p>
                    </div>
                </div>
            </div>
            <div class="appt-empty">No appointments found. Connect to the database to view records.</div>
        </div>""", unsafe_allow_html=True)