# pages/about.py
import streamlit as st
from datetime import datetime
from utils.db import get_connection


def show_about():
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

        /* ── STAT CARDS ── */
        .stat-card {
            background: #fff;
            border: 1.5px solid #E2E8F0;
            border-radius: 20px;
            padding: 26px 20px;
            text-align: center;
            box-shadow: 0 2px 10px rgba(30,74,118,0.05);
        }
        .stat-num { font-size: 34px; font-weight: 800; color: #1E4A76; margin: 0 0 6px; letter-spacing: -1px; }
        .stat-lbl { font-size: 11px; color: #6B8FAB; font-weight: 700; text-transform: uppercase; letter-spacing: 0.8px; }

        /* ── SECTION LABEL ── */
        .sec-label {
            font-size: 11px; font-weight: 700; color: #6B8FAB;
            letter-spacing: 1.2px; text-transform: uppercase;
            margin: 32px 0 20px;
        }

        /* ── CONTENT CARDS ── */
        .cc {
            background: #fff;
            border: 1.5px solid #E2E8F0;
            border-radius: 20px;
            padding: 26px;
            box-shadow: 0 2px 10px rgba(30,74,118,0.05);
            height: 100%;
        }
        .cc-hd {
            display: flex; align-items: center; gap: 12px;
            margin-bottom: 18px; padding-bottom: 14px;
        }
        .cc-hd-ic {
            width: 40px; height: 40px;
            background: #EBF3FB;
            border-radius: 12px;
            display: flex; align-items: center; justify-content: center;
            flex-shrink: 0;
        }
        .cc-hd-title { font-size: 15px; font-weight: 700; color: #1A3A5C; margin: 0; }

        /* ── FEATURE GRID ── */
        .feat-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 14px; }
        .feat-item {
            display: flex; align-items: center; gap: 9px;
            padding: 9px 12px;
            background: #F8FAFD;
            border: 1px solid #EEF2F7;
            border-radius: 10px;
            font-size: 12.5px; color: #1A3A5C; font-weight: 500;
        }
        .feat-dot { width: 6px; height: 6px; background: #E88C30; border-radius: 50%; flex-shrink: 0; }

        /* ── INFO ROWS (tech stack) ── */
        .info-row {
            display: flex; justify-content: space-between; align-items: center;
            padding: 11px 0;
        }
        .info-lbl { font-size: 12px; font-weight: 700; color: #6B8FAB; text-transform: uppercase; letter-spacing: 0.5px; }
        .info-val { font-size: 13.5px; color: #1A3A5C; font-weight: 600; }
        .info-tag {
            display: inline-block; background: #EBF3FB;
            color: #1E4A76; font-size: 12px; font-weight: 700;
            padding: 3px 12px; border-radius: 20px;
        }
        .info-tag-amber {
            display: inline-block; background: #FDEBD3;
            color: #B5670F; font-size: 12px; font-weight: 700;
            padding: 3px 12px; border-radius: 20px;
        }

        /* ── PERSON CARDS ── */
        .person-card {
            background: linear-gradient(135deg, #1E4A76 0%, #2D6A9F 100%);
            border-radius: 20px;
            padding: 24px;
            box-shadow: 0 4px 16px rgba(30,74,118,0.18);
            position: relative; overflow: hidden;
        }
        .person-card::before {
            content: ''; position: absolute; right: -20px; bottom: -20px;
            width: 100px; height: 100px;
            background: radial-gradient(circle, rgba(232,140,48,0.15) 0%, transparent 70%);
            pointer-events: none;
        }
        .person-hd { display: flex; align-items: center; gap: 14px; margin-bottom: 16px; position: relative; z-index: 1; }
        .person-av {
            width: 52px; height: 52px;
            background: rgba(255,255,255,0.12);
            border: 1.5px solid rgba(255,255,255,0.2);
            border-radius: 16px;
            display: flex; align-items: center; justify-content: center;
            font-size: 17px; font-weight: 800; color: #E88C30;
            flex-shrink: 0;
        }
        .person-role { font-size: 10px; font-weight: 700; color: rgba(255,255,255,0.5); text-transform: uppercase; letter-spacing: 0.8px; margin: 0 0 3px; }
        .person-name { font-size: 17px; font-weight: 800; color: #fff; margin: 0; letter-spacing: -0.2px; }
        .person-body { position: relative; z-index: 1; }
        .person-row {
            display: flex; align-items: baseline; gap: 8px;
            font-size: 12.5px; color: rgba(255,255,255,0.65);
            padding: 5px 0;
        }
        .person-row-lbl { font-size: 10px; font-weight: 700; color: rgba(255,255,255,0.4); text-transform: uppercase; letter-spacing: 0.5px; min-width: 72px; }
        .person-row-val { color: rgba(255,255,255,0.85); font-weight: 500; }

        /* ── CLINIC INFO GRID ── */
        .clinic-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-top: 4px; }
        .clinic-item {
            background: #F8FAFD;
            border: 1px solid #EEF2F7;
            border-radius: 14px;
            padding: 16px 14px;
            text-align: center;
        }
        .clinic-lbl { font-size: 10px; font-weight: 700; color: #6B8FAB; text-transform: uppercase; letter-spacing: 0.6px; margin: 0 0 6px; }
        .clinic-val { font-size: 13px; font-weight: 600; color: #1A3A5C; margin: 0; }

        /* ── TIMELINE CARDS ── */
        .tl-card {
            background: #fff;
            border: 1.5px solid #E2E8F0;
            border-radius: 18px;
            padding: 22px 16px;
            text-align: center;
            box-shadow: 0 2px 10px rgba(30,74,118,0.05);
            position: relative;
        }
        .tl-num {
            width: 32px; height: 32px;
            background: linear-gradient(135deg, #1E4A76, #2D6A9F);
            border-radius: 50%;
            display: inline-flex; align-items: center; justify-content: center;
            color: #fff; font-size: 13px; font-weight: 700;
            margin-bottom: 14px;
            box-shadow: 0 3px 10px rgba(30,74,118,0.25);
        }
        .tl-period { font-size: 11px; font-weight: 700; color: #E88C30; margin: 0 0 6px; letter-spacing: 0.3px; }
        .tl-title { font-size: 13.5px; font-weight: 700; color: #1A3A5C; margin: 0; }

        /* ── FOOTER ── */
        .about-footer {
            background: linear-gradient(135deg, #1E4A76 0%, #2D6A9F 100%);
            border-radius: 24px;
            padding: 40px;
            text-align: center;
            margin-top: 8px;
            box-shadow: 0 8px 24px rgba(30,74,118,0.15);
            position: relative; overflow: hidden;
        }
        .about-footer::before {
            content: ''; position: absolute; left: 50%; top: -60px; transform: translateX(-50%);
            width: 300px; height: 300px;
            background: radial-gradient(circle, rgba(255,255,255,0.04) 0%, transparent 70%);
            pointer-events: none;
        }
        .af-title { font-size: 22px; font-weight: 800; color: #fff; margin: 0 0 8px; letter-spacing: -0.3px; position: relative; z-index: 1; }
        .af-sub { font-size: 14px; color: rgba(255,255,255,0.65); margin: 0 0 6px; position: relative; z-index: 1; }
        .af-copy { font-size: 12px; color: rgba(255,255,255,0.4); margin: 0; position: relative; z-index: 1; }

        .access-date {
            text-align: center; color: #6B8FAB;
            font-size: 12px; margin-top: 20px; font-weight: 500;
        }
    </style>
    """, unsafe_allow_html=True)

    # ── GET DATA ──
    conn = get_connection()
    patient_count = 0
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM patients")
        patient_count = cursor.fetchone()[0]
        cursor.close()
        conn.close()

    module_count = 9
    model_accuracy = "99.94%"

    # ── PAGE HEADER ──
    st.markdown("""
    <div class="page-header">
        <div class="ph-left">
            <div class="ph-icon">
                <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="1.8">
                    <circle cx="12" cy="12" r="10"/>
                    <line x1="12" y1="8" x2="12" y2="12"/>
                    <circle cx="12" cy="16" r="0.5" fill="white"/>
                </svg>
            </div>
            <div>
                <p class="ph-title">About This System</p>
                <p class="ph-subtitle">Shallom Dental Clinic Management and Prediction System — Final Year Project</p>
            </div>
        </div>
        <div class="ph-badge">Dimploma in Computer Science</div>
    </div>
    """, unsafe_allow_html=True)

    # ── STAT CARDS ──
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-num">{patient_count:,}+</div>
            <div class="stat-lbl">Patient Records</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-num">{model_accuracy}</div>
            <div class="stat-lbl">Model Accuracy</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-num">{module_count}</div>
            <div class="stat-lbl">System Modules</div>
        </div>""", unsafe_allow_html=True)

    # ── SECTION: SYSTEM OVERVIEW ──
    st.markdown("""
    <div class="sec-label">System Overview</div>""", unsafe_allow_html=True)

    col1, col2 = st.columns(2, gap="medium")

    with col1:
        st.markdown("""
        <div class="cc">
            <div class="cc-hd">
                <div class="cc-hd-ic">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#1E4A76" stroke-width="1.8">
                        <circle cx="12" cy="12" r="10"/>
                        <line x1="12" y1="16" x2="12" y2="12"/>
                        <circle cx="12" cy="8" r="0.5" fill="#1E4A76"/>
                    </svg>
                </div>
                <p class="cc-hd-title">Project Overview</p>
            </div>
            <p style="font-size:13.5px;color:#5C7A9A;line-height:1.65;margin:0 0 14px;">
                <strong style="color:#1A3A5C;">Shallom Dental Clinic Management System</strong> is a comprehensive
                digital solution designed to modernize and streamline daily clinic operations at Shallom Dental Clinic, Kampala.
            </p>
            <div class="feat-grid">
                <div class="feat-item"><div class="feat-dot"></div>Patient Management</div>
                <div class="feat-item"><div class="feat-dot"></div>Appointment Scheduling</div>
                <div class="feat-item"><div class="feat-dot"></div>Payment Tracking</div>
                <div class="feat-item"><div class="feat-dot"></div>Inventory Management</div>
                <div class="feat-item"><div class="feat-dot"></div>No-Show Prediction</div>
                <div class="feat-item"><div class="feat-dot"></div>Analytics &amp; Reports</div>
                <div class="feat-item"><div class="feat-dot"></div>Audit Trail</div>
                <div class="feat-item"><div class="feat-dot"></div>Role-Based Access</div>
            </div>
        </div>""", unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="cc">
            <div class="cc-hd">
                <div class="cc-hd-ic">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#1E4A76" stroke-width="1.8">
                        <polyline points="16 18 22 12 16 6"/>
                        <polyline points="8 6 2 12 8 18"/>
                    </svg>
                </div>
                <p class="cc-hd-title">Technical Stack</p>
            </div>
            <div class="info-row">
                <span class="info-lbl">Frontend</span>
                <span class="info-tag">Streamlit</span>
            </div>
            <div class="info-row">
                <span class="info-lbl">Backend</span>
                <span class="info-tag">Python 3</span>
            </div>
            <div class="info-row">
                <span class="info-lbl">Database</span>
                <span class="info-tag">PostgreSQL</span>
            </div>
            <div class="info-row">
                <span class="info-lbl">ML Library</span>
                <span class="info-tag">scikit-learn</span>
            </div>
            <div class="info-row">
                <span class="info-lbl">ML Model</span>
                <span class="info-tag">Random Forest</span>
            </div>
            <div class="info-row">
                <span class="info-lbl">Model Accuracy</span>
                <span class="info-tag-amber">99.94%</span>
            </div>
        </div>""", unsafe_allow_html=True)

    # ── SECTION: PEOPLE ──
    st.markdown("""
    <div class="sec-label">Developer &amp; Supervisor</div>""", unsafe_allow_html=True)

    col1, col2 = st.columns(2, gap="medium")

    with col1:
        st.markdown("""
        <div class="person-card">
            <div class="person-hd">
                <div class="person-av">FR</div>
                <div>
                    <p class="person-role">Developer</p>
                    <p class="person-name">Fayima Rahuman</p>
                </div>
            </div>
            <div class="person-body">
                <div class="person-row">
                    <span class="person-row-lbl">Email</span>
                    <span class="person-row-val">fayimarahuman2002@gmail.com</span>
                </div>
                <div class="person-row">
                    <span class="person-row-lbl">Phone</span>
                    <span class="person-row-val">+256 777 150997</span>
                </div>
                <div class="person-row">
                    <span class="person-row-lbl">Program</span>
                    <span class="person-row-val">Diploma in Computer Science</span>
                </div>
                <div class="person-row">
                    <span class="person-row-lbl">Institute</span>
                    <span class="person-row-val">Women Institute of Technology and Innovation</span>
                </div>
            </div>
        </div>""", unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="person-card">
            <div class="person-hd">
                <div class="person-av">SN</div>
                <div>
                    <p class="person-role">Supervisor</p>
                    <p class="person-name">Miss Tugume Brenda</p>
                </div>
            </div>
            <div class="person-body">
                <div class="person-row">
                    <span class="person-row-lbl">Email</span>
                    <span class="person-row-val">tugume.brenda@witu.org</span>
                </div>
                <div class="person-row">
                    <span class="person-row-lbl">Phone</span>
                    <span class="person-row-val">+256 700 789012</span>
                </div>
                <div class="person-row">
                    <span class="person-row-lbl">Department</span>
                    <span class="person-row-val">Computer Science</span>
                </div>
                <div class="person-row">
                    <span class="person-row-lbl">Institution</span>
                    <span class="person-row-val">Women Institute of Technology and Innovation</span>
                </div>
            </div>
        </div>""", unsafe_allow_html=True)

    # ── CLINIC INFO ──
    st.markdown("""
    <div class="sec-label">Clinic Information</div>""", unsafe_allow_html=True)

    st.markdown("""
    <div class="cc">
        <div class="cc-hd">
            <div class="cc-hd-ic">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#1E4A76" stroke-width="1.8">
                    <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
                    <polyline points="9 22 9 12 15 12 15 22"/>
                </svg>
            </div>
            <p class="cc-hd-title">Shallom Dental Clinic</p>
        </div>
        <div class="clinic-grid">
            <div class="clinic-item">
                <p class="clinic-lbl">Clinic Name</p>
                <p class="clinic-val">Shallom Dental Clinic</p>
            </div>
            <div class="clinic-item">
                <p class="clinic-lbl">Location</p>
                <p class="clinic-val">Kyaliwajala, Uganda</p>
            </div>
            <div class="clinic-item">
                <p class="clinic-lbl">Email</p>
                <p class="clinic-val">info@shallomdental.com</p>
            </div>
            <div class="clinic-item">
                <p class="clinic-lbl">Phone</p>
                <p class="clinic-val">+256 755 358549</p>
            </div>
        </div>
    </div>""", unsafe_allow_html=True)

    # ── PROJECT TIMELINE ──
    st.markdown("""
    <div class="sec-label">Project Timeline</div>""", unsafe_allow_html=True)

    tc1, tc2, tc3, tc4 = st.columns(4, gap="small")
    with tc1:
        st.markdown("""
        <div class="tl-card">
            <div class="tl-num">1</div>
            <p class="tl-period">2024 – 2025</p>
            <p class="tl-title">Data Collection</p>
        </div>""", unsafe_allow_html=True)
    with tc2:
        st.markdown("""
        <div class="tl-card">
            <div class="tl-num">2</div>
            <p class="tl-period">Jan 2026</p>
            <p class="tl-title">Model Development</p>
        </div>""", unsafe_allow_html=True)
    with tc3:
        st.markdown("""
        <div class="tl-card">
            <div class="tl-num">3</div>
            <p class="tl-period">Mar 2026</p>
            <p class="tl-title">System Development</p>
        </div>""", unsafe_allow_html=True)
    with tc4:
        st.markdown("""
        <div class="tl-card">
            <div class="tl-num">4</div>
            <p class="tl-period">Jun 2026</p>
            <p class="tl-title">Presentation</p>
        </div>""", unsafe_allow_html=True)

    # ── FOOTER ──
    st.markdown("""
    <div class="about-footer">
        <p class="af-title">Final Year Project — 2026</p>
        <p class="af-sub">Diploma of Science in Computer Science · Women Institute of Technology and Innovation</p>
        <p class="af-copy">&copy; 2026 · Shallom Dental Clinic · All Rights Reserved</p>
    </div>""", unsafe_allow_html=True)

    st.markdown(
        f'<div class="access-date">System accessed on: {datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")}</div>',
        unsafe_allow_html=True
    )