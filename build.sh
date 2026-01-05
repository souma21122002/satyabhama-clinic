#!/bin/bash
set -e
pip install -r requirements.txt
python << 'EOF'
from app.database import init_db
init_db()
EOF
