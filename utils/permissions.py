"""utils.permissions

The project UI references role-based access in a few places.
The original repo had an entry in the editor, but this module does not
exist on disk in the current working tree.

This module centralizes permission checks.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional


@dataclass(frozen=True)
class PermissionResult:
    allowed: bool
    message: Optional[str] = None


def normalize_role(role: Optional[str]) -> str:
    return (role or "").strip().lower()


def has_any_role(user_role: Optional[str], allowed_roles: Iterable[str]) -> bool:
    r = normalize_role(user_role)
    allowed = {normalize_role(x) for x in allowed_roles}
    return r in allowed


def can_access(user_role: Optional[str], allowed_roles: Iterable[str]) -> PermissionResult:
    if has_any_role(user_role, allowed_roles):
        return PermissionResult(True, None)
    allowed_list = ", ".join(sorted({x for x in allowed_roles}))
    return PermissionResult(False, f"Access denied. Required role(s): {allowed_list}.")


def require_role(user_role: Optional[str], allowed_roles: Iterable[str]) -> PermissionResult:
    """Alias for can_access; kept for backward compatibility if used elsewhere."""
    return can_access(user_role, allowed_roles)


# ──────────────────────────────────────────────────────────────────────────
# Page-level access control
#
# This is the single source of truth for "which role can see which page".
# It is used by app.py to (a) hide nav items a role can't use, and
# (b) block direct access to a page even if someone manipulates session
# state to land on it.
#
# Adjust this mapping to match the roles defined in your project brief.
# Currently the database only ever creates accounts with role='admin'
# (see utils/auth.py init_auth_table) -- there is no UI yet to create a
# 'dentist' or 'receptionist' account, so for now you'd need to set the
# role manually in the `users` table to see the restrictions below in
# action.
# ──────────────────────────────────────────────────────────────────────────

# Pages every authenticated user can reach, regardless of role.
COMMON_PAGES = ["Dashboard", "Profile", "About"]

ROLE_PAGE_ACCESS = {
    "admin": [
        "Dashboard", "Patients", "Patient History", "Appointments",
        "Payments", "Inventory", "No-Show Predictor", "Reports",
        "Audit Trail", "User Management", "Profile", "About",
    ],
    "dentist": COMMON_PAGES + [
        "Patients", "Patient History", "Appointments", "No-Show Predictor",
    ],
    "receptionist": COMMON_PAGES + [
        "Patients", "Patient History", "Appointments", "Payments", "Inventory",
    ],
}


def get_allowed_pages(user_role: Optional[str]) -> set[str]:
    """Return the set of page names a role is allowed to view.

    Unknown/missing roles fall back to COMMON_PAGES only (safest default --
    deny by default rather than accidentally granting full access to a
    role that was mistyped or never defined above).
    """
    role = normalize_role(user_role)
    for known_role, pages in ROLE_PAGE_ACCESS.items():
        if normalize_role(known_role) == role:
            return set(pages)
    return set(COMMON_PAGES)


def can_view_page(user_role: Optional[str], page_name: str) -> bool:
    return page_name in get_allowed_pages(user_role)