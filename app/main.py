import os
import sys
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
from app.ai_matcher import AIRemedyMatcher

# Use appropriate database based on environment
if os.getenv("FLASK_ENV") == "production":
    from app.database import (
        init_db, save_case, load_all_cases, save_consultation, load_consultations,
        load_patient_consultations, save_user, get_user, load_all_patients,
        update_consultation_reply, delete_consultation_media, get_patient_history,
        update_patient_notes
    )
else:
    from app.database_local import (
        init_db, save_case, load_all_cases, save_consultation, load_consultations,
        load_patient_consultations, save_user, get_user, load_all_patients,
        update_consultation_reply, delete_consultation_media, get_patient_history,
        update_patient_notes
    )

from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "homeopathy-secret-key-2024")

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

ALLOWED_AUDIO = {'webm', 'mp3', 'wav', 'ogg', 'm4a'}
ALLOWED_IMAGES = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

try:
    init_db()
    print("✅ Database initialized")
    
    doctor_email = "doctor@homeopathy.com"
    if not get_user(doctor_email):
        doctor_data = {
            "name": "Dr. Ajoy Kumar Singha Mahapatra",
            "email": doctor_email,
            "password": "doctor123",
            "phone": "+919932199936",
            "age": 35,
            "gender": "male",
            "role": "doctor"
        }
        save_user(doctor_data)
        print(f"✅ Default doctor account created: {doctor_email}")
    else:
        print(f"✅ Doctor account already exists: {doctor_email}")
except Exception as e:
    print(f"⚠️ Startup warning: {e}")

matcher = AIRemedyMatcher()

# Production settings
if os.getenv("FLASK_ENV") == "production":
    app.config['DEBUG'] = False

# Security headers
@app.after_request
def add_security_headers(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    return response

def allowed_file(filename, allowed_set):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_set

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/find-remedy", methods=["POST"])
def find_remedy():
    symptoms = request.form.get("symptoms", "")
    results = matcher.find_matching_remedies(symptoms)
    save_case({"symptoms": symptoms, "suggested_remedies": str([r.get("name") for r in results[:3]])})
    return render_template("results.html", symptoms=symptoms, remedies=results)

@app.route("/history")
def history():
    cases = load_all_cases(limit=20)
    return render_template("history.html", cases=cases)

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/gallery")
def gallery():
    return render_template("gallery.html")

@app.route("/location")
def location():
    return render_template("location.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user = get_user(email)
        if user and user["password"] == password:
            if user["role"] == "doctor":
                flash("Please use Doctor Login page", "warning")
                return redirect(url_for("doctor_login"))
            session["user"] = user
            flash("Login successful!", "success")
            return redirect(url_for("patient_dashboard"))
        flash("Invalid email or password", "danger")
    return render_template("auth/login.html")

@app.route("/doctor/login", methods=["GET", "POST"])
def doctor_login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user = get_user(email)
        if user and user["password"] == password and user["role"] == "doctor":
            session["user"] = user
            flash("Welcome Doctor!", "success")
            return redirect(url_for("doctor_dashboard"))
        flash("Invalid credentials or not a doctor account", "danger")
    return render_template("auth/doctor_login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        user_data = {
            "name": request.form.get("name"),
            "email": request.form.get("email"),
            "password": request.form.get("password"),
            "phone": request.form.get("phone"),
            "age": request.form.get("age"),
            "gender": request.form.get("gender"),
            "role": "patient",
            "created_at": datetime.now().isoformat()
        }
        
        existing_user = get_user(user_data["email"])
        if existing_user:
            flash("Email already registered", "danger")
            return render_template("auth/register.html")
        
        if save_user(user_data):
            session["user"] = {
                "name": user_data["name"],
                "email": user_data["email"],
                "phone": user_data.get("phone"),
                "age": user_data.get("age"),
                "gender": user_data.get("gender"),
                "role": "patient"
            }
            flash("Registration successful! You are now logged in.", "success")
            return redirect(url_for("patient_dashboard"))
        else:
            flash("Registration failed. Please try again.", "danger")
    
    return render_template("auth/register.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("Logged out successfully", "info")
    return redirect(url_for("home"))

@app.route("/patient/dashboard")
def patient_dashboard():
    if "user" not in session or session["user"]["role"] != "patient":
        flash("Please login as patient", "warning")
        return redirect(url_for("login"))
    consultations = load_patient_consultations(session["user"]["email"])
    return render_template("patient/dashboard.html", consultations=consultations)

@app.route("/patient/consult", methods=["GET", "POST"])
def patient_consult():
    if "user" not in session or session["user"]["role"] != "patient":
        flash("Please login as patient", "warning")
        return redirect(url_for("login"))
    
    if request.method == "POST":
        voice_filename = None
        if "voice_record" in request.files:
            voice_file = request.files["voice_record"]
            if voice_file.filename and allowed_file(voice_file.filename, ALLOWED_AUDIO):
                voice_filename = f"audio_{datetime.now().strftime('%Y%m%d%H%M%S')}_{secure_filename(voice_file.filename)}"
                voice_file.save(os.path.join(app.config["UPLOAD_FOLDER"], voice_filename))
        
        image_filenames = []
        if "images" in request.files:
            images = request.files.getlist("images")
            for img in images:
                if img.filename and allowed_file(img.filename, ALLOWED_IMAGES):
                    img_filename = f"img_{datetime.now().strftime('%Y%m%d%H%M%S')}_{secure_filename(img.filename)}"
                    img.save(os.path.join(app.config["UPLOAD_FOLDER"], img_filename))
                    image_filenames.append(img_filename)
        
        consultation = {
            "patient_email": session["user"]["email"],
            "patient_name": session["user"]["name"],
            "symptoms": request.form.get("symptoms"),
            "duration": request.form.get("duration"),
            "severity": request.form.get("severity"),
            "medical_history": request.form.get("medical_history"),
            "current_medications": request.form.get("current_medications"),
            "voice_record": voice_filename,
            "images": image_filenames,
            "status": "pending",
            "doctor_reply": None,
            "created_at": datetime.now().isoformat()
        }
        
        save_consultation(consultation)
        flash("Consultation submitted successfully!", "success")
        return redirect(url_for("patient_dashboard"))
    
    return render_template("patient/consult.html")

@app.route("/doctor/dashboard")
def doctor_dashboard():
    if "user" not in session or session["user"]["role"] != "doctor":
        flash("Please login as doctor", "warning")
        return redirect(url_for("doctor_login"))
    
    consultations = load_consultations()
    pending_consultations = [c for c in consultations if c.get('status') == 'pending']
    replied_consultations = [c for c in consultations if c.get('status') == 'replied']
    pending_count = len(pending_consultations)
    replied_count = len(replied_consultations)
    
    return render_template(
        "doctor/dashboard.html",
        consultations=consultations,
        pending_consultations=pending_consultations,
        replied_consultations=replied_consultations,
        pending_count=pending_count,
        replied_count=replied_count
    )

@app.route("/doctor/reply/<int:consultation_id>", methods=["GET", "POST"])
def doctor_reply(consultation_id):
    if "user" not in session or session["user"]["role"] != "doctor":
        flash("Please login as doctor", "warning")
        return redirect(url_for("doctor_login"))
    
    consultations = load_consultations()
    consultation = next((c for c in consultations if c.get("id") == consultation_id), None)
    
    if not consultation:
        flash("Consultation not found", "danger")
        return redirect(url_for("doctor_dashboard"))
    
    patient_history = get_patient_history(consultation["patient_email"])
    patient_info = get_user(consultation["patient_email"])
    
    if request.method == "POST":
        reply = {
            "diagnosis": request.form.get("diagnosis"),
            "remedies": request.form.get("remedies"),
            "potency": request.form.get("potency"),
            "instructions": request.form.get("instructions"),
            "follow_up": request.form.get("follow_up"),
            "medicines_given": request.form.get("medicines_given"),
            "doctor_notes": request.form.get("doctor_notes"),
            "replied_at": datetime.now().isoformat()
        }
        update_consultation_reply(consultation_id, reply)
        flash("Reply sent to patient!", "success")
        return redirect(url_for("doctor_dashboard"))
    
    return render_template("doctor/reply.html",
                         consultation=consultation,
                         patient_history=patient_history,
                         patient_info=patient_info)

@app.route("/doctor/patient/<patient_email>")
def doctor_view_patient(patient_email):
    if "user" not in session or session["user"]["role"] != "doctor":
        flash("Please login as doctor", "warning")
        return redirect(url_for("doctor_login"))
    
    patient_info = get_user(patient_email)
    patient_history = get_patient_history(patient_email)
    
    if not patient_info:
        flash("Patient not found", "danger")
        return redirect(url_for("doctor_dashboard"))
    
    return render_template("doctor/patient_detail.html",
                         patient=patient_info,
                         history=patient_history)

@app.route("/doctor/patient/<patient_email>/notes", methods=["POST"])
def save_patient_notes(patient_email):
    if "user" not in session or session["user"]["role"] != "doctor":
        flash("Unauthorized", "danger")
        return redirect(url_for("doctor_login"))
    
    notes = request.form.get("patient_notes", "")
    update_patient_notes(patient_email, notes)
    flash("Patient notes saved successfully!", "success")
    return redirect(url_for("doctor_view_patient", patient_email=patient_email))

@app.route("/doctor/delete-media/<int:consultation_id>/<media_type>", methods=["POST"])
def delete_media(consultation_id, media_type):
    if "user" not in session or session["user"]["role"] != "doctor":
        flash("Unauthorized", "danger")
        return redirect(url_for("doctor_login"))
    
    filename = request.form.get("filename")
    if filename:
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        if os.path.exists(filepath):
            os.remove(filepath)
    
    delete_consultation_media(consultation_id, media_type, filename)
    flash(f"{media_type.capitalize()} deleted", "success")
    return redirect(url_for("doctor_reply", consultation_id=consultation_id))

@app.route("/doctor/patients")
def doctor_patients():
    if "user" not in session or session["user"]["role"] != "doctor":
        flash("Please login as doctor", "warning")
        return redirect(url_for("doctor_login"))
    patients = load_all_patients()
    all_consultations = load_consultations()
    for p in patients:
        p["consultation_count"] = len([c for c in all_consultations if c.get("patient_email") == p["email"]])
    return render_template("doctor/patients.html", patients=patients)

# ========== SERVE UPLOADS ==========
@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

if __name__ == "__main__":
    app.run(debug=True, port=8000)
