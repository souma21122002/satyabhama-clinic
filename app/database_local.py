import json
import os
import sqlite3
from datetime import datetime

DB_FILE = "homeopathy.db"

def get_db_connection():
    """Get SQLite connection"""
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

def init_db():
    """Initialize SQLite database"""
    conn = get_db_connection()
    if not conn:
        return
    
    try:
        cur = conn.cursor()
        
        # Create users table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                phone TEXT,
                age INTEGER,
                gender TEXT,
                role TEXT DEFAULT 'patient',
                doctor_notes TEXT,
                notes_updated TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create consultations table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS consultations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_email TEXT NOT NULL,
                patient_name TEXT NOT NULL,
                symptoms TEXT NOT NULL,
                duration TEXT,
                severity TEXT,
                medical_history TEXT,
                current_medications TEXT,
                voice_record TEXT,
                images TEXT,
                status TEXT DEFAULT 'pending',
                doctor_reply TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (patient_email) REFERENCES users(email)
            )
        """)
        
        # Create case history table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS case_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symptoms TEXT NOT NULL,
                suggested_remedies TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        print("✅ Database initialized")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

def save_user(user_data):
    """Save user"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO users (name, email, password, phone, age, gender, role, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
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
        print(f"Error: {e}")
        return False
    finally:
        conn.close()

def get_user(email):
    """Get user by email"""
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE email = ?", (email,))
        row = cur.fetchone()
        return dict(row) if row else None
    except Exception as e:
        print(f"Error: {e}")
        return None
    finally:
        conn.close()

def load_all_patients():
    """Get all patients"""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE role = 'patient' ORDER BY created_at DESC")
        return [dict(row) for row in cur.fetchall()]
    except Exception as e:
        print(f"Error: {e}")
        return []
    finally:
        conn.close()

def save_consultation(consultation):
    """Save consultation"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO consultations 
            (patient_email, patient_name, symptoms, duration, severity, medical_history, 
             current_medications, voice_record, images, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
        print(f"Error: {e}")
        return False
    finally:
        conn.close()

def load_consultations():
    """Get all consultations"""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM consultations ORDER BY created_at DESC")
        consultations = []
        for row in cur.fetchall():
            c = dict(row)
            c['images'] = json.loads(c['images']) if isinstance(c['images'], str) else []
            consultations.append(c)
        return consultations
    except Exception as e:
        print(f"Error: {e}")
        return []
    finally:
        conn.close()

def load_patient_consultations(patient_email):
    """Get patient consultations"""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM consultations WHERE patient_email = ? ORDER BY created_at DESC", (patient_email,))
        consultations = []
        for row in cur.fetchall():
            c = dict(row)
            c['images'] = json.loads(c['images']) if isinstance(c['images'], str) else []
            consultations.append(c)
        return consultations
    except Exception as e:
        print(f"Error: {e}")
        return []
    finally:
        conn.close()

def get_patient_history(patient_email):
    """Get patient history"""
    return load_patient_consultations(patient_email)

def update_consultation_reply(consultation_id, reply):
    """Update reply"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cur = conn.cursor()
        cur.execute("""
            UPDATE consultations SET doctor_reply = ?, status = 'replied' WHERE id = ?
        """, (json.dumps(reply), consultation_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        conn.close()

def update_patient_notes(patient_email, notes):
    """Update notes"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cur = conn.cursor()
        cur.execute("""
            UPDATE users SET doctor_notes = ?, notes_updated = ? WHERE email = ?
        """, (notes, datetime.now(), patient_email))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        conn.close()

def delete_consultation_media(consultation_id, media_type, filename):
    """Delete media"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cur = conn.cursor()
        if media_type == "audio":
            cur.execute("UPDATE consultations SET voice_record = NULL WHERE id = ?", (consultation_id,))
        elif media_type == "image":
            cur.execute("SELECT images FROM consultations WHERE id = ?", (consultation_id,))
            result = cur.fetchone()
            if result:
                images = json.loads(result['images']) if isinstance(result['images'], str) else []
                if filename in images:
                    images.remove(filename)
                cur.execute("UPDATE consultations SET images = ? WHERE id = ?", (json.dumps(images), consultation_id))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        conn.close()

def save_case(case_data):
    """Save case"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO case_history (symptoms, suggested_remedies, created_at)
            VALUES (?, ?, ?)
        """, (case_data.get('symptoms'), case_data.get('suggested_remedies'), datetime.now()))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        conn.close()

def load_all_cases(limit=20):
    """Get cases"""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM case_history ORDER BY created_at DESC LIMIT ?", (limit,))
        return [dict(row) for row in cur.fetchall()]
    except Exception as e:
        print(f"Error: {e}")
        return []
    finally:
        conn.close()
