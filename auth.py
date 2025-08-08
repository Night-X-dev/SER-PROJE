# auth.py
# Şifre sıfırlama sistemi için tüm arka plan mantığını içeren modül.

import os
import random
import string
import datetime
import dotenv
import pymysql.cursors
import bcrypt
import traceback
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import request, jsonify, session

# .env dosyasından ortam değişkenlerini yükle
dotenv.load_dotenv()

# Veritabanı bağlantı bilgilerini al
def get_db_connection():
    """Veritabanı bağlantısı oluşturan ve döndüren yardımcı fonksiyon."""
    return pymysql.connect(
        host=os.getenv("MYSQL_HOST"),
        port=int(os.getenv("MYSQL_PORT")),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DATABASE"),
        cursorclass=pymysql.cursors.DictCursor
    )

# E-posta gönderme fonksiyonu
def send_email(subject, body, to_email):
    """
    Belirtilen alıcıya e-posta gönderen yardımcı fonksiyon.
    E-posta bilgileri .env dosyasından alınır.
    """
    sender_email = os.getenv("EMAIL_SENDER")
    sender_password = os.getenv("EMAIL_PASSWORD")
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT"))

    try:
        # Mesajı oluştur
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = sender_email
        message["To"] = to_email

        # HTML içeriği ekle
        html = f"""\
        <html>
          <body>
            <p>Merhaba,<br>
               Şifre sıfırlama talebiniz için doğrulama kodunuz aşağıdadır:<br>
               <b>{body}</b><br>
               Bu kod 10 dakika sonra geçerliliğini yitirecektir.
            </p>
          </body>
        </html>
        """
        part = MIMEText(html, "html")
        message.attach(part)

        context = ssl.create_default_context()
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls(context=context)
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, to_email, message.as_string())
        
        print(f"DEBUG: E-posta başarıyla gönderildi: {to_email}")
        return True
    except Exception as e:
        print(f"Hata: E-posta gönderilirken bir sorun oluştu: {e}")
        traceback.print_exc()
        return False

# Şifre sıfırlama akışı için ana rotalar
def handle_forgot_password():
    """
    Kullanıcıdan e-posta alıp, doğrulama kodu oluşturup e-posta ile gönderen API rotası.
    """
    if request.method != 'POST':
        return jsonify({'success': False, 'message': 'Invalid request method'}), 405

    data = request.json
    email = data.get('email')

    if not email:
        return jsonify({'success': False, 'message': 'E-posta adresi gerekli.'}), 400

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # E-posta adresinin veritabanında var olup olmadığını kontrol et
            cursor.execute("SELECT user_id FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()

            if not user:
                return jsonify({'success': False, 'message': 'Bu e-posta adresi kayıtlı değil.'}), 404

            user_id = user['user_id']
            # 6 haneli rastgele bir doğrulama kodu oluştur
            verification_code = ''.join(random.choices(string.digits, k=6))
            # Kodun geçerlilik süresini (10 dakika) ayarla
            expiry_time = datetime.datetime.now() + datetime.timedelta(minutes=10)

            # Kod ve son kullanma tarihini veritabanına kaydet
            cursor.execute(
                "UPDATE users SET verification_code = %s, verification_code_expires_at = %s WHERE user_id = %s",
                (verification_code, expiry_time, user_id)
            )
            connection.commit()

            # Doğrulama kodunu e-posta ile gönder
            email_sent = send_email("Şifre Sıfırlama Kodunuz", verification_code, email)
            if email_sent:
                session['reset_email'] = email # E-posta adresini session'da sakla
                return jsonify({'success': True, 'message': 'Doğrulama kodu e-posta adresinize gönderildi.'}), 200
            else:
                return jsonify({'success': False, 'message': 'E-posta gönderimi başarısız oldu.'}), 500

    except Exception as e:
        print(f"Şifre sıfırlama talebi hatası: {e}")
        traceback.print_exc()
        return jsonify({'success': False, 'message': 'Sunucu hatası'}), 500
    finally:
        if connection:
            connection.close()
# app.py
from flask import Flask, request, jsonify
from auth import forgot_password_handler, reset_password_handler

app = Flask(__name__)

@app.route('/forgot-password', methods=['POST'])
def forgot_password_route():
    # auth.py'deki fonksiyonu çağırarak işi ona bırakır.
    return forgot_password_handler()

@app.route('/reset-password', methods=['POST'])
def reset_password_route():
    # auth.py'deki fonksiyonu çağırır.
    return reset_password_handler()
def handle_reset_password():
    """
    Kullanıcıdan doğrulama kodu ve yeni şifreleri alıp, şifreyi güncelleyen API rotası.
    """
    if request.method != 'POST':
        return jsonify({'success': False, 'message': 'Invalid request method'}), 405

    data = request.json
    email = session.get('reset_email')
    verification_code = data.get('code')
    new_password = data.get('new_password')
    confirm_password = data.get('confirm_password')

    if not all([email, verification_code, new_password, confirm_password]):
        return jsonify({'success': False, 'message': 'Tüm alanları doldurmanız gerekiyor.'}), 400

    if new_password != confirm_password:
        return jsonify({'success': False, 'message': 'Şifreler birbiriyle eşleşmiyor.'}), 400
    
    if len(new_password) < 8:
        return jsonify({'success': False, 'message': 'Şifre en az 8 karakter olmalıdır.'}), 400

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Doğrulama kodunu ve süresini kontrol et
            cursor.execute(
                "SELECT user_id, verification_code_expires_at FROM users WHERE email = %s AND verification_code = %s",
                (email, verification_code)
            )
            user = cursor.fetchone()

            if not user or datetime.datetime.now() > user['verification_code_expires_at']:
                return jsonify({'success': False, 'message': 'Geçersiz veya süresi dolmuş doğrulama kodu.'}), 400

            # Şifreyi hashle ve güncelle
            hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            cursor.execute(
                "UPDATE users SET password = %s, verification_code = NULL, verification_code_expires_at = NULL WHERE user_id = %s",
                (hashed_password, user['user_id'])
            )
            connection.commit()

            session.pop('reset_email', None) # Session'daki e-postayı temizle
            return jsonify({'success': True, 'message': 'Şifreniz başarıyla güncellendi.'}), 200

    except Exception as e:
        print(f"Şifre sıfırlama hatası: {e}")
        traceback.print_exc()
        return jsonify({'success': False, 'message': 'Sunucu hatası'}), 500
    finally:
        if connection:
            connection.close()
