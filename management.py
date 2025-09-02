from flask import Blueprint, render_template, redirect, url_for, session, flash, request, jsonify, current_app
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
        host=os.getenv("MYSQL_HOST_NEW"),
        user=os.getenv("MYSQL_USER_NEW"),
        password=os.getenv("MYSQL_PASSWORD_NEW"),
        database=os.getenv("MYSQL_DATABASE_NEW"),
        port=int(os.getenv("MYSQL_PORT_NEW")),
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
            data = request.get_json(silent=True)
            if not data:  # fallback form data
                data = request.form

            email = data.get('email')
            password = data.get('password')

            if not email or not password:
                return jsonify({"success": False, "message": "E-posta ve şifre gereklidir."})

            conn = get_db_connection()
            with conn.cursor() as cursor:
                sql = "SELECT * FROM personel WHERE email = %s"
                cursor.execute(sql, (email,))
                user = cursor.fetchone()

                if user and 'sifre' in user and check_password_hash(user['sifre'], password):
                    # Store user info in session
                    session['user_id'] = user['id']
                    session['email'] = user['email']
                    session['logged_in'] = True
                    
                    # Also create a JWT token for API authentication
                    secret_key = current_app.secret_key or os.getenv("SECRET_KEY", "gizli_anahtar")
                    token_payload = {
                        'user_id': user['id'],
                        'email': user['email'],
                        'exp': datetime.utcnow() + timedelta(hours=24)
                    }
                    token = jwt.encode(token_payload, secret_key, algorithm='HS256')
                    session['jwt_token'] = token
                    
                    # Return success response with token
                    return jsonify({
                        "success": True, 
                        "message": "Giriş başarılı!",
                        "token": token, 
                        "redirect": url_for('management.dashboard')
                    })
                else:
                    return jsonify({"success": False, "message": "Geçersiz e-posta veya şifre."})
        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({"success": False, "message": f"Bir hata oluştu: {str(e)}"}), 500
        finally:
            if 'conn' in locals():
                conn.close()

    # If GET request, check if already logged in
    if session.get('logged_in'):
        return redirect(url_for('management.dashboard'))
        
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
    # Check if user is logged in via session
    if not session.get('logged_in'):
        return redirect(url_for('management.login'))
        
    try:
        # Get user info from session
        user_id = session.get('user_id')
        email = session.get('email')
        
        if not user_id or not email:
            return redirect(url_for('management.login'))
            
        # Render dashboard with user info
        return render_template('personel/dashboard.html', 
                             user_id=user_id, 
                             email=email)
                             
    except Exception as e:
        # If any error occurs, log out and redirect to login
        session.clear()
        return redirect(url_for('management.login'))
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
