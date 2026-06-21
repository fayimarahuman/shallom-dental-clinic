# pages/reports.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from utils.db import get_connection
from utils.sanitize import esc
import base64


def show_reports():
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

        /* ── SECTION LABELS ── */
        .sec-label {
            font-size: 11px; font-weight: 700; color: #6B8FAB;
            letter-spacing: 1.2px; text-transform: uppercase;
            margin: 0 0 18px 2px;
            display: flex; align-items: center; gap: 8px;
        }

        /* ── SELECTBOX — comprehensive fix ── */
        .stSelectbox label {
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

        /* ── BUTTONS ── */
        .stButton button {
            background: linear-gradient(135deg, #1E4A76, #2D6A9F) !important;
            border: none !important; border-radius: 12px !important;
            padding: 12px 24px !important; font-weight: 600 !important;
            font-size: 14px !important; color: #fff !important;
            box-shadow: 0 2px 10px rgba(30,74,118,0.2) !important;
            transition: all 0.2s ease !important;
        }
        .stButton button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 16px rgba(30,74,118,0.25) !important;
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

        /* ── REPORT TABLE (matches appointments style) ── */
        .rpt-table-wrap {
            background: #fff;
            border-radius: 18px;
            border: 1.5px solid #E2E8F0;
            overflow: hidden;
            box-shadow: 0 4px 20px rgba(30,74,118,0.07);
            margin-top: 4px;
        }
        .rpt-table { width: 100%; border-collapse: collapse; }
        .rpt-table thead tr { background: linear-gradient(135deg, #1E4A76 0%, #2D6A9F 100%); }
        .rpt-table thead th {
            padding: 13px 18px;
            text-align: left;
            font-size: 10.5px; font-weight: 700;
            letter-spacing: 1.1px; text-transform: uppercase;
            color: rgba(255,255,255,0.75);
            white-space: nowrap; border: none;
        }
        .rpt-table tbody tr { border-bottom: 1px solid #F0F5FA; transition: background 0.12s ease; }
        .rpt-table tbody tr:last-child { border-bottom: none; }
        .rpt-table tbody tr:hover { background: #F7FAFD; }
        .rpt-table tbody td {
            padding: 13px 18px; vertical-align: middle; border: none;
            font-size: 13.5px; color: #2D4A6B;
        }
        .rpt-metric-label { font-weight: 600; color: #1A3A5C; }
        .rpt-metric-value { font-weight: 700; color: #1E4A76; }
        .rpt-month { font-size: 12.5px; color: #6B8FAB; font-weight: 500; white-space: nowrap; }
        .rpt-count { font-weight: 700; color: #1E4A76; }
        .rpt-tag {
            display: inline-block; font-size: 11px; font-weight: 700;
            padding: 4px 12px; border-radius: 20px; letter-spacing: 0.2px;
        }
        .rpt-tag-blue  { background: #DBEAFE; color: #1E4A76; }
        .rpt-tag-amber { background: #FDEBD3; color: #B5670F; }
        .rpt-tag-red   { background: #FEE2E2; color: #B91C1C; }
        .rpt-table-footer {
            padding: 11px 18px; background: #F8FAFD;
            border-top: 1px solid #E2E8F0;
            font-size: 12px; color: #6B8FAB; font-weight: 600;
        }

        /* ── DOWNLOAD LINK BUTTON ── */
        .dl-wrap { display: flex; justify-content: flex-end; margin-bottom: 18px; }
        .dl-btn {
            background: #1E4A76; color: #fff !important;
            padding: 9px 20px; border-radius: 12px;
            text-decoration: none !important;
            font-size: 12.5px; font-weight: 600;
            display: inline-flex; align-items: center; gap: 8px;
            box-shadow: 0 2px 8px rgba(30,74,118,0.2);
            transition: background 0.15s;
        }
        .dl-btn:hover { background: #2D6A9F; }

        /* ── INFO STRIP ── */
        .info-strip {
            display: flex; align-items: center; gap: 10px;
            background: #EBF3FB; border: 1px solid #B5D4F4;
            border-radius: 12px; padding: 12px 18px;
            font-size: 13px; color: #1A3A5C; font-weight: 500;
            margin-top: 16px;
        }

        /* ── PRINT HINT ── */
        .print-hint {
            display: flex; align-items: center; gap: 10px;
            background: #F8FAFD; border: 1.5px solid #E2E8F0;
            border-radius: 12px; padding: 12px 18px;
            font-size: 13px; color: #6B8FAB; font-weight: 500;
            margin-bottom: 20px;
        }

        /* ── EMPTY STATE ── */
        .empty-state {
            background: #fff; border: 1.5px dashed #CBD5E1;
            border-radius: 20px; padding: 48px 32px; text-align: center;
        }

        @media print {
            section[data-testid="stSidebar"] { display: none !important; }
            .stButton, .dl-wrap, .stSelectbox, .page-header, .print-hint { display: none !important; }
        }
    </style>
    """, unsafe_allow_html=True)

    # ── PAGE HEADER ──
    st.markdown("""
    <div class="page-header">
        <div class="ph-left">
            <div class="ph-icon">
                <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="1.8">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                    <polyline points="14 2 14 8 20 8"/>
                    <line x1="16" y1="13" x2="8" y2="13"/>
                    <line x1="16" y1="17" x2="8" y2="17"/>
                </svg>
            </div>
            <div>
                <p class="ph-title">Clinic Reports &amp; Analytics</p>
                <p class="ph-subtitle">Daily summaries, monthly trends, financials, and no-show analysis</p>
            </div>
        </div>
        <div class="ph-badge">Live Data</div>
    </div>
    """, unsafe_allow_html=True)

    # ── REPORT TYPE SELECTOR ──
    report_type = st.selectbox(
        "Select Report Type",
        ["Daily Summary", "Monthly Trends", "Treatment Analysis", "Financial Report", "No-Show Analysis"]
    )

    # ── PRINT HINT ──
    st.markdown("""
    <div class="print-hint">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#6B8FAB" stroke-width="2">
            <polyline points="6 9 6 2 18 2 18 9"/><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/>
            <rect x="6" y="14" width="12" height="8"/>
        </svg>
        To print or export as PDF — press <strong>&nbsp;Ctrl + P&nbsp;</strong> (Windows) or <strong>&nbsp;Cmd + P&nbsp;</strong> (Mac)
    </div>
    """, unsafe_allow_html=True)

    conn = get_connection()
    if not conn:
        st.error("Database connection failed.")
        return
    cursor = conn.cursor()

    def csv_download_link(df, filename):
        csv = df.to_csv(index=False)
        b64 = base64.b64encode(csv.encode()).decode()
        return f'''
        <div class="dl-wrap">
            <a class="dl-btn" href="data:file/csv;base64,{b64}" download="{filename}.csv">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.2">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                    <polyline points="7 10 12 15 17 10"/>
                    <line x1="12" y1="15" x2="12" y2="3"/>
                </svg>
                Download CSV
            </a>
        </div>'''

    # ══════════════════════════════════════════════════════
    # DAILY SUMMARY
    # ══════════════════════════════════════════════════════
    if report_type == "Daily Summary":
        st.markdown("""
        <div class="sec-label">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#E88C30" stroke-width="2">
                <rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/>
                <line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>
            </svg>
            Daily Summary
        </div>""", unsafe_allow_html=True)

        today = datetime.now().date()

        cursor.execute("SELECT COUNT(*) FROM appointments WHERE appointment_date = %s", (today,))
        today_appointments = int(cursor.fetchone()[0] or 0)
        cursor.execute("SELECT COUNT(*) FROM appointments WHERE appointment_date = %s AND status = 'Completed'", (today,))
        completed = int(cursor.fetchone()[0] or 0)
        cursor.execute("SELECT COUNT(*) FROM appointments WHERE appointment_date = %s AND status = 'No-show'", (today,))
        noshow = int(cursor.fetchone()[0] or 0)
        cursor.execute("SELECT COALESCE(SUM(amount_paid), 0) FROM payments WHERE payment_date = %s", (today,))
        today_revenue = float(cursor.fetchone()[0] or 0)
        cursor.execute("SELECT COUNT(*) FROM appointments WHERE appointment_date > %s AND status = 'Scheduled'", (today,))
        upcoming = int(cursor.fetchone()[0] or 0)

        df_report = pd.DataFrame({
            'Metric': ['Appointments Today', 'Completed', 'No-Shows', "Today's Revenue", 'Upcoming Scheduled'],
            'Value': [today_appointments, completed, noshow, f"UGX {today_revenue:,.0f}", upcoming]
        })
        st.markdown(csv_download_link(df_report, f"daily_summary_{today}"), unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Appointments Today", today_appointments)
        with c2:
            st.metric("Completed", completed)
        with c3:
            st.metric("No-Shows", noshow)

        c4, c5 = st.columns(2)
        with c4:
            st.metric("Today's Revenue", f"UGX {today_revenue:,.0f}")
        with c5:
            st.metric("Upcoming Scheduled", upcoming)

        # Summary table
        rows = ""
        icons = {
            "Appointments Today": ("rpt-tag-blue", "📅"),
            "Completed":          ("rpt-tag-amber", "✓"),
            "No-Shows":           ("rpt-tag-red", "✗"),
            "Today's Revenue":    ("rpt-tag-blue", "💰"),
            "Upcoming Scheduled": ("rpt-tag-blue", "🗓"),
        }
        for _, row in df_report.iterrows():
            tag_cls = icons.get(row["Metric"], ("rpt-tag-blue",))[0]
            rows += f"""
            <tr>
                <td><span class="rpt-metric-label">{row['Metric']}</span></td>
                <td><span class="rpt-metric-value">{row['Value']}</span></td>
            </tr>"""

        st.markdown(f"""
        <div class="rpt-table-wrap" style="margin-top:24px;">
            <table class="rpt-table">
                <thead><tr><th>Metric</th><th>Value</th></tr></thead>
                <tbody>{rows}</tbody>
            </table>
            <div class="rpt-table-footer">Summary for {today}</div>
        </div>""", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════
    # MONTHLY TRENDS
    # ══════════════════════════════════════════════════════
    elif report_type == "Monthly Trends":
        st.markdown("""
        <div class="sec-label">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#E88C30" stroke-width="2">
                <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
            </svg>
            Monthly Trends
        </div>""", unsafe_allow_html=True)

        cursor.execute("""
            SELECT month, total, noshows FROM (
                SELECT TO_CHAR(appointment_date, 'YYYY-MM') as month, COUNT(*) as total,
                       SUM(CASE WHEN status = 'No-show' THEN 1 ELSE 0 END) as noshows
                FROM appointments GROUP BY month ORDER BY month DESC LIMIT 12
            ) recent_months ORDER BY month ASC
        """)
        monthly_data = cursor.fetchall()

        if monthly_data:
            data_list = []
            for row in monthly_data:
                total_appts = int(row[1] or 0)
                noshows_count = int(row[2] or 0)
                noshow_percent = (noshows_count / total_appts * 100) if total_appts > 0 else 0
                data_list.append({
                    'Month': row[0],
                    'Total Appointments': total_appts,
                    'No-Shows': noshows_count,
                    'No-Show Rate (%)': round(noshow_percent, 1)
                })
            df = pd.DataFrame(data_list)

            st.markdown(csv_download_link(df, f"monthly_trends_{datetime.now().strftime('%Y%m%d')}"), unsafe_allow_html=True)

            fig1 = px.bar(df, x='Month', y='Total Appointments',
                          color_discrete_sequence=['#1E4A76'], text='Total Appointments')
            fig1.update_traces(textposition='outside', marker_line_width=0)
            fig1.update_layout(
                title=dict(text='Monthly Appointment Volume', font=dict(family='Inter', size=14, color='#1A3A5C')),
                plot_bgcolor='white', paper_bgcolor='white',
                height=380, margin=dict(t=48, b=40, l=12, r=12),
                xaxis=dict(showgrid=False, tickfont=dict(family='Inter', size=11, color='#6B8FAB')),
                yaxis=dict(gridcolor='#F0F5FA', tickfont=dict(family='Inter', size=11, color='#6B8FAB')),
                font=dict(family='Inter')
            )
            st.plotly_chart(fig1, use_container_width=True)

            fig2 = go.Figure(go.Scatter(
                x=df['Month'], y=df['No-Show Rate (%)'],
                mode='lines+markers',
                line=dict(color='#E88C30', width=3),
                marker=dict(color='#E88C30', size=9, line=dict(color='white', width=2)),
                fill='tozeroy', fillcolor='rgba(232,140,48,0.07)'
            ))
            fig2.update_layout(
                title=dict(text='No-Show Rate (%)', font=dict(family='Inter', size=14, color='#1A3A5C')),
                plot_bgcolor='white', paper_bgcolor='white',
                height=320, margin=dict(t=48, b=40, l=12, r=12),
                xaxis=dict(showgrid=False, tickfont=dict(family='Inter', size=11, color='#6B8FAB')),
                yaxis=dict(gridcolor='#F0F5FA', tickfont=dict(family='Inter', size=11, color='#6B8FAB'), ticksuffix='%'),
                font=dict(family='Inter')
            )
            st.plotly_chart(fig2, use_container_width=True)

            # Professional table
            rows = ""
            for _, row in df.iterrows():
                rate_cls = "rpt-tag-red" if row['No-Show Rate (%)'] > 20 else "rpt-tag-amber" if row['No-Show Rate (%)'] > 10 else "rpt-tag-blue"
                rows += f"""
                <tr>
                    <td><span class="rpt-month">{row['Month']}</span></td>
                    <td><span class="rpt-count">{row['Total Appointments']}</span></td>
                    <td>{row['No-Shows']}</td>
                    <td><span class="rpt-tag {rate_cls}">{row['No-Show Rate (%)']}%</span></td>
                </tr>"""

            st.markdown(f"""
            <div class="rpt-table-wrap" style="margin-top:8px;">
                <table class="rpt-table">
                    <thead><tr>
                        <th>Month</th><th>Total Appointments</th><th>No-Shows</th><th>No-Show Rate</th>
                    </tr></thead>
                    <tbody>{rows}</tbody>
                </table>
                <div class="rpt-table-footer">{len(df)} months displayed</div>
            </div>""", unsafe_allow_html=True)

            st.markdown(f"""
            <div class="info-strip">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#1E4A76" stroke-width="2">
                    <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><circle cx="12" cy="16" r="0.5" fill="#1E4A76"/>
                </svg>
                Average monthly appointments: <strong>&nbsp;{df['Total Appointments'].mean():.0f}&nbsp;</strong>
                &nbsp;·&nbsp; Average no-show rate: <strong>&nbsp;{df['No-Show Rate (%)'].mean():.1f}%</strong>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown("""<div class="empty-state">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#B0C8E8" stroke-width="1.5">
                    <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
                </svg>
                <p style="font-size:16px;font-weight:600;color:#1A3A5C;margin-top:16px;">No monthly data available</p>
                <p style="font-size:13px;color:#6B8FAB;margin-top:6px;">Appointment records will appear here once added.</p>
            </div>""", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════
    # TREATMENT ANALYSIS
    # ══════════════════════════════════════════════════════
    elif report_type == "Treatment Analysis":
        st.markdown("""
        <div class="sec-label">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#E88C30" stroke-width="2">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
            </svg>
            Treatment Analysis
        </div>""", unsafe_allow_html=True)

        cursor.execute("""
            SELECT treatment, COUNT(*) as count FROM appointments
            WHERE treatment IS NOT NULL AND treatment != ''
            GROUP BY treatment ORDER BY count DESC LIMIT 10
        """)
        treatments = cursor.fetchall()

        if treatments:
            df = pd.DataFrame([{
                'Treatment': row[0],
                'Number of Procedures': int(row[1] or 0)
            } for row in treatments])

            st.markdown(csv_download_link(df, f"treatment_analysis_{datetime.now().strftime('%Y%m%d')}"), unsafe_allow_html=True)

            fig = px.bar(
                df, x='Treatment', y='Number of Procedures',
                color_discrete_sequence=['#1E4A76'], text='Number of Procedures'
            )
            fig.update_traces(textposition='outside', marker_line_width=0)
            fig.update_layout(
                title=dict(text='Top 10 Treatments by Volume', font=dict(family='Inter', size=14, color='#1A3A5C')),
                plot_bgcolor='white', paper_bgcolor='white',
                height=420, margin=dict(t=48, b=60, l=12, r=12),
                xaxis=dict(showgrid=False, tickfont=dict(family='Inter', size=11, color='#6B8FAB'), tickangle=-20),
                yaxis=dict(gridcolor='#F0F5FA', tickfont=dict(family='Inter', size=11, color='#6B8FAB')),
                font=dict(family='Inter')
            )
            st.plotly_chart(fig, use_container_width=True)

            # Rank table
            rows = ""
            for i, (_, row) in enumerate(df.iterrows(), 1):
                rank_cls = "rpt-tag-amber" if i == 1 else "rpt-tag-blue" if i <= 3 else ""
                rank_html = f'<span class="rpt-tag {rank_cls}">#{i}</span>' if rank_cls else f'<span style="color:#6B8FAB;font-weight:600;">#{i}</span>'
                rows += f"""
                <tr>
                    <td>{rank_html}</td>
                    <td><span class="rpt-metric-label">{esc(row['Treatment'])}</span></td>
                    <td><span class="rpt-count">{row['Number of Procedures']}</span></td>
                </tr>"""

            st.markdown(f"""
            <div class="rpt-table-wrap" style="margin-top:8px;">
                <table class="rpt-table">
                    <thead><tr><th>Rank</th><th>Treatment</th><th>Procedures</th></tr></thead>
                    <tbody>{rows}</tbody>
                </table>
                <div class="rpt-table-footer">Total procedures recorded: {df['Number of Procedures'].sum()}</div>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown("""<div class="empty-state">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#B0C8E8" stroke-width="1.5">
                    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                </svg>
                <p style="font-size:16px;font-weight:600;color:#1A3A5C;margin-top:16px;">No treatment data available</p>
                <p style="font-size:13px;color:#6B8FAB;margin-top:6px;">Treatment records will appear here once appointments are added.</p>
            </div>""", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════
    # FINANCIAL REPORT
    # ══════════════════════════════════════════════════════
    elif report_type == "Financial Report":
        st.markdown("""
        <div class="sec-label">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#E88C30" stroke-width="2">
                <line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
            </svg>
            Financial Report
        </div>""", unsafe_allow_html=True)

        cursor.execute("SELECT COALESCE(SUM(amount_paid), 0) FROM payments")
        total_revenue = float(cursor.fetchone()[0] or 0)
        cursor.execute("SELECT (SELECT COALESCE(SUM(expected_cost), 0) FROM appointments) - (SELECT COALESCE(SUM(amount_paid), 0) FROM payments)")
        total_outstanding = float(cursor.fetchone()[0] or 0)
        cursor.execute("SELECT COALESCE(payment_method, 'Other') as method, COALESCE(SUM(amount_paid), 0) as total FROM payments GROUP BY method ORDER BY total DESC")
        payment_methods = cursor.fetchall()
        cursor.execute("""
            SELECT month, revenue FROM (
                SELECT TO_CHAR(payment_date, 'YYYY-MM') as month, SUM(amount_paid) as revenue
                FROM payments GROUP BY month ORDER BY month DESC LIMIT 12
            ) recent_months ORDER BY month ASC
        """)
        monthly_rev = cursor.fetchall()

        collection_rate = (total_revenue / (total_revenue + total_outstanding) * 100) if (total_revenue + total_outstanding) > 0 else 0

        summary_data = [
            {'Metric': 'Total Revenue Collected', 'Value': f"UGX {total_revenue:,.0f}"},
            {'Metric': 'Outstanding Balance', 'Value': f"UGX {total_outstanding:,.0f}"},
            {'Metric': 'Collection Rate', 'Value': f"{collection_rate:.1f}%"}
        ]
        for method, amount in payment_methods:
            summary_data.append({'Metric': f'Revenue via {method}', 'Value': f"UGX {float(amount):,.0f}"})
        df_summary = pd.DataFrame(summary_data)

        st.markdown(csv_download_link(df_summary, f"financial_summary_{datetime.now().strftime('%Y%m%d')}"), unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Total Revenue", f"UGX {total_revenue:,.0f}")
        with c2:
            st.metric("Outstanding Balance", f"UGX {total_outstanding:,.0f}")
        with c3:
            st.metric("Collection Rate", f"{collection_rate:.1f}%")

        if payment_methods:
            st.markdown("""
            <div class="sec-label" style="margin-top:24px;">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#E88C30" stroke-width="2">
                    <rect x="1" y="4" width="22" height="16" rx="2"/><line x1="1" y1="10" x2="23" y2="10"/>
                </svg>
                Payment Method Breakdown
            </div>""", unsafe_allow_html=True)
            method_rows = ""
            for method, amount in payment_methods:
                pct = (float(amount) / total_revenue * 100) if total_revenue > 0 else 0
                method_rows += f"""
                <tr>
                    <td><span class="rpt-metric-label">{method}</span></td>
                    <td><span class="rpt-count">UGX {float(amount):,.0f}</span></td>
                    <td><span class="rpt-tag rpt-tag-blue">{pct:.1f}%</span></td>
                </tr>"""
            st.markdown(f"""
            <div class="rpt-table-wrap">
                <table class="rpt-table">
                    <thead><tr><th>Payment Method</th><th>Amount Collected</th><th>Share</th></tr></thead>
                    <tbody>{method_rows}</tbody>
                </table>
                <div class="rpt-table-footer">{len(payment_methods)} payment method{'s' if len(payment_methods) != 1 else ''} recorded</div>
            </div>""", unsafe_allow_html=True)

        if monthly_rev:
            st.markdown("""
            <div class="sec-label" style="margin-top:24px;">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#E88C30" stroke-width="2">
                    <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/>
                    <polyline points="17 6 23 6 23 12"/>
                </svg>
                Monthly Revenue Trend
            </div>""", unsafe_allow_html=True)
            df_chart = pd.DataFrame([{'Month': row[0], 'Revenue': float(row[1] or 0)} for row in monthly_rev])
            fig = px.bar(df_chart, x='Month', y='Revenue', color_discrete_sequence=['#E88C30'], text='Revenue')
            fig.update_traces(texttemplate='UGX %{text:,.0f}', textposition='outside', marker_line_width=0)
            fig.update_layout(
                plot_bgcolor='white', paper_bgcolor='white',
                height=380, margin=dict(t=32, b=40, l=12, r=12),
                xaxis=dict(showgrid=False, tickfont=dict(family='Inter', size=11, color='#6B8FAB')),
                yaxis=dict(gridcolor='#F0F5FA', tickfont=dict(family='Inter', size=11, color='#6B8FAB')),
                font=dict(family='Inter')
            )
            st.plotly_chart(fig, use_container_width=True)

    # ══════════════════════════════════════════════════════
    # NO-SHOW ANALYSIS
    # ══════════════════════════════════════════════════════
    else:
        st.markdown("""
        <div class="sec-label">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#E88C30" stroke-width="2">
                <path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
                <line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
            </svg>
            No-Show Analysis
        </div>""", unsafe_allow_html=True)

        cursor.execute("SELECT COUNT(*) as total, SUM(CASE WHEN status = 'No-show' THEN 1 ELSE 0 END) as noshows FROM appointments")
        result = cursor.fetchone()
        total = int(result[0] or 0) if result else 0
        noshows = int(result[1] or 0) if result else 0
        noshow_rate = (noshows / total * 100) if total > 0 else 0
        attended = total - noshows

        cursor.execute("""
            SELECT TO_CHAR(appointment_date, 'FMDay') as day, COUNT(*) as noshows
            FROM appointments WHERE status = 'No-show'
            GROUP BY TO_CHAR(appointment_date, 'FMDay'), EXTRACT(DOW FROM appointment_date)
            ORDER BY EXTRACT(DOW FROM appointment_date)
        """)
        noshow_days = cursor.fetchall()

        df_summary = pd.DataFrame({
            'Metric': ['Total Appointments', 'Attended', 'No-Shows', 'No-Show Rate'],
            'Value': [total, attended, noshows, f"{noshow_rate:.1f}%"]
        })
        st.markdown(csv_download_link(df_summary, f"noshow_analysis_{datetime.now().strftime('%Y%m%d')}"), unsafe_allow_html=True)

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Total Appointments", total)
        with c2:
            st.metric("Attended", attended)
        with c3:
            st.metric("No-Shows", noshows)
        with c4:
            st.metric("No-Show Rate", f"{noshow_rate:.1f}%")

        if noshow_days:
            df_days = pd.DataFrame([{'Day': row[0].strip(), 'No-Shows': int(row[1] or 0)} for row in noshow_days])

            fig = px.bar(df_days, x='Day', y='No-Shows',
                         color_discrete_sequence=['#B91C1C'], text='No-Shows')
            fig.update_traces(textposition='outside', marker_line_width=0)
            fig.update_layout(
                title=dict(text='No-Shows by Day of Week', font=dict(family='Inter', size=14, color='#1A3A5C')),
                plot_bgcolor='white', paper_bgcolor='white',
                height=380, margin=dict(t=48, b=40, l=12, r=12),
                xaxis=dict(showgrid=False, tickfont=dict(family='Inter', size=11, color='#6B8FAB')),
                yaxis=dict(gridcolor='#F0F5FA', tickfont=dict(family='Inter', size=11, color='#6B8FAB')),
                font=dict(family='Inter')
            )
            st.plotly_chart(fig, use_container_width=True)

            # Day breakdown table
            day_rows = ""
            max_val = df_days['No-Shows'].max() if not df_days.empty else 1
            for _, row in df_days.iterrows():
                is_max = row['No-Shows'] == max_val
                tag_cls = "rpt-tag-red" if is_max else "rpt-tag-blue"
                day_rows += f"""
                <tr>
                    <td><span class="rpt-metric-label">{row['Day']}</span></td>
                    <td><span class="rpt-tag {tag_cls}">{row['No-Shows']}</span></td>
                </tr>"""

            st.markdown(f"""
            <div class="rpt-table-wrap" style="margin-top:8px;">
                <table class="rpt-table">
                    <thead><tr><th>Day of Week</th><th>No-Shows</th></tr></thead>
                    <tbody>{day_rows}</tbody>
                </table>
                <div class="rpt-table-footer">Breakdown by weekday</div>
            </div>""", unsafe_allow_html=True)

            if not df_days.empty:
                max_day = df_days.loc[df_days['No-Shows'].idxmax()]
                st.markdown(f"""
                <div class="info-strip">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#1E4A76" stroke-width="2">
                        <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><circle cx="12" cy="16" r="0.5" fill="#1E4A76"/>
                    </svg>
                    Highest no-shows occur on <strong>&nbsp;{max_day['Day']}&nbsp;</strong> with
                    <strong>&nbsp;{max_day['No-Shows']}&nbsp;</strong> missed appointments.
                </div>""", unsafe_allow_html=True)
        else:
            st.markdown("""<div class="empty-state">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#B0C8E8" stroke-width="1.5">
                    <path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
                </svg>
                <p style="font-size:16px;font-weight:600;color:#1A3A5C;margin-top:16px;">No no-show data available</p>
                <p style="font-size:13px;color:#6B8FAB;margin-top:6px;">Records will appear once no-show appointments are logged.</p>
            </div>""", unsafe_allow_html=True)

    cursor.close()
    conn.close()