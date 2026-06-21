# pages/audit_trail.py
import streamlit as st
import pandas as pd
from datetime import datetime
from utils.db import get_connection
from utils.sanitize import esc
from utils.permissions import can_view_page


def show_audit_trail():
    if not can_view_page(st.session_state.get('role'), 'Audit Trail'):
        st.error("Access Denied. Admin privileges required.")
        st.stop()

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

        /* ── Kill ALL ghost rectangles, hr lines, borders ── */
        hr,
        [data-testid="stForm"] hr,
        [data-testid="stVerticalBlock"] hr,
        .stMarkdown hr { display: none !important; border: none !important; height: 0 !important; }

        [data-testid="stVerticalBlockBorderWrapper"],
        [data-testid="stVerticalBlockBorderWrapper"] > div {
            border: none !important;
            padding: 0 !important;
            background: transparent !important;
            box-shadow: none !important;
            outline: none !important;
        }
        .element-container:empty,
        [data-testid="stVerticalBlock"] > div:empty { display: none !important; }

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
            display: flex; align-items: center; justify-content: center;
            border: 1px solid rgba(255,255,255,0.2);
            flex-shrink: 0;
        }
        .ph-title { color: #fff; font-size: 22px; font-weight: 800; margin: 0 0 4px; letter-spacing: -0.3px; }
        .ph-subtitle { color: rgba(255,255,255,0.65); font-size: 13px; margin: 0; }
        .ph-badge {
            background: rgba(232,140,48,0.2);
            border: 1px solid rgba(232,140,48,0.4);
            color: #F5BC6A;
            font-size: 12px; font-weight: 700;
            padding: 8px 20px; border-radius: 40px;
            z-index: 1; letter-spacing: 0.2px;
        }

        /* ── METRIC CARDS ── */
        [data-testid="stMetric"] {
            background: #fff !important;
            border: 1.5px solid #E2E8F0 !important;
            border-radius: 18px !important;
            padding: 20px 22px !important;
            box-shadow: 0 2px 10px rgba(30,74,118,0.05) !important;
        }
        [data-testid="stMetricLabel"] {
            font-size: 11px !important; font-weight: 700 !important;
            color: #6B8FAB !important; text-transform: uppercase !important;
            letter-spacing: 0.8px !important;
        }
        [data-testid="stMetricValue"] {
            font-size: 22px !important; font-weight: 800 !important;
            color: #1E4A76 !important; letter-spacing: -0.5px !important;
        }

        /* ── SECTION LABELS ── */
        .sec-label {
            font-size: 11px; font-weight: 700; color: #6B8FAB;
            letter-spacing: 1.2px; text-transform: uppercase;
            margin: 0 0 16px 2px;
            display: flex; align-items: center; gap: 8px;
        }

        /* ── SELECTBOX ── */
        .stSelectbox label, .stTextInput label {
            font-size: 12px !important; font-weight: 600 !important;
            color: #1A3A5C !important; letter-spacing: 0.1px !important;
        }
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
            font-size: 14px !important; color: #1A3A5C !important;
            padding: 10px 16px !important; font-family: 'Inter', sans-serif !important;
        }
        [data-baseweb="popover"] [aria-selected="true"],
        [data-baseweb="menu"] [aria-selected="true"],
        [role="option"]:hover {
            background: #EEF4FB !important; color: #1E4A76 !important; font-weight: 600 !important;
        }

        /* ── TEXT INPUT ── */
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

        /* ── BUTTON ── */
        .stButton button, .stDownloadButton button {
            background: linear-gradient(135deg, #1E4A76, #2D6A9F) !important;
            border: none !important; border-radius: 12px !important;
            padding: 12px 24px !important; font-weight: 600 !important;
            font-size: 14px !important; color: #fff !important;
            box-shadow: 0 2px 10px rgba(30,74,118,0.2) !important;
            transition: all 0.2s ease !important;
        }
        .stButton button:hover, .stDownloadButton button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 16px rgba(30,74,118,0.25) !important;
        }

        /* ── AUDIT TABLE ── */
        .audit-table-wrap {
            background: #fff;
            border-radius: 18px;
            border: 1.5px solid #E2E8F0;
            overflow: hidden;
            box-shadow: 0 4px 20px rgba(30,74,118,0.07);
            margin-top: 4px;
        }
        .audit-table { width: 100%; border-collapse: collapse; }
        .audit-table thead tr { background: linear-gradient(135deg, #1E4A76 0%, #2D6A9F 100%); }
        .audit-table thead th {
            padding: 13px 16px;
            text-align: left;
            font-size: 10.5px; font-weight: 700;
            letter-spacing: 1.1px; text-transform: uppercase;
            color: rgba(255,255,255,0.75);
            white-space: nowrap; border: none;
        }
        .audit-table tbody tr { border-bottom: 1px solid #F0F5FA; transition: background 0.12s ease; }
        .audit-table tbody tr:last-child { border-bottom: none; }
        .audit-table tbody tr:hover { background: #F7FAFD; }
        .audit-table tbody td {
            padding: 12px 16px; vertical-align: middle; border: none;
            font-size: 13px; color: #2D4A6B;
        }
        .audit-ts { font-size: 11.5px; color: #6B8FAB; font-weight: 500; white-space: nowrap; font-family: 'Inter', monospace; }
        .audit-user { font-weight: 600; color: #1A3A5C; }
        .audit-rid { font-size: 11px; color: #6B8FAB; font-weight: 500; }
        .audit-err { font-size: 11.5px; color: #B91C1C; font-style: italic; max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        .audit-err-none { color: #CBD5E1; font-size: 12px; }

        /* action badges */
        .badge-action {
            display: inline-block; font-size: 10.5px; font-weight: 700;
            padding: 3px 10px; border-radius: 20px; letter-spacing: 0.3px;
            white-space: nowrap;
        }
        .badge-login    { background: #DBEAFE; color: #1E40AF; }
        .badge-logout   { background: #E2E8F0; color: #475569; }
        .badge-failed   { background: #FEE2E2; color: #B91C1C; }
        .badge-create   { background: #D1FAE5; color: #065F46; }
        .badge-update   { background: #FDEBD3; color: #B5670F; }
        .badge-delete   { background: #FEE2E2; color: #B91C1C; }
        .badge-predict  { background: #EDE9FE; color: #5B21B6; }
        .badge-default  { background: #F0F5FA; color: #6B8FAB; }

        /* status badges */
        .badge-status {
            display: inline-block; font-size: 10.5px; font-weight: 700;
            padding: 3px 10px; border-radius: 20px; letter-spacing: 0.3px;
        }
        .badge-success  { background: #D1FAE5; color: #065F46; }
        .badge-fail     { background: #FEE2E2; color: #B91C1C; }
        .badge-info     { background: #DBEAFE; color: #1E40AF; }

        .audit-table-footer {
            padding: 11px 18px; background: #F8FAFD;
            border-top: 1px solid #E2E8F0;
            font-size: 12px; color: #6B8FAB; font-weight: 600;
            display: flex; align-items: center; justify-content: space-between;
        }

        /* ── EMPTY / INFO STATES ── */
        .empty-state {
            background: #fff; border: 1.5px dashed #CBD5E1;
            border-radius: 20px; padding: 48px 32px; text-align: center;
        }
        .info-strip {
            display: flex; align-items: center; gap: 10px;
            background: #EBF3FB; border: 1px solid #B5D4F4;
            border-radius: 12px; padding: 12px 18px;
            font-size: 13px; color: #1A3A5C; font-weight: 500;
            margin-top: 16px;
        }

        /* ── LEGEND CARD ── */
        .legend-card {
            background: #fff;
            border: 1.5px solid #E2E8F0;
            border-radius: 18px;
            padding: 22px 24px;
            margin-top: 24px;
            box-shadow: 0 2px 10px rgba(30,74,118,0.05);
        }
        .legend-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 12px;
            margin-top: 14px;
        }
        .legend-item {
            display: flex; align-items: center; gap: 10px;
            font-size: 13px; color: #2D4A6B;
        }
        .legend-item span { font-weight: 500; }
    </style>
    """, unsafe_allow_html=True)

    # ── PAGE HEADER ──
    st.markdown("""
    <div class="page-header">
        <div class="ph-left">
            <div class="ph-icon">
                <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="1.8">
                    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                </svg>
            </div>
            <div>
                <p class="ph-title">Audit Trail</p>
                <p class="ph-subtitle">Complete system activity log — track all user actions and events</p>
            </div>
        </div>
        <div class="ph-badge">Admin Only</div>
    </div>
    """, unsafe_allow_html=True)

    # ── FILTER PANEL ──
    st.markdown("""
    <div class="sec-label">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#E88C30" stroke-width="2">
            <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/>
        </svg>
        Filter Audit Logs
    </div>
    <style>
        /* Style the next columns block as the filter panel — no split divs needed */
        [data-testid="stHorizontalBlock"]:has(.stSelectbox) {
            background: #fff;
            border: 1.5px solid #E2E8F0;
            border-radius: 20px;
            padding: 18px 20px 14px !important;
            margin-bottom: 24px;
            box-shadow: 0 2px 10px rgba(30,74,118,0.05);
        }
    </style>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        days = st.selectbox("Time Period", [7, 14, 30, 60, 90], index=2,
                            format_func=lambda x: f"Last {x} days")
    with col2:
        action_options = ["All", "LOGIN", "LOGOUT", "LOGIN_FAILED", "CREATE", "UPDATE", "DELETE", "PREDICTION"]
        action_filter = st.selectbox("Action Type", action_options)
    with col3:
        conn_u = get_connection()
        users = ["All"]
        if conn_u:
            _c = conn_u.cursor()
            _c.execute("SELECT DISTINCT username FROM audit_logs ORDER BY username")
            users.extend([row[0] for row in _c.fetchall() if row[0]])
            _c.close()
            conn_u.close()
        user_filter = st.selectbox("User", users)
    with col4:
        search_term = st.text_input("Search", placeholder="Search all fields...")

    # ── FETCH LOGS ──
    conn = get_connection()
    if not conn:
        st.error("Database connection failed.")
        return

    cursor = conn.cursor()
    where_clause = "WHERE created_at >= CURRENT_DATE - (%s * INTERVAL '1 day')"
    params = [days]

    if action_filter != "All":
        where_clause += " AND action = %s"
        params.append(action_filter)
    if user_filter != "All":
        where_clause += " AND username = %s"
        params.append(user_filter)
    if search_term:
        where_clause += " AND (username ILIKE %s OR action ILIKE %s OR table_name ILIKE %s OR CAST(record_id AS TEXT) ILIKE %s OR status ILIKE %s)"
        search_pattern = f"%{search_term}%"
        params.extend([search_pattern] * 5)

    # Aggregate metrics computed over the FULL filtered set (not capped), so
    # "Total Records" / "Active Users" / "Success Rate" stay accurate even when
    # more than 500 logs match the filter -- previously these were silently
    # computed only from the 500 rows returned for the table below.
    cursor.execute(f"""
        SELECT COUNT(*),
               COUNT(*) FILTER (WHERE status = 'FAILED'),
               COUNT(DISTINCT username)
        FROM audit_logs {where_clause}
    """, params)
    total_logs, failed_logs, unique_users = cursor.fetchone()
    total_logs = int(total_logs or 0)
    failed_logs = int(failed_logs or 0)
    unique_users = int(unique_users or 0)

    # Detail rows for the table -- still capped at 500 for display performance.
    cursor.execute(f"""
        SELECT log_id, username, action, table_name, record_id, status, error_message,
               TO_CHAR(created_at, 'YYYY-MM-DD HH24:MI:SS') as timestamp
        FROM audit_logs {where_clause} ORDER BY created_at DESC LIMIT 500
    """, params)
    logs = cursor.fetchall()
    cursor.close()
    conn.close()

    # ── METRIC CARDS ──
    if total_logs:
        success_rate = round((total_logs - failed_logs) / total_logs * 100, 1) if total_logs > 0 else 100.0

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Total Records", f"{total_logs:,}")
        with c2:
            st.metric("Failed Actions", failed_logs)
        with c3:
            st.metric("Active Users", unique_users)
        with c4:
            st.metric("Success Rate", f"{success_rate}%")


    # ── AUDIT TABLE ──
    st.markdown("""
    <div class="sec-label" style="margin-top:24px;">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#E88C30" stroke-width="2">
            <polygon points="22 3 22 15 16 15 16 21 2 21 2 3 22 3"/>
            <line x1="10" y1="9" x2="18" y2="9"/><line x1="10" y1="13" x2="18" y2="13"/>
        </svg>
        Audit Log Entries
    </div>""", unsafe_allow_html=True)

    if logs:
        def action_badge(action):
            a = (action or "").upper()
            if a == "LOGIN":        return f'<span class="badge-action badge-login">LOGIN</span>'
            if a == "LOGOUT":       return f'<span class="badge-action badge-logout">LOGOUT</span>'
            if a == "LOGIN_FAILED": return f'<span class="badge-action badge-failed">LOGIN FAILED</span>'
            if a == "CREATE":       return f'<span class="badge-action badge-create">CREATE</span>'
            if a == "UPDATE":       return f'<span class="badge-action badge-update">UPDATE</span>'
            if a == "DELETE":       return f'<span class="badge-action badge-delete">DELETE</span>'
            if a == "PREDICTION":   return f'<span class="badge-action badge-predict">PREDICTION</span>'
            return f'<span class="badge-action badge-default">{esc(action)}</span>'

        def status_badge(status):
            s = (status or "").upper()
            if s == "SUCCESS": return f'<span class="badge-status badge-success">Success</span>'
            if s == "FAILED":  return f'<span class="badge-status badge-fail">Failed</span>'
            return f'<span class="badge-status badge-info">{esc(status) or "—"}</span>'

        rows = ""
        for log in logs:
            log_id, username, action, table_name, record_id, status, error_msg, timestamp = log
            username, table_name = esc(username), esc(table_name)
            error_msg_safe = esc(error_msg)
            err_html = (
                f'<span class="audit-err" title="{error_msg_safe}">{error_msg_safe[:40]}{"…" if len(error_msg_safe) > 40 else ""}</span>'
                if error_msg else '<span class="audit-err-none">—</span>'
            )
            rows += f"""
            <tr>
                <td><span class="audit-ts">{timestamp or '—'}</span></td>
                <td><span class="audit-user">{username or '—'}</span></td>
                <td>{action_badge(action)}</td>
                <td><span style="font-size:12.5px;color:#2D4A6B;">{table_name or '—'}</span></td>
                <td><span class="audit-rid">{record_id if record_id is not None else '—'}</span></td>
                <td>{status_badge(status)}</td>
                <td>{err_html}</td>
            </tr>"""

        st.markdown(f"""
        <div class="audit-table-wrap">
            <table class="audit-table">
                <thead>
                    <tr>
                        <th>Timestamp</th>
                        <th>User</th>
                        <th>Action</th>
                        <th>Table</th>
                        <th>Record ID</th>
                        <th>Status</th>
                        <th>Error</th>
                    </tr>
                </thead>
                <tbody>{rows}</tbody>
            </table>
            <div class="audit-table-footer">
                <span>Showing {len(logs):,} of {total_logs:,} matching record{'s' if total_logs != 1 else ''} · last {days} days</span>
                <span style="color:#CBD5E1;">{"Truncated to 500 most recent" if total_logs > 500 else ""}</span>
            </div>
        </div>""", unsafe_allow_html=True)

        # ── EXPORT ──
        df_export = pd.DataFrame(logs, columns=['ID', 'User', 'Action', 'Table', 'Record ID', 'Status', 'Error', 'Timestamp'])
        csv = df_export.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"audit_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

        st.markdown(f"""
        <div class="info-strip">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#1E4A76" stroke-width="2">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
            </svg>
            Audit logs are <strong>&nbsp;immutable&nbsp;</strong> — all system actions are recorded for security and compliance.
        </div>""", unsafe_allow_html=True)

    else:
        st.markdown("""
        <div class="empty-state">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#B0C8E8" stroke-width="1.5">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
            </svg>
            <p style="font-size:16px;font-weight:600;color:#1A3A5C;margin-top:16px;">No audit logs found</p>
            <p style="font-size:13px;color:#6B8FAB;margin-top:6px;">Try adjusting the time period, action type, or user filter.</p>
        </div>""", unsafe_allow_html=True)

        # ── LEGEND ──
        st.markdown("""
        <div class="legend-card">
            <div class="sec-label" style="margin-bottom:0;">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#E88C30" stroke-width="2">
                    <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><circle cx="12" cy="16" r="0.5" fill="#E88C30"/>
                </svg>
                How Audit Logging Works
            </div>
            <div class="legend-grid">
                <div class="legend-item"><span class="badge-action badge-login">LOGIN</span><span>Successful user sign-in</span></div>
                <div class="legend-item"><span class="badge-action badge-failed">LOGIN FAILED</span><span>Failed login attempt</span></div>
                <div class="legend-item"><span class="badge-action badge-logout">LOGOUT</span><span>User signed out</span></div>
                <div class="legend-item"><span class="badge-action badge-create">CREATE</span><span>New record added</span></div>
                <div class="legend-item"><span class="badge-action badge-update">UPDATE</span><span>Existing record edited</span></div>
                <div class="legend-item"><span class="badge-action badge-delete">DELETE</span><span>Record removed</span></div>
                <div class="legend-item"><span class="badge-action badge-predict">PREDICTION</span><span>No-show prediction run</span></div>
            </div>
        </div>""", unsafe_allow_html=True)