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

# Initialize database and create default doctor on startup
try:
    init_db()
    print("✅ Database initialized")
    
    # Create default doctor account
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

ALLOWED_AUDIO = {'webm', 'mp3', 'wav', 'ogg', 'm4a'}
ALLOWED_IMAGES = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

matcher = AIRemedyMatcher()

# Production settings
if os.getenv("FLASK_ENV") == "production":
    app.config['DEBUG'] = False
    app.config['TESTING'] = False

# Security headers
@app.after_request
def add_security_headers(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    return response

# Ensure uploads folder exists
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Disable caching for dynamic pages
@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response

# Set security headers
@app.after_request
def set_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
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
    case = CaseHistory(
        symptoms=symptoms,
        suggested_remedies=str([r["name"] for r in results[:3]]),
        created_at=datetime.now()
    )
    save_case(case)
    return render_template("results.html", symptoms=symptoms, remedies=results)

@app.route("/history")
def history():
    try:
        cases = load_all_cases(limit=20)
        
        # Ensure dates are properly formatted for template
        for case in cases:
            if case.get('created_at'):
                if not isinstance(case['created_at'], str):
                    case['created_at'] = case['created_at'].strftime('%Y-%m-%d %H:%M')
        
        return render_template("history.html", cases=cases)
    except Exception as e:
        print(f"❌ Error in history route: {e}")
        flash("Error loading history", "danger")
        return render_template("history.html", cases=[])

# ========== AUTHENTICATION ==========
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
        if get_user(user_data["email"]):
            flash("Email already registered", "danger")
        else:lash("Email already registered", "danger")
            save_user(user_data) registered", "danger")
            flash("Registration successful! Please login.", "success")
            return redirect(url_for("login"))on
    return render_template("auth/register.html")
                flash("Registration successful! You are now logged in.", "success")
@app.route("/logout")n redirect(url_for("patient_dashboard"))
def logout():lse:name": user_data["name"],
    session.pop("user", None)ration failed. Please try again.", "danger")
    flash("Logged out successfully", "info")e"),
    return redirect(url_for("home"))ister.html")
                "gender": user_data.get("gender"),
# ========== PATIENT ROUTES ==========
@app.route("/patient/dashboard")
def patient_dashboard():None)on successful! You are now logged in.", "success")
    if "user" not in session or session["user"]["role"] != "patient":
        flash("Please login as patient", "warning")
        return redirect(url_for("login"))lease try again.", "danger")
    consultations = load_patient_consultations(session["user"]["email"])
    return render_template("patient/dashboard.html", consultations=consultations)
def patient_dashboard():te("auth/register.html")
@app.route("/patient/consult", methods=["GET", "POST"]) != "patient":
def patient_consult():login as patient", "warning")
    if "user" not in session or session["user"]["role"] != "patient":
        flash("Please login as patient", "warning")ion["user"]["email"])
        return redirect(url_for("login"))oard.html", consultations=consultations)
    return redirect(url_for("home"))
    if request.method == "POST":ethods=["GET", "POST"])
        # Handle voice recording======
        voice_filename = Noneor session["user"]["role"] != "patient":
        if "voice_record" in request.files:arning")
            voice_file = request.files["voice_record"]] != "patient":
            if voice_file.filename and allowed_file(voice_file.filename, ALLOWED_AUDIO):
                voice_filename = f"audio_{datetime.now().strftime('%Y%m%d%H%M%S')}_{secure_filename(voice_file.filename)}"
                voice_file.save(os.path.join(app.config["UPLOAD_FOLDER"], voice_filename))
        voice_filename = Noneatient/dashboard.html", consultations=consultations)
        # Handle multiple imagesuest.files:
        image_filenames = []uest.files["voice_record"])
        if "images" in request.files:d allowed_file(voice_file.filename, ALLOWED_AUDIO):
            images = request.files.getlist("images")ow().strftime('%Y%m%d%H%M%S')}_{secure_filename(voice_file.filename)}"
            for img in images:e(os.path.join(app.config["UPLOAD_FOLDER"], voice_filename))
                if img.filename and allowed_file(img.filename, ALLOWED_IMAGES):
                    img_filename = f"img_{datetime.now().strftime('%Y%m%d%H%M%S')}_{secure_filename(img.filename)}"
                    img.save(os.path.join(app.config["UPLOAD_FOLDER"], img_filename))
                    image_filenames.append(img_filename)
            images = request.files.getlist("images")
        consultation = {mages:equest.files:
            "patient_email": session["user"]["email"],ilename, ALLOWED_IMAGES):
            "patient_name": session["user"]["name"],ow().strftime('%Y%m%d%H%M%S')}_{secure_filename(img.filename)}"
            "symptoms": request.form.get("symptoms"),"UPLOAD_FOLDER"], img_filename))ecure_filename(voice_file.filename)}"
            "duration": request.form.get("duration"),me)"UPLOAD_FOLDER"], voice_filename))
            "severity": request.form.get("severity"),
            "medical_history": request.form.get("medical_history"),
            "current_medications": request.form.get("current_medications"),
            "voice_record": voice_filename,["name"],
            "images": image_filenames,et("symptoms"),
            "status": "pending",form.get("duration"),
            "doctor_reply": None,orm.get("severity"),filename, ALLOWED_IMAGES):
            "created_at": datetime.now().isoformat()ical_history"),%Y%m%d%H%M%S')}_{secure_filename(img.filename)}"
        }   "current_medications": request.form.get("current_medications"),filename))
            "voice_record": voice_filename,img_filename)
        save_consultation(consultation)
        flash("Consultation submitted successfully!", "success")
        return redirect(url_for("patient_dashboard")),
            "created_at": datetime.now().isoformat()
    return render_template("patient/consult.html")"),
            "duration": request.form.get("duration"),
# ========== DOCTOR ROUTES ==========n)t("severity"),
@app.route("/doctor/dashboard")mitted successfully!", "success")"),
def doctor_dashboard():(url_for("patient_dashboard"))current_medications"),
    if "user" not in session or session["user"]["role"] != "doctor":
        flash("Please login as doctor", "warning")
        return redirect(url_for("doctor_login"))
    ======== DOCTOR ROUTES ==========
    consultations = load_consultations().isoformat()
    doctor_dashboard():
    # Separate pending and replied session["user"]["role"] != "doctor":
    pending_consultations = [c for c in consultations if c.get('status') == 'pending']
    replied_consultations = [c for c in consultations if c.get('status') == 'replied']
    pending_count = len(pending_consultations)oard"))
    replied_count = len(replied_consultations)consultations = load_consultations()
    return render_template("patient/consult.html")
    return render_template(
        "doctor/dashboard.html", consultations if c.get('status') == 'pending'])
        consultations=consultations, c.get('status') == 'replied'])
        pending_consultations=pending_consultations, in consultations if c.get('status') == 'pending']
        replied_consultations=replied_consultations,e"] != "doctor":
        pending_count=pending_count,return render_template(
        replied_count=replied_count        "doctor/dashboard.html", 
    )onsultations = load_consultations()
ing_consultations,ding and replied consultations
@app.route("/doctor/reply/<int:consultation_id>", methods=["GET", "POST"])= 'pending']
def doctor_reply(consultation_id): c in consultations if c.get('status') == 'replied']
    if "user" not in session or session["user"]["role"] != "doctor":
        flash("Please login as doctor", "warning")
        return redirect(url_for("doctor_login"))ion_id>", methods=["GET", "POST"])
    return render_template(
    consultations = load_consultations()if "user" not in session or session["user"]["role"] != "doctor":
    consultation = next((c for c in consultations if c.get("id") == consultation_id), None)gin as doctor", "warning")
        pending_consultations=pending_consultations, 
    if not consultation:tions=replied_consultations,
        flash("Consultation not found", "danger")consultations = load_consultations()
        return redirect(url_for("doctor_dashboard"))consultations if c.get("id") == consultation_id), None)
    )
    # Get patient's complete history
    patient_history = get_patient_history(consultation["patient_email"])    flash("Consultation not found", "danger")
    patient_info = get_user(consultation["patient_email"])"doctor_dashboard"))
    if "user" not in session or session["user"]["role"] != "doctor":
    if request.method == "POST":octor", "warning")
        reply = {n["patient_email"])tor_login"))
            "diagnosis": request.form.get("diagnosis"),mail"])
            "remedies": request.form.get("remedies"),
            "potency": request.form.get("potency"),f c.get("id") == consultation_id), None)
            "instructions": request.form.get("instructions"),
            "follow_up": request.form.get("follow_up"),
            "medicines_given": request.form.get("medicines_given"),,l"])
            "doctor_notes": request.form.get("doctor_notes"),   "potency": request.form.get("potency"),
            "replied_at": datetime.now().isoformat()s"),
        }up"),.method == "POST":
        update_consultation_reply(consultation_id, reply)icines_given"),
        flash("Reply sent to patient!", "success")        "doctor_notes": request.form.get("doctor_notes"),
        return redirect(url_for("doctor_dashboard"))at()
            "potency": request.form.get("potency"),
    return render_template("doctor/reply.html", structions"),
                         consultation=consultation, "),
                         patient_history=patient_history,        return redirect(url_for("doctor_dashboard"))
                         patient_info=patient_info)r_notes"),
y.html",    "replied_at": datetime.now().isoformat()
@app.route("/doctor/patient/<patient_email>")
def doctor_view_patient(patient_email):istory,_id, reply)
    if "user" not in session or session["user"]["role"] != "doctor":fo)
        flash("Please login as doctor", "warning")))
        return redirect(url_for("doctor_login"))>")
    return render_template("doctor/reply.html", 
    patient_info = get_user(patient_email)if "user" not in session or session["user"]["role"] != "doctor":
    patient_history = get_patient_history(patient_email)gin as doctor", "warning")
    n"))                 patient_info=patient_info)
    if not patient_info:
        flash("Patient not found", "danger")patient_info = get_user(patient_email)
        return redirect(url_for("doctor_dashboard"))
    if "user" not in session or session["user"]["role"] != "doctor":
    return render_template("doctor/patient_detail.html", 
                         patient=patient_info,         flash("Patient not found", "danger")
                         history=patient_history)
    patient_info = get_user(patient_email)
@app.route("/doctor/patient/<patient_email>/notes", methods=["POST"])
def save_patient_notes(patient_email):t_info, 
    if "user" not in session or session["user"]["role"] != "doctor":)
        flash("Unauthorized", "danger")ger")
        return redirect(url_for("doctor_login"))", methods=["POST"])
    
    from app.database import update_patient_notes]["role"] != "doctor":
    notes = request.form.get("patient_notes", "")
    update_patient_notes(patient_email, notes)ry)
    flash("Patient notes saved successfully!", "success")    
    return redirect(url_for("doctor_view_patient", patient_email=patient_email))
"") save_patient_notes(patient_email):
@app.route("/doctor/delete-media/<int:consultation_id>/<media_type>", methods=["POST"])
def delete_media(consultation_id, media_type):ully!", "success")
    if "user" not in session or session["user"]["role"] != "doctor":", patient_email=patient_email))
        flash("Unauthorized", "danger")
        return redirect(url_for("doctor_login"))ltation_id>/<media_type>", methods=["POST"])
    (consultation_id, media_type):mail, notes)
    filename = request.form.get("filename")!", "success")    
    if filename:r")(url_for("doctor_view_patient", patient_email=patient_email))
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)("doctor_login"))
        if os.path.exists(filepath):t:consultation_id>/<media_type>", methods=["POST"])
            os.remove(filepath)d, media_type):
    if "user" not in session or session["user"]["role"] != "doctor":
    delete_consultation_media(consultation_id, media_type, filename)
    flash(f"{media_type.capitalize()} deleted successfully", "success")        if os.path.exists(filepath):
    return redirect(url_for("doctor_reply", consultation_id=consultation_id)))
    if filename:
@app.route("/doctor/patients")n(app.config["UPLOAD_FOLDER"], filename)
def doctor_patients():essfully", "success")
    if "user" not in session or session["user"]["role"] != "doctor":ultation_id=consultation_id))
        flash("Please login as doctor", "warning")
        return redirect(url_for("doctor_login"))edia_type, filename)
    patients = load_all_patients()()} deleted successfully", "success")
    # Add consultation count for each patientession or session["user"]["role"] != "doctor":
    all_consultations = load_consultations()
    for p in patients:tients")
        p["consultation_count"] = len([c for c in all_consultations if c.get("patient_email") == p["email"]])    patients = load_all_patients()
    return render_template("doctor/patients.html", patients=patients)ach patient
s = load_consultations()gin as doctor", "warning")
# ========== ABOUT PAGE ========== patients:n"))
@app.route("/about") for c in all_consultations if c.get("patient_email") == p["email"]])
def about():    return render_template("doctor/patients.html", patients=patients)
    return render_template("about.html")ns()
E ========== patients:
# ========== GALLERY PAGE ==========bout")or c in all_consultations if c.get("patient_email") == p["email"]])
@app.route("/gallery")late("doctor/patients.html", patients=patients)
def gallery():    return render_template("about.html")
    return render_template("gallery.html")
GE ==========about")
# ========== LOCATION PAGE ==========llery")
@app.route("/location")ate("about.html")
def location():    return render_template("gallery.html")
    return render_template("location.html")
@app.route("/gallery")
# ========== SERVE UPLOADS ==========
@app.route("/uploads/<path:filename>")ml")
def uploaded_file(filename):    return render_template("location.html")
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)
===p.route("/location")
if __name__ == "__main__":@app.route("/uploads/<path:filename>")
    return render_template("location.html")

    app.run(debug=True, port=8000)def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)
def uploaded_file(filename):
if __name__ == "__main__":tory(app.config["UPLOAD_FOLDER"], filename)
    app.run(debug=True, port=8000)
if __name__ == "__main__":
    app.run(debug=True, port=8000)
