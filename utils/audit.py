# utils/audit.py
import streamlit as st
import json
from datetime import datetime
from utils.db import get_connection


def log_action(action, table_name=None, record_id=None, old_data=None, new_data=None,
               status="SUCCESS", error_message=None, user_id=None, username=None):
    """Log user actions to audit trail.

    user_id/username are normally read from st.session_state (the logged-in
    user performing the action). Pass them explicitly for events that happen
    before session state is set -- e.g. a login attempt, where we're logging
    the very user_id/username that's about to (or failed to) become "current".
    """

    conn = get_connection()
    if not conn:
        return

    cursor = conn.cursor()

    # Get current user info (fall back to session state unless overridden)
    if user_id is None:
        user_id = st.session_state.get('user_id')
    if username is None:
        username = st.session_state.get('username', 'unknown')
    
    # Convert dict to JSON string
    if isinstance(old_data, (dict, list)):
        old_data = json.dumps(old_data)
    if isinstance(new_data, (dict, list)):
        new_data = json.dumps(new_data)
    
    try:
        cursor.execute("""
            INSERT INTO audit_logs (user_id, username, action, table_name, record_id, old_data, new_data, status, error_message)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (user_id, username, action, table_name, record_id, old_data, new_data, status, error_message))
        conn.commit()
    except Exception as e:
        print(f"Audit log error: {e}")
    finally:
        cursor.close()
        conn.close()


def get_audit_logs(days=30, action=None, user=None, table=None, limit=200):
    """Retrieve audit logs with filters"""
    conn = get_connection()
    if not conn:
        return []
    
    cursor = conn.cursor()
    
    query = """
        SELECT log_id, username, action, table_name, record_id, status, error_message,
               TO_CHAR(created_at, 'YYYY-MM-DD HH24:MI:SS') as created_at
        FROM audit_logs
        WHERE created_at >= CURRENT_DATE - (%s * INTERVAL '1 day')
    """
    params = [days]
    
    if action:
        query += " AND action = %s"
        params.append(action)
    if user:
        query += " AND username = %s"
        params.append(user)
    if table:
        query += " AND table_name = %s"
        params.append(table)
    
    query += " ORDER BY created_at DESC LIMIT %s"
    params.append(limit)
    
    cursor.execute(query, params)
    logs = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return logs