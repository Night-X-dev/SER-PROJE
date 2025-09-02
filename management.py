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


@management_bp.route('/register', methods=['GET', 'POST'])
@management_bp.route('/register.html', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            data = request.get_json() if request.is_json else request.form
            
            # Form verilerini al
            ad = data.get('ad', '').strip()
            soyad = data.get('soyad', '').strip()
            email = data.get('email', '').strip().lower()
            telefon = data.get('telefon', '').strip()
            sifre = data.get('password', '')
            sifre_tekrar = data.get('password_confirm', '')
            
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
            
            # Telefon numarasını temizle (sadece rakamlar)
            telefon = ''.join(filter(str.isdigit, telefon))
            
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
                    
                    # Yeni oluşturulan kullanıcıyı al
                    user_id = cursor.lastrowid
                    
                    # Kullanıcıyı oturum açık olarak işaretle
                    session['personel_logged_in'] = True
                    session['personel_id'] = user_id
                    session['personel_email'] = email
                    session['personel_adi'] = f"{ad} {soyad}"
                    
                    return jsonify({
                        "success": True,
                        "message": "Kayıt başarılı! Yönlendiriliyorsunuz...",
                        "redirect": url_for('management.dashboard')
                    })
                    
            except Exception as e:
                print(f"Kayıt sırasında hata oluştu: {e}")
                return jsonify({"success": False, "message": "Kayıt sırasında bir hata oluştu!"}), 500
                
            finally:
                connection.close()
                
        except Exception as e:
            print(f"Beklenmeyen hata: {e}")
            return jsonify({"success": False, "message": "Beklenmeyen bir hata oluştu!"}), 500
    
    # GET isteği için giriş sayfasını göster (register formu login.html'de)
    return redirect(url_for('management.login'))

@management_bp.route('/login', methods=['GET', 'POST'])
@management_bp.route('/login.html', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            # Get request data (handle both JSON and form data)
            data = request.get_json() if request.is_json else request.form
            email = data.get('email', '').strip().lower()
            password = data.get('password', '')
            
            # Required field validation
            if not email or not password:
                return jsonify({"success": False, "message": "E-posta ve şifre alanları zorunludur!"}), 400
            
            # Email format validation
            if not validate_email(email):
                return jsonify({"success": False, "message": "Geçerli bir e-posta adresi giriniz!"}), 400
            
            # Get user from database
            user = get_user_by_email(email)
            
            # Check if user exists and password is correct
            if not user or not check_password(user['sifre'], password):
                return jsonify({"success": False, "message": "Geçersiz e-posta veya şifre!"}), 401
            
            # Check if user is active
            if user.get('durum') != 'aktif':
                return jsonify({
                    "success": False, 
                    "message": "Hesabınız aktif değil! Lütfen yöneticinizle iletişime geçin."
                }), 403
            
            # Update last login time
            connection = get_db_connection()
            try:
                with connection.cursor() as cursor:
                    sql = "UPDATE personel SET son_giris_tarihi = %s WHERE id = %s"
                    cursor.execute(sql, (datetime.now(), user['id']))
            finally:
                connection.close()
            
            # Set session data
            session['personel_logged_in'] = True
            session['personel_id'] = user['id']
            session['personel_email'] = user['email']
            session['personel_adi'] = f"{user['ad']} {user['soyad']}"
            
            # Create JWT token for API authentication
            token = create_jwt_token(user['id'], user['email'])
            
            # Prepare response data
            response_data = {
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
            }
            
            # If it's a JSON request, return JSON response
            if request.is_json:
                return jsonify(response_data)
            
            # For form submission, redirect to dashboard
            flash('Başarıyla giriş yaptınız!', 'success')
            return redirect(url_for('management.dashboard'))
            
        except Exception as e:
            error_message = "Giriş sırasında bir hata oluştu!"
            print(f"{error_message}: {e}")
            
            if request.is_json:
                return jsonify({"success": False, "message": error_message}), 500
            
            flash(error_message, 'danger')
            return redirect(url_for('management.login'))
    
    # For GET request, check if user is already logged in
    if 'personel_logged_in' in session:
        return redirect(url_for('management.dashboard'))
    
    # Show login page for non-logged in users
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
