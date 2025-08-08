#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Bu betik, Cron job ile belirli aralıklarla çalışacak şekilde tasarlanmıştır.
# Bitiş tarihi geçmiş veya bugünün tarihi olan iş adımlarını bulur ve mail gönderir.

import os
import sys
import pymysql.cursors
import dotenv
from dotenv import load_dotenv
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import datetime
import traceback
import json

# dotenv dosyasını yükle (veritabanı ayarları için hala gerekli olabilir)
load_dotenv()

# Veritabanı ayarlarını env dosyasından çek
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_NAME = os.getenv("DB_NAME")
DB_PORT = int(os.getenv("DB_PORT", 3306))

# E-posta ayarlarını manuel olarak yazıldı
EMAIL_SENDER_ADDRESS = "serelektrikotomasyon@gmail.com"
EMAIL_SENDER_PASSWORD = "yqsjayixagvesrct"  # Boşluklar kaldırıldı
EMAIL_SMTP_SERVER = "smtp.gmail.com"
EMAIL_SMTP_PORT = 587
ADMIN_EMAIL_LIST_JSON = os.getenv("ADMIN_EMAIL_LIST_JSON")

# Eğer ADMIN_EMAIL_LIST_JSON mevcutsa, JSON olarak yükle. Yoksa boş liste kullan.
try:
    ADMIN_EMAIL_LIST = json.loads(ADMIN_EMAIL_LIST_JSON)
except (json.JSONDecodeError, TypeError):
    ADMIN_EMAIL_LIST = []

def get_db_connection():
    """Veritabanı bağlantısı kurar ve döndürür."""
    try:
        return pymysql.connect(host=DB_HOST,
                               user=DB_USER,
                               password=DB_PASS,
                               database=DB_NAME,
                               port=DB_PORT,
                               cursorclass=pymysql.cursors.DictCursor)
    except Exception as e:
        print(f"Hata: Veritabanına bağlanılamadı. Hata detayları: {e}", file=sys.stderr, flush=True)
        return None

def send_email(subject, body, recipient_emails):
    """
    Belirtilen alıcılara e-posta gönderir.
    """
    if not recipient_emails:
        print("Hata: E-posta alıcı listesi boş.", file=sys.stderr, flush=True)
        return False

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = EMAIL_SENDER_ADDRESS
    message["To"] = ", ".join(recipient_emails)
    message.attach(MIMEText(body, "html"))

    try:
        # 'with' ifadesi ile bağlantının otomatik olarak kapanmasını sağla
        with smtplib.SMTP(EMAIL_SMTP_SERVER, EMAIL_SMTP_PORT) as server:
            server.set_debuglevel(1)  # Hata ayıklama çıktısını etkinleştirme
            print("SMTP bağlantısı başlatıldı. TLS'ye yükseltiliyor...", file=sys.stdout, flush=True)
            
            # TLS'ye yükseltme
            server.starttls(context=ssl.create_default_context())
            
            print("TLS başarılı. Giriş yapılıyor...", file=sys.stdout, flush=True)
            
            try:
                # Giriş yapma
                server.login(EMAIL_SENDER_ADDRESS, EMAIL_SENDER_PASSWORD)
            except smtplib.SMTPAuthenticationError as e:
                print(f"Hata: Kimlik doğrulama başarısız. Şifre (uygulama şifresi) veya kullanıcı adı yanlış olabilir. Hata: {e}", file=sys.stderr, flush=True)
                return False
            
            print("Giriş başarılı. E-posta gönderiliyor...", file=sys.stdout, flush=True)
            server.sendmail(EMAIL_SENDER_ADDRESS, recipient_emails, message.as_string())
            print(f"Başarılı: E-posta '{subject}' şu alıcılara gönderildi: {recipient_emails}", file=sys.stdout, flush=True)
        return True
    except smtplib.SMTPException as e:
        print(f"Hata: SMTP sunucusuna bağlanırken veya iletişimde sorun oluştu. Hata: {e}", file=sys.stderr, flush=True)
        return False
    except Exception as e:
        print(f"Hata: Genel bir hata oluştu. Detay: {e}", file=sys.stderr, flush=True)
        traceback.print_exc(file=sys.stderr)
        return False

def notify_overdue_step(db_cursor, step):
    """Süresi geçmiş bir iş adımı için e-posta bildirimi gönderir."""
    progress_id = step['progress_id']
    project_id = step['project_id']
    project_name = step['project_name']
    step_title = step['title']

    # Proje yöneticisi e-postasını bul
    db_cursor.execute("SELECT u.email FROM users u JOIN projects p ON u.id = p.project_manager_id WHERE p.project_id = %s", (project_id,))
    project_manager = db_cursor.fetchone()
    manager_email = project_manager['email'] if project_manager else None

    # Bildirim e-postası alıcı listesi
    recipients = []
    if manager_email:
        recipients.append(manager_email)
    recipients.extend(ADMIN_EMAIL_LIST)
    
    # Sadece benzersiz e-postaları al
    recipients = list(set(recipients))

    if not recipients:
        print(f"Uyarı: progress_id {progress_id} için e-posta alıcısı bulunamadı.")
        return False

    subject = f"ACİL: Proje Adımı Süresi Doldu: {project_name} - {step_title}"
    body = f"""
    <html>
        <body>
            <p>Merhaba,</p>
            <p>Aşağıdaki proje adımı için bitiş tarihi dolmuştur ve henüz tamamlanmamıştır:</p>
            <ul>
                <li><strong>Proje Adı:</strong> {project_name}</li>
                <li><strong>İş Adımı:</strong> {step_title}</li>
                <li><strong>Bitiş Tarihi:</strong> {step['end_date'].strftime('%Y-%m-%d')}</li>
            </ul>
            <p>Lütfen ilgili adımı en kısa sürede kontrol ediniz.</p>
            <p>Teşekkürler.</p>
        </body>
    </html>
    """
    
    return send_email(subject, body, recipients)

def main():
    """Ana fonksiyon - bitiş tarihi geçmiş veya bugünün tarihi olan adımları kontrol eder ve bildirim gönderir."""
    print(f"[{datetime.datetime.now()}] Zamanlanmış görev başlatıldı...")
        
    connection = get_db_connection()
    if not connection:
        return

    try:
        with connection.cursor() as cursor:
            # Bugünden önce veya bugünün tarihi olan adımları bul ve daha önce bildirim gönderilmemiş olanları filtrele.
            sql = """
                SELECT pp.progress_id, pp.end_date, pp.project_id, pp.title, p.project_name
                FROM project_progress pp
                JOIN projects p ON pp.project_id = p.project_id
                WHERE pp.end_date <= CURDATE()
                AND pp.completion_notified = 0
            """
            cursor.execute(sql)
            steps_to_notify = cursor.fetchall()
            
            notified_count = 0
            for step in steps_to_notify:
                if notify_overdue_step(cursor, step):
                    notified_count += 1
                    # Bildirim gönderildikten sonra `completion_notified` flag'ini güncelle
                    cursor.execute("UPDATE project_progress SET completion_notified = 1 WHERE progress_id = %s", (step['progress_id'],))
            
            connection.commit()
            print(f"[{datetime.datetime.now()}] Görev tamamlandı. {notified_count} adet tamamlanmamış iş adımı için bildirim gönderildi.")
            
            # --- TEST E-POSTASI GÖNDERİMİ ---
            print(f"[{datetime.datetime.now()}] Test e-postası gönderiliyor...")
            test_subject = "Cron Job Test E-postası"
            test_body = """
            <html>
                <body>
                    <p>Merhaba,</p>
                    <p>Bu, cron job'un e-posta gönderme ayarlarını kontrol etmek için gönderilmiş otomatik bir test e-postasıdır.</p>
                    <p>Bu e-postayı aldıysanız, ayarlarınız başarılı bir şekilde çalışıyor demektir.</p>
                    <p>İyi çalışmalar.</p>
                </body>
            </html>
            """
            # Buradaki e-posta adresini kendi test adresinizle değiştirmeyi unutmayın.
            test_recipients = ['mustafaozturkk1907@gmail.com']
            send_email(test_subject, test_body, test_recipients)
            print(f"[{datetime.datetime.now()}] Test e-postası gönderim işlemi tamamlandı.")

    except Exception as e:
        print(f"Zamanlanmış görevde bir hata oluştu: {e}", file=sys.stderr, flush=True)
        traceback.print_exc(file=sys.stderr)
    finally:
        if connection:
            connection.close()

if __name__ == "__main__":
    main()
