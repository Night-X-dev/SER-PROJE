# app.py
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
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

load_dotenv()

app = Flask(__name__)
# Oturum yönetimi gizli anahtarı
# BU, GÜVENLİ VE TAHMİN EDİLEMEYEN BİR DİZE İLE DEĞİŞTİRİLMELİDİR!
app.secret_key = os.getenv("SECRET_KEY", "supersecretkeythatshouldbemorecomplex") 
CORS(app, resources={r"/*": {"origins": ["https://37.148.213.89:8000", "http://serotomasyon.tr"]}}, supports_credentials=True)
@app.route('/')
@app.route('/login.html') # Her iki URL de aynı fonksiyona yönlendirilecektir
def serve_login_page():
    """Kök URL (/) ve /login.html isteklerini login.html sayfasına yönlendirir."""
    return render_template('login.html')

@app.route('/index.html')
def serve_index_page():
    """/index.html isteklerini index.html sayfasına yönlendirir."""
    return render_template('index.html')

@app.route('/ayarlar.html')
def serve_ayarlar_page():
    """/ayarlar.html isteklerini ayarlar.html sayfasına yönlendirir.
    Tüm giriş yapmış kullanıcılar erişebilir, ancak içerik role göre ön uçta gizlenecektir."""
    if 'user_id' not in session:
        return redirect(url_for('serve_login_page'))
    # Tüm giriş yapmış kullanıcıların ayarlar sayfasına erişmesine izin ver
    return render_template('ayarlar.html')


@app.route('/kayitonay.html')
def serve_kayitonay_page():
    """/kayitonay.html isteklerini kayitonay.html sayfasına yönlendirir."""
    return render_template('kayitonay.html')

@app.route('/musteriler.html')
def serve_musteriler_page():
    """/musteriler.html isteklerini musteriler.html sayfasına yönlendirir."""
    return render_template('musteriler.html')

@app.route('/proje_ekle.html')
def serve_proje_ekle_page():
    """/proje_ekle.html isteklerini proje_ekle.html sayfasına yönlendirir."""
    return render_template('proje_ekle.html')

@app.route('/projeler.html')
def serve_projeler_page():
    """/projeler.html isteklerini projeler.html sayfasına yönlendirir."""
    return render_template('projeler.html')

@app.route('/raporlar.html')
def serve_raporlar_page():
    """/raporlar.html isteklerini raporlar.html sayfasına yönlendirir.
    Kullanıcının giriş yapıp raporlara erişim izni olup olmadığını kontrol eder."""
    # Kullanıcının giriş yapıp yapmadığını kontrol et
    if 'user_id' not in session:
        return redirect(url_for('serve_login_page')) # Giriş yapılmadıysa giriş sayfasına yönlendir

    user_id = session['user_id']
    user_role = get_user_role_from_db(user_id) # Veritabanından kullanıcı rolünü al

    if user_role:
        # Rolün rapor izni olup olmadığını kontrol et
        has_permission = check_role_permission(user_role, 'raporlar')
        if has_permission:
            return render_template('raporlar.html')
        else:
            # İzin yoksa ana sayfaya yönlendir
            return redirect(url_for('serve_index_page')) 
    else:
        # Kullanıcı rolü bulunamazsa giriş sayfasına yönlendir
        return redirect(url_for('serve_login_page'))

@app.route('/takvim.html')
def serve_takvim_page():
    """/takvim.html isteklerini takvim.html sayfasına yönlendirir."""
    return render_template('takvim.html')

@app.route('/users.html')
def serve_users_page():
    """/users.html isteklerini users.html sayfasına yönlendirir.
    Kullanıcının giriş yapmış olmasını gerektirir."""
    if 'user_id' not in session:
        return redirect(url_for('serve_login_page'))
    return render_template('users.html')

@app.route('/waiting.html')
def serve_waiting_page():
    """/waiting.html isteklerini waiting.html sayfasına yönlendirir."""
    return render_template('waiting.html')

@app.route('/yeni_musteri.html')
def serve_yeni_musteri_page():
    """/yeni_musteri.html isteklerini yeni_musteri.html sayfasına yönlendirir."""
    return render_template('yeni_musteri.html')

@app.route('/bildirim.html')
def serve_bildirim_page():
    """/bildirim.html isteklerini bildirim.html sayfasına yönlendirir."""
    return render_template('bildirim.html')

# CORS (Cross-Origin Resource Sharing) ayarları
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

def get_db_connection():
    """Veritabanı bağlantısı kurar ve döndürür."""
    connection = None
    try:
        # Eğer MySQL_PUBLIC_URL gibi tek bir URL ortam değişkeni kullanılıyorsa, onu ayrıştırmayı dener.
        # XCloud'un böyle bir URL sağlamadığını varsayarak bu kısım muhtemelen çalışmayacaktır.
        # Ancak kodunuzda olduğu için bırakıyorum.
        public_url = os.getenv("MYSQL_PUBLIC_URL")
        if public_url:
            try:
                parsed_url = urllib.parse.urlparse(public_url)
                host = parsed_url.hostname
                port = parsed_url.port if parsed_url.port else 3306
                user = parsed_url.username
                password = parsed_url.password
                database = parsed_url.path.lstrip('/')
                print(f"DEBUG: Ayrıştırılmış genel URL kullanılıyor. Host={host}, Port={port}, User={user}, DB={database}")
            except Exception as url_parse_e:
                print(f"HATA: MYSQL_PUBLIC_URL ayrıştırılamad\u0131: {url_parse_e}. Sabit değerlere veya bireysel ortam değişkenlerine geri dönülüyor.")
                # URL ayrıştırma hatası durumunda sabit değerlere veya bireysel ortam değişkenlerine düşer
                host = os.getenv("MYSQL_HOST", "localhost")
                port = int(os.getenv("MYSQL_PORT", 3306))
                user = os.getenv("MYSQL_USER", "admin") # Güncellendi
                password = os.getenv("MYSQL_PASSWORD", "Ser171234") # Güncellendi
                database = os.getenv("MYSQL_DATABASE", "ser_db") # Güncellendi
                print(f"DEBUG: Ortam değişkenleri veya sabit değerler kullanılıyor: Host={host}, Port={port}, User={user}, DB={database}")
        else:
            print("DEBUG: MYSQL_PUBLIC_URL bulunamad\u0131 veya bo\u015f. Ortam değişkenleri veya sabit değerler kullanılıyor.")
            # MYSQL_PUBLIC_URL yoksa veya boşsa, bireysel ortam değişkenlerini kullanır.
            # Eğer ortam değişkenleri de yoksa, burada belirttiğiniz sabit değerleri kullanır.
            host = os.getenv("MYSQL_HOST", "localhost")
            port = int(os.getenv("MYSQL_PORT", 3306))
            user = os.getenv("MYSQL_USER", "admin") # Güncellendi
            password = os.getenv("MYSQL_PASSWORD", "Ser171234") # Güncellendi
            database = os.getenv("MYSQL_DATABASE", "ser_db") # Güncellendi
            print(f"DEBUG: Ortam değişkenleri veya sabit değerler kullanılıyor: Host={host}, Port={port}, User={user}, DB={database}")

        connection = pymysql.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            port=port,
            cursorclass=pymysql.cursors.DictCursor
        )
        print("MySQL veritaban\u0131na ba\u015far\u0131yla ba\u011fland\u0131!")
        return connection
    except pymysql.Error as e:
        print(f"MySQL ba\u011flant\u0131 hatas\u0131: {e}")
        if connection:
            connection.close()
        raise

# Yardımcı fonksiyon: Veritabanından kullanıcı rolünü alır
def get_user_role_from_db(user_id):
    """Veritabanından bir kullanıcının rolünü getirir."""
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT role FROM users WHERE id = %s", (user_id,))
            result = cursor.fetchone()
            return result['role'] if result else None
    except Exception as e:
        print(f"Kullan\u0131c\u0131 rol\u00FC \u00E7ekilirken hata: {e}")
        return None
    finally:
        if connection:
            connection.close()

# Yardımcı fonksiyon: Bir rolün belirli bir izne sahip olup olmadığını kontrol eder
def check_role_permission(role_name, permission_key):
    """Belirli bir rolün belirli bir izne sahip olup olmadığını kontrol eder."""
    # Admin rolü her zaman tüm izinlere sahip kabul edilir
    if role_name.lower() == 'admin':
        return True

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # 'yetki' tablosundaki ilgili izin sütununu sorgula
            sql = f"SELECT {permission_key} FROM yetki WHERE LOWER(role_name) = %s"
            cursor.execute(sql, (role_name.lower(),))
            result = cursor.fetchone()
            
            # Rol için izin kaydı yoksa veya izin değeri 0 ise False döndür
            if result and result[permission_key] == 1:
                return True
            return False
    except Exception as e:
        print(f"\u0130zin kontrol\u00FC s\u0131ras\u0131nda hata: {e}")
        return False
    finally:
        if connection:
            connection.close()


# Tüm bildirimleri okundu olarak işaretle API'si (bildirimler tablosu için)
@app.route('/api/notifications/mark_all_read', methods=['PUT'])
def mark_all_notifications_as_read():
    """Veritabanındaki tüm bildirimleri okundu olarak işaretler."""
    data = request.get_json() # PUT istekleri için get_json() kullanın
    user_id = data.get('user_id') # İstek gövdesinden user_id'yi alın
    if not user_id:
        return jsonify({'message': 'Kullan\u0131c\u0131 ID\'si eksik.'}), 400

    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = "UPDATE notifications SET is_read = 1 WHERE user_id = %s AND is_read = 0" 
            cursor.execute(sql, (user_id,))
            connection.commit()
            rows_affected = cursor.rowcount 
        return jsonify({'message': f'{rows_affected} bildirim okundu olarak i\u015faretlendi.'}), 200
    except pymysql.Error as e:
        print(f"Veritaban\u0131 hatas\u0131 t\u00FCm bildirimleri g\u00FCncellerken: {e}")
        return jsonify({'message': f'Veritaban\u0131 hatas\u0131 olu\u015ftu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel hata t\u00FCm bildirimleri g\u00FCncellerken: {e}")
        return jsonify({'message': 'Sunucu hatas\u0131, l\u00FCtfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()

# Okunmamış Bildirim Sayısı API'si (bildirimler tablosu için)
@app.route('/api/notifications/unread-count', methods=['GET'])
def get_unread_notifications_count():
    """Veritabanındaki okunmamış bildirim sayısını döndürür."""
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'unread_count': 0, 'message': 'Kullan\u0131c\u0131 ID\'si eksik.'}), 400

    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = "SELECT COUNT(id) as unread_count FROM notifications WHERE user_id = %s AND is_read = 0"
            cursor.execute(sql, (user_id,))
            result = cursor.fetchone()
            return jsonify(result), 200
    except pymysql.Error as e:
        print(f"Veritaban\u0131 hatas\u0131 okunmam\u0131\u015f bildirim say\u0131s\u0131n\u0131 \u00E7ekerken: {e}")
        return jsonify({'message': f'Veritaban\u0131 hatas\u0131 olu\u015ftu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel hata okunmam\u0131\u015f bildirim say\u0131s\u0131n\u0131 \u00E7ekerken: {e}")
        return jsonify({'message': 'Sunucu hatas\u0131, l\u00FCtfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()


# Bildirimi Okundu Olarak İşaretle API'si (bildirimler tablosu için)
@app.route('/api/notifications/<int:notification_id>/read', methods=['PUT'])
def mark_notification_as_read(notification_id):
    """Belirli bir bildirimi veritabanında okundu olarak işaretler."""
    data = request.get_json()
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({'message': 'Kullan\u0131c\u0131 ID\'si eksik.'}), 400

    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM notifications WHERE id = %s AND user_id = %s", (notification_id, user_id))
            if not cursor.fetchone():
                return jsonify({'message': 'Bildirim bulunamad\u0131 veya de\u011fi\u015ftirme izniniz yok.'}), 404

            sql = "UPDATE notifications SET is_read = 1 WHERE id = %s"
            cursor.execute(sql, (notification_id,))
            connection.commit()

        return jsonify({'message': 'Bildirim ba\u015far\u0131yla okundu olarak i\u015faretlendi.'}), 200
    except pymysql.Error as e:
        print(f"Veritaban\u0131 hatas\u0131 bildirimi g\u00FCncellerken: {e}")
        return jsonify({'message': f'Veritaban\u0131 hatas\u0131 olu\u015ftu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel hata bildirimi g\u00FCncellerken: {e}")
        return jsonify({'message': 'Sunucu hatas\u0131, l\u00FCtfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()

# Bildirimleri Getir API'si (bildirimler tablosu için)
@app.route('/api/notifications', methods=['GET'])
def get_notifications():
    """Belirli bir kullanıcı için bildirimleri getirir."""
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'message': 'Kullan\u0131c\u0131 ID\'si eksik.'}), 400

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
                # created_at'ı ISO formatına çevir
                if 'created_at' in row and isinstance(row['created_at'], datetime.datetime):
                    row['created_at'] = row['created_at'].isoformat()
            return jsonify(result)
    except pymysql.Error as e:
        print(f"Veritaban\u0131 hatas\u0131 bildirimleri \u00E7ekerken: {e}")
        return jsonify({'message': f'Veritaban\u0131 hatas\u0131 olu\u015ftu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel hata bildirimleri \u00E7ekerken: {e}")
        return jsonify({'message': 'Sunucu hatas\u0131, l\u00FCtfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()

@app.route('/api/notifications/<int:notification_id>', methods=['DELETE'])
def delete_notification(notification_id):
    """Giriş yapmış kullanıcı için belirli bir bildirimi siler."""
    data = request.get_json()
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({'message': 'Kullan\u0131c\u0131 ID\'si eksik.'}), 400

    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM notifications WHERE id = %s AND user_id = %s", (notification_id, user_id))
            if not cursor.fetchone():
                return jsonify({'message': 'Bildirim bulunamad\u0131 veya silme izniniz yok.'}), 404

            cursor.execute("DELETE FROM notifications WHERE id = %s", (notification_id,))
            connection.commit()
            return jsonify({'message': 'Bildirim silindi.'}), 200
    except Exception as e:
        print(f"Bildirim silme hatas\u0131: {e}")
        return jsonify({'message': 'Sunucu hatas\u0131'}), 500
    finally:
        connection.close()

@app.route('/api/notifications/all', methods=['DELETE'])
def delete_all_notifications():
    """Giriş yapmış kullanıcı için tüm bildirimleri siler."""
    data = request.get_json()
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({'message': 'Kullan\u0131c\u0131 ID\'si eksik.'}), 400

    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM notifications WHERE user_id = %s", (user_id,))
            connection.commit()
            return jsonify({'message': 'T\u00FCm bildirimleriniz silindi.'})
    except Exception as e:
        if connection:
            connection.rollback()
        return jsonify({'message': f'Hata: {str(e)}'}), 500
    finally:
        connection.close()


# Yeni Bildirim Ekle API'si (bildirimler tablosu için)
@app.route('/api/notifications', methods=['POST'])
def add_notification():
    """Veritabanına yeni bir bildirim ekler."""
    data = request.get_json()
    user_id = data.get('user_id')
    title = data.get('title')
    message = data.get('message') 

    if not all([user_id, title, message]):
        return jsonify({'message': 'Kullan\u0131c\u0131 ID\'si, ba\u015fl\u0131k ve mesaj zorunludur.'}), 400

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
        return jsonify({'message': 'Bildirim ba\u015far\u0131yla kaydedildi!'}), 201
    except pymysql.Error as e:
        print(f"Veritaban\u0131 hatas\u0131 bildirim kaydederken: {e}")
        if e.args[0] == 1062:
            return jsonify({'message': 'Bu e-posta adresi zaten kullan\u0131mda.'}), 409
        return jsonify({'message': f'Veritaban\u0131 hatas\u0131 olu\u015ftu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel hata bildirim kaydederken: {e}")
        return jsonify({'message': 'Sunucu hatas\u0131, l\u00FCtfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()

# Yeni Aktivite Ekle API'si (aktiviteler tablosu için)
@app.route('/api/activities', methods=['POST'])
def add_activity():
    """Veritabanına yeni bir aktivite ekler."""
    data = request.get_json()
    user_id = data.get('user_id')
    title = data.get('title')
    description = data.get('description')
    icon = data.get('icon', 'fas fa-info-circle') 

    if not all([user_id, title, description]):
        return jsonify({'message': 'Kullan\u0131c\u0131 ID\'si, ba\u015fl\u0131k ve a\u00E7\u0131klama zorunludur.'}), 400

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
        return jsonify({'message': 'Aktivite ba\u015far\u0131yla kaydedildi!'}), 201
    except pymysql.Error as e:
        print(f"Veritaban\u0131 hatas\u0131 aktivite kaydederken: {e}")
        return jsonify({'message': f'Veritaban\u0131 hatas\u0131 olu\u015ftu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel hata aktivite kaydederken: {e}")
        return jsonify({'message': 'Sunucu hatas\u0131, l\u00FCtfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()

@app.route('/api/update_user_profile', methods=['POST'])
def update_user_profile():
    """Kullanıcının profil bilgilerini, profil resmi ve görünürlük ayarları dahil olmak üzere günceller.
    Kişisel detaylar (tam ad, e-posta, telefon, rol) artık bu uç nokta üzerinden güncellenmez,
    çünkü bu alanlar için ön uç modalı kaldırılmıştır."""
    data = request.get_json()
    user_id = data.get('userId')
    profile_picture = data.get('profile_picture') 
    hide_email = data.get('hide_email') 
    hide_phone = data.get('hide_phone') 

    if not user_id:
        return jsonify({'message': 'Kullan\u0131c\u0131 ID\'si eksik.'}), 400

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT profile_picture, hide_email, hide_phone FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()

            if not user:
                return jsonify({'message': 'Kullan\u0131c\u0131 bulunamad\u0131.'}), 404

            updates = []
            params = []
            message_parts = []

            if profile_picture is not None: 
                if profile_picture == "null": 
                    updates.append("profile_picture = NULL")
                    message_parts.append("Profil Resmi Kald\u0131r\u0131ld\u0131")
                elif profile_picture != user['profile_picture']: 
                    updates.append("profile_picture = %s")
                    params.append(profile_picture)
                    message_parts.append("Profil Resmi")
            
            if hide_email is not None and hide_email != user['hide_email']:
                updates.append("hide_email = %s")
                params.append(hide_email)
                message_parts.append("E-posta G\u00F6r\u00FCn\u00FCrl\u00FC\u011F\u00FC")

            if hide_phone is not None and hide_phone != user['hide_phone']:
                updates.append("hide_phone = %s")
                params.append(hide_phone)
                message_parts.append("Telefon G\u00F6r\u00FCn\u00FCrl\u00FC\u011F\u00FC")

            if not updates:
                return jsonify({'message': 'G\u00FCncellenecek bilgi bulunamad\u0131.'}), 200

            sql = f"UPDATE users SET {', '.join(updates)} WHERE id = %s"
            params.append(user_id)

            cursor.execute(sql, tuple(params))
            connection.commit()

            final_message = "Ba\u015far\u0131yla g\u00FCncellendi: " + ", ".join(message_parts) + "."
            if not message_parts: 
                 final_message = "G\u00FCncellenecek de\u011fi\u015fiklik bulunamad\u0131."

            return jsonify({'message': final_message}), 200

    except pymysql.Error as e:
        print(f"Veritaban\u0131 hatas\u0131 profil g\u00FCncellerken: {e}")
        return jsonify({'message': f'Veritaban\u0131 hatas\u0131 olu\u015ftu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel hata profil g\u00FCncellerken: {e}")
        return jsonify({'message': 'Sunucu hatas\u0131, l\u00FCtfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()

@app.route('/api/pending-users', methods=['GET'])
def get_pending_users():
    """'Onay' durumu 0 olan kullanıcıları getirir."""
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor(pymysql.cursors.DictCursor) as cursor: 
            sql = "SELECT id, fullname, email, phone, role, created_at FROM users WHERE onay = 0"
            cursor.execute(sql)
            pending_users = cursor.fetchall()
            return jsonify(pending_users), 200
    except pymysql.Error as e:
        print(f"Veritaban\u0131 hatas\u0131 bekleyen kullan\u0131c\u0131lar\u0131 \u00E7ekerken: {e}")
        return jsonify({'message': f'Veritaban\u0131 hatas\u0131 olu\u015ftu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel hata bekleyen kullan\u0131c\u0131lar\u0131 \u00E7ekerken: {e}")
        return jsonify({'message': 'Sunucu hatas\u0131, l\u00FCtfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()

@app.route('/api/users/approve/<int:user_id>', methods=['PATCH'])
def approve_user(user_id):
    """Bir kullanıcının 'onay' durumunu 1 olarak ayarlayarak onaylar."""
    data = request.get_json()
    actor_user_id = data.get('actor_user_id') # Onaylama işlemini yapan kullanıcı

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, fullname, onay FROM users WHERE id = %s", (user_id,))
            user_to_approve = cursor.fetchone()
    
            if not user_to_approve:
                return jsonify({'message': 'Kullan\u0131c\u0131 bulunamad\u0131.'}), 404
            if user_to_approve['onay'] == 1:
                return jsonify({'message': 'Kullan\u0131c\u0131 zaten onaylanm\u0131\u015f.'}), 400 

            sql = "UPDATE users SET onay = 1 WHERE id = %s"
            cursor.execute(sql, (user_id,))
            connection.commit()

            # Aktivite kaydı
            log_activity(
                user_id=actor_user_id, # Onaylayan kişi
                title='Kullan\u0131c\u0131 Onayland\u0131',
                description=f'"{user_to_approve["fullname"]}" adl\u0131 kullan\u0131c\u0131 onayland\u0131.',
                icon='fas fa-user-check',
                target_user_id=user_id # Onaylanan kişi
            )

        return jsonify({'message': 'Kullan\u0131c\u0131 ba\u015far\u0131yla onayland\u0131!'}), 200

    except pymysql.Error as e:
        print(f"Veritaban\u0131 hatas\u0131 kullan\u0131c\u0131y\u0131 onaylarken: {e}")
        return jsonify({'message': f'Veritaban\u0131 hatas\u0131 olu\u015ftu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel hata kullan\u0131c\u0131y\u0131 onaylarken: {e}")
        return jsonify({'message': 'Sunucu hatas\u0131, l\u00FCtfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Bir kullanıcıyı siler ve ilişkili projelerini ve görevlerini yeniden atar veya siler."""
    data = request.get_json()
    actor_user_id = data.get('actor_user_id') # Silme işlemini yapan kullanıcı

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, fullname FROM users WHERE id = %s", (user_id,))
            user_info = cursor.fetchone()
            if not user_info:
                return jsonify({'message': 'Kullan\u0131c\u0131 bulunamad\u0131.'}), 404

            if user_info['id'] == 1: 
                 return jsonify({'message': 'Bu kullan\u0131c\u0131 silinemez.'}), 403 

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
                print(f"DEBUG: {cursor.rowcount} proje kullan\u0131c\u0131 {user_id}'den {default_manager_id}'e yeniden atand\u0131.")
            else:
                cursor.execute("DELETE FROM projects WHERE project_manager_id = %s", (user_id,))
                print(f"DEBUG: Kullan\u0131c\u0131 {user_id} i\u00E7in {cursor.rowcount} proje silindi (yeniden atanacak y\u00F6netici yok).")

            cursor.execute("DELETE FROM tasks WHERE assigned_user_id = %s", (user_id,))
            print(f"DEBUG: Kullan\u0131c\u0131 {user_id} i\u00E7in {cursor.rowcount} g\u00F6rev silindi.")

            sql = "DELETE FROM users WHERE id = %s"
            cursor.execute(sql, (user_id,))
            connection.commit()
            print(f"DEBUG: Kullan\u0131c\u0131 {user_id} silindi.")

            # Aktivite kaydı
            log_activity(
                user_id=actor_user_id, # Silme işlemini yapan kişi
                title='Kullan\u0131c\u0131 Silindi',
                description=f'"{user_info["fullname"]}" adl\u0131 kullan\u0131c\u0131 silindi.',
                icon='fas fa-user-times',
                target_user_id=user_id # Silinen kişi
            )

        return jsonify({'message': 'Kullan\u0131c\u0131 ba\u015far\u0131yla silindi!'}), 200

    except pymysql.Error as e:
        print(f"Veritaban\u0131 hatas\u0131 kullan\u0131c\u0131 silerken: {e}")
        return jsonify({'message': f'Veritaban\u0131 hatas\u0131 olu\u015ftu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel hata kullan\u0131c\u0131 silerken: {e}")
        return jsonify({'message': 'Sunucu hatas\u0131, l\u00FCtfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()

TURKEY_LOCATIONS = {}
try:
    script_dir = os.path.dirname(__file__)
    file_path = os.path.join(script_dir, 'turkey_locations.json')
    with open(file_path, 'r', encoding='utf-8') as f:
        TURKEY_LOCATIONS = json.load(f)
    print("Konum verileri ba\u015far\u0131yla y\u00FCklendi.")
except FileNotFoundError:
    print(f"Hata: 'turkey_locations.json' dosyas\u0131 bulunamad\u0131. L\u00FCtfen '{file_path}' yolunu kontrol edin.")
    TURKEY_LOCATIONS = {"T\u00FCrkiye": {"iller": {"Varsay\u0131lan \u0130l": []}}} 
except json.JSONDecodeError:
    print("Hata: 'turkey_locations.json' dosyas\u0131 JSON format\u0131nda de\u011fil veya bozuk.")
    TURKEY_LOCATIONS = {"T\u00FCrkiye": {"iller": {"Varsay\u0131lan \u0130l": []}}} 
except Exception as e:
    print(f"Konum verileri y\u00FCklenirken beklenmeyen hata: {e}")
    TURKEY_LOCATIONS = {"T\u00FCrkiye": {"iller": {"Varsay\u0131lan \u0130l": []}}} 


@app.route('/api/role-permissions', methods=['GET'])
def get_permissions_by_role():
    """Belirli bir rol için izinleri getirir."""
    role_name = request.args.get('role')
    if not role_name:
        return jsonify({'message': 'Rol ad\u0131 gerekli'}), 400

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            sql = "SELECT proje_ekle, proje_duzenle, proje_sil, pdf_olusturma, musteri_duzenleme, raporlar FROM yetki WHERE LOWER(role_name) = %s"
            cursor.execute(sql, (role_name.lower(),))
            result = cursor.fetchone()
            if not result:
                # Rol için izin kaydı yoksa, varsayılan olarak tüm izinleri 0 olarak döndür
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
    """Belirli bir rol için izinleri günceller."""
    data = request.json
    role = data.get('role')
    if not role:
        return jsonify({'message': 'Rol belirtilmedi.'}), 400

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
        return jsonify({'message': 'Yetkiler ba\u015far\u0131yla g\u00FCncellendi.'})
    except Exception as e:
        if connection:
            connection.rollback()
        return jsonify({'message': f'Hata: {str(e)}'}), 500
    finally:
        if connection:
            connection.close()

# Kullanıcı Kayıt API'si
@app.route('/api/register', methods=['POST'])
def register_user():
    """Yeni bir kullanıcı kaydeder."""
    data = request.get_json()
    fullname = data.get('fullname')
    email = data.get('email')
    phone = data.get('phone', '') 
    password = data.get('password')
    role = data.get('role', 'Çal\u0131\u015fan') # Sağlanmazsa varsayılan pozisyon
    profile_picture = data.get('profile_picture') 
    hide_email = data.get('hide_email', 0) 
    hide_phone = data.get('hide_phone', 0) 

    if not all([fullname, email, password, role]):
        return jsonify({'message': 'L\u00FCtfen t\u00FCm gerekli alanlar\u0131 doldurun.'}), 400

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            existing_user = cursor.fetchone()
            if existing_user:
                return jsonify({'message': 'Bu e-posta adresi zaten kullan\u0131mda.'}), 409

            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            sql = """
            INSERT INTO users (fullname, email, phone, password, role, profile_picture, hide_email, hide_phone)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (fullname, email, phone, hashed_password, role, profile_picture, hide_email, hide_phone))
            connection.commit()
        return jsonify({'message': 'Kay\u0131t ba\u015far\u0131l\u0131!'}), 201
    except pymysql.Error as e:
        print(f"Veritaban\u0131 kay\u0131t hatas\u0131: {e}")
        if e.args[0] == 1062:
            return jsonify({'message': 'Bu e-posta adresi zaten kullan\u0131mda.'}), 409
        return jsonify({'message': f'Veritaban\u0131 hatas\u0131 olu\u015ftu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel kay\u0131t hatas\u0131: {e}")
        return jsonify({'message': 'Sunucu hatas\u0131, l\u00FCtfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()


@app.route('/api/login', methods=['POST'])
def login_user():
    """Bir kullanıcıyı doğrular ve oturum oluşturur."""
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not all([email, password]):
        return jsonify({'message': 'L\u00FCtfen e-posta adresinizi ve \u015fifrenizi girin.'}), 400

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Yeni alanlar dahil tüm kullanıcı detaylarını getir
            cursor.execute("SELECT id, fullname, email, phone, password, role, onay, profile_picture, hide_email, hide_phone, created_at FROM users WHERE email = %s", (email,))
            
            user = cursor.fetchone()

            if not user:
                return jsonify({'message': 'Ge\u00E7ersiz e-posta veya \u015fifre.'}), 401

            is_match = bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8'))

            if not is_match:
                return jsonify({'message': 'Ge\u00E7ersiz e-posta veya \u015fifre.'}), 401

            if user['onay'] == 0:
                return jsonify({
                    'message': 'Hesab\u0131n\u0131z hen\u00FCz onaylanmad\u0131. L\u00FCtfen y\u00F6neticinizle ileti\u015fime ge\u00E7in.',
                    'user': {
                        'email': user['email'], 
                        'onay': user['onay']
                    },
                    'redirect': 'waiting.html' 
                }), 403 

            # Kullanıcı ID'sini oturuma kaydet
            session['user_id'] = user['id'] 
            del user['password'] # Güvenlik nedeniyle şifreyi yanıttan kaldır

            return jsonify({
                'message': 'Giri\u015f ba\u015far\u0131l\u0131!',
                'user': user 
            }), 200

    except pymysql.Error as e:
        print(f"Veritaban\u0131 giri\u015f hatas\u0131: {e}")
        return jsonify({'message': f'Veritaban\u0131 hatas\u0131 olu\u015ftu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel giri\u015f hatas\u0131: {e}")
        return jsonify({'message': 'Sunucu hatas\u0131, l\u00FCtfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()

# Yeni Müşteri Ekle API'si
@app.route('/api/customers', methods=['POST'])
def add_customer():
    """Veritabanına yeni bir müşteri ekler."""
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
    user_id = data.get('user_id') # Aktivite kaydı için projeyi ekleyen kullanıcı ID'si

    if not all([customer_name, contact_person, phone, user_id]): 
        return jsonify({'message': '\u015eirket Ad\u0131, \u0130lgili Ki\u015fi, Telefon ve Kullan\u0131c\u0131 ID\'si zorunlu alanlard\u0131r.'}), 400

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT customer_id FROM customers WHERE customer_name = %s", (customer_name,))
            existing_customer = cursor.fetchone()
            if existing_customer:
                return jsonify({'message': 'Bu \u015firket ad\u0131 zaten kay\u0131tl\u0131.'}), 409

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

            log_activity(
                user_id=user_id,
                title='Yeni M\u00FC\u015fteri Eklendi',
                description=f'"{customer_name}" adl\u0131 yeni m\u00FC\u015fteri eklendi.',
                icon='fas fa-user-plus'
            )

        return jsonify({'message': 'M\u00FC\u015fteri ba\u015far\u0131yla eklendi!', 'customerId': new_customer_id}), 201

    except pymysql.Error as e:
        print(f"Veritaban\u0131 hatas\u0131 m\u00FC\u015fteri eklerken: {e}")
        if e.args[0] == 1062: # Duplicate entry error
            return jsonify({'message': 'Bu e-posta veya \u015firket ad\u0131 zaten kay\u0131tl\u0131.'}), 409
        return jsonify({'message': f'Veritaban\u0131 hatas\u0131 olu\u015ftu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel hata m\u00FC\u015fteri eklerken: {e}")
        return jsonify({'message': 'Sunucu hatas\u0131, l\u00FCtfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()

# Tüm Müşterileri Listele API'si
@app.route('/api/customers', methods=['GET'])
def get_customers():
    """Tüm müşterilerin bir listesini getirir."""
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
        print(f"Veritaban\u0131 hatas\u0131 m\u00FC\u015fterileri \u00E7ekerken: {e}")
        return jsonify({'message': f'Veritaban\u0131 hatas\u0131 olu\u015ftu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel hata m\u00FC\u015fterileri \u00E7ekerken: {e}")
        return jsonify({'message': 'Sunucu hatas\u0131, l\u00FCtfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()

# Tek bir müşterinin detaylarını getirme API'si (Modal için eklendi)
@app.route('/api/customers/<int:customer_id>', methods=['GET'])
def get_customer_details(customer_id):
    """Tek bir müşterinin detaylarını getirir."""
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
                return jsonify({'message': 'M\u00FC\u015fteri bulunamad\u0131.'}), 404

        return jsonify(customer), 200
    except pymysql.Error as e:
        print(f"Veritaban\u0131 hatas\u0131 m\u00FC\u015fteri detaylar\u0131n\u0131 \u00E7ekerken: {e}")
        return jsonify({'message': f'Veritaban\u0131 hatas\u0131 olu\u015ftu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel hata m\u00FC\u015fteri detaylar\u0131n\u0131 \u00E7ekerken: {e}")
        return jsonify({'message': 'Sunucu hatas\u0131, l\u00FCtfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()

# Müşteri Güncelleme API'si (PUT)
@app.route('/api/customers/<int:customer_id>', methods=['PUT'])
def update_customer(customer_id):
    """Mevcut bir müşterinin bilgilerini günceller."""
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
    user_id = data.get('user_id') # Aktivite kaydı için güncelleyen kullanıcı ID'si

    if not user_id: 
        return jsonify({'message': 'Kullan\u0131c\u0131 ID\'si eksik.'}), 400
    if not any([customer_name, status, contact_person, contact_title, phone, email, country, city, district, postal_code, address, notes]):
        return jsonify({'message': 'G\u00FCncellenecek veri bulunamad\u0131.'}), 400

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT customer_name FROM customers WHERE customer_id = %s", (customer_id,))
            existing_customer_info = cursor.fetchone()
            if not existing_customer_info:
                return jsonify({'message': 'M\u00FC\u015fteri bulunamad\u0131.'}), 404
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
                return jsonify({'message': 'G\u00FCncelleme i\u00E7in belirtilen alan yok.'}), 400

            sql = f"UPDATE customers SET {', '.join(updates)} WHERE customer_id = %s"
            params.append(customer_id)

            cursor.execute(sql, tuple(params))
            connection.commit()

            if cursor.rowcount == 0:
                return jsonify({'message': 'M\u00FC\u015fteri verisi zaten g\u00FCncel veya de\u011fi\u015fiklik yap\u0131lmad\u0131.'}), 200

            log_activity(
                user_id=user_id,
                title='M\u00FC\u015fteri G\u00FCncellendi',
                description=f'"{old_customer_name}" adl\u0131 m\u00FC\u015fteri bilgileri g\u00FCncellendi.',
                icon='fas fa-user-edit'
            )

        return jsonify({'message': 'M\u00FC\u015fteri ba\u015far\u0131yla g\u00FCncellendi!'}), 200

    except pymysql.Error as e:
        print(f"Veritaban\u0131 hatas\u0131 m\u00FC\u015fteri g\u00FCncellerken: {e}")
        if e.args[0] == 1062:
            return jsonify({'message': 'Bu e-posta veya \u015firket ad\u0131 zaten kay\u0131tl\u0131.'}), 409
        return jsonify({'message': f'Veritaban\u0131 hatas\u0131 olu\u015ftu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel hata m\u00FC\u015fteri g\u00FCncellerken: {e}")
        return jsonify({'message': 'Sunucu hatas\u0131, l\u00FCtfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()

@app.route('/api/customers/<int:customer_id>', methods=['DELETE'])
def delete_customer(customer_id):
    """Veritabanından bir müşteriyi siler."""
    data = request.get_json() # DELETE isteği gövdesinden user_id'yi al
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({'message': 'Kullan\u0131c\u0131 ID\'si eksik.'}), 400

    customer_name = "Bilinmeyen M\u00FC\u015fteri" # Loglama için varsayılan değer
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT customer_name FROM customers WHERE customer_id = %s", (customer_id,))
            customer_info = cursor.fetchone()
            if not customer_info:
                return jsonify({'message': 'M\u00FC\u015fteri bulunamad\u0131.'}), 404
            customer_name = customer_info['customer_name']

            sql = "DELETE FROM customers WHERE customer_id = %s"
            cursor.execute(sql, (customer_id,))
            connection.commit()

            if cursor.rowcount == 0:
                return jsonify({'message': 'M\u00FC\u015fteri silinemedi veya mevcut de\u011fil.'}), 404
            
            log_activity(
                user_id=user_id,
                title='M\u00FC\u015fteri Silindi',
                description=f'"{customer_name}" adl\u0131 m\u00FC\u015fteri silindi.',
                icon='fas fa-user-minus'
            )

        return jsonify({'message': 'M\u00FC\u015fteri ba\u015far\u0131yla silindi!'}), 200

    except pymysql.Error as e:
        print(f"Veritaban\u0131 hatas\u0131 m\u00FC\u015fteri silerken: {e}")
        if e.args[0] == 1451: # Foreign key constraint fails
            return jsonify({'message': 'Bu m\u00FC\u015fteriyle ili\u015fkili projeler var. L\u00FCtfen \u00F6nce ilgili projeleri silin.'}), 409
        return jsonify({'message': f'Veritaban\u0131 hatas\u0131 olu\u015ftu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel hata m\u00FC\u015fteri silerken: {e}")
        return jsonify({'message': 'Sunucu hatas\u0131, l\u00FCtfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()


# Tüm Projeleri Listele API'si
@app.route('/api/projects', methods=['GET'])
def get_projects():
    """
    Müşteri ve yönetici adlarıyla birlikte tüm projelerin bir listesini getirir,
    ayrıca en son ilerleme adımının başlığını ve gecikme durumunu içerir.
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
                p.status,
                c.customer_name, 
                u.fullname AS project_manager_name, 
                c.customer_id, 
                u.id AS project_manager_user_id,
                -- En son iş gidişat başlığını ve gecikme günlerini getir
                (SELECT title FROM project_progress WHERE project_id = p.project_id ORDER BY created_at DESC LIMIT 1) AS last_progress_title,
                (SELECT delay_days FROM project_progress WHERE project_id = p.project_id ORDER BY created_at DESC LIMIT 1) AS last_progress_delay_days,
                (SELECT IFNULL(SUM(pp.delay_days), 0) FROM project_progress pp WHERE pp.project_id = p.project_id) AS total_delay_days
            FROM projects p
            JOIN customers c ON p.customer_id = c.customer_id
            JOIN users u ON p.project_manager_id = u.id
            ORDER BY p.created_at DESC
            """
            cursor.execute(sql)
            projects_data = cursor.fetchall()

            for project in projects_data:
                # Proje durumunu en son iş gidişat başlığına göre ayarla
                # Eğer en son iş gidişatı yoksa, projenin kendi status'unu kullan
                display_status = project['last_progress_title'] if project['last_progress_title'] else project['status']

                # Eğer en son iş adımında gecikme varsa, durumu güncelle
                if project['last_progress_delay_days'] is not None and project['last_progress_delay_days'] > 0:
                    display_status += ' (Gecikmeli)'
                
                project['display_status'] = display_status # Yeni bir alan olarak ekle

                # datetime.date nesnelerini JSON serileştirmesi için ISO formatlı dizelere dönüştür
                project['contract_date'] = project['contract_date'].isoformat() if isinstance(project['contract_date'], datetime.date) else None
                project['meeting_date'] = project['meeting_date'].isoformat() if isinstance(project['meeting_date'], datetime.date) else None
                project['start_date'] = project['start_date'].isoformat() if isinstance(project['start_date'], datetime.date) else None
                project['end_date'] = project['end_date'].isoformat() if isinstance(project['end_date'], datetime.date) else None

        return jsonify(projects_data), 200
    except pymysql.Error as e:
        print(f"Veritaban\u0131 hatas\u0131 projeleri \u00E7ekerken: {e}")
        return jsonify({'message': f'Veritaban\u0131 hatas\u0131 olu\u015ftu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel hata projeleri \u00E7ekerken: {e}")
        return jsonify({'message': 'Sunucu hatas\u0131, l\u00FCtfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()

# Tek bir projenin detaylarını getirme API'si (Modal için)
@app.route('/api/projects/<int:project_id>', methods=['GET'])
def get_project_details(project_id):
    """Tek bir projenin detaylarını getirir."""
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
                return jsonify({'message': 'Proje bulunamad\u0131.'}), 404

            # datetime.date nesnelerini JSON serileştirmesi için ISO formatlı dizelere dönüştür
            project['contract_date'] = project['contract_date'].isoformat() if isinstance(project['contract_date'], datetime.date) else None
            project['meeting_date'] = project['meeting_date'].isoformat() if isinstance(project['meeting_date'], datetime.date) else None
            project['start_date'] = project['start_date'].isoformat() if isinstance(project['start_date'], datetime.date) else None
            project['end_date'] = project['end_date'].isoformat() if isinstance(project['end_date'], datetime.date) else None

        return jsonify(project), 200
    except pymysql.Error as e:
        print(f"Veritaban\u0131 hatas\u0131 proje detaylar\u0131n\u0131 \u00E7ekerken: {e}")
        return jsonify({'message': f'Veritaban\u0131 hatas\u0131 olu\u015ftu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel hata proje detaylar\u0131n\u0131 \u00E7ekerken: {e}")
        return jsonify({'message': 'Sunucu hatas\u0131, l\u00FCtfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()

# Bildirim gönderme yardımcı fonksiyonu
def send_notification(user_id, title, message):
    """Belirli bir kullanıcıya bildirim gönderir."""
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = "INSERT INTO notifications (user_id, title, message, created_at) VALUES (%s, %s, %s, NOW())"
            cursor.execute(sql, (user_id, title, message))
            connection.commit()
            print(f"Bildirim g\u00F6nderildi: Kullan\u0131c\u0131 ID: {user_id}, Ba\u015fl\u0131k: '{title}', Mesaj: '{message}'")
    except pymysql.Error as e:
        print(f"Veritaban\u0131 hatas\u0131 bildirim g\u00F6nderirken: {e}")
    except Exception as e:
        print(f"Genel hata bildirim g\u00F6nderirken: {e}")
    finally:
        if connection:
            connection.close()

# Proje Güncelleme API'si (PUT) - projeler tablosu için
# app.py dosyasında update_project fonksiyonunu bulun ve aşağıdaki gibi güncelleyin:

@app.route('/api/projects/<int:project_id>', methods=['PUT'])
def update_project(project_id):
    data = request.get_json()
    print(f"DEBUG: update_project'e gelen ham JSON veri: {data}")
    print(f"DEBUG: G\u00FCncellenmek istenen Proje ID: {project_id}")

    def clean_input_value(value):
        if value is None or value == '':
            return None
        return str(value)

    project_name = clean_input_value(data.get('project_name'))
    reference_no = clean_input_value(data.get('reference_no'))
    description = clean_input_value(data.get('description'))
    contract_date = clean_input_value(data.get('contract_date'))
    meeting_date = clean_input_value(data.get('meeting_date'))
    start_date = clean_input_value(data.get('start_date'))
    end_date = clean_input_value(data.get('end_date'))
    project_location = clean_input_value(data.get('project_location'))
    status = clean_input_value(data.get('status'))
    
    # customer_id'yi burada alıyoruz
    customer_id_new = data.get('customer_id')
    try:
        customer_id_new = int(customer_id_new) if customer_id_new else None
    except ValueError:
        customer_id_new = None

    project_manager_id_new = data.get('project_manager_id')
    try:
        project_manager_id_new = int(project_manager_id_new) if project_manager_id_new else None
    except ValueError:
        project_manager_id_new = None

    user_id = clean_input_value(data.get('user_id'))

    print(f"DEBUG: \u0130\u015flenmi\u015f de\u011ferler: "
          f"ad='{project_name}', ref='{reference_no}', a\u00E7\u0131klama='{description}', "
          f"s\u00F6zle\u015fme='{contract_date}', toplant\u0131='{meeting_date}', ba\u015flang\u0131\u00E7='{start_date}', biti\u015f='{end_date}', "
          f"konum='{project_location}', durum='{status}', m\u00FC\u015fteri_id='{customer_id_new}', y\u00F6netici_id='{project_manager_id_new}', kullan\u0131c\u0131_id='{user_id}'")

    if not user_id: 
        print("HATA: Kullan\u0131c\u0131 ID'si eksik.")
        return jsonify({'message': 'Kullan\u0131c\u0131 ID\'si eksik.'}), 400

    connection = None
    try:
        connection = get_db_connection()
        print("DEBUG: Veritaban\u0131 ba\u011flant\u0131s\u0131 kuruldu.")
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT project_name, reference_no, description, contract_date, meeting_date,
                       start_date, end_date, project_location, status, customer_id, project_manager_id
                FROM projects WHERE project_id = %s
            """, (project_id,))
            existing_project_info = cursor.fetchone()
            print(f"DEBUG: Mevcut proje bilgileri: {existing_project_info}")

            if not existing_project_info:
                print("HATA: Proje bulunamad\u0131.")
                return jsonify({'message': 'Proje bulunamad\u0131.'}), 404

            old_project_name = existing_project_info['project_name']
            old_reference_no = existing_project_info['reference_no']
            old_description = existing_project_info['description']
            old_contract_date = existing_project_info['contract_date'].isoformat() if isinstance(existing_project_info['contract_date'], datetime.date) else None
            old_meeting_date = existing_project_info['meeting_date'].isoformat() if isinstance(existing_project_info['meeting_date'], datetime.date) else None
            old_start_date = existing_project_info['start_date'].isoformat() if isinstance(existing_project_info['start_date'], datetime.date) else None
            old_end_date = existing_project_info['end_date'].isoformat() if isinstance(existing_project_info['end_date'], datetime.date) else None
            old_project_location = existing_project_info['project_location']
            old_status = existing_project_info['status']
            old_customer_id = existing_project_info['customer_id'] # Eski müşteri ID'si
            old_project_manager_id = existing_project_info['project_manager_id'] 

            print(f"DEBUG: Eski de\u011ferler: "
                  f"ad='{old_project_name}', ref='{old_reference_no}', a\u00E7\u0131klama='{old_description}', "
                  f"s\u00F6zle\u015fme='{old_contract_date}', toplant\u0131='{old_meeting_date}', ba\u015flang\u0131\u00E7='{old_start_date}', biti\u015f='{old_end_date}', "
                  f"konum='{old_project_location}', durum='{old_status}', m\u00FC\u015fteri_id='{old_customer_id}', y\u00F6netici_id='{old_project_manager_id}'")

            updates = []
            params = []

            # Karşılaştırma mantığı
            if clean_input_value(project_name) != clean_input_value(old_project_name):
                updates.append("project_name = %s")
                params.append(project_name)
            if clean_input_value(reference_no) != clean_input_value(old_reference_no):
                updates.append("reference_no = %s")
                params.append(reference_no)
            if clean_input_value(description) != clean_input_value(old_description):
                updates.append("description = %s")
                params.append(description)
            if clean_input_value(contract_date) != clean_input_value(old_contract_date):
                updates.append("contract_date = %s")
                params.append(contract_date)
            if clean_input_value(meeting_date) != clean_input_value(old_meeting_date):
                updates.append("meeting_date = %s")
                params.append(meeting_date)
            if clean_input_value(start_date) != clean_input_value(old_start_date):
                updates.append("start_date = %s")
                params.append(start_date)
            if clean_input_value(end_date) != clean_input_value(old_end_date):
                updates.append("end_date = %s")
                params.append(end_date)
            if clean_input_value(project_location) != clean_input_value(old_project_location):
                updates.append("project_location = %s")
                params.append(project_location)
            if clean_input_value(status) != clean_input_value(old_status):
                updates.append("status = %s")
                params.append(status)
            
            # Müşteri ID'sinin güncellenmesi eklendi
            if customer_id_new != old_customer_id:
                updates.append("customer_id = %s")
                params.append(customer_id_new)

            if project_manager_id_new != old_project_manager_id:
                updates.append("project_manager_id = %s")
                params.append(project_manager_id_new)

            if not updates:
                print("DEBUG: G\u00FCncellenecek bilgi bulunamad\u0131, 200 d\u00F6nd\u00FCr\u00FCl\u00FCyor.")
                return jsonify({'message': 'G\u00FCncellenecek bilgi bulunamad\u0131.'}), 200 

            sql = f"UPDATE projects SET {', '.join(updates)} WHERE project_id = %s"
            params.append(project_id)
            print(f"DEBUG: Olu\u015fturulan SQL: {sql}")
            print(f"DEBUG: SQL parametreleri: {tuple(params)}")

            cursor.execute(sql, tuple(params))
            connection.commit()
            print(f"DEBUG: Veritaban\u0131 g\u00FCncellemesi tamamland\u0131. Etkilenen sat\u0131r say\u0131s\u0131: {cursor.rowcount}")

            if cursor.rowcount == 0:
                print("DEBUG: Proje verisi zaten g\u00FCncel veya de\u011fi\u015fiklik yap\u0131lmad\u0131, 200 d\u00F6nd\u00FCr\u00FCl\u00FCyor.")
                return jsonify({'message': 'Proje verisi zaten g\u00FCncel veya de\u011fi\u015fiklik yap\u0131lmad\u0131.'}), 200

        return jsonify({'message': 'Proje ba\u015far\u0131yla g\u00FCncellendi!'}), 200

    except pymysql.Error as e:
        print(f"VER\u0130TABANI HATASI (update_project): {e}")
        return jsonify({'message': f'Veritaban\u0131 hatas\u0131 olu\u015ftu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"GENEL HATA (update_project): {e}")
        return jsonify({'message': 'Sunucu hatas\u0131, l\u00FCtfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()
            print("DEBUG: Veritaban\u0131 ba\u011flant\u0131s\u0131 kapat\u0131ld\u0131.")

# Proje Silme API'si (DELETE)
@app.route('/api/projects/<int:project_id>', methods=['DELETE'])
def delete_project_api(project_id):
    """Veritabanından bir projeyi siler."""
    data = request.get_json() # DELETE isteği gövdesinden user_id'yi al
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({'message': 'Kullan\u0131c\u0131 ID\'si eksik.'}), 400

    project_name = "Bilinmeyen Proje" # Loglama için varsayılan değer
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT project_name, project_manager_id FROM projects WHERE project_id = %s", (project_id,))
            project_info = cursor.fetchone()

            if not project_info:
                return jsonify({'message': 'Proje silinemedi veya bulunamad\u0131.'}), 404

            project_name = project_info['project_name']
            project_manager_id = project_info['project_manager_id']

            cursor.execute("DELETE FROM project_progress WHERE project_id = %s", (project_id,))

            sql = "DELETE FROM projects WHERE project_id = %s"
            cursor.execute(sql, (project_id,))
            connection.commit()

            if cursor.rowcount == 0:
                return jsonify({'message': 'Proje silinemedi veya bulunamad\u0131.'}), 404

            log_activity(
                user_id=user_id,
                title='Proje Silindi',
                description=f'"{project_name}" adl\u0131 proje silindi.',
                icon='fas fa-trash',
                project_id=project_id # Proje ID'sini log_activity'ye geç
            )

            # Proje yöneticisine bildirim gönder
            send_notification(
                project_manager_id,
                "Proje Silindi",
                f"Y\u00F6netti\u011finiz '{project_name}' projesi silindi."
            )
           
        return jsonify({'message': 'Proje ba\u015far\u0131yla silindi!'}), 200

    except pymysql.Error as e:
        print(f"Veritaban\u0131 hatas\u0131 proje silerken: {e}")
        if e.args[0] == 1451: # Foreign key constraint fails
            return jsonify({'message': 'Bu m\u00FC\u015fteriyle ili\u015fkili projeler var. L\u00FCtfen \u00F6nce ilgili projeleri silin.'}), 409
        return jsonify({'message': f'Veritaban\u0131 hatas\u0131 olu\u015ftu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel hata proje silerken: {e}")
        return jsonify({'message': 'Sunucu hatas\u0131, l\u00FCtfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()


# Proje Yöneticilerini Listele API'si
@app.route('/api/project_managers', methods=['GET'])
def get_project_managers():
    """Proje yöneticisi olarak atanabilecek kullanıcıların bir listesini getirir."""
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, fullname FROM users WHERE role IN ('Teknisyen', 'Tekniker', 'M\u00FChendis', 'M\u00FCd\u00FCr', 'Proje Y\u00F6neticisi') ORDER BY fullname")
            managers = cursor.fetchall()
        return jsonify(managers), 200
    except pymysql.Error as e:
        print(f"Veritaban\u0131 hatas\u0131 y\u00F6neticileri \u00E7ekerken: {e}")
        return jsonify({'message': f'Veritaban\u0131 hatas\u0131 olu\u015ftu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel hata y\u00F6neticileri \u00E7ekerken: {e}")
        return jsonify({'message': 'Sunucu hatas\u0131, l\u00FCtfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()

# Konum verilerini sağlama API uç noktası
@app.route('/api/locations/turkey', methods=['GET'])
def get_turkey_locations():
    """T\u00FCrkiye konum verilerini (iller ve il\u00E7eler) d\u00F6nd\u00FCr\u00FCr."""
    if not TURKEY_LOCATIONS:
        return jsonify({'message': 'Konum verileri y\u00FCklenemedi veya bo\u015f.'}), 500
    return jsonify(TURKEY_LOCATIONS), 200

# Gösterge Paneli İstatistikleri API'si
@app.route('/api/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    """G\u00F6sterge paneli i\u00E7in \u00E7e\u015fitli istatistikleri getirir."""
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(project_id) AS count FROM projects WHERE status IN ('Aktif', 'Aktif (\u0130\u015f Gecikmeli)')")
            active_projects = cursor.fetchone()['count']

            cursor.execute("SELECT COUNT(project_id) AS count FROM projects WHERE status = 'Tamamland\u0131'")
            completed_projects = cursor.fetchone()['count']

            cursor.execute("SELECT COUNT(project_id) AS count FROM projects WHERE status IN ('Gecikti', 'Aktif (\u0130\u015f Gecikmeli)')")
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
        print(f"Veritaban\u0131 hatas\u0131 istatistikleri \u00E7ekerken: {e}")
        return jsonify({'message': f'Veritaban\u0131 hatas\u0131 olu\u015ftu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel hata istatistikleri \u00E7ekerken: {e}")
        return jsonify({'message': 'Sunucu hatas\u0131, l\u00FCtfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()


# Gösterge Paneli Son Aktiviteler API'si (aktiviteler tablosundan getirir)
@app.route('/api/recent_activities', methods=['GET'])
def get_recent_activities():
    """Aktiviteler tablosundan en son aktiviteleri getirir."""
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
            # created_at'ı ISO formatına çevir
            for activity in activities:
                if 'created_at' in activity and isinstance(activity['created_at'], datetime.datetime):
                    activity['created_at'] = activity['created_at'].isoformat()
            return jsonify(activities)
    except pymysql.Error as e:
        print(f"Veritaban\u0131 hatas\u0131 (son aktiviteler): {e}")
        return jsonify({"error": "Veritaban\u0131 hatas\u0131 olu\u015ftu."}), 500
    except Exception as e:
        print(f"Bilinmeyen hata (son aktiviteler): {e}")
        return jsonify({"error": "Bilinmeyen bir sunucu hatas\u0131 olu\u015ftu."}), 500
    finally:
        if connection: 
            connection.close()


# Yeni bir aktiviteyi kaydetmek için yardımcı fonksiyon
def log_activity(user_id, title, description, icon, is_read=0, project_id=None, target_user_id=None):
    """Aktiviteler tablosuna yeni bir aktivite kaydeder.
    Proje adı ve hedef kullanıcı adı gibi ek bilgileri açıklamaya dahil eder.
    """
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            user_fullname = "Bilinmeyen Kullan\u0131c\u0131"
            if user_id:
                cursor.execute("SELECT fullname FROM users WHERE id = %s", (user_id,))
                user = cursor.fetchone()
                if user:
                    user_fullname = user['fullname']

            project_name_str = ""
            if project_id:
                cursor.execute("SELECT project_name FROM projects WHERE project_id = %s", (project_id,))
                project = cursor.fetchone()
                if project:
                    project_name_str = f"'{project['project_name']}' projesi"

            target_user_fullname = ""
            if target_user_id:
                cursor.execute("SELECT fullname FROM users WHERE id = %s", (target_user_id,))
                target_user = cursor.fetchone()
                if target_user:
                    target_user_fullname = f"'{target_user['fullname']}'"

            # Açıklamadan potansiyel (ID: X) ifadesini kaldır
            cleaned_description = re.sub(r' \(ID: \d+\)', '', description)

            # Yeni açıklama formatı
            final_description = f"{user_fullname} taraf\u0131ndan: "

            if project_name_str and target_user_fullname:
                final_description += f"{project_name_str} i\u00E7in {target_user_fullname} ile ilgili {cleaned_description}"
            elif project_name_str:
                final_description += f"{project_name_str} i\u00E7in {cleaned_description}"
            elif target_user_fullname:
                final_description += f"{target_user_fullname} ile ilgili {cleaned_description}"
            else:
                final_description += cleaned_description


            sql = """
            INSERT INTO activities (user_id, title, description, icon, created_at, is_read)
            VALUES (%s, %s, %s, %s, NOW(), %s)
            """
            cursor.execute(sql, (user_id, title, final_description, icon, is_read))
        connection.commit() 
        print(f"Aktivite kaydedildi: Ba\u015fl\u0131k: '{title}', A\u00E7\u0131klama: '{final_description}'")
    except pymysql.Error as e:
        print(f"Aktivite kaydederken hata: {e}")
    except Exception as e:
        print(f"Genel aktivite kaydetme hatas\u0131: {e}")
    finally:
        if connection:
            connection.close()

# Yeni Proje Ekle API'si (önceki sürümden yorum satırı kaldırıldı ve tamamlandı)
@app.route('/api/projects', methods=['POST'])
def add_project():
    """Veritabanına yeni bir proje ekler."""
    data = request.json
    project_name = data.get('projectName') # Ön uçtan 'projectName' olarak gelir
    customer_id = data.get('customerId')
    project_manager_id = data.get('projectManagerId')
    reference_no = data.get('projectRef') # Ön uçtan 'projectRef' olarak gelir
    description = data.get('projectDescription') # Ön uçtan 'projectDescription' olarak gelir
    contract_date = data.get('contractDate')
    meeting_date = data.get('meetingDate')
    start_date_str = data.get('startDate') # datetime nesnesiyle çakışmayı önlemek için yeniden adlandırıldı
    end_date_str = data.get('endDate')     # datetime nesnesiyle çakışmayı önlemek için yeniden adlandırıldı
    project_location = data.get('projectLocation')
    status = data.get('status', 'Planlama A\u015famas\u0131nda') # Sağlanmazsa varsayılan durum

    user_id = data.get('user_id') # Projeyi ekleyen kullanıcı ID'si (aktivite günlüğü için)

    if not all([project_name, customer_id, project_manager_id, start_date_str, end_date_str]): # Tarih kontrolleri eklendi
        return jsonify({'message': 'Proje ad\u0131, m\u00FC\u015fteri, proje y\u00F6neticisi, ba\u015flang\u0131\u00E7 tarihi ve biti\u015f tarihi zorunludur.'}), 400

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
            connection.commit()
            new_project_id = cursor.lastrowid

            # Proje ilerleme adımlarını işle ve ekle
            progress_steps = data.get('progressSteps', [])
            last_step_end_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date() # Proje başlangıç tarihiyle başlat

            for step in progress_steps:
                step_title = step.get('title')
                step_description = step.get('description')
                step_start_date_str = step.get('startDate')
                step_end_date_str = step.get('endDate')

                if not all([step_title, step_start_date_str, step_end_date_str]):
                    print(f"UYARI: Proje {new_project_id} i\u00E7in bir ilerleme ad\u0131m\u0131nda eksik veri var. Ad\u0131m atlan\u0131yor.")
                    continue

                step_start_date = datetime.datetime.strptime(step_start_date_str, '%Y-%m-%d').date()
                step_end_date = datetime.datetime.strptime(step_end_date_str, '%Y-%m-%d').date()

                delay_days = 0
                # Önceki adımın bitiş tarihine veya projenin başlangıç tarihine göre gecikmeyi hesapla
                if last_step_end_date:
                    time_diff = (step_start_date - last_step_end_date).days
                    if time_diff > 1: # 1 günden fazla bir boşluk varsa, gecikme oluşmuştur
                        delay_days = time_diff - 1
                
                sql_insert_progress = """
                INSERT INTO project_progress (project_id, title, description, start_date, end_date, delay_days)
                VALUES (%s, %s, %s, %s, %s, %s)
                """
                cursor.execute(sql_insert_progress, (new_project_id, step_title, step_description, step_start_date_str, step_end_date_str, delay_days))
                connection.commit() # Her adımı commit et veya döngüden sonra bir kez commit et

                last_step_end_date = step_end_date # Bir sonraki iterasyon için last_step_end_date'i güncelle

            # Proje yöneticisine bildirim gönder
            send_notification(
                project_manager_id,
                "Yeni Proje Atand\u0131",
                f"Size yeni bir proje atand\u0131: '{project_name}'."
            )

        log_activity(
            user_id=user_id,
            title='Yeni Proje Eklendi',
            description=f'"{project_name}" adl\u0131 yeni proje olu\u015fturuldu.',
            icon='fas fa-plus',
            project_id=new_project_id # Proje ID'sini log_activity'ye geç
        )
        return jsonify({"message": "Proje ba\u015far\u0131yla eklendi", "projectId": new_project_id}), 201
    except pymysql.Error as e:
        print(f"Veritaban\u0131 hatas\u0131 proje eklerken: {e}")
        return jsonify({'message': f'Veritaban\u0131 hatas\u0131 olu\u015ftu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel hata proje eklerken: {e}")
        return jsonify({'message': 'Sunucu hatas\u0131, l\u00FCtfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()

# PDF Raporu Oluşturma Aktivitesini Kaydetme API'si (ön uçtan çağrılacak)
@app.route('/api/log_pdf_report', methods=['POST'])
def log_pdf_report_api():
    """Bir PDF raporu oluşturma etkinliğini kaydeder."""
    data = request.get_json()
    user_id = data.get('user_id')
    report_type = data.get('report_type', 'Genel Rapor') # Varsayılan değer
    project_name = data.get('project_name') # İsteğe bağlı
    project_id = data.get('project_id') # İsteğe bağlı

    if not user_id:
        return jsonify({'message': 'Kullan\u0131c\u0131 ID\'si eksik.'}), 400

    description_text = f'"{report_type}" raporunun PDF dosyas\u0131 olu\u015fturuldu.'
    if project_name:
        description_text = f'"{project_name}" projesi i\u00E7in PDF raporu olu\u015fturuldu.'

    try:
        log_activity(
            user_id=user_id,
            title='PDF Raporu Olu\u015fturuldu',
            description=description_text,
            icon='fas fa-file-pdf',
            project_id=project_id # Proje ID'sini log_activity'ye geç
        )
        return jsonify({'message': 'PDF rapor aktivitesi ba\u015far\u0131yla kaydedildi.'}), 200
    except Exception as e:
        print(f"PDF rapor aktivitesi kaydederken hata: {e}")
        return jsonify({'message': 'PDF rapor aktivitesi kaydedilirken hata olu\u015ftu.'}), 500


# Proje İlerleme Adımlarını Getir API'si
@app.route('/api/projects/<int:project_id>/progress', methods=['GET'])
def get_project_progress_steps(project_id):
    """Belirli bir proje için tüm ilerleme adımlarını getirir."""
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            sql = """
            SELECT
                progress_id,          
                project_id,
                title AS step_name,   
                description,
                start_date,
                end_date,
                delay_days,
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
                step['created_at'] = step['created_at'].isoformat() if isinstance(step['created_at'], datetime.datetime) else None

        return jsonify(steps), 200
    except pymysql.Error as e:
        print(f"Veritaban\u0131 hatas\u0131 ilerleme ad\u0131mlar\u0131n\u0131 \u00E7ekerken: {e}")
        return jsonify({'message': f'Veritaban\u0131 hatas\u0131 olu\u015ftu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel hata ilerleme ad\u0131mlar\u0131n\u0131 \u00E7ekerken: {e}")
        return jsonify({'message': 'Sunucu hatas\u0131, l\u00FCtfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()

# Yeni Proje İlerleme Adımı Ekle API'si (projects.html'den çağrılır)
@app.route('/api/projects/<int:project_id>/progress', methods=['POST'])
def add_project_progress_step_from_modal(project_id): # project_id artık URL'den geliyor
    """Bir projeye yeni bir ilerleme adımı ekler."""
    data = request.get_json()
    step_name = data.get('step_name')
    description = data.get('description')
    start_date_str = data.get('start_date')
    end_date_str = data.get('end_date')
    user_id = data.get('user_id') # Adımı ekleyen kullanıcı ID'si

    if not all([project_id, step_name, start_date_str, end_date_str, user_id]):
        return jsonify({'message': 'Proje ID\'si, ba\u015fl\u0131k, ba\u015flang\u0131\u00E7 ve biti\u015f tarihi ve kullan\u0131c\u0131 ID\'si zorunludur.'}), 400

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Projenin mevcut bitiş tarihini bul (gecikme günlerini hesaplamak için)
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
                # Önceki adımın bitiş tarihi ile yeni adımın başlangıç tarihi arasındaki farkı hesapla
                time_diff = (new_step_start_date - previous_end_date).days
                if time_diff > 1: # 1 günden fazla bir boşluk varsa, gecikme oluşmuştur
                    delay_days = time_diff - 1

            sql_insert = """
            INSERT INTO project_progress (project_id, title, description, start_date, end_date, delay_days)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql_insert, (project_id, step_name, description, start_date_str, end_date_str, delay_days))
            new_progress_id = cursor.lastrowid
            connection.commit()

            # Proje yöneticisine bildirim gönder
            cursor.execute("SELECT project_manager_id, project_name FROM projects WHERE project_id = %s", (project_id,))
            project_info = cursor.fetchone()
            if project_info:
                project_manager_id = project_info['project_manager_id']
                project_name = project_info['project_name']
                send_notification(
                    project_manager_id,
                    "Proje \u0130lerleme Ad\u0131m\u0131 Eklendi",
                    f"'{step_name}' adl\u0131 yeni bir ilerleme ad\u0131m\u0131 '{project_name}' projesine eklendi."
                )
            
            # Aktivite kaydı
            log_activity(
                user_id=user_id,
                title='\u0130\u015f Ad\u0131m\u0131 Eklendi',
                description=f'"{step_name}" i\u015f ad\u0131m\u0131 eklendi.',
                icon='fas fa-tasks',
                project_id=project_id
            )

        return jsonify({'message': '\u0130lerleme ad\u0131m\u0131 ba\u015far\u0131yla eklendi!', 'progress_id': new_progress_id}), 201
    except pymysql.Error as e:
        print(f"Veritaban\u0131 hatas\u0131 ilerleme ad\u0131m\u0131 eklerken: {e}")
        return jsonify({'message': f'Veritaban\u0131 hatas\u0131 olu\u015ftu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel hata ilerleme ad\u0131m\u0131 eklerken: {e}")
        return jsonify({'message': 'Sunucu hatas\u0131, l\u00FCtfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()

# Proje İlerleme Adımını Güncelle API'si
@app.route('/api/progress/<int:progress_id>', methods=['PUT'])
def update_project_progress_step(progress_id):
    """Mevcut bir proje ilerleme adımını günceller."""
    data = request.get_json()
    step_name = data.get('step_name')
    description = data.get('description')
    start_date_str = data.get('start_date')
    end_date_str = data.get('end_date')
    user_id = data.get('user_id') # Adımı güncelleyen kullanıcı ID'si

    if not all([step_name, start_date_str, end_date_str, user_id]):
        return jsonify({'message': 'Ba\u015fl\u0131k, ba\u015flang\u0131\u00E7 ve biti\u015f tarihi ve kullan\u0131c\u0131 ID\'si zorunludur.'}), 400

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Mevcut ilerleme adımının proje ID'sini ve başlığını al
            cursor.execute("SELECT project_id, title FROM project_progress WHERE progress_id = %s", (progress_id,))
            existing_step = cursor.fetchone()
            if not existing_step:
                return jsonify({'message': '\u0130lerleme ad\u0131m\u0131 bulunamad\u0131.'}), 404

            current_project_id = existing_step['project_id']
            old_step_name = existing_step['title'] # Eski adım adını al

            # Önceki adımın bitiş tarihini bul (bu adım hariç)
            delay_days = 0
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
                return jsonify({'message': '\u0130lerleme ad\u0131m\u0131 verisi zaten g\u00FCncel veya de\u011fi\u015fiklik yap\u0131lmad\u0131.'}), 200

            # Proje yöneticisine bildirim gönder
            cursor.execute("SELECT project_manager_id, project_name FROM projects WHERE project_id = %s", (current_project_id,))
            project_info = cursor.fetchone()
            if project_info:
                project_manager_id = project_info['project_manager_id']
                project_name = project_info['project_name']
                send_notification(
                    project_manager_id,
                    "Proje \u0130lerleme Ad\u0131m\u0131 G\u00FCncellendi",
                    f"'{project_name}' projesindeki '{step_name}' ilerleme ad\u0131m\u0131 g\u00FCncellendi."
                )
            
            # Aktivite kaydı
            log_activity(
                user_id=user_id,
                title='\u0130\u015f Ad\u0131m\u0131 G\u00FCncellendi',
                description=f'"{step_name}" i\u015f ad\u0131m\u0131 g\u00FCncellendi.',
                icon='fas fa-edit',
                project_id=current_project_id
            )

        return jsonify({'message': '\u0130lerleme ad\u0131m\u0131 ba\u015far\u0131yla g\u00FCncellendi!'}), 200
    except pymysql.Error as e:
        print(f"Veritaban\u0131 hatas\u0131 ilerleme ad\u0131m\u0131 g\u00FCncellerken: {e}")
        return jsonify({'message': f'Veritaban\u0131 hatas\u0131 olu\u015ftu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel hata ilerleme ad\u0131m\u0131 g\u00FCncellerken: {e}")
        return jsonify({'message': 'Sunucu hatas\u0131, l\u00FCtfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()

# Proje İlerleme Adımını Sil API'si
@app.route('/api/progress/<int:progress_id>', methods=['DELETE'])
def delete_project_progress_step(progress_id):
    """Bir proje ilerleme adımını siler."""
    data = request.get_json()
    user_id = data.get('user_id') # Adımı silen kullanıcı ID'si

    if not user_id:
        return jsonify({'message': 'Kullan\u0131c\u0131 ID\'si eksik.'}), 400

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Silinecek adımın proje ID'sini ve başlığını al
            cursor.execute("SELECT project_id, title FROM project_progress WHERE progress_id = %s", (progress_id,))
            step_info = cursor.fetchone()
            if not step_info:
                return jsonify({'message': '\u0130lerleme ad\u0131m\u0131 silinemedi veya bulunamad\u0131.'}), 404
            
            current_project_id = step_info['project_id']
            step_name = step_info['title']

            sql = "DELETE FROM project_progress WHERE progress_id = %s"
            cursor.execute(sql, (progress_id,))
            connection.commit()

            if cursor.rowcount == 0:
                return jsonify({'message': '\u0130lerleme ad\u0131m\u0131 silinemedi veya bulunamad\u0131.'}), 404

            # Proje yöneticisine bildirim gönder
            cursor.execute("SELECT project_manager_id, project_name FROM projects WHERE project_id = %s", (current_project_id,))
            project_info = cursor.fetchone()
            if project_info:
                project_manager_id = project_info['project_manager_id']
                project_name = project_info['project_name']
                send_notification(
                    project_manager_id,
                    "Proje \u0130lerleme Ad\u0131m\u0131 Silindi",
                    f"'{project_name}' projesindeki '{step_name}' ilerleme ad\u0131m\u0131 silindi."
                )
            
            # Aktivite kaydı
            log_activity(
                user_id=user_id,
                title='\u0130\u015f Ad\u0131m\u0131 Silindi',
                description=f'"{step_name}" i\u015f ad\u0131m\u0131 silindi.',
                icon='fas fa-trash-alt',
                project_id=current_project_id
            )

        return jsonify({'message': '\u0130lerleme ad\u0131m\u0131 ba\u015far\u0131yla silindi!'}), 200
    except pymysql.Error as e:
        print(f"Veritaban\u0131 hatas\u0131 ilerleme ad\u0131m\u0131 silerken: {e}")
        return jsonify({'message': f'Veritaban\u0131 hatas\u0131 olu\u015ftu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel hata ilerleme ad\u0131m\u0131 silerken: {e}")
        return jsonify({'message': 'Sunucu hatas\u0131, l\u00FCtfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()

@app.route('/api/user-info', methods=['GET'])
def get_user_info():
    """Tek bir kullanıcı için detaylı bilgileri getirir."""
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'message': 'Kullan\u0131c\u0131 ID\'si eksik'}), 400

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Yeni alanlar dahil tüm kullanıcı alanlarını getir
            cursor.execute("SELECT id, fullname, email, phone, role, profile_picture, hide_email, hide_phone, created_at FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            if not user:
                return jsonify({'message': 'Kullan\u0131c\u0131 bulunamad\u0131'}), 404
            
            # datetime nesnelerini JSON serileştirmesi için dizeye dönüştür
            if 'created_at' in user and isinstance(user['created_at'], datetime.datetime):
                user['created_at'] = user['created_at'].isoformat()

            return jsonify(user), 200
    except Exception as e:
        print(f"Genel hata kullan\u0131c\u0131 bilgisi \u00E7ekerken: {e}")
        return jsonify({'message': 'Sunucu hatas\u0131, l\u00FCtfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()

@app.route('/api/users', methods=['GET'])
def get_all_users():
    """Tüm kullanıcıların bir listesini getirir."""
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Yeni alanlar dahil tüm kullanıcı alanlarını getir
            cursor.execute("SELECT id, fullname, email, phone, role, profile_picture, hide_email, hide_phone, created_at FROM users")
            users = cursor.fetchall()
            
            # datetime nesnelerini JSON serileştirmesi için dizeye dönüştür
            for user in users:
                if 'created_at' in user and isinstance(user['created_at'], datetime.datetime):
                    user['created_at'] = user['created_at'].isoformat()

            return jsonify(users), 200
    except pymysql.Error as e:
        print(f"Veritaban\u0131 hatas\u0131 t\u00FCm kullan\u0131c\u0131lar\u0131 \u00E7ekerken: {e}")
        return jsonify({'message': f'Veritaban\u0131 hatas\u0131 olu\u015ftu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel hata t\u00FCm kullan\u0131c\u0131lar\u0131 \u00E7ekerken: {e}")
        return jsonify({'message': 'Sunucu hatas\u0131, l\u00FCtfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()

@app.route('/api/users', methods=['POST'])
def add_user():
    """Veritabanına yeni bir kullanıcı ekler (genellikle bir yönetici tarafından)."""
    data = request.get_json()
    fullname = data.get('fullname')
    email = data.get('email')
    phone = data.get('phone', '')
    password = data.get('password')
    role = data.get('role', 'Çal\u0131\u015fan') # Sağlanmazsa varsayılan pozisyon
    profile_picture = data.get('profile_picture') 
    hide_email = data.get('hide_email', 0) 
    hide_phone = data.get('hide_phone', 0) 


    if not fullname or not email or not password or not role:
        return jsonify({'message': 'T\u00FCm alanlar zorunludur!'}), 400

    onay = 1 # Yönetici tarafından eklenen kullanıcılar için varsayılan olarak onaylandı
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
        return jsonify({'message': 'Kullan\u0131c\u0131 ba\u015far\u0131yla eklendi!'}), 201
    except pymysql.Error as e:
        print(f"Veritaban\u0131 kullan\u0131c\u0131 ekleme hatas\u0131: {e}")
        if e.args[0] == 1062:
            return jsonify({'message': 'Bu e-posta adresi zaten kullan\u0131mda.'}), 409
        return jsonify({'message': f'Veritaban\u0131 hatas\u0131 olu\u015ftu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel kullan\u0131c\u0131 ekleme hatas\u0131: {e}")
        return jsonify({'message': 'Sunucu hatas\u0131, l\u00FCtfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()

@app.route('/ayarlar')
def ayarlar_page():
    """Ayarlar sayfasını render eder."""
    return render_template('ayarlar.html')

@app.route('/api/roles', methods=['GET'])
def get_distinct_roles():
    """Kullanıcılar tablosundan farklı rolleri getirir ('Admin' hariç)."""
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            sql = "SELECT DISTINCT role FROM users WHERE role != 'Admin'"
            cursor.execute(sql)
            roles = [row['role'] for row in cursor.fetchall()]

        return jsonify(roles), 200
    except pymysql.Error as e:
        print(f"Veritaban\u0131 hatas\u0131 rolleri \u00E7ekerken: {e}")
        return jsonify({'message': f'Veritaban\u0131 hatas\u0131 olu\u015ftu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel hata rolleri \u00E7ekerken: {e}")
        return jsonify({'message': 'Sunucu hatas\u0131, l\u00FCtfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()


@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    """Görevleri, isteğe bağlı olarak atanmış kullanıcıya göre filtrelenmiş olarak getirir."""
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
        print(f"G\u00F6revler \u00E7ekilirken hata: {e}")
        return jsonify({'message': 'G\u00F6revler \u00E7ekilemedi.'}), 500
    finally:
        if connection:
            connection.close()

@app.route('/api/tasks', methods=['POST'])
def add_task():
    """Veritabanına yeni bir görev ekler."""
    data = request.get_json()
    title = data.get('title')
    description = data.get('description')
    start = data.get('start')
    end = data.get('end')
    priority = data.get('priority', 'medium')
    assigned_user_id = int(data.get('assigned_user_id')) if data.get('assigned_user_id') else None
    created_by = int(data.get('created_by')) if data.get('created_by') else None

    if not all([title, start, assigned_user_id, created_by]):
        return jsonify({'message': 'Gerekli alanlar eksik!'}), 400

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

            # Yeni atanan kullanıcıya bildirim gönder
            send_notification(
                assigned_user_id,
                "Yeni G\u00F6rev Atand\u0131",
                f"Size yeni bir g\u00F6rev atand\u0131: '{title}'."
            )
            
            # Aktivite kaydı
            log_activity(
                user_id=created_by, # G\u00F6revi olu\u015fturan ki\u015fi
                title='G\u00F6rev Eklendi',
                description=f'"{title}" adl\u0131 g\u00F6rev eklendi.',
                icon='fas fa-clipboard-list',
                target_user_id=assigned_user_id # G\u00F6revin atand\u0131\u011f\u0131 ki\u015fi
            )


        return jsonify({'message': 'G\u00F6rev ba\u015far\u0131yla eklendi!'}), 201
    except Exception as e:
        print(f"G\u00F6rev eklerken hata: {e}")
        return jsonify({'message': 'G\u00F6rev eklenirken hata olu\u015ftu.'}), 500
    finally:
        if connection:
            connection.close()

@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    """Mevcut bir g\u00F6revi g\u00FCnceller."""
    data = request.get_json()
    title = data.get('title')
    description = data.get('description')
    start = data.get('start')
    end = data.get('end')
    priority = data.get('priority', 'medium')
    new_assigned_user_id = int(data.get('assigned_user_id')) if data.get('assigned_user_id') else None
    updated_by_user_id = int(data.get('updated_by_user_id')) if data.get('updated_by_user_id') else None # G\u00FCncelleme yapan kullan\u0131c\u0131 ID'si

    if not all([title, start, new_assigned_user_id, updated_by_user_id]): # updated_by_user_id kontrol\u00FC eklendi
        return jsonify({'message': 'Gerekli alanlar eksik!'}), 400

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # G\u00F6revin mevcut atanan kullan\u0131c\u0131s\u0131n\u0131 al
            cursor.execute("SELECT assigned_user_id FROM tasks WHERE id = %s", (task_id,))
            existing_task = cursor.fetchone()
            old_assigned_user_id = existing_task['assigned_user_id'] if existing_task else None

            sql = """
                UPDATE tasks
                SET title=%s, description=%s, start=%s, end=%s, priority=%s, assigned_user_id=%s
                WHERE id=%s
            """
            cursor.execute(sql, (title, description, start, end, priority, new_assigned_user_id, task_id))
            connection.commit()

            # Atanan kullan\u0131c\u0131 de\u011fi\u015ftiyse, eski ve yeni kullan\u0131c\u0131lara bildirim g\u00F6nder
            if old_assigned_user_id and old_assigned_user_id != new_assigned_user_id:
                send_notification(
                    old_assigned_user_id,
                    "G\u00F6rev Atamas\u0131 De\u011fi\u015fti",
                    f"'{title}' g\u00F6revi art\u0131k size atanmam\u0131\u015ft\u0131r."
                )
            send_notification(
                new_assigned_user_id,
                "G\u00F6rev G\u00FCncellendi",
                f"Size atanan '{title}' g\u00F6revi g\u00FCncellendi."
            )
            
            # Aktivite kaydı
            log_activity(
                user_id=updated_by_user_id, # G\u00FCncelleme yapan ki\u015fi
                title='G\u00F6rev G\u00FCncellendi',
                description=f'"{title}" adl\u0131 g\u00F6rev g\u00FCncellendi.',
                icon='fas fa-edit',
                target_user_id=new_assigned_user_id # G\u00F6revin atand\u0131\u011f\u0131 ki\u015fi
            )

        return jsonify({'message': 'G\u00F6rev ba\u015far\u0131yla g\u00FCncellendi!'}), 200
    except Exception as e:
        print(f"G\u00F6rev g\u00FCncellerken hata: {e}")
        return jsonify({'message': 'G\u00F6rev g\u00FCncellenirken hata olu\u015ftu.'}), 500
    finally:
        if connection:
            connection.close()

@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    """Veritabanından bir görevi siler."""
    data = request.get_json()
    user_id = data.get('user_id') # G\u00F6revi silen kullan\u0131c\u0131 ID'si

    if not user_id:
        return jsonify({'message': 'Kullan\u0131c\u0131 ID\'si eksik.'}), 400

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Bildirim g\u00F6ndermek i\u00E7in g\u00F6rev bilgilerini al
            cursor.execute("SELECT title, assigned_user_id FROM tasks WHERE id = %s", (task_id,))
            task_info = cursor.fetchone()
            
            cursor.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
            connection.commit()

            if task_info:
                send_notification(
                    task_info['assigned_user_id'],
                    "G\u00F6rev Silindi",
                    f"Size atanan '{task_info['title']}' g\u00F6revi silindi."
                )
            
            # Aktivite kaydı
            log_activity(
                user_id=user_id, # G\u00F6revi silen ki\u015fi
                title='G\u00F6rev Silindi',
                description=f'"{task_info["title"]}" adl\u0131 g\u00F6rev silindi.',
                icon='fas fa-trash',
                target_user_id=task_info['assigned_user_id'] # Silinen g\u00F6revin atand\u0131\u011f\u0131 ki\u015fi
            )

        return jsonify({'message': 'G\u00F6rev ba\u015far\u0131yla silindi!'}), 200
    except Exception as e:
        print(f"G\u00F6rev silerken hata: {e}")
        return jsonify({'message': 'G\u00F6rev silinirken hata olu\u015ftu.'}), 500
    finally:
        if connection:
            connection.close()

@app.route('/api/manager-stats')
def manager_stats():
    """Proje y\u00F6neticilerinin performans\u0131yla ilgili istatistikleri getirir."""
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
                (SELECT IFNULL(SUM(pr.delay_days), 0)
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
    """\u00C7al\u0131\u015fanlar (proje y\u00F6neticileri) i\u00E7in performans metriklerini getirir."""
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
            WHERE u.role IN ('Tekniker', 'Teknisyen', 'M\u00FChendis', 'M\u00FCd\u00FCr', 'Proje Y\u00F6neticisi')
            GROUP BY p.project_manager_id, u.fullname
            """
            cursor.execute(sql)
            result = cursor.fetchall()
            return jsonify(result)
    finally:    
        if connection:
            connection.close()

##if __name__ == '__main__':
  ##  app.run(host='0.0.0.0', port=3001, debug=True)
