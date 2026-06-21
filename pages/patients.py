# pages/patients.py
import streamlit as st
import pandas as pd
import re
from utils.db import get_connection
from utils.sanitize import esc
from utils.audit import log_action


def show_patients():
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

        /* ── Form card ── */
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
            border-radius: 20px; padding: 28px 32px; margin-bottom: 24px;
            display: flex; align-items: center; justify-content: space-between;
            box-shadow: 0 8px 32px rgba(30,74,118,0.18);
            position: relative; overflow: hidden;
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
            width: 54px; height: 54px; background: rgba(255,255,255,0.12);
            border-radius: 16px; display: flex; align-items: center; justify-content: center;
            border: 1px solid rgba(255,255,255,0.2); flex-shrink: 0;
        }
        .ph-title { color: #fff; font-size: 22px; font-weight: 800; margin: 0 0 4px; letter-spacing: -0.3px; }
        .ph-subtitle { color: rgba(255,255,255,0.6); font-size: 13px; margin: 0; }
        .ph-badge {
            background: rgba(232,140,48,0.2); border: 1px solid rgba(232,140,48,0.4);
            color: #F5BC6A; font-size: 12px; font-weight: 700;
            padding: 8px 20px; border-radius: 40px; z-index: 1; letter-spacing: 0.2px;
        }

        /* ── TABS ── */
        .stTabs [data-baseweb="tab-list"] {
            background: #fff !important; border-radius: 16px !important;
            border: 1.5px solid #E2E8F0 !important; padding: 6px 8px !important;
            gap: 4px !important; margin-bottom: 24px !important;
            box-shadow: 0 2px 8px rgba(30,74,118,0.06) !important;
        }
        .stTabs [data-baseweb="tab"] {
            border-radius: 12px !important; font-size: 13.5px !important;
            font-weight: 500 !important; color: #6B8FAB !important;
            padding: 10px 26px !important; transition: color 0.15s !important;
        }
        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, #1E4A76, #2D6A9F) !important;
            color: #fff !important; font-weight: 600 !important;
            box-shadow: 0 2px 10px rgba(30,74,118,0.2) !important;
        }
        .stTabs [data-baseweb="tab-highlight"],
        .stTabs [data-baseweb="tab-border"] { display: none !important; }

        /* ── SECTION LABELS ── */
        .sec-label {
            font-size: 11px; font-weight: 700; color: #6B8FAB;
            letter-spacing: 1.3px; text-transform: uppercase;
            margin: 0 0 14px 2px; display: flex; align-items: center; gap: 8px;
        }
        .sec-label::before {
            content: ''; display: inline-block; width: 3px; height: 14px;
            background: linear-gradient(180deg, #E88C30, #F5BC6A);
            border-radius: 2px; flex-shrink: 0;
        }

        /* ── INPUT FIELDS ── */
        .stTextInput label, .stSelectbox label, .stNumberInput label {
            font-size: 12px !important; font-weight: 600 !important;
            color: #1A3A5C !important; letter-spacing: 0.1px !important;
        }
        .stTextInput input, .stNumberInput > div > div > input {
            border: 1.5px solid #E2E8F0 !important; border-radius: 12px !important;
            font-size: 14px !important; color: #1A3A5C !important;
            background: #F8FAFD !important; padding: 12px 16px !important;
            transition: border-color 0.15s, box-shadow 0.15s !important;
        }
        .stTextInput input:focus {
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
        /* Target every possible node BaseUI uses to render the selected value */
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
        /* Dropdown option list */
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
            border: none !important; border-radius: 12px !important;
            padding: 12px 24px !important; font-weight: 600 !important;
            font-size: 14px !important; color: #fff !important;
            box-shadow: 0 2px 10px rgba(30,74,118,0.2) !important;
            transition: all 0.2s ease !important;
        }
        .stFormSubmitButton button:hover, .stButton button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 18px rgba(30,74,118,0.28) !important;
        }

        /* ── PATIENT RECORDS TABLE ── */
        .pt-table-wrap {
            background: #fff;
            border-radius: 20px;
            border: 1.5px solid #E2E8F0;
            overflow: hidden;
            box-shadow: 0 4px 24px rgba(30,74,118,0.08);
        }
        .pt-table {
            width: 100%;
            border-collapse: collapse;
        }
        /* Header */
        .pt-table thead tr {
            background: linear-gradient(135deg, #1E4A76 0%, #2D6A9F 100%);
        }
        .pt-table thead th {
            padding: 14px 20px;
            text-align: left;
            font-size: 10.5px;
            font-weight: 700;
            letter-spacing: 1.2px;
            text-transform: uppercase;
            color: rgba(255,255,255,0.75);
            white-space: nowrap;
            border: none;
        }
        .pt-table thead th:first-child { border-radius: 0; }
        /* Body rows */
        .pt-table tbody tr {
            border-bottom: 1px solid #F0F5FA;
            transition: background 0.12s ease;
        }
        .pt-table tbody tr:last-child { border-bottom: none; }
        .pt-table tbody tr:hover { background: #F7FAFD; }
        .pt-table tbody td {
            padding: 14px 20px;
            vertical-align: middle;
            border: none;
        }
        /* Cell styles */
        .cell-id {
            display: inline-flex; align-items: center;
            background: #EEF4FB; color: #2D6A9F;
            font-size: 11px; font-weight: 700;
            padding: 4px 10px; border-radius: 8px;
            letter-spacing: 0.3px;
        }
        .cell-name {
            font-size: 14px; font-weight: 600; color: #1A3A5C;
            display: block; line-height: 1.3;
        }
        .cell-phone {
            font-size: 13px; color: #2D6A9F; font-weight: 500;
        }
        .cell-email {
            font-size: 12.5px; color: #7A9BB5; max-width: 180px;
            overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
            display: block;
        }
        .badge {
            display: inline-block; font-size: 11px; font-weight: 700;
            padding: 4px 12px; border-radius: 20px; letter-spacing: 0.2px;
        }
        .badge-male   { background: #DBEAFE; color: #1E4A76; }
        .badge-female { background: #FDEBD3; color: #B5670F; }
        .badge-other  { background: #E2E8F0; color: #1A3A5C; }
        .cell-age {
            display: inline-flex; align-items: center; justify-content: center;
            background: #F0F5FA; color: #1A3A5C;
            font-size: 13px; font-weight: 700;
            width: 40px; height: 30px; border-radius: 8px;
        }
        .cell-location {
            font-size: 13px; color: #4B7FA8; font-weight: 500;
        }
        .cell-location-icon { color: #E88C30; margin-right: 4px; }
        .cell-date {
            font-size: 12px; color: #94A3B8; white-space: nowrap;
        }
        .cell-dash { color: #CBD5E1; font-size: 16px; }
        /* Table footer */
        .pt-table-footer {
            padding: 12px 20px;
            background: #F8FAFD;
            border-top: 1px solid #E2E8F0;
            display: flex; align-items: center; justify-content: space-between;
        }
        .pt-table-footer-count {
            font-size: 12.5px; font-weight: 600; color: #6B8FAB;
        }
        .pt-table-footer-hint {
            font-size: 11.5px; color: #B0C4D8;
        }

        /* ── DELETE WARNING ── */
        .delete-warn {
            background: #FEF2F2; border: 1.5px solid #FECACA;
            border-radius: 16px; padding: 20px 24px; margin: 20px 0;
        }
        .delete-warn-title {
            font-size: 14px; font-weight: 700; color: #B91C1C;
            margin-bottom: 12px; display: flex; align-items: center; gap: 8px;
        }
        .delete-field { font-size: 13px; color: #1A3A5C; margin-bottom: 6px; }
        .delete-field span { font-weight: 600; color: #1E4A76; }
        .delete-note { font-size: 12px; color: #DC2626; margin-top: 10px; font-style: italic; }

        /* ── EMPTY STATE ── */
        .empty-state {
            background: #fff; border: 1.5px dashed #CBD5E1;
            border-radius: 20px; padding: 52px 32px; text-align: center;
        }
    </style>
    """, unsafe_allow_html=True)

    if 'confirm_delete_patient' not in st.session_state:
        st.session_state.confirm_delete_patient = None
    if '_pt_flash' not in st.session_state:
        st.session_state._pt_flash = None

    conn = get_connection()
    total = 0
    if conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM patients")
        total = cur.fetchone()[0]
        cur.close()
        conn.close()

    st.markdown(f"""
    <div class="page-header">
        <div class="ph-left">
            <div class="ph-icon">
                <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="1.8">
                    <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/>
                </svg>
            </div>
            <div>
                <p class="ph-title">Patient Management</p>
                <p class="ph-subtitle">Register, search and manage patient records</p>
            </div>
        </div>
        <div class="ph-badge">{total:,} patients registered</div>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state._pt_flash:
        st.success(st.session_state._pt_flash)
        st.session_state._pt_flash = None

    tab1, tab2, tab3 = st.tabs(["Register", "Records", "Edit / Delete"])

    # ========== TAB 1 - REGISTER ==========
    with tab1:
        st.markdown('<div class="sec-label">New Patient Details</div>', unsafe_allow_html=True)
        with st.form("register_form"):
            col1, col2 = st.columns(2)
            with col1:
                name     = st.text_input("Full Name *", placeholder="e.g. Sarah Nakato")
                phone    = st.text_input("Phone", placeholder="e.g. 0701 234 567")
                age      = st.number_input("Age", min_value=0, max_value=120, step=1, value=0)
            with col2:
                email    = st.text_input("Email", placeholder="Leave blank if not available")
                gender   = st.selectbox("Gender", ["Male", "Female", "Other"])
                location = st.text_input("Location", placeholder="e.g. Kampala, Ntinda")

            if st.form_submit_button("Register Patient", use_container_width=True):
                if not name.strip():
                    st.error("Full name is required.")
                else:
                    conn = get_connection()
                    if conn:
                        cur = conn.cursor()
                        if email.strip():
                            cur.execute("SELECT COUNT(*) FROM patients WHERE email = %s", (email.strip(),))
                            if cur.fetchone()[0] > 0:
                                st.warning("A patient with this email already exists.")
                                cur.close(); conn.close(); st.stop()
                        try:
                            cur.execute("""
                                INSERT INTO patients (name, phone, email, gender, age, location)
                                VALUES (%s, %s, %s, %s, %s, %s)
                                RETURNING patient_id
                            """, (
                                name.strip(),
                                phone.strip() or None,
                                email.strip() or None,
                                gender,
                                age if age > 0 else None,
                                location.strip() or None
                            ))
                            new_patient_id = cur.fetchone()[0]
                            conn.commit()
                            log_action("CREATE", table_name="patients", record_id=new_patient_id,
                                       new_data={"name": name.strip(), "phone": phone.strip(),
                                                 "email": email.strip(), "gender": gender})
                            st.session_state._pt_flash = f"Patient '{name.strip()}' registered successfully."
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error registering patient: {e}")
                        finally:
                            cur.close(); conn.close()

    # ========== TAB 2 - RECORDS ==========
    with tab2:
        st.markdown('<div class="sec-label">Search Patients</div>', unsafe_allow_html=True)
        search_term = st.text_input(
            "Search", placeholder="Search by name, phone, email or location...",
            label_visibility="collapsed", key="patient_search"
        )

        conn = get_connection()
        if conn:
            cur = conn.cursor()
            if search_term:
                cur.execute("""
                    SELECT patient_id, name, phone, email, gender, age, location,
                           TO_CHAR(created_at, 'DD Mon YYYY')
                    FROM patients
                    WHERE name ILIKE %s OR phone ILIKE %s OR email ILIKE %s OR location ILIKE %s
                    ORDER BY created_at DESC
                """, (f'%{search_term}%',) * 4)
            else:
                cur.execute("""
                    SELECT patient_id, name, phone, email, gender, age, location,
                           TO_CHAR(created_at, 'DD Mon YYYY')
                    FROM patients ORDER BY created_at DESC
                """)
            data = cur.fetchall()
            cur.close()
            conn.close()

            if data:
                badge_map = {
                    "Male":   "badge-male",
                    "Female": "badge-female",
                    "Other":  "badge-other",
                }
                rows = ""
                for row in data:
                    r_id, nm, ph, em, gn, ag, loc, reg = row
                    ph_html  = f'<span class="cell-phone">{ph}</span>'                          if ph  else '<span class="cell-dash">—</span>'
                    em_html  = f'<span class="cell-email" title="{em}">{em}</span>'             if em  else '<span class="cell-dash">—</span>'
                    gn_html  = f'<span class="badge {badge_map.get(gn,"badge-other")}">{gn}</span>' if gn else '<span class="cell-dash">—</span>'
                    ag_html  = f'<span class="cell-age">{ag}</span>'                            if ag  else '<span class="cell-dash">—</span>'
                    loc_html = f'<span class="cell-location">{loc}</span>' if loc else '<span class="cell-dash">—</span>'
                    rows += f"""
                    <tr>
                        <td><span class="cell-id">#{r_id}</span></td>
                        <td><span class="cell-name">{nm}</span></td>
                        <td>{ph_html}</td>
                        <td>{em_html}</td>
                        <td>{gn_html}</td>
                        <td>{ag_html}</td>
                        <td>{loc_html}</td>
                        <td><span class="cell-date">{reg or '—'}</span></td>
                    </tr>"""

                st.markdown(f"""
                <div class="pt-table-wrap">
                    <table class="pt-table">
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Patient Name</th>
                                <th>Phone</th>
                                <th>Email</th>
                                <th>Gender</th>
                                <th>Age</th>
                                <th>Location</th>
                                <th>Registered</th>
                            </tr>
                        </thead>
                        <tbody>{rows}</tbody>
                    </table>
                    <div class="pt-table-footer">
                        <span class="pt-table-footer-count">
                            {len(data)} patient{'s' if len(data) != 1 else ''} found
                        </span>
                        <span class="pt-table-footer-hint">Sorted by most recent</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            else:
                st.markdown(f"""
                <div class="empty-state">
                    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#B0C8E8" stroke-width="1.5">
                        <circle cx="12" cy="12" r="10"/>
                        <line x1="12" y1="8" x2="12" y2="12"/>
                        <circle cx="12" cy="16" r="0.5" fill="#B0C8E8"/>
                    </svg>
                    <p style="font-size:16px;font-weight:600;color:#1A3A5C;margin-top:16px;">No patients found</p>
                    <p style="font-size:13px;color:#6B8FAB;">{"No results for &quot;" + search_term + "&quot;" if search_term else "No patients registered yet."}</p>
                </div>
                """, unsafe_allow_html=True)

    # ========== TAB 3 - EDIT/DELETE ==========
    with tab3:
        conn = get_connection()
        if not conn:
            st.error("Database connection failed.")
            return
        cur = conn.cursor()
        cur.execute("SELECT patient_id, name FROM patients ORDER BY name")
        patients = cur.fetchall()
        cur.close()
        conn.close()

        if not patients:
            st.markdown('<div class="empty-state"><p style="font-size:16px;font-weight:600;color:#1A3A5C;">No patients available.</p></div>', unsafe_allow_html=True)
            return

        st.markdown('<div class="sec-label">Find Patient</div>', unsafe_allow_html=True)
        ec1, ec2 = st.columns([2, 3])
        with ec1:
            edit_search = st.text_input("Search", placeholder="Type name to filter...", label_visibility="collapsed", key="edit_search")
        with ec2:
            p_all  = [f"{p[1]} (ID {p[0]})" for p in patients]
            p_filt = [n for n in p_all if edit_search.lower() in n.lower()] if edit_search else p_all
            selected = st.selectbox("Select", p_filt if p_filt else p_all, label_visibility="collapsed", key="select_patient")

        pid = int(re.search(r'ID (\d+)', selected).group(1))

        conn = get_connection()
        cur  = conn.cursor()
        cur.execute("SELECT patient_id, name, phone, email, gender, age, location FROM patients WHERE patient_id = %s", (pid,))
        p = cur.fetchone()
        cur.close()
        conn.close()

        if not p:
            st.error("Patient not found.")
            return

        with st.form("edit_form"):
            col1, col2 = st.columns(2)
            with col1:
                new_name  = st.text_input("Full Name *", value=p[1])
                new_phone = st.text_input("Phone", value=p[2] or "")
                new_age   = st.number_input("Age", 0, 120, value=int(p[5]) if p[5] else 0)
            with col2:
                new_email    = st.text_input("Email", value=p[3] or "")
                new_location = st.text_input("Location", value=p[6] or "")
                genders      = ["Male", "Female", "Other"]
                new_gender   = st.selectbox("Gender", genders, index=genders.index(p[4]) if p[4] in genders else 0)

            col1, col2 = st.columns(2)
            with col1:
                save   = st.form_submit_button("Save Changes", use_container_width=True)
            with col2:
                delete = st.form_submit_button("Delete Patient", use_container_width=True)

            if save:
                if not new_name.strip():
                    st.error("Full name is required.")
                else:
                    conn = get_connection()
                    if conn:
                        cur = conn.cursor()
                        if new_email.strip():
                            cur.execute("SELECT COUNT(*) FROM patients WHERE email = %s AND patient_id != %s", (new_email.strip(), pid))
                            if cur.fetchone()[0] > 0:
                                st.warning("Another patient already has this email.")
                                cur.close(); conn.close(); st.stop()
                        try:
                            cur.execute("""
                                UPDATE patients
                                SET name=%s, phone=%s, email=%s, gender=%s, age=%s, location=%s
                                WHERE patient_id=%s
                            """, (
                                new_name.strip(),
                                new_phone.strip() or None,
                                new_email.strip() or None,
                                new_gender,
                                new_age if new_age > 0 else None,
                                new_location.strip() or None,
                                pid
                            ))
                            conn.commit()
                            log_action("UPDATE", table_name="patients", record_id=pid,
                                       new_data={"name": new_name.strip(), "phone": new_phone.strip(),
                                                 "email": new_email.strip(), "gender": new_gender})
                            st.session_state._pt_flash = f"Patient '{new_name.strip()}' updated successfully."
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error updating patient: {e}")
                        finally:
                            cur.close(); conn.close()

            if delete:
                st.session_state.confirm_delete_patient = pid

        if st.session_state.confirm_delete_patient == pid:
            conn = get_connection()
            cur  = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM appointments WHERE patient_id=%s", (pid,))
            appt_count = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM payments WHERE patient_id=%s", (pid,))
            pay_count  = cur.fetchone()[0]
            cur.close()
            conn.close()

            st.markdown(f"""
            <div class="delete-warn">
                <div class="delete-warn-title">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#B91C1C" stroke-width="1.8">
                        <circle cx="12" cy="12" r="10"/>
                        <line x1="12" y1="8" x2="12" y2="12"/>
                        <circle cx="12" cy="16" r="0.5" fill="#B91C1C"/>
                    </svg>
                    Confirm deletion — this cannot be undone
                </div>
                <div class="delete-field">Patient: <span>{p[1]}</span></div>
                <div class="delete-field">Linked appointments: <span>{appt_count}</span></div>
                <div class="delete-field">Linked payments: <span>{pay_count}</span></div>
                <div class="delete-note">All linked appointments and payments will also be permanently deleted.</div>
            </div>
            """, unsafe_allow_html=True)

            dc1, dc2 = st.columns(2)
            with dc1:
                if st.button("Yes, Delete Patient", use_container_width=True, key="confirm_del_pat"):
                    conn = get_connection()
                    if conn:
                        cur = conn.cursor()
                        try:
                            cur.execute("DELETE FROM payments WHERE patient_id = %s", (pid,))
                            cur.execute("DELETE FROM appointments WHERE patient_id = %s", (pid,))
                            cur.execute("DELETE FROM patients WHERE patient_id = %s", (pid,))
                            conn.commit()
                            log_action("DELETE", table_name="patients", record_id=pid,
                                       old_data={"name": p[1]},
                                       error_message=f"Cascade: {appt_count} appointment(s), {pay_count} payment(s) also removed")
                            st.session_state.confirm_delete_patient = None
                            st.session_state._pt_flash = f"Patient '{p[1]}' and all linked records deleted."
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error deleting patient: {e}")
                        finally:
                            cur.close(); conn.close()
            with dc2:
                if st.button("Cancel", use_container_width=True, key="cancel_del_pat"):
                    st.session_state.confirm_delete_patient = None
                    st.rerun()