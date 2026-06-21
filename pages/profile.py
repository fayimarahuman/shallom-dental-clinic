# pages/profile.py
import streamlit as st
from utils.auth import get_user_by_id, update_user_profile
from utils.sanitize import esc


def show_profile():
    st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
        .stApp { background: #F5F8FC !important; }
        #MainMenu, footer, header { display: none !important; }
        .block-container { padding: 1.5rem 2rem 2rem !important; max-width: 100% !important; }

        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: #E8EDF2; border-radius: 10px; }
        ::-webkit-scrollbar-thumb { background: #E88C30; border-radius: 10px; }

        /* ── Kill ghost rectangles & hr lines ── */
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

        /* ── Strip stForm's own border/background so our card shows cleanly ── */
        [data-testid="stForm"] {
            border: none !important;
            background: transparent !important;
            box-shadow: none !important;
            padding: 0 !important;
        }

        /* ── PAGE HEADER ── */
        .page-header {
            background: linear-gradient(135deg, #1E4A76 0%, #2D6A9F 50%, #3A7CA5 100%);
            border-radius: 24px;
            padding: 28px 32px;
            margin-bottom: 32px;
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

        /* ── TWO-COLUMN LAYOUT ── */
        .profile-layout {
            display: grid;
            grid-template-columns: 260px 1fr;
            gap: 24px;
            align-items: start;
            max-width: 960px;
            margin: 0 auto;
        }

        /* ── LEFT IDENTITY CARD ── */
        .identity-card {
            background: #fff;
            border: 1.5px solid #E2E8F0;
            border-radius: 22px;
            padding: 32px 24px;
            text-align: center;
            box-shadow: 0 2px 12px rgba(30,74,118,0.06);
        }
        .avatar-ring {
            width: 88px; height: 88px;
            background: linear-gradient(135deg, #1E4A76, #2D6A9F);
            border-radius: 26px;
            display: flex; align-items: center; justify-content: center;
            margin: 0 auto 20px;
            box-shadow: 0 6px 20px rgba(30,74,118,0.25);
        }
        .id-username {
            font-size: 18px; font-weight: 800;
            color: #1A3A5C; margin-bottom: 6px; letter-spacing: -0.3px;
        }
        .id-email {
            font-size: 12.5px; color: #6B8FAB;
            font-weight: 500; margin-bottom: 18px;
            word-break: break-all;
        }
        .role-pill {
            display: inline-flex; align-items: center; gap: 6px;
            background: linear-gradient(135deg, rgba(30,74,118,0.08), rgba(45,106,159,0.08));
            border: 1.5px solid rgba(30,74,118,0.15);
            color: #1E4A76; font-size: 12px; font-weight: 700;
            padding: 6px 16px; border-radius: 40px;
            text-transform: uppercase; letter-spacing: 0.8px;
        }
        .id-divider {
            height: 1px; background: #F0F5FA;
            margin: 24px 0;
        }
        .id-stat { margin-bottom: 14px; }
        .id-stat-label {
            font-size: 10.5px; font-weight: 700; color: #6B8FAB;
            text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 3px;
        }
        .id-stat-value {
            font-size: 13.5px; font-weight: 600; color: #1A3A5C;
        }

        .sec-label {
            font-size: 11px; font-weight: 700; color: #6B8FAB;
            letter-spacing: 1.2px; text-transform: uppercase;
            margin: 0 0 18px 2px;
            display: flex; align-items: center; gap: 8px;
        }
        .sec-label + .sec-label-gap { margin-top: 28px; }

        /* ── INPUT FIELDS ── */
        .stTextInput label {
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

        /* ── SUBMIT BUTTON ── */
        .stFormSubmitButton button {
            background: linear-gradient(135deg, #1E4A76, #2D6A9F) !important;
            border: none !important;
            border-radius: 12px !important;
            padding: 13px 24px !important;
            font-weight: 700 !important;
            font-size: 14px !important;
            color: #fff !important;
            width: 100% !important;
            box-shadow: 0 4px 14px rgba(30,74,118,0.22) !important;
            transition: all 0.2s ease !important;
            letter-spacing: 0.1px !important;
        }
        .stFormSubmitButton button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 8px 20px rgba(30,74,118,0.28) !important;
        }

        /* ── PASSWORD HINT ── */
        .pw-hint {
            display: flex; align-items: flex-start; gap: 9px;
            background: #F8FAFD;
            border: 1.5px solid #E2E8F0;
            border-radius: 12px;
            padding: 12px 16px;
            font-size: 12.5px; color: #6B8FAB; font-weight: 500;
            margin-bottom: 18px; line-height: 1.5;
        }

        /* ── BOTTOM NOTE ── */
        .bottom-note {
            background: #EBF3FB;
            border: 1px solid #B5D4F4;
            border-radius: 14px;
            padding: 14px 20px;
            font-size: 12.5px; color: #1A3A5C; font-weight: 500;
            display: flex; align-items: flex-start; gap: 10px;
            margin-top: 20px; line-height: 1.6;
            max-width: 960px; margin-left: auto; margin-right: auto;
        }
    </style>
    """, unsafe_allow_html=True)

    user = None
    if st.session_state.get('user_id'):
        user = get_user_by_id(st.session_state.user_id)

    if not user:
        st.error("Unable to load profile. Please sign out and sign in again.")
        return

    user_id, username, role, email = user

    if '_profile_flash' not in st.session_state:
        st.session_state._profile_flash = None

    # ── PAGE HEADER ──
    st.markdown(f"""
    <div class="page-header">
        <div class="ph-left">
            <div class="ph-icon">
                <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="1.8">
                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                    <circle cx="12" cy="7" r="4"/>
                </svg>
            </div>
            <div>
                <p class="ph-title">My Profile</p>
                <p class="ph-subtitle">Manage your account details and login credentials</p>
            </div>
        </div>
        <div class="ph-badge">{role.title()}</div>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state._profile_flash:
        st.success(st.session_state._profile_flash)
        st.session_state._profile_flash = None

    # ── TWO-COLUMN LAYOUT ──
    left_col, right_col = st.columns([1, 2.2], gap="large")

    # ── LEFT — IDENTITY CARD ──
    with left_col:
        initials = "".join([w[0].upper() for w in username.split()[:2]]) if username else "U"
        st.markdown(f"""
        <div class="identity-card">
            <div class="avatar-ring">
                <svg width="38" height="38" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="1.7">
                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                    <circle cx="12" cy="7" r="4"/>
                </svg>
            </div>
            <div class="id-username">{esc(username)}</div>
            <div class="id-email">{esc(email) or "No email set"}</div>
            <div class="role-pill">
                <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="#1E4A76" stroke-width="2.5">
                    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                </svg>
                {role.title()}
            </div>
            <div class="id-divider"></div>
            <div class="id-stat">
                <div class="id-stat-label">User ID</div>
                <div class="id-stat-value">#{user_id}</div>
            </div>
            <div class="id-stat">
                <div class="id-stat-label">Account Type</div>
                <div class="id-stat-value">{role.title()} Access</div>
            </div>
            <div class="id-stat">
                <div class="id-stat-label">Status</div>
                <div class="id-stat-value" style="color:#065F46;">Active</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── RIGHT — EDIT FORM ──
    # Style the form card via CSS on [data-testid="stForm"] — no wrapper divs needed
    with right_col:
        st.markdown("""
        <style>
            /* Card styling applied directly to the stForm element */
            [data-testid="stForm"] {
                background: #fff !important;
                border: 1.5px solid #E2E8F0 !important;
                border-radius: 22px !important;
                padding: 28px 28px 24px !important;
                box-shadow: 0 2px 12px rgba(30,74,118,0.06) !important;
            }
        </style>
        <div class="sec-label" style="margin-bottom:14px;">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#E88C30" stroke-width="2.2">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                <circle cx="12" cy="7" r="4"/>
            </svg>
            Account Details
        </div>
        """, unsafe_allow_html=True)

        with st.form("profile_form"):
            new_username = st.text_input("Username", value=username)
            new_email    = st.text_input("Email Address", value=email or "")

            st.markdown("""
            <div style="height:1px;background:#F0F5FA;margin:20px 0 22px;"></div>
            <div class="sec-label">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#E88C30" stroke-width="2.2">
                    <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                    <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                </svg>
                Change Password
            </div>
            <div class="pw-hint">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#6B8FAB" stroke-width="2" style="flex-shrink:0;margin-top:1px;">
                    <circle cx="12" cy="12" r="10"/>
                    <line x1="12" y1="8" x2="12" y2="12"/>
                    <circle cx="12" cy="16" r="0.5" fill="#6B8FAB"/>
                </svg>
                Leave both fields blank to keep your current password unchanged.
            </div>
            """, unsafe_allow_html=True)

            new_password     = st.text_input("New Password", type="password", placeholder="Enter new password")
            confirm_password = st.text_input("Confirm New Password", type="password", placeholder="Re-enter new password")

            st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

            if st.form_submit_button("Save Changes", use_container_width=True):
                if new_password and new_password != confirm_password:
                    st.error("The new password and confirmation do not match.")
                else:
                    success, message = update_user_profile(
                        user_id,
                        new_username.strip(),
                        new_email.strip(),
                        new_password.strip() if new_password else None
                    )
                    if success:
                        st.session_state.username = new_username.strip()
                        st.session_state._profile_flash = message
                        st.rerun()
                    else:
                        st.error(message)

    # ── BOTTOM NOTE ──
    st.markdown("""
    <div class="bottom-note">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#1E4A76" stroke-width="2" style="flex-shrink:0;margin-top:2px;">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="8" x2="12" y2="12"/>
            <circle cx="12" cy="16" r="0.5" fill="#1E4A76"/>
        </svg>
        <span>Username changes take effect immediately and update your display name across the system.
        Password changes are optional — only applied when both password fields are filled in.</span>
    </div>
    """, unsafe_allow_html=True)