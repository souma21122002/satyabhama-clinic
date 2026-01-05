web: gunicorn app.main:app
release: python -c "from app.database import init_db; init_db()"
