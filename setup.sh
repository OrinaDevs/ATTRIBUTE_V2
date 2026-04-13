#!/bin/bash
# ============================================================
# Attribute Land Survey & Consultants - Setup Script
# Run: bash setup.sh
# ============================================================

set -e

echo ""
echo "========================================================"
echo "  Attribute Land Survey & Consultants - Project Setup"
echo "========================================================"
echo ""

# Check Python
python3 --version || { echo "Python 3 not found. Please install Python 3.10+"; exit 1; }

# Create virtual environment
echo "[1/6] Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "[2/6] Installing dependencies..."
pip install --upgrade pip -q
pip install -r requirements.txt -q

# Run migrations
echo "[3/6] Running database migrations..."
python manage.py migrate

# Seed data
echo "[4/6] Seeding initial data (services, users)..."
python manage.py seed_data

# Collect static files
echo "[5/6] Collecting static files..."
python manage.py collectstatic --noinput -v 0

echo ""
echo "[6/6] Setup complete!"
echo ""
echo "========================================================"
echo "  Credentials"
echo "========================================================"
echo "  Admin:  admin@attributesurvey.co.ke  / admin1234"
echo "  Staff:  staff@attributesurvey.co.ke  / staff1234"
echo "  Client: client@example.com           / client1234"
echo ""
echo "  Staff login uses OTP — check the console email output."
echo "========================================================"
echo ""
echo "Starting development server at http://127.0.0.1:8000 ..."
echo ""
python manage.py runserver
