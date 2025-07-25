# app.py
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import pymysql.cursors
import bcrypt
import os
import json
import datetime
import dotenv
from dotenv import load_dotenv
import urllib.parse
import re # Yeni eklendi: Düzenli ifadeler için

load_dotenv()

app = Flask(__name__)
CORS(app) # CORS'u tüm uygulama için etkinleştir

# Veritabanı bağlantı bilgileri
DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')

def get_db_connection():
    """Veritabanı bağlantısı kurar ve döndürür."""
    try:
        return pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            cursorclass=pymysql.cursors.DictCursor # Sözlük olarak sonuç döndürmesi için
        )
    except Exception as e:
        print(f"Veritabanı bağlantı hatası: {e}")
        return None

def create_notifications_table():
    """Bildirimler tablosunu oluşturur eğer yoksa."""
    connection = get_db_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
                sql = """
                CREATE TABLE IF NOT EXISTS notifications (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    title VARCHAR(255) NOT NULL,
                    message TEXT NOT NULL,
                    is_read BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
                """
                cursor.execute(sql)
            connection.commit()
            print("Notifications tablosu başarıyla kontrol edildi/oluşturuldu.")
        except Exception as e:
            print(f"Notifications tablosu oluşturulurken hata oluştu: {e}")
        finally:
            connection.close()

def create_tasks_table():
    """Görevler tablosunu oluşturur eğer yoksa."""
    connection = get_db_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
                sql = """
                CREATE TABLE IF NOT EXISTS tasks (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    project_id INT,
                    assigned_to_user_id INT,
                    title VARCHAR(255) NOT NULL,
                    description TEXT,
                    due_date DATE,
                    status VARCHAR(50) DEFAULT 'Beklemede',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE,
                    FOREIGN KEY (assigned_to_user_id) REFERENCES users(id) ON DELETE SET NULL
                ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
                """
                cursor.execute(sql)
            connection.commit()
            print("Tasks tablosu başarıyla kontrol edildi/oluşturuldu.")
        except Exception as e:
            print(f"Tasks tablosu oluşturulurken hata oluştu: {e}")
        finally:
            connection.close()

# Uygulama başlangıcında tabloları oluştur
with app.app_context():
    create_notifications_table()
    create_tasks_table() # tasks tablosunun da var olduğundan emin olalım

@app.route('/')
def serve_login_page():
    """Kök URL'ye (/) gelen istekleri login.html sayfasına yönlendirir."""
    return render_template('login.html')

@app.route('/index.html')
def serve_index_page():
    """/index.html URL'ye gelen istekleri index.html sayfasına yönlendirir."""
    return render_template('index.html')

@app.route('/ayarlar.html')
def serve_ayarlar_page():
    """/ayarlar.html URL'ye gelen istekleri ayarlar.html sayfasına yönlendirir."""
    return render_template('ayarlar.html')

@app.route('/kayitonay.html')
def serve_kayitonay_page():
    """/kayitonay.html URL'ye gelen istekleri kayitonay.html sayfasına yönlendirir."""
    return render_template('kayitonay.html')

@app.route('/musteriler.html')
def serve_musteriler_page():
    """/musteriler.html URL'ye gelen istekleri musteriler.html sayfasına yönlendirir."""
    return render_template('musteriler.html')

@app.route('/proje_ekle.html')
def serve_proje_ekle_page():
    """/proje_ekle.html URL'ye gelen istekleri proje_ekle.html sayfasına yönlendirir."""
    return render_template('proje_ekle.html')

@app.route('/projeler.html')
def serve_projeler_page():
    """/projeler.html URL'ye gelen istekleri projeler.html sayfasına yönlendirir."""
    return render_template('projeler.html')

@app.route('/raporlar.html')
def serve_raporlar_page():
    """/raporlar.html URL'ye gelen istekleri raporlar.html sayfasına yönlendirir."""
    return render_template('raporlar.html')

@app.route('/sifre_sifirlama.html')
def serve_sifre_sifirlama_page():
    """/sifre_sifirlama.html URL'ye gelen istekleri sifre_sifirlama.html sayfasına yönlendirir."""
    return render_template('sifre_sifirlama.html')

@app.route('/takvim.html')
def serve_takvim_page():
    """/takvim.html URL'ye gelen istekleri takvim.html sayfasına yönlendirir."""
    return render_template('takvim.html')

@app.route('/bildirim.html')
def serve_bildirim_page():
    """/bildirim.html URL'ye gelen istekleri bildirim.html sayfasına yönlendirir."""
    return render_template('bildirim.html')

# Bildirim yardımcı fonksiyonu
def add_notification(user_id, title, message):
    """Veritabanına yeni bir bildirim ekler."""
    connection = get_db_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
                sql = "INSERT INTO notifications (user_id, title, message) VALUES (%s, %s, %s)"
                cursor.execute(sql, (user_id, title, message))
            connection.commit()
            print(f"Bildirim eklendi: Kullanıcı ID: {user_id}, Başlık: {title}")
            return True
        except Exception as e:
            print(f"Bildirim eklenirken hata oluştu: {e}")
            return False
        finally:
            connection.close()

# Kullanıcıya özel bildirimleri getiren API
@app.route('/api/notifications', methods=['GET'])
def get_notifications():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"message": "Kullanıcı ID'si gerekli"}), 400

    connection = get_db_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
                sql = "SELECT id, user_id, title, message, is_read, created_at FROM notifications WHERE user_id = %s ORDER BY created_at DESC"
                cursor.execute(sql, (user_id,))
                notifications = cursor.fetchall()
                # Datetime objelerini stringe çevir
                for notification in notifications:
                    if isinstance(notification['created_at'], datetime.datetime):
                        notification['created_at'] = notification['created_at'].isoformat()
                return jsonify(notifications), 200
        except Exception as e:
            print(f"Bildirimler çekilirken hata oluştu: {e}")
            return jsonify({"message": "Bildirimler çekilirken bir hata oluştu."}), 500
        finally:
            connection.close()
    return jsonify({"message": "Veritabanı bağlantı hatası."}), 500

# Okunmamış bildirim sayısını getiren API
@app.route('/api/notifications/unread-count', methods=['GET'])
def get_unread_notification_count():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"message": "Kullanıcı ID'si gerekli"}), 400

    connection = get_db_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
                sql = "SELECT COUNT(*) AS unread_count FROM notifications WHERE user_id = %s AND is_read = FALSE"
                cursor.execute(sql, (user_id,))
                result = cursor.fetchone()
                return jsonify({"unread_count": result['unread_count']}), 200
        except Exception as e:
            print(f"Okunmamış bildirim sayısı çekilirken hata oluştu: {e}")
            return jsonify({"message": "Okunmamış bildirim sayısı çekilirken bir hata oluştu."}), 500
        finally:
            connection.close()
    return jsonify({"message": "Veritabanı bağlantı hatası."}), 500

# Yeni bildirim ekleyen API
@app.route('/api/notifications', methods=['POST'])
def create_notification_api():
    data = request.get_json()
    user_id = data.get('user_id')
    title = data.get('title')
    message = data.get('message')

    if not all([user_id, title, message]):
        return jsonify({"message": "Eksik bilgi: user_id, title ve message gerekli."}), 400

    if add_notification(user_id, title, message):
        return jsonify({"message": "Bildirim başarıyla eklendi."}), 201
    return jsonify({"message": "Bildirim eklenirken bir hata oluştu."}), 500

# Belirli bir bildirimi okunmuş olarak işaretleyen API
@app.route('/api/notifications/<int:notification_id>/read', methods=['PUT'])
def mark_notification_as_read(notification_id):
    user_id = request.args.get('user_id') # Güvenlik için user_id'yi de kontrol et
    if not user_id:
        return jsonify({"message": "Kullanıcı ID'si gerekli"}), 400

    connection = get_db_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
                sql = "UPDATE notifications SET is_read = TRUE WHERE id = %s AND user_id = %s"
                cursor.execute(sql, (notification_id, user_id))
            connection.commit()
            if cursor.rowcount > 0:
                return jsonify({"message": "Bildirim okunmuş olarak işaretlendi."}), 200
            return jsonify({"message": "Bildirim bulunamadı veya yetkiniz yok."}), 404
        except Exception as e:
            print(f"Bildirim okunmuş olarak işaretlenirken hata oluştu: {e}")
            return jsonify({"message": "Bildirim okunmuş olarak işaretlenirken bir hata oluştu."}), 500
        finally:
            connection.close()
    return jsonify({"message": "Veritabanı bağlantı hatası."}), 500

# Tüm bildirimleri okunmuş olarak işaretleyen API
@app.route('/api/notifications/mark_all_read', methods=['PUT'])
def mark_all_notifications_as_read():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"message": "Kullanıcı ID'si gerekli"}), 400

    connection = get_db_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
                sql = "UPDATE notifications SET is_read = TRUE WHERE user_id = %s AND is_read = FALSE"
                cursor.execute(sql, (user_id,))
            connection.commit()
            return jsonify({"message": f"{cursor.rowcount} bildirim okunmuş olarak işaretlendi."}), 200
        except Exception as e:
            print(f"Tüm bildirimler okunmuş olarak işaretlenirken hata oluştu: {e}")
            return jsonify({"message": "Tüm bildirimler okunmuş olarak işaretlenirken bir hata oluştu."}), 500
        finally:
            connection.close()
    return jsonify({"message": "Veritabanı bağlantı hatası."}), 500

# Belirli bir bildirimi silen API
@app.route('/api/notifications/<int:notification_id>', methods=['DELETE'])
def delete_notification(notification_id):
    user_id = request.args.get('user_id') # Güvenlik için user_id'yi de kontrol et
    if not user_id:
        return jsonify({"message": "Kullanıcı ID'si gerekli"}), 400

    connection = get_db_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
                sql = "DELETE FROM notifications WHERE id = %s AND user_id = %s"
                cursor.execute(sql, (notification_id, user_id))
            connection.commit()
            if cursor.rowcount > 0:
                return jsonify({"message": "Bildirim başarıyla silindi."}), 200
            return jsonify({"message": "Bildirim bulunamadı veya yetkiniz yok."}), 404
        except Exception as e:
            print(f"Bildirim silinirken hata oluştu: {e}")
            return jsonify({"message": "Bildirim silinirken bir hata oluştu."}), 500
        finally:
            connection.close()
    return jsonify({"message": "Veritabanı bağlantı hatası."}), 500

# Okunmuş tüm bildirimleri silen API
@app.route('/api/notifications/delete_all_read', methods=['DELETE'])
def delete_all_read_notifications():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"message": "Kullanıcı ID'si gerekli"}), 400

    connection = get_db_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
                sql = "DELETE FROM notifications WHERE user_id = %s AND is_read = TRUE"
                cursor.execute(sql, (user_id,))
            connection.commit()
            return jsonify({"message": f"{cursor.rowcount} okunmuş bildirim başarıyla silindi."}), 200
        except Exception as e:
            print(f"Okunmuş bildirimler silinirken hata oluştu: {e}")
            return jsonify({"message": "Okunmuş bildirimler silinirken bir hata oluştu."}), 500
        finally:
            connection.close()
    return jsonify({"message": "Veritabanı bağlantı hatası."}), 500


# Mevcut API endpoint'lerine bildirim entegrasyonu
@app.route('/api/projects', methods=['POST'])
def add_project():
    data = request.get_json()
    project_name = data.get('project_name')
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    status = data.get('status')
    project_manager_id = data.get('project_manager_id')
    customer_id = data.get('customer_id')
    description = data.get('description')
    budget = data.get('budget')
    currency = data.get('currency')
    assigned_users = data.get('assigned_users', []) # Yeni: Atanan kullanıcılar listesi

    if not all([project_name, start_date, end_date, status, project_manager_id, customer_id]):
        return jsonify({"message": "Eksik bilgi: proje adı, başlangıç/bitiş tarihi, durum, proje yöneticisi ve müşteri ID'si gerekli."}), 400

    connection = get_db_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
                # Proje ekleme
                sql = """
                INSERT INTO projects (project_name, start_date, end_date, status, project_manager_id, customer_id, description, budget, currency)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(sql, (project_name, start_date, end_date, status, project_manager_id, customer_id, description, budget, currency))
                project_id = cursor.lastrowid

                # Proje atanan kullanıcıları kaydetme
                if assigned_users:
                    for user_id in assigned_users:
                        assign_sql = "INSERT INTO project_assignments (project_id, user_id) VALUES (%s, %s)"
                        cursor.execute(assign_sql, (project_id, user_id))

                connection.commit()

                # Bildirim gönderme: Proje yöneticisine ve atanan kullanıcılara
                manager_info = get_user_info(project_manager_id)
                manager_name = manager_info['fullname'] if manager_info else 'Bilinmeyen Yönetici'
                
                # Proje yöneticisine bildirim
                add_notification(project_manager_id, "Yeni Proje Eklendi", f"'{project_name}' adlı yeni proje size atandı. Yöneticisi: {manager_name}")

                # Atanan kullanıcılara bildirim
                for user_id in assigned_users:
                    user_info = get_user_info(user_id)
                    if user_info:
                        add_notification(user_id, "Yeni Proje Eklendi", f"'{project_name}' adlı yeni projeye atandınız. Proje Yöneticisi: {manager_name}")

                return jsonify({"message": "Proje başarıyla eklendi.", "project_id": project_id}), 201
        except Exception as e:
            connection.rollback()
            print(f"Proje eklenirken hata oluştu: {e}")
            return jsonify({"message": "Proje eklenirken bir hata oluştu."}), 500
        finally:
            connection.close()
    return jsonify({"message": "Veritabanı bağlantı hatası."}), 500


@app.route('/api/projects/<int:project_id>', methods=['PUT'])
def update_project(project_id):
    data = request.get_json()
    project_name = data.get('project_name')
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    status = data.get('status')
    project_manager_id = data.get('project_manager_id')
    customer_id = data.get('customer_id')
    description = data.get('description')
    budget = data.get('budget')
    currency = data.get('currency')
    assigned_users = data.get('assigned_users', []) # Yeni: Atanan kullanıcılar listesi

    if not all([project_name, start_date, end_date, status, project_manager_id, customer_id]):
        return jsonify({"message": "Eksik bilgi: proje adı, başlangıç/bitiş tarihi, durum, proje yöneticisi ve müşteri ID'si gerekli."}), 400

    connection = get_db_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
                # Mevcut proje bilgilerini al
                cursor.execute("SELECT project_name, project_manager_id FROM projects WHERE project_id = %s", (project_id,))
                old_project_info = cursor.fetchone()
                
                # Projeyi güncelle
                sql = """
                UPDATE projects SET
                    project_name = %s,
                    start_date = %s,
                    end_date = %s,
                    status = %s,
                    project_manager_id = %s,
                    customer_id = %s,
                    description = %s,
                    budget = %s,
                    currency = %s
                WHERE project_id = %s
                """
                cursor.execute(sql, (project_name, start_date, end_date, status, project_manager_id, customer_id, description, budget, currency, project_id))

                # Proje atamalarını güncelle
                # Önce mevcut atamaları sil
                cursor.execute("DELETE FROM project_assignments WHERE project_id = %s", (project_id,))
                # Sonra yeni atamaları ekle
                if assigned_users:
                    for user_id in assigned_users:
                        assign_sql = "INSERT INTO project_assignments (project_id, user_id) VALUES (%s, %s)"
                        cursor.execute(assign_sql, (project_id, user_id))

                connection.commit()

                # Bildirim gönderme: Proje yöneticisine ve atanan kullanıcılara
                # Kimlere bildirim gideceğini belirle: eski yönetici, yeni yönetici, eski atananlar, yeni atananlar
                notified_users = set()

                if old_project_info:
                    old_manager_id = old_project_info['project_manager_id']
                    if old_manager_id:
                        notified_users.add(old_manager_id)

                if project_manager_id:
                    notified_users.add(project_manager_id)

                # Mevcut atanan kullanıcıları al
                cursor.execute("SELECT user_id FROM project_assignments WHERE project_id = %s", (project_id,))
                current_assigned_users = [row['user_id'] for row in cursor.fetchall()]
                for user_id in current_assigned_users:
                    notified_users.add(user_id)
                for user_id in assigned_users: # Yeni atananlar da dahil
                    notified_users.add(user_id)

                # Bildirim mesajı
                notification_message = f"'{project_name}' adlı proje güncellendi."
                
                for user_id in notified_users:
                    add_notification(user_id, "Proje Güncellendi", notification_message)

                return jsonify({"message": "Proje başarıyla güncellendi."}), 200
        except Exception as e:
            connection.rollback()
            print(f"Proje güncellenirken hata oluştu: {e}")
            return jsonify({"message": "Proje güncellenirken bir hata oluştu."}), 500
        finally:
            connection.close()
    return jsonify({"message": "Veritabanı bağlantı hatası."}), 500

@app.route('/api/projects/<int:project_id>', methods=['DELETE'])
def delete_project(project_id):
    connection = get_db_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
                # Silinecek projenin bilgilerini al
                cursor.execute("SELECT project_name, project_manager_id FROM projects WHERE project_id = %s", (project_id,))
                project_info = cursor.fetchone()

                if not project_info:
                    return jsonify({"message": "Proje bulunamadı."}), 404

                project_name = project_info['project_name']
                
                # Projeye atanan tüm kullanıcıları al
                cursor.execute("SELECT user_id FROM project_assignments WHERE project_id = %s", (project_id,))
                assigned_users = [row['user_id'] for row in cursor.fetchall()]

                # Projeyi sil
                sql = "DELETE FROM projects WHERE project_id = %s"
                cursor.execute(sql, (project_id,))
                connection.commit()

                # Bildirim gönderme: Proje yöneticisine ve atanan kullanıcılara
                notified_users = set(assigned_users)
                if project_info['project_manager_id']:
                    notified_users.add(project_info['project_manager_id'])

                notification_message = f"'{project_name}' adlı proje silindi."
                for user_id in notified_users:
                    add_notification(user_id, "Proje Silindi", notification_message)

                return jsonify({"message": "Proje başarıyla silindi."}), 200
        except Exception as e:
            connection.rollback()
            print(f"Proje silinirken hata oluştu: {e}")
            return jsonify({"message": "Proje silinirken bir hata oluştu."}), 500
        finally:
            connection.close()
    return jsonify({"message": "Veritabanı bağlantı hatası."}), 500

# Görev ekleme API'si (takvim.html için)
@app.route('/api/tasks', methods=['POST'])
def add_task():
    data = request.get_json()
    project_id = data.get('project_id')
    assigned_to_user_id = data.get('assigned_to_user_id')
    title = data.get('title')
    description = data.get('description')
    due_date = data.get('due_date')
    status = data.get('status', 'Beklemede')

    if not all([assigned_to_user_id, title, due_date]):
        return jsonify({"message": "Eksik bilgi: Atanan kullanıcı, başlık ve bitiş tarihi gerekli."}), 400

    connection = get_db_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
                sql = """
                INSERT INTO tasks (project_id, assigned_to_user_id, title, description, due_date, status)
                VALUES (%s, %s, %s, %s, %s, %s)
                """
                cursor.execute(sql, (project_id, assigned_to_user_id, title, description, due_date, status))
                task_id = cursor.lastrowid
                connection.commit()

                # Bildirim gönderme: Görev atanan kullanıcıya
                user_info = get_user_info(assigned_to_user_id)
                if user_info:
                    add_notification(assigned_to_user_id, "Yeni Görev Atandı", f"'{title}' başlıklı yeni bir görev size atandı. Bitiş Tarihi: {due_date}")

                return jsonify({"message": "Görev başarıyla eklendi.", "task_id": task_id}), 201
        except Exception as e:
            connection.rollback()
            print(f"Görev eklenirken hata oluştu: {e}")
            return jsonify({"message": "Görev eklenirken bir hata oluştu."}), 500
        finally:
            connection.close()
    return jsonify({"message": "Veritabanı bağlantı hatası."}), 500

# Görev güncelleme API'si
@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    data = request.get_json()
    project_id = data.get('project_id')
    assigned_to_user_id = data.get('assigned_to_user_id')
    title = data.get('title')
    description = data.get('description')
    due_date = data.get('due_date')
    status = data.get('status')

    if not all([assigned_to_user_id, title, due_date]):
        return jsonify({"message": "Eksik bilgi: Atanan kullanıcı, başlık ve bitiş tarihi gerekli."}), 400

    connection = get_db_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
                # Mevcut görev bilgilerini al
                cursor.execute("SELECT assigned_to_user_id, title FROM tasks WHERE id = %s", (task_id,))
                old_task_info = cursor.fetchone()

                sql = """
                UPDATE tasks SET
                    project_id = %s,
                    assigned_to_user_id = %s,
                    title = %s,
                    description = %s,
                    due_date = %s,
                    status = %s
                WHERE id = %s
                """
                cursor.execute(sql, (project_id, assigned_to_user_id, title, description, due_date, status, task_id))
                connection.commit()

                # Bildirim gönderme: Görev atanan kullanıcıya (değiştiyse veya güncellendiyse)
                if old_task_info and (old_task_info['assigned_to_user_id'] != assigned_to_user_id or old_task_info['title'] != title):
                    user_info = get_user_info(assigned_to_user_id)
                    if user_info:
                        add_notification(assigned_to_user_id, "Görev Güncellendi", f"'{title}' başlıklı göreviniz güncellendi. Bitiş Tarihi: {due_date}")

                return jsonify({"message": "Görev başarıyla güncellendi."}), 200
        except Exception as e:
            connection.rollback()
            print(f"Görev güncellenirken hata oluştu: {e}")
            return jsonify({"message": "Görev güncellenirken bir hata oluştu."}), 500
        finally:
            connection.close()
    return jsonify({"message": "Veritabanı bağlantı hatası."}), 500

# Görev silme API'si
@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    connection = get_db_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
                # Silinecek görevin bilgilerini al
                cursor.execute("SELECT assigned_to_user_id, title FROM tasks WHERE id = %s", (task_id,))
                task_info = cursor.fetchone()

                if not task_info:
                    return jsonify({"message": "Görev bulunamadı."}), 404

                task_title = task_info['title']
                assigned_user_id = task_info['assigned_to_user_id']

                sql = "DELETE FROM tasks WHERE id = %s"
                cursor.execute(sql, (task_id,))
                connection.commit()

                # Bildirim gönderme: Görev atanan kullanıcıya
                if assigned_user_id:
                    add_notification(assigned_user_id, "Görev Silindi", f"'{task_title}' başlıklı göreviniz silindi.")

                return jsonify({"message": "Görev başarıyla silindi."}), 200
        except Exception as e:
            connection.rollback()
            print(f"Görev silinirken hata oluştu: {e}")
            return jsonify({"message": "Görev silinirken bir hata oluştu."}), 500
        finally:
            connection.close()
    return jsonify({"message": "Veritabanı bağlantı hatası."}), 500


# Kullanıcı bilgilerini çeken yardımcı fonksiyon (bildirimler için gerekli)
def get_user_info(user_id):
    connection = get_db_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
                sql = "SELECT id, fullname, email, role FROM users WHERE id = %s"
                cursor.execute(sql, (user_id,))
                return cursor.fetchone()
        except Exception as e:
            print(f"Kullanıcı bilgisi çekilirken hata oluştu: {e}")
            return None
        finally:
            connection.close()
    return None

# Diğer mevcut endpoint'ler (değiştirilmediyse)
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    connection = get_db_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
                sql = "SELECT id, fullname, email, password, role FROM users WHERE email = %s"
                cursor.execute(sql, (email,))
                user = cursor.fetchone()

                if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
                    # Şifreyi response'tan kaldır
                    user.pop('password')
                    return jsonify({"message": "Giriş başarılı", "user": user}), 200
                else:
                    return jsonify({"message": "Geçersiz e-posta veya şifre"}), 401
        except Exception as e:
            print(f"Giriş sırasında hata oluştu: {e}")
            return jsonify({"message": "Giriş sırasında bir hata oluştu."}), 500
        finally:
            connection.close()
    return jsonify({"message": "Veritabanı bağlantı hatası."}), 500

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    fullname = data.get('fullname')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'Çalışan') # Varsayılan rol

    if not all([fullname, email, password]):
        return jsonify({"message": "Tüm alanlar gerekli."}), 400

    # E-posta formatı kontrolü
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return jsonify({"message": "Geçersiz e-posta formatı."}), 400

    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    connection = get_db_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
                # E-posta zaten var mı kontrol et
                cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
                if cursor.fetchone():
                    return jsonify({"message": "Bu e-posta adresi zaten kayıtlı."}), 409

                sql = "INSERT INTO users (fullname, email, password, role) VALUES (%s, %s, %s, %s)"
                cursor.execute(sql, (fullname, email, hashed_password, role))
                connection.commit()
                return jsonify({"message": "Kayıt başarılı. Lütfen giriş yapın."}), 201
        except Exception as e:
            connection.rollback()
            print(f"Kayıt sırasında hata oluştu: {e}")
            return jsonify({"message": "Kayıt sırasında bir hata oluştu."}), 500
        finally:
            connection.close()
    return jsonify({"message": "Veritabanı bağlantı hatası."}), 500

@app.route('/api/users', methods=['GET'])
def get_users():
    connection = get_db_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
                sql = "SELECT id, fullname, email, role FROM users"
                cursor.execute(sql)
                users = cursor.fetchall()
                return jsonify(users), 200
        except Exception as e:
            print(f"Kullanıcılar çekilirken hata oluştu: {e}")
            return jsonify({"message": "Kullanıcılar çekilirken bir hata oluştu."}), 500
        finally:
            connection.close()
    return jsonify({"message": "Veritabanı bağlantı hatası."}), 500

@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    connection = get_db_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
                sql = "SELECT id, fullname, email, role FROM users WHERE id = %s"
                cursor.execute(sql, (user_id,))
                user = cursor.fetchone()
                if user:
                    return jsonify(user), 200
                return jsonify({"message": "Kullanıcı bulunamadı."}), 404
        except Exception as e:
            print(f"Kullanıcı çekilirken hata oluştu: {e}")
            return jsonify({"message": "Kullanıcı çekilirken bir hata oluştu."}), 500
        finally:
            connection.close()
    return jsonify({"message": "Veritabanı bağlantı hatası."}), 500

@app.route('/api/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    data = request.get_json()
    fullname = data.get('fullname')
    email = data.get('email')
    role = data.get('role')

    if not all([fullname, email, role]):
        return jsonify({"message": "Tüm alanlar gerekli."}), 400

    # E-posta formatı kontrolü
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return jsonify({"message": "Geçersiz e-posta formatı."}), 400

    connection = get_db_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
                # E-posta başka bir kullanıcıya ait mi kontrol et
                cursor.execute("SELECT id FROM users WHERE email = %s AND id != %s", (email, user_id))
                if cursor.fetchone():
                    return jsonify({"message": "Bu e-posta adresi başka bir kullanıcıya ait."}), 409

                sql = "UPDATE users SET fullname = %s, email = %s, role = %s WHERE id = %s"
                cursor.execute(sql, (fullname, email, role, user_id))
                connection.commit()
                if cursor.rowcount > 0:
                    return jsonify({"message": "Kullanıcı başarıyla güncellendi."}), 200
                return jsonify({"message": "Kullanıcı bulunamadı veya güncellenecek veri yok."}), 404
        except Exception as e:
            connection.rollback()
            print(f"Kullanıcı güncellenirken hata oluştu: {e}")
            return jsonify({"message": "Kullanıcı güncellenirken bir hata oluştu."}), 500
        finally:
            connection.close()
    return jsonify({"message": "Veritabanı bağlantı hatası."}), 500

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    connection = get_db_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
                sql = "DELETE FROM users WHERE id = %s"
                cursor.execute(sql, (user_id,))
                connection.commit()
                if cursor.rowcount > 0:
                    return jsonify({"message": "Kullanıcı başarıyla silindi."}), 200
                return jsonify({"message": "Kullanıcı bulunamadı."}), 404
        except Exception as e:
            connection.rollback()
            print(f"Kullanıcı silinirken hata oluştu: {e}")
            return jsonify({"message": "Kullanıcı silinirken bir hata oluştu."}), 500
        finally:
            connection.close()
    return jsonify({"message": "Veritabanı bağlantı hatası."}), 500

@app.route('/api/roles', methods=['GET'])
def get_roles():
    connection = get_db_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
                sql = "SELECT * FROM roles"
                cursor.execute(sql)
                roles = cursor.fetchall()
                return jsonify(roles), 200
        except Exception as e:
            print(f"Roller çekilirken hata oluştu: {e}")
            return jsonify({"message": "Roller çekilirken bir hata oluştu."}), 500
        finally:
            connection.close()
    return jsonify({"message": "Veritabanı bağlantı hatası."}), 500

@app.route('/api/role-permissions', methods=['GET'])
def get_role_permissions():
    role_name = request.args.get('role')
    if not role_name:
        return jsonify({"message": "Rol adı gerekli"}), 400

    connection = get_db_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
                sql = """
                SELECT rp.* FROM role_permissions rp
                JOIN roles r ON rp.role_id = r.id
                WHERE r.role_name = %s
                """
                cursor.execute(sql, (role_name,))
                permissions = cursor.fetchall()
                if permissions:
                    return jsonify(permissions), 200
                return jsonify({"message": "Bu rol için yetki bulunamadı."}), 404
        except Exception as e:
            print(f"Rol yetkileri çekilirken hata oluştu: {e}")
            return jsonify({"message": "Rol yetkileri çekilirken bir hata oluştu."}), 500
        finally:
            connection.close()
    return jsonify({"message": "Veritabanı bağlantı hatası."}), 500

@app.route('/api/customers', methods=['GET'])
def get_customers():
    connection = get_db_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
                sql = "SELECT id, customer_name, contact_person, email, phone FROM customers"
                cursor.execute(sql)
                customers = cursor.fetchall()
                return jsonify(customers), 200
        except Exception as e:
            print(f"Müşteriler çekilirken hata oluştu: {e}")
            return jsonify({"message": "Müşteriler çekilirken bir hata oluştu."}), 500
        finally:
            connection.close()
    return jsonify({"message": "Veritabanı bağlantı hatası."}), 500

@app.route('/api/customers', methods=['POST'])
def add_customer():
    data = request.get_json()
    customer_name = data.get('customer_name')
    contact_person = data.get('contact_person')
    email = data.get('email')
    phone = data.get('phone')

    if not all([customer_name, contact_person, email, phone]):
        return jsonify({"message": "Tüm alanlar gerekli."}), 400

    connection = get_db_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
                sql = "INSERT INTO customers (customer_name, contact_person, email, phone) VALUES (%s, %s, %s, %s)"
                cursor.execute(sql, (customer_name, contact_person, email, phone))
                connection.commit()
                return jsonify({"message": "Müşteri başarıyla eklendi."}), 201
        except Exception as e:
            connection.rollback()
            print(f"Müşteri eklenirken hata oluştu: {e}")
            return jsonify({"message": "Müşteri eklenirken bir hata oluştu."}), 500
        finally:
            connection.close()
    return jsonify({"message": "Veritabanı bağlantı hatası."}), 500

@app.route('/api/customers/<int:customer_id>', methods=['PUT'])
def update_customer(customer_id):
    data = request.get_json()
    customer_name = data.get('customer_name')
    contact_person = data.get('contact_person')
    email = data.get('email')
    phone = data.get('phone')

    if not all([customer_name, contact_person, email, phone]):
        return jsonify({"message": "Tüm alanlar gerekli."}), 400

    connection = get_db_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
                sql = "UPDATE customers SET customer_name = %s, contact_person = %s, email = %s, phone = %s WHERE id = %s"
                cursor.execute(sql, (customer_name, contact_person, email, phone, customer_id))
                connection.commit()
                if cursor.rowcount > 0:
                    return jsonify({"message": "Müşteri başarıyla güncellendi."}), 200
                return jsonify({"message": "Müşteri bulunamadı veya güncellenecek veri yok."}), 404
        except Exception as e:
            connection.rollback()
            print(f"Müşteri güncellenirken hata oluştu: {e}")
            return jsonify({"message": "Müşteri güncellenirken bir hata oluştu."}), 500
        finally:
            connection.close()
    return jsonify({"message": "Veritabanı bağlantı hatası."}), 500

@app.route('/api/customers/<int:customer_id>', methods=['DELETE'])
def delete_customer(customer_id):
    connection = get_db_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
                sql = "DELETE FROM customers WHERE id = %s"
                cursor.execute(sql, (customer_id,))
                connection.commit()
                if cursor.rowcount > 0:
                    return jsonify({"message": "Müşteri başarıyla silindi."}), 200
                return jsonify({"message": "Müşteri bulunamadı."}), 404
        except Exception as e:
            connection.rollback()
            print(f"Müşteri silinirken hata oluştu: {e}")
            return jsonify({"message": "Müşteri silinirken bir hata oluştu."}), 500
        finally:
            connection.close()
    return jsonify({"message": "Veritabanı bağlantı hatası."}), 500

@app.route('/api/projects', methods=['GET'])
def get_projects():
    connection = get_db_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
                sql = """
                SELECT
                    p.project_id,
                    p.project_name,
                    p.start_date,
                    p.end_date,
                    p.status,
                    p.project_manager_id,
                    pm.fullname AS project_manager_name,
                    p.customer_id,
                    c.customer_name,
                    p.description,
                    p.budget,
                    p.currency,
                    GROUP_CONCAT(DISTINCT u.id) AS assigned_user_ids,
                    GROUP_CONCAT(DISTINCT u.fullname) AS assigned_user_names
                FROM projects p
                LEFT JOIN users pm ON p.project_manager_id = pm.id
                LEFT JOIN customers c ON p.customer_id = c.id
                LEFT JOIN project_assignments pa ON p.project_id = pa.project_id
                LEFT JOIN users u ON pa.user_id = u.id
                GROUP BY p.project_id
                ORDER BY p.start_date DESC
                """
                cursor.execute(sql)
                projects = cursor.fetchall()

                # Tarih objelerini stringe çevir ve atanan kullanıcıları listeye dönüştür
                for project in projects:
                    if isinstance(project['start_date'], datetime.date):
                        project['start_date'] = project['start_date'].isoformat()
                    if isinstance(project['end_date'], datetime.date):
                        project['end_date'] = project['end_date'].isoformat()
                    project['assigned_user_ids'] = [int(x) for x in project['assigned_user_ids'].split(',') if x] if project['assigned_user_ids'] else []
                    project['assigned_user_names'] = [x for x in project['assigned_user_names'].split(',') if x] if project['assigned_user_names'] else []

                    # Proje bitişine 14 gün kala bildirim kontrolü (her gün gönderilmemesi için basit kontrol)
                    if project['end_date']:
                        end_date_obj = datetime.datetime.strptime(project['end_date'], '%Y-%m-%d').date()
                        today = datetime.date.today()
                        days_left = (end_date_obj - today).days

                        if 0 < days_left <= 14:
                            # Bu kontrolü her API çağrısında yapmak yerine, gerçek bir uygulamada
                            # zamanlanmış bir görev (cron job vb.) ile yapmak daha verimli olacaktır.
                            # Şimdilik, her istekte kontrol edip, aynı gün içinde tekrar bildirim göndermemek için
                            # bir mekanizma düşünmeliyiz. Ancak bildirim tablosunda `created_at` olduğu için
                            # frontend bu bildirimi zaten her gün yeniymiş gibi göstermeyecektir.
                            # Backend tarafında her gün sadece bir kez gönderildiğinden emin olmak için
                            # bildirim tablosuna `notification_type` ve `reference_id` gibi sütunlar eklenip
                            # kontrol edilebilir.
                            
                            # Basit bir kontrol: Eğer bu proje için bugün zaten bir "Yaklaşan Bitiş" bildirimi gönderilmediyse
                            # (Bu kısım için daha gelişmiş bir kontrol gerekebilir, şimdilik her istekte tetiklenebilir)
                            notification_title = "Proje Bitiş Tarihi Yaklaşıyor"
                            notification_message = f"'{project['project_name']}' projesinin bitişine {days_left} gün kaldı."
                            
                            # Proje yöneticisine ve atanan kullanıcılara bildirim gönder
                            users_to_notify = set(project['assigned_user_ids'])
                            if project['project_manager_id']:
                                users_to_notify.add(project['project_manager_id'])
                            
                            for user_id in users_to_notify:
                                # Burada aynı gün içinde aynı bildirimden birden fazla gitmemesi için ek kontrol yapılabilir.
                                # Örneğin, notifications tablosunda `notification_type` ve `reference_id` sütunları ekleyip
                                # bugün bu proje için bu tür bir bildirim gönderilip gönderilmediği kontrol edilebilir.
                                # Şimdilik, frontend'in zaten `created_at`'e göre filtreleme yapacağı varsayılır.
                                pass # add_notification(user_id, notification_title, notification_message)
                                # Yukarıdaki satırı yorum satırı yaptım çünkü her GET isteğinde bildirim göndermesi istenmez.
                                # Bu tür bildirimler için zamanlanmış görevler (cron job) kullanılmalıdır.
                                # Bu sadece bir örnek olarak burada duruyor.

                return jsonify(projects), 200
        except Exception as e:
            print(f"Projeler çekilirken hata oluştu: {e}")
            return jsonify({"message": "Projeler çekilirken bir hata oluştu."}), 500
        finally:
            connection.close()
    return jsonify({"message": "Veritabanı bağlantı hatası."}), 500

@app.route('/api/project-details/<int:project_id>', methods=['GET'])
def get_project_details(project_id):
    connection = get_db_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
                sql = """
                SELECT
                    p.project_id,
                    p.project_name,
                    p.start_date,
                    p.end_date,
                    p.status,
                    p.project_manager_id,
                    pm.fullname AS project_manager_name,
                    p.customer_id,
                    c.customer_name,
                    p.description,
                    p.budget,
                    p.currency,
                    GROUP_CONCAT(DISTINCT u.id) AS assigned_user_ids,
                    GROUP_CONCAT(DISTINCT u.fullname) AS assigned_user_names
                FROM projects p
                LEFT JOIN users pm ON p.project_manager_id = pm.id
                LEFT JOIN customers c ON p.customer_id = c.id
                LEFT JOIN project_assignments pa ON p.project_id = pa.project_id
                LEFT JOIN users u ON pa.user_id = u.id
                WHERE p.project_id = %s
                GROUP BY p.project_id
                """
                cursor.execute(sql, (project_id,))
                project = cursor.fetchone()

                if project:
                    if isinstance(project['start_date'], datetime.date):
                        project['start_date'] = project['start_date'].isoformat()
                    if isinstance(project['end_date'], datetime.date):
                        project['end_date'] = project['end_date'].isoformat()
                    project['assigned_user_ids'] = [int(x) for x in project['assigned_user_ids'].split(',') if x] if project['assigned_user_ids'] else []
                    project['assigned_user_names'] = [x for x in project['assigned_user_names'].split(',') if x] if project['assigned_user_names'] else []

                    # Proje ilerlemesini çek
                    cursor.execute("SELECT * FROM project_progress WHERE project_id = %s ORDER BY progress_date ASC", (project_id,))
                    project['progress'] = cursor.fetchall()
                    for prog in project['progress']:
                        if isinstance(prog['progress_date'], datetime.date):
                            prog['progress_date'] = prog['progress_date'].isoformat()

                    return jsonify(project), 200
                return jsonify({"message": "Proje bulunamadı."}), 404
        except Exception as e:
            print(f"Proje detayları çekilirken hata oluştu: {e}")
            return jsonify({"message": "Proje detayları çekilirken bir hata oluştu."}), 500
        finally:
            connection.close()
    return jsonify({"message": "Veritabanı bağlantı hatası."}), 500

@app.route('/api/project-progress', methods=['POST'])
def add_project_progress():
    data = request.get_json()
    project_id = data.get('project_id')
    progress_percentage = data.get('progress_percentage')
    delay_days = data.get('delay_days')
    notes = data.get('notes')

    if not all([project_id, progress_percentage is not None]):
        return jsonify({"message": "Eksik bilgi: proje ID ve ilerleme yüzdesi gerekli."}), 400

    connection = get_db_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
                sql = """
                INSERT INTO project_progress (project_id, progress_percentage, delay_days, notes)
                VALUES (%s, %s, %s, %s)
                """
                cursor.execute(sql, (project_id, progress_percentage, delay_days, notes))
                connection.commit()
                return jsonify({"message": "Proje ilerlemesi başarıyla eklendi."}), 201
        except Exception as e:
            connection.rollback()
            print(f"Proje ilerlemesi eklenirken hata oluştu: {e}")
            return jsonify({"message": "Proje ilerlemesi eklenirken bir hata oluştu."}), 500
        finally:
            connection.close()
    return jsonify({"message": "Veritabanı bağlantı hatası."}), 500

@app.route('/api/project-progress/<int:progress_id>', methods=['PUT'])
def update_project_progress(progress_id):
    data = request.get_json()
    progress_percentage = data.get('progress_percentage')
    delay_days = data.get('delay_days')
    notes = data.get('notes')

    if progress_percentage is None:
        return jsonify({"message": "İlerleme yüzdesi gerekli."}), 400

    connection = get_db_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
                sql = """
                UPDATE project_progress SET
                    progress_percentage = %s,
                    delay_days = %s,
                    notes = %s
                WHERE id = %s
                """
                cursor.execute(sql, (progress_percentage, delay_days, notes, progress_id))
                connection.commit()
                if cursor.rowcount > 0:
                    return jsonify({"message": "Proje ilerlemesi başarıyla güncellendi."}), 200
                return jsonify({"message": "Proje ilerlemesi bulunamadı veya güncellenecek veri yok."}), 404
        except Exception as e:
            connection.rollback()
            print(f"Proje ilerlemesi güncellenirken hata oluştu: {e}")
            return jsonify({"message": "Proje ilerlemesi güncellenirken bir hata oluştu."}), 500
        finally:
            connection.close()
    return jsonify({"message": "Veritabanı bağlantı hatası."}), 500

@app.route('/api/project-progress/<int:progress_id>', methods=['DELETE'])
def delete_project_progress(progress_id):
    connection = get_db_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
                sql = "DELETE FROM project_progress WHERE id = %s"
                cursor.execute(sql, (progress_id,))
                connection.commit()
                if cursor.rowcount > 0:
                    return jsonify({"message": "Proje ilerlemesi başarıyla silindi."}), 200
                return jsonify({"message": "Proje ilerlemesi bulunamadı."}), 404
        except Exception as e:
            connection.rollback()
            print(f"Proje ilerlemesi silinirken hata oluştu: {e}")
            return jsonify({"message": "Proje ilerlemesi silinirken bir hata oluştu."}), 500
        finally:
            connection.close()
    return jsonify({"message": "Veritabanı bağlantı hatası."}), 500

@app.route('/api/dashboard-summary')
def dashboard_summary():
    connection = get_db_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
                # Toplam Proje Sayısı
                cursor.execute("SELECT COUNT(*) AS total_projects FROM projects")
                total_projects = cursor.fetchone()['total_projects']

                # Devam Eden Projeler
                cursor.execute("SELECT COUNT(*) AS ongoing_projects FROM projects WHERE status = 'Devam Ediyor'")
                ongoing_projects = cursor.fetchone()['ongoing_projects']

                # Tamamlanan Projeler
                cursor.execute("SELECT COUNT(*) AS completed_projects FROM projects WHERE status = 'Bitti'")
                completed_projects = cursor.fetchone()['completed_projects']

                # Yaklaşan Bitiş Tarihli Projeler (Son 30 gün içinde bitmesi gerekenler)
                thirty_days_later = datetime.date.today() + datetime.timedelta(days=30)
                cursor.execute("SELECT COUNT(*) AS approaching_projects FROM projects WHERE end_date BETWEEN CURDATE() AND %s AND status != 'Bitti'", (thirty_days_later,))
                approaching_projects = cursor.fetchone()['approaching_projects']

                # En Son Eklenen Projeler (Son 5)
                cursor.execute("""
                    SELECT p.project_id, p.project_name, p.status, p.end_date, u.fullname AS project_manager_name
                    FROM projects p
                    LEFT JOIN users u ON p.project_manager_id = u.id
                    ORDER BY p.start_date DESC
                    LIMIT 5
                """)
                latest_projects = cursor.fetchall()
                for project in latest_projects:
                    if isinstance(project['end_date'], datetime.date):
                        project['end_date'] = project['end_date'].isoformat()

                # Proje Durumlarına Göre Dağılım
                cursor.execute("SELECT status, COUNT(*) AS count FROM projects GROUP BY status")
                project_status_distribution = cursor.fetchall()

                # Aktivite Logları (Son 10) - Bu kısım için `activities` tablosu varsayılıyor
                cursor.execute("""
                    SELECT a.title, a.description, a.created_at, u.fullname AS user_name
                    FROM activities a
                    LEFT JOIN users u ON a.user_id = u.id
                    ORDER BY a.created_at DESC
                    LIMIT 10
                """)
                activity_logs = cursor.fetchall()
                for log in activity_logs:
                    if isinstance(log['created_at'], datetime.datetime):
                        log['created_at'] = log['created_at'].isoformat()

                summary = {
                    "total_projects": total_projects,
                    "ongoing_projects": ongoing_projects,
                    "completed_projects": completed_projects,
                    "approaching_projects": approaching_projects,
                    "latest_projects": latest_projects,
                    "project_status_distribution": project_status_distribution,
                    "activity_logs": activity_logs
                }
                return jsonify(summary), 200
        except Exception as e:
            print(f"Dashboard özeti çekilirken hata oluştu: {e}")
            return jsonify({"message": "Dashboard özeti çekilirken bir hata oluştu."}), 500
        finally:
            connection.close()
    return jsonify({"message": "Veritabanı bağlantı hatası."}), 500

@app.route('/api/worker-performance')
def worker_performance():
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = """
            SELECT
                u.fullname AS manager_name,
                COUNT(DISTINCT p.project_id) AS total_projects,
                SUM(CASE
                        WHEN p.status = 'Bitti' AND (
                            SELECT SUM(pr.delay_days)
                            FROM project_progress pr
                            WHERE pr.project_id = p.project_id
                        ) IS NULL OR (
                            SELECT SUM(pr.delay_days)
                            FROM project_progress pr
                            WHERE pr.project_id = p.project_id
                        ) = 0
                    THEN 1
                    ELSE 0
                END) AS on_time_projects
            FROM projects p
            LEFT JOIN users u ON u.id = p.project_manager_id
            WHERE u.role IN ('Tekniker', 'Teknisyen', 'Mühendis', 'Müdür', 'Proje Yöneticisi')
            GROUP BY p.project_manager_id, u.fullname
            """
            cursor.execute(sql)
            result = cursor.fetchall()
            return jsonify(result)
    finally:
        if connection:
            connection.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3001, debug=True)
