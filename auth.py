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
    Şifremi unuttum isteğini işler, doğrulama kodu oluşturur ve e-posta gönderir.
    """
    data = request.get_json()
    email = data.get('email')

    if not email:
        return jsonify({'message': 'E-posta adresi gerekli.'}), 400

    # Veritabanında e-posta adresinin varlığını kontrol et
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT user_id FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()

            if not user:
                return jsonify({'message': 'Bu e-posta adresine kayıtlı bir kullanıcı bulunamadı.'}), 404

            # 6 haneli rastgele bir doğrulama kodu oluştur
            verification_code = ''.join(random.choices(string.digits, k=6))
            # Kodun geçerlilik süresini 15 dakika olarak ayarla
            expires_at = datetime.datetime.now() + datetime.timedelta(minutes=15)

            # Doğrulama kodunu ve süresini veritabanına kaydet
            cursor.execute(
                "UPDATE users SET verification_code = %s, verification_code_expires_at = %s WHERE email = %s",
                (verification_code, expires_at, email)
            )
            connection.commit()

            # Kullanıcıya e-posta gönder
            subject = "Şifre Sıfırlama Kodunuz"
            body = f"Şifrenizi sıfırlamak için doğrulama kodunuz: {verification_code}. Bu kod 15 dakika içinde geçerliliğini yitirecektir."
            send_email(subject, body, email)

            # Session'a e-postayı kaydet (İleriki adımlarda kullanmak için)
            session['reset_email'] = email

            return jsonify({'message': 'Şifre sıfırlama kodu e-posta adresinize gönderildi.'}), 200

    except Exception as e:
        print(f"Şifre sıfırlama kodu gönderme hatası: {e}")
        traceback.print_exc()
        return jsonify({'message': 'Bir hata oluştu, lütfen tekrar deneyin.'}), 500
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
    Doğrulama kodunu ve yeni şifreyi alarak şifreyi sıfırlar.
    """
    data = request.get_json()
    email = session.get('reset_email') # Session'dan e-postayı al
    verification_code = data.get('code')
    new_password = data.get('new_password')

    if not email or not verification_code or not new_password:
        return jsonify({'message': 'Eksik bilgi.'}), 400

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
                return jsonify({'message': 'Geçersiz veya süresi dolmuş doğrulama kodu.'}), 400

            # Şifreyi hashle ve güncelle
            hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            cursor.execute(
                "UPDATE users SET password = %s, verification_code = NULL, verification_code_expires_at = NULL WHERE user_id = %s",
                (hashed_password, user['user_id'])
            )
            connection.commit()

            session.pop('reset_email', None) # Session'daki e-postayı temizle
            return jsonify({'message': 'Şifreniz başarıyla güncellendi.'}), 200

    except Exception as e:
        print(f"Şifre sıfırlama hatası: {e}")
        traceback.print_exc()
        return jsonify({'message': 'Bir hata oluştu, lütfen tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()
def handle_verify_code():
    """
    Kullanıcının girdiği doğrulama kodunu kontrol eder.
    Kod doğru ve süresi geçmemişse 200 döner, değilse hata verir.
    """
    data = request.get_json()
    email = session.get('reset_email')
    code = data.get('code')

    if not email or not code:
        return jsonify({'message': 'Eksik bilgi.'}), 400

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT verification_code, verification_code_expires_at FROM users WHERE email = %s",
                (email,)
            )
            user = cursor.fetchone()
            if not user:
                return jsonify({'message': 'Kullanıcı bulunamadı.'}), 404

            if user['verification_code'] != code:
                return jsonify({'message': 'Kod hatalı.'}), 400

            if not user['verification_code_expires_at'] or datetime.datetime.now() > user['verification_code_expires_at']:
                return jsonify({'message': 'Kodun süresi dolmuş.'}), 400

            return jsonify({'message': 'Kod doğrulandı.'}), 200

    except Exception as e:
        print(f"Kod doğrulama hatası: {e}")
        return jsonify({'message': 'Bir hata oluştu.'}), 500
    finally:
        if connection:
            connection.close()