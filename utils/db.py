import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    """
    PostgreSQL connection with proper error handling.
    Returns standard connection object.
    """
    try:
        database_url = os.getenv("DATABASE_URL")
        
        if database_url:
            # For cloud deployment
            return psycopg2.connect(database_url)
        
        # Local development - use values from .env
        return psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            database=os.getenv("DB_NAME", "dental_clinic_db"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD"),
            port=os.getenv("DB_PORT", "5432")
        )
        
    except Exception as e:
        print(f"PostgreSQL connection error: {e}")
        return None


def execute_query(query, params=None, fetch=False):
    """Execute a query and optionally fetch results"""
    conn = None
    try:
        conn = get_connection()
        if not conn:
            print("No database connection")
            return None
        
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params or ())
                if fetch:
                    return cursor.fetchall()
                return True
                
    except Exception as e:
        print(f"Query execution error: {e}")
        return None
    finally:
        if conn:
            conn.close()


def init_database():
    """Initialize all database tables"""
    conn = None
    try:
        conn = get_connection()
        if not conn:
            print("Cannot initialize database - no connection")
            return False
        
        with conn:
            with conn.cursor() as cursor:
                # Patients table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS patients (
                        patient_id SERIAL PRIMARY KEY,
                        name VARCHAR(100) NOT NULL,
                        phone VARCHAR(20),
                        email VARCHAR(100),
                        gender VARCHAR(20),
                        age INTEGER,
                        location TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Appointments table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS appointments (
                        appointment_id SERIAL PRIMARY KEY,
                        patient_id INTEGER REFERENCES patients(patient_id) ON DELETE CASCADE,
                        appointment_date DATE NOT NULL,
                        appointment_time TIME NOT NULL,
                        dentist VARCHAR(100),
                        treatment VARCHAR(100),
                        expected_cost DECIMAL(12,2) DEFAULT 0,
                        status VARCHAR(50) DEFAULT 'Scheduled',
                        appointment_type VARCHAR(50) DEFAULT 'New',
                        lead_time INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Payments table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS payments (
                        payment_id SERIAL PRIMARY KEY,
                        patient_id INTEGER REFERENCES patients(patient_id) ON DELETE CASCADE,
                        payment_date DATE DEFAULT CURRENT_DATE,
                        amount_paid DECIMAL(12,2) DEFAULT 0,
                        balance DECIMAL(12,2) DEFAULT 0,
                        payment_method VARCHAR(50) DEFAULT 'Cash',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Inventory table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS inventory (
                        item_id SERIAL PRIMARY KEY,
                        item_name VARCHAR(100) UNIQUE NOT NULL,
                        quantity INTEGER DEFAULT 0,
                        status VARCHAR(50) DEFAULT 'OK',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Audit logs table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS audit_logs (
                        log_id SERIAL PRIMARY KEY,
                        user_id INTEGER,
                        username VARCHAR(50),
                        action VARCHAR(50),
                        table_name VARCHAR(50),
                        record_id INTEGER,
                        old_data TEXT,
                        new_data TEXT,
                        status VARCHAR(20),
                        error_message TEXT,
                        ip_address VARCHAR(45),
                        user_agent TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
        print("Database initialized successfully")
        return True
        
    except Exception as e:
        print(f"Database initialization error: {e}")
        return False
    finally:
        if conn:
            conn.close()


def test_connection():
    """Test if database connection works"""
    conn = None
    try:
        conn = get_connection()
        if not conn:
            return False
        
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            
        return result is not None
        
    except Exception as e:
        print(f"Database test failed: {e}")
        return False
    finally:
        if conn:
            conn.close()