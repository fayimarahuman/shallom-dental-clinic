# pages/appointments.py
import streamlit as st
import pandas as pd
from datetime import datetime, time
from utils.db import get_connection
from utils.sanitize import esc
from utils.audit import log_action
from pages.inventory import auto_reduce_inventory


def show_appointments():
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

        /* ── Form card styling on stForm itself ── */
        [data-testid="stForm"] {
            background: #fff !important;
            border: 1.5px solid #E2E8F0 !important;
            border-radius: 20px !important;
            padding: 26px 28px !important;
            box-shadow: 0 2px 12px rgba(30,74,118,0.05) !important;
        }

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
            padding: 8px 20px;
            border-radius: 40px;
            z-index: 1;
            letter-spacing: 0.2px;
        }

        /* ── TABS ── */
        .stTabs [data-baseweb="tab-list"] {
            background: #fff !important;
            border-radius: 16px !important;
            border: 1.5px solid #E2E8F0 !important;
            padding: 6px 8px !important;
            gap: 4px !important;
            margin-bottom: 28px !important;
            box-shadow: 0 2px 8px rgba(30,74,118,0.06) !important;
        }
        .stTabs [data-baseweb="tab"] {
            border-radius: 12px !important;
            font-size: 13.5px !important;
            font-weight: 500 !important;
            color: #6B8FAB !important;
            padding: 10px 22px !important;
            transition: color 0.15s !important;
        }
        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, #1E4A76, #2D6A9F) !important;
            color: #fff !important;
            font-weight: 600 !important;
            box-shadow: 0 2px 10px rgba(30,74,118,0.2) !important;
        }
        .stTabs [data-baseweb="tab-highlight"],
        .stTabs [data-baseweb="tab-border"] { display: none !important; }

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

        /* ── INPUT FIELDS ── */
        .stTextInput label, .stSelectbox label, .stDateInput label, .stTimeInput label, .stNumberInput label {
            font-size: 12px !important;
            font-weight: 600 !important;
            color: #1A3A5C !important;
            letter-spacing: 0.1px !important;
        }
        .stTextInput input, .stDateInput input, .stTimeInput input, .stNumberInput > div > div > input {
            border: 1.5px solid #E2E8F0 !important;
            border-radius: 12px !important;
            font-size: 14px !important;
            color: #1A3A5C !important;
            background: #F8FAFD !important;
            padding: 12px 16px !important;
            transition: border-color 0.15s, box-shadow 0.15s !important;
        }
        .stTextInput input:focus, .stDateInput input:focus, .stTimeInput input:focus {
            border-color: #E88C30 !important;
            box-shadow: 0 0 0 3px rgba(232,140,48,0.12) !important;
            background: #fff !important;
        }
        .stNumberInput > div > div { overflow: hidden !important; }

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
        .stFormSubmitButton button, .stButton button {
            background: linear-gradient(135deg, #1E4A76, #2D6A9F) !important;
            border: none !important;
            border-radius: 12px !important;
            padding: 12px 24px !important;
            font-weight: 600 !important;
            font-size: 14px !important;
            color: #fff !important;
            box-shadow: 0 2px 10px rgba(30,74,118,0.2) !important;
            transition: all 0.2s ease !important;
        }
        .stFormSubmitButton button:hover, .stButton button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 16px rgba(30,74,118,0.25) !important;
        }

        /* ── BALANCE STRIP ── */
        .bal-strip {
            display: inline-flex;
            align-items: center;
            gap: 10px;
            padding: 10px 18px;
            border-radius: 40px;
            font-size: 13px;
            font-weight: 600;
            margin-bottom: 20px;
        }
        .bal-strip.neutral { background: #EEF4FB; color: #1E4A76; }
        .bal-strip.owed { background: #FDEBD3; color: #B5670F; }
        .bal-strip.credit { background: #DBEAFE; color: #1E4A76; }

        /* ── MODERN APPOINTMENTS TABLE ── */
        .apt-table-wrap {
            background: #fff;
            border-radius: 18px;
            border: 1.5px solid #E2E8F0;
            overflow: hidden;
            box-shadow: 0 4px 20px rgba(30,74,118,0.07);
            margin-top: 4px;
        }
        .apt-table { width: 100%; border-collapse: collapse; }
        .apt-table thead tr { background: linear-gradient(135deg, #1E4A76 0%, #2D6A9F 100%); }
        .apt-table thead th {
            padding: 13px 18px;
            text-align: left;
            font-size: 10.5px;
            font-weight: 700;
            letter-spacing: 1.1px;
            text-transform: uppercase;
            color: rgba(255,255,255,0.75);
            white-space: nowrap;
            border: none;
        }
        .apt-table tbody tr {
            border-bottom: 1px solid #F0F5FA;
            transition: background 0.12s ease;
        }
        .apt-table tbody tr:last-child { border-bottom: none; }
        .apt-table tbody tr:hover { background: #F7FAFD; }
        .apt-table tbody td {
            padding: 13px 18px;
            vertical-align: middle;
            border: none;
            font-size: 13.5px;
            color: #2D4A6B;
        }
        .apt-id {
            display: inline-flex; align-items: center;
            background: #EEF4FB; color: #2D6A9F;
            font-size: 11px; font-weight: 700;
            padding: 4px 10px; border-radius: 8px;
        }
        .apt-patient { font-weight: 600; color: #1A3A5C; }
        .apt-date { font-size: 12.5px; color: #6B8FAB; font-weight: 500; white-space: nowrap; }
        .apt-dentist { color: #2D6A9F; font-weight: 500; }
        .apt-cost { font-weight: 700; color: #1E4A76; }
        .badge-status {
            display: inline-block; font-size: 11px; font-weight: 700;
            padding: 4px 12px; border-radius: 20px; letter-spacing: 0.2px;
        }
        .badge-scheduled { background: #DBEAFE; color: #1E4A76; }
        .badge-completed { background: #FDEBD3; color: #B5670F; }
        .badge-noshow    { background: #E2E8F0; color: #1A3A5C; }
        .badge-cancelled { background: #E2E8F0; color: #1A3A5C; }
        .apt-dash { color: #CBD5E1; }
        .apt-table-footer {
            padding: 11px 18px;
            background: #F8FAFD;
            border-top: 1px solid #E2E8F0;
            font-size: 12px;
            color: #6B8FAB;
            font-weight: 600;
        }

        /* ── DELETE WARNING ── */
        .delete-warn {
            background: #FEF2F2;
            border: 1.5px solid #FECACA;
            border-radius: 16px;
            padding: 20px 24px;
            margin: 20px 0;
        }
        .delete-warn-title {
            font-size: 14px;
            font-weight: 700;
            color: #B91C1C;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .delete-field { font-size: 13px; color: #1A3A5C; margin-bottom: 6px; }
        .delete-field span { font-weight: 600; color: #1E4A76; }

        /* ── EMPTY STATE ── */
        .empty-state {
            background: #fff;
            border: 1.5px dashed #CBD5E1;
            border-radius: 20px;
            padding: 48px 32px;
            text-align: center;
        }
    </style>
    """, unsafe_allow_html=True)

    # Total Count
    if '_apt_flash' not in st.session_state:
        st.session_state._apt_flash = None

    conn_count = get_connection()
    total_appts = 0
    if conn_count:
        _c = conn_count.cursor()
        _c.execute("SELECT COUNT(*) FROM appointments")
        total_appts = _c.fetchone()[0]
        _c.close()
        conn_count.close()

    st.markdown(f"""
    <div class="page-header">
        <div class="ph-left">
            <div class="ph-icon">
                <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="1.8">
                    <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
                    <line x1="16" y1="2" x2="16" y2="6"/>
                    <line x1="8" y1="2" x2="8" y2="6"/>
                    <line x1="3" y1="10" x2="21" y2="10"/>
                </svg>
            </div>
            <div>
                <p class="ph-title">Appointment Management</p>
                <p class="ph-subtitle">Schedule, view, edit and manage clinic appointments</p>
            </div>
        </div>
        <div class="ph-badge">{total_appts:,} total appointments</div>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state._apt_flash:
        st.success(st.session_state._apt_flash)
        st.session_state._apt_flash = None

    tab1, tab2, tab3, tab4 = st.tabs(["Schedule New", "View All", "Edit", "Delete"])

    # ========== TAB 1 - SCHEDULE ==========
    with tab1:
        conn = get_connection()
        if not conn:
            st.error("Database connection failed.")
            return
        cursor = conn.cursor()
        cursor.execute("SELECT patient_id, name FROM patients ORDER BY name")
        patients = cursor.fetchall()
        cursor.close()
        conn.close()

        if not patients:
            st.warning("No patients registered yet. Please add a patient first.")
            return

        p_dict = {name: pid for pid, name in patients}

        st.markdown('<div class="sec-label"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#E88C30" stroke-width="2"><circle cx="10" cy="10" r="7"/><line x1="21" y1="21" x2="15" y2="15"/></svg> Find Patient</div>', unsafe_allow_html=True)
        sc1, sc2 = st.columns([2, 3])
        with sc1:
            search_sched = st.text_input("Search", placeholder="Type name to filter...", label_visibility="collapsed", key="schedule_search")
        with sc2:
            filtered_sched = [n for n in p_dict if search_sched.lower() in n.lower()] if search_sched else list(p_dict)
            patient_name_sched = st.selectbox("Select", filtered_sched, label_visibility="collapsed", key="schedule_patient")

        patient_id_sched = p_dict.get(patient_name_sched)

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COALESCE(SUM(expected_cost),0) FROM appointments WHERE patient_id=%s", (patient_id_sched,))
        total_cost = cursor.fetchone()[0]
        cursor.execute("SELECT COALESCE(SUM(amount_paid),0) FROM payments WHERE patient_id=%s", (patient_id_sched,))
        total_paid = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        owed = total_cost - total_paid

        if owed > 0:
            bal_cls, bal_txt = "owed", f"Outstanding: UGX {owed:,.0f}"
            bal_ico_svg = "<svg width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='#B5670F' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'><path d='M12 9v4'/><path d='M12 17h.01'/><path d='M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z'/></svg>"
        elif owed < 0:
            bal_cls, bal_txt = "credit", f"Credit: UGX {abs(owed):,.0f}"
            bal_ico_svg = "<svg width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='#1E4A76' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'><path d='M20 6 9 17l-5-5'/></svg>"
        else:
            bal_cls, bal_txt = "neutral", "No outstanding balance"
            bal_ico_svg = "<svg width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='#1E4A76' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'><circle cx='12' cy='12' r='10'/></svg>"

        st.markdown(f'<div class="bal-strip {bal_cls}">{bal_ico_svg} {esc(patient_name_sched)} · {bal_txt}</div>', unsafe_allow_html=True)

        st.markdown('<div class="sec-label"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#E88C30" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg> Appointment Details</div>', unsafe_allow_html=True)
        with st.form("schedule_form"):
            col1, col2 = st.columns(2)
            with col1:
                app_date = st.date_input("Date *", value=datetime.now().date())
                app_time_val = st.time_input("Time *", value=time(9, 0))
                dentist = st.text_input("Dentist *", placeholder="e.g. Dr. Nakato")
                treatment = st.text_input("Treatment *", placeholder="e.g. Tooth Extraction")
            with col2:
                expected_cost = st.number_input("Expected Cost (UGX)", min_value=0, value=0, step=1000)
                # Options match label_encoders.pkl's APPT_TYPE_STANDARDIZE classes exactly
                # (['Follow-up', 'New', 'Others']) so the no-show predictor encodes a real,
                # known category instead of an unlabeled value silently falling into "Others".
                app_type = st.selectbox("Appointment Type", ["New", "Follow-up", "Others"])
                visit_type = st.selectbox("Visit Type", ["Appointment", "Walk-in"])
                status = st.selectbox("Status", ["Scheduled", "Completed", "No-show", "Cancelled"])

            if st.form_submit_button("Schedule Appointment", use_container_width=True):
                if not dentist or not treatment:
                    st.error("Dentist and Treatment fields are required.")
                else:
                    conn = get_connection()
                    if conn:
                        cursor = conn.cursor()
                        cursor.execute("""
                            INSERT INTO appointments (patient_id, appointment_date, appointment_time, dentist, treatment,
                                 expected_cost, appointment_type, visit_type, status)
                            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                            RETURNING appointment_id
                        """, (patient_id_sched, app_date, app_time_val, dentist, treatment,
                              expected_cost, app_type, visit_type, status))
                        new_appt_id = cursor.fetchone()[0]
                        conn.commit()
                        log_action("CREATE", table_name="appointments", record_id=new_appt_id,
                                   new_data={"dentist": dentist, "treatment": treatment, "status": status})
                        cursor.close()
                        conn.close()

                        flash_msg = f"Appointment scheduled successfully for {patient_name_sched}."

                        # If this appointment is being recorded as already Completed
                        # (e.g. a walk-in logged after the fact), reduce stock now.
                        if status == "Completed":
                            inv_result = auto_reduce_inventory(treatment)
                            if not inv_result["success"]:
                                flash_msg += " Inventory was NOT updated: " + "; ".join(inv_result["errors"])
                            elif inv_result["warnings"]:
                                flash_msg += " Inventory updated with warnings: " + "; ".join(inv_result["warnings"])
                            elif inv_result["reductions"]:
                                used_summary = ", ".join(f"{r['item']} -{r['used']}" for r in inv_result["reductions"])
                                flash_msg += f" Inventory reduced: {used_summary}."

                        st.session_state._apt_flash = flash_msg
                        st.rerun()

    # ========== TAB 2 - VIEW ALL ==========
    with tab2:
        st.markdown('<div class="sec-label"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#E88C30" stroke-width="2"><polygon points="22 3 22 15 16 15 16 21 2 21 2 3 22 3"/><line x1="10" y1="9" x2="18" y2="9"/><line x1="10" y1="13" x2="18" y2="13"/><line x1="10" y1="17" x2="14" y2="17"/></svg> Search & Filter</div>', unsafe_allow_html=True)
        fc1, fc2, fc3 = st.columns(3)
        with fc1:
            search_patient_v = st.text_input("Patient", placeholder="Patient name...", label_visibility="collapsed", key="view_patient")
        with fc2:
            search_dentist_v = st.text_input("Dentist", placeholder="Dentist name...", label_visibility="collapsed", key="view_dentist")
        with fc3:
            status_filter_v = st.selectbox("Status", ["All", "Scheduled", "Completed", "No-show", "Cancelled"], label_visibility="collapsed", key="view_status")

        conn = get_connection()
        if not conn:
            st.error("Database connection failed.")
            return
        query = """
            SELECT a.appointment_id, p.name, a.appointment_date, a.appointment_time,
                   a.dentist, a.treatment, a.expected_cost, a.status
            FROM appointments a JOIN patients p ON a.patient_id = p.patient_id WHERE 1=1
        """
        params = []
        if search_patient_v:
            query += " AND p.name ILIKE %s"
            params.append(f"%{search_patient_v}%")
        if search_dentist_v:
            query += " AND a.dentist ILIKE %s"
            params.append(f"%{search_dentist_v}%")
        if status_filter_v != "All":
            query += " AND a.status = %s"
            params.append(status_filter_v)
        query += " ORDER BY a.appointment_date DESC, a.appointment_time DESC"
        cursor = conn.cursor()
        cursor.execute(query, params)
        appointments = cursor.fetchall()
        cursor.close()
        conn.close()

        if appointments:
            status_badge = {
                "scheduled": "badge-scheduled",
                "completed": "badge-completed",
                "no-show": "badge-noshow",
                "cancelled": "badge-cancelled",
            }
            rows = ""
            for app in appointments:
                a_id, a_patient, a_date, a_time, a_dentist, a_treat, a_cost, a_status = app
                a_patient, a_dentist, a_treat = esc(a_patient), esc(a_dentist), esc(a_treat)
                status_cls = status_badge.get((a_status or "").lower(), "badge-scheduled")
                cost_html = f'<span class="apt-cost">UGX {a_cost:,.0f}</span>' if a_cost is not None else '<span class="apt-dash">—</span>'
                status_html = f'<span class="badge-status {status_cls}">{a_status}</span>' if a_status else '<span class="apt-dash">—</span>'
                rows += f"""
                <tr>
                    <td><span class="apt-id">#{a_id}</span></td>
                    <td><span class="apt-patient">{a_patient}</span></td>
                    <td><span class="apt-date">{str(a_date)}</span></td>
                    <td><span class="apt-date">{str(a_time)[:5]}</span></td>
                    <td><span class="apt-dentist">{a_dentist}</span></td>
                    <td>{a_treat}</td>
                    <td>{cost_html}</td>
                    <td>{status_html}</td>
                </tr>"""

            st.markdown(f"""
            <div class="apt-table-wrap">
                <table class="apt-table">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Patient</th>
                            <th>Date</th>
                            <th>Time</th>
                            <th>Dentist</th>
                            <th>Treatment</th>
                            <th>Cost</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>{rows}</tbody>
                </table>
                <div class="apt-table-footer">{len(appointments)} record{'s' if len(appointments) != 1 else ''} found</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="empty-state">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#B0C8E8" stroke-width="1.5">
                    <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>
                </svg>
                <p style="font-size:16px;font-weight:600;color:#1A3A5C;margin-top:16px;">No appointments found</p>
                <p style="font-size:13px;color:#6B8FAB;">Try adjusting your search or filter criteria.</p>
            </div>
            """, unsafe_allow_html=True)

    # ========== TAB 3 - EDIT ==========
    with tab3:
        conn = get_connection()
        if not conn:
            st.error("Database connection failed.")
            return
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.appointment_id, p.name, a.appointment_date, a.appointment_time,
                   a.dentist, a.treatment, a.expected_cost, a.status
            FROM appointments a JOIN patients p ON a.patient_id = p.patient_id
            ORDER BY a.appointment_date DESC
        """)
        app_list = cursor.fetchall()
        cursor.close()
        conn.close()

        if not app_list:
            st.info("No appointments to edit.")
            return

        st.markdown('<div class="sec-label"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#E88C30" stroke-width="2"><circle cx="10" cy="10" r="7"/><line x1="21" y1="21" x2="15" y2="15"/></svg> Find Appointment</div>', unsafe_allow_html=True)
        ec1, ec2 = st.columns([2, 3])
        with ec1:
            edit_search = st.text_input("Search", placeholder="Search patient name...", label_visibility="collapsed", key="edit_search_patient")
        with ec2:
            opts_full = [f"ID {a[0]} · {a[1]} · {str(a[2])} · {a[4]}" for a in app_list]
            opts_filt = [o for o, a in zip(opts_full, app_list) if edit_search.lower() in a[1].lower()] if edit_search else opts_full
            selected_edit = st.selectbox("Select", opts_filt, label_visibility="collapsed", key="edit_select")

        try:
            app_id_edit = int(selected_edit.split("·")[0].replace("ID", "").strip())
        except:
            st.error("Invalid selection.")
            return

        sel = next((a for a in app_list if a[0] == app_id_edit), None)
        if not sel:
            st.error("Appointment not found.")
            return

        _, pat_name_e, app_date_e, app_time_e, dentist_e, treatment_e, cost_e, status_e = sel

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT patient_id, name FROM patients ORDER BY name")
        patients_e = cursor.fetchall()
        cursor.close()
        conn.close()
        p_dict_e = {name: pid for pid, name in patients_e}
        p_names_e = list(p_dict_e.keys())
        curr_idx = p_names_e.index(pat_name_e) if pat_name_e in p_names_e else 0

        with st.form("edit_form"):
            col1, col2 = st.columns(2)
            with col1:
                new_patient = st.selectbox("Patient", p_names_e, index=curr_idx)
                new_date = st.date_input("Date", value=app_date_e)
                new_time = st.time_input("Time", value=app_time_e)
                new_dentist = st.text_input("Dentist", value=dentist_e)
            with col2:
                new_treatment = st.text_input("Treatment", value=treatment_e)
                new_cost = st.number_input("Cost (UGX)", min_value=0, value=int(cost_e or 0), step=1000)
                st_opts = ["Scheduled", "Completed", "No-show", "Cancelled"]
                new_status = st.selectbox("Status", st_opts, index=st_opts.index(status_e) if status_e in st_opts else 0)

            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("Save Changes", use_container_width=True):
                    conn = get_connection()
                    if conn:
                        cursor = conn.cursor()
                        cursor.execute("""
                            UPDATE appointments SET patient_id=%s, appointment_date=%s, appointment_time=%s,
                                dentist=%s, treatment=%s, expected_cost=%s, status=%s WHERE appointment_id=%s
                        """, (p_dict_e[new_patient], new_date, new_time, new_dentist, new_treatment, new_cost, new_status, app_id_edit))
                        conn.commit()
                        log_action("UPDATE", table_name="appointments", record_id=app_id_edit,
                                   old_data={"status": status_e}, new_data={"status": new_status, "treatment": new_treatment})
                        cursor.close()
                        conn.close()

                        flash_msg = "Appointment updated successfully!"

                        # Only reduce stock on the transition INTO "Completed".
                        # If it was already Completed before this edit, do nothing —
                        # otherwise re-saving an already-completed appointment would
                        # deduct inventory a second time for the same treatment.
                        if new_status == "Completed" and status_e != "Completed":
                            inv_result = auto_reduce_inventory(new_treatment)
                            if not inv_result["success"]:
                                flash_msg += " Inventory was NOT updated: " + "; ".join(inv_result["errors"])
                            elif inv_result["warnings"]:
                                flash_msg += " Inventory updated with warnings: " + "; ".join(inv_result["warnings"])
                            elif inv_result["reductions"]:
                                used_summary = ", ".join(f"{r['item']} -{r['used']}" for r in inv_result["reductions"])
                                flash_msg += f" Inventory reduced: {used_summary}."

                        st.session_state._apt_flash = flash_msg
                        st.rerun()
            with col2:
                if st.form_submit_button("Cancel", use_container_width=True):
                    st.rerun()

    # ========== TAB 4 - DELETE ==========
    with tab4:
        conn = get_connection()
        if not conn:
            st.error("Database connection failed.")
            return
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.appointment_id, p.name, a.appointment_date, a.dentist, a.treatment, a.status
            FROM appointments a JOIN patients p ON a.patient_id = p.patient_id
            ORDER BY a.appointment_date DESC
        """)
        del_list = cursor.fetchall()
        cursor.close()
        conn.close()

        if not del_list:
            st.info("No appointments to delete.")
            return

        st.markdown('<div class="sec-label"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#E88C30" stroke-width="2"><circle cx="10" cy="10" r="7"/><line x1="21" y1="21" x2="15" y2="15"/></svg> Find Appointment</div>', unsafe_allow_html=True)
        dc1, dc2 = st.columns([2, 3])
        with dc1:
            del_search = st.text_input("Search", placeholder="Search patient name...", label_visibility="collapsed", key="delete_search")
        with dc2:
            d_opts_full = [f"ID {a[0]} · {a[1]} · {str(a[2])} · {a[3]}" for a in del_list]
            d_opts_filt = [o for o, a in zip(d_opts_full, del_list) if del_search.lower() in a[1].lower()] if del_search else d_opts_full
            selected_del = st.selectbox("Select", d_opts_filt, label_visibility="collapsed", key="delete_select")

        try:
            del_id = int(selected_del.split("·")[0].replace("ID", "").strip())
        except:
            st.error("Invalid selection.")
            return

        target = next((a for a in del_list if a[0] == del_id), None)
        if target:
            st.markdown(f"""
            <div class="delete-warn">
                <div class="delete-warn-title">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#B91C1C" stroke-width="1.8">
                        <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><circle cx="12" cy="16" r="0.5" fill="#B91C1C"/>
                    </svg>
                    Confirm deletion — this cannot be undone
                </div>
                <div class="delete-field">Patient: <span>{esc(target[1])}</span></div>
                <div class="delete-field">Date: <span>{target[2]}</span></div>
                <div class="delete-field">Dentist: <span>{esc(target[3])}</span></div>
                <div class="delete-field">Treatment: <span>{esc(target[4])}</span></div>
                <div class="delete-field">Status: <span>{target[5]}</span></div>
            </div>
            """, unsafe_allow_html=True)

            if st.button("Delete Appointment Permanently", use_container_width=True, key="confirm_delete_btn"):
                conn = get_connection()
                if conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM appointments WHERE appointment_id = %s", (del_id,))
                    conn.commit()
                    log_action("DELETE", table_name="appointments", record_id=del_id,
                               old_data={"patient": target[1], "treatment": target[4], "status": target[5]})
                    cursor.close()
                    conn.close()
                    st.session_state._apt_flash = f"Appointment ID {del_id} deleted successfully."
                    st.rerun()