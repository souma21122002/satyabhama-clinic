import os
from app.main import app

if __name__ == "__main__":
    print("=" * 50)
    print("🌿 HOMEOPATHY HEALING CENTER")
    print("=" * 50)
    print("✅ Gemini AI API key configured")
    print("")
    print("📍 Open http://localhost:8000")
    print("")
    print("👨‍⚕️ Doctor Login:")
    print("   Email: doctor@homeopathy.com")
    print("   Password: doctor123")
    print("=" * 50)
    
    app.run(debug=True, host="0.0.0.0", port=8000)
