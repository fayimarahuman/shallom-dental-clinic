# utils/audit.py
import streamlit as st
import json
import traceback
from utils.db import get_connection


# ─────────────────────────────────────────────────────────────────────────────
# Core logger
# ─────────────────────────────────────────────────────────────────────────────

def log_action(
    action,
    table_name=None,
    record_id=None,
    old_data=None,
    new_data=None,
    status="SUCCESS",
    error_message=None,
    user_id=None,
    username=None,
):
    """
    Write one row to audit_logs.

    user_id / username fall back to st.session_state so callers don't
    need to pass them for normal CRUD actions.  Pass them explicitly for
    LOGIN / LOGIN_FAILED events that fire before session_state is set.
    """
    conn = get_connection()
    if not conn:
        return

    # ── resolve caller identity ──────────────────────────────────────────────
    if user_id is None:
        user_id = st.session_state.get("user_id")
    if username is None:
        username = st.session_state.get("username", "unknown")

    # ── serialise dicts / lists ──────────────────────────────────────────────
    if isinstance(old_data, (dict, list)):
        old_data = json.dumps(old_data, default=str)
    if isinstance(new_data, (dict, list)):
        new_data = json.dumps(new_data, default=str)

    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO audit_logs
                (user_id, username, action, table_name, record_id,
                 old_data, new_data, status, error_message)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                user_id, username, action, table_name, record_id,
                old_data, new_data, status, error_message,
            ),
        )
        conn.commit()
    except Exception as exc:
        # Never let audit errors crash the main app
        print(f"[audit] INSERT failed: {exc}\n{traceback.format_exc()}")
    finally:
        cur.close()
        conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# Convenience wrappers  (optional – keeps call-sites clean)
# ─────────────────────────────────────────────────────────────────────────────

def audit_login(username, user_id, success=True):
    log_action(
        action="LOGIN" if success else "LOGIN_FAILED",
        status="SUCCESS" if success else "FAILED",
        username=username,
        user_id=user_id,
        error_message=None if success else "Invalid credentials",
    )


def audit_logout(username=None, user_id=None):
    log_action(
        action="LOGOUT",
        username=username,
        user_id=user_id,
    )


def audit_create(table_name, record_id, new_data: dict):
    """Call AFTER the INSERT so record_id is known."""
    log_action(
        action="CREATE",
        table_name=table_name,
        record_id=record_id,
        new_data=new_data,
    )


def audit_update(table_name, record_id, old_data: dict, new_data: dict):
    """
    Call BEFORE the UPDATE to capture old_data, then pass the new values.
    Fetch old_data with a SELECT before running the UPDATE.
    """
    log_action(
        action="UPDATE",
        table_name=table_name,
        record_id=record_id,
        old_data=old_data,
        new_data=new_data,
    )


def audit_delete(table_name, record_id, old_data: dict):
    """Call BEFORE the DELETE so old_data can still be read."""
    log_action(
        action="DELETE",
        table_name=table_name,
        record_id=record_id,
        old_data=old_data,
        status="SUCCESS",
    )


def audit_predict(record_id, result_summary: dict):
    log_action(
        action="PREDICTION",
        table_name="appointments",
        record_id=record_id,
        new_data=result_summary,
    )


def audit_error(action, table_name, record_id, exc: Exception):
    """Log a failed operation – call from an except block."""
    log_action(
        action=action,
        table_name=table_name,
        record_id=record_id,
        status="FAILED",
        error_message=str(exc)[:500],
    )


# ─────────────────────────────────────────────────────────────────────────────
# Query helper (used by audit_trail.py)
# ─────────────────────────────────────────────────────────────────────────────

def get_audit_logs(days=30, action=None, user=None, table=None, limit=500):
    conn = get_connection()
    if not conn:
        return []

    query = """
        SELECT log_id, username, action, table_name, record_id,
               status, error_message,
               TO_CHAR(created_at, 'YYYY-MM-DD HH24:MI:SS') AS created_at
        FROM   audit_logs
        WHERE  created_at >= CURRENT_DATE - (%s * INTERVAL '1 day')
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

    try:
        cur = conn.cursor()
        cur.execute(query, params)
        rows = cur.fetchall()
    except Exception as exc:
        print(f"[audit] SELECT failed: {exc}")
        rows = []
    finally:
        cur.close()
        conn.close()

    return rows
# HOW TO CALL audit.py FROM EVERY PAGE
# Copy the relevant snippet into your page / handler.

from utils.audit import (
    audit_login, audit_logout,
    audit_create, audit_update, audit_delete,
    audit_predict, audit_error,
)


# ══════════════════════════════════════════════════════════════
# 1.  LOGIN  (pages/login.py or auth handler)
# ══════════════════════════════════════════════════════════════
def handle_login(username, password):
    user = db_get_user(username)          # your existing lookup

    if user and verify_password(password, user["password_hash"]):
        st.session_state["user_id"]  = user["id"]
        st.session_state["username"] = user["username"]
        st.session_state["role"]     = user["role"]

        audit_login(username=username, user_id=user["id"], success=True)
        st.rerun()
    else:
        # Pass username/user_id explicitly — session_state not set yet
        audit_login(
            username=username,
            user_id=user["id"] if user else None,
            success=False,
        )
        st.error("Invalid credentials.")


# ══════════════════════════════════════════════════════════════
# 2.  LOGOUT
# ══════════════════════════════════════════════════════════════
def handle_logout():
    audit_logout()          # reads from session_state automatically
    st.session_state.clear()
    st.rerun()


# ══════════════════════════════════════════════════════════════
# 3.  CREATE  — e.g. adding a patient / appointment
# ══════════════════════════════════════════════════════════════
def create_patient(form_data: dict):
    conn = get_connection()
    cur  = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO patients (name, dob, phone) VALUES (%s,%s,%s) RETURNING patient_id",
            (form_data["name"], form_data["dob"], form_data["phone"]),
        )
        new_id = cur.fetchone()[0]
        conn.commit()

        audit_create(table_name="patients", record_id=new_id, new_data=form_data)
        st.success("Patient added.")
    except Exception as exc:
        conn.rollback()
        audit_error("CREATE", "patients", None, exc)
        st.error(f"Failed to add patient: {exc}")
    finally:
        cur.close(); conn.close()


# ══════════════════════════════════════════════════════════════
# 4.  UPDATE — ALWAYS fetch old row first
# ══════════════════════════════════════════════════════════════
def update_appointment(appt_id: int, new_values: dict):
    conn = get_connection()
    cur  = conn.cursor()
    try:
        # ① capture current state BEFORE the change
        cur.execute(
            "SELECT patient_id, scheduled_at, status FROM appointments WHERE appt_id = %s",
            (appt_id,),
        )
        row = cur.fetchone()
        old_data = dict(zip(["patient_id", "scheduled_at", "status"], row)) if row else {}

        # ② apply the update
        cur.execute(
            "UPDATE appointments SET status=%s, scheduled_at=%s WHERE appt_id=%s",
            (new_values["status"], new_values["scheduled_at"], appt_id),
        )
        conn.commit()

        # ③ log with both snapshots
        audit_update("appointments", appt_id, old_data, new_values)
        st.success("Appointment updated.")
    except Exception as exc:
        conn.rollback()
        audit_error("UPDATE", "appointments", appt_id, exc)
        st.error(f"Update failed: {exc}")
    finally:
        cur.close(); conn.close()


# ══════════════════════════════════════════════════════════════
# 5.  DELETE — fetch the row BEFORE deleting it
# ══════════════════════════════════════════════════════════════
def delete_patient(patient_id: int):
    conn = get_connection()
    cur  = conn.cursor()
    try:
        # ① snapshot the record while it still exists
        cur.execute("SELECT * FROM patients WHERE patient_id = %s", (patient_id,))
        row = cur.fetchone()
        col_names = [d[0] for d in cur.description]
        old_data  = dict(zip(col_names, row)) if row else {}

        # ② delete
        cur.execute("DELETE FROM patients WHERE patient_id = %s", (patient_id,))
        conn.commit()

        audit_delete("patients", patient_id, old_data)
        st.success("Patient deleted.")
    except Exception as exc:
        conn.rollback()
        audit_error("DELETE", "patients", patient_id, exc)
        st.error(f"Delete failed: {exc}")
    finally:
        cur.close(); conn.close()


# ══════════════════════════════════════════════════════════════
# 6.  PREDICTION
# ══════════════════════════════════════════════════════════════
def run_noshow_prediction(appt_id: int, features: dict):
    try:
        result = your_ml_model.predict(features)   # your existing call
        audit_predict(
            record_id=appt_id,
            result_summary={"probability": result, "features": features},
        )
        return result
    except Exception as exc:
        audit_error("PREDICTION", "appointments", appt_id, exc)
        raise