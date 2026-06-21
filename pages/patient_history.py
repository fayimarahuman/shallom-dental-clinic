# pages/patient_history.py
import streamlit as st
import pandas as pd
from utils.db import get_connection
from utils.sanitize import esc
from utils.audit import log_action


def show_patient_history():
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

        /* ── Ghost box / form chrome removal ── */
        hr { display: none !important; }
        [data-testid="stForm"],
        [data-testid="stVerticalBlockBorderWrapper"],
        [data-testid="stVerticalBlockBorderWrapper"] > div {
            border: none !important; padding: 0 !important;
            background: transparent !important; box-shadow: none !important; outline: none !important;
        }
        .element-container:empty,
        [data-testid="stVerticalBlock"] > div:empty,
        [data-testid="stForm"] > div:empty { display: none !important; }
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

        /* ── SECTION LABELS ── */
        .sec-label {
            font-size: 11px;
            font-weight: 700;
            color: #6B8FAB;
            letter-spacing: 1.2px;
            text-transform: uppercase;
            margin: 24px 0 14px 4px;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        /* ── PATIENT PROFILE CARD ── */
        .profile-card {
            background: #fff;
            border: 1.5px solid #E2E8F0;
            border-radius: 20px;
            padding: 24px;
            margin: 16px 0;
            display: flex;
            gap: 20px;
            box-shadow: 0 2px 12px rgba(30,74,118,0.05);
        }
        .profile-avatar {
            width: 56px; height: 56px;
            background: linear-gradient(135deg, #1E4A76, #2D6A9F);
            border-radius: 18px;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
            box-shadow: 0 4px 12px rgba(30,74,118,0.2);
        }
        .profile-name { font-size: 18px; font-weight: 700; color: #1A3A5C; margin: 0 0 8px; }
        .profile-grid { display: flex; flex-wrap: wrap; gap: 20px; margin-top: 8px; }
        .pf-item { min-width: 120px; }
        .pf-label { font-size: 10px; font-weight: 700; color: #6B8FAB; letter-spacing: 0.6px; text-transform: uppercase; margin-bottom: 4px; }
        .pf-val { font-size: 14px; font-weight: 600; color: #1A3A5C; }

        /* ── STAT TILES ── */
        .stat-tile {
            background: #fff;
            border: 1.5px solid #E2E8F0;
            border-radius: 16px;
            padding: 16px;
            text-align: center;
            transition: all 0.2s ease;
            box-shadow: 0 2px 8px rgba(30,74,118,0.04);
        }
        .stat-tile:hover { transform: translateY(-3px); box-shadow: 0 6px 16px rgba(30,74,118,0.1); }
        .st-val { font-size: 22px; font-weight: 800; color: #1E4A76; margin: 0 0 4px; }
        .st-lbl { font-size: 11px; color: #6B8FAB; margin: 0; font-weight: 600; letter-spacing: 0.2px; }
        .st-red { color: #B91C1C !important; }
        .st-green { color: #15803D !important; }

        /* ── INPUTS ── */
        .stTextInput label, .stSelectbox label {
            font-size: 12px !important; font-weight: 600 !important;
            color: #1A3A5C !important; letter-spacing: 0.1px !important;
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
            border-radius: 12px !important;
            padding: 11px 20px !important;
            font-weight: 600 !important;
            font-size: 13.5px !important;
            color: #fff !important;
            box-shadow: 0 2px 10px rgba(30,74,118,0.2) !important;
            transition: all 0.2s ease !important;
        }
        .stButton button:hover { transform: translateY(-2px); box-shadow: 0 6px 16px rgba(30,74,118,0.25) !important; }

        .caption-text { font-size: 12px; color: #6B8FAB; margin-top: 8px; margin-bottom: 4px; font-weight: 500; }

        /* ── MODERN RECORD TABLES (appointments / payments) ── */
        .rec-table-wrap {
            background: #fff;
            border-radius: 18px;
            border: 1.5px solid #E2E8F0;
            overflow: hidden;
            box-shadow: 0 4px 20px rgba(30,74,118,0.07);
            margin-top: 4px;
        }
        .rec-table { width: 100%; border-collapse: collapse; }
        .rec-table thead tr { background: linear-gradient(135deg, #1E4A76 0%, #2D6A9F 100%); }
        .rec-table thead th {
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
        .rec-table tbody tr {
            border-bottom: 1px solid #F0F5FA;
            transition: background 0.12s ease;
        }
        .rec-table tbody tr:last-child { border-bottom: none; }
        .rec-table tbody tr:hover { background: #F7FAFD; }
        .rec-table tbody td {
            padding: 13px 18px;
            vertical-align: middle;
            border: none;
            font-size: 13.5px;
            color: #2D4A6B;
        }
        .rec-id {
            display: inline-flex; align-items: center;
            background: #EEF4FB; color: #2D6A9F;
            font-size: 11px; font-weight: 700;
            padding: 4px 10px; border-radius: 8px;
        }
        .rec-date { font-size: 12.5px; color: #6B8FAB; font-weight: 500; white-space: nowrap; }
        .rec-strong { font-weight: 600; color: #1A3A5C; }
        .rec-cost { font-weight: 700; color: #1E4A76; }
        .rec-amount { font-weight: 700; color: #15803D; }
        .rec-balance-due { font-weight: 700; color: #B91C1C; }
        .rec-balance-clear { font-weight: 700; color: #15803D; }
        .badge-status {
            display: inline-block; font-size: 11px; font-weight: 700;
            padding: 4px 12px; border-radius: 20px; letter-spacing: 0.2px;
            text-transform: capitalize;
        }
        .badge-completed, .badge-paid { background: #DBEAFE; color: #1E4A76; }
        .badge-pending, .badge-scheduled { background: #FDEBD3; color: #B5670F; }
        .badge-cancelled { background: #E2E8F0; color: #1A3A5C; }
        .badge-default { background: #EEF4FB; color: #2D6A9F; }
        .rec-method {
            display: inline-block; font-size: 11.5px; font-weight: 600;
            color: #2D6A9F; background: #EEF4FB;
            padding: 3px 10px; border-radius: 8px;
        }
        .rec-dash { color: #CBD5E1; }
        .rec-table-footer {
            padding: 11px 18px;
            background: #F8FAFD;
            border-top: 1px solid #E2E8F0;
            font-size: 12px;
            color: #6B8FAB;
            font-weight: 600;
        }

        /* ── DANGER ZONE ── */
        .delete-warn, .danger-card {
            background: #FEF2F2;
            border: 1.5px solid #FECACA;
            border-radius: 16px;
            padding: 20px 24px;
            margin: 16px 0;
        }
        .delete-warn-title, .danger-title {
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
        .danger-text { font-size: 13px; color: #B91C1C; margin: 0; line-height: 1.5; }

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

    st.markdown("""
    <div class="page-header">
        <div class="ph-left">
            <div class="ph-icon">
                <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="1.8">
                    <path d="M12 8v4l3 3M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z"/>
                    <path d="M12 6v6"/>
                </svg>
            </div>
            <div>
                <p class="ph-title">Patient History</p>
                <p class="ph-subtitle">View appointment and payment records per patient</p>
            </div>
        </div>
        <div class="ph-badge">Full clinical record</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Flash message (survives st.rerun()) ──────────────────────────────────
    if '_ph_flash' not in st.session_state:
        st.session_state._ph_flash = None
    if st.session_state._ph_flash:
        st.success(st.session_state._ph_flash)
        st.session_state._ph_flash = None

    # Session state init
    for k, v in [('show_appointment_delete', False), ('appointment_to_delete', None), ('show_clear_history', False)]:
        if k not in st.session_state:
            st.session_state[k] = v

    # Fetch patients
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
        st.markdown("""
        <div class="empty-state">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#B0C8E8" stroke-width="1.5">
                <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><circle cx="12" cy="16" r="0.5" fill="#B0C8E8"/>
            </svg>
            <p style="font-size:16px;font-weight:600;color:#1A3A5C;margin-top:16px;">No patients found</p>
            <p style="font-size:13px;color:#6B8FAB;">Please register patients first.</p>
        </div>
        """, unsafe_allow_html=True)
        return

    patient_dict = {name: pid for pid, name in patients}

    # Patient search
    st.markdown('<div class="sec-label" style="margin-top:0;"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#E88C30" stroke-width="2"><circle cx="10" cy="10" r="7"/><line x1="21" y1="21" x2="15" y2="15"/></svg> Find Patient</div>', unsafe_allow_html=True)
    sc1, sc2 = st.columns([2, 3])
    with sc1:
        ph_search = st.text_input("Search", placeholder="Type name to filter...", label_visibility="collapsed", key="ph_search")
    with sc2:
        ph_names = list(patient_dict.keys())
        ph_filt = [n for n in ph_names if ph_search.lower() in n.lower()] if ph_search else ph_names
        selected_patient = st.selectbox("Select", ph_filt, label_visibility="collapsed", key="ph_select")

    patient_id = patient_dict[selected_patient]

    # Patient profile
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM patients WHERE patient_id=%s", (patient_id,))
    patient = cursor.fetchone()

    if patient:
        p_name  = esc(patient[1])
        p_phone = esc(patient[2] or '—')
        p_email = esc(patient[3] or '—')
        p_gender = esc(patient[4] or '—')
        p_loc   = esc(patient[6] or '—')
        age_val = f"{patient[5]} yrs" if patient[5] else "—"
        st.markdown(f"""
        <div class="profile-card">
            <div class="profile-avatar">
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="1.8">
                    <circle cx="12" cy="12" r="10"/><path d="M12 10a3 3 0 1 0 0-6 3 3 0 0 0 0 6z"/><path d="M12 14a7 7 0 0 0-7 7h14a7 7 0 0 0-7-7z"/>
                </svg>
            </div>
            <div style="flex:1;">
                <p class="profile-name">{p_name}</p>
                <div class="profile-grid">
                    <div class="pf-item"><div class="pf-label">Phone</div><div class="pf-val">{p_phone}</div></div>
                    <div class="pf-item"><div class="pf-label">Email</div><div class="pf-val">{p_email}</div></div>
                    <div class="pf-item"><div class="pf-label">Gender</div><div class="pf-val">{p_gender}</div></div>
                    <div class="pf-item"><div class="pf-label">Age</div><div class="pf-val">{age_val}</div></div>
                    <div class="pf-item"><div class="pf-label">Location</div><div class="pf-val">{p_loc}</div></div>
                    <div class="pf-item"><div class="pf-label">Patient ID</div><div class="pf-val">#{patient[0]}</div></div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ========== APPOINTMENTS ==========
    st.markdown('<div class="sec-label"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#E88C30" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg> Appointment History</div>', unsafe_allow_html=True)

    cursor.execute("""
        SELECT appointment_id, appointment_date, TO_CHAR(appointment_time, 'HH12:MI AM'),
               dentist, treatment, expected_cost, status
        FROM appointments WHERE patient_id=%s
        ORDER BY appointment_date DESC, appointment_time DESC
    """, (patient_id,))
    appointments = cursor.fetchall()

    if appointments:
        status_badge = {
            "completed": "badge-completed",
            "pending": "badge-pending",
            "scheduled": "badge-scheduled",
            "cancelled": "badge-cancelled",
        }
        rows = ""
        for a in appointments:
            a_id, a_date, a_time, a_dentist, a_treat, a_cost, a_status = a
            status_cls = status_badge.get((a_status or "").lower(), "badge-default")
            cost_html = f'<span class="rec-cost">UGX {a_cost:,.0f}</span>' if a_cost is not None else '<span class="rec-dash">—</span>'
            status_html = f'<span class="badge-status {status_cls}">{esc(a_status)}</span>' if a_status else '<span class="rec-dash">—</span>'
            rows += f"""
            <tr>
                <td><span class="rec-id">#{a_id}</span></td>
                <td><span class="rec-date">{a_date}</span></td>
                <td><span class="rec-date">{a_time or '—'}</span></td>
                <td><span class="rec-strong">{esc(a_dentist or '—')}</span></td>
                <td>{esc(a_treat or '—')}</td>
                <td>{cost_html}</td>
                <td>{status_html}</td>
            </tr>"""

        st.markdown(f"""
        <div class="rec-table-wrap">
            <table class="rec-table">
                <thead>
                    <tr>
                        <th>ID</th>
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
            <div class="rec-table-footer">{len(appointments)} appointment{'s' if len(appointments) != 1 else ''} on record</div>
        </div>
        """, unsafe_allow_html=True)

        # Delete single appointment
        # Options embed the real appointment_id so the selector is unambiguous
        # even when two rows share the same date/time/treatment text.
        st.markdown('<div class="sec-label"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#D32F2F" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><circle cx="12" cy="16" r="0.5" fill="#D32F2F"/></svg> Delete an Appointment</div>', unsafe_allow_html=True)
        da1, da2 = st.columns([3, 1])
        with da1:
            # Format: "ID #42 · 2024-01-15 · 09:00 AM · Cleaning"
            app_options = [f"ID #{a[0]} · {a[1]} · {a[2]} · {a[4] or '—'}" for a in appointments]
            selected_app_str = st.selectbox("Select", app_options, label_visibility="collapsed", key="del_app_select")
        with da2:
            if st.button("Delete Selected", use_container_width=True, key="del_app_btn"):
                # Extract the appointment_id directly from the label — no fragile index lookup
                selected_app_id = int(selected_app_str.split("ID #")[1].split(" ·")[0])
                st.session_state.appointment_to_delete = selected_app_id
                st.session_state.show_appointment_delete = True
                st.rerun()

        if st.session_state.show_appointment_delete and st.session_state.appointment_to_delete:
            app_id = st.session_state.appointment_to_delete
            app_det = next((a for a in appointments if a[0] == app_id), None)
            if app_det:
                st.markdown(f"""
                <div class="delete-warn">
                    <div class="delete-warn-title">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#D32F2F" stroke-width="1.8">
                            <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><circle cx="12" cy="16" r="0.5" fill="#D32F2F"/>
                        </svg>
                        Confirm deletion — this cannot be undone
                    </div>
                    <div class="delete-field">Date: <span>{esc(str(app_det[1]))}</span></div>
                    <div class="delete-field">Treatment: <span>{esc(app_det[4] or '—')}</span></div>
                    <div class="delete-field">Dentist: <span>{esc(app_det[3] or '—')}</span></div>
                </div>
                """, unsafe_allow_html=True)
                dc1, dc2 = st.columns(2)
                with dc1:
                    if st.button("Yes, Delete Appointment", use_container_width=True, key="confirm_app_del"):
                        conn2 = get_connection()
                        if conn2:
                            cur2 = conn2.cursor()
                            try:
                                cur2.execute("DELETE FROM appointments WHERE appointment_id=%s", (app_id,))
                                conn2.commit()
                                log_action("DELETE", table_name="appointments", record_id=app_id,
                                           old_data={"treatment": app_det[4], "dentist": app_det[3]})
                                st.session_state._ph_flash = "Appointment deleted successfully."
                                st.session_state.show_appointment_delete = False
                                st.session_state.appointment_to_delete = None
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")
                            finally:
                                cur2.close()
                                conn2.close()
                with dc2:
                    if st.button("Cancel", use_container_width=True, key="cancel_app_del"):
                        st.session_state.show_appointment_delete = False
                        st.session_state.appointment_to_delete = None
                        st.rerun()
    else:
        st.markdown("""
        <div class="empty-state">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#B0C8E8" stroke-width="1.5">
                <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>
            </svg>
            <p style="font-size:16px;font-weight:600;color:#1A3A5C;margin-top:16px;">No appointment history</p>
            <p style="font-size:13px;color:#6B8FAB;">This patient has no recorded appointments.</p>
        </div>
        """, unsafe_allow_html=True)

    # ========== PAYMENTS ==========
    st.markdown('<div class="sec-label"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#E88C30" stroke-width="2"><rect x="1" y="4" width="22" height="16" rx="2" ry="2"/><line x1="1" y1="10" x2="23" y2="10"/></svg> Payment History</div>', unsafe_allow_html=True)

    cursor.execute("""
        SELECT payment_id, payment_date, amount_paid, balance, payment_method
        FROM payments WHERE patient_id=%s ORDER BY payment_date DESC
    """, (patient_id,))
    payments = cursor.fetchall()
    cursor.close()
    conn.close()

    if payments:
        rows = ""
        for pmt in payments:
            p_id, p_date, p_amount, p_balance, p_method = pmt
            amount_html = f'<span class="rec-amount">UGX {p_amount:,.0f}</span>' if p_amount is not None else '<span class="rec-dash">—</span>'
            if p_balance is not None:
                bal_cls = "rec-balance-due" if p_balance > 0 else "rec-balance-clear"
                balance_html = f'<span class="{bal_cls}">UGX {abs(p_balance):,.0f}{" (credit)" if p_balance < 0 else ""}</span>'
            else:
                balance_html = '<span class="rec-dash">—</span>'
            method_html = f'<span class="rec-method">{esc(p_method)}</span>' if p_method else '<span class="rec-dash">—</span>'
            rows += f"""
            <tr>
                <td><span class="rec-id">#{p_id}</span></td>
                <td><span class="rec-date">{p_date}</span></td>
                <td>{amount_html}</td>
                <td>{balance_html}</td>
                <td>{method_html}</td>
            </tr>"""

        st.markdown(f"""
        <div class="rec-table-wrap">
            <table class="rec-table">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Date</th>
                        <th>Amount Paid</th>
                        <th>Balance</th>
                        <th>Method</th>
                    </tr>
                </thead>
                <tbody>{rows}</tbody>
            </table>
            <div class="rec-table-footer">{len(payments)} transaction{'s' if len(payments) != 1 else ''} on record</div>
        </div>
        """, unsafe_allow_html=True)

        # Summary stats
        total_paid = sum(p[2] for p in payments)
        conn2 = get_connection()
        cur2 = conn2.cursor()
        cur2.execute("SELECT COALESCE(SUM(expected_cost),0) FROM appointments WHERE patient_id=%s", (patient_id,))
        total_cost = cur2.fetchone()[0]
        cur2.close()
        conn2.close()
        balance = total_cost - total_paid
        bal_display = f"UGX {abs(balance):,.0f}" + (" (credit)" if balance < 0 else "")

        t1, t2, t3, t4 = st.columns(4)
        with t1:
            st.markdown(f'<div class="stat-tile"><div class="st-val">UGX {total_paid:,.0f}</div><div class="st-lbl">Total Paid</div></div>', unsafe_allow_html=True)
        with t2:
            st.markdown(f'<div class="stat-tile"><div class="st-val">UGX {total_cost:,.0f}</div><div class="st-lbl">Treatment Cost</div></div>', unsafe_allow_html=True)
        with t3:
            color_class = "st-red" if balance > 0 else "st-green"
            st.markdown(f'<div class="stat-tile"><div class="st-val {color_class}">{bal_display}</div><div class="st-lbl">Balance</div></div>', unsafe_allow_html=True)
        with t4:
            st.markdown(f'<div class="stat-tile"><div class="st-val">{len(payments)}</div><div class="st-lbl">Transactions</div></div>', unsafe_allow_html=True)

        # Danger zone
        st.markdown('<div class="sec-label"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#D32F2F" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><circle cx="12" cy="16" r="0.5" fill="#D32F2F"/></svg> Danger Zone</div>', unsafe_allow_html=True)

        if not st.session_state.show_clear_history:
            if st.button("Clear All History for This Patient", use_container_width=True, key="clear_hist_btn"):
                st.session_state.show_clear_history = True
                st.rerun()
        else:
            st.markdown(f"""
            <div class="danger-card">
                <div class="danger-title">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#D32F2F" stroke-width="1.8">
                        <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><circle cx="12" cy="16" r="0.5" fill="#D32F2F"/>
                    </svg>
                    Warning — this cannot be undone
                </div>
                <div class="danger-text">
                    You are about to permanently delete <strong>all appointments and payment records</strong>
                    for <strong>{esc(selected_patient)}</strong>. The patient profile will remain but all history will be erased.
                </div>
            </div>
            """, unsafe_allow_html=True)
            cc1, cc2 = st.columns(2)
            with cc1:
                if st.button("Yes, Clear All History", use_container_width=True, key="confirm_clear_hist"):
                    conn3 = get_connection()
                    if conn3:
                        cur3 = conn3.cursor()
                        try:
                            cur3.execute("DELETE FROM payments WHERE patient_id=%s", (patient_id,))
                            p_del = cur3.rowcount
                            cur3.execute("DELETE FROM appointments WHERE patient_id=%s", (patient_id,))
                            a_del = cur3.rowcount
                            conn3.commit()
                            log_action("DELETE", table_name="patients", record_id=patient_id,
                                       old_data={"patient": selected_patient},
                                       error_message=f"Cleared history: {a_del} appointment(s), {p_del} payment(s) removed")
                            st.session_state._ph_flash = f"History cleared: {a_del} appointment(s) and {p_del} payment(s) removed."
                            st.session_state.show_clear_history = False
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error clearing history: {e}")
                        finally:
                            cur3.close()
                            conn3.close()
            with cc2:
                if st.button("Cancel", use_container_width=True, key="cancel_clear_hist"):
                    st.session_state.show_clear_history = False
                    st.rerun()
    else:
        st.markdown("""
        <div class="empty-state">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#B0C8E8" stroke-width="1.5">
                <rect x="1" y="4" width="22" height="16" rx="2" ry="2"/><line x1="1" y1="10" x2="23" y2="10"/>
            </svg>
            <p style="font-size:16px;font-weight:600;color:#1A3A5C;margin-top:16px;">No payment history</p>
            <p style="font-size:13px;color:#6B8FAB;">No payments have been recorded for this patient.</p>
        </div>
        """, unsafe_allow_html=True)