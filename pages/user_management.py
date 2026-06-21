# pages/user_management.py
import textwrap
import streamlit as st
from utils.auth import (
    list_users, create_user, set_user_role, set_user_locked, delete_user, VALID_ROLES
)
from utils.sanitize import esc


def show_user_management():
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
        [data-testid="stHorizontalBlock"] { align-items: center !important; gap: 0.6rem !important; }

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

        /* ── SELECTBOX ── */
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
        .stButton button:disabled {
            background: #E2E8F0 !important; color: #A6B8CC !important;
            box-shadow: none !important; transform: none !important; cursor: not-allowed !important;
        }
        /* Danger button — Delete (matched by key prefix via data-testid wrapper order is not possible in pure CSS,
           so danger styling is applied via the .danger-btn wrapper class added with st.container) */
        .danger-zone .stButton button {
            background: linear-gradient(135deg, #DC2626, #B91C1C) !important;
            box-shadow: 0 2px 10px rgba(220,38,38,0.2) !important;
        }
        .danger-zone .stButton button:hover {
            box-shadow: 0 6px 18px rgba(220,38,38,0.28) !important;
        }
        .danger-zone .stButton button:disabled {
            background: #E2E8F0 !important; color: #A6B8CC !important; box-shadow: none !important;
        }

        /* ── USERS TABLE ── */
        .ut-table-wrap {
            background: #fff;
            border-radius: 20px;
            border: 1.5px solid #E2E8F0;
            overflow: hidden;
            box-shadow: 0 4px 24px rgba(30,74,118,0.08);
        }
        .ut-table { width: 100%; border-collapse: collapse; }
        .ut-table thead tr { background: linear-gradient(135deg, #1E4A76 0%, #2D6A9F 100%); }
        .ut-table thead th {
            padding: 14px 20px; text-align: left;
            font-size: 10.5px; font-weight: 700; letter-spacing: 1.2px;
            text-transform: uppercase; color: rgba(255,255,255,0.75);
            white-space: nowrap; border: none;
        }
        .ut-table tbody tr { border-bottom: 1px solid #F0F5FA; transition: background 0.12s ease; }
        .ut-table tbody tr:last-child { border-bottom: none; }
        .ut-table tbody tr:hover { background: #F7FAFD; }
        .ut-table tbody td { padding: 14px 20px; vertical-align: middle; border: none; }
        .cell-user {
            font-size: 14px; font-weight: 600; color: #1A3A5C; display: block; line-height: 1.3;
        }
        .cell-you {
            font-size: 10.5px; font-weight: 700; color: #E88C30; margin-left: 6px;
        }
        .cell-email { font-size: 12.5px; color: #7A9BB5; }
        .cell-date { font-size: 12px; color: #94A3B8; white-space: nowrap; }
        .badge {
            display: inline-block; font-size: 11px; font-weight: 700;
            padding: 4px 12px; border-radius: 20px; letter-spacing: 0.2px;
        }
        .badge-admin        { background: #DBEAFE; color: #1E4A76; }
        .badge-dentist      { background: #FDEBD3; color: #B5670F; }
        .badge-receptionist { background: #E2E8F0; color: #1A3A5C; }
        .badge-active { background: #DCFCE7; color: #15803D; }
        .badge-locked  { background: #FEE2E2; color: #B91C1C; }
        .ut-table-footer {
            padding: 12px 20px; background: #F8FAFD; border-top: 1px solid #E2E8F0;
            display: flex; align-items: center; justify-content: space-between;
        }
        .ut-table-footer-count { font-size: 12.5px; font-weight: 600; color: #6B8FAB; }
        .ut-table-footer-hint { font-size: 11.5px; color: #B0C4D8; }

        /* ── MANAGE-USER SUMMARY CARD ── */
        .user-summary {
            background: #fff; border: 1.5px solid #E2E8F0; border-radius: 20px;
            padding: 22px 26px; margin-bottom: 20px;
            box-shadow: 0 2px 12px rgba(30,74,118,0.05);
            display: flex; align-items: center; gap: 16px;
        }
        .us-avatar {
            width: 50px; height: 50px; border-radius: 14px; flex-shrink: 0;
            background: linear-gradient(135deg, #1E4A76, #2D6A9F);
            display: flex; align-items: center; justify-content: center;
            font-size: 16px; font-weight: 800; color: #F5BC6A;
            border: 2px solid rgba(232,140,48,0.4);
        }
        .us-name { font-size: 16px; font-weight: 700; color: #1A3A5C; }
        .us-meta { font-size: 12.5px; color: #6B8FAB; margin-top: 2px; }

        /* ── DELETE / LOCK WARNING ── */
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

    if "confirm_delete_user" not in st.session_state:
        st.session_state.confirm_delete_user = None
    if "_um_flash" not in st.session_state:
        st.session_state._um_flash = None

    current_user_id = st.session_state.get("user_id")
    users = list_users()
    total = len(users)

    # ── HEADER ──────────────────────────────────────────────────────
    st.markdown(textwrap.dedent(f"""
    <div class="page-header">
        <div class="ph-left">
            <div class="ph-icon">
                <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="1.8">
                    <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/>
                    <path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>
                </svg>
            </div>
            <div>
                <p class="ph-title">User Management</p>
                <p class="ph-subtitle">Create staff accounts and control who can access what</p>
            </div>
        </div>
        <div class="ph-badge">{total} account{'s' if total != 1 else ''} on system</div>
    </div>
    """), unsafe_allow_html=True)

    if st.session_state._um_flash:
        st.success(st.session_state._um_flash)
        st.session_state._um_flash = None

    tab1, tab2, tab3 = st.tabs(["All Users", "Create User", "Manage / Remove"])

    # ========== TAB 1 — ALL USERS ==========
    with tab1:
        if users:
            rows = ""
            for u in users:
                is_self = current_user_id is not None and u["user_id"] == current_user_id
                role_class = f"badge-{u['role']}" if u["role"] in VALID_ROLES else "badge-receptionist"
                status_class = "badge-locked" if u["is_locked"] else "badge-active"
                status_text = "Locked" if u["is_locked"] else "Active"
                last_login = esc(str(u["last_login"])[:16]) if u["last_login"] else "Never"
                you_tag = '<span class="cell-you">YOU</span>' if is_self else ''
                email_cell = esc(u['email']) if u['email'] else '—'
                created_cell = esc(str(u['created_at'])[:16]) if u['created_at'] else '—'
                rows += (
                    "<tr>"
                    f'<td><span class="cell-user">{esc(u["username"])}{you_tag}</span></td>'
                    f'<td><span class="badge {role_class}">{esc(u["role"].title())}</span></td>'
                    f'<td><span class="cell-email">{email_cell}</span></td>'
                    f'<td><span class="badge {status_class}">{status_text}</span></td>'
                    f'<td><span class="cell-date">{last_login}</span></td>'
                    f'<td><span class="cell-date">{created_cell}</span></td>'
                    "</tr>"
                )

            st.markdown(
                '<div class="ut-table-wrap">'
                '<table class="ut-table">'
                '<thead><tr>'
                '<th>User</th><th>Role</th><th>Email</th>'
                '<th>Status</th><th>Last Login</th><th>Created</th>'
                '</tr></thead>'
                f'<tbody>{rows}</tbody>'
                '</table>'
                '<div class="ut-table-footer">'
                f'<span class="ut-table-footer-count">{total} user{"s" if total != 1 else ""} found</span>'
                '<span class="ut-table-footer-hint">Sorted by most recently created</span>'
                '</div>'
                '</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(textwrap.dedent("""
            <div class="empty-state">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#B0C8E8" stroke-width="1.5">
                    <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/>
                </svg>
                <p style="font-size:16px;font-weight:600;color:#1A3A5C;margin-top:16px;">No users found</p>
                <p style="font-size:13px;color:#6B8FAB;">The database may be unavailable.</p>
            </div>
            """), unsafe_allow_html=True)

    # ========== TAB 2 — CREATE USER ==========
    with tab2:
        st.markdown('<div class="sec-label">New Staff Account</div>', unsafe_allow_html=True)
        with st.form("create_user_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                new_username = st.text_input("Username *", placeholder="e.g. dr_jane")
                new_role = st.selectbox("Role *", VALID_ROLES, index=1,
                                         format_func=lambda r: r.title())
            with col2:
                new_password = st.text_input("Temporary Password *", type="password",
                                              placeholder="Minimum 6 characters")
                new_email = st.text_input("Email (optional)", placeholder="e.g. jane@shallomdental.com")

            submitted = st.form_submit_button("Create User", use_container_width=True)
            if submitted:
                success, message = create_user(new_username, new_password, new_role, new_email)
                if success:
                    st.session_state._um_flash = message
                    st.rerun()
                else:
                    st.error(message)

    # ========== TAB 3 — MANAGE / REMOVE ==========
    with tab3:
        if not users:
            st.markdown('<div class="empty-state"><p style="font-size:16px;font-weight:600;color:#1A3A5C;">No users available.</p></div>', unsafe_allow_html=True)
            return

        st.markdown('<div class="sec-label">Find User</div>', unsafe_allow_html=True)
        options = [f"{u['username']} (ID {u['user_id']})" for u in users]
        selected = st.selectbox("Select", options, label_visibility="collapsed", key="select_user")
        selected_id = int(selected.split("ID ")[1].rstrip(")"))
        u = next((x for x in users if x["user_id"] == selected_id), None)

        if not u:
            st.error("User not found.")
            return

        is_self = current_user_id is not None and u["user_id"] == current_user_id
        initials = (u["username"][:2]).upper()

        st.markdown(textwrap.dedent(f"""
        <div class="user-summary">
            <div class="us-avatar">{initials}</div>
            <div>
                <div class="us-name">{esc(u['username'])}{' <span style="color:#E88C30;">(you)</span>' if is_self else ''}</div>
                <div class="us-meta">{esc(u['email']) if u['email'] else 'No email on file'} &nbsp;·&nbsp; {esc(u['login_attempts'])} failed login attempt(s)</div>
            </div>
        </div>
        """), unsafe_allow_html=True)

        st.markdown('<div class="sec-label">Change Role</div>', unsafe_allow_html=True)
        with st.form("role_form"):
            col1, col2 = st.columns([3, 1])
            with col1:
                role_pick = st.selectbox(
                    "Role", VALID_ROLES,
                    index=VALID_ROLES.index(u["role"]) if u["role"] in VALID_ROLES else 0,
                    format_func=lambda r: r.title(), label_visibility="collapsed"
                )
            with col2:
                role_submit = st.form_submit_button("Update Role", use_container_width=True)
            if role_submit:
                success, message = set_user_role(u["user_id"], role_pick, current_user_id)
                if success:
                    st.session_state._um_flash = message
                    st.rerun()
                else:
                    st.error(message)

        st.markdown('<div class="sec-label">Account Status</div>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            if u["is_locked"]:
                if st.button("Unlock Account", use_container_width=True, key="unlock_btn"):
                    success, message = set_user_locked(u["user_id"], False)
                    st.session_state._um_flash = message if success else None
                    if not success:
                        st.error(message)
                    else:
                        st.rerun()
            else:
                if st.button("Lock Account", use_container_width=True, key="lock_btn", disabled=is_self):
                    success, message = set_user_locked(u["user_id"], True)
                    st.session_state._um_flash = message if success else None
                    if not success:
                        st.error(message)
                    else:
                        st.rerun()
        with col2:
            st.markdown('<div class="danger-zone">', unsafe_allow_html=True)
            if st.button("Delete Account", use_container_width=True, key="delete_btn", disabled=is_self):
                st.session_state.confirm_delete_user = u["user_id"]
            st.markdown('</div>', unsafe_allow_html=True)

        if st.session_state.confirm_delete_user == u["user_id"]:
            st.markdown(textwrap.dedent(f"""
            <div class="delete-warn">
                <div class="delete-warn-title">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#B91C1C" stroke-width="1.8">
                        <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/>
                        <circle cx="12" cy="16" r="0.5" fill="#B91C1C"/>
                    </svg>
                    Confirm deletion — this cannot be undone
                </div>
                <div class="delete-field">User: <span>{esc(u['username'])}</span></div>
                <div class="delete-field">Role: <span>{esc(u['role'].title())}</span></div>
                <div class="delete-note">This permanently removes the login account. Audit log entries already recorded under this username are kept.</div>
            </div>
            """), unsafe_allow_html=True)

            dc1, dc2 = st.columns(2)
            with dc1:
                st.markdown('<div class="danger-zone">', unsafe_allow_html=True)
                if st.button("Yes, Delete User", use_container_width=True, key="confirm_del_user"):
                    success, message = delete_user(u["user_id"], current_user_id)
                    st.session_state.confirm_delete_user = None
                    if success:
                        st.session_state._um_flash = message
                        st.rerun()
                    else:
                        st.error(message)
                st.markdown('</div>', unsafe_allow_html=True)
            with dc2:
                if st.button("Cancel", use_container_width=True, key="cancel_del_user"):
                    st.session_state.confirm_delete_user = None
                    st.rerun()