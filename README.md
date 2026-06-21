# Shallom Dental Clinic Management System

This is a Streamlit web app backed by PostgreSQL.

## 1) Create/configure PostgreSQL
1. Install PostgreSQL and create a database, for example:
   - Database: `dental_clinic_db`
2. Create/choose a user (default in this app: `postgres`).
3. Set the user password.

## 2) Configure environment variables
Copy the provided example:

```powershell
copy .env.example .env
```

Edit `.env` and set:
- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`

Alternatively, you can use `DATABASE_URL` (recommended):

```env
DATABASE_URL="postgresql://DB_USER:DB_PASSWORD@localhost:5432/dental_clinic_db"
```

## 3) Start the app
### Using PowerShell (Windows)
Activate your virtual environment (if you created one):

```powershell
.\venv\Scripts\Activate.ps1
```

Run the app:

```powershell
streamlit run app.py
```

### If you see: `WARNING: DB_PASSWORD environment variable not configured`
That means `DB_PASSWORD` (or `DATABASE_URL`) was not set. Set it in your shell environment or in `.env` and restart Streamlit.

## 4) Default admin account
On first run (when the DB is reachable), the app creates a default admin user:
- Username: `admin`
- Password: `admin123`

If the DB is not reachable, the admin user cannot be created.

## 5) Deployment notes
- In production, do **not** hardcode secrets.
- Prefer `DATABASE_URL`.
- Ensure `audit_logs` table exists if you use the audit pages (see next section).

## 6) Database schema
Tables for the core app are created in `utils/db.py` via `init_database()`.
Auth tables are created in `utils/auth.py` via `init_auth_table()`.

> Note: the audit logger (`utils/audit.py`) expects an `audit_logs` table. If audit features are used, ensure that table exists (or run a full schema initialization that includes it).

