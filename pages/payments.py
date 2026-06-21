# pages/payments.py
import streamlit as st
import pandas as pd
import re
from datetime import datetime
from utils.db import get_connection
from utils.sanitize import esc
from utils.audit import log_action


def show_payments():
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

        /* ── BALANCE CARD ── */
        .balance-card {
            border-radius: 20px;
            padding: 24px;
            margin-bottom: 24px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .balance-card.owed   { background: #FDEBD3; border: 1.5px solid #F5BC6A; }
        .balance-card.clear  { background: #DBEAFE; border: 1.5px solid #93C5FD; }
        .balance-card.credit { background: #EEF4FB; border: 1.5px solid #B5D4F4; }
        .bal-left { display: flex; align-items: center; gap: 16px; }
        .bal-icon {
            width: 52px; height: 52px;
            border-radius: 16px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .bal-amount { font-size: 28px; font-weight: 800; margin: 0 0 4px; }
        .bal-label { font-size: 12px; font-weight: 500; margin: 0; color: #4B7FA8; }
        .bal-owed-clr { color: #B5670F; }
        .bal-clear-clr { color: #1E4A76; }
        .bal-credit-clr { color: #1E4A76; }
        .bal-tag {
            font-size: 11px;
            font-weight: 700;
            padding: 6px 14px;
            border-radius: 30px;
        }
        .tag-amber { background: #F5BC6A; color: #7A3E0A; }
        .tag-blue  { background: #1E4A76; color: #fff; }

        /* ── PREVIEW STRIP ── */
        .preview-strip {
            background: #EEF4FB;
            border: 1.5px solid #D6E6F5;
            border-radius: 14px;
            padding: 14px 18px;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 13px;
            font-weight: 600;
            color: #1E4A76;
        }

        /* ── INPUT FIELDS ── */
        .stTextInput label, .stSelectbox label, .stDateInput label, .stNumberInput label {
            font-size: 12px !important;
            font-weight: 600 !important;
            color: #1A3A5C !important;
            letter-spacing: 0.1px !important;
        }
        .stTextInput input, .stDateInput input, .stNumberInput > div > div > input {
            border: 1.5px solid #E2E8F0 !important;
            border-radius: 12px !important;
            font-size: 14px !important;
            color: #1A3A5C !important;
            background: #F8FAFD !important;
            padding: 12px 16px !important;
            transition: border-color 0.15s, box-shadow 0.15s !important;
        }
        .stTextInput input:focus, .stDateInput input:focus {
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
        .stFormSubmitButton, .stButton { width: 100% !important; }
        .stFormSubmitButton button, .stButton button {
            background: linear-gradient(135deg, #1E4A76, #2D6A9F) !important;
            border: none !important;
            border-radius: 12px !important;
            padding: 0 22px !important;
            height: 46px !important;
            min-height: 46px !important;
            line-height: 46px !important;
            font-weight: 600 !important;
            font-size: 14px !important;
            color: #fff !important;
            box-shadow: 0 2px 10px rgba(30,74,118,0.2) !important;
            transition: all 0.2s ease !important;
            width: 100% !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
        }
        .stFormSubmitButton button:hover, .stButton button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 16px rgba(30,74,118,0.25) !important;
        }
        .stFormSubmitButton button:active, .stButton button:active {
            transform: translateY(0) !important;
        }

        /* Danger / delete-style button */
        .danger-btn-wrap .stButton button {
            background: #fff !important;
            color: #B91C1C !important;
            border: 1.5px solid #FECACA !important;
            box-shadow: none !important;
        }
        .danger-btn-wrap .stButton button:hover {
            background: #FEF2F2 !important;
            box-shadow: 0 4px 12px rgba(185,28,28,0.12) !important;
        }
        .confirm-btn-wrap .stButton button {
            background: linear-gradient(135deg, #B91C1C, #DC2626) !important;
            box-shadow: 0 2px 10px rgba(185,28,28,0.25) !important;
        }
        .confirm-btn-wrap .stButton button:hover {
            box-shadow: 0 6px 16px rgba(185,28,28,0.32) !important;
        }
        .cancel-btn-wrap .stButton button {
            background: #fff !important;
            color: #6B8FAB !important;
            border: 1.5px solid #E2E8F0 !important;
            box-shadow: none !important;
        }
        .cancel-btn-wrap .stButton button:hover {
            background: #F5F8FC !important;
            box-shadow: none !important;
            transform: none !important;
        }

        /* ── ACTION BAR (Edit/Delete tab button row) ── */
        .action-bar-spacer { height: 14px; }
        /* Equal-height, equal-gap button row for confirm/cancel pairs */
        div[data-testid="column"] { display: flex !important; flex-direction: column !important; justify-content: flex-end !important; }
        div[data-testid="stHorizontalBlock"] { gap: 12px !important; align-items: stretch !important; }

        /* ── STAT TILES ── */
        .stat-tile {
            background: #fff;
            border: 1.5px solid #E2E8F0;
            border-radius: 16px;
            padding: 18px;
            text-align: center;
            box-shadow: 0 2px 8px rgba(30,74,118,0.04);
        }
        .st-val { font-size: 20px; font-weight: 800; color: #1E4A76; }
        .st-lbl { font-size: 11px; color: #6B8FAB; font-weight: 600; margin-top: 4px; }

        /* ── PAYMENT HISTORY TABLE ── */
        .pay-table-wrap {
            background: #fff;
            border-radius: 18px;
            border: 1.5px solid #E2E8F0;
            overflow: hidden;
            box-shadow: 0 4px 20px rgba(30,74,118,0.07);
            margin-top: 4px;
        }
        .pay-table { width: 100%; border-collapse: collapse; }
        .pay-table thead tr { background: linear-gradient(135deg, #1E4A76 0%, #2D6A9F 100%); }
        .pay-table thead th {
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
        .pay-table tbody tr {
            border-bottom: 1px solid #F0F5FA;
            transition: background 0.12s ease;
        }
        .pay-table tbody tr:last-child { border-bottom: none; }
        .pay-table tbody tr:hover { background: #F7FAFD; }
        .pay-table tbody td {
            padding: 13px 18px;
            vertical-align: middle;
            border: none;
            font-size: 13.5px;
            color: #2D4A6B;
        }
        .pay-id {
            display: inline-flex; align-items: center;
            background: #EEF4FB; color: #2D6A9F;
            font-size: 11px; font-weight: 700;
            padding: 4px 10px; border-radius: 8px;
        }
        .pay-date { font-size: 12.5px; color: #6B8FAB; font-weight: 500; white-space: nowrap; }
        .pay-patient { font-weight: 600; color: #1A3A5C; }
        .pay-amount { font-weight: 700; color: #1E4A76; }
        .pay-balance-due { font-weight: 700; color: #B5670F; }
        .pay-balance-clear { font-weight: 700; color: #1E4A76; }
        .pay-method {
            display: inline-block; font-size: 11.5px; font-weight: 600;
            color: #2D6A9F; background: #EEF4FB;
            padding: 3px 10px; border-radius: 8px;
        }
        .pay-dash { color: #CBD5E1; }
        .pay-table-footer {
            padding: 11px 18px;
            background: #F8FAFD;
            border-top: 1px solid #E2E8F0;
            font-size: 12px;
            color: #6B8FAB;
            font-weight: 600;
        }
        .caption-text { font-size: 12px; color: #6B8FAB; margin-top: 12px; font-weight: 500; }

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
    if '_pay_flash' not in st.session_state:
        st.session_state._pay_flash = None

    conn_count = get_connection()
    total_payments = 0
    if conn_count:
        _c = conn_count.cursor()
        _c.execute("SELECT COUNT(*) FROM payments")
        total_payments = _c.fetchone()[0]
        _c.close()
        conn_count.close()

    st.markdown(f"""
    <div class="page-header">
        <div class="ph-left">
            <div class="ph-icon">
                <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="1.8">
                    <rect x="1" y="4" width="22" height="16" rx="2" ry="2"/>
                    <line x1="1" y1="10" x2="23" y2="10"/>
                </svg>
            </div>
            <div>
                <p class="ph-title">Payment Management</p>
                <p class="ph-subtitle">Record, view, edit and delete patient payments</p>
            </div>
        </div>
        <div class="ph-badge">{total_payments:,} payments recorded</div>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state._pay_flash:
        st.success(st.session_state._pay_flash)
        st.session_state._pay_flash = None

    tab1, tab2, tab3 = st.tabs(["Record Payment", "Payment History", "Edit / Delete"])

    # ========== TAB 1 - RECORD PAYMENT ==========
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
            st.warning("No patients found. Please register a patient first.")
            return

        patient_dict = {name: pid for pid, name in patients}

        st.markdown('<div class="sec-label"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#E88C30" stroke-width="2"><circle cx="10" cy="10" r="7"/><line x1="21" y1="21" x2="15" y2="15"/></svg> Find Patient</div>', unsafe_allow_html=True)
        sc1, sc2 = st.columns([2, 3])
        with sc1:
            pay_search = st.text_input("Search", placeholder="Type name to filter...", label_visibility="collapsed", key="pay_search")
        with sc2:
            pay_names = list(patient_dict.keys())
            pay_filt = [n for n in pay_names if pay_search.lower() in n.lower()] if pay_search else pay_names
            patient_name = st.selectbox("Select", pay_filt, label_visibility="collapsed", key="pay_select")

        patient_id = patient_dict[patient_name]
        patient_name_safe = esc(patient_name)

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COALESCE(SUM(expected_cost),0) FROM appointments WHERE patient_id=%s", (patient_id,))
        total_cost = cursor.fetchone()[0]
        cursor.execute("SELECT COALESCE(SUM(amount_paid),0) FROM payments WHERE patient_id=%s", (patient_id,))
        total_paid = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        current_balance = total_cost - total_paid

        if current_balance > 0:
            st.markdown(f"""
            <div class="balance-card owed">
                <div class="bal-left">
                    <div class="bal-icon" style="background:#F5BC6A;">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#7A3E0A" stroke-width="1.8">
                            <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><circle cx="12" cy="16" r="0.5" fill="#7A3E0A"/>
                        </svg>
                    </div>
                    <div>
                        <p class="bal-amount bal-owed-clr">UGX {current_balance:,.0f}</p>
                        <p class="bal-label">Amount owed by {patient_name_safe}</p>
                    </div>
                </div>
                <div class="bal-tag tag-amber">Unpaid</div>
            </div>
            """, unsafe_allow_html=True)
        elif current_balance == 0:
            st.markdown(f"""
            <div class="balance-card clear">
                <div class="bal-left">
                    <div class="bal-icon" style="background:#DBEAFE;">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#1E4A76" stroke-width="1.8">
                            <path d="M20 6L9 17l-5-5"/>
                        </svg>
                    </div>
                    <div>
                        <p class="bal-amount bal-clear-clr">UGX 0</p>
                        <p class="bal-label">{patient_name_safe} is fully paid up</p>
                    </div>
                </div>
                <div class="bal-tag tag-blue">Settled</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="balance-card credit">
                <div class="bal-left">
                    <div class="bal-icon" style="background:#EEF4FB;">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#1E4A76" stroke-width="1.8">
                            <circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>
                        </svg>
                    </div>
                    <div>
                        <p class="bal-amount bal-credit-clr">UGX {abs(current_balance):,.0f}</p>
                        <p class="bal-label">{patient_name_safe} has a credit (overpaid)</p>
                    </div>
                </div>
                <div class="bal-tag tag-blue">Credit</div>
            </div>
            """, unsafe_allow_html=True)

        if current_balance > 0:
            with st.form("payment_form"):
                col1, col2 = st.columns(2)
                with col1:
                    amount_paid = st.number_input("Amount Paid (UGX)", min_value=0, max_value=int(current_balance), value=0, step=10000)
                    payment_date = st.date_input("Payment Date", value=datetime.now().date())
                    payment_method = st.selectbox("Payment Method", ["Cash", "Mobile Money", "Bank Transfer", "Card", "Other"])
                with col2:
                    new_balance = current_balance - amount_paid
                    st.markdown(f"""
                    <div class="preview-strip">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#E88C30" stroke-width="1.8">
                            <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="16"/><line x1="8" y1="12" x2="16" y2="12"/>
                        </svg>
                        After this payment: <strong>UGX {new_balance:,.0f}</strong> remaining
                    </div>
                    """, unsafe_allow_html=True)

                if st.form_submit_button("Record Payment", use_container_width=True):
                    if amount_paid <= 0:
                        st.error("Please enter an amount greater than zero.")
                    else:
                        conn = get_connection()
                        if conn:
                            cursor = conn.cursor()
                            cursor.execute("""
                                INSERT INTO payments (patient_id, amount_paid, balance, payment_date, payment_method)
                                VALUES (%s, %s, %s, %s, %s)
                                RETURNING payment_id
                            """, (patient_id, amount_paid, new_balance, payment_date, payment_method))
                            new_payment_id = cursor.fetchone()[0]
                            conn.commit()
                            log_action("CREATE", table_name="payments", record_id=new_payment_id,
                                       new_data={"amount_paid": float(amount_paid), "method": payment_method})
                            cursor.close()
                            conn.close()
                            st.session_state._pay_flash = f"Payment of UGX {amount_paid:,.0f} recorded for {patient_name}."
                            st.rerun()
        else:
            st.markdown("""
            <div class="empty-state">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#1E4A76" stroke-width="1.5">
                    <path d="M20 6L9 17l-5-5"/>
                </svg>
                <p style="font-size:16px;font-weight:600;color:#1A3A5C;margin-top:16px;">No payment needed</p>
                <p style="font-size:13px;color:#6B8FAB;">This patient has no outstanding balance.</p>
            </div>
            """, unsafe_allow_html=True)

    # ========== TAB 2 - PAYMENT HISTORY ==========
    with tab2:
        st.markdown('<div class="sec-label"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#E88C30" stroke-width="2"><polygon points="22 3 22 15 16 15 16 21 2 21 2 3 22 3"/></svg> Search Payments</div>', unsafe_allow_html=True)
        hist_search = st.text_input("Search", placeholder="Search by patient name...", label_visibility="collapsed", key="hist_search")

        conn = get_connection()
        if not conn:
            st.error("Database connection failed.")
            return
        cursor = conn.cursor()
        query = """
            SELECT p.payment_id, TO_CHAR(p.payment_date,'YYYY-MM-DD'), pt.name, p.amount_paid, p.balance, p.payment_method
            FROM payments p JOIN patients pt ON p.patient_id = pt.patient_id WHERE 1=1
        """
        params = []
        if hist_search:
            query += " AND pt.name ILIKE %s"
            params.append(f"%{hist_search}%")
        query += " ORDER BY p.payment_date DESC, p.payment_id DESC"
        cursor.execute(query, params)
        payments = cursor.fetchall()
        cursor.close()
        conn.close()

        if payments:
            rows = ""
            for pmt in payments:
                p_id, p_date, p_patient, p_amount, p_balance, p_method = pmt
                p_patient = esc(p_patient)
                amount_html = f'<span class="pay-amount">UGX {p_amount:,.0f}</span>' if p_amount is not None else '<span class="pay-dash">—</span>'
                if p_balance is not None:
                    bal_cls = "pay-balance-due" if p_balance > 0 else "pay-balance-clear"
                    balance_html = f'<span class="{bal_cls}">UGX {abs(p_balance):,.0f}{" (credit)" if p_balance < 0 else ""}</span>'
                else:
                    balance_html = '<span class="pay-dash">—</span>'
                method_html = f'<span class="pay-method">{p_method}</span>' if p_method else '<span class="pay-dash">—</span>'
                rows += f"""
                <tr>
                    <td><span class="pay-id">#{p_id}</span></td>
                    <td><span class="pay-date">{p_date}</span></td>
                    <td><span class="pay-patient">{p_patient}</span></td>
                    <td>{amount_html}</td>
                    <td>{balance_html}</td>
                    <td>{method_html}</td>
                </tr>"""

            st.markdown(f"""
            <div class="pay-table-wrap">
                <table class="pay-table">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Date</th>
                            <th>Patient</th>
                            <th>Amount</th>
                            <th>Balance</th>
                            <th>Method</th>
                        </tr>
                    </thead>
                    <tbody>{rows}</tbody>
                </table>
                <div class="pay-table-footer">{len(payments)} payment{'s' if len(payments) != 1 else ''} found</div>
            </div>
            """, unsafe_allow_html=True)

            total_collected = sum(p[3] for p in payments)
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f'<div class="stat-tile"><div class="st-val">UGX {total_collected:,.0f}</div><div class="st-lbl">Total Displayed</div></div>', unsafe_allow_html=True)
            with c2:
                st.markdown(f'<div class="stat-tile"><div class="st-val">{len(payments)}</div><div class="st-lbl">Transactions</div></div>', unsafe_allow_html=True)
            with c3:
                avg_payment = total_collected // len(payments) if payments else 0
                st.markdown(f'<div class="stat-tile"><div class="st-val">UGX {avg_payment:,.0f}</div><div class="st-lbl">Avg Payment</div></div>', unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="empty-state">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#B0C8E8" stroke-width="1.5">
                    <rect x="1" y="4" width="22" height="16" rx="2" ry="2"/><line x1="1" y1="10" x2="23" y2="10"/>
                </svg>
                <p style="font-size:16px;font-weight:600;color:#1A3A5C;margin-top:16px;">No payments found</p>
                <p style="font-size:13px;color:#6B8FAB;">{"No results for &quot;" + hist_search + "&quot;" if hist_search else "No payment records yet."}</p>
            </div>
            """, unsafe_allow_html=True)

    # ========== TAB 3 - EDIT/DELETE ==========
    with tab3:
        conn = get_connection()
        if not conn:
            st.error("Database connection failed.")
            return
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.payment_id, pt.name, TO_CHAR(p.payment_date,'YYYY-MM-DD'), p.amount_paid, p.balance, p.payment_method
            FROM payments p JOIN patients pt ON p.patient_id = pt.patient_id
            ORDER BY p.payment_date DESC
        """)
        all_payments = cursor.fetchall()
        cursor.close()
        conn.close()

        if not all_payments:
            st.markdown('<div class="empty-state"><p style="font-size:16px;font-weight:600;color:#1A3A5C;">No payment records found.</p></div>', unsafe_allow_html=True)
            return

        st.markdown('<div class="sec-label"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#E88C30" stroke-width="2"><circle cx="10" cy="10" r="7"/><line x1="21" y1="21" x2="15" y2="15"/></svg> Find Payment Record</div>', unsafe_allow_html=True)
        ed1, ed2 = st.columns([2, 3])
        with ed1:
            edit_search = st.text_input("Search", placeholder="Search patient name...", label_visibility="collapsed", key="ed_pay_search")
        with ed2:
            opts_full = [f"ID {p[0]} · {p[1]} · {p[2]} · UGX {p[3]:,.0f}" for p in all_payments]
            opts_filt = [o for o, p in zip(opts_full, all_payments) if edit_search.lower() in p[1].lower()] if edit_search else opts_full
            selected = st.selectbox("Select", opts_filt, label_visibility="collapsed", key="ed_pay_select")

        match = re.search(r'ID (\d+)', selected)
        if not match:
            st.error("Invalid selection.")
            return

        payment_id = int(match.group(1))
        sel = next((p for p in all_payments if p[0] == payment_id), None)
        if not sel:
            st.error("Payment not found.")
            return

        _, pat_name, pay_date, pay_amount, pay_balance, pay_method = sel
        pat_name = esc(pat_name)

        st.markdown(f"""
        <div class="preview-strip">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#E88C30" stroke-width="1.8">
                <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><circle cx="12" cy="16" r="0.5" fill="#E88C30"/>
            </svg>
            Selected: <strong>{pat_name}</strong> · {pay_date} · <strong>UGX {pay_amount:,.0f}</strong> via {pay_method}
        </div>
        """, unsafe_allow_html=True)

        with st.form("edit_payment_form"):
            col1, col2 = st.columns(2)
            with col1:
                new_amount = st.number_input("Amount Paid (UGX)", min_value=0, value=int(pay_amount), step=10000)
                new_date = st.date_input("Payment Date", value=datetime.strptime(pay_date, '%Y-%m-%d').date())
            with col2:
                methods = ["Cash", "Mobile Money", "Bank Transfer", "Card", "Other"]
                new_method = st.selectbox("Payment Method", methods, index=methods.index(pay_method) if pay_method in methods else 0)

            st.markdown('<div class="action-bar-spacer"></div>', unsafe_allow_html=True)
            save_changes = st.form_submit_button("Save Changes", use_container_width=True)
            if save_changes:
                conn = get_connection()
                if conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE payments SET amount_paid=%s, payment_date=%s, payment_method=%s WHERE payment_id=%s", (new_amount, new_date, new_method, payment_id))
                    conn.commit()
                    log_action("UPDATE", table_name="payments", record_id=payment_id,
                               new_data={"amount_paid": float(new_amount), "method": new_method})
                    cursor.close()
                    conn.close()
                    st.session_state._pay_flash = "Payment updated successfully."
                    st.rerun()

        # ── Danger zone: delete this payment ──
        st.markdown('<div class="sec-label" style="margin-top:24px;"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#D32F2F" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><circle cx="12" cy="16" r="0.5" fill="#D32F2F"/></svg> Danger Zone</div>', unsafe_allow_html=True)

        if not st.session_state.get('confirm_del_payment'):
            st.markdown('<div class="danger-btn-wrap">', unsafe_allow_html=True)
            if st.button("🗑  Delete This Payment", use_container_width=True, key="del_pay_btn"):
                st.session_state['confirm_del_payment'] = payment_id
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        if st.session_state.get('confirm_del_payment') == payment_id:
            st.markdown(f"""
            <div class="delete-warn">
                <div class="delete-warn-title">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#B91C1C" stroke-width="1.8">
                        <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><circle cx="12" cy="16" r="0.5" fill="#B91C1C"/>
                    </svg>
                    Confirm deletion — this cannot be undone
                </div>
                <div class="delete-field">Patient: <span>{pat_name}</span></div>
                <div class="delete-field">Date: <span>{pay_date}</span></div>
                <div class="delete-field">Amount: <span>UGX {pay_amount:,.0f}</span></div>
                <div class="delete-field">Method: <span>{pay_method}</span></div>
            </div>
            """, unsafe_allow_html=True)
            dc1, dc2 = st.columns(2, gap="small")
            with dc1:
                st.markdown('<div class="confirm-btn-wrap">', unsafe_allow_html=True)
                if st.button("✓  Yes, Delete", use_container_width=True, key="confirm_del_pay_yes"):
                    conn = get_connection()
                    if conn:
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM payments WHERE payment_id=%s", (payment_id,))
                        conn.commit()
                        log_action("DELETE", table_name="payments", record_id=payment_id,
                                   old_data={"patient": pat_name, "amount": float(pay_amount)})
                        cursor.close()
                        conn.close()
                        st.session_state.pop('confirm_del_payment', None)
                        st.session_state._pay_flash = "Payment deleted successfully."
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            with dc2:
                st.markdown('<div class="cancel-btn-wrap">', unsafe_allow_html=True)
                if st.button("✕  Cancel", use_container_width=True, key="cancel_del_pay"):
                    st.session_state.pop('confirm_del_payment', None)
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)