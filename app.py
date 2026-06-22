# SHALLOM DENTAL CLINIC MANAGEMENT SYSTEM — v4 UI
import base64
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components
from utils.db import init_database
from utils.auth import init_auth_table, login_user
from utils.permissions import can_view_page, get_allowed_pages

LOGO_PATH = Path("assets/logo.jpeg")

def load_logo_data_url(path):
    if not path.exists():
        return None
    try:
        content = path.read_bytes()
        ext = path.suffix.lower().lstrip('.')
        data = base64.b64encode(content).decode('utf-8')
        return f"data:image/{ext};base64,{data}"
    except Exception:
        return None

logo_data_url = load_logo_data_url(LOGO_PATH)

st.set_page_config(
    page_title="Shallom Dental Clinic",
    page_icon=logo_data_url if logo_data_url else "🦷",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Auto-dismiss the "Bad message format / SessionInfo" frontend popup ──
# This is a known Streamlit frontend race condition triggered by slow
# cold starts (Streamlit Cloud + Neon waking up). It doesn't affect app
# logic, but auto-clicking it keeps it from being visible to users.
components.html("""
<script>
const observer = new MutationObserver(() => {
    const buttons = window.parent.document.querySelectorAll('button');
    buttons.forEach(btn => {
        if (btn.innerText.trim() === 'OK' || btn.innerText.trim() === 'Close') {
            const dialogText = btn.closest('div')?.innerText || '';
            if (dialogText.includes('SessionInfo') || dialogText.includes('Bad message format')) {
                btn.click();
            }
        }
    });
});
observer.observe(window.parent.document.body, { childList: true, subtree: true });
</script>
""", height=0)

st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<style>
  html,body,[class*="css"],.stApp,button,input,select,textarea{
    font-family:'Plus Jakarta Sans',sans-serif!important;
  }
  #MainMenu,header,footer,[data-testid="stSidebarNav"],
  [data-testid="collapsedControl"],.stAppDeployButton,[data-testid="stToolbar"]
    { display:none!important; }
  hr,[data-testid="stSidebar"] hr,.stForm>div>hr,
  [data-baseweb="divider"],[data-baseweb="block-divider"]
    { display:none!important; height:0!important; margin:0!important; }
  div[data-baseweb="input"]{ border:none!important; box-shadow:none!important; }
  ::-webkit-scrollbar{ width:4px; }
  ::-webkit-scrollbar-track{ background:transparent; }
  ::-webkit-scrollbar-thumb{ background:#F59E0B; border-radius:4px; }
</style>
""", unsafe_allow_html=True)

init_database()
init_auth_table()

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'page' not in st.session_state:
    st.session_state.page = "Dashboard"
if '_login_msg' not in st.session_state:
    st.session_state._login_msg = None

VALID_PAGES = ["Dashboard","Patients","Patient History","Appointments",
               "Payments","Inventory","No-Show Predictor","Reports",
               "Audit Trail","User Management","Profile","About"]

def logout():
    from utils.audit import log_action
    if st.session_state.get('user_id'):
        log_action("LOGOUT", table_name="users", record_id=st.session_state.get('user_id'),
                   status="SUCCESS")
    for k in ['authenticated','user_id','username','role','page','_login_msg']:
        st.session_state.pop(k, None)
    st.rerun()

qp = st.query_params
if qp:
    st.query_params.clear()

# ══════════════════════════════════════════════════════════════════════════════
# LOGIN PAGE
# ══════════════════════════════════════════════════════════════════════════════
if not st.session_state.authenticated:

    st.markdown("""
    <style>
      [data-testid="stSidebar"]{ display:none!important; }
      .stApp{
        background:
          radial-gradient(ellipse at 20% 50%, rgba(0,71,171,0.45) 0%, transparent 55%),
          radial-gradient(ellipse at 80% 20%, rgba(245,158,11,0.08) 0%, transparent 45%),
          linear-gradient(160deg,#071830 0%,#0D2952 50%,#0A1F44 100%)!important;
      }
      .block-container{
        min-height:100vh!important; padding:0!important; max-width:100%!important;
        display:flex!important; flex-direction:column!important;
        align-items:center!important; justify-content:center!important;
      }
      div[data-testid="stVerticalBlock"]{ align-items:center!important; gap:0!important; }

      /* ── Card top (HTML portion) ── */
      .lp-card-top{
        width:100%; background:#ffffff;
        border-radius:20px 20px 0 0;
        font-family:'Plus Jakarta Sans',sans-serif;
      }
      .lp-stripe{
        height:4px;
        background:linear-gradient(90deg,#0047AB 0%,#1565D8 40%,#F59E0B 78%,#FBBF24 100%);
        border-radius:20px 20px 0 0;
      }
      .lp-top-body{ padding:28px 34px 20px; background:#ffffff; border-radius:0; }

      .lp-logo-wrap{
        width:110px; height:110px; border-radius:14px; overflow:hidden;
        margin:0 auto 14px; background:#F0F5FF;
        display:flex; align-items:center; justify-content:center;
        box-shadow:0 6px 20px rgba(0,71,171,0.18);
        border:2.5px solid rgba(245,158,11,0.5);
      }
      .lp-logo-wrap img{ width:100%; height:100%; object-fit:contain; display:block; }

      .lp-clinic-name{
        text-align:center; font-size:20px; font-weight:800;
        color:#0A1F44; letter-spacing:-0.3px; margin:0 0 4px;
      }
      .lp-tagline{
        text-align:center; font-size:13px; color:#8AAAC8;
        font-weight:400; margin:0 0 12px;
      }
      .lp-msg{ padding:11px 14px; border-radius:10px; font-size:13px; font-weight:500; margin-bottom:6px; }
      .lp-msg.error{ background:#FFF0F0; color:#C0392B; border:1px solid #F5C6C6; }
      .lp-msg.warn { background:#FFFBEA; color:#92600A; border:1px solid #F5DFA0; }

      /* ── stForm: entire card ── */
      [data-testid="stForm"]{
        width:400px!important;
        margin:0 auto!important;
        background:#ffffff!important;
        border:none!important;
        border-radius:20px!important;
        overflow:hidden!important;
        padding:0!important;
        box-shadow:
          0 28px 40px rgba(0,0,0,0.45),
          -28px 0 40px -10px rgba(0,0,0,0.45),
           28px 0 40px -10px rgba(0,0,0,0.45)!important;
        outline:none!important;
      }
      [data-testid="stForm"] > div,
      [data-testid="stForm"] > div > div,
      [data-testid="stForm"] [data-testid="stVerticalBlock"],
      [data-testid="stForm"] [data-testid="stVerticalBlock"] > div,
      [data-testid="stForm"] .element-container,
      [data-testid="stForm"] [data-testid="stElementContainer"] {
        background:#ffffff!important;
        border:none!important;
        box-shadow:none!important;
      }
      [data-testid="stForm"] [data-testid="stTextInput"],
      [data-testid="stForm"] [data-testid="stFormSubmitButton"] {
        padding-left:32px!important;
        padding-right:32px!important;
      }
      [data-testid="stForm"] label p{
        font-size:10px!important; font-weight:800!important; color:#0047AB!important;
        letter-spacing:1px!important; text-transform:uppercase!important;
      }
      [data-testid="stForm"] [data-baseweb="input"]{
        border-radius:10px!important; border:1.5px solid #D8E6F7!important;
        background:#F6FAFF!important; box-shadow:none!important;
      }
      [data-testid="stForm"] [data-baseweb="input"]:focus-within{
        border-color:#0047AB!important; background:#fff!important;
        box-shadow:0 0 0 3px rgba(0,71,171,0.11)!important;
      }
      [data-testid="stForm"] input{
        font-family:'Plus Jakarta Sans',sans-serif!important;
        font-size:13.5px!important; color:#0A1628!important; background:transparent!important;
      }
      [data-testid="stForm"] input::placeholder{ color:#B8D0E8!important; }
      [data-testid="stForm"] .stFormSubmitButton button{
        width:100%!important; padding:14px!important; margin-top:8px!important;
        background:linear-gradient(135deg,#0047AB 0%,#003080 100%)!important;
        color:#fff!important; border:none!important; border-radius:12px!important;
        font-size:15px!important; font-weight:700!important;
        font-family:'Plus Jakarta Sans',sans-serif!important;
        box-shadow:0 8px 24px rgba(0,71,171,0.32)!important;
        transition:all 0.22s ease!important;
      }
      [data-testid="stForm"] .stFormSubmitButton button:hover{
        background:linear-gradient(135deg,#F59E0B 0%,#D97706 100%)!important;
        box-shadow:0 10px 28px rgba(245,158,11,0.4)!important;
        transform:translateY(-2px)!important;
      }
      [data-testid="stForm"] [data-testid="stVerticalBlock"]{
        gap:0.6rem!important; padding-bottom:32px!important;
      }
    </style>
    """, unsafe_allow_html=True)

    if logo_data_url:
        logo_img = f'<img src="{logo_data_url}" alt="logo"/>'
    else:
        logo_img = '<svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#0047AB" stroke-width="1.7"><path d="M12 2C8 2 5 4.5 5 8c0 2.5 1 4 1.3 6.5.3 2.3.7 5.5 2.2 5.5 1.6 0 1.7-3 2.2-5 .3-1.2.7-2 1.3-2s1 .8 1.3 2c.5 2 .6 5 2.2 5 1.5 0 1.9-3.2 2.2-5.5C17.9 12 19 10.5 19 8c0-3.5-3-6-7-6z"/></svg>'

    msg_html = ""
    lm = st.session_state.get("_login_msg")
    if lm == "wrong":
        msg_html = '<div class="lp-msg error">Incorrect username or password.</div>'
    elif lm == "empty":
        msg_html = '<div class="lp-msg warn">Please enter both username and password.</div>'
    elif lm == "locked":
        msg_html = '<div class="lp-msg error">&#128274; Account locked. Contact your administrator.</div>'
    elif lm == "error":
        msg_html = '<div class="lp-msg error">&#9888; Service error. Please try again.</div>'

    with st.form("login_form", clear_on_submit=True):
        st.markdown(f"""
        <div class="lp-card-top">
          <div class="lp-stripe"></div>
          <div class="lp-top-body">
            <div class="lp-logo-wrap">{logo_img}</div>
            <p class="lp-clinic-name">Shallom Dental Clinic</p>
            <p class="lp-tagline">Sign in to access your workspace</p>
            {msg_html}
          </div>
        </div>
        """, unsafe_allow_html=True)
        lp_u = st.text_input("Username", placeholder="Enter your username")
        lp_p = st.text_input("Password", placeholder="Enter your password", type="password")
        submitted = st.form_submit_button("Sign In →")

    if submitted:
        if lp_u and lp_p:
            result = login_user(lp_u, lp_p)
            status = result.get("status")
            if status == "success":
                u = result["user"]
                st.session_state.update(
                    authenticated=True, user_id=u[0],
                    username=u[1], role=u[2],
                    page="Dashboard", _login_msg=None
                )
                st.rerun()
            else:
                st.session_state._login_msg = (
                    "locked" if status == "locked"
                    else "error" if status == "error"
                    else "wrong"
                )
                st.rerun()
        else:
            st.session_state._login_msg = "empty"
            st.rerun()

    st.stop()


# ══════════════════════════════════════════════════════════════════════════════
# ICONS
# ══════════════════════════════════════════════════════════════════════════════
ICONS = {
    "Dashboard":         '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="9" rx="1.5"/><rect x="14" y="3" width="7" height="5" rx="1.5"/><rect x="14" y="12" width="7" height="9" rx="1.5"/><rect x="3" y="16" width="7" height="5" rx="1.5"/></svg>',
    "Patients":          '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="9" cy="7" r="4"/><path d="M3 21v-2a4 4 0 0 1 4-4h4a4 4 0 0 1 4 4v2"/><path d="M16 3.13a4 4 0 0 1 0 7.75M21 21v-2a4 4 0 0 0-3-3.87"/></svg>',
    "Patient History":   '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M9 5H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2"/><rect x="9" y="3" width="6" height="4" rx="2"/><path d="M9 12h6M9 16h4"/></svg>',
    "Appointments":      '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18M8 14h.01M12 14h.01M16 14h.01M8 18h.01M12 18h.01"/></svg>',
    "Payments":          '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="5" width="20" height="14" rx="2"/><path d="M2 10h20M7 15h2M12 15h3"/></svg>',
    "Inventory":         '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3l9 4.5v9L12 21l-9-4.5v-9L12 3z"/><path d="M12 12l9-4.5M12 12v9M12 12L3 7.5"/></svg>',
    "No-Show Predictor": '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 8v4l3 3"/></svg>',
    "Reports":           '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6M8 13h8M8 17h5"/></svg>',
    "Audit Trail":       '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>',
    "User Management":   '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
    "Profile":           '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="8" r="4"/><path d="M4 20c0-4 3.6-7 8-7s8 3 8 7"/></svg>',
    "About":             '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/></svg>',
}
SIGNOUT_SVG = '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>'

NAV_SECTIONS = [
    ("Main",          ["Dashboard"]),
    ("Clinical",      ["Patients", "Patient History", "Appointments"]),
    ("Finance & Ops", ["Payments", "Inventory"]),
    ("Intelligence",  ["No-Show Predictor", "Reports"]),
    ("System",        ["Audit Trail", "User Management", "Profile", "About"]),
]
ALL_PAGES = [p for _, pages in NAV_SECTIONS for p in pages]

current_role     = st.session_state.get("role")
allowed_pages    = get_allowed_pages(current_role)
# Only show nav sections/items the current role is actually allowed to open.
NAV_SECTIONS = [
    (section_label, [p for p in pages if p in allowed_pages])
    for section_label, pages in NAV_SECTIONS
]
NAV_SECTIONS = [(label, pages) for label, pages in NAV_SECTIONS if pages]

current_page = st.session_state.get("page", "Dashboard")
if current_page not in allowed_pages:
    # Someone navigated to a page their role can't use (stale session state,
    # role changed, or a direct attempt to force a page) -- bounce to
    # Dashboard instead of silently rendering restricted content.
    current_page = "Dashboard"
    st.session_state.page = "Dashboard"

username_display = st.session_state.get("username", "User")
role_display     = st.session_state.get("role", "staff").title()
initials         = (username_display[:2]).upper()

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
  [data-testid="stSidebar"]{
    background:linear-gradient(180deg,#071830 0%,#0D2952 100%)!important;
    width:265px!important; min-width:265px!important; max-width:265px!important;
    border-right:none!important;
  }
  [data-testid="stSidebar"]>div,
  section[data-testid="stSidebarContent"]{ padding:0!important; }
  [data-testid="stSidebar"] [data-testid="stVerticalBlockSeparator"],
  [data-testid="stSidebar"] hr{ display:none!important; }

  [data-testid="stSidebar"] [data-testid="stVerticalBlock"]{ gap:0!important; }
  [data-testid="stSidebar"] .element-container,
  [data-testid="stSidebar"] [data-testid="stElementContainer"]{ margin:0!important; }

  /* ── Nav item ── */
  .sn-item{
    display:flex; align-items:center; gap:12px;
    height:44px;
    box-sizing:border-box;
    padding:0 16px;
    margin:3px 10px;
    border-radius:10px;
    cursor:pointer; transition:background 0.15s, transform 0.15s;
    user-select:none;
  }
  .sn-item:hover{ background:rgba(255,255,255,0.08); transform:translateX(3px); }
  .sn-item.active{
    background:linear-gradient(135deg,#F59E0B 0%,#FBBF24 100%);
    box-shadow:0 3px 10px rgba(245,158,11,0.30);
  }
  .sn-item.active .sn-icon svg{ stroke:#0A1F44!important; }
  .sn-item.active .sn-label{ color:#0A1F44!important; font-weight:700!important; }
  .sn-icon{ width:20px; height:20px; display:flex; align-items:center; justify-content:center; flex-shrink:0; }
  .sn-icon svg{ stroke:rgba(255,255,255,0.6); }
  .sn-label{ font-size:13.5px; font-weight:500; color:rgba(255,255,255,0.78); flex:1; }

  .sn-sec{
    font-size:10.5px; font-weight:800;
    color:rgba(245,158,11,0.85);
    letter-spacing:1.5px; text-transform:uppercase;
    padding:20px 24px 12px;
    position:relative;
    z-index:5;
  }

  .sn-out{
    display:flex; align-items:center; gap:12px;
    height:44px;
    box-sizing:border-box;
    padding:0 16px;
    margin:12px 10px 4px;
    border-radius:10px;
    cursor:pointer; border:1.5px solid rgba(245,158,11,0.28);
    background:rgba(245,158,11,0.07);
    transition:background 0.15s, transform 0.15s; user-select:none;
  }
  .sn-out:hover{ background:rgba(245,158,11,0.18); border-color:rgba(245,158,11,0.6); transform:translateX(3px); }
  .sn-out svg{ stroke:#F59E0B; }
  .sn-out-label{ font-size:13px; font-weight:700; color:#F59E0B; flex:1; }

  /* ── Invisible click-capture buttons ── */
  [data-testid="stSidebar"] .stButton {
    margin:0 10px!important;
  }
  [data-testid="stSidebar"] .stButton > button {
    background:transparent!important; border:none!important;
    box-shadow:none!important; color:transparent!important;
    height:44px!important;
    box-sizing:border-box!important;
    width:100%!important;
    padding:0!important; cursor:pointer!important;
    opacity:0!important;
  }
  [data-testid="stSidebar"] .stButton > button:hover {
    background:transparent!important;
  }
</style>
""", unsafe_allow_html=True)

with st.sidebar:

    if logo_data_url:
        logo_sb = (
            f'<img src="{logo_data_url}" '
            f'style="width:54px;height:54px;border-radius:10px;object-fit:contain;'
            f'background:#fff;border:2.5px solid rgba(245,158,11,0.55);flex-shrink:0;" alt="logo"/>'
        )
    else:
        logo_sb = '<div style="width:54px;height:54px;border-radius:10px;background:linear-gradient(135deg,#F59E0B,#FBBF24);display:flex;align-items:center;justify-content:center;border:2.5px solid rgba(245,158,11,0.55);font-size:24px;flex-shrink:0;">🦷</div>'

    st.markdown(f"""
    <div style="padding:22px 16px 14px;display:flex;align-items:center;gap:13px;">
      {logo_sb}
      <div>
        <div style="font-size:15px;font-weight:800;color:#fff;letter-spacing:-0.3px;line-height:1.2;">Shallom Dental</div>
        <div style="font-size:11px;color:rgba(245,158,11,0.8);font-weight:500;margin-top:3px;">Clinic Management</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style="margin:14px 10px 18px;background:rgba(255,255,255,0.05);
        border:1px solid rgba(255,255,255,0.09);border-radius:13px;
        padding:11px 14px;display:flex;align-items:center;gap:11px;">
      <div style="width:36px;height:36px;border-radius:9px;flex-shrink:0;
          background:linear-gradient(135deg,#0047AB,#003080);
          border:2px solid rgba(245,158,11,0.5);
          display:flex;align-items:center;justify-content:center;
          font-size:12px;font-weight:800;color:#F59E0B;">{initials}</div>
      <div style="flex:1;min-width:0;">
        <div style="font-size:13.5px;font-weight:700;color:#fff;
            white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{username_display}</div>
        <div style="font-size:9px;font-weight:600;color:rgba(245,158,11,0.65);
            text-transform:none;letter-spacing:0.3px;margin-top:2px;">{role_display}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    NAV_BTN_H = 44  # must match height in CSS above

    for section_label, pages in NAV_SECTIONS:
        st.markdown(f'<div class="sn-sec">{section_label}</div>', unsafe_allow_html=True)
        for page_name in pages:
            icon   = ICONS.get(page_name, "")
            active = "active" if page_name == current_page else ""
            st.markdown(
                f'<div class="sn-item {active}" style="pointer-events:none;margin-bottom:-{NAV_BTN_H}px;">'
                f'<span class="sn-icon">{icon}</span>'
                f'<span class="sn-label">{page_name}</span></div>',
                unsafe_allow_html=True
            )
            if st.button(page_name, key=f"nav_{page_name}", use_container_width=True):
                st.session_state.page = page_name
                st.rerun()

    st.markdown(
        f'<div class="sn-out" style="pointer-events:none;margin-bottom:-{NAV_BTN_H}px;">'
        f'<span class="sn-icon">{SIGNOUT_SVG}</span>'
        f'<span class="sn-out-label">Sign Out</span></div>',
        unsafe_allow_html=True
    )
    if st.button("Sign Out ", key="nav_signout", use_container_width=True):
        logout()

    st.markdown("""
    <div style="text-align:center;color:rgba(255,255,255,0.16);font-size:10.5px;
        padding:20px 0 24px;">v1.0.0 · Shallom Dental</div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN CONTENT
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
  .stApp{ background:#EEF3FA!important; }
  .block-container{ padding:2rem 2.5rem!important; max-width:100%!important; }
  [data-testid="stForm"]{ border:none!important; background:transparent!important; padding:0!important; }
  .ui-card{
    background:#fff; border-radius:16px; padding:22px 26px;
    box-shadow:0 2px 14px rgba(0,71,171,0.07);
    border:1px solid rgba(0,71,171,0.06); margin-bottom:18px;
  }
  .page-title{ font-size:25px; font-weight:800; color:#0A1F44; letter-spacing:-0.5px; margin-bottom:2px; }
  .page-subtitle{ font-size:13px; color:#6B8EAC; margin-bottom:22px; }
  .stSelectbox>div>div, .stTextInput>div>div>input,
  .stTextArea>div>div>textarea, .stDateInput>div>div>input,
  .stNumberInput>div>div>input{
    border-radius:10px!important; border-color:#D0DFF0!important;
  }
  .stDataFrame,.stTable{ border-radius:12px; overflow:hidden; }
</style>
""", unsafe_allow_html=True)

page = st.session_state.get("page", "Dashboard")

# Defense in depth: even though the nav above already hides/bounces
# disallowed pages, re-check right before rendering. This protects against
# any future code path that sets st.session_state.page directly.
if not can_view_page(current_role, page):
    st.error("Access denied. You don't have permission to view this page.")
    st.session_state.page = "Dashboard"
    page = "Dashboard"

if page == "Dashboard":
    from pages.home import show_dashboard; show_dashboard()
elif page == "Patients":
    from pages.patients import show_patients; show_patients()
elif page == "Patient History":
    from pages.patient_history import show_patient_history; show_patient_history()
elif page == "Appointments":
    from pages.appointments import show_appointments; show_appointments()
elif page == "Payments":
    from pages.payments import show_payments; show_payments()
elif page == "Inventory":
    from pages.inventory import show_inventory; show_inventory()
elif page == "No-Show Predictor":
    from pages.prediction import show_prediction; show_prediction()
elif page == "Reports":
    from pages.reports import show_reports; show_reports()
elif page == "Audit Trail":
    from pages.audit_trail import show_audit_trail; show_audit_trail()
elif page == "User Management":
    from pages.user_management import show_user_management; show_user_management()
elif page == "Profile":
    from pages.profile import show_profile; show_profile()
elif page == "About":
    from pages.about import show_about; show_about()