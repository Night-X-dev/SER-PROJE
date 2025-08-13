#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Bu betik, Cron job ile belirli aralıklarla çalışacak şekilde tasarlanmıştır.
# Tamamlanmış iş adımlarını bulur ve mail gönderir.

import os
import sys
import pymysql.cursors
from dotenv import load_dotenv
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import datetime
import traceback
import json

# .env dosyasını yükle
load_dotenv()

# Veritabanı ve E-posta ayarlarını .env dosyasından çek
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_NAME = os.getenv("DB_NAME")
DB_PORT = int(os.getenv("DB_PORT", 3306))

EMAIL_SENDER_ADDRESS = os.getenv("EMAIL_SENDER")
# Şifredeki boşlukları kaldır
EMAIL_SENDER_PASSWORD = os.getenv("EMAIL_PASSWORD", "").replace(" ", "")
EMAIL_SMTP_SERVER = os.getenv("SMTP_SERVER")
EMAIL_SMTP_PORT = int(os.getenv("SMTP_PORT", 587))

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

def get_admin_emails(db_cursor):
    """
    Veritabanından 'Admin' rolüne sahip kullanıcıların e-posta adreslerini çeker.
    """
    try:
        sql = "SELECT email FROM users WHERE role = 'Admin'"
        db_cursor.execute(sql)
        admin_emails = [row['email'] for row in db_cursor.fetchall()]
        return admin_emails
    except Exception as e:
        print(f"Hata: Admin e-posta adresleri veritabanından çekilemedi. Hata detayları: {e}", file=sys.stderr, flush=True)
        return []

def send_email(subject, body, recipient_emails):
    """
    Belirtilen alıcılara e-posta gönderir.
    """
    if not recipient_emails:
        print("Hata: E-posta alıcı listesi boş.", file=sys.stderr, flush=True)
        return False
    
    # E-posta içeriği
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = EMAIL_SENDER_ADDRESS
    message["To"] = ", ".join(recipient_emails)
    message.attach(MIMEText(body, "html"))

    try:
        with smtplib.SMTP(EMAIL_SMTP_SERVER, EMAIL_SMTP_PORT) as server:
            server.starttls(context=ssl.create_default_context())
            server.login(EMAIL_SENDER_ADDRESS, EMAIL_SENDER_PASSWORD)
            server.sendmail(EMAIL_SENDER_ADDRESS, recipient_emails, message.as_string())
        print(f"Başarılı: E-posta '{subject}' şu alıcılara gönderildi: {recipient_emails}", file=sys.stdout, flush=True)
        return True
    except smtplib.SMTPAuthenticationError as e:
        print(f"Hata: Kimlik doğrulama başarısız. Şifre (uygulama şifresi) veya kullanıcı adı yanlış olabilir. Hata: {e}", file=sys.stderr, flush=True)
        return False
    except smtplib.SMTPException as e:
        print(f"Hata: SMTP sunucusuna bağlanırken veya iletişimde sorun oluştu. Hata: {e}", file=sys.stderr, flush=True)
        return False
    except Exception as e:
        print(f"Hata: Genel bir hata oluştu. Detay: {e}", file=sys.stderr, flush=True)
        traceback.print_exc(file=sys.stderr)
        return False

def notify_completed_step(db_cursor, step, admin_emails):
    """Tamamlanmış bir iş adımı için e-posta bildirimi gönderir."""
    progress_id = step['progress_id']
    project_id = step['project_id']
    project_name = step['project_name']
    step_title = step['title']

    # Proje yöneticisinin e-posta adresini bulma
    db_cursor.execute("SELECT u.email FROM users u JOIN projects p ON u.id = p.project_manager_id WHERE p.project_id = %s", (project_id,))
    project_manager = db_cursor.fetchone()
    manager_email = project_manager['email'] if project_manager else None

    # E-posta alıcı listesini oluşturma
    recipients = []
    if manager_email:
        recipients.append(manager_email)
    recipients.extend(admin_emails)
    
    # Kopyaları kaldırarak son alıcı listesini oluşturma
    recipients = list(set(recipients))

    if not recipients:
        print(f"Uyarı: progress_id {progress_id} için e-posta alıcısı bulunamadı.", file=sys.stderr, flush=True)
        return False

    subject = f"Proje Adımı Tamamlandı: {project_name} - {step_title}"
    
    # Turkish month names
    turkish_months = {
        1: 'Ocak', 2: 'Şubat', 3: 'Mart', 4: 'Nisan', 5: 'Mayıs', 6: 'Haziran',
        7: 'Temmuz', 8: 'Ağustos', 9: 'Eylül', 10: 'Ekim', 11: 'Kasım', 12: 'Aralık'
    }
    
    day = step['end_date'].day
    month = turkish_months[step['end_date'].month]
    year = step['end_date'].year
    formatted_date = f"{day} {month} {year}"
    body = f"""
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Proje Adımı Tamamlandı | SER Elektrik</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f8f9fa;
            color: #333333;
            line-height: 1.6;
        }}
        
        .container {{
            max-width: 600px;
            margin: 20px auto;
            background-color: #ffffff;
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
        }}
        
        .header {{
            background: linear-gradient(135deg, #005c9d, #0980d3);
            padding: 30px 20px;
            text-align: center;
            color: white;
        }}
        
        .logo {{
            margin-bottom: 15px;
            text-align: center;
        }}
        
        .logo img {{
            height: 60px;
            max-width: 100%;
        }}
        
        .header h1 {{
            margin: 10px 0 5px;
            font-size: 28px;
            font-weight: 600;
        }}
        
        .header p {{
            margin: 0;
            opacity: 0.9;
            font-size: 18px;
        }}
        
        .content {{
            padding: 40px 30px;
        }}
        
        .title {{
            font-size: 24px;
            font-weight: 700;
            margin-bottom: 25px;
            text-align: center;
            color: #005c9d;
            margin-top: 0;
        }}
        
        .message {{
            margin-bottom: 30px;
            font-size: 16px;
            color: #5e6870;
            text-align: center;
        }}
        
        .project-card {{
            background: linear-gradient(135deg, #f0f4f8, #e1e5e9);
            border-radius: 12px;
            padding: 30px;
            margin: 30px 0;
            box-shadow: 0 4px 15px rgba(0, 92, 157, 0.08);
            border-left: 4px solid #0980d3;
        }}
        
        .detail-item {{
            display: flex;
            margin-bottom: 18px;
            padding-bottom: 18px;
            border-bottom: 1px solid rgba(0, 92, 157, 0.1);
        }}
        
        .detail-item:last-child {{
            border-bottom: none;
            margin-bottom: 0;
            padding-bottom: 0;
        }}
        
        .detail-label {{
            font-weight: 600;
            color: #005c9d;
            width: 140px;
            flex-shrink: 0;
        }}
        
        .detail-value {{
            color: #333333;
            font-weight: 500;
        }}
        
        .status-badge {{
            display: inline-block;
            background: #28a745;
            color: white;
            padding: 10px 20px;
            border-radius: 50px;
            font-weight: 600;
            font-size: 16px;
            margin-top: 15px;
            text-align: center;
            width: 100%;
            box-sizing: border-box;
        }}
        
        .signature {{
            margin-top: 30px;
            text-align: center;
            font-style: italic;
            color: #5e6870;
        }}
        
        .footer {{
            background-color: #f0f4f8;
            padding: 25px 20px;
            text-align: center;
            font-size: 14px;
            color: #97a1aa;
        }}
        
        .footer-links {{
            margin-bottom: 15px;
        }}
        
        .footer-links a {{
            color: #0980d3;
            text-decoration: none;
            margin: 0 10px;
            transition: all 0.3s;
        }}
        
        .footer-links a:hover {{
            color: #005c9d;
            text-decoration: underline;
        }}
        
        .contact {{
            margin-top: 15px;
            font-size: 13px;
        }}
        
        @media (max-width: 600px) {{
            .detail-item {{
                flex-direction: column;
            }}
            
            .detail-label {{
                width: 100%;
                margin-bottom: 5px;
            }}
            
            .content {{
                padding: 30px 20px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">
                <img src="https://serotomasyon.tr/static/serlogobeyaz.png" alt="SER Elektrik Otomasyon">
            </div>
            <h1>Proje Adımı Tamamlandı</h1>
            <p>Başarıyla tamamlanan proje aşaması hakkında bilgilendirme</p>
        </div>
        
        <div class="content">
            <h2 class="title">Proje Adımı Başarıyla Tamamlandı</h2>
            
            <p class="message">
                Merhaba,<br>
                Aşağıda belirtilen proje adımı başarıyla tamamlanmıştır. Detaylar aşağıda yer almaktadır.
            </p>
            
            <div class="project-card">
                <div class="detail-item">
                    <div class="detail-label">Proje Adı:</div>
                    <div class="detail-value">{project_name}</div>
                </div>
                
                <div class="detail-item">
                    <div class="detail-label">İş Adımı:</div>
                    <div class="detail-value">{step_title}</div>
                </div>
                
                <div class="detail-item">
                    <div class="detail-label">Bitiş Tarihi:</div>
                    <div class="detail-value">{formatted_date}</div>
                </div>
                
                <div class="status-badge">
                    ✔ BAŞARIYLA TAMAMLANDI
                </div>
            </div>
            
            <p class="signature">
                Bilgilerinize sunarız.<br>
                Teşekkür ederiz.
            </p>
        </div>
        
        <div class="footer">
            <div class="footer-links">
                <a href="https://www.serelektrik.com">Web Sitemiz</a>
            </div>
            
            <div>© 2025 SER Elektrik Otomasyon. Tüm hakları saklıdır.</div>
            
            <div class="contact">
                <div>Adres: Ser Plaza, Yeşilce, Dalgıç Sk. No:9, 34418 Kağıthane/İstanbul</div>
                <div>Telefon: (0212) 324 64 14 | E-posta: info@serelektrik.com</div>
            </div>
        </div>
    </div>
</body>
</html>
"""
    
    return send_email(subject, body, recipients)

def main():
    """Ana fonksiyon - tamamlanmış adımları kontrol eder ve bildirim gönderir."""
    print(f"[{datetime.datetime.now()}] Zamanlanmış görev başlatıldı...")
        
    connection = get_db_connection()
    if not connection:
        return

    try:
        with connection.cursor() as cursor:
            # Admin e-postalarını veritabanından çek
            admin_emails = get_admin_emails(cursor)

            # `is_complete` değeri 1 olan ve daha önce bildirim gönderilmemiş adımları bul.
            # `completion_notified` koşulu, aynı adım için tekrar tekrar e-posta gönderilmesini engeller.
            sql = """
                 SELECT pp.progress_id, pp.end_date, pp.project_id, pp.title, p.project_name
                FROM project_progress pp
                JOIN projects p ON pp.project_id = p.project_id
                WHERE pp.end_date <= CURDATE()
                AND pp.is_completed = 1
                AND pp.completion_notified = 0
            """
            cursor.execute(sql)
            steps_to_notify = cursor.fetchall()
            
            notified_count = 0
            for step in steps_to_notify:
                if notify_completed_step(cursor, step, admin_emails):
                    notified_count += 1
                    # Bildirim gönderildikten sonra `completion_notified` flag'ini güncelle
                    cursor.execute("UPDATE project_progress SET completion_notified = 1 WHERE progress_id = %s", (step['progress_id'],))
            
            connection.commit()
            print(f"[{datetime.datetime.now()}] Görev tamamlandı. {notified_count} adet tamamlanmış iş adımı için bildirim gönderildi.")

    except Exception as e:
        print(f"Zamanlanmış görevde bir hata oluştu: {e}", file=sys.stderr, flush=True)
        traceback.print_exc(file=sys.stderr)
    finally:
        if connection:
            connection.close()

if __name__ == "__main__":
    main()
