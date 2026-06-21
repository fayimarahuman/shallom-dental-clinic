"""
Small helper to prevent stored/reflected XSS across the app.

Every page builds its tables and cards by interpolating values straight into
HTML strings via st.markdown(..., unsafe_allow_html=True). Any value that
came from a user-editable field (patient name, phone, email, location,
dentist, treatment, item name, search boxes, etc.) must be passed through
esc() before being placed inside an HTML string. Values that are guaranteed
to come from a fixed set (e.g. a status from a selectbox, a number) don't
strictly need it, but escaping them too is harmless.

Usage:
    from utils.sanitize import esc
    row_html = f'<td>{esc(patient_name)}</td>'
"""
import html


def esc(value):
    """HTML-escape a value for safe interpolation into raw HTML strings.
    None becomes an empty string; everything else is converted to str first."""
    if value is None:
        return ""
    return html.escape(str(value), quote=True)