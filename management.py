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

@management_bp.route('/')
def index():
    return redirect(url_for('management.dashboard'))

@management_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            data = request.get_json()
            email = data.get('email')
            password = data.get('password')

            if not email or not password:
                return jsonify({"success": False, "message": "E-posta ve şifre gereklidir."})

            conn = get_db_connection()
            with conn.cursor() as cursor:
                # 'personel' tablosunu ve 'email' sütununu kullan
                sql = "SELECT * FROM personel WHERE email = %s"
                cursor.execute(sql, (email,))
                user = cursor.fetchone()

                # Şifre kontrolü için 'sifre' sütununu kullan
                if user and check_password_hash(user['sifre'], password):
                    # JWT Token oluşturma
                    secret_key = os.getenv("SECRET_KEY", "gizli_anahtar")
                    token_payload = {
                        'user_id': user['id'],
                        'email': user['email'],
                        'exp': datetime.utcnow() + timedelta(hours=24)
                    }
                    token = jwt.encode(token_payload, secret_key, algorithm='HS256')
                    return jsonify({"success": True, "message": "Giriş başarılı!", "token": token, "redirect": url_for('management.dashboard')})
                else:
                    return jsonify({"success": False, "message": "Geçersiz e-posta veya şifre."})
        except Exception as e:
            return jsonify({"success": False, "message": f"Bir hata oluştu: {str(e)}"}), 500
        finally:
            if 'conn' in locals():
                conn.close()
    return render_template('personel/login.html')

@management_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        ad = data.get('ad')
        soyad = data.get('soyad')
        email = data.get('email')
        telefon = data.get('telefon')
        password = data.get('password')

        if not ad or not soyad or not email or not password:
            return jsonify({"success": False, "message": "Lütfen tüm alanları doldurunuz."})

        # E-posta formatı kontrolü
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            return jsonify({"success": False, "message": "Geçerli bir e-posta adresi giriniz."})

        # Telefon numarası formatı kontrolü (isteğe bağlı)
        if telefon and not re.match(r"^\d{10}$", telefon):
            return jsonify({"success": False, "message": "Telefon numarası 10 hane olmalıdır."})

        conn = get_db_connection()
        with conn.cursor() as cursor:
            # 'personel' tablosunda e-posta'nın benzersizliğini kontrol etme
            sql_check = "SELECT id FROM personel WHERE email = %s"
            cursor.execute(sql_check, (email,))
            if cursor.fetchone():
                return jsonify({"success": False, "message": "Bu e-posta adresi zaten kullanılıyor."})

            # Şifreyi hash'leme
            hashed_password = generate_password_hash(password)

            # Kullanıcıyı 'personel' tablosuna kaydetme ve 'sifre' sütununu kullanma
            sql_insert = "INSERT INTO personel (ad, soyad, email, telefon, sifre) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(sql_insert, (ad, soyad, email, telefon, hashed_password))
            
            user_id = cursor.lastrowid
            
            # JWT Token oluşturma
            secret_key = os.getenv("SECRET_KEY", "gizli_anahtar")
            token_payload = {
                'user_id': user_id,
                'email': email,
                'exp': datetime.utcnow() + timedelta(hours=24)
            }
            token = jwt.encode(token_payload, secret_key, algorithm='HS256')

            return jsonify({"success": True, "message": "Kayıt başarılı!", "token": token, "redirect": url_for('management.dashboard')})

    except Exception as e:
        return jsonify({"success": False, "message": f"Bir hata oluştu: {str(e)}"}), 500
    finally:
        if 'conn' in locals():
            conn.close()

@management_bp.route('/dashboard')
def dashboard():
    return "Giriş başarılı! Bu bir ana sayfa (dashboard) örneğidir."

# API Endpoints
@management_bp.route('/api/test-db')
def test_db():
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # 'personel' tablosunu kontrol et
            cursor.execute("SHOW TABLES LIKE 'personel';")
            tables = cursor.fetchall()
        return jsonify({"status": "success", "tables": tables})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        if 'conn' in locals():
            conn.close()
