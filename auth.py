import os
import random
import string
import datetime
import pymysql.cursors
import bcrypt
import traceback
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import request, jsonify, session
import dotenv

dotenv.load_dotenv()

# -------------------- DB CONNECTION --------------------
def get_db_connection():
    return pymysql.connect(
        host=os.getenv("MYSQL_HOST"),
        port=int(os.getenv("MYSQL_PORT")),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DATABASE"),
        cursorclass=pymysql.cursors.DictCursor
    )

# -------------------- SEND EMAIL --------------------
def send_email(subject, code, to_email):
    sender_email = os.getenv("EMAIL_SENDER")
    sender_password = os.getenv("EMAIL_PASSWORD")
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT"))

    try:
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = sender_email
        message["To"] = to_email

        # Yeni HTML içeriğimiz
        # 'Şifremi Sıfırla' butonuna tıklanınca doğrudan doğrulama kodunun girilmesi aşamasına geçiş
        html = f"""
        <!DOCTYPE html>
        <html lang="tr">
        <head>
            <meta charset="UTF-8">
            <title>Şifre Sıfırlama</title>
        </head>
        <body>
            <div style="font-family: sans-serif; max-width: 600px; margin: auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
                <h2 style="color: #005c9d;">Şifre Sıfırlama İsteği</h2>
                <p>Merhaba,</p>
                <p>Şifrenizi sıfırlamak için bir istek aldınız. Lütfen aşağıdaki butona tıklayarak işlemi tamamlayın.</p>
                <p style="text-align: center; margin: 30px 0;">
                    <!-- 'sifremi_unuttum.html' sayfasına yönlendiren link. 'step' parametresi ile doğrudan 2. adıma atlanacak. -->
                    <!-- NOT: Kod ve email güvenlik nedeniyle URL'ye eklenmiştir. Gerçek bir senaryoda bu yerine token kullanılması daha güvenli olacaktır. -->
                    <a href="https://www.serotomasyon.tr/sifremi_unuttum.html?step=2&email={to_email}&code={code}" class="button" style="display: inline-block; padding: 12px 24px; font-size: 16px; color: #ffffff; background-color: #005c9d; text-decoration: none; border-radius: 5px;">Şifremi Sıfırla</a>
                </p>
                <p>Doğrudan kodu girmek isterseniz: <strong>{code}</strong></p>
                <p>Eğer bu isteği siz yapmadıysanız, bu e-postayı dikkate almayın.</p>
                <p style="font-size: 12px; color: #777;">Ser Elektrik Otomasyon</p>
            </div>
        </body>
        </html>
        """

        part1 = MIMEText(html, "html")
        message.attach(part1)

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_server, smtp_port, context=context) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, to_email, message.as_string())

        return True
    except Exception as e:
        print(f"E-posta gönderme hatası: {e}")
        return False

# -------------------- HANDLERS --------------------
def handle_forgot_password():
    data = request.get_json()
    email = data.get('email')
    if not email:
        return jsonify({'message': 'E-posta adresi gerekli.'}), 400

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()
            if not user:
                return jsonify({'message': 'Bu e-posta adresine kayıtlı bir kullanıcı bulunamadı.'}), 404

            code = ''.join(random.choices(string.digits, k=6))
            expires_at = datetime.datetime.now() + datetime.timedelta(minutes=15)

            cursor.execute(
                "UPDATE users SET verification_code = %s, verification_code_expires_at = %s WHERE email = %s",
                (code, expires_at, email)
            )
            connection.commit()

            send_email("Şifre Sıfırlama Kodunuz", code, email)
            session['reset_email'] = email

            return jsonify({'message': 'Şifre sıfırlama kodu e-posta adresinize gönderildi.'}), 200
    except Exception as e:
        print(f"Şifre sıfırlama kodu gönderme hatası: {e}")
        traceback.print_exc()
        return jsonify({'message': 'Bir hata oluştu, lütfen tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()

def handle_verify_code():
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
        traceback.print_exc()
        return jsonify({'message': 'Bir hata oluştu.'}), 500
    finally:
        if connection:
            connection.close()

def handle_reset_password():
    data = request.get_json()
    email = session.get('reset_email')
    code = data.get('code')
    new_password = data.get('new_password')

    if not email or not code or not new_password:
        return jsonify({'message': 'Eksik bilgi.'}), 400

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id, verification_code, verification_code_expires_at FROM users WHERE email = %s",
                (email,)
            )
            user = cursor.fetchone()
            if not user or user['verification_code'] != code:
                return jsonify({'message': 'Geçersiz kod.'}), 400

            if not user['verification_code_expires_at'] or datetime.datetime.now() > user['verification_code_expires_at']:
                return jsonify({'message': 'Kodun süresi dolmuş.'}), 400

            hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            cursor.execute(
                "UPDATE users SET password = %s, verification_code = NULL, verification_code_expires_at = NULL WHERE id = %s",
                (hashed_password, user['id'])
            )
            connection.commit()
            session.pop('reset_email', None)

            return jsonify({'message': 'Şifreniz başarıyla güncellendi.'}), 200
    except Exception as e:
        print(f"Şifre sıfırlama hatası: {e}")
        traceback.print_exc()
        return jsonify({'message': 'Bir hata oluştu, lütfen tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()