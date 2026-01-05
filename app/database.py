import json
import os
from datetime import datetime
import psycopg

def get_database_url():
    """Get PostgreSQL connection URL"""
    db_url = os.getenv("DATABASE_URL", "postgresql://localhost/homeopathy")
    
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    
    return db_url

DATABASE_URL = get_database_url()

def get_db_connection():
    """Get PostgreSQL connection"""
    try:
        conn = psycopg.connect(DATABASE_URL, autocommit=False)
        return conn
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return None

def init_db():
    """Initialize PostgreSQL database"""
    conn = get_db_connection()
    if not conn:
        print("❌ Could not connect to database")
        return
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    password VARCHAR(100) NOT NULL,
                    phone VARCHAR(20),
                    age INTEGER,
                    gender VARCHAR(20),
                    role VARCHAR(20) NOT NULL DEFAULT 'patient',
                    doctor_notes TEXT,
                    notes_updated TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cur.execute("""
                CREATE TABLE IF NOT EXISTS consultations (
                    id SERIAL PRIMARY KEY,
                    patient_email VARCHAR(100) NOT NULL,
                    patient_name VARCHAR(100) NOT NULL,
                    symptoms TEXT NOT NULL,
                    duration VARCHAR(50),
                    severity VARCHAR(50),
                    medical_history TEXT,
                    current_medications TEXT,
                    voice_record VARCHAR(255),
                    images TEXT,
                    status VARCHAR(20) DEFAULT 'pending',
                    doctor_reply JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (patient_email) REFERENCES users(email) ON DELETE CASCADE
                )
            """)
            
            cur.execute("""
                CREATE TABLE IF NOT EXISTS case_history (
                    id SERIAL PRIMARY KEY,
                    symptoms TEXT NOT NULL,
                    suggested_remedies VARCHAR(500),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            print("✅ Database initialized")
    except Exception as e:
        print(f"❌ Database init error: {e}")
        conn.rollback()
    finally:
        conn.close()

def save_user(user_data):
    """Save user"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO users (name, email, password, phone, age, gender, role, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (email) DO NOTHING
            """, (
                user_data['name'],
                user_data['email'],
                user_data['password'],
                user_data.get('phone'),
                user_data.get('age'),
                user_data.get('gender'),
                user_data.get('role', 'patient'),
                user_data.get('created_at', datetime.now())
            ))
            conn.commit()
            return True
    except Exception as e:
        print(f"❌ Error saving user: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def get_user(email):
    """Get user by email"""
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE email = %s", (email,))
            row = cur.fetchone()
            if row:
                columns = [desc[0] for desc in cur.description]
                return dict(zip(columns, row))
            return None
    except Exception as e:
        print(f"❌ Error getting user: {e}")
        return None
    finally:
        conn.close()

def load_all_patients():
    """Get all patients"""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE role = 'patient' ORDER BY created_at DESC")
            rows = cur.fetchall()
            columns = [desc[0] for desc in cur.description]
            return [dict(zip(columns, row)) for row in rows]
    except Exception as e:
        print(f"❌ Error loading patients: {e}")
        return []
    finally:
        conn.close()

def save_consultation(consultation):
    """Save consultation"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO consultations 
                (patient_email, patient_name, symptoms, duration, severity, medical_history, 
                 current_medications, voice_record, images, status, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                consultation['patient_email'],
                consultation['patient_name'],
                consultation['symptoms'],
                consultation.get('duration'),
                consultation.get('severity'),
                consultation.get('medical_history'),
                consultation.get('current_medications'),
                consultation.get('voice_record'),
                json.dumps(consultation.get('images', [])),
                consultation.get('status', 'pending'),
                consultation.get('created_at', datetime.now())
            ))
            conn.commit()
            return True
    except Exception as e:
        print(f"❌ Error saving consultation: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def load_consultations():
    """Get all consultations"""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT * FROM consultations ORDER BY created_at DESC
            """)
            rows = cur.fetchall()
            columns = [desc[0] for desc in cur.description]
            consultations = []
            for row in rows:
                cons = dict(zip(columns, row))
                if cons.get('images'):
                    cons['images'] = json.loads(cons['images']) if isinstance(cons['images'], str) else cons['images']
                if cons.get('doctor_reply'):
                    cons['doctor_reply'] = json.loads(cons['doctor_reply']) if isinstance(cons['doctor_reply'], str) else cons['doctor_reply']
                consultations.append(cons)
            return consultations
    except Exception as e:
        print(f"❌ Error loading consultations: {e}")
        return []
    finally:
        conn.close()

def load_patient_consultations(patient_email):
    """Get patient consultations"""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT * FROM consultations WHERE patient_email = %s ORDER BY created_at DESC
            """, (patient_email,))
            rows = cur.fetchall()
            columns = [desc[0] for desc in cur.description]
            consultations = []
            for row in rows:
                cons = dict(zip(columns, row))
                if cons.get('images'):
                    cons['images'] = json.loads(cons['images']) if isinstance(cons['images'], str) else cons['images']
                if cons.get('doctor_reply'):
                    cons['doctor_reply'] = json.loads(cons['doctor_reply']) if isinstance(cons['doctor_reply'], str) else cons['doctor_reply']
                consultations.append(cons)
            return consultations
    except Exception as e:
        print(f"❌ Error loading patient consultations: {e}")
        return []
    finally:
        conn.close()

def get_patient_history(patient_email):
    """Get patient history"""
    return load_patient_consultations(patient_email)

def update_consultation_reply(consultation_id, reply):
    """Update consultation reply"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE consultations 
                SET doctor_reply = %s::jsonb, status = 'replied'
                WHERE id = %s
            """, (json.dumps(reply), consultation_id))
            conn.commit()
            return True
    except Exception as e:
        print(f"❌ Error updating reply: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def update_patient_notes(patient_email, notes):
    """Update patient notes"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE users 
                SET doctor_notes = %s, notes_updated = %s
                WHERE email = %s
            """, (notes, datetime.now(), patient_email))
            conn.commit()
            return True
    except Exception as e:
        print(f"❌ Error updating notes: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def delete_consultation_media(consultation_id, media_type, filename):
    """Delete media"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        with conn.cursor() as cur:
            if media_type == "audio":
                cur.execute("UPDATE consultations SET voice_record = NULL WHERE id = %s", (consultation_id,))
            elif media_type == "image":
                cur.execute("SELECT images FROM consultations WHERE id = %s", (consultation_id,))
                result = cur.fetchone()
                if result:
                    images = json.loads(result[0]) if isinstance(result[0], str) else []
                    if filename in images:
                        images.remove(filename)
                    cur.execute("UPDATE consultations SET images = %s WHERE id = %s", (json.dumps(images), consultation_id))
            
            conn.commit()
            return True
    except Exception as e:
        print(f"❌ Error deleting media: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def save_case(case_data):
    """Save case"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO case_history (symptoms, suggested_remedies, created_at)
                VALUES (%s, %s, %s)
            """, (case_data.get('symptoms'), case_data.get('suggested_remedies'), datetime.now()))
            conn.commit()
            return True
    except Exception as e:
        print(f"❌ Error saving case: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def load_all_cases(limit=20):
    """Get all cases"""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT * FROM case_history ORDER BY created_at DESC LIMIT %s
            """, (limit,))
            rows = cur.fetchall()
            columns = [desc[0] for desc in cur.description]
            return [dict(zip(columns, row)) for row in rows]
    except Exception as e:
        print(f"❌ Error loading cases: {e}")
        return []
    finally:
        conn.close()
