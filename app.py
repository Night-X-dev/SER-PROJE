# app.py
from flask import Flask, logging, request, jsonify, render_template, session, redirect, url_for
from datetime import datetime
from flask_cors import CORS
import pymysql.cursors
import bcrypt
import os
import json
import datetime
import dotenv
from dotenv import load_dotenv
import urllib.parse
import re
import traceback # Import traceback for detailed error logging

# E-posta göndermek için gerekli kütüphaneler
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import threading
import time
load_dotenv()

app = Flask(__name__)
# Session management secret key
# THIS SHOULD BE A SECURE AND UNPREDICTABLE STRING!
app.secret_key = os.getenv("SECRET_KEY", "supersecretkeythatshouldbemorecomplex")

PRIORITY_TRANSLATIONS = {
    "low": "Düşük Öncelik",
    "medium": "Orta Öncelik",
    "high": "Yüksek Öncelik"
}
CORS(app, resources={r"/*": {"origins": ["https://37.148.213.89:8000", "http://serotomasyon.tr"]}}, supports_credentials=True)
@app.route('/')
def serve_welcome_page():
    """Directs root URL (/) requests to the welcome.html page."""
    return render_template('welcome.html')

@app.route('/login.html')
def serve_login_page():
    """Directs /login.html requests to the login.html page."""
    return render_template('login.html')
# Yeni rota: sifremi_unuttum.html sayfasını sunar
@app.route('/sifremi_unuttum.html')
def serve_forgot_password_page():
    """Directs /sifremi_unuttum.html requests to the sifremi_unuttum.html page."""
    return render_template('sifremi_unuttum.html')
@app.route('/ayarlar')
def ayarlar_page():
    """Renders the settings page."""
    return render_template('ayarlar.html')
@app.route('/logout')
def logout():
    """
    Clears the user session and redirects to welcome.html page.
    """
    session.clear()
    return redirect(url_for('serve_welcome_page'))

@app.route('/index.html')
def serve_index_page():
    """Directs /index.html requests to the index.html page."""
    return render_template('index.html')

@app.route('/ayarlar.html')
def serve_ayarlar_page():
    """Directs /ayarlar.html requests to the ayarlar.html page.
    All logged-in users can access, but content will be hidden on the frontend based on role."""
    if 'user_id' not in session:
        return redirect(url_for('serve_login_page'))
    # Allow all logged-in users to access the settings page
    return render_template('ayarlar.html')

@app.route('/kablo_hesap.html')
def serve_kablo_hesap_page():
    """Directs /kablo_hesap.html requests to the kablo_hesap.html page.
    This page is now accessible without a login, based on user request."""
    return render_template('kablo_hesap.html')

@app.route('/kayitonay.html')
def serve_kayitonay_page():
    """Directs /kayitonay.html requests to the kayitonay.html page."""
    return render_template('kayitonay.html')

@app.route('/musteriler.html')
def serve_musteriler_page():
    """Directs /musteriler.html requests to the musteriler.html page."""
    return render_template('musteriler.html')

@app.route('/proje_ekle.html')
def serve_proje_ekle_page():
    """Directs /proje_ekle.html requests to the proje_ekle.html page."""
    if 'user_id' not in session:
        return redirect(url_for('serve_login_page'))
    return render_template('proje_ekle.html')

@app.route('/projeler.html')
def serve_projeler_page():
    """Directs /projeler.html requests to the projeler.html page."""
    return render_template('projeler.html')

@app.route('/raporlar.html')
def serve_raporlar_page():
    """Directs /raporlar.html requests to the raporlar.html page.
    Checks if the user is logged in and has permission to access reports."""
    # Check if the user is logged in
    if 'user_id' not in session:
        return redirect(url_for('serve_login_page')) # Redirect to login page if not logged in

    user_id = session['user_id']
    user_role = get_user_role_from_db(user_id) # Get user role from the database

    if user_role:
        # Check if the role has report permission
        has_permission = check_role_permission(user_role, 'raporlar')
        if has_permission:
            return render_template('raporlar.html')
        else:
            # If no permission, redirect to the home page
            return redirect(url_for('serve_index_page'))
    else:
        # If user role is not found, redirect to the login page
        return redirect(url_for('serve_login_page'))

@app.route('/takvim.html')
def serve_takvim_page():
    """Directs /takvim.html requests to the takvim.html page."""
    return render_template('takvim.html')

@app.route('/users.html')
def serve_users_page():
    """Directs /users.html requests to the users.html page.
    Requires the user to be logged in."""
    if 'user_id' not in session:
        return redirect(url_for('serve_login_page'))
    return render_template('users.html')

@app.route('/waiting.html')
def serve_waiting_page():
    """Directs /waiting.html requests to the waiting.html page."""
    return render_template('waiting.html')

@app.route('/yeni_musteri.html')
def serve_yeni_musteri_page():
    """Directs /yeni_musteri.html requests to the yeni_musteri.html page."""
    return render_template('yeni_musteri.html')

@app.route('/bildirim.html')
def serve_bildirim_page():
    """Directs /bildirim.html requests to the bildirim.html page."""
    return render_template('bildirim.html')
# CORS (Cross-Origin Resource Sharing) settings
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

def get_db_connection():
    """Establishes and returns a database connection."""
    connection = None
    try:
        # MYSQL_PUBLIC_URL ortam değişkenini kontrol et
        public_url = os.getenv("MYSQL_PUBLIC_URL")
        host = None
        port = None
        user = None
        password = None
        database = None

        if public_url:
            try:
                # Eğer public URL varsa, onu ayrıştır
                parsed_url = urllib.parse.urlparse(public_url)
                host = parsed_url.hostname
                port = parsed_url.port if parsed_url.port else 3306
                user = parsed_url.username
                password = parsed_url.password
                database = parsed_url.path.lstrip('/')
                print(f"DEBUG: Parsed public URL used. Host={host}, Port={port}, User={user}, DB={database}")
            except Exception as url_parse_e:
                print(f"ERROR: Could not parse MYSQL_PUBLIC_URL: {url_parse_e}. Falling back to individual environment variables.")

        # Eğer public_url kullanılmadıysa veya ayrıştırma başarısız olduysa,
        # ayrı ayrı ortam değişkenlerini kullanmayı dene
        if not host: # Eğer host hala None ise (yani public_url başarılı olmadıysa)
            host = os.getenv("MYSQL_HOST")
            port = int(os.getenv("MYSQL_PORT", 3306)) # Port için varsayılan değer tutulabilir
            user = os.getenv("MYSQL_USER")
            password = os.getenv("MYSQL_PASSWORD")
            database = os.getenv("MYSQL_DATABASE")
            print(f"DEBUG: Individual environment variables used. Host={host}, Port={port}, User={user}, DB={database}")

        # Gerekli tüm bağlantı bilgilerinin ayarlandığından emin ol
        if not all([host, user, password, database]):
            raise ValueError(
                "Veritabanı bağlantı bilgileri (.env dosyasında veya ortam değişkenlerinde) eksik. "
                "Lütfen MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE değişkenlerini ayarlayın."
            )

        connection = pymysql.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            port=port,
            cursorclass=pymysql.cursors.DictCursor
        )
        print("Successfully connected to MySQL database!")
        return connection
    except pymysql.Error as e:
        print(f"MySQL connection error: {e}")
        if connection:
            connection.close()
        raise # Hatanın yukarıya iletilmesini sağla
    except ValueError as e: # Özel ValueError'ı yakala
        print(f"Configuration error: {e}")
        raise # Hatanın yukarıya iletilmesini sağla
    except Exception as e:
        print(f"General connection error: {e}")
        if connection:
            connection.close()
        raise # Hatanın yukarıya iletilmesini sağla
from auth import handle_forgot_password, handle_verify_code, handle_reset_password
@app.route('/forgot-password', methods=['POST'])
def forgot_password_route():
     return handle_forgot_password()

@app.route('/verify-code', methods=['POST'])
def verify_code_route():
     return handle_verify_code()

@app.route('/reset-password', methods=['POST'])
def reset_password_route():
     return handle_reset_password()
def format_datetime_for_email(dt_str):
    """
    Tarih/saat stringini e-posta için daha okunaklı bir formata dönüştürür.
    'YYYY-MM-DDTHH:MM' veya 'YYYY-MM-DD' formatlarını destekler.
    """
    if not dt_str:
        return "Belirtilmemiş"
    try:
        if 'T' in dt_str:
            # Hem tarih hem saat içeren format
            dt_obj = datetime.datetime.fromisoformat(dt_str)
            return dt_obj.strftime('%d.%m.%Y %H:%M')
        else:
            # Sadece tarih içeren format
            dt_obj = datetime.datetime.strptime(dt_str, '%Y-%m-%d').date()
            return dt_obj.strftime('%d.%m.%Y')
    except ValueError:
        return dt_str # Ayrıştırma başarısız olursa orijinal stringi döndür

@app.route('/api/update_user_profile', methods=['POST'])
def update_user_profile():
    if 'user_id' not in session:
        return jsonify({"error": "Oturum bulunamadı"}), 401

    data = request.get_json()
    user_id = session.get('user_id')
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # Check if user exists
                cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
                if not cursor.fetchone():
                    return jsonify({"error": "Kullanıcı bulunamadı"}), 404
                
                # Build update query based on provided fields
                update_fields = []
                update_values = []
                
                if 'fullname' in data:
                    update_fields.append("fullname = %s")
                    update_values.append(data['fullname'])
                
                if 'email' in data:
                    cursor.execute("SELECT id FROM users WHERE email = %s AND id != %s", 
                                 (data['email'], user_id))
                    if cursor.fetchone():
                        return jsonify({"error": "Bu e-posta adresi zaten kullanılıyor"}), 400
                    update_fields.append("email = %s")
                    update_values.append(data['email'])
                
                # Handle password change if provided
                if 'currentPassword' in data and 'newPassword' in data:
                    cursor.execute("SELECT password FROM users WHERE id = %s", (user_id,))
                    user = cursor.fetchone()
                    if not user or not check_password_hash(user['password'], data['currentPassword']):
                        return jsonify({"error": "Mevcut şifre yanlış"}), 400
                    
                    hashed_password = generate_password_hash(data['newPassword'])
                    update_fields.append("password = %s")
                    update_values.append(hashed_password)
                
                if not update_fields:
                    return jsonify({"error": "Güncellenecek alan bulunamadı"}), 400
                
                # Execute update
                update_query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = %s"
                update_values.append(user_id)
                cursor.execute(update_query, tuple(update_values))
                conn.commit()
                
                # Update session if email was changed
                if 'email' in data:
                    session['email'] = data['email']
                
                return jsonify({"message": "Profil başarıyla güncellendi"}), 200
                
    except Exception as e:
        print(f"Error updating user profile: {str(e)}")
        return jsonify({"error": "Profil güncelleme sırasında bir hata oluştu"}), 500
@app.route('/api/project-report/<int:project_id>', methods=['GET'])
def get_project_report_data(project_id):
    """
    Belirtilen proje ID'sine göre detaylı rapor verilerini getirir.
    Bu, Proje detay sayfasında ve PDF raporunda kullanılır.
    """
    connection = get_db_connection()
    if connection is None:
        return jsonify({"error": "Veritabanı bağlantısı kurulamadı."}), 500

    try:
        with connection.cursor() as cursor:
            # 1. Proje detaylarını çek
            sql_project = "SELECT project_id, title, description, start_date, end_date, budget, status FROM projects WHERE project_id = %s"
            cursor.execute(sql_project, (project_id,))
            project_data = cursor.fetchone()

            if not project_data:
                return jsonify({"error": "Proje bulunamadı."}), 404

            # 2. Proje ilerleme adımlarını çek
            sql_progress = """
            SELECT
                progress_id,
                title AS step_name,
                description,
                start_date,
                end_date,
                delay_days,
                custom_delay_days,
                real_end_date,
                completion_notified
            FROM project_progress
            WHERE project_id = %s
            ORDER BY start_date ASC, created_at ASC
            """
            cursor.execute(sql_progress, (project_id,))
            progress_steps = cursor.fetchall()

            total_project_delay_days = 0
            completed_steps_count = 0
            today = datetime.date.today()

            last_end_date = None # Önceki iş gidişatının bitiş tarihini tutmak için yeni eklenen değişken

            # Her bir iş gidişatını döngüye al
            for i, step in enumerate(progress_steps):
                # Önceki adımın bitiş tarihi ile mevcut adımın başlangıç tarihi arasındaki gecikmeyi hesapla
                step_delay_days = 0
                step_custom_delay_days = step['custom_delay_days'] or 0

                step_start_date_obj = datetime.date.fromisoformat(str(step['start_date'])) if step['start_date'] else None
                
                # Sadece ilk adım değilse ve bir önceki adımın bitiş tarihi varsa gecikme hesapla
                if i > 0 and last_end_date and step_start_date_obj:
                    time_difference = step_start_date_obj - last_end_date
                    # Fark 1 günden büyükse gecikme oluşmuştur (Örnek: 14'ünde bitip, 16'sında başlıyorsa 1 gün gecikme var)
                    if time_difference.days > 1:
                        step_delay_days = time_difference.days - 1
                        
                # Proje gecikme günü ve ertelenen günü (custom_delay_days) topla
                step['delay_days'] = step_delay_days # Dinamik olarak hesaplanan değeri ata
                step_total_delay = step_delay_days + step_custom_delay_days
                total_project_delay_days += step_total_delay

                # Tarihleri ISO formatına çevir (Frontend tarafı için)
                for key in ['start_date', 'end_date', 'real_end_date']:
                    if key in step and isinstance(step[key], datetime.date):
                        step[key] = step[key].isoformat()
                    else:
                        step[key] = None

                # Durum belirleme mantığı güncellendi
                step_end_date_obj = datetime.date.fromisoformat(str(step['end_date'])) if step['end_date'] else None
                step_real_end_date_obj = datetime.date.fromisoformat(str(step['real_end_date'])) if step['real_end_date'] else None

                if step_real_end_date_obj:
                    # Adım tamamlandıysa
                    if step_real_end_date_obj <= step_end_date_obj:
                        step['status'] = 'Tamamlandı'
                    elif step_real_end_date_obj > step_end_date_obj and step_custom_delay_days > 0:
                        step['status'] = 'Ertelenmiş Bitti'
                    elif step_real_end_date_obj > step_end_date_obj and step_delay_days > 0:
                        step['status'] = 'Gecikmeli Bitti'
                    else:
                        step['status'] = 'Tamamlandı'
                # Adım henüz tamamlanmadıysa
                elif step_start_date_obj and today < step_start_date_obj:
                    step['status'] = 'Başlamadı'
                elif step_end_date_obj and today > step_end_date_obj and step_custom_delay_days > 0:
                    step['status'] = 'Ertelenmiş'
                elif step_end_date_obj and today > step_end_date_obj and step_delay_days > 0:
                    step['status'] = 'Gecikmeli'
                else:
                    step['status'] = 'Aktif'
                
                if step['status'] in ['Tamamlandı', 'Gecikmeli Bitti', 'Ertelenmiş Bitti']:
                    completed_steps_count += 1
                
                # Sonraki döngü için bitiş tarihini güncelle
                last_end_date = datetime.date.fromisoformat(str(step['end_date'])) if step['end_date'] else None

            # 3. Genel Tamamlanma Yüzdesini Hesapla
            total_steps = len(progress_steps)
            completion_percentage = 0
            if total_steps > 0:
                completion_percentage = round((completed_steps_count / total_steps) * 100)

            if project_data['status'] == 'Tamamlandı':
                completion_percentage = 100

            # 4. Final rapor verilerini hazırla
            report_data = {
                'project': project_data,
                'progress_steps': progress_steps,
                'total_project_delay_days': total_project_delay_days,
                'completion_percentage': completion_percentage,
                'completed_steps_count': completed_steps_count
            }

            return jsonify(report_data), 200

    except Exception as e:
        app.logger.error(f"Proje rapor verisi çekme hatası: {e}")
        traceback.print_exc()
        return jsonify({"error": "Proje rapor verisi çekilirken bir hata oluştu."}), 500
    finally:
        connection.close()


# Helper function: Gets user role from the database
def get_user_role_from_db(user_id):
    """Retrieves the role of a user from the database."""
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT role FROM users WHERE id = %s", (user_id,))
            result = cursor.fetchone()
            return result['role'] if result else None
    except Exception as e:
        print(f"Error fetching user role: {e}")
        return None
    finally:
        if connection:
            connection.close()

def check_role_permission(role_name, permission_key):
    """Checks if a specific role has a specific permission."""
    # Admin role is always considered to have all permissions
    if role_name.lower() == 'admin':
        return True

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Query the relevant permission column in the 'yetki' table
            sql = f"SELECT {permission_key} FROM yetki WHERE LOWER(role_name) = %s"
            cursor.execute(sql, (role_name.lower(),))
            result = cursor.fetchone()

            # If no permission record for the role or permission value is 0, return False
            if result and result[permission_key] == 1:
                return True
            return False
    except Exception as e:
        print(f"Error during permission check: {e}")
        return False
    finally:
        if connection:
            connection.close()


# API to mark all notifications as read (for notifications table)
@app.route('/api/notifications/mark_all_read', methods=['PUT'])
def mark_all_notifications_as_read():
    """Marks all notifications in the database as read."""
    data = request.get_json() # Use get_json() for PUT requests
    user_id = data.get('user_id') # Get user_id from the request body
    if not user_id:
        return jsonify({'message': 'User ID is missing.'}), 400

    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = "UPDATE notifications SET is_read = 1 WHERE user_id = %s AND is_read = 0"
            cursor.execute(sql, (user_id,))
            connection.commit()
            rows_affected = cursor.rowcount
        return jsonify({'message': f'{rows_affected} notifications marked as read.'}), 200
    except pymysql.Error as e:
        print(f"Database error while updating all notifications: {e}")
        return jsonify({'message': f'Database error occurred: {e.args[1]}'}), 500
    except Exception as e:
        print(f"General error while updating all notifications: {e}")
        return jsonify({'message': 'Server error, please try again later.'}), 500
    finally:
        if connection:
            connection.close()

# API for unread notification count (for notifications table)
# API for unread notification count (for notifications table)
@app.route('/api/notifications/unread-count', methods=['GET'])
def get_unread_notifications_count():
    """Returns the count of unread notifications in the database."""
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'unread_count': 0, 'message': 'User ID is missing.'}), 400

    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = "SELECT COUNT(id) as unread_count FROM notifications WHERE user_id = %s AND is_read = 0"
            cursor.execute(sql, (user_id,))
            result = cursor.fetchone()
            return jsonify(result), 200
    except pymysql.Error as e:
        print(f"Database error while fetching unread notification count: {e}")
        return jsonify({'message': f'Database error occurred: {e.args[1]}'}), 500
    except Exception as e:
        print(f"General error while fetching unread notification count: {e}")
        return jsonify({'message': 'Server error, please try again later.'}), 500
    finally:
        if connection:
            connection.close()


# API to mark notification as read (for notifications table)
@app.route('/api/notifications/<int:notification_id>/read', methods=['PUT'])
def mark_notification_as_read(notification_id):
    """Marks a specific notification as read in the database."""
    data = request.get_json()
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({'message': 'User ID is missing.'}), 400
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM notifications WHERE id = %s AND user_id = %s", (notification_id, user_id))
            if not cursor.fetchone():
                return jsonify({'message': 'Notification not found or you do not have permission to modify it.'}), 404
            sql = "UPDATE notifications SET is_read = 1 WHERE id = %s"
            cursor.execute(sql, (notification_id,))
            connection.commit()
            return jsonify({'message': 'Notification successfully marked as read!'}), 200
    except pymysql.Error as e:
        print(f"Database error while updating notification: {e}")
        return jsonify({'message': f'Database error occurred: {e.args[1]}'}), 500
    except Exception as e:
        print(f"General error while updating notification: {e}")
        return jsonify({'message': 'Server error, please try again later.'}), 500
    finally:
        if connection:
            connection.close()
def determine_and_update_project_status(cursor, project_id):
    """
    Determines and updates the project's 'status' column in the database based on its progress steps and dates.
    This function expects an active cursor and does not manage connection.
    """
    try:
        # Mevcut proje bilgilerini çek
        cursor.execute("SELECT start_date, end_date, status FROM projects WHERE project_id = %s", (project_id,))
        project_info = cursor.fetchone()
        if not project_info:
            print(f"Project {project_id} not found for status update.")
            return False

        project_start_date = project_info['start_date']
        project_end_date = project_info['end_date']
        current_db_status = project_info['status']

        # Eğer proje açıkça 'Tamamlandı' olarak işaretlendiyse, bu durumu koru.
        if current_db_status == 'Tamamlandı':
            print(f"Project {project_id} is already 'Tamamlandı', no auto-update needed.")
            return True

        today = datetime.date.today()
        new_status = 'Aktif'  # Varsayılan durum

        # Projenin tüm iş adımlarını çek
        cursor.execute("""
            SELECT start_date, end_date, delay_days, custom_delay_days
            FROM project_progress
            WHERE project_id = %s
            ORDER BY start_date ASC
        """, (project_id,))
        progress_steps = cursor.fetchall()
        total_project_delay_days = 0
        for step in progress_steps:
            total_project_delay_days += (step['delay_days'] or 0) + (step['custom_delay_days'] or 0)

        # 1. 'Gecikmeli' durumu kontrolü
        if total_project_delay_days > 0:
            new_status = 'Gecikmeli'
        
        # 2. 'Planlandı' durumu kontrolü
        elif project_start_date and today < project_start_date:
            new_status = 'Planlandı'

        # 3. 'Tamamlandı' durumu kontrolü
        # Tüm iş adımları tamamlanmış mı kontrol et
        all_steps_completed = True
        for step in progress_steps:
            if not step['real_end_date']: # Gerçek bitiş tarihi yoksa tamamlanmamıştır
                all_steps_completed = False
                break
        
        if all_steps_completed:
            new_status = 'Tamamlandı'
        
        # 4. Durum güncellemesi
        if current_db_status != new_status:
            cursor.execute("UPDATE projects SET status = %s WHERE project_id = %s", (new_status, project_id))
            print(f"Project {project_id} status updated from '{current_db_status}' to '{new_status}'.")
            return True
        return False
    except Exception as e:
        print(f"Error determining and updating project status: {e}")
        traceback.print_exc()
        return False
# API to get notifications (for notifications table)
@app.route('/api/notifications', methods=['GET'])
def get_notifications():
    """Retrieves notifications for a specific user."""
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'message': 'User ID is missing.'}), 400

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            sql = "SELECT id, user_id, title, message, is_read, created_at FROM notifications WHERE user_id = %s ORDER BY created_at DESC"
            cursor.execute(sql, (user_id,))
            result = cursor.fetchall()
            for row in result:
                if 'is_read' in row:
                    try:
                        row['is_read'] = int(row['is_read'])
                    except Exception:
                        row['is_read'] = 0
                # Convert created_at to ISO format
                if 'created_at' in row and isinstance(row['created_at'], datetime.datetime):
                    row['created_at'] = row['created_at'].isoformat()
            return jsonify(result)
    except pymysql.Error as e:
        print(f"Database error while fetching notifications: {e}")
        return jsonify({'message': f'Database error occurred: {e.args[1]}'}), 500
    except Exception as e:
        print(f"General error while fetching notifications: {e}")
        return jsonify({'message': 'Server error, please try again later.'}), 500
    finally:
        if connection:
            connection.close()

@app.route('/api/notifications/<int:notification_id>', methods=['DELETE'])
def delete_notification(notification_id):
    """Deletes a specific notification for the logged-in user."""
    data = request.get_json()
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({'message': 'User ID is missing.'}), 400

    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM notifications WHERE id = %s AND user_id = %s", (notification_id, user_id))
            if not cursor.fetchone():
                return jsonify({'message': 'Notification not found or you do not have permission to modify it.'}), 404

            cursor.execute("DELETE FROM notifications WHERE id = %s", (notification_id,))
            connection.commit()
            return jsonify({'message': 'Notification deleted.'}), 200
    except Exception as e:
        print(f"Notification deletion error: {e}")
        return jsonify({'message': 'Server error'}), 500
    finally:
        connection.close()

@app.route('/api/notifications/all', methods=['DELETE'])
def delete_all_notifications():
    """Deletes all notifications for the logged-in user."""
    data = request.get_json()
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({'message': 'User ID is missing.'}), 400

    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM notifications WHERE user_id = %s", (user_id,))
            connection.commit()
            return jsonify({'message': 'All your notifications have been deleted.'})
    except Exception as e:
        if connection:
            connection.rollback()
        return jsonify({'message': f'Error: {str(e)}'}), 500
    finally:
        connection.close()

# Yeni API rotası: Rol ekleme
@app.route('/api/add-role', methods=['POST'])
def add_role():
    
    if 'user_id' not in session:
        return jsonify({"error": "Oturum açık değil."}), 401

    data = request.get_json()
    role_name = data.get('role_name')

    if not role_name:
        return jsonify({"error": "Rol adı boş bırakılamaz."}), 400

    connection = get_db_connection()
    if not connection:
        return jsonify({"error": "Veritabanı bağlantısı kurulamadı."}), 500

    try:
        with connection.cursor() as cursor:
            # Rolün zaten var olup olmadığını kontrol et
            sql_check = "SELECT id FROM yetki WHERE role_name = %s"
            cursor.execute(sql_check, (role_name,))
            if cursor.fetchone():
                return jsonify({"error": "Bu isimde bir rol zaten mevcut."}), 409

            # Yeni rolü ekle
            sql_insert = "INSERT INTO yetki (role_name) VALUES (%s)"
            cursor.execute(sql_insert, (role_name,))
            connection.commit()

            return jsonify({"message": f"'{role_name}' rolü başarıyla eklendi."}), 201

    except pymysql.Error as e:
        print(f"MySQL error: {e}")
        return jsonify({"error": "Veritabanı hatası oluştu."}), 500
    finally:
        connection.close()

# is_admin fonksiyonu (eğer yoksa ekleyin)
def is_admin(user_id):
    """
    Verilen user_id'nin admin rolüne sahip olup olmadığını kontrol eder.
    """
    connection = get_db_connection()
    if not connection:
        return False
    try:
        with connection.cursor() as cursor:
            sql = """
                SELECT r.role_name
                FROM users u
                JOIN roles r ON u.role_id = r.role_id
                WHERE u.user_id = %s
            """
            cursor.execute(sql, (user_id,))
            result = cursor.fetchone()
            if result and result['role_name'] == 'Admin':
                return True
            return False
    except pymysql.Error as e:
        print(f"MySQL error in is_admin: {e}")
        return False
    finally:
        connection.close()

# API to add new notification (for notifications table)
@app.route('/api/notifications', methods=['POST'])
def add_notification():
    """Adds a new notification to the database."""
    data = request.get_json()
    user_id = data.get('user_id')
    title = data.get('title')
    message = data.get('message')

    if not all([user_id, title, message]):
        return jsonify({'message': 'User ID, title, and message are required.'}), 400

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            sql = """
            INSERT INTO notifications (user_id, title, message, created_at)
            VALUES (%s, %s, %s, NOW())
            """
            cursor.execute(sql, (user_id, title, message))
            connection.commit()
        return jsonify({'message': 'Notification successfully saved!'}), 201
    except pymysql.Error as e:
        print(f"Database error while saving notification: {e}")
        if e.args[0] == 1062:
            return jsonify({'message': 'This email address is already in use.'}), 409
        return jsonify({'message': f'Database error occurred: {e.args[1]}'}), 500
    except Exception as e:
        print(f"General error while saving notification: {e}")
        return jsonify({'message': 'Server error, please try again later.'}), 500
    finally:
        if connection:
            connection.close()

# API to add new activity (for activities table)
@app.route('/api/activities', methods=['POST'])
def add_activity():
    """Adds a new activity to the database."""
    data = request.get_json()
    user_id = data.get('user_id')
    title = data.get('title')
    description = data.get('description')
    icon = data.get('icon', 'fas fa-info-circle')

    if not all([user_id, title, description]):
        return jsonify({'message': 'User ID, title, and description are required.'}), 400

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            sql = """
            INSERT INTO activities (user_id, title, description, icon, created_at)
            VALUES (%s, %s, %s, %s, NOW())
            """
            cursor.execute(sql, (user_id, title, description, icon))
            connection.commit()
        return jsonify({'message': 'Activity successfully saved!'}), 201
    except pymysql.Error as e:
        print(f"Database error while saving activity: {e}")
        return jsonify({'message': f'Database error occurred: {e.args[1]}'}), 500
    except Exception as e:
        print(f"General error while saving activity: {e}")
        return jsonify({'message': 'Server error, please try again later.'}), 500
    finally:
        if connection:
            connection.close()


@app.route('/api/pending-users', methods=['GET'])
def get_pending_users():
    """Retrieves users with 'onay' status 0."""
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            sql = "SELECT id, fullname, email, phone, role, created_at FROM users WHERE onay = 0"
            cursor.execute(sql)
            pending_users = cursor.fetchall()
            return jsonify(pending_users), 200
    except pymysql.Error as e:
        print(f"Database error while fetching pending users: {e}")
        return jsonify({'message': f'Database error occurred: {e.args[1]}'}), 500
    except Exception as e:
        print(f"General error while fetching pending users: {e}")
        return jsonify({'message': 'Server error, please try again later.'}), 500
    finally:
        if connection:
            connection.close()

@app.route('/api/users/approve/<int:user_id>', methods=['PATCH'])
def approve_user(user_id):
    """Approves a user by setting their 'onay' status to 1 and updating their role."""
    connection = None
    try:
        # Get the selected role from the request headers
        selected_role = request.headers.get('X-Selected-Role')
        if not selected_role:
            return jsonify({'message': 'Rol seçimi bulunamadı.'}), 400

        connection = get_db_connection()
        with connection.cursor() as cursor:
            # First, verify the user exists and is pending approval
            cursor.execute("SELECT id, onay FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()

            if not user:
                return jsonify({'message': 'Kullanıcı bulunamadı.'}), 404
            if user['onay'] == 1:
                return jsonify({'message': 'Bu kullanıcı zaten onaylanmış.'}), 400

            # Update the user's status and role
            sql = "UPDATE users SET onay = 1, role = %s WHERE id = %s"
            cursor.execute(sql, (selected_role, user_id))
            connection.commit()

            return jsonify({'message': 'Kullanıcı başarıyla onaylandı ve rolü güncellendi.'}), 200

    except pymysql.Error as e:
        print(f"Veritabanı hatası: {e}")
        return jsonify({'message': f'Veritabanı hatası: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel hata: {e}")
        return jsonify({'message': 'Sunucu hatası, lütfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Deletes a user and reassigns or deletes their associated projects and tasks."""
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, fullname FROM users WHERE id = %s", (user_id,))
            user_info = cursor.fetchone()
            if not user_info:
                return jsonify({'message': 'User not found.'}), 404

            if user_info['id'] == 1:
                 return jsonify({'message': 'This user cannot be deleted.'}), 403

            default_manager_id = None
            cursor.execute("SELECT id FROM users WHERE role = 'Admin' AND id != %s LIMIT 1", (user_id,))
            admin_user = cursor.fetchone()
            if admin_user:
                default_manager_id = admin_user['id']
            else:
                cursor.execute("SELECT id FROM users WHERE id != %s LIMIT 1", (user_id,))
                other_user = cursor.fetchone()
                if other_user:
                    default_manager_id = other_user['id']

            if default_manager_id:
                cursor.execute(
                    "UPDATE projects SET project_manager_id = %s WHERE project_manager_id = %s",
                    (default_manager_id, user_id)
                )
                print(f"DEBUG: {cursor.rowcount} projects reassigned from user {user_id} to {default_manager_id}.")
            else:
                cursor.execute("DELETE FROM projects WHERE project_manager_id = %s", (user_id,))
                print(f"DEBUG: {cursor.rowcount} projects deleted for user {user_id} (no manager to reassign to).")

            cursor.execute("DELETE FROM tasks WHERE assigned_user_id = %s", (user_id,))
            print(f"DEBUG: {cursor.rowcount} tasks deleted for user {user_id}.")

            sql = "DELETE FROM users WHERE id = %s"
            cursor.execute(sql, (user_id,))
            connection.commit()
            print(f"DEBUG: User {user_id} deleted.")

        return jsonify({'message': 'User successfully deleted!'}), 200

    except pymysql.Error as e:
        print(f"Database error while deleting user: {e}")
        return jsonify({'message': f'Database error occurred: {e.args[1]}'}), 500
    except Exception as e:
        print(f"General error while deleting user: {e}")
        return jsonify({'message': 'Server error, please try again later.'}), 500
    finally:
        if connection:
            connection.close()

TURKEY_LOCATIONS = {}
try:
    script_dir = os.path.dirname(__file__)
    file_path = os.path.join(script_dir, 'turkey_locations.json')
    with open(file_path, 'r', encoding='utf-8') as f:
        TURKEY_LOCATIONS = json.load(f)
    print("Location data successfully loaded.")
except FileNotFoundError:
    print(f"Error: 'turkey_locations.json' file not found. Please check the path '{file_path}'.")
    TURKEY_LOCATIONS = {"Türkiye": {"iller": {"Varsayılan İl": []}}}
except json.JSONDecodeError:
    print("Error: 'turkey_locations.json' file is not in JSON format or corrupted.")
    TURKEY_LOCATIONS = {"Türkiye": {"iller": {"Varsayılan İl": []}}}
except Exception as e:
    print(f"Unexpected error while loading location data: {e}")
    TURKEY_LOCATIONS = {"Türkiye": {"iller": {"Varsayılan İl": []}}}


@app.route('/api/role-permissions', methods=['GET'])
def get_permissions_by_role():
    """Retrieves permissions for a specific role."""
    role_name = request.args.get('role')
    if not role_name:
        return jsonify({'message': 'Role name is required'}), 400

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            sql = "SELECT proje_ekle, proje_duzenle, proje_sil, pdf_olusturma, musteri_duzenleme, raporlar FROM yetki WHERE LOWER(role_name) = %s"
            cursor.execute(sql, (role_name.lower(),))
            result = cursor.fetchone()
            if not result:
                # If no permission record for the role, return all permissions as 0 by default
                return jsonify({
                    'proje_ekle': 0,
                    'proje_duzenle': 0,
                    'proje_sil': 0,
                    'pdf_olusturma': 0,
                    'musteri_duzenleme': 0,
                    'raporlar': 0
                }), 200
            return jsonify(result), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500
    finally:
        if connection:
            connection.close()

@app.route('/api/role-permissions', methods=['POST'])
def update_role_permissions():
    """Updates permissions for a specific role."""
    data = request.json
    role = data.get('role')
    if not role:
        return jsonify({'message': 'Role not specified.'}), 400

    proje_ekle = data.get('proje_ekle', 0)
    proje_duzenle = data.get('proje_duzenle', 0)
    proje_sil = data.get('proje_sil', 0)
    pdf_olusturma = data.get('pdf_olusturma', 0)
    musteri_duzenleme = data.get('musteri_duzenleme', 0)
    raporlar = data.get('raporlar', 0)

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM yetki WHERE LOWER(role_name) = %s", (role.lower(),))
            exists = cursor.fetchone()['COUNT(*)']

            if exists:
                sql = """
                    UPDATE yetki
                    SET proje_ekle=%s, proje_duzenle=%s, proje_sil=%s, pdf_olusturma=%s, musteri_duzenleme=%s, raporlar=%s
                    WHERE LOWER(role_name)=%s
                """
                cursor.execute(sql, (proje_ekle, proje_duzenle, proje_sil, pdf_olusturma, musteri_duzenleme, raporlar, role.lower()))
            else:
                sql = """
                    INSERT INTO yetki (role_name, proje_ekle, proje_duzenle, proje_sil, pdf_olusturma, musteri_duzenleme, raporlar)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(sql, (role, proje_ekle, proje_duzenle, proje_sil, pdf_olusturma, musteri_duzenleme, raporlar))

            connection.commit()
        return jsonify({'message': 'Permissions successfully updated.'})
    except Exception as e:
        if connection:
            connection.rollback()
        return jsonify({'message': f'Error: {str(e)}'}), 500
    finally:
        if connection:
            connection.close()

# User Registration API
@app.route('/api/register', methods=['POST'])
def register_user():
    """
    Kullanıcı kaydı için API endpoint'i.
    Kullanıcının seçtiği rol yerine varsayılan olarak 'ziyaretci' rolü atar.
    """
    try:
        data = request.get_json()
        fullname = data.get('fullname')
        email = data.get('email')
        phone = data.get('phone')
        password = data.get('password')
        role = 'Ziyaretçi'  # Kullanıcının seçtiği rolü dikkate alma, varsayılan olarak 'ziyaretci' ata

        if not all([fullname, email, phone, password]):
            return jsonify({'message': 'Tüm alanları doldurmanız gerekmektedir.'}), 400

        # E-posta formatı ve telefon numarası formatı için basit kontrol
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            return jsonify({'message': 'Geçerli bir e-posta adresi girin.'}), 400
        
        # Parola hash'leme
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        connection = get_db_connection()
        if connection is None:
            return jsonify({'message': 'Veritabanı bağlantısı kurulamadı.'}), 500

        with connection.cursor() as cursor:
            # E-posta adresinin zaten var olup olmadığını kontrol et
            sql_check = "SELECT id FROM users WHERE email = %s"
            cursor.execute(sql_check, (email,))
            if cursor.fetchone():
                return jsonify({'message': 'Bu e-posta adresi zaten kayıtlı.'}), 409

            # Yeni kullanıcıyı kaydet
            sql_insert = "INSERT INTO users (fullname, email, phone, password, role) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(sql_insert, (fullname, email, phone, hashed_password, role))
            connection.commit()

        return jsonify({'message': 'Kayıt başarılı! Yöneticinin onayı bekleniyor.'}), 201

    except Exception as e:
        app.logger.error(f"Kullanıcı kayıt hatası: {e}")
        traceback.print_exc()
        return jsonify({'message': 'Kayıt sırasında bir hata oluştu.'}), 500
    finally:
        if 'connection' in locals() and connection.open:
            connection.close()

@app.route('/api/login', methods=['POST'])
def login_user():
    """Authenticates a user and creates a session."""
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not all([email, password]):
        return jsonify({'message': 'Please enter your email and password.'}), 400

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Get all user details including new fields
            cursor.execute("SELECT id, fullname, email, phone, password, role, onay, profile_picture, hide_email, hide_phone, created_at FROM users WHERE email = %s", (email,))

            user = cursor.fetchone()

            if not user:
                return jsonify({'message': 'Invalid email or password.'}), 401

            is_match = bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8'))

            if not is_match:
                return jsonify({'message': 'Invalid email or password.'}), 401

            if user['onay'] == 0:
                return jsonify({
                    'message': 'Your account has not been approved yet. Please contact your administrator.',
                    'user': {
                        'email': user['email'],
                        'onay': user['onay']
                    },
                    'redirect': 'waiting.html'
                }), 403

            # Save user ID to session
            session['user_id'] = user['id']
            del user['password'] # Remove password from response for security

            # BAŞARILI GİRİŞTEN SONRA BİLDİRİM KONTROLÜNÜ ÇALIŞTIR
            # _check_and_notify_completed_steps(cursor)
            connection.commit() # _check_and_notify_completed_steps içinde yapılan güncellemeleri kaydet

            return jsonify({
                'message': 'Login successful!',
                'user': user
            }), 200

    except pymysql.Error as e:
        print(f"Database login error: {e}")
        if connection:
            connection.rollback() # Hata durumunda değişiklikleri geri al
        return jsonify({'message': f'Database error occurred: {e.args[1]}'}), 500
    except Exception as e:
        print(f"General login error: {e}")
        if connection:
            connection.rollback() # Hata durumunda değişiklikleri geri al
        return jsonify({'message': 'Server error, please try again later.'}), 500
    finally:
        if connection:
            connection.close()

# API to add new customer
@app.route('/api/customers', methods=['POST'])
def add_customer():
    """Adds a new customer to the database."""
    data = request.get_json()
    customer_name = data.get('companyName')
    status = data.get('status', 'active')
    contact_person = data.get('contactPerson')
    contact_title = data.get('contactTitle')
    phone = data.get('phone')
    email = data.get('email')
    country = data.get('country')
    city = data.get('city')
    district = data.get('district')
    postal_code = data.get('postalCode')
    address = data.get('address')
    notes = data.get('notes')
    user_id = data.get('user_id') # User ID who added the project for activity logging

    if not all([customer_name, contact_person, phone, user_id]):
        return jsonify({'message': 'Company Name, Contact Person, Phone, and User ID are required fields.'}), 400

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT customer_id FROM customers WHERE customer_name = %s", (customer_name,))
            existing_customer = cursor.fetchone()
            if existing_customer:
                return jsonify({'message': 'This company name is already registered.'}), 409

            sql = """
            INSERT INTO customers
            (customer_name, status, contact_person, contact_title,
             phone, email, country, city, district, postal_code, address, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (
                customer_name, status, contact_person, contact_title,
                phone, email, country, city, district, postal_code, address, notes
            ))
            connection.commit()
            new_customer_id = cursor.lastrowid

            # log_activity(
            #     user_id=user_id,
            #     title='New Customer Added',
            #     description=f'New customer named "{customer_name}" added.',
            #     icon='fas fa-user-plus'
            # )
            # Call add_activity API
            activity_data = {
                'user_id': user_id,
                'title': 'New Customer Added',
                'description': f'New customer named "{customer_name}" added.',
                'icon': 'fas fa-user-plus'
            }
        return jsonify({'message': 'Customer successfully added!', 'customerId': new_customer_id}), 201

    except pymysql.Error as e:
        print(f"Database error while adding customer: {e}")
        if e.args[0] == 1062: # Duplicate entry error
            return jsonify({'message': 'This email or company name is already registered.'}), 409
        return jsonify({'message': f'Database error occurred: {e.args[1]}'}), 500
    except Exception as e:
        print(f"General error while adding customer: {e}")
        return jsonify({'message': 'Server error, please try again later.'}), 500
    finally:
        if connection:
            connection.close()

def log_to_db(message, level="INFO"):
    """
    Log mesajlarını veritabanındaki 'logs' tablosuna kaydeder.
    """
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            sql = "INSERT INTO logs (timestamp, level, message) VALUES (NOW(), %s, %s)"
            cursor.execute(sql, (level, message))
            connection.commit()
    except Exception as e:
        # Veritabanına log yazarken bir hata olursa, konsola yazdır
        print(f"HATA: Veritabanına log yazarken bir hata oluştu: {e} - Mesaj: {message}")
        traceback.print_exc()
    finally:
        if connection:
            connection.close()
# API to list all customers
@app.route('/api/customers', methods=['GET'])
def get_customers():
    """Retrieves a list of all customers."""
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            sql = """
            SELECT c.customer_id, c.customer_name, c.contact_person, c.phone, c.email, c.status, c.country, c.city,
                    COUNT(p.project_id) AS project_count
            FROM customers c
            LEFT JOIN projects p ON c.customer_id = c.customer_id
            GROUP BY c.customer_id
            ORDER BY c.customer_name
            """
            cursor.execute(sql)
            customers = cursor.fetchall()
        return jsonify(customers), 200
    except pymysql.Error as e:
        print(f"Database error while fetching customers: {e}")
        return jsonify({'message': f'Database error occurred: {e.args[1]}'}), 500
    except Exception as e:
        print(f"General error while fetching customers: {e}")
        return jsonify({'message': 'Server error, please try again later.'}), 500
    finally:
        if connection:
            connection.close()

# API to get details of a single customer (added for Modal)
@app.route('/api/customers/<int:customer_id>', methods=['GET'])
def get_customer_details(customer_id):
    """Retrieves details of a single customer."""
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            sql = """
            SELECT customer_id, customer_name, status, contact_person, contact_title,
                   phone, email, country, city, district, postal_code, address, notes
            FROM customers
            WHERE customer_id = %s
            """
            cursor.execute(sql, (customer_id,))
            customer = cursor.fetchone()

            if not customer:
                return jsonify({'message': 'Customer not found.'}), 404

        return jsonify(customer), 200
    except pymysql.Error as e:
        print(f"Database error while fetching customer details: {e}")
        return jsonify({'message': f'Database error occurred: {e.args[1]}'}), 500
    except Exception as e:
        print(f"General error while fetching customer details: {e}")
        return jsonify({'message': 'Server error, please try again later.'}), 500
    finally:
        if connection:
            connection.close()

# Customer Update API (PUT)
@app.route('/api/customers/<int:customer_id>', methods=['PUT'])
def update_customer(customer_id):
    """Updates information of an existing customer."""
    data = request.get_json()
    customer_name = data.get('companyName')
    status = data.get('status')
    contact_person = data.get('contactPerson')
    contact_title = data.get('contactTitle')
    phone = data.get('phone')
    email = data.get('email')
    country = data.get('country')
    city = data.get('city')
    district = data.get('district')
    postal_code = data.get('postalCode')
    address = data.get('address')
    notes = data.get('notes')
    user_id = data.get('user_id') # User ID who updated for activity logging

    if not user_id:
        return jsonify({'message': 'User ID is missing.'}), 400
    if not any([customer_name, status, contact_person, contact_title, phone, email, country, city, district, postal_code, address, notes]):
        return jsonify({'message': 'No data to update.'}), 400

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT customer_name FROM customers WHERE customer_id = %s", (customer_id,))
            existing_customer_info = cursor.fetchone()
            if not existing_customer_info:
                return jsonify({'message': 'Customer not found.'}), 404
            old_customer_name = existing_customer_info['customer_name']


            updates = []
            params = []
            if customer_name is not None:
                updates.append("customer_name = %s")
                params.append(customer_name)
            if status is not None:
                updates.append("status = %s")
                params.append(status)
            if contact_person is not None:
                updates.append("contact_person = %s")
                params.append(contact_person)
            if contact_title is not None:
                updates.append("contact_title = %s")
                params.append(contact_title)
            if phone is not None:
                updates.append("phone = %s")
                params.append(phone)
            if email is not None:
                updates.append("email = %s")
                params.append(email)
            if country is not None:
                updates.append("country = %s")
                params.append(country)
            if city is not None:
                updates.append("city = %s")
                params.append(city)
            if district is not None:
                updates.append("district = %s")
                params.append(district)
            if postal_code is not None:
                updates.append("postal_code = %s")
                params.append(postal_code)
            if address is not None:
                updates.append("address = %s")
                params.append(address)
            if notes is not None:
                updates.append("notes = %s")
                params.append(notes)

            if not updates:
                return jsonify({'message': 'No fields specified for update.'}), 400

            sql = f"UPDATE customers SET {', '.join(updates)} WHERE customer_id = %s"
            params.append(customer_id)

            cursor.execute(sql, tuple(params))
            connection.commit()

            if cursor.rowcount == 0:
                return jsonify({'message': 'Customer data is already up to date or no changes were made.'}), 200

            activity_data = {
                'user_id': user_id,
                'title': 'Customer Updated',
                'description': f'Customer "{old_customer_name}" information updated.',
                'icon': 'fas fa-user-edit'
            }
            # Call add_activity API
        return jsonify({'message': 'Customer successfully updated!'}), 200

    except pymysql.Error as e:
        print(f"Database error while updating customer: {e}")
        if e.args[0] == 1062:
            return jsonify({'message': 'This email or company name is already registered.'}), 409
        return jsonify({'message': f'Database error occurred: {e.args[1]}'}), 500
    except Exception as e:
        print(f"General error while updating customer: {e}")
        return jsonify({'message': 'Server error, please try again later.'}), 500
    finally:
        if connection:
            connection.close()

@app.route('/api/customers/<int:customer_id>', methods=['DELETE'])
def delete_customer(customer_id):
    """Deletes a customer from the database."""
    data = request.get_json() # Get user_id from DELETE request body
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({'message': 'User ID is missing.'}), 400

    customer_name = "Unknown Customer" # Default value for logging
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT customer_name FROM customers WHERE customer_id = %s", (customer_id,))
            customer_info = cursor.fetchone()
            if not customer_info:
                return jsonify({'message': 'Customer not found.'}), 404
            customer_name = customer_info['customer_name']

            sql = "DELETE FROM customers WHERE customer_id = %s"
            cursor.execute(sql, (customer_id,))
            connection.commit()

            if cursor.rowcount == 0:
                return jsonify({'message': 'Customer could not be deleted or does not exist.'}), 404

            activity_data = {
                'user_id': user_id,
                'title': 'Customer Deleted',
                'description': f'Customer "{customer_name}" deleted.',
                'icon': 'fas fa-user-minus'
            }
            # Call add_activity API

        return jsonify({'message': 'Customer successfully deleted!'}), 200

    except pymysql.Error as e:
        print(f"Database error while deleting customer: {e}")
        if e.args[0] == 1451: # Foreign key constraint fails
            return jsonify({'message': 'There are projects associated with this customer. Please delete related projects first.'}), 409
        return jsonify({'message': f'Database error occurred: {e.args[1]}'}), 500
    except Exception as e:
        print(f"General error while deleting customer: {e}")
        return jsonify({'message': 'Server error, please try again later.'}), 500
    finally:
        if connection:
            connection.close()


# API to list all projects
@app.route('/api/projects', methods=['GET'])
def get_projects():
    """
    Retrieves a list of all projects with customer and manager names,
    also includes the title of the latest progress step and delay status.
    """
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            sql = """
            SELECT
                p.project_id,
                p.project_name,
                p.reference_no,
                p.description,
                p.contract_date,
                p.meeting_date,
                p.start_date,
                p.end_date,
                p.project_location,
                p.status, -- Projenin ana durumunu da çekiyoruz
                c.customer_name,
                u.fullname AS project_manager_name,
                c.customer_id,
                u.id AS project_manager_user_id,
                -- Toplam gecikme günlerini doğrudan projeler tablosundan alıyoruz
                (SELECT IFNULL(SUM(pp.delay_days), 0) + IFNULL(SUM(pp.custom_delay_days), 0) FROM project_progress pp WHERE pp.project_id = p.project_id) AS total_delay_days,
                -- Mevcut tarih aralığına uyan iş gidişatının başlığını al
                (SELECT title FROM project_progress
                 WHERE project_id = p.project_id
                   AND CURDATE() BETWEEN start_date AND end_date
                 ORDER BY start_date ASC -- Birden fazla adım aynı anda aktifse en erken başlayanı al
                 LIMIT 1) AS current_progress_title,
                -- Mevcut tarih aralığına uyan iş gidişatının gecikme günlerini al
                (SELECT IFNULL(delay_days, 0) FROM project_progress
                 WHERE project_id = p.project_id
                   AND CURDATE() BETWEEN start_date AND end_date
                 ORDER BY start_date ASC
                 LIMIT 1) AS current_step_delay_days,
                -- Mevcut tarih aralığına uyan iş gidişatının özel gecikme günlerini al
                (SELECT IFNULL(custom_delay_days, 0) FROM project_progress
                 WHERE project_id = p.project_id
                   AND CURDATE() BETWEEN start_date AND end_date
                 ORDER BY start_date ASC
                 LIMIT 1) AS current_step_custom_delay_days,
                -- Yeni eklenen: Projenin ilk iş adımının başlığı (yedek olarak kullanılacak)
                (SELECT title FROM project_progress
                 WHERE project_id = p.project_id
                 ORDER BY start_date ASC, created_at ASC
                 LIMIT 1) AS first_progress_step_title
            FROM projects p
            JOIN customers c ON p.customer_id = c.customer_id
            JOIN users u ON p.project_manager_id = u.id
            ORDER BY p.created_at DESC
            """
            cursor.execute(sql)
            projects_data = cursor.fetchall()

            for project in projects_data:
                current_project_status = project['status'] # Bu, DB'den gelen kalıcı durumdur
                total_delay_days = project['total_delay_days'] if project['total_delay_days'] is not None else 0
                current_progress_title = project['current_progress_title']
                current_step_delay_days = project['current_step_delay_days'] if project['current_step_delay_days'] is not None else 0
                current_step_custom_delay_days = project['current_step_custom_delay_days'] if project['current_step_custom_delay_days'] is not None else 0

                # Mevcut iş adımının toplam gecikmesini hesapla
                current_step_total_delay = current_step_delay_days + current_step_custom_delay_days

                # display_status'u belirle
                if current_project_status == 'Tamamlandı':
                    project['display_status'] = 'Tamamlandı'
                elif current_progress_title: # Mevcut tarih aralığına uyan bir iş gidişatı başlığı varsa
                    if current_step_total_delay > 0:
                        project['display_status'] = f"{current_progress_title} (Gecikmeli)"
                    else:
                        project['display_status'] = current_progress_title
                elif total_delay_days > 0: # Aktif bir adım yok ama genel projede gecikme var
                    # Eğer proje genel olarak gecikmeli ve aktif bir adım yoksa,
                    # projenin adını veya ilk iş adımının adını kullan
                    fallback_title = project['project_name'] # Varsayılan olarak proje adı
                    if project['first_progress_step_title']: # Eğer ilk iş adımının başlığı varsa onu kullan
                        fallback_title = project['first_progress_step_title']
                    project['display_status'] = f"{fallback_title} (Gecikmeli)"
                elif current_project_status == 'Planlama Aşamasında': # Backend'den gelen durum Planlama ise
                    project['display_status'] = 'Planlama Aşamasında'
                else: # Aktif bir adım yok ve genel gecikme yok, veya diğer durumlar
                    project['display_status'] = 'Aktif' # Varsayılan olarak Aktif

                # datetime.date objelerini ISO formatlı stringlere dönüştür
                project['contract_date'] = project['contract_date'].isoformat() if isinstance(project['contract_date'], datetime.date) else None
                project['meeting_date'] = project['meeting_date'].isoformat() if isinstance(project['meeting_date'], datetime.date) else None
                project['start_date'] = project['start_date'].isoformat() if isinstance(project['start_date'], datetime.date) else None
                project['end_date'] = project['end_date'].isoformat() if isinstance(project['end_date'], datetime.date) else None

        return jsonify(projects_data), 200
    except pymysql.Error as e:
        print(f"Database error while fetching projects: {e}")
        return jsonify({'message': f'Database error occurred: {e.args[1]}'}), 500
    except Exception as e:
        print(f"General error while fetching projects: {e}")
        return jsonify({'message': 'Server error, please try again later.'}), 500
    finally:
        if connection:
            connection.close()

# API to get details of a single project (for Modal)
@app.route('/api/projects/<int:project_id>', methods=['GET'])
def get_project_details(project_id):
    """Retrieves details of a single project."""
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            sql = """
            SELECT p.project_id, p.project_name, p.reference_no, p.description, p.contract_date,
                    p.meeting_date, p.start_date, p.end_date, p.project_location, p.status,
                    c.customer_name, u.fullname AS project_manager_name, c.customer_id, u.id AS project_manager_user_id
            FROM projects p
            JOIN customers c ON p.customer_id = c.customer_id
            JOIN users u ON p.project_manager_id = u.id
            WHERE p.project_id = %s
            """
            cursor.execute(sql, (project_id,))
            project = cursor.fetchone()

            if not project:
                return jsonify({'message': 'Project not found.'}), 404

            project['contract_date'] = project['contract_date'].isoformat() if isinstance(project['contract_date'], datetime.date) else None
            project['meeting_date'] = project['meeting_date'].isoformat() if isinstance(project['meeting_date'], datetime.date) else None
            project['start_date'] = project['start_date'].isoformat() if isinstance(project['start_date'], datetime.date) else None
            project['end_date'] = project['end_date'].isoformat() if isinstance(project['end_date'], datetime.date) else None

        return jsonify(project), 200
    except pymysql.Error as e:
        print(f"Database error while fetching project details: {e}")
        return jsonify({'message': f'Database error occurred: {e.args[1]}'}), 500
    except Exception as e:
        print(f"General error while fetching project details: {e}")
        return jsonify({'message': 'Server error, please try again later.'}), 500
    finally:
        if connection:
            connection.close()

# Helper function for sending notifications
def send_notification(cursor, user_id, title, message):
    """Sends a notification to a specific user using the provided cursor."""
    try:
        sql = "INSERT INTO notifications (user_id, title, message, created_at) VALUES (%s, %s, %s, NOW())"
        cursor.execute(sql, (user_id, title, message))
        # Note: We don't commit here. The main function (e.g., login_user) will commit all changes at once.
        print(f"Bildirim hazırlandı: Kullanıcı ID: {user_id}, Başlık: '{title}', Mesaj: '{message}'")
    except pymysql.Error as e:
        print(f"Bildirim hazırlanırken veritabanı hatası: {e}")
    except Exception as e:
        print(f"Bildirim hazırlanırken genel hata: {e}")

# YENİ EKLENEN FONKSİYON: E-posta gönderme yardımcı fonksiyonu
def send_email_notification(recipient_email, subject, body):
    """
    Belirtilen e-posta adresine bildirim e-postası gönderir.
    Ortam değişkenlerinden SMTP bilgilerini alır.
    """
    sender_email = os.getenv("EMAIL_SENDER")
    sender_password = os.getenv("EMAIL_PASSWORD")
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT", 587)) # Varsayılan 587 (TLS)

    if not all([sender_email, sender_password, smtp_server]):
        print("UYARI: E-posta gönderme ayarları eksik. E-posta gönderilemedi.")
        return

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = sender_email
    message["To"] = recipient_email

    html_body = f"""\
    <html>
      <head>
        <style>
          table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
          }}
          th, td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
          }}
          th {{
            background-color: #f2f2f2;
          }}
        </style>
      </head>
      <body>
        <p>Merhaba,</p>
        {body}
        <p>Saygılarımızla,</p>
        <p>Ser Elektrik Otomasyon Yönetimi</p>
        <br>
        <p style="font-size: 10px; color: #888;">Bu e-posta otomatik olarak gönderilmiştir, lütfen yanıtlamayın.</p>
      </body>
    </html>
    """
    # Düz metin içeriği, HTML'nin bir yedeği olarak kalır.
    part1 = MIMEText(body.replace('<p>','').replace('</p>','').replace('<table>','').replace('</table>','').replace('<tr>','').replace('</tr>','').replace('<th>','').replace('</th>','').replace('<td>','').replace('</td>',''), "plain")
    part2 = MIMEText(html_body, "html")

    message.attach(part1)
    message.attach(part2)

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.ehlo()  # Can be omitted
            server.starttls(context=context)
            server.ehlo()  # Can be omitted
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, message.as_string())
        print(f"E-posta başarıyla gönderildi: {recipient_email}")
    except Exception as e:
        print(f"E-posta gönderme hatası ({recipient_email}): {e}")
        traceback.print_exc()
def get_user_fullname_by_id(cursor, user_id):
    """Retrieves the full name of a user by their ID."""
    if not user_id:
        return "Bilinmeyen Kullanıcı"
    try:
        cursor.execute("SELECT fullname FROM users WHERE id = %s", (user_id,))
        result = cursor.fetchone()
        return result['fullname'] if result else "Bilinmeyen Kullanıcı"
    except Exception as e:
        print(f"Error fetching user fullname: {e}")
        return "Bilinmeyen Kullanıcı"

# Project Update API (PUT) - for projects table
# Find the update_project function in app.py and update it as follows:

@app.route('/api/projects/<int:project_id>', methods=['PUT'])
def update_project(project_id):
    """Updates a project."""
    data = request.get_json()
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({'message': 'User ID is required.'}), 400

    # Tüm olası sütunlar
    possible_columns = [
        'project_name', 'reference_no', 'description', 'customer_id',
        'project_location', 'status', 'project_manager_id', 'contract_date',
        'meeting_date', 'start_date', 'end_date'
    ]

    # Hangi sütunların güncellendiğini takip et
    updates = []
    params = []

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Mevcut projeyi getir
            cursor.execute("SELECT * FROM projects WHERE project_id = %s", (project_id,))
            existing_project = cursor.fetchone()
            if not existing_project:
                return jsonify({'message': 'Project not found.'}), 404

            # Güncellenecek değerleri belirle
            for column in possible_columns:
                # Sadece 'status' alanı için özel bir durum: Eğer manuel olarak 'Tamamlandı' gelmediyse, otomatik güncellemeye bırak
                if column == 'status':
                    if data.get(column) == 'Tamamlandı': # Eğer frontend'den Tamamlandı olarak gelirse güncelle
                        updates.append(f"{column} = %s")
                        params.append(data[column])
                    # Aksi takdirde, status alanını bu API'de güncelleme, determine_and_update_project_status yönetsin
                elif column in data and data[column] is not None:
                    updates.append(f"{column} = %s")
                    params.append(data[column])

            # Hiçbir güncelleme yoksa
            if not updates:
                return jsonify({'message': 'No information to update.'}), 200

            # SQL sorgusunu oluştur
            sql = f"UPDATE projects SET {', '.join(updates)} WHERE project_id = %s"
            params.append(project_id)

            print(f"Güncelleme sorgusu: {sql}")
            print(f"Parametre değerleri: {params}")

            # Sorguyu çalıştır
            cursor.execute(sql, params)
            connection.commit() # update_project tarafından yapılan değişiklikleri commit et

            # Projenin genel durumunu belirle ve güncelle
            determine_and_update_project_status(cursor, project_id)
            connection.commit() # determine_and_update_project_status tarafından yapılan değişiklikleri commit et

            return jsonify({'message': 'Proje başarıyla güncellendi!'}), 200

    except Exception as e:
        print(f"Proje güncelleme hatası: {str(e)}")
        traceback.print_exc()
        if connection:
            connection.rollback()
        return jsonify({'message': f'Server error: {str(e)}'}), 500

    finally:
        if connection:
            connection.close()
# Proje silme api (DELETE)
@app.route('/api/projects/<int:project_id>', methods=['DELETE'])
def delete_project_api(project_id):
    """Deletes a project from the database."""
    data = request.get_json()
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({'message': 'User ID is missing.'}), 400

    project_name = "Unknown Project"
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT project_name, project_manager_id FROM projects WHERE project_id = %s", (project_id,))
            project_info = cursor.fetchone()

            if not project_info:
                return jsonify({'message': 'Project could not be deleted or not found.'}), 404

            project_name = project_info['project_name']
            project_manager_id = project_info['project_manager_id']

            cursor.execute("DELETE FROM project_progress WHERE project_id = %s", (project_id,))

            sql = "DELETE FROM projects WHERE project_id = %s"
            cursor.execute(sql, (project_id,))
            connection.commit()

            if cursor.rowcount == 0:
                return jsonify({'message': 'Project could not be deleted or not found.'}), 404

            activity_data = {
                'user_id': user_id,
                'title': 'Project Deleted',
                'description': f'Project named "{project_name}" deleted.',
                'icon': 'fas fa-trash'
            }
            # Call add_activity API

            # Send notification to project manager
            send_notification(
                cursor, # Pass the cursor
                project_manager_id,
                "Proje Silindi",
                f"Yönettiğiniz '{project_name}' Projesi silindi.." # Message updated
            )

            # Proje yöneticisinin e-postasını al ve e-posta gönder
            cursor.execute("SELECT email FROM users WHERE id = %s", (project_manager_id,))
            manager_email = cursor.fetchone()
            if manager_email and manager_email['email']:
                send_email_notification(
                    manager_email['email'],
                    "Proje Silindi",
                    f"Yönettiğiniz '{project_name}' Projesi silindi."
                )
            else:
                print(f"UYARI: Proje yöneticisi {project_manager_id} için e-posta adresi bulunamadı.")


        return jsonify({'message': 'Project successfully deleted!'}), 200

    except pymysql.Error as e:
        print(f"Database error while deleting project: {e}")
        if e.args[0] == 1451: # Foreign key constraint fails
            return jsonify({'message': 'There are projects associated with this customer. Please delete related projects first.'}), 409
        return jsonify({'message': f'Database error occurred: {e.args[1]}'}), 500
    except Exception as e:
        print(f"General error while deleting project: {e}")
        return jsonify({'message': 'Server error, please try again later.'}), 500
    finally:
        if connection: # Hata düzeltmesi: connection'ın varlığını kontrol et
            connection.close()

# API to list project managers
@app.route('/api/project_managers', methods=['GET'])
def get_project_managers():
    """Retrieves a list of users who can be assigned as project managers."""
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, fullname FROM users WHERE role IN ('Technician', 'Engineer', 'Manager', 'Project Manager') ORDER BY fullname")
            managers = cursor.fetchall()
        return jsonify(managers), 200
    except pymysql.Error as e:
        print(f"Database error while fetching managers: {e}")
        return jsonify({'message': f'Database error occurred: {e.args[1]}'}), 500
    except Exception as e:
        print(f"General error while fetching managers: {e}")
        return jsonify({'message': 'Server error, please try again later.'}), 500
    finally:
        if connection:
            connection.close()

# API endpoint for providing location data
@app.route('/api/locations/turkey', methods=['GET'])
def get_turkey_locations():
    """Returns Turkey location data (provinces and districts)."""
    if not TURKEY_LOCATIONS:
        return jsonify({'message': 'Location data could not be loaded or is empty.'}), 500
    return jsonify(TURKEY_LOCATIONS), 200

# Dashboard Statistics API
@app.route('/api/project-stats', methods=['GET'])
def get_project_stats():
    """Kontrol paneli için çeşitli istatistikleri alır."""
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Aktif Projeler: 'Tamamlandı' durumunda olmayan tüm projeler.
            # Kullanıcının isteğine göre güncellendi.
            cursor.execute("SELECT COUNT(project_id) AS count FROM projects WHERE status != 'Tamamlandı'")
            active_projects = cursor.fetchone()['count']

            # Tamamlanan projeler
            cursor.execute("SELECT COUNT(project_id) AS count FROM projects WHERE status = 'Tamamlandı'")
            completed_projects = cursor.fetchone()['count']

            # Geciken Projeler: total_delay_days > 0 olan projeler (herhangi bir iş adımında gecikme olan projeler)
            # Kullanıcının isteğine göre güncellendi.
            cursor.execute("""
                SELECT COUNT(DISTINCT p.project_id) AS count
                FROM projects p
                JOIN project_progress pp ON p.project_id = pp.project_id
                WHERE pp.delay_days > 0 OR pp.custom_delay_days > 0
            """)
            delayed_projects = cursor.fetchone()['count']

            # Toplam projeler
            cursor.execute("SELECT COUNT(project_id) AS count FROM projects")
            total_projects = cursor.fetchone()['count']

        stats = {
            "activeProjects": active_projects,
            "completedProjects": completed_projects,
            "delayedProjects": delayed_projects,
            "totalProjects": total_projects,
        }
        return jsonify(stats), 200
    except pymysql.Error as e:
        print(f"İstatistikler alınırken veritabanı hatası: {e}")
        return jsonify({'message': f'Veritabanı hatası oluştu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"İstatistikler alınırken genel hata: {e}")
        return jsonify({'message': 'Sunucu hatası, lütfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()


# Dashboard Recent Activities API (retrieves from activities table)
@app.route('/api/recent_activities', methods=['GET'])
def get_recent_activities():
    """Retrieves recent activities from the activities table."""
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = """
            SELECT
                activity_id,
                user_id,
                title,
                description,
                icon,
                created_at,
                is_read
            FROM
                activities
            ORDER BY
                created_at DESC
            LIMIT 5;
            """
            cursor.execute(sql)
            activities = cursor.fetchall()
            # Convert created_at to ISO format
            for activity in activities:
                if 'created_at' in activity and isinstance(activity['created_at'], datetime.datetime):
                    activity['created_at'] = activity['created_at'].isoformat()
            return jsonify(activities)
    except pymysql.Error as e:
        print(f"Database error (recent activities): {e}")
        return jsonify({"error": "Database error occurred."}), 500
    except Exception as e:
        print(f"Unknown error (recent activities): {e}")
        return jsonify({"error": "An unknown server error occurred."}), 500
    finally:
        if connection:
            connection.close()


# Helper function to log a new activity
def log_activity(user_id, title, description, icon, is_read=0):
    """Logs a new activity to the activities table."""
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            user_fullname = "Unknown User"
            if user_id:
                cursor.execute("SELECT fullname FROM users WHERE id = %s", (user_id,))
                user = cursor.fetchone()
                if user:
                    user_fullname = user['fullname']

            # Remove potential (ID: X) expression from description
            cleaned_description = re.sub(r' \(ID: \d+\)', '', description)

            full_description = f"By {user_fullname}: {cleaned_description}"

            sql = """
            INSERT INTO activities (user_id, title, description, icon, created_at, is_read)
            VALUES (%s, %s, %s, %s, NOW(), %s)
            """
            cursor.execute(sql, (user_id, title, full_description, icon, is_read))
        connection.commit()
        print(f"Activity logged: Title: '{title}', Description: '{full_description}'")
    except pymysql.Error as e:
        print(f"Error logging activity: {e}")
    except Exception as e:
        print(f"General error logging activity: {e}")
    finally:
        if connection:
            connection.close()

# API to add new project (uncommented and completed from previous version)
@app.route('/api/projects', methods=['POST'])
def add_project():
    data = request.json
    project_name = data.get('projectName')
    customer_id = data.get('customerId')
    project_manager_id = data.get('projectManagerId')
    reference_no = data.get('projectRef')
    description = data.get('projectDescription')
    contract_date = data.get('contractDate')
    meeting_date = data.get('meetingDate')
    start_date_str = data.get('startDate')
    end_date_str = data.get('endDate')
    project_location = data.get('projectLocation')
    status = data.get('status', 'Planlama Aşamasında')

    user_id = data.get('user_id')

    if not all([project_name, customer_id, project_manager_id, start_date_str, end_date_str]):
        return jsonify({'message': 'Project name, customer, project manager, start date, and end date are required.'}), 400

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            sql = """
            INSERT INTO projects (project_name, customer_id, project_manager_id, reference_no, description,
                                  contract_date, meeting_date, start_date, end_date, project_location, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (
                project_name, customer_id, project_manager_id, reference_no, description,
                contract_date, meeting_date, start_date_str, end_date_str, project_location, status
            ))
            # No commit here, commit after all progress steps are added

            new_project_id = cursor.lastrowid

            progress_steps = data.get('progressSteps', [])
            last_step_end_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()

            for step in progress_steps:
                step_title = step.get('title')
                step_description = step.get('description')
                step_start_date_str = step.get('startDate')
                step_end_date_str = step.get('endDate')

                if not all([step_title, step_start_date_str, step_end_date_str]):
                    print(f"WARNING: Missing data in a progress step for project {new_project_id}. Skipping step.")
                    continue

                new_step_start_date = datetime.datetime.strptime(step_start_date_str, '%Y-%m-%d').date()
                step_end_date = datetime.datetime.strptime(step_end_date_str, '%Y-%m-%d').date()

                delay_days = 0
                if last_step_end_date:
                    time_diff = (new_step_start_date - last_step_end_date).days
                    if time_diff > 1:
                        delay_days = time_diff - 1

                sql_insert_progress = """
                INSERT INTO project_progress (project_id, title, description, start_date, end_date, delay_days, real_end_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(sql_insert_progress, (new_project_id, step_title, step_description, step_start_date_str, step_end_date_str, delay_days, step_end_date_str))
                # Removed commit inside the loop

                last_step_end_date = step_end_date

            # Commit all changes (project and its progress steps) at once
            connection.commit()

            if project_manager_id:
                send_notification(
                    cursor, # Pass the cursor here
                    project_manager_id,
                    "Yeni Bir Proje Atandı",
                    f"Size yeni bir proje atandı: '{project_name}'."
                )
                # Proje yöneticisinin e-postasını al ve e-posta gönder
                cursor.execute("SELECT email FROM users WHERE id = %s", (project_manager_id,))
                manager_email = cursor.fetchone()
                if manager_email and manager_email['email']:
                    send_email_notification(
                        manager_email['email'],
                        "Yeni Bir Proje Atandı",
                        f"Size yeni bir proje atandı: '{project_name}'. Proje detaylarını sistemden kontrol edebilirsiniz."
                    )
                else:
                    print(f"UYARI: Proje yöneticisi {project_manager_id} için e-posta adresi bulunamadı.")


        return jsonify({"message": "Project successfully added", "projectId": new_project_id}), 201
    except pymysql.Error as e:
        print(f"Database error while adding project: {e}")
        traceback.print_exc() # Print full traceback for database errors
        if connection:
            connection.rollback() # Rollback on database error
        return jsonify({'message': f'Database error occurred: {e.args[1]}'}), 500
    except Exception as e:
        print(f"General error while adding project: {e}")
        traceback.print_exc() # Print full traceback for general errors
        if connection:
            connection.rollback() # Rollback on general error
        return jsonify({'message': 'Server error, please try again later.'}), 500
    finally:
        if connection:
            connection.close()

# API to log PDF Report Creation Activity (to be called from frontend)
@app.route('/api/log_pdf_report', methods=['POST'])
def log_pdf_report_api():
    """Logs a PDF report creation activity."""
    data = request.get_json()
    user_id = data.get('user_id')
    report_type = data.get('report_type', 'General Report') # Default value
    project_name = data.get('project_name') # Optional

    if not user_id:
        return jsonify({'message': 'User ID is missing.'}), 400

    description_text = f'PDF file of "{report_type}" report created.'
    if project_name:
        description_text = f'PDF report created for project "{project_name}".'

    try:
        activity_data = {
            'user_id': user_id,
            'title': 'PDF Report Created',
            'description': description_text,
            'icon': 'fas fa-file-pdf'
        }
        # Call add_activity API
        return jsonify({'message': 'PDF report activity successfully logged.'}), 200
    except Exception as e:
        print(f"Error logging PDF report activity: {e}")
        return jsonify({'message': 'Error logging PDF report activity.'}), 500


# API to get project progress steps
@app.route('/api/projects/<int:project_id>/progress', methods=['GET'])
def get_project_progress_steps(project_id):
    """Retrieves all progress steps for a specific project."""
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Check if 'is_completed' column exists and add if not
            cursor.execute("SHOW COLUMNS FROM project_progress LIKE 'is_completed'")
            column_exists = cursor.fetchone() is not None
            if not column_exists:
                print("is_completed sütunu bulunamadı, ekleniyor...")
                cursor.execute("ALTER TABLE project_progress ADD COLUMN is_completed TINYINT(1) DEFAULT 0")
                connection.commit()

            # Check if 'custom_delay_days' column exists and add if not
            cursor.execute("SHOW COLUMNS FROM project_progress LIKE 'custom_delay_days'")
            column_exists_custom_delay = cursor.fetchone() is not None
            if not column_exists_custom_delay:
                print("custom_delay_days sütunu bulunamadı, ekleniyor...")
                cursor.execute("ALTER TABLE project_progress ADD COLUMN custom_delay_days INT DEFAULT 0")
                connection.commit()

            # Check if 'real_end_date' column exists and add if not
            cursor.execute("SHOW COLUMNS FROM project_progress LIKE 'real_end_date'")
            column_exists_real_end_date = cursor.fetchone() is not None
            if not column_exists_real_end_date:
                print("real_end_date sütunu bulunamadı, ekleniyor...")
                cursor.execute("ALTER TABLE project_progress ADD COLUMN real_end_date DATE NULL")
                connection.commit()

            sql = """
            SELECT
                progress_id,
                project_id,
                title AS step_name,
                description,
                start_date,
                end_date,
                delay_days,
                custom_delay_days,
                real_end_date,
                is_completed,  # Added this line
                created_at
            FROM project_progress
            WHERE project_id = %s
            ORDER BY start_date ASC, created_at ASC
            """
            cursor.execute(sql, (project_id,))
            steps = cursor.fetchall()

            for step in steps:
                step['start_date'] = step['start_date'].isoformat() if isinstance(step['start_date'], datetime.date) else None
                step['end_date'] = step['end_date'].isoformat() if isinstance(step['end_date'], datetime.date) else None
                step['real_end_date'] = step['real_end_date'].isoformat() if isinstance(step['real_end_date'], datetime.date) else None
                step['created_at'] = step['created_at'].isoformat() if isinstance(step['created_at'], datetime.datetime) else None
                step['custom_delay_days'] = int(step['custom_delay_days']) if step['custom_delay_days'] is not None else 0
                step['is_completed'] = bool(step['is_completed'])  # Convert TINYINT to boolean

        return jsonify(steps), 200
    except pymysql.Error as e:
        print(f"Database error while fetching progress steps: {e}")
        return jsonify({'message': f'Database error occurred: {e.args[1]}'}), 500
    except Exception as e:
        print(f"General error while fetching progress steps: {e}")
        traceback.print_exc()
        return jsonify({'message': 'Server error, please try again later.'}), 500
    finally:
        if connection:
            connection.close()

@app.route('/api/projects/<int:project_id>/progress', methods=['POST'])
def add_project_progress_step_from_modal(project_id):
    data = request.get_json()
    step_name = data.get('step_name')
    description = data.get('description')
    start_date_str = data.get('start_date')
    end_date_str = data.get('end_date')

    user_id = session.get('user_id')
    if not user_id and 'user_id' in data:
        user_id = data.get('user_id')

    if not all([project_id, step_name, start_date_str, end_date_str]):
        return jsonify({'message': 'Project ID, title, start and end date are required.'}), 400

    if not user_id:
        print("Warning: No user_id found in session or request. Using default.")
        user_id = 1

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT project_name, project_manager_id FROM projects WHERE project_id = %s", (project_id,))
            project_info = cursor.fetchone()
            project_name = project_info['project_name'] if project_info else f"ID: {project_id}"
            project_manager_id = project_info['project_manager_id'] if project_info else None

            cursor.execute("""
                SELECT end_date FROM project_progress
                WHERE project_id = %s
                ORDER BY end_date DESC
                LIMIT 1
            """, (project_id,))
            last_step = cursor.fetchone()
            previous_end_date = last_step['end_date'] if last_step else None
            delay_days = 0

            if previous_end_date:
                new_step_start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()
                time_diff = (new_step_start_date - previous_end_date).days
                if time_diff > 1:
                    delay_days = time_diff - 1

            cursor.execute("SHOW COLUMNS FROM project_progress LIKE 'custom_delay_days'")
            column_exists_custom_delay = cursor.fetchone() is not None
            if not column_exists_custom_delay:
                cursor.execute("ALTER TABLE project_progress ADD COLUMN custom_delay_days INT DEFAULT 0")
                connection.commit()

            # BURADA DEĞİŞİKLİK YAPILDI: 'real_end_date' sütununun varlığı kontrol edildi ve yoksa eklendi
            cursor.execute("SHOW COLUMNS FROM project_progress LIKE 'real_end_date'")
            column_exists_real_end_date = cursor.fetchone() is not None
            if not column_exists_real_end_date:
                cursor.execute("ALTER TABLE project_progress ADD COLUMN real_end_date DATE NULL")
                connection.commit()

            sql_insert = """
                INSERT INTO project_progress (project_id, title, description, start_date, end_date, delay_days, custom_delay_days, real_end_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            # BURADA DEĞİŞİKLİK YAPILDI: Yeni eklenen iş adımının real_end_date'i, başlangıçta end_date ile aynı olacak
            cursor.execute(sql_insert, (project_id, step_name, description, start_date_str, end_date_str, delay_days, 0, end_date_str))
            new_progress_id = cursor.lastrowid

            update_result = update_project_dates(cursor, project_id)
            if update_result:
                print(f"Project dates successfully updated for project {project_id}")
            else:
                print(f"Failed to update project dates for project {project_id}")

            determine_and_update_project_status(cursor, project_id)
            connection.commit()

            if project_manager_id:
                try:
                    send_notification(
                        cursor, # Pass the cursor here
                        project_manager_id,
                        "Proje İlerleme Adımı Eklendi",
                        f"Yönettiğiniz '{project_name}' projesine '{step_name}' adında yeni bir iş adımı eklendi."
                    )
                    # E-posta bildirimi gönder
                    cursor.execute("SELECT email FROM users WHERE id = %s", (project_manager_id,))
                    manager_email = cursor.fetchone()
                    if manager_email and manager_email['email']:
                        send_email_notification(
                            manager_email['email'],
                            "Proje İlerleme Adımı Eklendi",
                            f"Yönettiğiniz '{project_name}' projesine '{step_name}' adında yeni bir iş adımı eklendi. Detaylar için sistemi kontrol edin."
                        )
                    else:
                        print(f"UYARI: Proje yöneticisi {project_manager_id} için e-posta adresi bulunamadı.")

                except Exception as notif_error:
                    print(f"Error sending notification (non-critical): {notif_error}")

            return jsonify({
                'message': 'Progress step successfully added!',
                'progress_id': new_progress_id
            }), 201

    except pymysql.Error as e:
        print(f"Database error while adding progress step: {e}")
        if connection:
            connection.rollback()
        return jsonify({'message': f'Database error occurred: {e.args[1]}'}), 500

    except Exception as e:
        print(f"General error while adding progress step: {e}")
        traceback.print_exc()
        if connection:
            connection.rollback()
        return jsonify({'message': 'Server error, please try again later.'}), 500

    finally:
        if connection:
            connection.close()
def send_email_async(to_emails, subject, body):
    """
    E-posta gönderme işlemini ayrı bir thread'de asenkron olarak gerçekleştirir.
    Args:
        to_emails (list): E-posta gönderilecek alıcıların listesi.
        subject (str): E-postanın konusu.
        body (str): E-postanın içeriği.
    """
    def _send_email():
        # E-posta gönderme ayarları .env dosyasından çekilir
        smtp_server = os.getenv("SMTP_SERVER")
        smtp_port = int(os.getenv("SMTP_PORT", 465))
        sender_email = os.getenv("SENDER_EMAIL")
        sender_password = os.getenv("SENDER_PASSWORD")

        if not all([smtp_server, sender_email, sender_password]):
            log_to_db("SMTP sunucu bilgileri eksik. E-posta gönderilemedi.", "ERROR")
            return

        try:
            # SSL bağlantısını kur
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(smtp_server, smtp_port, context=context) as server:
                server.login(sender_email, sender_password)
                
                # MIME formatında e-posta oluştur
                msg = MIMEMultipart("alternative")
                msg['Subject'] = subject
                msg['From'] = sender_email
                msg['To'] = ", ".join(to_emails)

                # HTML içeriğini ekle
                part = MIMEText(body, "html")
                msg.attach(part)
                
                server.sendmail(sender_email, to_emails, msg.as_string())
            log_to_db(f"E-posta başarıyla gönderildi: {subject} - Alıcılar: {to_emails}", "INFO")
        except Exception as e:
            log_to_db(f"E-posta gönderilirken bir hata oluştu: {e}", "ERROR")
            traceback.print_exc()
# API to update project progress step

@app.route('/api/progress/<int:progress_id>', methods=['PUT'])
def update_project_progress_step(progress_id):
    data = request.get_json()
    print(f"Received data for updating progress {progress_id}: {data}")

    step_name = data.get('step_name')
    description = data.get('description')
    start_date_str = data.get('start_date')
    end_date_str = data.get('end_date')

    newly_added_custom_delay = data.get('newly_added_custom_delay', 0)
    if newly_added_custom_delay is None:
        newly_added_custom_delay = 0
    newly_added_custom_delay = int(newly_added_custom_delay)

    user_id = session.get('user_id')    
    if not user_id and 'user_id' in data:
        user_id = data.get('user_id')

    if not all([step_name, start_date_str, end_date_str]):
        return jsonify({'message': 'Title, start, end date are required.'}), 400

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Mevcut iş adımının verilerini çek
            cursor.execute("SELECT project_id, title, custom_delay_days, end_date FROM project_progress WHERE progress_id = %s", (progress_id,))
            existing_step = cursor.fetchone()

            if not existing_step:
                return jsonify({'message': 'Progress step not found.'}), 404

            current_project_id = existing_step['project_id']
            old_step_name = existing_step['title']
            current_custom_delay_from_db = existing_step.get('custom_delay_days', 0) or 0
            current_custom_delay_from_db = int(current_custom_delay_from_db)

            # Toplam custom_delay_days'i hesapla
            final_custom_delay_for_db = current_custom_delay_from_db + newly_added_custom_delay

            # Gerçek bitiş tarihini hesapla: real_end_date, erteleme günlerinden etkilenmemeli,
            # sadece end_date'in ilk girildiği hali olmalı.
            # Dolayısıyla, eğer bu bir erteleme işlemi değilse, mevcut real_end_date'i koru.
            # Eğer yeni bir adım ekleniyorsa, end_date ile aynı olsun.
            # Mevcut real_end_date'i veritabanından çekelim.
            cursor.execute("SELECT real_end_date FROM project_progress WHERE progress_id = %s", (progress_id,))
            current_real_end_date_from_db = cursor.fetchone()['real_end_date']

            # Eğer veritabanında zaten bir real_end_date varsa onu kullan, yoksa end_date'i kullan
            if current_real_end_date_from_db:
                real_end_date_to_save = current_real_end_date_from_db.isoformat()
            else:
                real_end_date_to_save = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date().isoformat()

            # Proje adını ve yöneticisini al (bildirimler için)
            cursor.execute("SELECT project_name, project_manager_id FROM projects WHERE project_id = %s", (current_project_id,))
            project_info = cursor.fetchone()
            project_name = project_info['project_name'] if project_info else f"ID: {current_project_id}"
            project_manager_id = project_info['project_manager_id'] if project_info else None

            # calculated_delay_days'i yeniden hesapla (bir önceki adımın bitiş tarihi ile mevcut adımın başlangıç tarihi arasındaki fark)
            calculated_delay_days = 0
            cursor.execute("""
                SELECT end_date FROM project_progress
                WHERE project_id = %s AND progress_id < %s
                ORDER BY end_date DESC
                LIMIT 1
            """, (current_project_id, progress_id))
            previous_step = cursor.fetchone()

            if previous_step and previous_step['end_date']:
                prev_end_date = previous_step['end_date']
                current_start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()
                time_diff = (current_start_date - prev_end_date).days
                if time_diff > 1:
                    calculated_delay_days = time_diff - 1
            elif not previous_step: # Eğer bu ilk iş adımıysa, projenin başlangıç tarihine göre gecikmeyi hesapla
                cursor.execute("SELECT start_date FROM projects WHERE project_id = %s", (current_project_id,))
                project_start_info = cursor.fetchone()
                if project_start_info and project_start_info['start_date']:
                    project_start_date = project_start_info['start_date']
                    current_start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()
                    time_diff = (current_start_date - project_start_date).days
                    if time_diff > 1:
                        calculated_delay_days = time_diff - 1

            sql_update = """
                UPDATE project_progress
                SET title = %s, description = %s, start_date = %s, end_date = %s,
                    delay_days = %s, custom_delay_days = %s, real_end_date = %s
                WHERE progress_id = %s
            """
            cursor.execute(sql_update, (
                step_name, description, start_date_str, end_date_str,
                calculated_delay_days, final_custom_delay_for_db, real_end_date_to_save, progress_id
            ))

            print(f"SQL query executed. Rows affected: {cursor.rowcount}")

            # Sonraki adımların delay_days'ini yeniden hesapla ve güncelle
            # Bu, güncel adımı takip eden tüm adımların gecikme durumunu doğru yansıtır
            cursor.execute("""
                SELECT progress_id, start_date, end_date, custom_delay_days, real_end_date
                FROM project_progress
                WHERE project_id = %s AND progress_id > %s
                ORDER BY start_date ASC, created_at ASC
            """, (current_project_id, progress_id))
            subsequent_steps = cursor.fetchall()

            last_end_date_for_recalc = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date() # Güncel adımın yeni bitiş tarihini kullan

            for sub_step in subsequent_steps:
                sub_progress_id = sub_step['progress_id']
                sub_start_date = sub_step['start_date'] # Bu, DB'den gelen tarih objesidir
                sub_end_date = sub_step['end_date'] # Bu, DB'den gelen tarih objesidir
                sub_custom_delay_days = sub_step['custom_delay_days'] or 0
                sub_real_end_date_from_db = sub_step['real_end_date']

                recalculated_sub_delay_days = 0
                time_diff_sub = (sub_start_date - last_end_date_for_recalc).days
                if time_diff_sub > 1:
                    recalculated_sub_delay_days = time_diff_sub - 1

                # Sonraki adımın gerçek bitiş tarihini de güncelle (mevcut real_end_date'i koru)
                if sub_real_end_date_from_db:
                    sub_real_end_date_to_save = sub_real_end_date_from_db.isoformat()
                else:
                    sub_real_end_date_to_save = sub_end_date.isoformat() # Eğer yoksa end_date'i kullan

                cursor.execute("""
                    UPDATE project_progress
                    SET delay_days = %s, real_end_date = %s
                    WHERE progress_id = %s
                """, (recalculated_sub_delay_days, sub_real_end_date_to_save, sub_progress_id))
                connection.commit()

                last_end_date_for_recalc = sub_end_date # Bir sonraki adım için bitiş tarihini güncelle

            # Projenin genel başlangıç ve bitiş tarihlerini iş adımlarına göre güncelle
            update_project_dates(cursor, current_project_id)
            # Projenin genel durumunu belirle ve güncelle
            determine_and_update_project_status(cursor, current_project_id)
            connection.commit()

            return jsonify({
                'message': 'Progress step successfully updated!',
                'custom_delay_days': final_custom_delay_for_db,
                'delay_days': calculated_delay_days,
                'real_end_date': real_end_date_to_save
            }), 200

    except Exception as e:
        print(f"Proje güncelleme hatası: {str(e)}")
        traceback.print_exc()
        if connection:
            connection.rollback()
        return jsonify({'message': f'Server error: {str(e)}'}), 500

    finally:
        if connection:
            connection.close()

@app.route('/api/progress/<int:progress_id>', methods=['DELETE'])
def delete_project_progress_step(progress_id):
    """Deletes a project progress step."""
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # İş adımının ait olduğu projeyi bul
            cursor.execute("SELECT project_id, title FROM project_progress WHERE progress_id = %s", (progress_id,))
            step_info = cursor.fetchone()

            if not step_info:
                return jsonify({'message': 'İş adımı bulunamadı.'}), 404

            project_id = step_info['project_id']
            step_title = step_info['title']

            # İş adımını sil
            sql_delete = "DELETE FROM project_progress WHERE progress_id = %s"
            cursor.execute(sql_delete, (progress_id,))

            # Proje başlangıç ve bitiş tarihlerini güncelle
            update_result = update_project_dates(cursor, project_id)
            if update_result:
                print(f"Project dates successfully updated after step deletion for project {project_id}")
            else:
                print(f"Failed to update project dates after step deletion for project {project_id}")

            # Projenin genel durumunu belirle ve güncelle
            determine_and_update_project_status(cursor, project_id)
            connection.commit()

            # Aktivite kaydı
            user_id = session.get('user_id')
            if user_id:
                log_activity(
                    user_id=user_id,
                    title="İş Adımı Silindi",
                    description=f"Proje ID: {project_id} için '{step_title}' iş adımı silindi.",
                    icon="fas fa-trash",
                    is_read=0
                )

        return jsonify({'message': 'İş adımı başarıyla silindi!'}), 200
    except pymysql.Error as e:
        print(f"Database error while deleting progress step: {e}")
        if connection:
            connection.rollback()
        return jsonify({'message': f'Veritabanı hatası oluştu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"General error while deleting progress step: {e}")
        traceback.print_exc()
        if connection:
            connection.rollback()
        return jsonify({'message': 'Sunucu hatası, lütfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()


@app.route('/api/user-info', methods=['GET'])
def get_user_info():
    """Retrieves detailed information for a single user."""
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'message': 'User ID is missing'}), 400

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Get all user fields including new ones
            cursor.execute("SELECT id, fullname, email, phone, role, profile_picture, hide_email, hide_phone, created_at FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            if not user:
                return jsonify({'message': 'User not found'}), 404

            # Convert datetime objects to string for JSON serialization
            if 'created_at' in user and isinstance(user['created_at'], datetime.datetime):
                user['created_at'] = user['created_at'].isoformat()

            return jsonify(user), 200
    except Exception as e:
        print(f"General error while fetching user information: {e}")
        return jsonify({'message': 'Server error, please try again later.'}), 500
    finally:
        if connection:
            connection.close()
def update_project_dates(cursor, project_id):
    """Updates project start and end dates based on its progress steps."""
    try:
        # Get all progress steps for the project
        cursor.execute("""
            SELECT MIN(start_date) AS earliest_start, MAX(end_date) AS latest_end
            FROM project_progress
            WHERE project_id = %s
        """, (project_id,))

        date_range = cursor.fetchone()

        if not date_range or (not date_range['earliest_start'] and not date_range['latest_end']):
            print(f"No progress steps found for project {project_id}")

            # Eğer hiç iş adımı kalmadıysa, projenin başlangıç ve bitiş tarihlerini sıfırla
            cursor.execute("""
                UPDATE projects
                SET start_date = NULL, end_date = NULL
                WHERE project_id = %s
            """, (project_id,))
            print(f"Project dates set to NULL for project {project_id} as no progress steps remain.")
            return True

        earliest_start = date_range['earliest_start']
        latest_end = date_range['latest_end']

        if earliest_start and latest_end:
            # Update project dates
            cursor.execute("""
                UPDATE projects
                SET start_date = %s, end_date = %s
                WHERE project_id = %s
            """, (earliest_start, latest_end, project_id))

            print(f"Project dates updated: project_id={project_id}, start={earliest_start}, end={latest_end}")
            return True
        else:
            print(f"Could not determine date range for project {project_id}")
            return False

    except Exception as e:
        print(f"Error in update_project_dates: {str(e)}")
        return False



@app.route('/api/users', methods=['GET'])
def get_all_users():
    """Retrieves a list of all users."""
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Get all user fields including new ones
            cursor.execute("SELECT id, fullname, email, phone, role, profile_picture, hide_email, hide_phone, created_at FROM users")
            users = cursor.fetchall()

            # Convert datetime objects to string for JSON serialization
            for user in users:
                if 'created_at' in user and isinstance(user['created_at'], datetime.datetime):
                    user['created_at'] = user['created_at'].isoformat()

            return jsonify(users), 200
    except pymysql.Error as e:
        print(f"Database error while fetching all users: {e}")
        return jsonify({'message': f'Database error occurred: {e.args[1]}'}), 500
    except Exception as e:
        print(f"General error while fetching all users: {e}")
        return jsonify({'message': 'Server error, please try again later.'}), 500
    finally:
        if connection:
            connection.close()

@app.route('/api/users/non-admin', methods=['GET'])
def get_non_admin_users():
    """Retrieves a list of all users excluding those with the 'Admin' role."""
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            sql = "SELECT id, fullname, email, phone, role, profile_picture, hide_email, hide_phone, created_at FROM users WHERE role != 'Admin' ORDER BY fullname"
            cursor.execute(sql)
            users = cursor.fetchall()

            # Convert datetime objects to string for JSON serialization
            for user in users:
                if 'created_at' in user and isinstance(user['created_at'], datetime.datetime):
                    user['created_at'] = user['created_at'].isoformat()

            return jsonify(users), 200
    except pymysql.Error as e:
        print(f"Database error while fetching non-admin users: {e}")
        return jsonify({'message': f'Database error occurred: {e.args[1]}'}), 500
    except Exception as e:
        print(f"General error while fetching non-admin users: {e}")
        return jsonify({'message': 'Server error, please try again later.'}), 500
    finally:
        if connection:
            connection.close()

@app.route('/api/users', methods=['POST'])
def add_user():
    """Adds a new user to the database (usually by an administrator)."""
    data = request.get_json()
    fullname = data.get('fullname')
    email = data.get('email')
    phone = data.get('phone', '')
    password = data.get('password')
    role = data.get('role', 'Employee') # Default position if not provided
    profile_picture = data.get('profile_picture')
    hide_email = data.get('hide_email', 0)
    hide_phone = data.get('hide_phone', 0)


    if not fullname or not email or not password or not role:
        return jsonify({'message': 'All fields are required!'}), 400

    onay = 1 # Approved by default for users added by administrator
    created_at = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    try:
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        connection = get_db_connection()
        with connection.cursor() as cursor:
            sql = """
            INSERT INTO users (fullname, email, phone, password, role, created_at, onay, profile_picture, hide_email, hide_phone)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (fullname, email, phone, hashed_password, role, created_at, onay, profile_picture, hide_email, hide_phone))
            connection.commit()
        return jsonify({'message': 'User successfully added!'}), 201
    except pymysql.Error as e:
        print(f"Database user addition error: {e}")
        if e.args[0] == 1062:
            return jsonify({'message': 'This email address is already in use.'}), 409
        return jsonify({'message': f'Database error occurred: {e.args[1]}'}), 500
    except Exception as e:
        print(f"General user addition error: {e}")
        return jsonify({'message': 'Server error, please try again later.'}), 500
    finally:
        if connection:
            connection.close()

@app.route('/api/user/email', methods=['PUT'])
def update_email():
    """Kullanıcının e-posta adresini günceller."""
    if 'user_id' not in session:
        return jsonify({'message': 'Lütfen giriş yapın.'}), 401

    data = request.get_json()
    new_email = data.get('email')
    user_id = session['user_id']

    if not new_email or not re.match(r'[^@]+@[^@]+\.[^@]+', new_email):
        return jsonify({'message': 'Geçerli bir e-posta adresi girin.'}), 400

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Yeni e-postanın başka bir kullanıcı tarafından kullanılıp kullanılmadığını kontrol et
            cursor.execute("SELECT id FROM users WHERE email = %s AND id != %s", (new_email, user_id))
            if cursor.fetchone():
                return jsonify({'message': 'Bu e-posta adresi zaten kullanılıyor.'}), 409

            # E-postayı güncelle
            cursor.execute("UPDATE users SET email = %s WHERE id = %s", (new_email, user_id))
            connection.commit()
        return jsonify({'message': 'E-posta adresiniz başarıyla güncellendi.'}), 200
    except pymysql.Error as e:
        print(f"E-posta güncellenirken veritabanı hatası: {e}")
        return jsonify({'message': 'Veritabanı hatası oluştu.'}), 500
    except Exception as e:
        print(f"E-posta güncellenirken genel hata: {e}")
        return jsonify({'message': 'Sunucu hatası oluştu.'}), 500
    finally:
        if connection:
            connection.close()

@app.route('/api/user/password', methods=['PUT'])
def update_password():
    """Kullanıcının şifresini günceller."""
    if 'user_id' not in session:
        return jsonify({'message': 'Lütfen giriş yapın.'}), 401

    data = request.get_json()
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    user_id = session['user_id']

    if not current_password or not new_password:
        return jsonify({'message': 'Tüm alanları doldurun.'}), 400

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Mevcut şifreyi doğrula
            cursor.execute("SELECT password FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            if not user or not bcrypt.checkpw(current_password.encode('utf-8'), user['password'].encode('utf-8')):
                return jsonify({'message': 'Mevcut şifreniz yanlış.'}), 403

            # Yeni şifreyi hash'le
            hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())

            # Yeni şifreyi veritabanında güncelle
            cursor.execute("UPDATE users SET password = %s WHERE id = %s", (hashed_password.decode('utf-8'), user_id))
            connection.commit()

        return jsonify({'message': 'Şifreniz başarıyla değiştirildi.'}), 200
    except pymysql.Error as e:
        print(f"Şifre güncellenirken veritabanı hatası: {e}")
        return jsonify({'message': 'Veritabanı hatası oluştu.'}), 500
    except Exception as e:
        print(f"Şifre güncellenirken genel hata: {e}")
        return jsonify({'message': 'Sunucu hatası oluştu.'}), 500
    finally:
        if connection:
            connection.close()
@app.route('/api/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """Update user information including role."""
    if 'user_id' not in session:
        return jsonify({"error": "Oturum açık değil."}), 401

    # Debug: Temporarily allow all authenticated users for testing
    # TODO: Restore admin-only access after testing
    if 'user_id' not in session:
        return jsonify({"error": "Oturum açık değil."}), 401

    data = request.get_json()
    if not data:
        return jsonify({"error": "Geçersiz veri."}), 400

    connection = None
    try:
        connection = get_db_connection()
        if not connection:
            return jsonify({"error": "Veritabanı bağlantısı kurulamadı."}), 500

        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # Check if user exists
            cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
            if not cursor.fetchone():
                return jsonify({"error": "Kullanıcı bulunamadı."}), 404

            # Update user fields
            update_fields = []
            update_values = []
            
            if 'fullname' in data:
                update_fields.append("fullname = %s")
                update_values.append(data['fullname'])
                
            if 'email' in data:
                update_fields.append("email = %s")
                update_values.append(data['email'])
                
            if 'role' in data:
                # Verify the role exists
                cursor.execute("SELECT id FROM yetki WHERE role_name = %s", (data['role'],))
                if not cursor.fetchone():
                    return jsonify({"error": "Geçersiz rol."}), 400
                update_fields.append("role = %s")
                update_values.append(data['role'])

            if not update_fields:
                return jsonify({"message": "Güncellenecek alan bulunamadı."}), 200

            # Add user_id to the values list
            update_values.append(user_id)
            
            # Build and execute the update query
            update_query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = %s"
            cursor.execute(update_query, update_values)
            connection.commit()

            return jsonify({"message": "Kullanıcı başarıyla güncellendi."}), 200

    except pymysql.Error as e:
        connection.rollback()
        print(f"Veritabanı hatası: {e}")
        return jsonify({"error": "Veritabanı hatası oluştu."}), 500
    except Exception as e:
        if connection:
            connection.rollback()
        print(f"Beklenmeyen hata: {e}")
        return jsonify({"error": "Beklenmeyen bir hata oluştu."}), 500
    finally:
        if connection:
            connection.close()

@app.route('/api/yetkitable')
def get_yetkitable():
    """Retrieves all roles except 'Admin' from the yetki table."""
    if 'user_id' not in session:
        return jsonify({"error": "Oturum açık değil."}), 401

    connection = None
    try:
        connection = get_db_connection()
        if not connection:
            return jsonify({"error": "Veritabanı bağlantısı kurulamadı."}), 500

        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # Admin rolünü hariç tutarak tüm rolleri getir
            sql = "SELECT * FROM yetki WHERE role_name != 'Admin' ORDER BY id"
            cursor.execute(sql)
            roles = cursor.fetchall()
            return jsonify(roles)

    except pymysql.Error as e:
        print(f"MySQL hatası: {e}")
        return jsonify({"error": "Veritabanı hatası oluştu."}), 500
    except Exception as e:
        print(f"Beklenmeyen hata: {e}")
        return jsonify({"error": "Beklenmeyen bir hata oluştu."}), 500
    finally:
        if connection:
            connection.close()
@app.route('/api/update-role', methods=['POST'])
def update_role():
    if 'user_id' not in session:
        return jsonify({"error": "Oturum açık değil."}), 401

    connection = None
    try:
        data = request.get_json()
        role_id = data.get('role_id')
        role_name = data.get('role_name')

        if not role_id or not role_name:
            return jsonify({"error": "Rol ID'si veya adı boş bırakılamaz."}), 400

        connection = get_db_connection()
        if not connection:
            return jsonify({"error": "Veritabanı bağlantısı kurulamadı."}), 500

        with connection.cursor() as cursor:
            # Aynı isimde başka bir rol var mı kontrol et
            cursor.execute("SELECT id FROM yetki WHERE role_name = %s AND id != %s", 
                         (role_name, role_id))
            if cursor.fetchone():
                return jsonify({"error": "Bu isimde bir rol zaten mevcut."}), 400

            # Rolü güncelle
            sql = "UPDATE yetki SET role_name = %s WHERE id = %s"
            cursor.execute(sql, (role_name, role_id))
            
            if cursor.rowcount == 0:
                return jsonify({"error": "Belirtilen rol bulunamadı."}), 404
                
            connection.commit()
            return jsonify({"message": "Rol başarıyla güncellendi."}), 200

    except pymysql.Error as e:
        if connection:
            connection.rollback()
        print(f"MySQL hatası: {e}")
        return jsonify({"error": f"Veritabanı hatası: {str(e)}"}), 500
    except Exception as e:
        if connection:
            connection.rollback()
        print(f"Beklenmeyen hata: {e}")
        return jsonify({"error": f"Beklenmeyen hata: {str(e)}"}), 500
    finally:
        if connection:
            connection.close()

@app.route('/api/delete-role/<int:role_id>', methods=['DELETE'])
def delete_role(role_id):
    if 'user_id' not in session:
        return jsonify({"error": "Oturum açık değil."}), 401

    connection = None
    try:
        connection = get_db_connection()
        if not connection:
            return jsonify({"error": "Veritabanı bağlantısı kurulamadı."}), 500

        with connection.cursor() as cursor:
            # Önce bu rolü kullanan kullanıcı var mı kontrol et
            cursor.execute("SELECT COUNT(*) as user_count FROM users WHERE role_id = %s", (role_id,))
            result = cursor.fetchone()
            
            if result and result['user_count'] > 0:
                return jsonify({"error": "Bu rolü kullanan kullanıcılar olduğu için silinemez."}), 400

            # Rolü sil
            cursor.execute("DELETE FROM yetki WHERE id = %s", (role_id,))
            
            if cursor.rowcount == 0:
                return jsonify({"error": "Silinecek rol bulunamadı."}), 404
                
            connection.commit()
            return jsonify({"message": "Rol başarıyla silindi."}), 200

    except pymysql.Error as e:
        if connection:
            connection.rollback()
        print(f"MySQL hatası: {e}")
        return jsonify({"error": f"Veritabanı hatası: {str(e)}"}), 500
    except Exception as e:
        if connection:
            connection.rollback()
        print(f"Beklenmeyen hata: {e}")
        return jsonify({"error": f"Beklenmeyen hata: {str(e)}"}), 500
    finally:
        if connection:
            connection.close()
@app.route('/api/roles', methods=['GET'])
def get_distinct_roles():
    """Retrieves all roles from the yetki table."""
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            sql = "SELECT DISTINCT role_name FROM yetki ORDER BY role_name"
            cursor.execute(sql)
            roles = [row['role_name'] for row in cursor.fetchall()]

        return jsonify(roles), 200
    except pymysql.Error as e:
        print(f"Database error while fetching roles: {e}")
        return jsonify({'message': f'Database error occurred: {e.args[1]}'}), 500
    except Exception as e:
        print(f"General error while fetching roles: {e}")
        return jsonify({'message': 'Server error, please try again later.'}), 500
    finally:
        if connection:
            connection.close()

@app.route('/api/calendar-events', methods=['GET'])
def get_calendar_events():
    """Retrieves tasks and projects for the calendar."""
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # Fetch tasks
            tasks_sql = """
                SELECT
                    id,
                    title,
                    description,
                    start,
                    end,
                    priority,
                    assigned_user_id,
                    created_by
                FROM tasks
            """
            cursor.execute(tasks_sql)
            tasks_data = cursor.fetchall()

            # Fetch projects
            projects_sql = """
                SELECT
                    project_id,
                    project_name,
                    description,
                    start_date,
                    end_date,
                    status,
                    project_manager_id
                FROM projects
            """
            cursor.execute(projects_sql)
            projects_data = cursor.fetchall()

            events = []

            # Convert tasks to FullCalendar format
            for task in tasks_data:
                # Öncelik rengini belirle - Türkçe çevirilerle uyumlu hale getirildi
                color = "#2ed573" # Varsayılan: Düşük Öncelik (Low)
                if task['priority'].lower() == "high":
                    color = "#ff4757" # Yüksek Öncelik (High)
                elif task['priority'].lower() == "medium":
                    color = "#ffa502" # Orta Öncelik (Medium)

                events.append({
                    'id': f"task-{task['id']}", # Add type to ID
                    'title': task['title'],
                    'start': task['start'].isoformat() if isinstance(task['start'], (datetime.datetime, datetime.date)) else task['start'],
                    'end': task['end'].isoformat() if isinstance(task['end'], (datetime.datetime, datetime.date)) else (task['end'] if task['end'] else None), # Handle None for end date
                    'color': color,
                    'type': 'task',
                    'extendedProps': {
                        'originalColor': color,
                        'priority': task['priority'],
                        'description': task['description'],
                        'assigned_user_id': task['assigned_user_id'],
                        'created_by': task['created_by'],
                        'id': task['id'], # Add original task ID here for detail modals
                        'title': task['title'], # Add title to extendedProps for consistency
                        'start': task['start'].isoformat() if isinstance(task['start'], (datetime.datetime, datetime.date)) else task['start'],
                        'end': task['end'].isoformat() if isinstance(task['end'], (datetime.datetime, datetime.date)) else (task['end'] if task['end'] else None) # Add end to extendedProps for consistency
                    }
                })

            # Convert projects to FullCalendar format
            for project in projects_data:
                # Color assignment based on project status - Türkçe statü isimleriyle uyumlu hale getirildi
                project_color = "#005c9d" # Default
                if project['status'] == 'Gecikmeli': # 'Delayed' yerine 'Gecikmeli'
                    project_color = "#ff4757" # Red
                elif project['status'] == 'Tamamlandı': # 'Completed' yerine 'Tamamlandı'
                    project_color = "#2ed573" # Green
                elif project['status'] == 'Aktif': # 'Active' yerine 'Aktif'
                    project_color = "#0980d3" # Blue
                elif project['status'] == 'Planlama Aşamasında': # 'Planning' yerine 'Planlama Aşamasında'
                    project_color = "#ffa502" # Orange (Örnek renk)

                events.append({
                    'id': f"project-{project['project_id']}", # Add type to ID
                    'title': f"Proje: {project['project_name']}",
                    'start': project['start_date'].isoformat() if isinstance(project['start_date'], (datetime.datetime, datetime.date)) else project['start_date'],
                    'end': project['end_date'].isoformat() if isinstance(project['end_date'], (datetime.datetime, datetime.date)) else (project['end_date'] if project['end_date'] else None), # Handle None for end date
                    'color': project_color,
                    'type': 'project',
                    'extendedProps': {
                        'originalColor': project_color,
                        'description': project['description'],
                        'status': project['status'],
                        'project_manager_id': project['project_manager_id'],
                        'id': project['project_id'], # Add original project ID here for detail modals
                        'project_name': project['project_name'], # Add project_name to extendedProps for consistency
                        'start': project['start_date'].isoformat() if isinstance(project['start_date'], (datetime.datetime, datetime.date)) else project['start_date'],
                        'end': project['end_date'].isoformat() if isinstance(project['end_date'], (datetime.datetime, datetime.date)) else (project['end_date'] if project['end_date'] else None) # Add end to extendedProps for consistency
                    }
                })

        return jsonify(events), 200
    except Exception as e:
        print(f"Error fetching calendar events: {e}")
        return jsonify({'message': 'Could not fetch calendar events.'}), 500
    finally:
        if connection:
            connection.close()

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    """Retrieves tasks, optionally filtered by assigned user."""
    assigned_user_id = request.args.get('assigned_user_id')
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            if assigned_user_id:
                sql = """
                    SELECT t.*, u.fullname AS assignee_name
                    FROM tasks t
                    LEFT JOIN users u ON t.assigned_user_id = u.id
                    WHERE t.assigned_user_id = %s
                    ORDER BY t.start ASC
                """
                cursor.execute(sql, (assigned_user_id,))
            else:
                sql = """
                    SELECT t.*, u.fullname AS assignee_name
                    FROM tasks t
                    LEFT JOIN users u ON t.assigned_user_id = u.id
                    ORDER BY t.start ASC
                """
                cursor.execute(sql)
            tasks = cursor.fetchall()
        return jsonify(tasks), 200
    except Exception as e:
        print(f"Error fetching tasks: {e}")
        return jsonify({'message': 'Could not fetch tasks.'}), 500
    finally:
        if connection:
            connection.close()

@app.route('/api/tasks', methods=['POST'])
def add_task():
    """Adds a new task to the database."""
    data = request.get_json()
    title = data.get('title')
    description = data.get('description')
    start = data.get('start')
    end = data.get('end')
    priority = data.get('priority', 'medium')
    assigned_user_id = int(data.get('assigned_user_id')) if data.get('assigned_user_id') else None
    created_by = int(data.get('created_by')) if data.get('created_by') else None

    if not all([title, start, assigned_user_id, created_by]):
        return jsonify({'message': 'Required fields are missing!'}), 400

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            sql = """
                INSERT INTO tasks (title, description, start, end, priority, assigned_user_id, created_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (title, description, start, end, priority, assigned_user_id, created_by))
            connection.commit()

            # Atayan kullanıcının adını al
            created_by_fullname = get_user_fullname_by_id(cursor, created_by)
            # Öncelik çevirisini al
            translated_priority = PRIORITY_TRANSLATIONS.get(priority.lower(), priority.capitalize())

            # Send notification to the newly assigned user
            send_notification(
                cursor, # Pass the cursor here
                assigned_user_id,
                "Yeni Görev Atandı",
                f"Size yeni bir görev atandı: '{title}'."
            )

            # Atanan kullanıcının e-posta adresini al ve e-posta gönder
            cursor.execute("SELECT email FROM users WHERE id = %s", (assigned_user_id,))
            assigned_user_email_info = cursor.fetchone()
            if assigned_user_email_info and assigned_user_email_info['email']:
                email_body = (
                    f"<p>Size yeni bir görev atandı:</p>"
                    f"<table>"
                    f"<tr><th>Görev Adı</th><td>{title}</td></tr>"
                    f"<tr><th>Açıklama</th><td>{description or 'Yok'}</td></tr>"
                    f"<tr><th>Başlangıç Tarihi</th><td>{format_datetime_for_email(start)}</td></tr>"
                    f"<tr><th>Bitiş Tarihi</th><td>{format_datetime_for_email(end)}</td></tr>"
                    f"<tr><th>Öncelik</th><td>{translated_priority}</td></tr>"
                    f"<tr><th>Görevi Atayan</th><td>{created_by_fullname}</td></tr>"
                    f"</table>"
                    f"<p>Detaylar için lütfen <a href='https://www.serotomasyon.tr'>SER Proje Takip</a> Uygulamasını kontrol edin.</p>"
                )
                send_email_notification(
                    assigned_user_email_info['email'],
                    "Yeni Görev Atandı - SERProjeTakip",
                    email_body
                )
            else:
                print(f"UYARI: Atanan kullanıcı {assigned_user_id} için e-posta adresi bulunamadı.")


        return jsonify({'message': 'Task successfully added!'}), 201
    except Exception as e:
        print(f"Error adding task: {e}")
        return jsonify({'message': 'Error adding task.'}), 500
    finally:
        if connection:
            connection.close()
# API to update an existing task - Güncellendi
@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    """Updates an existing task."""
    data = request.get_json()
    title = data.get('title')
    description = data.get('description')
    start = data.get('start')
    end = data.get('end')
    priority = data.get('priority', 'medium')
    new_assigned_user_id = int(data.get('assigned_user_id')) if data.get('assigned_user_id') else None
    created_by = int(data.get('created_by')) if data.get('created_by') else None # Bu, görevi ilk oluşturan kişi

    # Görevi güncelleyen kişinin ID'si (session'dan veya request body'den alınabilir)
    # Varsayılan olarak session'daki kullanıcıyı alalım veya isteğe bağlı olarak data'dan
    updated_by_user_id = session.get('user_id')
    if not updated_by_user_id and 'user_id' in data:
        updated_by_user_id = data.get('user_id')

    if not all([title, start, new_assigned_user_id, created_by]):
        return jsonify({'message': 'Required fields are missing!'}), 400

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Get the current assigned user of the task
            cursor.execute("SELECT assigned_user_id FROM tasks WHERE id = %s", (task_id,))
            existing_task = cursor.fetchone()
            old_assigned_user_id = existing_task['assigned_user_id'] if existing_task else None

            sql = """
                UPDATE tasks
                SET title=%s, description=%s, start=%s, end=%s, priority=%s, assigned_user_id=%s, created_by=%s
                WHERE id=%s
            """
            cursor.execute(sql, (title, description, start, end, priority, new_assigned_user_id, created_by, task_id))
            connection.commit()

            # Görevi güncelleyen kişinin adını al
            updated_by_fullname = get_user_fullname_by_id(cursor, updated_by_user_id)
            # Öncelik çevirisini al
            translated_priority = PRIORITY_TRANSLATIONS.get(priority.lower(), priority.capitalize())

            # If the assigned user changed, send notifications to old and new users
            if old_assigned_user_id and old_assigned_user_id != new_assigned_user_id:
                send_notification(
                    cursor, # Pass the cursor here
                    old_assigned_user_id,
                    "Görev Atama Değişti",
                    f"'{title}' adlı görev artık size atanmadı."
                )
                # Eski atanan kullanıcının e-posta adresini al ve e-posta gönder
                cursor.execute("SELECT email FROM users WHERE id = %s", (old_assigned_user_id,))
                old_assigned_user_email_info = cursor.fetchone()
                if old_assigned_user_email_info and old_assigned_user_email_info['email']:
                    old_assignee_email_body = (
                        f"<p>'{title}' başlıklı görev artık size atanmamıştır.</p>"
                        f"<table>"
                        f"<tr><th>Görevi Güncelleyen</th><td>{updated_by_fullname}</td></tr>"
                        f"</table>"
                        f"<p>Detaylar için lütfen <a href='https://www.serotomasyon.tr'>SER Proje Takip</a> Uygulamasını kontrol edin.</p>"
                    )
                    send_email_notification(
                        old_assigned_user_email_info['email'],
                        "Görev Atama Değişti - SERProjeTakip",
                        old_assignee_email_body
                    )
                else:
                    print(f"UYARI: Eski atanan kullanıcı {old_assigned_user_id} için e-posta adresi bulunamadı.")

            # Yeni atanan kullanıcıya bildirim gönder
            send_notification(
                cursor, # Pass the cursor here
                new_assigned_user_id,
                "Görev Güncellendi",
                f"Size atanmış görev güncellendi: '{title}'." # Mesaj güncellendi
            )
            # Yeni atanan kullanıcının e-posta adresini al ve e-posta gönder
            cursor.execute("SELECT email FROM users WHERE id = %s", (new_assigned_user_id,))
            new_assigned_user_email_info = cursor.fetchone()
            if new_assigned_user_email_info and new_assigned_user_email_info['email']:
                new_assignee_email_body = (
                    f"<p>Size atanmış olan '{title}' başlıklı görev güncellendi:</p>"
                    f"<table>"
                    f"<tr><th>Açıklama</th><td>{description or 'Yok'}</td></tr>"
                    f"<tr><th>Başlangıç Tarihi</th><td>{format_datetime_for_email(start)}</td></tr>"
                    f"<tr><th>Bitiş Tarihi</th><td>{format_datetime_for_email(end)}</td></tr>"
                    f"<tr><th>Öncelik</th><td>{translated_priority}</td></tr>"
                    f"<tr><th>Görevi Güncelleyen</th><td>{updated_by_fullname}</td></tr>"
                    f"</table>"
                    f"<p>Detaylar için lütfen <a href='https://www.serotomasyon.tr'>SER Proje Takip</a> Uygulamasını kontrol edin.</p>"
                )
                send_email_notification(
                    new_assigned_user_email_info['email'],
                    "Görev Güncellendi - SERProjeTakip",
                    new_assignee_email_body
                )
            else:
                print(f"UYARI: Yeni atanan kullanıcı {new_assigned_user_id} için e-posta adresi bulunamadı.")


        return jsonify({'message': 'Görev başarıyla güncellendi!'}), 200
    except Exception as e:
        print(f"Error updating task: {e}")
        return jsonify({'message': 'Error updating task.'}), 500
    finally:
        if connection:
            connection.close()

@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    """Deletes a task from the database."""
    # Get user_id from session, as DELETE requests might not have a body.
    user_id = session.get('user_id')

    if not user_id:
        # Return JSON error if user is not authenticated
        return jsonify({'message': 'User ID is missing. Please log in.'}), 401

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Get task information for notification and permission check
            cursor.execute("SELECT title, assigned_user_id, created_by FROM tasks WHERE id = %s", (task_id,))
            task_info = cursor.fetchone()

            if not task_info:
                return jsonify({'message': 'Task not found.'}), 404

            # Check if the current user is authorized to delete the task
            # User must be either the assigned user or the creator
            if not (user_id == task_info['assigned_user_id'] or user_id == task_info['created_by']):
                return jsonify({'message': 'You are not authorized to delete this task.'}), 403

            # Görevi silen kişinin adını al
            deleted_by_fullname = get_user_fullname_by_id(cursor, user_id)

            cursor.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
            connection.commit()

            # Send notification to the assigned user (if different from deleter)
            if user_id != task_info['assigned_user_id']:
                send_notification(
                    cursor, # Pass the cursor here
                    task_info['assigned_user_id'],
                    "Görev Silindi",
                    f"'{task_info['title']}' adlı görev size atanmıştı ve silindi."
                )
                # Atanan kullanıcının e-posta adresini al ve e-posta gönder
                cursor.execute("SELECT email FROM users WHERE id = %s", (task_info['assigned_user_id'],))
                assigned_user_email_info = cursor.fetchone()
                if assigned_user_email_info and assigned_user_email_info['email']:
                    assigned_user_email_body = (
                        f"<p>'{task_info['title']}' başlıklı görev size atanmıştı ve silindi.</p>"
                        f"<table>"
                        f"<tr><th>Görevi Silen</th><td>{deleted_by_fullname}</td></tr>"
                        f"</table>"
                        f"<p>Detaylar için lütfen <a href='https://www.serotomasyon.tr'>SER Proje Takip</a> Uygulamasını kontrol edin.</p>"
                    )
                    send_email_notification(
                        assigned_user_email_info['email'],
                        "Görev Silindi - SERProjeTakip",
                        assigned_user_email_body
                    )
                else:
                    print(f"UYARI: Atanan kullanıcı {task_info['assigned_user_id']} için e-posta adresi bulunamadı.")

            # If the creator is different from assigned user and deleter, notify creator too
            if user_id != task_info['created_by'] and task_info['created_by'] != task_info['assigned_user_id']:
                 send_notification(
                    cursor, # Pass the cursor here
                    task_info['created_by'],
                    "Görev Silindi",
                    f"Yönettiğiniz '{task_info['title']}' adlı görev silindi."
                )
                 # Oluşturan kullanıcının e-postasını al ve e-posta gönder
                 cursor.execute("SELECT email FROM users WHERE id = %s", (task_info['created_by'],))
                 creator_user_email_info = cursor.fetchone()
                 if creator_user_email_info and creator_user_email_info['email']:
                     creator_email_body = (
                         f"<p>Yönettiğiniz '{task_info['title']}' başlıklı görev silindi.</p>"
                         f"<table>"
                         f"<tr><th>Görevi Silen</th><td>{deleted_by_fullname}</td></tr>"
                         f"</table>"
                         f"<p>Detaylar için lütfen <a href='https://www.serotomasyon.tr'>SER Proje Takip</a> Uygulamasını kontrol edin.</p>"
                     )
                     send_email_notification(
                         creator_user_email_info['email'],
                         "Görev Silindi - SERProjeTakip",
                         creator_email_body
                     )
                 else:
                     print(f"UYARI: Oluşturan kullanıcı {task_info['created_by']} için e-posta adresi bulunamadı.")


        return jsonify({'message': 'Task successfully deleted!'}), 200
    except Exception as e:
        print(f"Error deleting task: {e}")
        return jsonify({'message': 'Error deleting task.'}), 500
    finally:
        if connection: # Hata düzeltmesi: connection'ın varlığını kontrol et
            connection.close()

@app.route('/api/manager-stats')
def manager_stats():
    """Retrieves statistics related to project managers' performance."""
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = """
            SELECT
                p.project_manager_id,
                u.fullname as manager_name,
                COUNT(DISTINCT p.project_id) AS total_projects,
                SUM(CASE
                        WHEN p.status = 'Completed' AND (
                            SELECT SUM(pr.delay_days) + SUM(pr.custom_delay_days)
                            FROM project_progress pr
                            WHERE pr.project_id = p.project_id
                        ) IS NULL OR (
                            SELECT SUM(pr.delay_days) + SUM(pr.custom_delay_days)
                            FROM project_progress pr
                            WHERE pr.project_id = p.project_id
                        ) = 0
                    THEN 1
                    ELSE 0
                END) AS on_time_projects,
                SUM(CASE
                        WHEN (
                            SELECT SUM(pr.delay_days) + SUM(pr.custom_delay_days)
                            FROM project_progress pr
                            WHERE pr.project_id = p.project_id
                        ) > 0
                    THEN 1
                    ELSE 0
                END) AS delayed_projects,
                (SELECT IFNULL(SUM(pr.delay_days), 0) + IFNULL(SUM(pr.custom_delay_days), 0)
                 FROM project_progress pr
                 WHERE pr.project_id IN (
                     SELECT project_id FROM projects WHERE project_manager_id = p.project_manager_id
                 )
                ) AS total_delay_days,
                AVG(DATEDIFF(p.end_date, p.start_date)) AS avg_project_duration
            FROM projects p
            LEFT JOIN users u ON u.id = p.project_manager_id
            GROUP BY p.project_manager_id, u.fullname
            """
            cursor.execute(sql)
            result = cursor.fetchall()
            return jsonify(result)
    finally:
        if connection:
            connection.close()

@app.route('/api/project-status-stats', methods=['GET'])
def get_project_status_stats():
    """Get project status statistics for charts"""
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Güncellenmiş sorgu: İngilizce statüleri Türkçe kategorilere dönüştür
            sql = """
                SELECT
                    CASE
                        WHEN status = 'Completed' THEN 'Tamamlandı'
                        WHEN status IN ('Active', 'Active (Work Delayed)') THEN 'Devam Ediyor'
                        WHEN status IN ('Delayed', 'Active (Work Delayed)') THEN 'Gecikti'
                        WHEN status = 'Planning' THEN 'Planlama'
                        ELSE 'Diğer'
                    END as status_category,
                    COUNT(*) as count
                FROM projects
                GROUP BY status_category
                ORDER BY
                    CASE status_category
                        WHEN 'Tamamlandı' THEN 1
                        WHEN 'Devam Ediyor' THEN 2
                        WHEN 'Gecikti' THEN 3
                        WHEN 'Planlama' THEN 4
                        ELSE 5
                    END
            """
            cursor.execute(sql)
            results = cursor.fetchall()

            # Varsayılan değerlerle sözlük oluştur
            status_counts = {
                'Tamamlandı': 0,
                'Devam Ediyor': 0,
                'Gecikti': 0,
                'Planlama': 0
            }

            for row in results:
                status_category = row[0]
                count = row[1]
                if status_category in status_counts:
                    status_counts[status_category] = count

            return jsonify({
                'labels': list(status_counts.keys()),
                'data': list(status_counts.values())
            }), 200

    except pymysql.Error as e:
        print(f"Database error while fetching project status stats: {e}")
        return jsonify({'message': f'Veritabanı hatası: {e.args[1]}'}), 500
    except Exception as e:
        print(f"General error while fetching project status stats: {e}")
        return jsonify({'message': 'Sunucu hatası, lütfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()

def _check_and_notify_completed_steps(cursor):
    
    try:
        today = datetime.date.today()

        # Tüm Admin kullanıcılarının ID'lerini ve e-posta adreslerini al
        cursor.execute("SELECT id, email FROM users WHERE role = 'Admin'")
        admin_users_info = cursor.fetchall()
        admin_ids = [user['id'] for user in admin_users_info]
        admin_emails = [user['email'] for user in admin_users_info if user['email']]

        print(f"DEBUG: Admin ID'ler: {admin_ids}")
        print(f"DEBUG: Admin E-postaları: {admin_emails}")

        if not admin_ids:
            print("UYARI: Yönetici (Admin) kullanıcısı bulunamadı. Yöneticiye bildirim/e-posta gönderilemeyecek.")

        # Bitiş tarihi bugün veya geçmiş olan ve henüz bildirim gönderilmemiş iş adımlarını bul
        sql = """
        SELECT
            pp.progress_id,
            pp.title AS step_name,
            pp.end_date,
            p.project_name,
            p.project_id,
            p.project_manager_id
        FROM
            project_progress pp
        JOIN
            projects p ON pp.project_id = p.project_id
        WHERE
            pp.end_date <= %s AND pp.completion_notified = 0
        """
        cursor.execute(sql, (today,))
        completed_steps = cursor.fetchall()

        if not completed_steps:
            print("Giriş sırasında biten ve bildirim bekleyen iş adımı bulunamadı.")
            return

        print(f"Giriş sırasında biten iş adımları bulunuyor: {len(completed_steps)}")

        for step in completed_steps:
            progress_id = step['progress_id']
            step_name = step['step_name']
            project_name = step['project_name']
            project_manager_id = step['project_manager_id']
            step_end_date = step['end_date'].strftime('%d.%m.%Y')

            notification_title = "İş Adımı Tamamlandı"
            notification_message = f"'{project_name}' projesindeki '{step_name}' iş adımı planlanan bitiş tarihine ({step_end_date}) ulaştı."

            # Proje yöneticisine bildirim gönder
            if project_manager_id:
                send_notification(cursor, project_manager_id, notification_title, notification_message)
                # Proje yöneticisinin e-postasını al ve e-posta gönder
                cursor.execute("SELECT email FROM users WHERE id = %s", (project_manager_id,))
                manager_email_info = cursor.fetchone()
                if manager_email_info and manager_email_info['email']:
                    email_body = (
                        f"<p>'{project_name}' projesindeki '{step_name}' iş adımı planlanan bitiş tarihine ({step_end_date}) ulaştı.</p>"
                        f"<p>Detaylar için lütfen <a href='https://www.serotomasyon.tr'>SER Proje Takip</a> Uygulamasını kontrol edin.</p>"
                    )
                    send_email_notification(
                        manager_email_info['email'],
                        notification_title + " - SERProjeTakip",
                        email_body
                    )
                else:
                    print(f"UYARI: Proje yöneticisi {project_manager_id} için e-posta adresi bulunamadı.")
            else:
                print(f"UYARI: Proje '{project_name}' için proje yöneticisi bulunamadı. Proje yöneticisine bildirim/e-posta gönderilemedi.")

            # Tüm yöneticilere bildirim gönder ve e-posta gönder
            if admin_ids:
                for admin_id in admin_ids:
                    send_notification(cursor, admin_id, notification_title, notification_message)
                for admin_email in admin_emails:
                    email_body = (
                        f"<p>'{project_name}' projesindeki '{step_name}' iş adımı planlanan bitiş tarihine ({step_end_date}) ulaştı.</p>"
                        f"<p>Detaylar için lütfen <a href='https://www.serotomasyon.tr'>SER Proje Takip</a> Uygulamasını kontrol edin.</p>"
                    )
                    send_email_notification(
                        admin_email,
                        notification_title + " - SERProjeTakip",
                        email_body
                    )
            else:
                print(f"UYARI: Yöneticiye bildirim/e-posta gönderilemedi (Admin ID/E-posta bulunamadı).")

            # İş adımının completion_notified durumunu güncelle
            cursor.execute(
                "UPDATE project_progress SET completion_notified = 1 WHERE progress_id = %s",
                (progress_id,)
            )
            print(f"İş adımı {progress_id} için bildirim gönderildi ve 'completion_notified' güncellendi.")

        # Not: Bu fonksiyonun çağrıldığı yerde (login_user) commit işlemi yapılacaktır.
        # Burada ayrı bir commit yapmaya gerek yok.

    except pymysql.Error as e:
        print(f"Veritabanı hatası (_check_and_notify_completed_steps): {e}")
        # Hata durumunda rollback, çağıran fonksiyonda ele alınmalı
    except Exception as e:
        print(f"Genel hata (_check_and_notify_completed_steps): {e}")
        traceback.print_exc()

            
def check_and_notify_completed_steps():
    """
    Her gün 00:10'da çalışacak olan zamanlanmış görev fonksiyonu.
    Bitiş tarihi geçmiş ve tamamlanmamış iş adımlarını bulur ve mail gönderir.
    """
    print("Zamanlanmış görev başlatıldı: Tamamlanmamış iş adımları kontrol ediliyor...")
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Bugünden önce bitiş tarihi olan ve henüz tamamlanmamış (real_end_date NULL olan) adımları bul
            sql = """
                SELECT progress_id
                FROM project_progress
                WHERE end_date < CURDATE()
                AND real_end_date IS NULL
                AND completion_notified = 0
            """
            cursor.execute(sql)
            steps_to_notify = cursor.fetchall()

            for step in steps_to_notify:
                progress_id = step['progress_id']
                notify_on_step_completion_or_update(progress_id, is_update=False)

                # Bildirim gönderildikten sonra `completion_notified` flag'ini güncelle
                cursor.execute("UPDATE project_progress SET completion_notified = 1 WHERE progress_id = %s", (progress_id,))

            connection.commit()
            print(f"DEBUG: {len(steps_to_notify)} adet tamamlanmamış iş adımı için bildirim gönderildi.")

    except Exception as e:
        print(f"Zamanlanmış görevde hata: {e}")
        traceback.print_exc()
    finally:
        if connection:
            connection.close()
# Endpoint to list all work progress headers
@app.route('/api/work-progress-headers', methods=['GET'])
def list_work_progress_headers():
    try:
        with get_db_connection() as conn:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute("""
                    SELECT id, title, description, is_active, created_at, updated_at
                    FROM work_progress_headers
                    ORDER BY title
                """)
                headers = cursor.fetchall()
                return jsonify(headers)
    except Exception as e:
        print(f"Error listing work progress headers: {str(e)}")
        return jsonify({"error": "İş gidişat başlıkları listelenirken bir hata oluştu"}), 500

# Endpoint to add a new work progress header
@app.route('/api/work-progress-headers', methods=['POST'])
def create_work_progress_header():
    if 'user_id' not in session:
        return jsonify({"error": "Oturum açık değil"}), 401

    data = request.get_json()
    if not data or 'title' not in data:
        return jsonify({"error": "Başlık alanı zorunludur"}), 400

    title = data.get('title', '').strip()
    description = data.get('description', '').strip()
    is_active = data.get('is_active', True)

    if not title:
        return jsonify({"error": "Başlık boş olamaz"}), 400

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO work_progress_headers 
                    (title, description, is_active, created_by)
                    VALUES (%s, %s, %s, %s)
                """, (title, description, is_active, session['user_id']))
                conn.commit()
                return jsonify({
                    "message": "Başlık başarıyla eklendi",
                    "id": cursor.lastrowid
                }), 201
    except Exception as e:
        print(f"Error creating work progress header: {str(e)}")
        return jsonify({"error": "Başlık eklenirken bir hata oluştu"}), 500

@app.route('/api/work-progress-headers/<int:header_id>', methods=['DELETE'])
def delete_work_progress_header(header_id):
    if 'user_id' not in session:
        return jsonify({"error": "Oturum açık değil"}), 401

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # First check if the header exists
                cursor.execute("SELECT id FROM work_progress_headers WHERE id = %s", (header_id,))
                if not cursor.fetchone():
                    return jsonify({"error": "Başlık bulunamadı"}), 404

                # Delete the header
                cursor.execute("DELETE FROM work_progress_headers WHERE id = %s", (header_id,))
                conn.commit()
                return jsonify({"message": "Başlık başarıyla silindi"}), 200
    except Exception as e:
        print(f"Error deleting work progress header: {str(e)}")
        return jsonify({"error": "Başlık silinirken bir hata oluştu"}), 500
@app.route('/api/work-progress-headers/<int:header_id>', methods=['PUT'])
@app.route('/api/work-progress-headers/<int:header_id>', methods=['PUT'])
def update_work_progress_header(header_id):
    if 'user_id' not in session:
        return jsonify({"error": "Oturum açık değil"}), 401

    data = request.get_json()
    if not data or 'title' not in data:
        return jsonify({"error": "Başlık alanı zorunludur"}), 400

    title = data.get('title', '').strip()
    description = data.get('description', '').strip()
    is_active = data.get('is_active', True)

    if not title:
        return jsonify({"error": "Başlık boş olamaz"}), 400

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # Check if header exists
                cursor.execute("SELECT id FROM work_progress_headers WHERE id = %s", (header_id,))
                if not cursor.fetchone():
                    return jsonify({"error": "Başlık bulunamadı"}), 404

                # Update the header
                cursor.execute("""
                    UPDATE work_progress_headers 
                    SET title = %s, 
                        description = %s, 
                        is_active = %s,
                        updated_at = NOW()
                    WHERE id = %s
                """, (title, description, is_active, header_id))
                conn.commit()
                return jsonify({"message": "Başlık başarıyla güncellendi"}), 200
    except Exception as e:
        print(f"Error updating work progress header: {str(e)}")
        return jsonify({"error": "Başlık güncellenirken bir hata oluştu"}), 500
@app.route('/api/work-progress-headers/<int:header_id>', methods=['GET'])
def get_work_progress_header(header_id):
    try:
        with get_db_connection() as conn:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute("""
                    SELECT id, title, description, is_active, created_at, updated_at
                    FROM work_progress_headers
                    WHERE id = %s
                """, (header_id,))
                header = cursor.fetchone()
                if not header:
                    return jsonify({"error": "Başlık bulunamadı"}), 404
                return jsonify(header)
    except Exception as e:
        print(f"Error fetching work progress header: {str(e)}")
        return jsonify({"error": "Başlık getirilirken bir hata oluştu"}), 500
# In app.py
@app.route('/api/work-progress-headers/active', methods=['GET'])
def get_active_work_progress_headers():
    try:
        with get_db_connection() as conn:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute("""
                    SELECT id, title 
                    FROM work_progress_headers 
                    WHERE is_active = 1
                    ORDER BY title
                """)
                headers = cursor.fetchall()
                return jsonify(headers)
    except Exception as e:
        print(f"Error fetching active work progress headers: {str(e)}")
        return jsonify({"error": "Başlıklar getirilirken bir hata oluştu"}), 500

# app.py dosyasına eklenmesi gereken kod bloğu

@app.route('/api/revision-requests', methods=['POST'])
def handle_revision_request():
    """
    Handles revision requests from the frontend and saves them to the database.
    """
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Authentication required. Please log in.'}), 401

    data = request.get_json()
    project_id = data.get('project_id')
    progress_id = data.get('progress_id')
    title = data.get('title')
    message = data.get('message')
    requester_user_id = session.get('user_id')
    
    # Check for required fields
    if not all([project_id, progress_id, title, message, requester_user_id]):
        return jsonify({'success': False, 'message': 'Missing required fields.'}), 400

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Check if the progress step is valid and belongs to the project
            # NOTE: We've changed the column name from `id` to `progress_id`
            # to match your table's schema. This was likely the cause of the database error.
            cursor.execute(
                "SELECT progress_id FROM project_progress WHERE progress_id = %s AND project_id = %s",
                (progress_id, project_id)
            )
            if not cursor.fetchone():
                return jsonify({'success': False, 'message': 'Geçersiz proje veya ilerleme adımı ID.'}), 404
                
            # Check if there is an open revision request for the same progress step
            cursor.execute(
                "SELECT id FROM revision_requests WHERE progress_id = %s AND status = 'pending'",
                (progress_id)
            )
            if cursor.fetchone():
                return jsonify({'success': False, 'message': 'Bu adım için açık bir revizyon talebi zaten mevcut.'}), 409

            # Insert the new revision request into the database
            cursor.execute(
                """
                INSERT INTO revision_requests (project_id, progress_id, requested_by, title, message)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (project_id, progress_id, requester_user_id, title, message)
            )
            connection.commit()
            
            return jsonify({'success': True, 'message': 'Revizyon talebi başarıyla gönderildi.'}), 201

    except pymysql.Error as e:
        print(f"Database error during revision request: {e}")
        if connection:
            connection.rollback()
        return jsonify({'success': False, 'message': 'A database error occurred.'}), 500
    except Exception as e:
        print(f"General error during revision request: {e}")
        if connection:
            connection.rollback()
        return jsonify({'success': False, 'message': 'An internal server error occurred.'}), 500
    finally:
        if connection:
            connection.close()
@app.route('/api/revision-requests', methods=['GET'])
def get_revision_requests():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Oturum açmanız gerekiyor'}), 401

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # First, try a simple query to check connection
            cursor.execute("SELECT 1 as test")
            test = cursor.fetchone()
            print("Test query result:", test)  # Check if basic query works
            
            # Then try the actual query
            cursor.execute("""
                SELECT 
                    rr.id,
                    rr.project_id,
                    rr.progress_id,
                    rr.title,
                    rr.message,
                    rr.status,
                    rr.created_at
                FROM revision_requests rr
                ORDER BY rr.created_at DESC
                LIMIT 10  # Limit results for testing
            """)
            revisions = cursor.fetchall()
            print("Revisions found:", revisions)  # Debug output
            
            return jsonify({
                'success': True,
                'revisions': revisions
            })
            
    except Exception as e:
        print("Error in get_revision_requests:", str(e))  # Print to console
        import traceback
        traceback.print_exc()  # Print full traceback
        return jsonify({
            'success': False, 
            'message': 'Bir hata oluştu',
            'error': str(e)
        }), 500
    finally:
        if connection:
            connection.close()
# Bu kod, `revision_requests` tablosu oluşturulduktan sonra kullanılmalıdır.
# `projeler.html` dosyasından gelen `title` ve `message` alanlarını doğru şekilde işler.
@app.route('/api/progress/<int:progress_id>/complete', methods=['POST'])
def complete_progress_step(progress_id):
    data = request.get_json()
    is_completed = data.get('is_completed', False)
    project_id = data.get('project_id')
    
    if not project_id:
        return jsonify({'success': False, 'message': 'Proje ID zorunludur'}), 400
    
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # İş adımının gerçekten bu projeye ait olduğunu kontrol et
            cursor.execute(
                "SELECT progress_id FROM project_progress WHERE progress_id = %s AND project_id = %s",
                (progress_id, project_id)
            )
            if not cursor.fetchone():
                return jsonify({'success': False, 'message': 'Geçersiz iş adımı veya proje ID'}), 404
            
            # İş adımını güncelle
            cursor.execute(
                "UPDATE project_progress SET is_completed = %s WHERE progress_id = %s",
                (1 if is_completed else 0, progress_id)
            )
            
            # Proje durumunu güncelle
            determine_and_update_project_status(cursor, project_id)
            
            connection.commit()
            return jsonify({
                'success': True, 
                'message': 'İş adımı başarıyla güncellendi',
                'is_completed': is_completed
            })
            
    except Exception as e:
        print(f"İş adımı güncellenirken hata: {e}")
        if connection:
            connection.rollback()
        return jsonify({
            'success': False, 
            'message': f'İş adımı güncellenirken bir hata oluştu: {str(e)}'
        }), 500
        
    finally:
        if connection:
            connection.close()