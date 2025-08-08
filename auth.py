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
        html = f"""
        <!DOCTYPE html>
        <html lang="tr">
        
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Şifre Sıfırlama Kodu | SER Elektrik</title>
            <style>
                /* Yukarıdaki CSS kodunun tamamı buraya */
            </style>
        </head>
            <div style="font-family: sans-serif; max-width: 600px; margin: auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
        <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background-color: #f8f9fa; color: #333333;">
            <div class="container" style="max-width: 600px; margin: 20px auto; background-color: #ffffff; border-radius: 15px; overflow: hidden; box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);">
                <div class="header" style="background: linear-gradient(135deg, #005c9d, #0980d3); padding: 30px 20px; text-align: center; color: white;">
                    <div class="logo" style="margin-bottom: 15px; text-align: center;">
                        <img src="https://serotomasyon.tr/static/serlogobeyaz.png" alt="SER Elektrik Otomasyon" style="height: 60px; max-width: 100%; border-radius: 10px;">
                    </div>
                    <h1 style="margin: 0;">Şifre Sıfırlama Talebiniz</h1>
                </div>
                
                <div class="content" style="padding: 40px 30px; line-height: 1.6;">
                    <h2 class="title" style="font-size: 24px; font-weight: 700; margin-bottom: 25px; text-align: center; color: #005c9d; margin-top: 0;">Şifrenizi Sıfırlamak İçin Doğrulama Kodunuz</h2>
                    
                    <p class="message" style="margin-bottom: 30px; font-size: 16px; color: #5e6870;">Merhaba,<br>
                        Şifre sıfırlama talebiniz için doğrulama kodunuz aşağıdadır. Bu kodu kullanarak şifrenizi yeniden oluşturabilirsiniz.</p>
                    
                    <div class="code-container" style="background: linear-gradient(135deg, #f0f4f8, #e1e5e9); border-radius: 12px; padding: 20px; text-align: center; margin: 30px 0;">
                        <div class="code-label" style="font-size: 16px; margin-bottom: 15px; color: #5e6870;">Lütfen aşağıdaki kodu kullanın:</div>
                        <div class="code" style="font-size: 42px; font-weight: 700; letter-spacing: 8px; color: #005c9d; margin: 15px 0; padding: 10px; background: white; border-radius: 10px; display: inline-block; box-shadow: 0 4px 15px rgba(0, 92, 157, 0.15); font-family: monospace;">{code}</div>
                        <div class="code-label" style="font-size: 16px; margin-bottom: 0; color: #5e6870;">Bu kod 15 dakika sonra geçerliliğini yitirecektir.</div>
                    </div>
                    
                    <div style="text-align: center;">
                        <a href="https://www.serotomasyon.tr/sifremi_unuttum.html" class="button" style="display: inline-block; background: linear-gradient(to right, #005c9d, #0980d3); color: white; padding: 14px 35px; text-decoration: none; border-radius: 50px; font-weight: 600; font-size: 16px; margin: 20px 0; box-shadow: 0 4px 15px rgba(9, 128, 211, 0.25);">Şifremi Sıfırla</a>
                    </div>
                    
                    <div class="note" style="background-color: #fff9e6; border-left: 4px solid #ffd700; padding: 15px; border-radius: 0 8px 8px 0; margin: 25px 0; font-size: 14px;">
                        <strong>Önemli:</strong> Bu e-postayı siz talep etmediyseniz lütfen dikkate almayınız. 
                        Güvenliğiniz için bu kodu kimseyle paylaşmayınız.
                    </div>
                    
                </div>
                
                <div class="footer" style="background-color: #f0f4f8; padding: 25px 20px; text-align: center; font-size: 14px; color: #97a1aa;">
                    
                    
                    <div>© 2025 SER Elektrik Otomasyon. Tüm hakları saklıdır.</div>
                    
                    <div class="contact" style="margin-top: 15px; font-size: 13px;">
                        <div>Adres: Ser Plaza, Yeşilce, Dalgıç Sk. No:9, 34418 Kağıthane/İstanbul</div>
                        <div>Telefon: (0212) 324 64 14 | E-posta: info@serelektrik.com</div>
                    </div>
                </div>
            </div>
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
        return True
    except Exception as e:
        print(f"E-posta gönderim hatası: {e}")
        traceback.print_exc()
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