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

@app.route('/takvim.html')
def serve_takvim_page():
    """/takvim.html URL'ye gelen istekleri takvim.html sayfasına yönlendirir."""
    return render_template('takvim.html')

@app.route('/waiting.html')
def serve_waiting_page():
    """/waiting.html URL'ye gelen istekleri waiting.html sayfasına yönlendirir."""
    return render_template('waiting.html')

@app.route('/yeni_musteri.html')
def serve_yeni_musteri_page():
    """/yeni_musteri.html URL'ye gelen istekleri yeni_musteri.html sayfasına yönlendirir."""
    return render_template('yeni_musteri.html')

@app.route('/bildirim.html')
def serve_bildirim_page():
    """/bildirim.html URL'ye gelen istekleri bildirim.html sayfasına yönlendirir."""
    return render_template('bildirim.html')

# CORS (Cross-Origin Resource Sharing) ayarları
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

def get_db_connection():
    connection = None
    try:
        host = None
        port = None
        user = None
        password = None
        database = None

        public_url = os.getenv("MYSQL_PUBLIC_URL")
        print(f"DEBUG: MYSQL_PUBLIC_URL from env: '{public_url}'") # Added more detailed logging

        if public_url:
            try:
                parsed_url = urllib.parse.urlparse(public_url)
                host = parsed_url.hostname
                port = parsed_url.port if parsed_url.port else 3306
                user = parsed_url.username
                password = parsed_url.password
                database = parsed_url.path.lstrip('/')
                print(f"DEBUG: Using parsed public URL. Host={host}, Port={port}, User={user}, DB={database}")
            except Exception as url_parse_e:
                print(f"ERROR: Failed to parse MYSQL_PUBLIC_URL: {url_parse_e}. Falling back to individual env vars.")
                # URL ayrıştırma hatası durumunda tekil ortam değişkenlerine geri dön
                host = os.getenv("MYSQL_HOST") or "localhost"
                port = int(os.getenv("MYSQL_PORT") or 3306)
                user = os.getenv("MYSQL_USER") or "root"
                password = os.getenv("MYSQL_PASSWORD") or ""
                database = os.getenv("MYSQL_DATABASE") or "ser"
                print(f"DEBUG: Using individual env vars fallback: Host={host}, Port={port}, User={user}, DB={database}")
        else:
            print("DEBUG: MYSQL_PUBLIC_URL not found or empty. Using individual env vars.")
            # MYSQL_PUBLIC_URL yoksa tekil ortam değişkenlerini veya varsayılanları kullan
            host = os.getenv("MYSQL_HOST") or "localhost"
            port = int(os.getenv("MYSQL_PORT") or 3306)
            user = os.getenv("MYSQL_USER") or "root"
            password = os.getenv("MYSQL_PASSWORD") or ""
            database = os.getenv("MYSQL_DATABASE") or "ser"
            print(f"DEBUG: Using individual env vars: Host={host}, Port={port}, User={user}, DB={database}")

        connection = pymysql.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            port=port, 
            cursorclass=pymysql.cursors.DictCursor # Sorgu sonuçlarını sözlük olarak almak için
        )
        print("MySQL veritabanına başarıyla bağlandı!")
        return connection
    except pymysql.Error as e:
        print(f"MySQL bağlantı hatası: {e}")
        if connection:
            connection.close()
        raise # Hatayı yukarı fırlat, Flask bunu yakalayacaktır

# Bildirimleri Tümü Okundu API (notifications tablosu için)
@app.route('/api/notifications/mark_all_read', methods=['PUT'])
def mark_all_notifications_as_read():
    """Tüm bildirimleri veritabanında okunmuş olarak işaretler."""
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # notifications tablosundaki 'id' sütununu kullan
            sql = "UPDATE notifications SET is_read = 1 WHERE is_read = 0" # Sadece okunmamışları güncelle
            cursor.execute(sql)
            connection.commit()
            rows_affected = cursor.rowcount # Kaç satırın etkilendiğini al
        return jsonify({'message': f'{rows_affected} bildirim okunmuş olarak işaretlendi.'}), 200
    except pymysql.Error as e:
        print(f"Veritabanı tüm bildirimleri güncelleme hatası: {e}")
        return jsonify({'message': f'Veritabanı hatası oluştu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel tüm bildirimleri güncelleme hatası: {e}")
        return jsonify({'message': 'Sunucu hatası, lütfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()

# Okunmamış Bildirim Sayısı API (notifications tablosu için)
@app.route('/api/notifications/unread-count', methods=['GET'])
def get_unread_notifications_count():
    """Veritabanındaki okunmamış bildirimlerin sayısını döndürür."""
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # notifications tablosundaki 'id' sütununu kullan
            sql = "SELECT COUNT(id) as unread_count FROM notifications WHERE is_read = 0"
            cursor.execute(sql)
            result = cursor.fetchone()
            return jsonify(result), 200
    except pymysql.Error as e:
        print(f"Veritabanı okunmamış bildirim sayısı çekme hatası: {e}")
        return jsonify({'message': f'Veritabanı hatası oluştu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel okunmamış bildirim sayısı çekme hatası: {e}")
        return jsonify({'message': 'Sunucu hatası, lütfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()


# Bildirimi Okundu API (notifications tablosu için)
@app.route('/api/notifications/<int:notification_id>/read', methods=['PUT'])
def mark_notification_as_read(notification_id):
    """Belirli bir bildirimi veritabanında okunmuş olarak işaretler."""
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # Bildirimin varlığını kontrol et
            # notifications tablosundaki 'id' sütununu kullan
            cursor.execute("SELECT id FROM notifications WHERE id = %s", (notification_id,))
            if not cursor.fetchone():
                return jsonify({'message': 'Bildirim bulunamadı.'}), 404

            # is_read sütununu 1 olarak güncelle
            # notifications tablosundaki 'id' sütununu kullan
            sql = "UPDATE notifications SET is_read = 1 WHERE id = %s"
            cursor.execute(sql, (notification_id,))
            connection.commit()

        return jsonify({'message': 'Bildirim başarıyla okunmuş olarak işaretlendi.'}), 200
    except pymysql.Error as e:
        print(f"Veritabanı bildirim güncelleme hatası: {e}")
        return jsonify({'message': f'Veritabanı hatası oluştu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel bildirim güncelleme hatası: {e}")
        return jsonify({'message': 'Sunucu hatası, lütfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()

# Bildirimleri Çekme API (notifications tablosu için)
@app.route('/api/notifications', methods=['GET'])
def get_notifications():
    """Veritabanından tüm bildirimleri çeker."""
    connection = get_db_connection()
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # 'notifications' tablosundan tüm verileri çekmek için SQL sorgusu
            # Yeni tablo yapısına göre 'id' ve 'message' kullanıldı, 'icon' ve 'project_id' kaldırıldı.
            sql = "SELECT id, user_id, title, message, is_read, created_at FROM notifications ORDER BY created_at DESC"
            cursor.execute(sql)
            result = cursor.fetchall()
            # is_read alanını int olarak döndür (garanti)
            for row in result:
                if 'is_read' in row:
                    try:
                        row['is_read'] = int(row['is_read'])
                    except Exception:
                        row['is_read'] = 0
            return jsonify(result)
    finally:
        if connection:
            connection.close()

# Yeni Bildirim Ekle API (notifications tablosu için)
@app.route('/api/notifications', methods=['POST'])
def add_notification():
    data = request.get_json()
    user_id = data.get('user_id')
    title = data.get('title')
    message = data.get('message') # 'raw_description' yerine 'message' kullanıldı

    # Zorunlu alan kontrolü
    if not all([user_id, title, message]):
        return jsonify({'message': 'Kullanıcı ID, başlık ve mesaj zorunludur.'}), 400

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Bildirim tablosuna ekleme
            # Yeni tablo yapısına göre 'message' kullanıldı, 'icon' ve 'action_type' kaldırıldı.
            sql = """
            INSERT INTO notifications (user_id, title, message, created_at)
            VALUES (%s, %s, %s, NOW())
            """
            cursor.execute(sql, (user_id, title, message))
            connection.commit()
        return jsonify({'message': 'Bildirim başarıyla kaydedildi!'}), 201
    except pymysql.Error as e:
        print(f"Veritabanı bildirim kaydetme hatası: {e}")
        if e.args[0] == 1062:
            return jsonify({'message': 'Bu e-posta adresi zaten kullanılıyor.'}), 409
        return jsonify({'message': f'Veritabanı hatası oluştu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel bildirim kaydetme hatası: {e}")
        return jsonify({'message': 'Sunucu hatası, lütfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()

# Yeni Aktivite Ekle API (activities tablosu için)
@app.route('/api/activities', methods=['POST'])
def add_activity():
    data = request.get_json()
    user_id = data.get('user_id')
    title = data.get('title')
    description = data.get('description')
    icon = data.get('icon', 'fas fa-info-circle') # Varsayılan ikon

    if not all([user_id, title, description]):
        return jsonify({'message': 'Kullanıcı ID, başlık ve açıklama zorunludur.'}), 400

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # 'activity' yerine 'activities' olarak düzeltildi
            sql = """
            INSERT INTO activities (user_id, title, description, icon, created_at)
            VALUES (%s, %s, %s, %s, NOW())
            """
            cursor.execute(sql, (user_id, title, description, icon))
            connection.commit()
        return jsonify({'message': 'Aktivite başarıyla kaydedildi!'}), 201
    except pymysql.Error as e:
        print(f"Veritabanı aktivite kaydetme hatası: {e}")
        return jsonify({'message': f'Veritabanı hatası oluştu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel aktivite kaydetme hatası: {e}")
        return jsonify({'message': 'Sunucu hatası, lütfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()

@app.route('/api/update_user_profile', methods=['POST'])
def update_user_profile():
    data = request.get_json()
    user_id = data.get('userId')
    current_password = data.get('currentPassword')
    new_password = data.get('newPassword')
    fullname = data.get('fullname')
    email = data.get('email')

    if not user_id:
        return jsonify({'message': 'Kullanıcı ID eksik.'}), 400

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Kullanıcının mevcut bilgilerini veritabanından çek
            cursor.execute("SELECT fullname, email, password FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()

            if not user:
                return jsonify({'message': 'Kullanıcı bulunamadı.'}), 404

            updates = []
            params = []
            message_parts = []

            # Ad Soyad Güncelleme
            if fullname is not None and fullname != user['fullname']:
                updates.append("fullname = %s")
                params.append(fullname)
                message_parts.append("Ad Soyad")

            # Email Güncelleme
            if email is not None and email != user['email']:
                # Yeni e-posta adresinin başka bir kullanıcı tarafından kullanılıp kullanılmadığını kontrol et
                cursor.execute("SELECT id FROM users WHERE email = %s AND id != %s", (email, user_id))
                if cursor.fetchone():
                    return jsonify({'message': 'Bu e-posta adresi zaten başka bir kullanıcı tarafından kullanılıyor.'}), 409
                updates.append("email = %s")
                params.append(email)
                message_parts.append("Email")

            # Şifre Değiştirme
            if current_password or new_password: # Eğer şifre alanlarından herhangi biri doldurulmuşsa
                if not current_password or not new_password:
                    return jsonify({'message': 'Şifre değiştirmek için mevcut ve yeni şifre alanları boş bırakılamaz.'}), 400

                # Girilen mevcut şifreyi, veritabanındaki hash ile karşılaştır
                if not bcrypt.checkpw(current_password.encode('utf-8'), user['password'].encode('utf-8')):
                    return jsonify({'message': 'Mevcut şifre yanlış.'}), 401

                # Yeni şifreyi hash'le
                hashed_new_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                updates.append("password = %s")
                params.append(hashed_new_password)
                message_parts.append("Şifre")

            if not updates:
                return jsonify({'message': 'Güncellenecek herhangi bir bilgi bulunamadı.'}), 200

            sql = f"UPDATE users SET {', '.join(updates)} WHERE id = %s"
            params.append(user_id)

            cursor.execute(sql, tuple(params))
            connection.commit()

            final_message = "Başarıyla güncellendi: " + ", ".join(message_parts) + "."
            if not message_parts: # Eğer hiçbir şey güncellenmediyse (ancak kod buraya gelmemeli)
                 final_message = "Güncellenecek bir değişiklik bulunamadı."

            return jsonify({'message': final_message}), 200

    except pymysql.Error as e:
        print(f"Veritabanı profil güncelleme hatası: {e}")
        return jsonify({'message': f'Veritabanı hatası oluştu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel profil güncelleme hatası: {e}")
        return jsonify({'message': 'Sunucu hatası, lütfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()
    data = request.get_json()
    user_id = data.get('userId')
    current_password = data.get('currentPassword')
    new_password = data.get('newPassword')

    if not all([user_id, current_password, new_password]):
        return jsonify({'message': 'Tüm alanlar gereklidir.'}), 400

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Kullanıcının mevcut şifresini veritabanından çek
            cursor.execute("SELECT password FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone() # password alanı dönecek

            if not user:
                return jsonify({'message': 'Kullanıcı bulunamadı.'}), 404

            # 'password' anahtarını kullanarak hash'lenmiş şifreye erişiyoruz
            stored_password_hash = user['password'] 

            # Girilen mevcut şifreyi, veritabanındaki hash ile karşılaştır
            if not bcrypt.checkpw(current_password.encode('utf-8'), stored_password_hash.encode('utf-8')):
                return jsonify({'message': 'Mevcut şifre yanlış.'}), 401

            # Yeni şifreyi hash'le
            hashed_new_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

            # Veritabanında şifreyi güncelle
            cursor.execute("UPDATE users SET password = %s WHERE id = %s", (hashed_new_password, user_id))
            connection.commit()

            return jsonify({'message': 'Şifre başarıyla değiştirildi.'}), 200

    except pymysql.Error as e:
        print(f"Veritabanı şifre değiştirme hatası: {e}")
        return jsonify({'message': f'Veritabanı hatası oluştu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel şifre değiştirme hatası: {e}")
        return jsonify({'message': 'Sunucu hatası, lütfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()
@app.route('/api/pending-users', methods=['GET'])
def get_pending_users():
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor(pymysql.cursors.DictCursor) as cursor: # DictCursor kullanarak sütun adlarıyla verilere erişim
            sql = "SELECT id, fullname, email, phone, role, created_at FROM users WHERE onay = 0"
            cursor.execute(sql)
            pending_users = cursor.fetchall()
            return jsonify(pending_users), 200
    except pymysql.Error as e:
        print(f"Veritabanı onay bekleyen kullanıcıları çekme hatası: {e}")
        return jsonify({'message': f'Veritabanı hatası oluştu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel onay bekleyen kullanıcıları çekme hatası: {e}")
        return jsonify({'message': 'Sunucu hatası, lütfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()
# app.py dosyanızdaki diğer rotaların altına veya uygun bir yere ekleyin

@app.route('/api/users/approve/<int:user_id>', methods=['PATCH'])
def approve_user(user_id):
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Kullanıcının varlığını kontrol et
            cursor.execute("SELECT id, onay FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()
    
            if not user:
                return jsonify({'message': 'Kullanıcı bulunamadı.'}), 404
            if user['onay'] == 1:
                return jsonify({'message': 'Kullanıcı zaten onaylanmış.'}), 400 # Bad Request

            # Kullanıcıyı onaylamak için is_approved sütununu güncelle
            sql = "UPDATE users SET onay = 1 WHERE id = %s"
            cursor.execute(sql, (user_id,))
            connection.commit()

        return jsonify({'message': 'Kullanıcı başarıyla onaylandı!'}), 200

    except pymysql.Error as e:
        print(f"Veritabanı kullanıcı onaylama hatası: {e}")
        return jsonify({'message': f'Veritabanı hatası oluştu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel kullanıcı onaylama hatası: {e}")
        return jsonify({'message': 'Sunucu hatası, lütfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()
# Diğer rotalarınız ve fonksiyonlarınız...
@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Check if user exists
            cursor.execute("SELECT id, fullname FROM users WHERE id = %s", (user_id,))
            user_info = cursor.fetchone()
            if not user_info:
                return jsonify({'message': 'Kullanıcı bulunamadı.'}), 404

            # Prevent deletion of the 'Admin' user or any critical user (e.g., ID 1)
            # You might want to adjust this logic based on your specific admin user ID or role
            if user_info['id'] == 1: # Assuming ID 1 is a critical admin/system user
                 return jsonify({'message': 'Bu kullanıcı silinemez.'}), 403 # Forbidden

            # Find a default project manager to reassign projects to
            # This assumes you have a user with a specific ID (e.g., 1) or a role like 'Admin'
            # You might need to adjust this query to find a suitable default user.
            # For demonstration, let's try to find an 'Admin' user or just pick the first available user that is not the one being deleted.
            default_manager_id = None
            cursor.execute("SELECT id FROM users WHERE role = 'Admin' AND id != %s LIMIT 1", (user_id,))
            admin_user = cursor.fetchone()
            if admin_user:
                default_manager_id = admin_user['id']
            else:
                # If no other admin, try to find any other user that is not the one being deleted
                cursor.execute("SELECT id FROM users WHERE id != %s LIMIT 1", (user_id,))
                other_user = cursor.fetchone()
                if other_user:
                    default_manager_id = other_user['id']

            if default_manager_id:
                # Reassign projects managed by the user being deleted
                cursor.execute(
                    "UPDATE projects SET project_manager_id = %s WHERE project_manager_id = %s",
                    (default_manager_id, user_id)
                )
                print(f"DEBUG: Reassigned {cursor.rowcount} projects from user {user_id} to {default_manager_id}")
            else:
                # If no other user to reassign to, you must delete associated projects
                # This is a less desirable option if project data is important.
                # You might want to add a confirmation prompt on the frontend for this case.
                cursor.execute("DELETE FROM projects WHERE project_manager_id = %s", (user_id,))
                print(f"DEBUG: Deleted {cursor.rowcount} projects for user {user_id} (no manager to reassign to)")
                # Also delete project progress entries for these projects if not handled by CASCADE DELETE
                # (Assuming project_progress has a foreign key to projects with ON DELETE CASCADE)
                # If not, you'd need to delete from project_progress first:
                # cursor.execute("DELETE FROM project_progress WHERE project_id IN (SELECT project_id FROM projects WHERE project_manager_id = %s)", (user_id,))


            # Delete tasks assigned to the user
            cursor.execute("DELETE FROM tasks WHERE assigned_user_id = %s", (user_id,))
            print(f"DEBUG: Deleted {cursor.rowcount} tasks for user {user_id}")

            # Finally, delete the user
            sql = "DELETE FROM users WHERE id = %s"
            cursor.execute(sql, (user_id,))
            connection.commit()
            print(f"DEBUG: Deleted user {user_id}")

        return jsonify({'message': 'Kullanıcı başarıyla silindi!'}), 200

    except pymysql.Error as e:
        print(f"Veritabanı kullanıcı silme hatası: {e}")
        # Check for specific error code if needed, but general message is often sufficient
        return jsonify({'message': f'Veritabanı hatası oluştu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel kullanıcı silme hatası: {e}")
        return jsonify({'message': 'Sunucu hatası, lütfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()

# Veritabanı bağlantısı oluşturan yardımcı fonksiyon
# Konum verilerini (il/ilçe) JSON dosyasından yükle
TURKEY_LOCATIONS = {}
try:
    script_dir = os.path.dirname(__file__)
    file_path = os.path.join(script_dir, 'turkey_locations.json')
    with open(file_path, 'r', encoding='utf-8') as f:
        TURKEY_LOCATIONS = json.load(f)
    print("Konum verileri başarıyla yüklendi.")
except FileNotFoundError:
    print(f"Hata: 'turkey_locations.json' dosyası bulunamadı. Lütfen '{file_path}' yolunu kontrol edin.")
    TURKEY_LOCATIONS = {"Türkiye": {"iller": {"Varsayılan İl": ["Varsayılan İlçe"]}}}
except json.JSONDecodeError:
    print("Hata: 'turkey_locations.json' dosyası JSON formatında değil veya bozuk.")
    TURKEY_LOCATIONS = {"Türkiye": {"iller": {"Varsayılan İl": ["Varsayılan İlçe"]}}}
except Exception as e:
    print(f"Konum verilerini yüklerken beklenmeyen hata: {e}")
    TURKEY_LOCATIONS = {"Türkiye": {"iller": {"Varsayılan İl": ["Varsayılan İlçe"]}}}


# --- API Rotaları ---
@app.route('/api/role-permissions', methods=['GET'])
def get_permissions_by_role():
    role_name = request.args.get('role')
    if not role_name:
        return jsonify({'message': 'Rol adı gerekli'}), 400

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            sql = "SELECT * FROM yetki WHERE role_name = %s"
            cursor.execute(sql, (role_name,))
            result = cursor.fetchone()
            if not result:
                return jsonify({'message': 'Rol bulunamadı'}), 404
            return jsonify(result), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500
    finally:
        if connection:
            connection.close()

@app.route('/api/role-permissions', methods=['POST'])
def update_role_permissions():
    data = request.json
    role = data.get('role')
    if not role:
        return jsonify({'message': 'Rol belirtilmedi.'}), 400

    proje_ekle = data.get('proje_ekle', 0)
    proje_duzenle = data.get('proje_duzenle', 0)
    proje_sil = data.get('proje_sil', 0)
    pdf_olusturma = data.get('pdf_olusturma', 0)
    musteri_duzenleme = data.get('musteri_duzenleme', 0)
    raporlar = data.get('raporlar', 0) # Yeni eklenen raporlar yetkisi

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            sql = """
                UPDATE yetki
                SET proje_ekle=%s, proje_duzenle=%s, proje_sil=%s, pdf_olusturma=%s, musteri_duzenleme=%s, raporlar=%s
                WHERE LOWER(role_name)=%s
            """
            cursor.execute(sql, (proje_ekle, proje_duzenle, proje_sil, pdf_olusturma, musteri_duzenleme, raporlar, role.lower()))
            connection.commit()
        return jsonify({'message': 'İzinler başarıyla güncellendi.'})
    except Exception as e:
        if connection:
            connection.rollback()
        return jsonify({'message': f'Hata: {str(e)}'}), 500
    finally:
        if connection:
            connection.close()

# Kullanıcı Kayıt (Register) API
@app.route('/api/register', methods=['POST'])
def register_user():
    data = request.get_json()
    fullname = data.get('fullname')
    email = data.get('email')
    phone = data.get('phone')
    password = data.get('password')
    role = data.get('role')

    if not all([fullname, email, password, role]):
        return jsonify({'message': 'Lütfen tüm zorunlu alanları doldurun.'}), 400

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            existing_user = cursor.fetchone()
            if existing_user:
                return jsonify({'message': 'Bu e-posta adresi zaten kullanılıyor.'}), 409

            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            sql = "INSERT INTO users (fullname, email, phone, password, role) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(sql, (fullname, email, phone, hashed_password, role))
            connection.commit()
        return jsonify({'message': 'Kayıt başarıyla oluşturuldu!'}), 201
    except pymysql.Error as e:
        print(f"Veritabanı kayıt hatası: {e}")
        if e.args[0] == 1062:
            return jsonify({'message': 'Bu e-posta adresi zaten kullanılıyor.'}), 409
        return jsonify({'message': f'Veritabanı hatası oluştu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel kayıt hatası: {e}")
        return jsonify({'message': 'Sunucu hatası, lütfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()


@app.route('/api/login', methods=['POST'])
def login_user():
    
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not all([email, password]):
        return jsonify({'message': 'Lütfen e-posta ve şifrenizi girin.'}), 400

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # 'onay'ı SELECT ifadesine ekleyin
            cursor.execute("SELECT id, fullname, email, password, role, onay FROM users WHERE email = %s", (email,))
            
            user = cursor.fetchone()

            if not user:
                return jsonify({'message': 'Geçersiz e-posta veya şifre.'}), 401

            is_match = bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8'))

            if not is_match:
                return jsonify({'message': 'Geçersiz e-posta veya şifre.'}), 401

            # 'onay' durumunu kontrol et
            if user['onay'] == 0:
                # 'onay' 0 ise, belirli bir mesaj döndürün ve potansiyel olarak yönlendirin
                return jsonify({
                    'message': 'Hesabınız henüz onaylanmamıştır. Lütfen yöneticinizle iletişime geçin.',
                    'user': {
                        'email': user['email'], # Bekleme sayfası için minimum kullanıcı bilgisi gönderebilirsiniz
                        'onay': user['onay']
                    },
                    'redirect': 'waiting.html' # Frontend'e nereye yönlendireceğini belirt
                }), 403 # Yasak durumu, veya özel bir bayrakla 200

            del user['password'] # Kullanıcı verilerini frontend'e göndermeden önce parolayı kaldırın

            return jsonify({
                'message': 'Giriş başarılı!',
                'user': user # 'user' şimdi onay 1 ise 'onay'ı içeriyor
            }), 200

    except pymysql.Error as e:
        print(f"Veritabanı giriş hatası: {e}")
        return jsonify({'message': f'Veritabanı hatası oluştu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel giriş hatası: {e}")
        return jsonify({'message': 'Sunucu hatası, lütfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()
# Yeni Müşteri Ekle API
@app.route('/api/customers', methods=['POST'])
def add_customer():
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
    user_id = data.get('user_id') # Kullanıcı ID'si eklendi

    if not all([customer_name, contact_person, phone, user_id]): # user_id zorunlu hale getirildi
        return jsonify({'message': 'Firma Adı, İlgili Kişi, Telefon ve Kullanıcı ID zorunlu alanlardır.'}), 400

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT customer_id FROM customers WHERE customer_name = %s", (customer_name,))
            existing_customer = cursor.fetchone()
            if existing_customer:
                return jsonify({'message': 'Bu firma adı zaten kayıtlı.'}), 409

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

            # Aktivite loglama
            log_activity(
                user_id=user_id,
                title='Yeni Müşteri Eklendi',
                description=f'"{customer_name}" adlı yeni müşteri eklendi.',
                icon='fas fa-user-plus'
            )

        return jsonify({'message': 'Müşteri başarıyla eklendi!', 'customerId': new_customer_id}), 201

    except pymysql.Error as e:
        print(f"Veritabanı müşteri ekleme hatası: {e}")
        if e.args[0] == 1062:
            return jsonify({'message': 'Bu e-posta veya firma adı zaten kayıtlı.'}), 409
        return jsonify({'message': f'Veritabanı hatası oluştu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel müşteri ekleme hatası: {e}")
        return jsonify({'message': 'Sunucu hatası, lütfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()

# Tüm Müşterileri Listele API
@app.route('/api/customers', methods=['GET'])
def get_customers():
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            sql = """
            SELECT c.customer_id, c.customer_name, c.contact_person, c.phone, c.email, c.status, c.country, c.city,
                    COUNT(p.project_id) AS project_count
            FROM customers c
            LEFT JOIN projects p ON c.customer_id = p.customer_id
            GROUP BY c.customer_id
            ORDER BY c.customer_name
            """
            cursor.execute(sql)
            customers = cursor.fetchall()
        return jsonify(customers), 200
    except pymysql.Error as e:
        print(f"Veritabanı müşteri çekme hatası: {e}")
        return jsonify({'message': f'Veritabanı hatası oluştu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel müşteri çekme hatası: {e}")
        return jsonify({'message': 'Sunucu hatası, lütfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()

# Tek bir müşterinin detaylarını çekme API'si (Modal için eklendi)
@app.route('/api/customers/<int:customer_id>', methods=['GET'])
def get_customer_details(customer_id):
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
                return jsonify({'message': 'Müşteri bulunamadı.'}), 404

        return jsonify(customer), 200
    except pymysql.Error as e:
        print(f"Veritabanı müşteri detay çekme hatası: {e}")
        return jsonify({'message': f'Veritabanı hatası oluştu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel müşteri detay çekme hatası: {e}")
        return jsonify({'message': 'Sunucu hatası, lütfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()

# Müşteri Güncelleme API (PUT)
@app.route('/api/customers/<int:customer_id>', methods=['PUT'])
def update_customer(customer_id):
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
    user_id = data.get('user_id') # Kullanıcı ID'si eklendi

    if not user_id: # user_id zorunlu hale getirildi
        return jsonify({'message': 'Kullanıcı ID eksik.'}), 400
    if not any([customer_name, status, contact_person, contact_title, phone, email, country, city, district, postal_code, address, notes]):
        return jsonify({'message': 'Güncellenecek veri bulunamadı.'}), 400

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Güncellenecek müşterinin mevcut adını al (loglama için)
            cursor.execute("SELECT customer_name FROM customers WHERE customer_id = %s", (customer_id,))
            existing_customer_info = cursor.fetchone()
            if not existing_customer_info:
                return jsonify({'message': 'Müşteri bulunamadı.'}), 404
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
                return jsonify({'message': 'Güncellenecek bir alan belirtilmedi.'}), 400

            sql = f"UPDATE customers SET {', '.join(updates)} WHERE customer_id = %s"
            params.append(customer_id)

            cursor.execute(sql, tuple(params))
            connection.commit()

            if cursor.rowcount == 0:
                return jsonify({'message': 'Müşteri verileri zaten güncel veya bir değişiklik yapılmadı.'}), 200

            # Aktivite loglama
            log_activity(
                user_id=user_id,
                title='Müşteri Güncellendi',
                description=f'"{old_customer_name}" adlı müşteri bilgileri güncellendi.',
                icon='fas fa-user-edit'
            )

        return jsonify({'message': 'Müşteri başarıyla güncellendi!'}), 200

    except pymysql.Error as e:
        print(f"Veritabanı müşteri güncelleme hatası: {e}")
        if e.args[0] == 1062:
            return jsonify({'message': 'Bu e-posta veya firma adı zaten kayıtlı.'}), 409
        return jsonify({'message': f'Veritabanı hatası oluştu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel müşteri güncelleme hatası: {e}")
        return jsonify({'message': 'Sunucu hatası, lütfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()

@app.route('/api/customers/<int:customer_id>', methods=['DELETE'])
def delete_customer(customer_id):
    user_id = request.args.get('user_id') # user_id query parametresinden alınır
    if not user_id:
        return jsonify({'message': 'Kullanıcı ID eksik.'}), 400

    customer_name = "Bilinmeyen Müşteri" # Loglama için varsayılan
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Müşteri adını silmeden önce al
            cursor.execute("SELECT customer_name FROM customers WHERE customer_id = %s", (customer_id,))
            customer_info = cursor.fetchone()
            if not customer_info:
                return jsonify({'message': 'Müşteri bulunamadı.'}), 404
            customer_name = customer_info['customer_name']

            sql = "DELETE FROM customers WHERE customer_id = %s"
            cursor.execute(sql, (customer_id,))
            connection.commit()

            if cursor.rowcount == 0:
                return jsonify({'message': 'Müşteri silinemedi veya zaten mevcut değil.'}), 404
            
            # Aktivite loglama
            log_activity(
                user_id=user_id,
                title='Müşteri Silindi',
                description=f'"{customer_name}" adlı müşteri silindi.',
                icon='fas fa-user-minus'
            )

        return jsonify({'message': 'Müşteri başarıyla silindi!'}), 200

    except pymysql.Error as e:
        print(f"Veritabanı müşteri silme hatası: {e}")
        if e.args[0] == 1451: # Foreign key constraint fails
            return jsonify({'message': 'Bu müşteriyle ilişkili projeler bulunmaktadır. Lütfen önce ilgili projeleri silin.'}), 409
        return jsonify({'message': f'Veritabanı hatası oluştu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel müşteri silme hatası: {e}")
        return jsonify({'message': 'Sunucu hatası, lütfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()


# Tüm Projeleri Listele API
@app.route('/api/projects', methods=['GET'])
def get_projects():
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Proje durumunu otomatik güncelleme mantığı
            cursor.execute("""
                UPDATE projects
                SET status = CASE
                    WHEN status = 'Tamamlandı' THEN 'Tamamlandı' -- Tamamlanan projeyi değiştirmeyin
                    WHEN CURDATE() < DATE(meeting_date) THEN 'Planlama Aşamasında'
                    WHEN CURDATE() >= DATE(start_date) AND CURDATE() <= DATE(end_date) THEN 'Aktif'
                    WHEN CURDATE() > DATE(end_date) AND status != 'Tamamlandı' THEN 'Gecikti'
                    ELSE status -- Diğer durumlar için mevcut status'u koru
                END
                WHERE status != 'Tamamlandı'; -- Sadece tamamlanmamış projeleri kontrol et
            """)
            connection.commit() # Genel durum güncelleyicilerini kaydet

            # Projeleri ve ilgili gecikme bilgilerini çek
            sql = """
            SELECT p.project_id, p.project_name, p.reference_no, p.description, p.contract_date,
                    p.meeting_date, p.start_date, p.end_date, p.project_location, p.status,
                    c.customer_name, u.fullname AS project_manager_name, c.customer_id, u.id AS project_manager_user_id,
                    (SELECT COUNT(*) FROM project_progress pp WHERE pp.project_id = p.project_id AND pp.delay_days > 0) AS has_step_delay,
                    -- Toplam delay_days'i de çek!
                    (SELECT IFNULL(SUM(pp.delay_days),0) FROM project_progress pp WHERE pp.project_id = p.project_id) AS delay_days
            FROM projects p
            JOIN customers c ON p.customer_id = c.customer_id
            JOIN users u ON p.project_manager_id = u.id
            ORDER BY p.created_at DESC
            """
            cursor.execute(sql)
            projects_data = cursor.fetchall()

            # İş adımı gecikmelerine göre durumu güncelle ve veritabanına kaydet
            projects_to_update_with_step_delay_status = []
            for project in projects_data:
                original_status = project['status']
                new_status = original_status

                # Sadece genel durumlar 'Aktif' veya 'Planlama Aşamasında' ise iş gecikmesini ekle
                if original_status == 'Aktif' and project['has_step_delay'] > 0:
                    new_status = 'Aktif (İş Gecikmeli)'
                elif original_status == 'Planlama Aşamasında' and project['has_step_delay'] > 0:
                    new_status = 'Planlama (İş Gecikmeli)'

                # Eğer durum değiştiyse, güncelleme listesine ekle
                if new_status != original_status:
                    projects_to_update_with_step_delay_status.append({'project_id': project['project_id'], 'status': new_status})

                # Frontend'e göndereceğimiz listedeki status'u güncelleyelim
                project['status'] = new_status

                # Tarih objelerini string'e dönüştür (JSON serileştirme için)
                project['contract_date'] = project['contract_date'].isoformat() if isinstance(project['contract_date'], datetime.date) else None
                project['meeting_date'] = project['meeting_date'].isoformat() if isinstance(project['meeting_date'], datetime.date) else None
                project['start_date'] = project['start_date'].isoformat() if isinstance(project['start_date'], datetime.date) else None
                project['end_date'] = project['end_date'].isoformat() if isinstance(project['end_date'], datetime.date) else None

            # Değişen projeleri veritabanında güncelle (iş adımı gecikmesi durumları için)
            if projects_to_update_with_step_delay_status:
                update_sql = "UPDATE projects SET status = %s WHERE project_id = %s"
                for proj_info in projects_to_update_with_step_delay_status:
                    cursor.execute(update_sql, (proj_info['status'], proj_info['project_id']))
                connection.commit() # Bu ikinci commit'i de yapalım

        return jsonify(projects_data), 200
    except pymysql.Error as e:
        print(f"Veritabanı proje çekme hatası: {e}")
        return jsonify({'message': f'Veritabanı hatası oluştu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel proje çekme hatası: {e}")
        return jsonify({'message': 'Sunucu hatası, lütfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()

# Tek bir projenin detaylarını çekme API'si (Modal için)
@app.route('/api/projects/<int:project_id>', methods=['GET'])
def get_project_details(project_id):
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
                return jsonify({'message': 'Proje bulunamadı.'}), 404

            # Tarih objelerini string'e dönüştür (JSON serileştirme için)
            project['contract_date'] = project['contract_date'].isoformat() if isinstance(project['contract_date'], datetime.date) else None
            project['meeting_date'] = project['meeting_date'].isoformat() if isinstance(project['meeting_date'], datetime.date) else None
            project['start_date'] = project['start_date'].isoformat() if isinstance(project['start_date'], datetime.date) else None
            project['end_date'] = project['end_date'].isoformat() if isinstance(project['end_date'], datetime.date) else None

        return jsonify(project), 200
    except pymysql.Error as e:
        print(f"Veritabanı proje detay çekme hatası: {e}")
        return jsonify({'message': f'Veritabanı hatası oluştu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel proje detay çekme hatası: {e}")
        return jsonify({'message': 'Sunucu hatası, lütfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()


# Proje Güncelleme API (PUT) - projects tablosu için
@app.route('/api/projects/<int:project_id>', methods=['PUT'])
def update_project(project_id):
    data = request.get_json()
    project_name = data.get('project_name')
    reference_no = data.get('reference_no')
    description = data.get('description')
    contract_date = data.get('contract_date')
    meeting_date = data.get('meeting_date')
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    project_location = data.get('project_location')
    status = data.get('status')
    user_id = data.get('user_id') # Kullanıcı ID'si eklendi

    if not user_id: # user_id zorunlu hale getirildi
        return jsonify({'message': 'Kullanıcı ID eksik.'}), 400

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Güncellenecek projenin mevcut adını al (loglama için)
            cursor.execute("SELECT project_name FROM projects WHERE project_id = %s", (project_id,))
            existing_project_info = cursor.fetchone()
            if not existing_project_info:
                return jsonify({'message': 'Proje bulunamadı.'}), 404
            old_project_name = existing_project_info['project_name']

            updates = []
            params = []
            if project_name is not None:
                updates.append("project_name = %s")
                params.append(project_name)
            if reference_no is not None:
                updates.append("reference_no = %s")
                params.append(reference_no)
            if description is not None:
                updates.append("description = %s")
                params.append(description)
            if contract_date is not None:
                updates.append("contract_date = %s")
                params.append(contract_date)
            if meeting_date is not None:
                updates.append("meeting_date = %s")
                params.append(meeting_date)
            if start_date is not None:
                updates.append("start_date = %s")
                params.append(start_date)
            if end_date is not None:
                updates.append("end_date = %s")
                params.append(end_date)
            if project_location is not None:
                updates.append("project_location = %s")
                params.append(project_location)
            if status is not None:
                updates.append("status = %s")
                params.append(status)

            if not updates:
                return jsonify({'message': 'Güncellenecek bir alan belirtilmedi.'}), 400

            sql = f"UPDATE projects SET {', '.join(updates)} WHERE project_id = %s"
            params.append(project_id)

            cursor.execute(sql, tuple(params))
            connection.commit()

            if cursor.rowcount == 0:
                return jsonify({'message': 'Proje verileri zaten güncel veya bir değişiklik yapılmadı.'}), 200

            # Aktivite loglama
            log_activity(
                user_id=user_id,
                title='Proje Güncellendi',
                description=f'"{old_project_name}" adlı proje bilgileri güncellendi.',
                icon='fas fa-edit'
            )

        return jsonify({'message': 'Proje başarıyla güncellendi!'}), 200

    except pymysql.Error as e:
        print(f"Veritabanı proje güncelleme hatası: {e}")
        return jsonify({'message': f'Veritabanı hatası oluştu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel proje güncelleme hatası: {e}")
        return jsonify({'message': 'Sunucu hatası, lütfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()

# Proje Silme API (DELETE)
@app.route('/api/projects/<int:project_id>', methods=['DELETE'])
def delete_project_api(project_id):
    user_id = request.args.get('user_id') # user_id query parametresinden alınır
    if not user_id:
        return jsonify({'message': 'Kullanıcı ID eksik.'}), 400

    project_name = "Bilinmeyen Proje" # Loglama için varsayılan
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Silinecek projenin bilgilerini (özellikle adını) alın
            cursor.execute("SELECT project_name, project_manager_id FROM projects WHERE project_id = %s", (project_id,))
            project_info = cursor.fetchone()

            if not project_info:
                return jsonify({'message': 'Proje silinemedi veya bulunamadı.'}), 404

            project_name = project_info['project_name']
            project_manager_id = project_info['project_manager_id']

            # Önce ilgili proje_progress kayıtlarını sil (varsa)
            cursor.execute("DELETE FROM project_progress WHERE project_id = %s", (project_id,))

            # Sonra projeyi sil
            sql = "DELETE FROM projects WHERE project_id = %s"
            cursor.execute(sql, (project_id,))
            connection.commit()

            if cursor.rowcount == 0:
                return jsonify({'message': 'Proje silinemedi veya bulunamadı.'}), 404

            # Aktivite loglama
            log_activity(
                user_id=user_id,
                title='Proje Silindi',
                description=f'"{project_name}" adlı proje silindi.',
                icon='fas fa-trash'
            )
           
        return jsonify({'message': 'Proje başarıyla silindi!'}), 200

    except pymysql.Error as e:
        print(f"Veritabanı proje silme hatası: {e}")
        if e.args[0] == 1451: # Foreign key constraint fails
            return jsonify({'message': 'Bu müşteriyle ilişkili projeler bulunmaktadır. Lütfen önce ilgili projeleri silin.'}), 409
        return jsonify({'message': f'Veritabanı hatası oluştu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel proje silme hatası: {e}")
        return jsonify({'message': 'Sunucu hatası, lütfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()


# Proje Yöneticilerini Listele API
@app.route('/api/project_managers', methods=['GET'])
def get_project_managers():
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, fullname FROM users WHERE role IN ('Teknisyen', 'Tekniker', 'Mühendis', 'Müdür', 'Proje Yöneticisi') ORDER BY fullname")
            managers = cursor.fetchall()
        return jsonify(managers), 200
    except pymysql.Error as e:
        print(f"Veritabanı yönetici çekme hatası: {e}")
        return jsonify({'message': f'Veritabanı hatası oluştu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel yönetici çekme hatası: {e}")
        return jsonify({'message': 'Sunucu hatası, lütfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()

# Konum verilerini veren API endpoint'i
@app.route('/api/locations/turkey', methods=['GET'])
def get_turkey_locations():
    if not TURKEY_LOCATIONS:
        return jsonify({'message': 'Konum verileri yüklenemedi veya boş.'}), 500
    return jsonify(TURKEY_LOCATIONS), 200

# Dashboard İstatistikleri API
@app.route('/api/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Aktif projeler: 'Aktif' ve 'Aktif (İş Gecikmeli)' durumundaki projeler
            cursor.execute("SELECT COUNT(project_id) AS count FROM projects WHERE status IN ('Aktif', 'Aktif (İş Gecikmeli)')")
            active_projects = cursor.fetchone()['count']

            cursor.execute("SELECT COUNT(project_id) AS count FROM projects WHERE status = 'Tamamlandı'")
            completed_projects = cursor.fetchone()['count']

            cursor.execute("SELECT COUNT(project_id) AS count FROM projects WHERE status IN ('Gecikti', 'Aktif (İş Gecikmeli)')")
            delayed_projects = cursor.fetchone()['count']

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
        print(f"Veritabanı istatistik çekme hatası: {e}")
        return jsonify({'message': f'Veritabanı hatası oluştu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel istatistik çekme hatası: {e}")
        return jsonify({'message': 'Sunucu hatası, lütfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()


# Dashboard Son Aktivite API (activities tablosundan çeker)
@app.route('/api/recent_activities', methods=['GET'])
def get_recent_activities():
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
                activities  -- 'activity' yerine 'activities' olarak düzeltildi
            ORDER BY
                created_at DESC
            LIMIT 5;
            """
            cursor.execute(sql)
            activities = cursor.fetchall()
            return jsonify(activities)
    except pymysql.Error as e:
        print(f"Veritabanı hatası (recent_activities): {e}")
        return jsonify({"error": "Veritabanı hatası oluştu."}), 500
    except Exception as e:
        print(f"Bilinmeyen hata (recent_activities): {e}")
        return jsonify({"error": "Bilinmeyen bir sunucu hatası oluştu."}), 500
    finally:
        if connection: # Sadece bir tane connection.close() çağrısı bırakıldı
            connection.close()


# Yeni bir aktivite kaydetmek için yardımcı fonksiyon
def log_activity(user_id, title, description, icon, is_read=0):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            user_fullname = "Bilinmeyen Kullanıcı"
            if user_id:
                # Kullanıcının tam adını çek
                cursor.execute("SELECT fullname FROM users WHERE id = %s", (user_id,))
                user = cursor.fetchone()
                if user:
                    user_fullname = user['fullname']

            # Remove (ID: X) pattern from description if it exists
            # Açıklama metninden '(ID: rakamlar)' desenini temizle
            cleaned_description = re.sub(r' \(ID: \d+\)', '', description)

            # Kullanıcı adını açıklamaya dahil et
            full_description = f"{user_fullname} tarafından: {cleaned_description}"

            # 'activity' yerine 'activities' olarak düzeltildi
            sql = """
            INSERT INTO activities (user_id, title, description, icon, created_at, is_read)
            VALUES (%s, %s, %s, %s, NOW(), %s)
            """
            cursor.execute(sql, (user_id, title, full_description, icon, is_read))
        connection.commit() # Değişiklikleri veritabanına kaydet
        print(f"Aktivite kaydedildi: Başlık: '{title}', Açıklama: '{full_description}'")
    except pymysql.Error as e:
        print(f"Aktivite kaydı sırasında hata: {e}")
    except Exception as e:
        print(f"Genel aktivite kaydı sırasında hata: {e}")
    finally:
        if connection:
            connection.close()

# Yeni Proje Ekle API (önceki yorum satırından çıkarıldı ve tamamlandı)
@app.route('/api/add_project', methods=['POST'])
def add_project():
    data = request.json
    project_name = data.get('project_name')
    customer_id = data.get('customer_id')
    project_manager_id = data.get('project_manager_id')
    reference_no = data.get('reference_no')
    description = data.get('description')
    contract_date = data.get('contract_date')
    meeting_date = data.get('meeting_date')
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    project_location = data.get('project_location')
    status = data.get('status', 'Planlama Aşamasında') # Default status

    user_id = data.get('user_id') # İşlemi yapan kullanıcı ID'si

    if not all([project_name, customer_id, project_manager_id, user_id]):
        return jsonify({'message': 'Proje adı, müşteri, proje yöneticisi ve kullanıcı ID zorunludur.'}), 400

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
                contract_date, meeting_date, start_date, end_date, project_location, status
            ))
            connection.commit()
            new_project_id = cursor.lastrowid

        log_activity(
            user_id=user_id,
            title='Yeni Proje Eklendi',
            description=f'"{project_name}" adlı yeni proje oluşturuldu.',
            icon='fas fa-plus'
        )
        return jsonify({"message": "Proje başarıyla eklendi", "project_id": new_project_id}), 201
    except pymysql.Error as e:
        print(f"Veritabanı proje ekleme hatası: {e}")
        return jsonify({'message': f'Veritabanı hatası oluştu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel proje ekleme hatası: {e}")
        return jsonify({'message': 'Sunucu hatası, lütfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()

# PDF Raporu Oluşturma Aktivitesini Loglama API'si (Frontend'den çağrılacak)
@app.route('/api/log_pdf_report', methods=['POST'])
def log_pdf_report_api():
    data = request.get_json()
    user_id = data.get('user_id')
    report_type = data.get('report_type', 'Genel Rapor') # Varsayılan rapor tipi
    project_name = data.get('project_name') # Tek proje için proje adı

    if not user_id:
        return jsonify({'message': 'Kullanıcı ID eksik.'}), 400

    description_text = f'"{report_type}" raporunun PDF dosyası oluşturuldu.'
    if project_name:
        description_text = f'"{project_name}" projesi için PDF raporu oluşturuldu.'

    try:
        log_activity(
            user_id=user_id,
            title='PDF Raporu Oluşturuldu',
            description=description_text,
            icon='fas fa-file-pdf'
        )
        return jsonify({'message': 'PDF raporu aktivitesi başarıyla kaydedildi.'}), 200
    except Exception as e:
        print(f"PDF raporu aktivitesi kaydetme hatası: {e}")
        return jsonify({'message': 'PDF raporu aktivitesi kaydedilirken hata oluştu.'}), 500


# Projenin İş Gidişatı Adımlarını Çekme API'si
@app.route('/api/projects/<int:project_id>/progress', methods=['GET'])
def get_project_progress_steps(project_id):
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            sql = """
            SELECT
                progress_id,          -- Tablonuzdaki sütun adı
                project_id,
                title AS step_name,   -- Frontend'de `step_name` olarak kullanılacak
                description,
                start_date,
                end_date,
                delay_days,
                created_at            -- `created_at` sütunu da çekilebilir
            FROM project_progress
            WHERE project_id = %s
            ORDER BY start_date ASC, created_at ASC -- Sıralama önemli
            """
            cursor.execute(sql, (project_id,))
            steps = cursor.fetchall()

            # Tarih objelerini string'e dönüştür
            for step in steps:
                step['start_date'] = step['start_date'].isoformat() if isinstance(step['start_date'], datetime.date) else None
                step['end_date'] = step['end_date'].isoformat() if isinstance(step['end_date'], datetime.date) else None
                # created_at de dateobj olabilir
                step['created_at'] = step['created_at'].isoformat() if isinstance(step['created_at'], datetime.datetime) else None

        return jsonify(steps), 200
    except pymysql.Error as e:
        print(f"Veritabanı iş adımı çekme hatası: {e}")
        return jsonify({'message': f'Veritabanı hatası oluştu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel iş adımı çekme hatası: {e}")
        return jsonify({'message': 'Sunucu hatası, lütfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()

# Yeni İş Gidişatı Adımı Ekleme API'si (projeler.html içinden çağrılır)
@app.route('/api/projects/<int:project_id>/progress', methods=['POST'])
def add_project_progress_step_from_modal(project_id):
    data = request.get_json()
    step_name = data.get('step_name')
    description = data.get('description')
    start_date_str = data.get('start_date')
    end_date_str = data.get('end_date')

    if not all([step_name, start_date_str, end_date_str]):
        return jsonify({'message': 'Başlık, başlangıç ve bitiş tarihi zorunludur.'}), 400

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Bu projeye ait en son bitiş tarihini bul
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
                if time_diff > 1: # Eğer başlangıç tarihi önceki bitiş tarihinden sonra 1 günden fazla ise
                    delay_days = time_diff - 1

            sql_insert = """
            INSERT INTO project_progress (project_id, title, description, start_date, end_date, delay_days)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql_insert, (project_id, step_name, description, start_date_str, end_date_str, delay_days))
            new_progress_id = cursor.lastrowid
            connection.commit()
        return jsonify({'message': 'İş adımı başarıyla eklendi!', 'progress_id': new_progress_id}), 201
    except pymysql.Error as e:
        print(f"Veritabanı iş adımı ekleme hatası: {e}")
        return jsonify({'message': f'Veritabanı hatası oluştu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel iş adımı ekleme hatası: {e}")
        return jsonify({'message': 'Sunucu hatası, lütfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()

# İş Gidişatı Adımı Güncelleme API'si
@app.route('/api/progress/<int:progress_id>', methods=['PUT'])
def update_project_progress_step(progress_id):
    data = request.get_json()
    step_name = data.get('step_name')
    description = data.get('description')
    start_date_str = data.get('start_date')
    end_date_str = data.get('end_date')

    if not all([step_name, start_date_str, end_date_str]):
        return jsonify({'message': 'Başlık, başlangıç ve bitiş tarihi zorunludur.'}), 400

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Adımın kendisini bul
            cursor.execute("SELECT project_id, end_date FROM project_progress WHERE progress_id = %s", (progress_id,))
            existing_step = cursor.fetchone()
            if not existing_step:
                return jsonify({'message': 'İş adımı bulunamadı.'}), 404

            current_project_id = existing_step['project_id']

            # Gecikme gününü yeniden hesapla (Önceki adımı bulmaya çalış)
            delay_days = 0
            # Aynı projede, güncellenen adımdan daha önceki bir bitiş tarihine sahip en son adımı bul
            cursor.execute("""
                SELECT MAX(end_date) as last_end_date
                FROM project_progress
                WHERE project_id = %s AND progress_id != %s AND end_date < %s
                ORDER BY end_date DESC LIMIT 1
            """, (current_project_id, progress_id, start_date_str))
            result = cursor.fetchone()
            previous_end_date = result['last_end_date'] if result and result['last_end_date'] else None

            new_step_start_dt = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()
            if previous_end_date:
                diff = (new_step_start_dt - previous_end_date).days
                if diff > 1:
                    delay_days = diff - 1

            sql_update = """
            UPDATE project_progress
            SET title = %s, description = %s, start_date = %s, end_date = %s, delay_days = %s
            WHERE progress_id = %s
            """
            cursor.execute(sql_update, (step_name, description, start_date_str, end_date_str, delay_days, progress_id))
            connection.commit()

            if cursor.rowcount == 0:
                return jsonify({'message': 'İş adımı verileri zaten güncel veya bir değişiklik yapılmadı.'}), 200


        return jsonify({'message': 'İş adımı başarıyla güncellendi!'}), 200
    except pymysql.Error as e:
        print(f"Veritabanı iş adımı güncelleme hatası: {e}")
        return jsonify({'message': f'Veritabanı hatası oluştu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel iş adımı güncelleme hatası: {e}")
        return jsonify({'message': 'Sunucu hatası, lütfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()

# İş Gidişatı Adımı Silme API'si
@app.route('/api/progress/<int:progress_id>', methods=['DELETE'])
def delete_project_progress_step(progress_id):
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            sql = "DELETE FROM project_progress WHERE progress_id = %s"
            cursor.execute(sql, (progress_id,))
            connection.commit()

            if cursor.rowcount == 0:
                return jsonify({'message': 'İş adımı silinemedi veya bulunamadı.'}), 404

        return jsonify({'message': 'İş adımı başarıyla silindi!'}), 200
    except pymysql.Error as e:
        print(f"Veritabanı iş adımı silme hatası: {e}")
        return jsonify({'message': f'Veritabanı hatası oluştu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel iş adımı silme hatası: {e}")
        return jsonify({'message': 'Sunucu hatası, lütfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()

# oturum açma bilgisi alma

@app.route('/api/user-info', methods=['GET'])
def get_user_info():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'message': 'Kullanıcı ID eksik'}), 400

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Update to use 'fullname' and 'role' consistent with 'users' table
            cursor.execute("SELECT id, fullname, email, role FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            if not user:
                return jsonify({'message': 'Kullanıcı bulunamadı'}), 404
            return jsonify(user), 200
    except Exception as e:
        print(f"Genel kullanıcı bilgisi çekme hatası: {e}")
        return jsonify({'message': 'Sunucu hatası, lütfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()

@app.route('/api/users', methods=['GET'])
def get_all_users():
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Update to use 'fullname' and 'role' consistent with 'users' table
            cursor.execute("SELECT id, fullname, email, role FROM users")
            users = cursor.fetchall()
            return jsonify(users), 200
    except pymysql.Error as e:
        print(f"Veritabanı tüm kullanıcıları çekme hatası: {e}")
        return jsonify({'message': f'Veritabanı hatası oluştu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel tüm kullanıcıları çekme hatası: {e}")
        return jsonify({'message': 'Sunucu hatası, lütfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()

@app.route('/api/users', methods=['POST'])
def add_user():
    data = request.get_json()
    fullname = data.get('fullname')
    email = data.get('email')
    phone = data.get('phone', '')
    password = data.get('password')
    role = data.get('role')

    if not fullname or not email or not password or not role:
        return jsonify({'message': 'Tüm alanlar zorunludur!'}), 400

    onay = 1
    created_at = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    try:
        # Şifreyi bcrypt ile hashle
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        hashed_password = hashed_password.decode('utf-8')  # bytes -> str

        connection = get_db_connection()
        with connection.cursor() as cursor:
            sql = """
            INSERT INTO users (fullname, email, phone, password, role, created_at, onay)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (fullname, email, phone, hashed_password, role, created_at, onay))
            connection.commit()
        return jsonify({'message': 'Kullanıcı başarıyla eklendi!'}), 201
    except pymysql.Error as e:
        print(f"Veritabanı kullanıcı ekleme hatası: {e}")
        if e.args[0] == 1062:
            return jsonify({'message': 'Bu e-posta adresi zaten kullanılıyor.'}), 409
        return jsonify({'message': f'Veritabanı hatası oluştu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel kullanıcı ekleme hatası: {e}")
        return jsonify({'message': 'Sunucu hatası, lütfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()

@app.route('/ayarlar')
def ayarlar_page():
    return render_template('ayarlar.html')

@app.route('/api/roles', methods=['GET'])
def get_distinct_roles():
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            sql = "SELECT DISTINCT role FROM users WHERE role != 'Admin'"
            cursor.execute(sql)
            roles = [row['role'] for row in cursor.fetchall()]

        return jsonify(roles), 200
    except pymysql.Error as e:
        print(f"Veritabanı rol çekme hatası: {e}")
        return jsonify({'message': f'Veritabanı hatası oluştu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel rol çekme hatası: {e}")
        return jsonify({'message': 'Sunucu hatası, lütfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()
from flask import request, jsonify


@app.route('/api/tasks', methods=['GET'])
def get_tasks():
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
        print(f"Görevleri çekme hatası: {e}")
        return jsonify({'message': 'Görevler çekilemedi.'}), 500
    finally:
        if connection:
            connection.close()

@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    data = request.get_json()
    title = data.get('title')
    description = data.get('description')
    start = data.get('start')
    end = data.get('end')
    priority = data.get('priority', 'medium')
    assigned_user_id = int(data.get('assigned_user_id')) if data.get('assigned_user_id') else None
    created_by = int(data.get('created_by')) if data.get('created_by') else None

    if not all([title, start, assigned_user_id, created_by]):
        return jsonify({'message': 'Zorunlu alanlar eksik!'}), 400

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            sql = """
                UPDATE tasks
                SET title=%s, description=%s, start=%s, end=%s, priority=%s, assigned_user_id=%s, created_by=%s
                WHERE id=%s
            """
            cursor.execute(sql, (title, description, start, end, priority, assigned_user_id, created_by, task_id))
            connection.commit()
        return jsonify({'message': 'Görev başarıyla güncellendi!'}), 200
    except Exception as e:
        print(f"Görev güncelleme hatası: {e}")
        return jsonify({'message': 'Görev güncellenirken hata oluştu.'}), 500
    finally:
        if connection:
            connection.close()

@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
            connection.commit()
        return jsonify({'message': 'Görev başarıyla silindi!'}), 200
    except Exception as e:
        print(f"Görev silme hatası: {e}")
        return jsonify({'message': 'Görev silinirken hata oluştu.'}), 500
    finally:
        if connection:
            connection.close()
@app.route('/api/manager-stats')
def manager_stats():
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = """
            SELECT 
                p.project_manager_id,
                u.fullname as manager_name,
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
                END) AS on_time_projects,
                SUM(CASE 
                        WHEN (
                            SELECT SUM(pr.delay_days) 
                            FROM project_progress pr 
                            WHERE pr.project_id = p.project_id
                        ) > 0 
                    THEN 1 
                    ELSE 0 
                END) AS delayed_projects,
                (SELECT SUM(pr.delay_days) 
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
                        WHEN p.status = 'Bitti' AND (\
                            SELECT SUM(pr.delay_days) 
                            FROM project_progress pr 
                            WHERE pr.project_id = p.project_id
                        ) IS NULL OR (\
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
