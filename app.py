# Mark all notifications as read API (for notifications table)
@app.route('/api/notifications/mark_all_read', methods=['PUT'])
def mark_all_notifications_as_read():
    """Marks all notifications as read in the database."""
    data = request.get_json() # Use get_json() for PUT requests
    user_id = data.get('user_id') # Get user_id from the request body
    if not user_id:
        return jsonify({'message': 'Kullanıcı ID\'si eksik.'}), 400

    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = "UPDATE notifications SET is_read = 1 WHERE user_id = %s AND is_read = 0" 
            cursor.execute(sql, (user_id,))
            connection.commit()
            rows_affected = cursor.rowcount 
        return jsonify({'message': f'{rows_affected} bildirim okundu olarak işaretlendi.'}), 200 # Updated message
    except pymysql.Error as e:
        print(f"Veritabanı hatası tüm bildirimleri güncellerken: {e}") # Updated print
        return jsonify({'message': f'Veritabanı hatası oluştu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel hata tüm bildirimleri güncellerken: {e}") # Updated print
        return jsonify({'message': 'Sunucu hatası, lütfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()

# Unread Notification Count API (for notifications table)
@app.route('/api/notifications/unread-count', methods=['GET'])
def get_unread_notifications_count():
    """Returns the count of unread notifications in the database."""
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'unread_count': 0, 'message': 'Kullanıcı ID\'si eksik.'}), 400 # Updated message

    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = "SELECT COUNT(id) as unread_count FROM notifications WHERE user_id = %s AND is_read = 0"
            cursor.execute(sql, (user_id,))
            result = cursor.fetchone()
            return jsonify(result), 200
    except pymysql.Error as e:
        print(f"Veritabanı hatası okunmamış bildirim sayısını çekerken: {e}") # Updated print
        return jsonify({'message': f'Veritabanı hatası oluştu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel hata okunmamış bildirim sayısını çekerken: {e}") # Updated print
        return jsonify({'message': 'Sunucu hatası, lütfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()


# Mark Notification as Read API (for notifications table)
@app.route('/api/notifications/<int:notification_id>/read', methods=['PUT'])
def mark_notification_as_read(notification_id):
    """Marks a specific notification as read in the database."""
    data = request.get_json()
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({'message': 'Kullanıcı ID\'si eksik.'}), 400 # Updated message

    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM notifications WHERE id = %s AND user_id = %s", (notification_id, user_id))
            if not cursor.fetchone():
                return jsonify({'message': 'Bildirim bulunamadı veya değiştirme izniniz yok.'}), 404 # Updated message

            sql = "UPDATE notifications SET is_read = 1 WHERE id = %s"
            cursor.execute(sql, (notification_id,))
            connection.commit()

        return jsonify({'message': 'Bildirim başarıyla okundu olarak işaretlendi.'}), 200 # Updated message
    except pymysql.Error as e:
        print(f"Veritabanı hatası bildirimi güncellerken: {e}") # Updated print
        return jsonify({'message': f'Veritabanı hatası oluştu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel hata bildirimi güncellerken: {e}") # Updated print
        return jsonify({'message': 'Sunucu hatası, lütfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()

# Fetch Notifications API (for notifications table)
@app.route('/api/notifications', methods=['GET'])
def get_notifications():
    """Fetches notifications for a specific user."""
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'message': 'Kullanıcı ID\'si eksik.'}), 400 # Updated message

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # Fetch notifications only for the relevant user
            sql = "SELECT id, user_id, title, message, is_read, created_at FROM notifications WHERE user_id = %s ORDER BY created_at DESC"
            cursor.execute(sql, (user_id,))
            result = cursor.fetchall()
            for row in result:
                if 'is_read' in row:
                    try:
                        row['is_read'] = int(row['is_read'])
                    except Exception:
                        row['is_read'] = 0
            return jsonify(result)
    except pymysql.Error as e:
        print(f"Veritabanı hatası bildirimleri çekerken: {e}") # Updated print
        return jsonify({'message': f'Veritabanı hatası oluştu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel hata bildirimleri çekerken: {e}") # Updated print
        return jsonify({'message': 'Sunucu hatası, lütfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()

@app.route('/api/notifications/<int:notification_id>', methods=['DELETE'])
def delete_notification(notification_id):
    """Deletes a specific notification for the logged-in user."""
    data = request.get_json()
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({'message': 'Kullanıcı ID\'si eksik.'}), 400 # Updated message

    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM notifications WHERE id = %s AND user_id = %s", (notification_id, user_id))
            if not cursor.fetchone():
                return jsonify({'message': 'Bildirim bulunamadı veya silme izniniz yok.'}), 404 # Updated message

            cursor.execute("DELETE FROM notifications WHERE id = %s", (notification_id,))
            connection.commit()
            return jsonify({'message': 'Bildirim silindi.'}), 200 # Updated message
    except Exception as e:
        print(f"Bildirim silme hatası: {e}") # Updated print
        return jsonify({'message': 'Sunucu hatası'}), 500 # Updated message
    finally:
        connection.close()

@app.route('/api/notifications/all', methods=['DELETE'])
def delete_all_notifications():
    """Deletes all notifications for the logged-in user."""
    data = request.get_json()
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({'message': 'Kullanıcı ID\'si eksik.'}), 400 # Updated message

    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM notifications WHERE user_id = %s", (user_id,))
            connection.commit()
            return jsonify({'message': 'Tüm bildirimleriniz silindi.'}) # Updated message
    except Exception as e:
        if connection:
            connection.rollback()
        return jsonify({'message': f'Hata: {str(e)}'}), 500 # Updated message
    finally:
        connection.close()


# Add New Notification API (for notifications table)
@app.route('/api/notifications', methods=['POST'])
def add_notification():
    """Adds a new notification to the database."""
    data = request.get_json()
    user_id = data.get('user_id')
    title = data.get('title')
    message = data.get('message') 

    if not all([user_id, title, message]):
        return jsonify({'message': 'Kullanıcı ID\'si, başlık ve mesaj zorunludur.'}), 400 # Updated message

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
        return jsonify({'message': 'Bildirim başarıyla kaydedildi!'}), 201 # Updated message
    except pymysql.Error as e:
        print(f"Veritabanı hatası bildirim kaydederken: {e}") # Updated print
        if e.args[0] == 1062:
            return jsonify({'message': 'Bu e-posta adresi zaten kullanımda.'}), 409 # Updated message
        return jsonify({'message': f'Veritabanı hatası oluştu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel hata bildirim kaydederken: {e}") # Updated print
        return jsonify({'message': 'Sunucu hatası, lütfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()

# Add New Activity API (for activities table)
@app.route('/api/activities', methods=['POST'])
def add_activity():
    """Adds a new activity to the database."""
    data = request.get_json()
    user_id = data.get('user_id')
    title = data.get('title')
    description = data.get('description')
    icon = data.get('icon', 'fas fa-info-circle') 

    if not all([user_id, title, description]):
        return jsonify({'message': 'Kullanıcı ID\'si, başlık ve açıklama zorunludur.'}), 400 # Updated message

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
        return jsonify({'message': 'Aktivite başarıyla kaydedildi!'}), 201 # Updated message
    except pymysql.Error as e:
        print(f"Veritabanı hatası aktivite kaydederken: {e}") # Updated print
        return jsonify({'message': f'Veritabanı hatası oluştu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel hata aktivite kaydederken: {e}") # Updated print
        return jsonify({'message': 'Sunucu hatası, lütfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()

@app.route('/api/update_user_profile', methods=['POST'])
def update_user_profile():
    """Updates a user's profile information, including profile picture and visibility settings.
    Personal details (fullname, email, phone, role) are no longer updated via this endpoint,
    as the frontend modal for these fields has been removed."""
    data = request.get_json()
    user_id = data.get('userId')
    profile_picture = data.get('profile_picture') 
    hide_email = data.get('hide_email') 
    hide_phone = data.get('hide_phone') 

    if not user_id:
        return jsonify({'message': 'Kullanıcı ID\'si eksik.'}), 400 # Updated message

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT profile_picture, hide_email, hide_phone FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()

            if not user:
                return jsonify({'message': 'Kullanıcı bulunamadı.'}), 404 # Updated message

            updates = []
            params = []
            message_parts = []

            # Handle profile_picture: if it's explicitly null from frontend, set DB to NULL
            # If profile_picture is 'null' string, set to SQL NULL. Otherwise, update with the new value.
            if profile_picture is not None: 
                if profile_picture == "null": 
                    updates.append("profile_picture = NULL")
                    message_parts.append("Profil Resmi Kaldırıldı") # Updated message
                elif profile_picture != user['profile_picture']: # Only update if different from current DB value
                    updates.append("profile_picture = %s")
                    params.append(profile_picture)
                    message_parts.append("Profil Resmi") # Updated message
            
            if hide_email is not None and hide_email != user['hide_email']:
                updates.append("hide_email = %s")
                params.append(hide_email)
                message_parts.append("E-posta Görünürlüğü") # Updated message

            if hide_phone is not None and hide_phone != user['hide_phone']:
                updates.append("hide_phone = %s")
                params.append(hide_phone)
                message_parts.append("Telefon Görünürlüğü") # Updated message

            if not updates:
                return jsonify({'message': 'Güncellenecek bilgi bulunamadı.'}), 200 # Updated message

            sql = f"UPDATE users SET {', '.join(updates)} WHERE id = %s"
            params.append(user_id)

            cursor.execute(sql, tuple(params))
            connection.commit()

            final_message = "Başarıyla güncellendi: " + ", ".join(message_parts) + "." # Updated message
            if not message_parts: 
                 final_message = "Güncellenecek değişiklik bulunamadı." # Updated message

            return jsonify({'message': final_message}), 200

    except pymysql.Error as e:
        print(f"Veritabanı hatası profil güncellerken: {e}") # Updated print
        return jsonify({'message': f'Veritabanı hatası oluştu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel hata profil güncellerken: {e}") # Updated print
        return jsonify({'message': 'Sunucu hatası, lütfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()

@app.route('/api/pending-users', methods=['GET'])
def get_pending_users():
    """Fetches users with 'onay' (approval) status as 0."""
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor(pymysql.cursors.DictCursor) as cursor: 
            sql = "SELECT id, fullname, email, phone, role, created_at FROM users WHERE onay = 0"
            cursor.execute(sql)
            pending_users = cursor.fetchall()
            return jsonify(pending_users), 200
    except pymysql.Error as e:
        print(f"Veritabanı hatası bekleyen kullanıcıları çekerken: {e}") # Updated print
        return jsonify({'message': f'Veritabanı hatası oluştu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel hata bekleyen kullanıcıları çekerken: {e}") # Updated print
        return jsonify({'message': 'Sunucu hatası, lütfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()

@app.route('/api/users/approve/<int:user_id>', methods=['PATCH'])
def approve_user(user_id):
    """Approves a user by setting their 'onay' status to 1."""
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, onay FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()
    
            if not user:
                return jsonify({'message': 'Kullanıcı bulunamadı.'}), 404 # Updated message
            if user['onay'] == 1:
                return jsonify({'message': 'Kullanıcı zaten onaylanmış.'}), 400 # Updated message

            sql = "UPDATE users SET onay = 1 WHERE id = %s"
            cursor.execute(sql, (user_id,))
            connection.commit()

        return jsonify({'message': 'Kullanıcı başarıyla onaylandı!'}), 200 # Updated message

    except pymysql.Error as e:
        print(f"Veritabanı hatası kullanıcıyı onaylarken: {e}") # Updated print
        return jsonify({'message': f'Veritabanı hatası oluştu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel hata kullanıcıyı onaylarken: {e}") # Updated print
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
                return jsonify({'message': 'Kullanıcı bulunamadı.'}), 404 # Updated message

            if user_info['id'] == 1: 
                 return jsonify({'message': 'Bu kullanıcı silinemez.'}), 403 # Updated message

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
                print(f"DEBUG: {cursor.rowcount} proje kullanıcı {user_id}'den {default_manager_id}'e yeniden atandı.") # Updated print
            else:
                cursor.execute("DELETE FROM projects WHERE project_manager_id = %s", (user_id,))
                print(f"DEBUG: Kullanıcı {user_id} için {cursor.rowcount} proje silindi (yeniden atanacak yönetici yok).") # Updated print

            cursor.execute("DELETE FROM tasks WHERE assigned_user_id = %s", (user_id,))
            print(f"DEBUG: Kullanıcı {user_id} için {cursor.rowcount} görev silindi.") # Updated print

            sql = "DELETE FROM users WHERE id = %s"
            cursor.execute(sql, (user_id,))
            connection.commit()
            print(f"DEBUG: Kullanıcı {user_id} silindi.") # Updated print

        return jsonify({'message': 'Kullanıcı başarıyla silindi!'}), 200 # Updated message

    except pymysql.Error as e:
        print(f"Veritabanı hatası kullanıcı silerken: {e}") # Updated print
        return jsonify({'message': f'Veritabanı hatası oluştu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel hata kullanıcı silerken: {e}") # Updated print
        return jsonify({'message': 'Sunucu hatası, lütfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()

@app.route('/api/role-permissions', methods=['GET'])
def get_permissions_by_role():
    """Fetches permissions for a given role."""
    role_name = request.args.get('role')
    if not role_name:
        return jsonify({'message': 'Rol adı gerekli'}), 400 # Updated message

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            sql = "SELECT proje_ekle, proje_duzenle, proje_sil, pdf_olusturma, musteri_duzenleme, raporlar FROM yetki WHERE LOWER(role_name) = %s"
            cursor.execute(sql, (role_name.lower(),))
            result = cursor.fetchone()
            if not result:
                # If no permission record exists for the role, return all permissions as 0 by default
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
        return jsonify({'message': 'Rol belirtilmedi.'}), 400 # Updated message

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
        return jsonify({'message': 'Yetkiler başarıyla güncellendi.'}) # Updated message
    except Exception as e:
        if connection:
            connection.rollback()
        return jsonify({'message': f'Hata: {str(e)}'}), 500
    finally:
        if connection:
            connection.close()

# User Registration API
@app.route('/api/register', methods=['POST'])
def register_user():
    """Registers a new user."""
    data = request.get_json()
    fullname = data.get('fullname')
    email = data.get('email')
    phone = data.get('phone', '') 
    password = data.get('password')
    role = data.get('role', 'Çalışan') # Default position if not provided
    profile_picture = data.get('profile_picture') 
    hide_email = data.get('hide_email', 0) 
    hide_phone = data.get('hide_phone', 0) 

    if not all([fullname, email, password, role]):
        return jsonify({'message': 'Lütfen tüm gerekli alanları doldurun.'}), 400 # Updated message

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            existing_user = cursor.fetchone()
            if existing_user:
                return jsonify({'message': 'Bu e-posta adresi zaten kullanımda.'}), 409 # Updated message

            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            sql = """
            INSERT INTO users (fullname, email, phone, password, role, profile_picture, hide_email, hide_phone)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (fullname, email, phone, hashed_password, role, profile_picture, hide_email, hide_phone))
            connection.commit()
        return jsonify({'message': 'Kayıt başarılı!'}), 201 # Updated message
    except pymysql.Error as e:
        print(f"Veritabanı kayıt hatası: {e}") # Updated print
        if e.args[0] == 1062:
            return jsonify({'message': 'Bu e-posta adresi zaten kullanımda.'}), 409 # Updated message
        return jsonify({'message': f'Veritabanı hatası oluştu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel kayıt hatası: {e}") # Updated print
        return jsonify({'message': 'Sunucu hatası, lütfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()


@app.route('/api/login', methods=['POST'])
def login_user():
    """Authenticates a user and creates a session."""
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not all([email, password]):
        return jsonify({'message': 'Lütfen e-posta adresinizi ve şifrenizi girin.'}), 400 # Updated message

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Fetch all user details including new fields
            cursor.execute("SELECT id, fullname, email, phone, password, role, onay, profile_picture, hide_email, hide_phone, created_at FROM users WHERE email = %s", (email,))
            
            user = cursor.fetchone()

            if not user:
                return jsonify({'message': 'Geçersiz e-posta veya şifre.'}), 401 # Updated message

            is_match = bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8'))

            if not is_match:
                return jsonify({'message': 'Geçersiz e-posta veya şifre.'}), 401 # Updated message

            if user['onay'] == 0:
                return jsonify({
                    'message': 'Hesabınız henüz onaylanmadı. Lütfen yöneticinizle iletişime geçin.', # Updated message
                    'user': {
                        'email': user['email'], 
                        'onay': user['onay']
                    },
                    'redirect': 'waiting.html' 
                }), 403 

            # Save user ID to session
            session['user_id'] = user['id'] 
            del user['password'] 

            return jsonify({
                'message': 'Giriş başarılı!', # Updated message
                'user': user 
            }), 200

    except pymysql.Error as e:
        print(f"Veritabanı giriş hatası: {e}") # Updated print
        return jsonify({'message': f'Veritabanı hatası oluştu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel giriş hatası: {e}") # Updated print
        return jsonify({'message': 'Sunucu hatası, lütfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()

# Add New Customer API
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
    user_id = data.get('user_id') 

    if not all([customer_name, contact_person, phone, user_id]): 
        return jsonify({'message': 'Şirket Adı, İlgili Kişi, Telefon ve Kullanıcı ID\'si zorunlu alanlardır.'}), 400 # Updated message

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT customer_id FROM customers WHERE customer_name = %s", (customer_name,))
            existing_customer = cursor.fetchone()
            if existing_customer:
                return jsonify({'message': 'Bu şirket adı zaten kayıtlı.'}), 409 # Updated message

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
                title='Yeni Müşteri Eklendi', # Updated message
                description=f'"{customer_name}" adlı yeni müşteri eklendi.', # Updated message
                icon='fas fa-user-plus'
            )

        return jsonify({'message': 'Müşteri başarıyla eklendi!', 'customerId': new_customer_id}), 201 # Updated message

    except pymysql.Error as e:
        print(f"Veritabanı hatası müşteri eklerken: {e}") # Updated print
        if e.args[0] == 1062:
            return jsonify({'message': 'Bu e-posta veya şirket adı zaten kayıtlı.'}), 409 # Updated message
        return jsonify({'message': f'Veritabanı hatası oluştu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel hata müşteri eklerken: {e}") # Updated print
        return jsonify({'message': 'Sunucu hatası, lütfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()

# List All Customers API
@app.route('/api/customers', methods=['GET'])
def get_customers():
    """Fetches a list of all customers."""
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
        print(f"Veritabanı hatası müşterileri çekerken: {e}") # Updated print
        return jsonify({'message': f'Veritabanı hatası oluştu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel hata müşterileri çekerken: {e}") # Updated print
        return jsonify({'message': 'Sunucu hatası, lütfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()

# API to fetch details of a single customer (added for Modal)
@app.route('/api/customers/<int:customer_id>', methods=['GET'])
def get_customer_details(customer_id):
    """Fetches details of a single customer."""
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
                return jsonify({'message': 'Müşteri bulunamadı.'}), 404 # Updated message

        return jsonify(customer), 200
    except pymysql.Error as e:
        print(f"Veritabanı hatası müşteri detaylarını çekerken: {e}") # Updated print
        return jsonify({'message': f'Veritabanı hatası oluştu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel hata müşteri detaylarını çekerken: {e}") # Updated print
        return jsonify({'message': 'Sunucu hatası, lütfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()

# Update Customer API (PUT)
@app.route('/api/customers/<int:customer_id>', methods=['PUT'])
def update_customer(customer_id):
    """Updates an existing customer's information."""
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
    user_id = data.get('user_id') 

    if not user_id: 
        return jsonify({'message': 'Kullanıcı ID\'si eksik.'}), 400 # Updated message
    if not any([customer_name, status, contact_person, contact_title, phone, email, country, city, district, postal_code, address, notes]):
        return jsonify({'message': 'Güncellenecek veri bulunamadı.'}), 400 # Updated message

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT customer_name FROM customers WHERE customer_id = %s", (customer_id,))
            existing_customer_info = cursor.fetchone()
            if not existing_customer_info:
                return jsonify({'message': 'Müşteri bulunamadı.'}), 404 # Updated message
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
                return jsonify({'message': 'Güncelleme için belirtilen alan yok.'}), 400 # Updated message

            sql = f"UPDATE customers SET {', '.join(updates)} WHERE customer_id = %s"
            params.append(customer_id)

            cursor.execute(sql, tuple(params))
            connection.commit()

            if cursor.rowcount == 0:
                return jsonify({'message': 'Müşteri verisi zaten güncel veya değişiklik yapılmadı.'}), 200 # Updated message

            log_activity(
                user_id=user_id,
                title='Müşteri Güncellendi', # Updated message
                description=f'"{old_customer_name}" adlı müşteri bilgileri güncellendi.', # Updated message
                icon='fas fa-user-edit'
            )

        return jsonify({'message': 'Müşteri başarıyla güncellendi!'}), 200 # Updated message

    except pymysql.Error as e:
        print(f"Veritabanı hatası müşteri güncellerken: {e}") # Updated print
        if e.args[0] == 1062:
            return jsonify({'message': 'Bu e-posta veya şirket adı zaten kayıtlı.'}), 409 # Updated message
        return jsonify({'message': f'Veritabanı hatası oluştu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel hata müşteri güncellerken: {e}") # Updated print
        return jsonify({'message': 'Sunucu hatası, lütfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()

@app.route('/api/customers/<int:customer_id>', methods=['DELETE'])
def delete_customer(customer_id):
    """Deletes a customer from the database."""
    data = request.get_json()
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({'message': 'Kullanıcı ID\'si eksik.'}), 400 # Updated message

    customer_name = "Bilinmeyen Müşteri" # Updated message
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT customer_name FROM customers WHERE customer_id = %s", (customer_id,))
            customer_info = cursor.fetchone()
            if not customer_info:
                return jsonify({'message': 'Müşteri bulunamadı.'}), 404 # Updated message
            customer_name = customer_info['customer_name']

            sql = "DELETE FROM customers WHERE customer_id = %s"
            cursor.execute(sql, (customer_id,))
            connection.commit()

            if cursor.rowcount == 0:
                return jsonify({'message': 'Müşteri silinemedi veya mevcut değil.'}), 404 # Updated message
            
            log_activity(
                user_id=user_id,
                title='Müşteri Silindi', # Updated message
                description=f'"{customer_name}" adlı müşteri silindi.', # Updated message
                icon='fas fa-user-minus'
            )

        return jsonify({'message': 'Müşteri başarıyla silindi!'}), 200 # Updated message

    except pymysql.Error as e:
        print(f"Veritabanı hatası müşteri silerken: {e}") # Updated print
        if e.args[0] == 1451: 
            return jsonify({'message': 'Bu müşteriyle ilişkili projeler var. Lütfen önce ilgili projeleri silin.'}), 409 # Updated message
        return jsonify({'message': f'Veritabanı hatası oluştu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel hata müşteri silerken: {e}") # Updated print
        return jsonify({'message': 'Sunucu hatası, lütfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()


# List All Projects API
@app.route('/api/projects', methods=['GET'])
def get_projects():
    """
    Fetches a list of all projects with their associated customer and manager names,
    and includes the latest progress step title and its delay status.
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

                # Convert datetime.date objects to ISO format strings for JSON serialization
                project['contract_date'] = project['contract_date'].isoformat() if isinstance(project['contract_date'], datetime.date) else None
                project['meeting_date'] = project['meeting_date'].isoformat() if isinstance(project['meeting_date'], datetime.date) else None
                project['start_date'] = project['start_date'].isoformat() if isinstance(project['start_date'], datetime.date) else None
                project['end_date'] = project['end_date'].isoformat() if isinstance(project['end_date'], datetime.date) else None

        return jsonify(projects_data), 200
    except pymysql.Error as e:
        print(f"Veritabanı hatası projeleri çekerken: {e}") # Updated print
        return jsonify({'message': f'Veritabanı hatası oluştu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel hata projeleri çekerken: {e}") # Updated print
        return jsonify({'message': 'Sunucu hatası, lütfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()

# API to fetch details of a single project (for Modal)
@app.route('/api/projects/<int:project_id>', methods=['GET'])
def get_project_details(project_id):
    """Fetches details of a single project."""
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
                return jsonify({'message': 'Proje bulunamadı.'}), 404 # Updated message

            # Convert datetime.date objects to ISO format strings for JSON serialization
            project['contract_date'] = project['contract_date'].isoformat() if isinstance(project['contract_date'], datetime.date) else None
            project['meeting_date'] = project['meeting_date'].isoformat() if isinstance(project['meeting_date'], datetime.date) else None
            project['start_date'] = project['start_date'].isoformat() if isinstance(project['start_date'], datetime.date) else None
            project['end_date'] = project['end_date'].isoformat() if isinstance(project['end_date'], datetime.date) else None

        return jsonify(project), 200
    except pymysql.Error as e:
        print(f"Veritabanı hatası proje detaylarını çekerken: {e}") # Updated print
        return jsonify({'message': f'Veritabanı hatası oluştu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel hata proje detaylarını çekerken: {e}") # Updated print
        return jsonify({'message': 'Sunucu hatası, lütfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()

# Helper function to send notifications
def send_notification(user_id, title, message):
    """Sends a notification to a specific user."""
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = "INSERT INTO notifications (user_id, title, message, created_at) VALUES (%s, %s, %s, NOW())"
            cursor.execute(sql, (user_id, title, message))
            connection.commit()
            print(f"Bildirim gönderildi: Kullanıcı ID: {user_id}, Başlık: '{title}', Mesaj: '{message}'") # Updated print
    except pymysql.Error as e:
        print(f"Veritabanı hatası bildirim gönderirken: {e}") # Updated print
    except Exception as e:
        print(f"Genel hata bildirim gönderirken: {e}") # Updated print
    finally:
        if connection:
            connection.close()

# Update Project API (PUT) - for projects table
@app.route('/api/projects/<int:project_id>', methods=['PUT'])
def update_project(project_id):
    data = request.get_json()
    print(f"DEBUG: update_project'e gelen ham JSON veri: {data}")
    print(f"DEBUG: Güncellenmek istenen Project ID: {project_id}")

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

    project_manager_id_new = data.get('project_manager_id')
    try:
        project_manager_id_new = int(project_manager_id_new) if project_manager_id_new else None
    except ValueError:
        project_manager_id_new = None

    user_id = clean_input_value(data.get('user_id'))

    print(f"DEBUG: İşlenmiş değerler: "
          f"ad='{project_name}', ref='{reference_no}', açıklama='{description}', " # Updated print
          f"sözleşme='{contract_date}', toplantı='{meeting_date}', başlangıç='{start_date}', bitiş='{end_date}', " # Updated print
          f"konum='{project_location}', durum='{status}', yönetici_id='{project_manager_id_new}', kullanıcı_id='{user_id}'") # Updated print

    if not user_id: 
        print("HATA: Kullanıcı ID'si eksik.") # Updated print
        return jsonify({'message': 'Kullanıcı ID\'si eksik.'}), 400

    connection = None
    try:
        connection = get_db_connection()
        print("DEBUG: Veritabanı bağlantısı kuruldu.") # Updated print
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT project_name, reference_no, description, contract_date, meeting_date,
                       start_date, end_date, project_location, status, project_manager_id
                FROM projects WHERE project_id = %s
            """, (project_id,))
            existing_project_info = cursor.fetchone()
            print(f"DEBUG: Mevcut proje bilgileri: {existing_project_info}") # Updated print

            if not existing_project_info:
                print("HATA: Proje bulunamadı.") # Updated print
                return jsonify({'message': 'Proje bulunamadı.'}), 404

            old_project_name = existing_project_info['project_name']
            old_reference_no = existing_project_info['reference_no']
            old_description = existing_project_info['description']
            old_contract_date = existing_project_info['contract_date'].isoformat() if isinstance(existing_project_info['contract_date'], datetime.date) else None
            old_meeting_date = existing_project_info['meeting_date'].isoformat() if isinstance(existing_project_info['meeting_date'], datetime.date) else None
            old_start_date = existing_project_info['start_date'].isoformat() if isinstance(existing_project_info['start_date'], datetime.date) else None
            old_end_date = existing_project_info['end_date'].isoformat() if isinstance(existing_project_info['end_date'], datetime.date) else None
            old_project_location = existing_project_info['project_location']
            old_status = existing_project_info['status']
            old_project_manager_id = existing_project_info['project_manager_id'] 

            print(f"DEBUG: Eski değerler: "
                  f"ad='{old_project_name}', ref='{old_reference_no}', açıklama='{old_description}', " # Updated print
                  f"sözleşme='{old_contract_date}', toplantı='{old_meeting_date}', başlangıç='{old_start_date}', bitiş='{old_end_date}', " # Updated print
                  f"konum='{old_project_location}', durum='{old_status}', yönetici_id='{old_project_manager_id}'") # Updated print

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

            if project_manager_id_new != old_project_manager_id:
                updates.append("project_manager_id = %s")
                params.append(project_manager_id_new)

            if not updates:
                print("DEBUG: Güncellenecek bilgi bulunamadı, 200 döndürülüyor.") # Updated print
                return jsonify({'message': 'Güncellenecek bilgi bulunamadı.'}), 200 

            sql = f"UPDATE projects SET {', '.join(updates)} WHERE project_id = %s"
            params.append(project_id)
            print(f"DEBUG: Oluşturulan SQL: {sql}") # Updated print
            print(f"DEBUG: SQL parametreleri: {tuple(params)}") # Updated print

            cursor.execute(sql, tuple(params))
            connection.commit()
            print(f"DEBUG: Veritabanı güncellemesi tamamlandı. Etkilenen satır sayısı: {cursor.rowcount}") # Updated print

            if cursor.rowcount == 0:
                print("DEBUG: Proje verisi zaten güncel veya değişiklik yapılmadı, 200 döndürülüyor.") # Updated print
                return jsonify({'message': 'Proje verisi zaten güncel veya değişiklik yapılmadı.'}), 200

        return jsonify({'message': 'Proje başarıyla güncellendi!'}), 200 # Updated message

    except pymysql.Error as e:
        print(f"VERİTABANI HATASI (update_project): {e}") # Updated print
        return jsonify({'message': f'Veritabanı hatası oluştu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"GENEL HATA (update_project): {e}") # Updated print
        return jsonify({'message': 'Sunucu hatası, lütfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()
            print("DEBUG: Veritabanı bağlantısı kapatıldı.") # Updated print

# Delete Project API (DELETE)
@app.route('/api/projects/<int:project_id>', methods=['DELETE'])
def delete_project_api(project_id):
    """Deletes a project from the database."""
    data = request.get_json()
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({'message': 'Kullanıcı ID\'si eksik.'}), 400 # Updated message

    project_name = "Bilinmeyen Proje" # Updated message
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT project_name, project_manager_id FROM projects WHERE project_id = %s", (project_id,))
            project_info = cursor.fetchone()

            if not project_info:
                return jsonify({'message': 'Proje silinemedi veya bulunamadı.'}), 404 # Updated message

            project_name = project_info['project_name']
            project_manager_id = project_info['project_manager_id']

            cursor.execute("DELETE FROM project_progress WHERE project_id = %s", (project_id,))

            sql = "DELETE FROM projects WHERE project_id = %s"
            cursor.execute(sql, (project_id,))
            connection.commit()

            if cursor.rowcount == 0:
                return jsonify({'message': 'Proje silinemedi veya bulunamadı.'}), 404 # Updated message

            log_activity(
                user_id=user_id,
                title='Proje Silindi', # Updated message
                description=f'"{project_name}" adlı proje silindi.', # Updated message
                icon='fas fa-trash'
            )

            # Send notification to project manager
            send_notification(
                project_manager_id,
                "Proje Silindi", # Updated message
                f"Yönettiğiniz '{project_name}' projesi silindi." # Updated message
            )
           
        return jsonify({'message': 'Proje başarıyla silindi!'}), 200 # Updated message

    except pymysql.Error as e:
        print(f"Veritabanı hatası proje silerken: {e}") # Updated print
        if e.args[0] == 1451: 
            return jsonify({'message': 'Bu müşteriyle ilişkili projeler var. Lütfen önce ilgili projeleri silin.'}), 409 # Updated message
        return jsonify({'message': f'Veritabanı hatası oluştu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel hata proje silerken: {e}") # Updated print
        return jsonify({'message': 'Sunucu hatası, lütfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()


# List Project Managers API
@app.route('/api/project_managers', methods=['GET'])
def get_project_managers():
    """Fetches a list of users who can be assigned as project managers."""
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, fullname FROM users WHERE role IN ('Teknisyen', 'Tekniker', 'Mühendis', 'Müdür', 'Proje Yöneticisi') ORDER BY fullname")
            managers = cursor.fetchall()
        return jsonify(managers), 200
    except pymysql.Error as e:
        print(f"Veritabanı hatası yöneticileri çekerken: {e}") # Updated print
        return jsonify({'message': f'Veritabanı hatası oluştu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel hata yöneticileri çekerken: {e}") # Updated print
        return jsonify({'message': 'Sunucu hatası, lütfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()

# API endpoint to provide location data
@app.route('/api/locations/turkey', methods=['GET'])
def get_turkey_locations():
    """Returns Turkey's location data (provinces and districts)."""
    if not TURKEY_LOCATIONS:
        return jsonify({'message': 'Konum verileri yüklenemedi veya boş.'}), 500 # Updated message
    return jsonify(TURKEY_LOCATIONS), 200

# Dashboard Statistics API
@app.route('/api/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    """Fetches various statistics for the dashboard."""
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
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
        print(f"Veritabanı hatası istatistikleri çekerken: {e}") # Updated print
        return jsonify({'message': f'Veritabanı hatası oluştu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel hata istatistikleri çekerken: {e}") # Updated print
        return jsonify({'message': 'Sunucu hatası, lütfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()


# Dashboard Recent Activity API (fetches from activities table)
@app.route('/api/recent_activities', methods=['GET'])
def get_recent_activities():
    """Fetches the most recent activities from the activities table."""
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
            return jsonify(activities)
    except pymysql.Error as e:
        print(f"Veritabanı hatası (son aktiviteler): {e}") # Updated print
        return jsonify({"error": "Veritabanı hatası oluştu."}), 500 # Updated message
    except Exception as e:
        print(f"Bilinmeyen hata (son aktiviteler): {e}") # Updated print
        return jsonify({"error": "Bilinmeyen bir sunucu hatası oluştu."}), 500 # Updated message
    finally:
        if connection: 
            connection.close()


# Helper function to log a new activity
def log_activity(user_id, title, description, icon, is_read=0):
    """Logs a new activity in the activities table."""
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            user_fullname = "Bilinmeyen Kullanıcı" # Updated message
            if user_id:
                cursor.execute("SELECT fullname FROM users WHERE id = %s", (user_id,))
                user = cursor.fetchone()
                if user:
                    user_fullname = user['fullname']

            # Remove potential (ID: X) from description if present
            cleaned_description = re.sub(r' \(ID: \d+\)', '', description)

            full_description = f"{user_fullname} tarafından: {cleaned_description}"

            sql = """
            INSERT INTO activities (user_id, title, description, icon, created_at, is_read)
            VALUES (%s, %s, %s, %s, NOW(), %s)
            """
            cursor.execute(sql, (user_id, title, full_description, icon, is_read))
        connection.commit() 
        print(f"Aktivite kaydedildi: Başlık: '{title}', Açıklama: '{full_description}'") # Updated print
    except pymysql.Error as e:
        print(f"Aktivite kaydederken hata: {e}") # Updated print
    except Exception as e:
        print(f"Genel aktivite kaydetme hatası: {e}") # Updated print
    finally:
        if connection:
            connection.close()

# Add New Project API (uncommented and completed from previous version)
@app.route('/api/projects', methods=['POST'])
def add_project():
    """Adds a new project to the database."""
    data = request.json
    project_name = data.get('projectName') # Comes as 'projectName' from frontend
    customer_id = data.get('customerId')
    project_manager_id = data.get('projectManagerId')
    reference_no = data.get('projectRef') # Comes as 'projectRef' from frontend
    description = data.get('projectDescription') # Comes as 'projectDescription' from frontend
    contract_date = data.get('contractDate')
    meeting_date = data.get('meetingDate')
    start_date_str = data.get('startDate') # Renamed to avoid conflict with datetime object
    end_date_str = data.get('endDate')     # Renamed to avoid conflict with datetime object
    project_location = data.get('projectLocation')
    status = data.get('status', 'Planlama Aşamasında') 

    user_id = data.get('user_id') # User ID adding the project (for activity log)

    if not all([project_name, customer_id, project_manager_id, start_date_str, end_date_str]): # Added date checks
        return jsonify({'message': 'Proje adı, müşteri, proje yöneticisi, başlangıç tarihi ve bitiş tarihi zorunludur.'}), 400 # Updated message

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

            # Process and insert project progress steps
            progress_steps = data.get('progressSteps', [])
            last_step_end_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date() # Initialize with project start date

            for step in progress_steps:
                step_title = step.get('title')
                step_description = step.get('description')
                step_start_date_str = step.get('startDate')
                step_end_date_str = step.get('endDate')

                if not all([step_title, step_start_date_str, step_end_date_str]):
                    print(f"UYARI: Proje {new_project_id} için bir ilerleme adımında eksik veri var. Adım atlanıyor.") # Updated print
                    continue

                step_start_date = datetime.datetime.strptime(step_start_date_str, '%Y-%m-%d').date()
                step_end_date = datetime.datetime.strptime(step_end_date_str, '%Y-%m-%d').date()

                delay_days = 0
                # Calculate delay based on the previous step's end date or project's start date
                if last_step_end_date:
                    time_diff = (step_start_date - last_step_end_date).days
                    if time_diff > 1:
                        delay_days = time_diff - 1
                
                sql_insert_progress = """
                INSERT INTO project_progress (project_id, title, description, start_date, end_date, delay_days)
                VALUES (%s, %s, %s, %s, %s, %s)
                """
                cursor.execute(sql_insert_progress, (new_project_id, step_title, step_description, step_start_date_str, step_end_date_str, delay_days))
                connection.commit() # Commit each step or commit once after loop

                last_step_end_date = step_end_date # Update last_step_end_date for the next iteration

            # Send notification to project manager
            send_notification(
                project_manager_id,
                "Yeni Proje Atandı", # Updated message
                f"Size yeni bir proje atandı: '{project_name}'." # Updated message
            )

        log_activity(
            user_id=user_id,
            title='Yeni Proje Eklendi', # Updated message
            description=f'"{project_name}" adlı yeni proje oluşturuldu.', # Updated message
            icon='fas fa-plus'
        )
        return jsonify({"message": "Proje başarıyla eklendi", "projectId": new_project_id}), 201 # Updated message
    except pymysql.Error as e:
        print(f"Veritabanı hatası proje eklerken: {e}") # Updated print
        return jsonify({'message': f'Veritabanı hatası oluştu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel hata proje eklerken: {e}") # Updated print
        return jsonify({'message': 'Sunucu hatası, lütfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()

# API to log PDF Report Creation Activity (to be called from frontend)
@app.route('/api/log_pdf_report', methods=['POST'])
def log_pdf_report_api():
    """Logs the creation of a PDF report as an activity."""
    data = request.get_json()
    user_id = data.get('user_id')
    report_type = data.get('report_type', 'Genel Rapor') # Updated message
    project_name = data.get('project_name') 

    if not user_id:
        return jsonify({'message': 'Kullanıcı ID\'si eksik.'}), 400 # Updated message

    description_text = f'"{report_type}" raporunun PDF dosyası oluşturuldu.' # Updated message
    if project_name:
        description_text = f'"{project_name}" projesi için PDF raporu oluşturuldu.' # Updated message

    try:
        log_activity(
            user_id=user_id,
            title='PDF Raporu Oluşturuldu', # Updated message
            description=description_text,
            icon='fas fa-file-pdf'
        )
        return jsonify({'message': 'PDF rapor aktivitesi başarıyla kaydedildi.'}), 200 # Updated message
    except Exception as e:
        print(f"PDF rapor aktivitesi kaydederken hata: {e}") # Updated print
        return jsonify({'message': 'PDF rapor aktivitesi kaydedilirken hata oluştu.'}), 500 # Updated message


# API to fetch Project Progress Steps
@app.route('/api/projects/<int:project_id>/progress', methods=['GET'])
def get_project_progress_steps(project_id):
    """Fetches all progress steps for a given project."""
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
        print(f"Veritabanı hatası ilerleme adımlarını çekerken: {e}") # Updated print
        return jsonify({'message': f'Veritabanı hatası oluştu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel hata ilerleme adımlarını çekerken: {e}") # Updated print
        return jsonify({'message': 'Sunucu hatası, lütfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()

# Add New Project Progress Step API (called from projects.html)
@app.route('/api/projects/<int:project_id>/progress', methods=['POST'])
def add_project_progress_step_from_modal(project_id): # project_id now passed from URL
    """Adds a new progress step to a project."""
    data = request.get_json()
    step_name = data.get('step_name')
    description = data.get('description')
    start_date_str = data.get('start_date')
    end_date_str = data.get('end_date')

    if not all([project_id, step_name, start_date_str, end_date_str]):
        return jsonify({'message': 'Proje ID\'si, başlık, başlangıç ve bitiş tarihi zorunludur.'}), 400 # Updated message

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Find the existing end date of the project (for calculating delay_days)
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
                # Calculate the difference between the end date of the previous step and the start date of the new step
                time_diff = (new_step_start_date - previous_end_date).days
                if time_diff > 1: # If there's a gap of more than 1 day, a delay has occurred
                    delay_days = time_diff - 1

            sql_insert = """
            INSERT INTO project_progress (project_id, title, description, start_date, end_date, delay_days)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql_insert, (project_id, step_name, description, start_date_str, end_date_str, delay_days))
            new_progress_id = cursor.lastrowid
            connection.commit()

            # Send notification to project manager
            cursor.execute("SELECT project_manager_id, project_name FROM projects WHERE project_id = %s", (project_id,))
            project_info = cursor.fetchone()
            if project_info:
                project_manager_id = project_info['project_manager_id']
                project_name = project_info['project_name']
                send_notification(
                    project_manager_id,
                    "Proje İlerleme Adımı Eklendi", # Updated message
                    f"'{step_name}' adlı yeni bir ilerleme adımı '{project_name}' projesine eklendi." # Updated message
                )

        return jsonify({'message': 'İlerleme adımı başarıyla eklendi!', 'progress_id': new_progress_id}), 201 # Updated message
    except pymysql.Error as e:
        print(f"Veritabanı hatası ilerleme adımı eklerken: {e}") # Updated print
        return jsonify({'message': f'Veritabanı hatası oluştu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel hata ilerleme adımı eklerken: {e}") # Updated print
        return jsonify({'message': 'Sunucu hatası, lütfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()

# Update Project Progress Step API
@app.route('/api/progress/<int:progress_id>', methods=['PUT'])
def update_project_progress_step(progress_id):
    """Updates an existing project progress step."""
    data = request.get_json()
    step_name = data.get('step_name')
    description = data.get('description')
    start_date_str = data.get('start_date')
    end_date_str = data.get('end_date')

    if not all([step_name, start_date_str, end_date_str]):
        return jsonify({'message': 'Başlık, başlangıç ve bitiş tarihi zorunludur.'}), 400 # Updated message

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Get project ID and title of the existing progress step
            cursor.execute("SELECT project_id, title FROM project_progress WHERE progress_id = %s", (progress_id,))
            existing_step = cursor.fetchone()
            if not existing_step:
                return jsonify({'message': 'İlerleme adımı bulunamadı.'}), 404 # Updated message

            current_project_id = existing_step['project_id']
            old_step_name = existing_step['title'] # Get old step name

            # Find the end date of the previous step (excluding this step)
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
                return jsonify({'message': 'İlerleme adımı verisi zaten güncel veya değişiklik yapılmadı.'}), 200 # Updated message

            # Send notification to project manager
            cursor.execute("SELECT project_manager_id, project_name FROM projects WHERE project_id = %s", (current_project_id,))
            project_info = cursor.fetchone()
            if project_info:
                project_manager_id = project_info['project_manager_id']
                project_name = project_info['project_name']
                send_notification(
                    project_manager_id,
                    "Proje İlerleme Adımı Güncellendi", # Updated message
                    f"'{project_name}' projesindeki '{step_name}' ilerleme adımı güncellendi." # Updated message
                )

        return jsonify({'message': 'İlerleme adımı başarıyla güncellendi!'}), 200 # Updated message
    except pymysql.Error as e:
        print(f"Veritabanı hatası ilerleme adımı güncellerken: {e}") # Updated print
        return jsonify({'message': f'Veritabanı hatası oluştu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel hata ilerleme adımı güncellerken: {e}") # Updated print
        return jsonify({'message': 'Sunucu hatası, lütfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()

# Delete Project Progress Step API
@app.route('/api/progress/<int:progress_id>', methods=['DELETE'])
def delete_project_progress_step(progress_id):
    """Deletes a project progress step."""
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Get project ID of the step to be deleted
            cursor.execute("SELECT project_id, title FROM project_progress WHERE progress_id = %s", (progress_id,))
            step_info = cursor.fetchone()
            if not step_info:
                return jsonify({'message': 'İlerleme adımı silinemedi veya bulunamadı.'}), 404 # Updated message
            
            current_project_id = step_info['project_id']
            step_name = step_info['title']

            sql = "DELETE FROM project_progress WHERE progress_id = %s"
            cursor.execute(sql, (progress_id,))
            connection.commit()

            if cursor.rowcount == 0:
                return jsonify({'message': 'İlerleme adımı silinemedi veya bulunamadı.'}), 404 # Updated message

            # Send notification to project manager
            cursor.execute("SELECT project_manager_id, project_name FROM projects WHERE project_id = %s", (current_project_id,))
            project_info = cursor.fetchone()
            if project_info:
                project_manager_id = project_info['project_manager_id']
                project_name = project_info['project_name']
                send_notification(
                    project_manager_id,
                    "Proje İlerleme Adımı Silindi", # Updated message
                    f"'{project_name}' projesindeki '{step_name}' ilerleme adımı silindi." # Updated message
                )

        return jsonify({'message': 'İlerleme adımı başarıyla silindi!'}), 200 # Updated message
    except pymysql.Error as e:
        print(f"Veritabanı hatası ilerleme adımı silerken: {e}") # Updated print
        return jsonify({'message': f'Veritabanı hatası oluştu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel hata ilerleme adımı silerken: {e}") # Updated print
        return jsonify({'message': 'Sunucu hatası, lütfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()

@app.route('/api/user-info', methods=['GET'])
def get_user_info():
    """Fetches detailed information for a single user."""
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'message': 'Kullanıcı ID\'si eksik'}), 400 # Updated message

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, fullname, email, phone, role, profile_picture, hide_email, hide_phone, created_at FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            if not user:
                return jsonify({'message': 'Kullanıcı bulunamadı'}), 404 # Updated message
            
            # Convert datetime objects to string for JSON serialization
            if 'created_at' in user and isinstance(user['created_at'], datetime.datetime):
                user['created_at'] = user['created_at'].isoformat()

            return jsonify(user), 200
    except Exception as e:
        print(f"Genel hata kullanıcı bilgisi çekerken: {e}") # Updated print
        return jsonify({'message': 'Sunucu hatası, lütfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()

@app.route('/api/users', methods=['GET'])
def get_all_users():
    """Fetches a list of all users."""
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, fullname, email, phone, role, profile_picture, hide_email, hide_phone, created_at FROM users")
            users = cursor.fetchall()
            
            # Convert datetime objects to string for JSON serialization
            for user in users:
                if 'created_at' in user and isinstance(user['created_at'], datetime.datetime):
                    user['created_at'] = user['created_at'].isoformat()

            return jsonify(users), 200
    except pymysql.Error as e:
        print(f"Veritabanı hatası tüm kullanıcıları çekerken: {e}") # Updated print
        return jsonify({'message': f'Veritabanı hatası oluştu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel hata tüm kullanıcıları çekerken: {e}") # Updated print
        return jsonify({'message': 'Sunucu hatası, lütfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()

@app.route('/api/users', methods=['POST'])
def add_user():
    """Adds a new user to the database (typically by an admin)."""
    data = request.get_json()
    fullname = data.get('fullname')
    email = data.get('email')
    phone = data.get('phone', '')
    password = data.get('password')
    role = data.get('role', 'Çalışan') # Default position if not provided
    profile_picture = data.get('profile_picture') 
    hide_email = data.get('hide_email', 0) 
    hide_phone = data.get('hide_phone', 0) 


    if not fullname or not email or not password or not role:
        return jsonify({'message': 'Tüm alanlar zorunludur!'}), 400 # Updated message

    onay = 1 # Default to approved for admin added users
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
        return jsonify({'message': 'Kullanıcı başarıyla eklendi!'}), 201 # Updated message
    except pymysql.Error as e:
        print(f"Veritabanı kullanıcı ekleme hatası: {e}") # Updated print
        if e.args[0] == 1062:
            return jsonify({'message': 'Bu e-posta adresi zaten kullanımda.'}), 409 # Updated message
        return jsonify({'message': f'Veritabanı hatası oluştu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel kullanıcı ekleme hatası: {e}") # Updated print
        return jsonify({'message': 'Sunucu hatası, lütfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()

@app.route('/api/roles', methods=['GET'])
def get_distinct_roles():
    """Fetches distinct roles from the users table (excluding 'Admin')."""
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            sql = "SELECT DISTINCT role FROM users WHERE role != 'Admin'"
            cursor.execute(sql)
            roles = [row['role'] for row in cursor.fetchall()]

        return jsonify(roles), 200
    except pymysql.Error as e:
        print(f"Veritabanı hatası rolleri çekerken: {e}") # Updated print
        return jsonify({'message': f'Veritabanı hatası oluştu: {e.args[1]}'}), 500
    except Exception as e:
        print(f"Genel hata rolleri çekerken: {e}") # Updated print
        return jsonify({'message': 'Sunucu hatası, lütfen daha sonra tekrar deneyin.'}), 500
    finally:
        if connection:
            connection.close()


@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    """Fetches tasks, optionally filtered by assigned user."""
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
        print(f"Görevler çekilirken hata: {e}") # Updated print
        return jsonify({'message': 'Görevler çekilemedi.'}), 500 # Updated message
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
        return jsonify({'message': 'Gerekli alanlar eksik!'}), 400 # Updated message

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

            # Send notification to the newly assigned user
            send_notification(
                assigned_user_id,
                "Yeni Görev Atandı", # Updated message
                f"Size yeni bir görev atandı: '{title}'." # Updated message
            )

        return jsonify({'message': 'Görev başarıyla eklendi!'}), 201 # Updated message
    except Exception as e:
        print(f"Görev eklerken hata: {e}") # Updated print
        return jsonify({'message': 'Görev eklenirken hata oluştu.'}), 500 # Updated message
    finally:
        if connection:
            connection.close()

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
    created_by = int(data.get('created_by')) if data.get('created_by') else None

    if not all([title, start, new_assigned_user_id, created_by]):
        return jsonify({'message': 'Gerekli alanlar eksik!'}), 400 # Updated message

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

            # If the assigned user changed, send notifications to old and new users
            if old_assigned_user_id and old_assigned_user_id != new_assigned_user_id:
                send_notification(
                    old_assigned_user_id,
                    "Görev Ataması Değişti", # Updated message
                    f"'{title}' görevi artık size atanmamıştır." # Updated message
                )
            send_notification(
                new_assigned_user_id,
                "Görev Güncellendi", # Updated message
                f"Size atanan '{title}' görevi güncellendi." # Updated message
            )

        return jsonify({'message': 'Görev başarıyla güncellendi!'}), 200 # Updated message
    except Exception as e:
        print(f"Görev güncellerken hata: {e}") # Updated print
        return jsonify({'message': 'Görev güncellenirken hata oluştu.'}), 500 # Updated message
    finally:
        if connection:
            connection.close()

@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    """Deletes a task from the database."""
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Get task information to send notification
            cursor.execute("SELECT title, assigned_user_id FROM tasks WHERE id = %s", (task_id,))
            task_info = cursor.fetchone()
            
            cursor.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
            connection.commit()

            if task_info:
                send_notification(
                    task_info['assigned_user_id'],
                    "Görev Silindi", # Updated message
                    f"Size atanan '{task_info['title']}' görevi silindi." # Updated message
                )

        return jsonify({'message': 'Görev başarıyla silindi!'}), 200 # Updated message
    except Exception as e:
        print(f"Görev silerken hata: {e}") # Updated print
        return jsonify({'message': 'Görev silinirken hata oluştu.'}), 500 # Updated message
    finally:
        if connection:
            connection.close()

@app.route('/api/manager-stats')
def manager_stats():
    """Fetches statistics related to project managers' performance."""
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
    """Fetches performance metrics for workers (project managers)."""
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

@app.route('/ayarlar')
def ayarlar_page():
    """Renders the settings page."""
    return render_template('ayarlar.html')

@app.route('/api/roles', methods=['GET'])
def get_distinct_roles():
    """Fetches distinct roles from the users table (excluding 'Admin')."""
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            sql = "SELECT DISTINCT role FROM users WHERE role != 'Admin'"
            cursor.execute(sql)
            roles = [row['role'] for row in cursor.fetchall()]

        return jsonify(roles), 200
    except pymysql.Error as e:
        print(f"Database error fetching roles: {e}")
        return jsonify({'message': f'Database error occurred: {e.args[1]}'}), 500
    except Exception as e:
        print(f"General error fetching roles: {e}")
        return jsonify({'message': 'Server error, please try again later.'}), 500
    finally:
        if connection:
            connection.close()


@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    """Fetches tasks, optionally filtered by assigned user."""
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
        return jsonify({'message': 'Tasks could not be fetched.'}), 500
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

            # Send notification to the newly assigned user
            send_notification(
                assigned_user_id,
                "New Task Assigned",
                f"A new task has been assigned to you: '{title}'."
            )

        return jsonify({'message': 'Task successfully added!'}), 201
    except Exception as e:
        print(f"Error adding task: {e}")
        return jsonify({'message': 'Error occurred while adding task.'}), 500
    finally:
        if connection:
            connection.close()

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
    created_by = int(data.get('created_by')) if data.get('created_by') else None

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

            # If the assigned user changed, send notifications to old and new users
            if old_assigned_user_id and old_assigned_user_id != new_assigned_user_id:
                send_notification(
                    old_assigned_user_id,
                    "Task Assignment Changed",
                    f"The task '{title}' is no longer assigned to you."
                )
            send_notification(
                new_assigned_user_id,
                "Task Updated",
                f"The task '{title}' assigned to you has been updated."
            )

        return jsonify({'message': 'Task successfully updated!'}), 200
    except Exception as e:
        print(f"Error updating task: {e}")
        return jsonify({'message': 'Error occurred while updating task.'}), 500
    finally:
        if connection:
            connection.close()

@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    """Deletes a task from the database."""
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Get task information to send notification
            cursor.execute("SELECT title, assigned_user_id FROM tasks WHERE id = %s", (task_id,))
            task_info = cursor.fetchone()
            
            cursor.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
            connection.commit()

            if task_info:
                send_notification(
                    task_info['assigned_user_id'],
                    "Task Deleted",
                    f"The task '{task_info['title']}' assigned to you has been deleted."
                )

        return jsonify({'message': 'Task successfully deleted!'}), 200
    except Exception as e:
        print(f"Error deleting task: {e}")
        return jsonify({'message': 'Error occurred while deleting task.'}), 500
    finally:
        if connection:
            connection.close()

@app.route('/api/manager-stats')
def manager_stats():
    """Fetches statistics related to project managers' performance."""
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
    """Fetches performance metrics for workers (project managers)."""
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
