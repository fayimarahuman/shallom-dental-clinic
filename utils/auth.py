import bcrypt
import hashlib
from utils.db import get_connection
from utils.audit import log_action

MAX_LOGIN_ATTEMPTS = 5


def _is_bcrypt_hash(value):
    return isinstance(value, str) and value.startswith(("$2b$", "$2a$", "$2y$"))


def verify_password(password, stored_hash):
    if _is_bcrypt_hash(stored_hash):
        return bcrypt.checkpw(password.encode(), stored_hash.encode())
    
    # For backward compatibility with SHA256
    return hashlib.sha256(password.encode()).hexdigest() == stored_hash


def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def init_auth_table():
    conn = get_connection()
    if not conn:
        print("Warning: Could not connect to database for auth table initialization")
        return

    cursor = conn.cursor()

    try:
        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                role VARCHAR(20) DEFAULT 'admin',
                email VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                login_attempts INTEGER DEFAULT 0,
                is_locked BOOLEAN DEFAULT FALSE
            )
        """)

        # Add columns if they don't exist (for existing tables)
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login TIMESTAMP")
        except:
            pass
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS login_attempts INTEGER DEFAULT 0")
        except:
            pass
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_locked BOOLEAN DEFAULT FALSE")
        except:
            pass

        # Create default admin account
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = %s", ('admin',))
        count_result = cursor.fetchone()
        
        if isinstance(count_result, dict):
            user_count = list(count_result.values())[0]
        else:
            user_count = count_result[0]

        if user_count == 0:
            # Password is 'admin123' hashed with bcrypt
            default_password = hash_password("admin123")
            
            cursor.execute("""
                INSERT INTO users (username, password, role, email)
                VALUES (%s, %s, %s, %s)
            """, ('admin', default_password, 'admin', 'admin@shallomdental.com'))
            
            print("Admin user created")
            print("Username: admin")
            print("Password: admin123")

        conn.commit()

    except Exception as e:
        conn.rollback()
        print(f"Auth table initialization error: {e}")

    finally:
        cursor.close()
        conn.close()


def login_user(username, password):
    conn = get_connection()
    
    if not conn:
        print("Database connection failed in login_user")
        return {
            "status": "error",
            "message": "Database connection failed. Please check your database configuration."
        }

    cursor = conn.cursor()

    try:
        # Check if table exists first
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'users'
            )
        """)
        table_exists = cursor.fetchone()[0]
        
        if not table_exists:
            cursor.close()
            conn.close()
            return {
                "status": "error",
                "message": "Users table does not exist. Please restart the application to initialize database."
            }
        
        # Use a simpler query without RealDictCursor for compatibility
        cursor.execute("""
            SELECT 
                user_id,
                username,
                role,
                password,
                COALESCE(login_attempts, 0) as login_attempts,
                COALESCE(is_locked, FALSE) as is_locked
            FROM users
            WHERE username = %s
        """, (username,))

        row = cursor.fetchone()

        if not row:
            log_action("LOGIN_FAILED", table_name="users", status="FAILED",
                       error_message="Unknown username", username=username)
            return {
                "status": "invalid",
                "attempts": 0,
                "remaining": MAX_LOGIN_ATTEMPTS,
                "message": "Invalid username or password."
            }

        # Extract values from tuple
        user_id = row[0]
        db_username = row[1]
        role = row[2]
        stored_hash = row[3]
        attempts = row[4] if row[4] is not None else 0
        is_locked = row[5] if row[5] is not None else False

        if is_locked:
            log_action("LOGIN_FAILED", table_name="users", record_id=user_id, status="FAILED",
                       error_message="Account is locked", user_id=user_id, username=db_username)
            return {
                "status": "locked",
                "message": "Account locked after too many failed login attempts.",
                "attempts": attempts
            }

        password_valid = verify_password(password, stored_hash)

        if password_valid:
            # Upgrade legacy SHA256 passwords to bcrypt
            if not _is_bcrypt_hash(stored_hash):
                try:
                    cursor.execute(
                        "UPDATE users SET password = %s WHERE user_id = %s",
                        (hash_password(password), user_id)
                    )
                except Exception:
                    pass

            cursor.execute(
                """
                UPDATE users 
                SET last_login = CURRENT_TIMESTAMP,
                    login_attempts = 0,
                    is_locked = FALSE
                WHERE user_id = %s
                """,
                (user_id,)
            )

            conn.commit()

            log_action("LOGIN", table_name="users", record_id=user_id, status="SUCCESS",
                       user_id=user_id, username=db_username)

            return {
                "status": "success",
                "user": (user_id, db_username, role)
            }

        # Increment failed attempts
        attempts += 1
        locked = attempts >= MAX_LOGIN_ATTEMPTS

        cursor.execute(
            """
            UPDATE users 
            SET login_attempts = %s,
                is_locked = %s
            WHERE user_id = %s
            """,
            (attempts, locked, user_id)
        )

        conn.commit()

        if locked:
            log_action("LOGIN_FAILED", table_name="users", record_id=user_id, status="FAILED",
                       error_message="Account locked after repeated failed attempts",
                       user_id=user_id, username=db_username)
            return {
                "status": "locked",
                "attempts": attempts,
                "message": "Account has been locked after too many failed login attempts."
            }

        log_action("LOGIN_FAILED", table_name="users", record_id=user_id, status="FAILED",
                   error_message="Incorrect password", user_id=user_id, username=db_username)

        return {
            "status": "invalid",
            "attempts": attempts,
            "remaining": MAX_LOGIN_ATTEMPTS - attempts,
            "message": "Invalid username or password."
        }

    except Exception as e:
        print(f"Login error details: {e}")
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "message": f"Login error: {str(e)}"
        }

    finally:
        cursor.close()
        conn.close()


def get_user_by_id(user_id):
    conn = get_connection()
    if not conn:
        return None
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, username, role, email FROM users WHERE user_id = %s", (user_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    if row:
        return row
    return None


def update_user_profile(user_id, username, email, password=None):
    if not username:
        return False, "Username is required."

    conn = get_connection()
    if not conn:
        return False, "Database unavailable. Please try again later."

    cursor = conn.cursor()
    
    try:
        # Check if username is taken
        cursor.execute("SELECT user_id FROM users WHERE username = %s AND user_id != %s", (username, user_id))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return False, "That username is already taken."

        # Check if email is taken
        if email:
            cursor.execute("SELECT user_id FROM users WHERE email = %s AND user_id != %s", (email, user_id))
            if cursor.fetchone():
                cursor.close()
                conn.close()
                return False, "That email is already in use."

        if password and password.strip():
            password_hash = hash_password(password)
            cursor.execute(
                "UPDATE users SET username = %s, email = %s, password = %s WHERE user_id = %s",
                (username, email or None, password_hash, user_id)
            )
        else:
            cursor.execute(
                "UPDATE users SET username = %s, email = %s WHERE user_id = %s",
                (username, email or None, user_id)
            )
        
        conn.commit()
        
    except Exception as exc:
        conn.rollback()
        cursor.close()
        conn.close()
        return False, f"Unable to update profile: {exc}"

    cursor.close()
    conn.close()
    return True, "Profile updated successfully."

# ──────────────────────────────────────────────────────────────────────────
# User management (admin only -- enforced at the page level via
# utils.permissions, not here; these are plain data functions)
# ──────────────────────────────────────────────────────────────────────────

VALID_ROLES = ("admin", "dentist", "receptionist")


def list_users():
    """Return all users as a list of dicts, newest first."""
    conn = get_connection()
    if not conn:
        return []
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT user_id, username, role, email, created_at, last_login,
                   COALESCE(login_attempts, 0), COALESCE(is_locked, FALSE)
            FROM users
            ORDER BY created_at DESC
        """)
        rows = cursor.fetchall()
        return [
            {
                "user_id": r[0],
                "username": r[1],
                "role": r[2],
                "email": r[3],
                "created_at": r[4],
                "last_login": r[5],
                "login_attempts": r[6],
                "is_locked": r[7],
            }
            for r in rows
        ]
    except Exception as e:
        print(f"list_users error: {e}")
        return []
    finally:
        cursor.close()
        conn.close()


def create_user(username, password, role, email=None):
    """Create a new user account. Returns (success: bool, message: str)."""
    username = (username or "").strip()
    role = (role or "").strip().lower()

    if not username:
        return False, "Username is required."
    if not password or len(password) < 6:
        return False, "Password must be at least 6 characters."
    if role not in VALID_ROLES:
        return False, f"Role must be one of: {', '.join(VALID_ROLES)}."

    conn = get_connection()
    if not conn:
        return False, "Database unavailable. Please try again later."

    cursor = conn.cursor()
    try:
        cursor.execute("SELECT user_id FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            return False, "That username is already taken."

        if email:
            cursor.execute("SELECT user_id FROM users WHERE email = %s", (email,))
            if cursor.fetchone():
                return False, "That email is already in use."

        password_hash = hash_password(password)
        cursor.execute(
            """
            INSERT INTO users (username, password, role, email)
            VALUES (%s, %s, %s, %s)
            RETURNING user_id
            """,
            (username, password_hash, role, email or None)
        )
        new_user_id = cursor.fetchone()[0]
        conn.commit()
        log_action("CREATE", table_name="users", record_id=new_user_id,
                   new_data={"username": username, "role": role})
        return True, f"User '{username}' created with role '{role}'."

    except Exception as e:
        conn.rollback()
        return False, f"Unable to create user: {e}"
    finally:
        cursor.close()
        conn.close()


def set_user_role(user_id, new_role, acting_user_id=None):
    """Change a user's role. Returns (success: bool, message: str)."""
    new_role = (new_role or "").strip().lower()
    if new_role not in VALID_ROLES:
        return False, f"Role must be one of: {', '.join(VALID_ROLES)}."

    conn = get_connection()
    if not conn:
        return False, "Database unavailable. Please try again later."

    cursor = conn.cursor()
    try:
        # Prevent an admin from demoting themselves and getting locked out
        # of User Management in the same session.
        if acting_user_id is not None and int(acting_user_id) == int(user_id) and new_role != "admin":
            return False, "You can't change your own role away from admin."

        cursor.execute("UPDATE users SET role = %s WHERE user_id = %s", (new_role, user_id))
        conn.commit()
        log_action("UPDATE", table_name="users", record_id=user_id,
                   new_data={"role": new_role}, error_message="Role changed via User Management")
        return True, "Role updated."
    except Exception as e:
        conn.rollback()
        return False, f"Unable to update role: {e}"
    finally:
        cursor.close()
        conn.close()


def set_user_locked(user_id, locked):
    """Lock or unlock an account (also resets failed-attempt counter on unlock)."""
    conn = get_connection()
    if not conn:
        return False, "Database unavailable. Please try again later."

    cursor = conn.cursor()
    try:
        if locked:
            cursor.execute("UPDATE users SET is_locked = TRUE WHERE user_id = %s", (user_id,))
        else:
            cursor.execute(
                "UPDATE users SET is_locked = FALSE, login_attempts = 0 WHERE user_id = %s",
                (user_id,)
            )
        conn.commit()
        log_action("UPDATE", table_name="users", record_id=user_id,
                   new_data={"is_locked": locked}, error_message="Locked via User Management" if locked else "Unlocked via User Management")
        return True, "Unlocked." if not locked else "Locked."
    except Exception as e:
        conn.rollback()
        return False, f"Unable to update lock status: {e}"
    finally:
        cursor.close()
        conn.close()


def delete_user(user_id, acting_user_id=None):
    """Delete a user account. Returns (success: bool, message: str)."""
    if acting_user_id is not None and int(acting_user_id) == int(user_id):
        return False, "You can't delete your own account while logged in as it."

    conn = get_connection()
    if not conn:
        return False, "Database unavailable. Please try again later."

    cursor = conn.cursor()
    try:
        cursor.execute("SELECT username, role FROM users WHERE user_id = %s", (user_id,))
        target = cursor.fetchone()
        cursor.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
        conn.commit()
        log_action("DELETE", table_name="users", record_id=user_id,
                   old_data={"username": target[0], "role": target[1]} if target else None)
        return True, "User deleted."
    except Exception as e:
        conn.rollback()
        return False, f"Unable to delete user: {e}"
    finally:
        cursor.close()
        conn.close()