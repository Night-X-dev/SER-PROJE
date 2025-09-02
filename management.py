from flask import Blueprint, render_template, redirect, url_for, session, flash, request, jsonify
import pymysql.cursors
import os
import re
from datetime import datetime, timedelta
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
import jwt

# Load environment variables
load_dotenv()

# Create Blueprint
management_bp = Blueprint(
    'management',
    __name__,
    template_folder='templates/personel',
    static_folder='static',
    static_url_path='/personel/static',
    url_prefix='/personel'
)

# Database connection
def get_db_connection():
    return pymysql.connect(
        host=os.getenv("MYSQL_HOST_NEW", "localhost"),
        user=os.getenv("MYSQL_USER_NEW", "serik"),
        password=os.getenv("MYSQL_PASSWORD_NEW", "Ser.1712_"),
        database=os.getenv("MYSQL_DATABASE_NEW", "ser_ik"),
        port=int(os.getenv("MYSQL_PORT_NEW", 3306)),
        cursorclass=pymysql.cursors.DictCursor,
        charset='utf8mb4',
        autocommit=True
    )

# Utility functions
def validate_email(email):
    """Email adresi doğrulama"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    """Telefon numarası doğrulama (05XX XXX XX XX formatında)"""
    phone = ''.join(filter(str.isdigit, phone))
    return len(phone) == 10 and phone.startswith('5')

def hash_password(password):
    """Şifre hashleme"""
    return generate_password_hash(password)

def check_password(hashed_password, password):
    """Hash'li şifreyi doğrulama"""
    return check_password_hash(hashed_password, password)

def create_jwt_token(user_id, email):
    """JWT token oluşturma"""
    payload = {
        'user_id': user_id,
        'email': email,
        'exp': datetime.utcnow() + timedelta(seconds=86400)
    }
    return jwt.encode(payload, os.getenv('JWT_SECRET_KEY', 'your-secret-key-here'), algorithm='HS256')

# Routes
@management_bp.route('/')
def index():
    return redirect(url_for('management.dashboard'))

@management_bp.route('/login', methods=['GET'])
def login():
    return render_template('personel/login.html')

@management_bp.route('/dashboard')
def dashboard():
    return render_template('personel/dashboard.html')

# API Endpoints
@management_bp.route('/api/test-db')
def test_db():
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SHOW TABLES;")
            tables = cursor.fetchall()
        return jsonify({"status": "success", "tables": tables})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        if 'conn' in locals():
            conn.close()
