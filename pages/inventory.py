# pages/inventory.py
import streamlit as st
import pandas as pd
import re
from utils.db import get_connection
from utils.sanitize import esc
from utils.audit import log_action


def auto_reduce_inventory(treatment_name):
    """
    Decrements inventory stock for whatever items a treatment consumes,
    based on the treatment_item_mapping table.

    This is a module-level function (not nested inside show_inventory, and
    not stashed in st.session_state) so it can be imported and called from
    any page at any time, regardless of whether the Inventory page has been
    visited in the current session:

        from pages.inventory import auto_reduce_inventory
    """
    results = {"success": True, "warnings": [], "errors": [], "reductions": []}
    conn = get_connection()
    if not conn:
        results["success"] = False
        results["errors"].append("Database connection failed")
        return results

    cursor = conn.cursor()
    try:
        # Case/whitespace-insensitive match: a free-text "treatment" typed on the
        # Appointments page only needs to match a recipe approximately, not as an
        # exact byte-for-byte string -- otherwise "Tooth Extraction" vs
        # "tooth extraction " (trailing space) would silently match nothing.
        cursor.execute(
            "SELECT item_name, quantity_used FROM treatment_item_mapping "
            "WHERE LOWER(TRIM(treatment_name)) = LOWER(TRIM(%s))",
            (treatment_name,),
        )
        mappings = cursor.fetchall()
        if not mappings:
            return results  # no mapping for this treatment -> nothing to reduce

        missing = []
        for item_name, _ in mappings:
            cursor.execute("SELECT item_id FROM inventory WHERE item_name=%s", (item_name,))
            if not cursor.fetchone():
                missing.append(item_name)

        if missing:
            results["success"] = False
            results["errors"] = [f"Item '{m}' not found in inventory." for m in missing]
            return results

        for item_name, quantity_used in mappings:
            cursor.execute("SELECT item_id, quantity FROM inventory WHERE item_name=%s", (item_name,))
            row = cursor.fetchone()
            if row:
                item_id, current_qty = row
                new_qty = current_qty - quantity_used
                if new_qty < 0:
                    results["warnings"].append(f"'{item_name}' stock went negative")
                new_status = "OUT OF STOCK" if new_qty <= 0 else "LOW" if new_qty < 10 else "OK"
                cursor.execute(
                    "UPDATE inventory SET quantity=%s, status=%s WHERE item_id=%s",
                    (max(new_qty, 0), new_status, item_id),
                )
                log_action("UPDATE", table_name="inventory", record_id=item_id,
                           old_data={"quantity": current_qty},
                           new_data={"quantity": max(new_qty, 0), "reason": f"auto-reduced by treatment '{treatment_name}'"})
                results["reductions"].append(
                    {"item": item_name, "used": quantity_used, "remaining": max(new_qty, 0)}
                )

        conn.commit()
    except Exception as e:
        conn.rollback()
        results["success"] = False
        results["errors"].append(str(e))
    finally:
        cursor.close()
        conn.close()

    return results


def show_inventory():
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

        /* ── ALERT / INFO STRIPS ── */
        .alert-strip {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 14px 20px;
            border-radius: 14px;
            margin-bottom: 16px;
            font-size: 13px;
            font-weight: 600;
        }
        .alert-strip.low { background: #FDEBD3; border: 1.5px solid #F5BC6A; color: #B5670F; }
        .alert-strip.out { background: #FEF2F2; border: 1.5px solid #FECACA; color: #B91C1C; }

        .info-strip {
            background: #EEF4FB;
            border: 1.5px solid #D6E6F5;
            border-radius: 14px;
            padding: 14px 18px;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 13px;
            font-weight: 600;
            color: #1E4A76;
        }

        /* ── INPUT FIELDS ── */
        .stTextInput label, .stSelectbox label, .stNumberInput label {
            font-size: 12px !important;
            font-weight: 600 !important;
            color: #1A3A5C !important;
            letter-spacing: 0.1px !important;
        }
        .stTextInput input, .stNumberInput > div > div > input {
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

        /* ── ACTION BAR spacing & equal-height button rows ── */
        .action-bar-spacer { height: 14px; }
        div[data-testid="column"] { display: flex !important; flex-direction: column !important; justify-content: flex-end !important; }
        div[data-testid="stHorizontalBlock"] { gap: 12px !important; align-items: stretch !important; }

        /* ── INVENTORY TABLE ── */
        .inv-table-wrap {
            background: #fff;
            border-radius: 18px;
            border: 1.5px solid #E2E8F0;
            overflow: hidden;
            box-shadow: 0 4px 20px rgba(30,74,118,0.07);
            margin-top: 4px;
        }
        .inv-table { width: 100%; border-collapse: collapse; }
        .inv-table thead tr { background: linear-gradient(135deg, #1E4A76 0%, #2D6A9F 100%); }
        .inv-table thead th {
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
        .inv-table tbody tr {
            border-bottom: 1px solid #F0F5FA;
            transition: background 0.12s ease;
        }
        .inv-table tbody tr:last-child { border-bottom: none; }
        .inv-table tbody tr:hover { background: #F7FAFD; }
        .inv-table tbody td {
            padding: 13px 18px;
            vertical-align: middle;
            border: none;
            font-size: 13.5px;
            color: #2D4A6B;
        }
        .inv-id {
            display: inline-flex; align-items: center;
            background: #EEF4FB; color: #2D6A9F;
            font-size: 11px; font-weight: 700;
            padding: 4px 10px; border-radius: 8px;
        }
        .inv-name { font-weight: 600; color: #1A3A5C; }
        .inv-qty {
            display: inline-flex; align-items: center; justify-content: center;
            background: #F0F5FA; color: #1A3A5C;
            font-size: 13px; font-weight: 700;
            min-width: 40px; height: 30px; padding: 0 10px; border-radius: 8px;
        }
        .badge-status {
            display: inline-block; font-size: 11px; font-weight: 700;
            padding: 4px 12px; border-radius: 20px; letter-spacing: 0.2px;
        }
        .badge-ok  { background: #DBEAFE; color: #1E4A76; }
        .badge-low { background: #FDEBD3; color: #B5670F; }
        .badge-out { background: #FEE2E2; color: #B91C1C; }
        .inv-table-footer {
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
    if '_inv_flash' not in st.session_state:
        st.session_state._inv_flash = None

    conn_count = get_connection()
    total_items = 0
    if conn_count:
        _c = conn_count.cursor()
        _c.execute("SELECT COUNT(*) FROM inventory")
        total_items = _c.fetchone()[0]
        _c.close()
        conn_count.close()

    st.markdown(f"""
    <div class="page-header">
        <div class="ph-left">
            <div class="ph-icon">
                <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="1.8">
                    <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
                </svg>
            </div>
            <div>
                <p class="ph-title">Inventory Management</p>
                <p class="ph-subtitle">Track supplies, manage stock levels</p>
            </div>
        </div>
        <div class="ph-badge">{total_items:,} items tracked</div>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state._inv_flash:
        st.success(st.session_state._inv_flash)
        st.session_state._inv_flash = None

    tab1, tab2, tab3, tab4 = st.tabs(["Add Item", "View Stock", "Edit / Delete", "Treatment Recipes"])

    # ========== TAB 1 - ADD ITEM ==========
    with tab1:
        with st.form("add_item_form"):
            col1, col2 = st.columns(2)
            with col1:
                item_name = st.text_input("Item Name *", placeholder="e.g. Latex Gloves, Anesthetic, Syringes")
                quantity = st.number_input("Quantity *", min_value=0, value=0, step=1)
            with col2:
                if quantity <= 0:
                    default_status = "OUT OF STOCK"
                elif quantity < 10:
                    default_status = "LOW"
                else:
                    default_status = "OK"
                status = st.selectbox("Status", ["OK", "LOW", "OUT OF STOCK"], index=["OK", "LOW", "OUT OF STOCK"].index(default_status))

            if st.form_submit_button("Add to Inventory", use_container_width=True):
                if not item_name.strip():
                    st.error("Item name is required.")
                else:
                    conn = get_connection()
                    if conn:
                        cursor = conn.cursor()
                        try:
                            cursor.execute("SELECT COUNT(*) FROM inventory WHERE item_name ILIKE %s", (item_name.strip(),))
                            if cursor.fetchone()[0] > 0:
                                st.warning(f"'{item_name.strip()}' already exists. Use Edit to update it.")
                            else:
                                cursor.execute("INSERT INTO inventory (item_name, quantity, status) VALUES (%s, %s, %s) RETURNING item_id", (item_name.strip(), quantity, status))
                                new_item_id = cursor.fetchone()[0]
                                conn.commit()
                                log_action("CREATE", table_name="inventory", record_id=new_item_id,
                                           new_data={"item_name": item_name.strip(), "quantity": quantity, "status": status})
                                st.session_state._inv_flash = f"'{item_name.strip()}' added to inventory."
                                st.rerun()
                        except Exception as e:
                            st.error(f"Error adding item: {e}")
                        finally:
                            cursor.close()
                            conn.close()

    # ========== TAB 2 - VIEW STOCK ==========
    with tab2:
        st.markdown('<div class="sec-label"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#E88C30" stroke-width="2"><circle cx="10" cy="10" r="7"/><line x1="21" y1="21" x2="15" y2="15"/></svg> Search Inventory</div>', unsafe_allow_html=True)
        search_inv = st.text_input("Search", placeholder="Search by item name...", label_visibility="collapsed", key="inv_search")

        conn = get_connection()
        if not conn:
            st.error("Database connection failed.")
            return
        cursor = conn.cursor()
        if search_inv:
            cursor.execute("SELECT item_id, item_name, quantity, status FROM inventory WHERE item_name ILIKE %s ORDER BY item_name", (f'%{search_inv}%',))
        else:
            cursor.execute("SELECT item_id, item_name, quantity, status FROM inventory ORDER BY item_name")
        items = cursor.fetchall()
        cursor.close()
        conn.close()

        if items:
            low_count = sum(1 for i in items if i[3] == 'LOW')
            out_count = sum(1 for i in items if i[3] == 'OUT OF STOCK')

            if out_count > 0:
                st.markdown(f'<div class="alert-strip out"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><circle cx="12" cy="16" r="0.5" fill="currentColor"/></svg> {out_count} item(s) are OUT OF STOCK — reorder immediately</div>', unsafe_allow_html=True)
            if low_count > 0:
                st.markdown(f'<div class="alert-strip low"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><circle cx="12" cy="16" r="0.5" fill="currentColor"/></svg> {low_count} item(s) are running LOW — consider restocking</div>', unsafe_allow_html=True)

            status_badge = {"OK": "badge-ok", "LOW": "badge-low", "OUT OF STOCK": "badge-out"}
            rows = ""
            for it in items:
                i_id, i_name, i_qty, i_status = it
                i_name = esc(i_name)
                badge_cls = status_badge.get(i_status, "badge-ok")
                rows += f"""
                <tr>
                    <td><span class="inv-id">#{i_id}</span></td>
                    <td><span class="inv-name">{i_name}</span></td>
                    <td><span class="inv-qty">{i_qty}</span></td>
                    <td><span class="badge-status {badge_cls}">{i_status}</span></td>
                </tr>"""

            st.markdown(f"""
            <div class="inv-table-wrap">
                <table class="inv-table">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Item Name</th>
                            <th>Quantity</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>{rows}</tbody>
                </table>
                <div class="inv-table-footer">{len(items)} item{'s' if len(items) != 1 else ''} found</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="empty-state">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#B0C8E8" stroke-width="1.5">
                    <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
                </svg>
                <p style="font-size:16px;font-weight:600;color:#1A3A5C;margin-top:16px;">No items found</p>
                <p style="font-size:13px;color:#6B8FAB;">{"No results for &quot;" + esc(search_inv) + "&quot;" if search_inv else "Inventory is empty. Add items using the Add Item tab."}</p>
            </div>
            """, unsafe_allow_html=True)

    # ========== TAB 3 - EDIT/DELETE ==========
    with tab3:
        conn = get_connection()
        if not conn:
            st.error("Database connection failed.")
            return
        cursor = conn.cursor()
        cursor.execute("SELECT item_id, item_name, quantity, status FROM inventory ORDER BY item_name")
        all_items = cursor.fetchall()
        cursor.close()
        conn.close()

        if not all_items:
            st.markdown('<div class="empty-state"><p style="font-size:16px;font-weight:600;color:#1A3A5C;">No items to edit. Add items first.</p></div>', unsafe_allow_html=True)
            return

        st.markdown('<div class="sec-label"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#E88C30" stroke-width="2"><circle cx="10" cy="10" r="7"/><line x1="21" y1="21" x2="15" y2="15"/></svg> Find Item</div>', unsafe_allow_html=True)
        ie1, ie2 = st.columns([2, 3])
        with ie1:
            item_search = st.text_input("Search", placeholder="Type item name...", label_visibility="collapsed", key="item_ed_search")
        with ie2:
            opts_full = [f"{i[1]} (ID {i[0]}) · Qty: {i[2]} · {i[3]}" for i in all_items]
            opts_filt = [o for o, i in zip(opts_full, all_items) if item_search.lower() in i[1].lower()] if item_search else opts_full
            selected_item = st.selectbox("Select", opts_filt, label_visibility="collapsed", key="item_ed_select")

        match = re.search(r'ID (\d+)', selected_item)
        if not match:
            st.error("Invalid selection.")
            return
        item_id = int(match.group(1))
        item = next((i for i in all_items if i[0] == item_id), None)
        if not item:
            st.error("Item not found.")
            return

        # Inline SVG status icons (Tabler-style). No emoji.
        status_icon_svg = (
            "<svg width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='#1E4A76' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'>"
            "<path d='M20 6L9 17l-5-5'/>"
            "</svg>" if item[3] == 'OK' else
            "<svg width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='#B5670F' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'>"
            "<path d='M12 9v4'/>"
            "<path d='M12 17h.01'/>"
            "<path d='M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z'/>"
            "</svg>" if item[3] == 'LOW' else
            "<svg width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='#B91C1C' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'>"
            "<circle cx='12' cy='12' r='10'/>"
            "<path d='M15 9l-6 6'/>"
            "<path d='M9 9l6 6'/>"
            "</svg>"
        )
        st.markdown(
            f"<div class='info-strip'>{status_icon_svg} Current: <strong>{esc(item[1])}</strong> · Qty: <strong>{item[2]}</strong> · Status: <strong>{item[3]}</strong></div>",
            unsafe_allow_html=True,
        )

        with st.form("edit_item_form"):
            col1, col2 = st.columns(2)
            with col1:
                new_name = st.text_input("Item Name", value=item[1])
                new_qty = st.number_input("Quantity", value=item[2], min_value=0, step=1)
            with col2:
                if new_qty <= 0:
                    suggested = "OUT OF STOCK"
                elif new_qty < 10:
                    suggested = "LOW"
                else:
                    suggested = "OK"
                st_opts = ["OK", "LOW", "OUT OF STOCK"]
                new_status = st.selectbox("Status", st_opts, index=st_opts.index(suggested))

            st.markdown('<div class="action-bar-spacer"></div>', unsafe_allow_html=True)
            if st.form_submit_button("Save Changes", use_container_width=True):
                if not new_name.strip():
                    st.error("Item name cannot be empty.")
                else:
                    conn = get_connection()
                    if conn:
                        cursor = conn.cursor()
                        cursor.execute("UPDATE inventory SET item_name=%s, quantity=%s, status=%s WHERE item_id=%s", (new_name.strip(), new_qty, new_status, item_id))
                        conn.commit()
                        log_action("UPDATE", table_name="inventory", record_id=item_id,
                                   new_data={"item_name": new_name.strip(), "quantity": new_qty, "status": new_status})
                        cursor.close()
                        conn.close()
                        st.session_state._inv_flash = "Item updated successfully."
                        st.rerun()

        # ── Danger zone: delete this item ──
        st.markdown('<div class="sec-label" style="margin-top:24px;"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#D32F2F" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><circle cx="12" cy="16" r="0.5" fill="#D32F2F"/></svg> Danger Zone</div>', unsafe_allow_html=True)

        if not st.session_state.get('confirm_del_item'):
            st.markdown('<div class="danger-btn-wrap">', unsafe_allow_html=True)
            if st.button("🗑  Delete This Item", use_container_width=True, key="del_item_btn"):
                st.session_state['confirm_del_item'] = item_id
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        if st.session_state.get('confirm_del_item') == item_id:
            st.markdown(f"""
            <div class="delete-warn">
                <div class="delete-warn-title">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#B91C1C" stroke-width="1.8">
                        <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><circle cx="12" cy="16" r="0.5" fill="#B91C1C"/>
                    </svg>
                    Confirm deletion — this cannot be undone
                </div>
                <div class="delete-field">Item: <span>{esc(item[1])}</span></div>
                <div class="delete-field">Quantity: <span>{item[2]}</span></div>
                <div class="delete-field">Status: <span>{item[3]}</span></div>
            </div>
            """, unsafe_allow_html=True)
            dc1, dc2 = st.columns(2, gap="small")
            with dc1:
                st.markdown('<div class="confirm-btn-wrap">', unsafe_allow_html=True)
                if st.button("✓  Yes, Delete", use_container_width=True, key="confirm_del_item_yes"):
                    conn = get_connection()
                    if conn:
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM inventory WHERE item_id=%s", (item_id,))
                        conn.commit()
                        log_action("DELETE", table_name="inventory", record_id=item_id,
                                   old_data={"item_name": item[1], "quantity": item[2]})
                        cursor.close()
                        conn.close()
                        st.session_state.pop('confirm_del_item', None)
                        st.session_state._inv_flash = "Item deleted successfully."
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            with dc2:
                st.markdown('<div class="cancel-btn-wrap">', unsafe_allow_html=True)
                if st.button("✕  Cancel", use_container_width=True, key="cancel_del_item"):
                    st.session_state.pop('confirm_del_item', None)
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

    # ========== TAB 4 - TREATMENT RECIPES ==========
    with tab4:
        st.markdown(
            '<div class="info-strip">Define which inventory items a treatment consumes. '
            'When an appointment for a mapped treatment is marked Completed, stock is reduced automatically.</div>',
            unsafe_allow_html=True,
        )

        conn = get_connection()
        if not conn:
            st.error("Database connection failed.")
            return
        cursor = conn.cursor()
        cursor.execute("SELECT item_id, item_name FROM inventory ORDER BY item_name")
        inv_items = cursor.fetchall()
        cursor.close()
        conn.close()

        if not inv_items:
            st.warning("Add at least one inventory item first (Add Item tab) before creating a recipe.")
            return

        item_names = [i[1] for i in inv_items]

        st.markdown('<div class="sec-label" style="margin-top:8px;">Add Mapping</div>', unsafe_allow_html=True)
        with st.form("add_recipe_form"):
            rc1, rc2, rc3 = st.columns([2, 2, 1])
            with rc1:
                treatment_name_input = st.text_input(
                    "Treatment Name *",
                    placeholder="e.g. Tooth Extraction (must match the treatment field used in Appointments)",
                )
            with rc2:
                mapped_item = st.selectbox("Item *", item_names)
            with rc3:
                qty_used = st.number_input("Qty Used *", min_value=1, value=1, step=1)

            if st.form_submit_button("Save Mapping", use_container_width=True):
                tname = treatment_name_input.strip()
                if not tname:
                    st.error("Treatment name is required.")
                else:
                    conn = get_connection()
                    if conn:
                        cursor = conn.cursor()
                        try:
                            cursor.execute(
                                "SELECT 1 FROM treatment_item_mapping "
                                "WHERE LOWER(TRIM(treatment_name))=LOWER(TRIM(%s)) AND item_name=%s",
                                (tname, mapped_item),
                            )
                            if cursor.fetchone():
                                cursor.execute(
                                    "UPDATE treatment_item_mapping SET quantity_used=%s "
                                    "WHERE LOWER(TRIM(treatment_name))=LOWER(TRIM(%s)) AND item_name=%s",
                                    (qty_used, tname, mapped_item),
                                )
                                conn.commit()
                                log_action("UPDATE", table_name="treatment_item_mapping",
                                           new_data={"treatment": tname, "item": mapped_item, "qty": qty_used})
                                st.session_state._inv_flash = f"Updated: '{tname}' now uses {qty_used} x {mapped_item}."
                            else:
                                cursor.execute(
                                    "INSERT INTO treatment_item_mapping (treatment_name, item_name, quantity_used) VALUES (%s, %s, %s)",
                                    (tname, mapped_item, qty_used),
                                )
                                conn.commit()
                                log_action("CREATE", table_name="treatment_item_mapping",
                                           new_data={"treatment": tname, "item": mapped_item, "qty": qty_used})
                                st.session_state._inv_flash = f"'{tname}' now consumes {qty_used} x {mapped_item} when completed."
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error saving mapping: {e}")
                        finally:
                            cursor.close()
                            conn.close()

        st.markdown('<div class="sec-label" style="margin-top:24px;">Existing Recipes</div>', unsafe_allow_html=True)
        conn = get_connection()
        if not conn:
            st.error("Database connection failed.")
            return
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT treatment_name, item_name, quantity_used FROM treatment_item_mapping ORDER BY treatment_name, item_name"
            )
            recipes = cursor.fetchall()
        except Exception as e:
            recipes = []
            st.error(f"Could not load recipes: {e}")
        finally:
            cursor.close()
            conn.close()

        if recipes:
            rows = ""
            for t_name, i_name, q_used in recipes:
                rows += f"""
                <tr>
                    <td><span class="inv-name">{esc(t_name)}</span></td>
                    <td>{esc(i_name)}</td>
                    <td><span class="inv-qty">{q_used}</span></td>
                </tr>"""
            st.markdown(f"""
            <div class="inv-table-wrap">
                <table class="inv-table">
                    <thead>
                        <tr>
                            <th>Treatment</th>
                            <th>Item Consumed</th>
                            <th>Qty Used</th>
                        </tr>
                    </thead>
                    <tbody>{rows}</tbody>
                </table>
                <div class="inv-table-footer">{len(recipes)} mapping{'s' if len(recipes) != 1 else ''}</div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown('<div class="sec-label" style="margin-top:24px;">Edit a Mapping</div>', unsafe_allow_html=True)
            edit_opts = [f"{t} → {i} (currently {q})" for t, i, q in recipes]
            edit_choice = st.selectbox("Select mapping to edit", edit_opts, label_visibility="collapsed", key="edit_recipe_select")
            edit_idx = edit_opts.index(edit_choice)
            edit_t, edit_i, edit_q = recipes[edit_idx]

            with st.form("edit_recipe_form"):
                erc1, erc2 = st.columns([2, 1])
                with erc1:
                    st.text_input("Treatment", value=edit_t, disabled=True, key="edit_recipe_treatment_display")
                    st.caption(f"Item: {edit_i}")
                with erc2:
                    new_qty_used = st.number_input("Qty Used", min_value=1, value=edit_q, step=1, key="edit_recipe_qty")

                if st.form_submit_button("Save Changes", use_container_width=True):
                    conn = get_connection()
                    if conn:
                        cursor = conn.cursor()
                        cursor.execute(
                            "UPDATE treatment_item_mapping SET quantity_used=%s WHERE treatment_name=%s AND item_name=%s",
                            (new_qty_used, edit_t, edit_i),
                        )
                        conn.commit()
                        log_action("UPDATE", table_name="treatment_item_mapping",
                                   old_data={"qty": edit_q}, new_data={"treatment": edit_t, "item": edit_i, "qty": new_qty_used})
                        cursor.close()
                        conn.close()
                        st.session_state._inv_flash = f"Updated: '{edit_t}' now uses {new_qty_used} x {edit_i}."
                        st.rerun()

            st.markdown('<div class="sec-label" style="margin-top:24px;">Delete a Mapping</div>', unsafe_allow_html=True)
            del_opts = [f"{t} → {i} ({q})" for t, i, q in recipes]
            del_choice = st.selectbox("Select mapping to delete", del_opts, label_visibility="collapsed", key="del_recipe_select")
            del_idx = del_opts.index(del_choice)
            del_t, del_i, _ = recipes[del_idx]

            st.markdown('<div class="danger-btn-wrap">', unsafe_allow_html=True)
            if st.button("🗑  Delete This Mapping", use_container_width=True, key="del_recipe_btn"):
                conn = get_connection()
                if conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "DELETE FROM treatment_item_mapping WHERE treatment_name=%s AND item_name=%s",
                        (del_t, del_i),
                    )
                    conn.commit()
                    log_action("DELETE", table_name="treatment_item_mapping",
                               old_data={"treatment": del_t, "item": del_i})
                    cursor.close()
                    conn.close()
                    st.session_state._inv_flash = f"Mapping deleted: {del_t} → {del_i}."
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown(
                '<div class="empty-state"><p style="font-size:16px;font-weight:600;color:#1A3A5C;">No recipes defined yet</p>'
                '<p style="font-size:13px;color:#6B8FAB;">Add a mapping above to enable automatic stock reduction for that treatment.</p></div>',
                unsafe_allow_html=True,
            )
