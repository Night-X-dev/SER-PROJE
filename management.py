from flask import Blueprint, render_template, redirect, url_for, session, flash, request, jsonify
import pymysql.cursors
import os
import bcrypt
import re
from datetime import datetime, timedelta
from dotenv import load_dotenv
from functools import wraps
import jwt
from werkzeug.security import generate_password_hash, check_password_hash

# Load environment variables
load_dotenv()

# JWT Secret Key
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-secret-key-here')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION = 86400  # 24 hours in seconds

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
        'exp': datetime.utcnow() + timedelta(seconds=JWT_EXPIRATION)
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def get_user_by_email(email):
    """Email ile kullanıcı bilgilerini getir"""
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = "SELECT * FROM personel WHERE email = %s"
            cursor.execute(sql, (email,))
            return cursor.fetchone()
    except Exception as e:
        print(f"Kullanıcı getirilirken hata oluştu: {e}")
        return None
    finally:
        connection.close()

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'personel_logged_in' not in session:
            return redirect(url_for('management.login'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@management_bp.route('/')
def index():
    if 'personel_logged_in' in session:
        return redirect(url_for('management.dashboard'))
    return redirect(url_for('management.login'))

@management_bp.route('/register', methods=['GET', 'POST'])
@management_bp.route('/register.html', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            data = request.get_json() if request.is_json else request.form
            
            # Form verilerini al
            ad = data.get('ad')
            soyad = data.get('soyad')
            email = data.get('email')
            telefon = data.get('telefon')
            sifre = data.get('password')
            sifre_tekrar = data.get('password_confirm')
            
            # Zorunlu alan kontrolü
            if not all([ad, soyad, email, sifre, sifre_tekrar]):
                return jsonify({"success": False, "message": "Tüm alanları doldurunuz!"}), 400
                
            # Email format kontrolü
            if not validate_email(email):
                return jsonify({"success": False, "message": "Geçerli bir email adresi giriniz!"}), 400
                
            # Şifre eşleşme kontrolü
            if sifre != sifre_tekrar:
                return jsonify({"success": False, "message": "Şifreler eşleşmiyor!"}), 400
                
            # Şifre güvenlik kontrolü
            if len(sifre) < 8:
                return jsonify({"success": False, "message": "Şifre en az 8 karakter olmalıdır!"}), 400
                
            # Telefon numarası kontrolü
            if telefon and not validate_phone(telefon):
                return jsonify({"success": False, "message": "Geçerli bir telefon numarası giriniz! (05XX XXX XX XX)"}), 400
                
            # Email kontrolü
            if get_user_by_email(email):
                return jsonify({"success": False, "message": "Bu email adresi zaten kayıtlı!"}), 400
                
            # Veritabanına kaydet
            connection = get_db_connection()
            try:
                with connection.cursor() as cursor:
                    sql = """
                        INSERT INTO personel (ad, soyad, email, telefon, sifre, departman, pozisyon, ise_baslama_tarihi, durum)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    cursor.execute(sql, (
                        ad,
                        soyad,
                        email,
                        telefon,
                        hash_password(sifre),
                        'Genel',  # Varsayılan departman
                        'Personel',  # Varsayılan pozisyon
                        datetime.now().date(),  # İşe başlama tarihi
                        'aktif'  # Varsayılan durum
                    ))
                    
                    # Kullanıcıyı oturum açmış olarak işaretle
                    user_id = cursor.lastrowid
                    session['personel_logged_in'] = True
                    session['personel_id'] = user_id
                    session['personel_email'] = email
                    session['personel_adi'] = f"{ad} {soyad}"
                    
                    # JWT token oluştur
                    token = create_jwt_token(user_id, email)
                    
                    return jsonify({
                        "success": True,
                        "message": "Kayıt başarılı! Yönlendiriliyorsunuz...",
                        "redirect": url_for('management.dashboard'),
                        "token": token
                    })
                    
            except Exception as e:
                print(f"Kayıt sırasında hata oluştu: {e}")
                return jsonify({"success": False, "message": "Kayıt sırasında bir hata oluştu!"}), 500
                
            finally:
                connection.close()
                
        except Exception as e:
            print(f"Beklenmeyen hata: {e}")
            return jsonify({"success": False, "message": "Beklenmeyen bir hata oluştu!"}), 500
    
    # GET isteği için kayıt sayfasını göster
    return render_template('register.html')

@management_bp.route('/login', methods=['GET', 'POST'])
@management_bp.route('/login.html', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            # İstek verilerini al
            data = request.get_json() if request.is_json else request.form
            email = data.get('email')
            password = data.get('password')
            
            # Zorunlu alan kontrolü
            if not email or not password:
                return jsonify({"success": False, "message": "E-posta ve şifre alanları zorunludur!"}), 400
                
            # Kullanıcıyı veritabanından bul
            user = get_user_by_email(email)
            
            # Kullanıcı yoksa veya şifre yanlışsa
            if not user or not check_password(user['sifre'], password):
                return jsonify({"success": False, "message": "Geçersiz e-posta veya şifre!"}), 401
                
            # Kullanıcı pasifse
            if user.get('durum') != 'aktif':
                return jsonify({"success": False, "message": "Hesabınız aktif değil! Lütfen yöneticinizle iletişime geçin."}), 403
                
            # Oturum bilgilerini ayarla
            session['personel_logged_in'] = True
            session['personel_id'] = user['id']
            session['personel_email'] = user['email']
            session['personel_adi'] = f"{user['ad']} {user['soyad']}"
            
            # Son giriş tarihini güncelle
            connection = get_db_connection()
            try:
                with connection.cursor() as cursor:
                    sql = "UPDATE personel SET son_giris_tarihi = %s WHERE id = %s"
                    cursor.execute(sql, (datetime.now(), user['id']))
            finally:
                connection.close()
            
            # JWT token oluştur
            token = create_jwt_token(user['id'], user['email'])
            
            return jsonify({
                "success": True,
                "message": "Giriş başarılı!",
                "redirect": url_for('management.dashboard'),
                "token": token,
                "user": {
                    "id": user['id'],
                    "email": user['email'],
                    "ad": user['ad'],
                    "soyad": user['soyad'],
                    "departman": user.get('departman', ''),
                    "pozisyon": user.get('pozisyon', '')
                }
            })
            
        except Exception as e:
            print(f"Giriş sırasında hata oluştu: {e}")
            return jsonify({"success": False, "message": "Giriş sırasında bir hata oluştu!"}), 500
    
    # For GET request, render the login page
    return render_template('personel/login.html')

@management_bp.route('/logout')
def logout():
    session.pop('personel_logged_in', None)
    session.pop('personel_email', None)
    return redirect(url_for('management.login'))

@management_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('personel/dashboard.html')

@management_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # TODO: Implement password change logic
        if new_password == confirm_password:
            flash('Şifre başarıyla değiştirildi!', 'success')
            return redirect(url_for('management.dashboard'))
        else:
            flash('Yeni şifreler eşleşmiyor!', 'danger')
    
    return render_template('change_password.html')

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
