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
# Session management secret key
# THIS MUST BE REPLACED WITH A SECURE AND UNPREDICTABLE STRING!
app.secret_key = os.getenv("SECRET_KEY", "supersecretkeythatshouldbemorecomplex") 

@app.route('/')
@app.route('/login.html') # Both URLs will route to the same function
def serve_login_page():
    """Routes requests to the root URL (/) and /login.html to the login.html page."""
    return render_template('login.html')

@app.route('/index.html')
def serve_index_page():
    """Routes requests to /index.html to the index.html page."""
    return render_template('index.html')

@app.route('/ayarlar.html')
def serve_ayarlar_page():
    """Routes requests to /ayarlar.html to the ayarlar.html page.
    Accessible to all logged-in users, but content will be hidden on the frontend based on role."""
    if 'user_id' not in session:
        return redirect(url_for('serve_login_page'))
    # Allow all logged-in users to access the settings page
    return render_template('ayarlar.html')


@app.route('/kayitonay.html')
def serve_kayitonay_page():
    """Routes requests to /kayitonay.html to the kayitonay.html page."""
    return render_template('kayitonay.html')

@app.route('/musteriler.html')
def serve_musteriler_page():
    """Routes requests to /musteriler.html to the musteriler.html page."""
    return render_template('musteriler.html')

@app.route('/proje_ekle.html')
def serve_proje_ekle_page():
    """Routes requests to /proje_ekle.html to the proje_ekle.html page."""
    return render_template('proje_ekle.html')

@app.route('/projeler.html')
def serve_projeler_page():
    """Routes requests to /projeler.html to the projeler.html page."""
    return render_template('projeler.html')

@app.route('/raporlar.html')
def serve_raporlar_page():
    """Routes requests to /raporlar.html to the raporlar.html page.
    Checks if the user is logged in and has permission to access reports."""
    # Check if user is logged in
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
            # Redirect to home page if no permission
            return redirect(url_for('serve_index_page')) 
    else:
        # Redirect to login page if user role not found
        return redirect(url_for('serve_login_page'))

@app.route('/takvim.html')
def serve_takvim_page():
    """Routes requests to /takvim.html to the takvim.html page."""
    return render_template('takvim.html')

@app.route('/users.html')
def serve_users_page():
    """Routes requests to /users.html to the users.html page.
    Requires user to be logged in."""
    if 'user_id' not in session:
        return redirect(url_for('serve_login_page'))
    return render_template('users.html')

@app.route('/waiting.html')
def serve_waiting_page():
    """Routes requests to /waiting.html to the waiting.html page."""
    return render_template('waiting.html')

@app.route('/yeni_musteri.html')
def serve_yeni_musteri_page():
    """Routes requests to /yeni_musteri.html to the yeni_musteri.html page."""
    return render_template('yeni_musteri.html')

@app.route('/bildirim.html')
def serve_bildirim_page():
    """Routes requests to /bildirim.html to the bildirim.html page."""
    return render_template('bildirim.html')

# CORS (Cross-Origin Resource Sharing) settings
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

def get_db_connection():
    """Establishes and returns a database connection."""
    connection = None
    try:
        host = None
        port = None
        user = None
        password = None
        database = None

        public_url = os.getenv("MYSQL_PUBLIC_URL")
        print(f"DEBUG: MYSQL_PUBLIC_URL from env: '{public_url}'") 

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
                host = os.getenv("MYSQL_HOST") or "localhost"
                port = int(os.getenv("MYSQL_PORT") or 3306)
                user = os.getenv("MYSQL_USER") or "root"
                password = os.getenv("MYSQL_PASSWORD") or ""
                database = os.getenv("MYSQL_DATABASE") or "ser"
                print(f"DEBUG: Using individual env vars fallback: Host={host}, Port={port}, User={user}, DB={database}")
        else:
            print("DEBUG: MYSQL_PUBLIC_URL not found or empty. Using individual env vars.")
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
            cursorclass=pymysql.cursors.DictCursor 
        )
        print("Successfully connected to MySQL database!")
        return connection
    except pymysql.Error as e:
        print(f"MySQL connection error: {e}")
        if connection:
            connection.close()
        raise 

# Helper function: Gets user role from the database
def get_user_role_from_db(user_id):
    """Fetches the role of a user from the database."""
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

# Helper function: Checks if a role has a specific permission
def check_role_permission(role_name, permission_key):
    """Checks if a given role has a specific permission."""
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
            
            # If no permission record exists for the role or permission value is 0, return False
            if result and result[permission_key] == 1:
                return True
            return False
    except Exception as e:
        print(f"Error during permission check: {e}")
        return False
    finally:
        if connection:
            connection.close()


# Mark all notifications as read API (for notifications table)
@app.route('/api/notifications/mark_all_read', methods=['PUT'])
def mark_all_notifications_as_read():
    """Marks all notifications as read in the database."""
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = "UPDATE notifications SET is_read = 1 WHERE is_read = 0" 
            cursor.execute(sql)
            connection.commit()
            rows_affected = cursor.rowcount 
        return jsonify({'message': f'{rows_affected} notifications marked as read.'}), 200
    except pymysql.Error as e:
        print(f"Database error updating all notifications: {e}")
        return jsonify({'message': f'Database error occurred: {e.args[1]}'}), 500
    except Exception as e:
        print(f"General error updating all notifications: {e}")
        return jsonify({'message': 'Server error, please try again later.'}), 500
    finally:
        if connection:
            connection.close()

# Unread Notification Count API (for notifications table)
@app.route('/api/notifications/unread-count', methods=['GET'])
def get_unread_notifications_count():
    """Returns the count of unread notifications in the database."""
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'unread_count': 0, 'message': 'User ID missing.'}), 400 # Return 0 if user_id is missing

    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = "SELECT COUNT(id) as unread_count FROM notifications WHERE user_id = %s AND is_read = 0"
            cursor.execute(sql, (user_id,))
            result = cursor.fetchone()
            return jsonify(result), 200
    except pymysql.Error as e:
        print(f"Database error fetching unread notification count: {e}")
        return jsonify({'message': f'Database error occurred: {e.args[1]}'}), 500
    except Exception as e:
        print(f"General error fetching unread notification count: {e}")
        return jsonify({'message': 'Server error, please try again later.'}), 500
    finally:
        if connection:
            connection.close()


# Mark Notification as Read API (for notifications table)
@app.route('/api/notifications/<int:notification_id>/read', methods=['PUT'])
def mark_notification_as_read(notification_id):
    """Marks a specific notification as read in the database."""
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM notifications WHERE id = %s", (notification_id,))
            if not cursor.fetchone():
                return jsonify({'message': 'Notification not found.'}), 404

            sql = "UPDATE notifications SET is_read = 1 WHERE id = %s"
            cursor.execute(sql, (notification_id,))
            connection.commit()

        return jsonify({'message': 'Notification successfully marked as read.'}), 200
    except pymysql.Error as e:
        print(f"Database error updating notification: {e}")
        return jsonify({'message': f'Database error occurred: {e.args[1]}'}), 500
    except Exception as e:
        print(f"General error updating notification: {e}")
        return jsonify({'message': 'Server error, please try again later.'}), 500
    finally:
        if connection:
            connection.close()

# Fetch Notifications API (for notifications table)
@app.route('/api/notifications', methods=['GET'])
def get_notifications():
    """Fetches notifications for a specific user."""
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'message': 'User ID missing.'}), 400

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
        print(f"Database error fetching notifications: {e}")
        return jsonify({'message': f'Database error occurred: {e.args[1]}'}), 500
    except Exception as e:
        print(f"General error fetching notifications: {e}")
        return jsonify({'message': 'Server error, please try again later.'}), 500
    finally:
        if connection:
            connection.close()

@app.route('/api/notifications/<int:notification_id>', methods=['DELETE'])
def delete_notification(notification_id):
    """Deletes a specific notification for the logged-in user."""
    if 'user_id' not in session:
        return jsonify({'message': 'Login required.'}), 401

    user_id = session['user_id']
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # Allow user to delete only their own notification
            cursor.execute("SELECT id FROM notifications WHERE id = %s AND user_id = %s", (notification_id, user_id))
            if not cursor.fetchone():
                return jsonify({'message': 'Notification not found or you do not have permission to delete it.'}), 404

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
    if 'user_id' not in session:
        return jsonify({'message': 'Login required.'}), 401

    user_id = session['user_id']
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


# Add New Notification API (for notifications table)
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
        print(f"Database error saving notification: {e}")
        if e.args[0] == 1062:
            return jsonify({'message': 'This email address is already in use.'}), 409
        return jsonify({'message': f'Database error occurred: {e.args[1]}'}), 500
    except Exception as e:
        print(f"General error saving notification: {e}")
        return jsonify({'message': 'Server error, please try again later.'}), 500
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
        print(f"Database error saving activity: {e}")
        return jsonify({'message': f'Database error occurred: {e.args[1]}'}), 500
    except Exception as e:
        print(f"General error saving activity: {e}")
        return jsonify({'message': 'Server error, please try again later.'}), 500
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
        return jsonify({'message': 'User ID missing.'}), 400

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT profile_picture, hide_email, hide_phone FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()

            if not user:
                return jsonify({'message': 'User not found.'}), 404

            updates = []
            params = []
            message_parts = []

            # Handle profile_picture: if it's explicitly null from frontend, set DB to NULL
            # If profile_picture is 'null' string, set to SQL NULL. Otherwise, update with the new value.
            if profile_picture is not None: 
                if profile_picture == "null": 
                    updates.append("profile_picture = NULL")
                    message_parts.append("Profile Picture Removed")
                elif profile_picture != user['profile_picture']: # Only update if different from current DB value
                    updates.append("profile_picture = %s")
                    params.append(profile_picture)
                    message_parts.append("Profile Picture")
            
            if hide_email is not None and hide_email != user['hide_email']:
                updates.append("hide_email = %s")
                params.append(hide_email)
                message_parts.append("Email Visibility")

            if hide_phone is not None and hide_phone != user['hide_phone']:
                updates.append("hide_phone = %s")
                params.append(hide_phone)
                message_parts.append("Phone Visibility")

            if not updates:
                return jsonify({'message': 'No information to update.'}), 200

            sql = f"UPDATE users SET {', '.join(updates)} WHERE id = %s"
            params.append(user_id)

            cursor.execute(sql, tuple(params))
            connection.commit()

            final_message = "Successfully updated: " + ", ".join(message_parts) + "."
            if not message_parts: 
                 final_message = "No changes to update."

            return jsonify({'message': final_message}), 200

    except pymysql.Error as e:
        print(f"Database error updating profile: {e}")
        return jsonify({'message': f'Database error occurred: {e.args[1]}'}), 500
    except Exception as e:
        print(f"General error updating profile: {e}")
        return jsonify({'message': 'Server error, please try again later.'}), 500
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
        print(f"Database error fetching pending users: {e}")
        return jsonify({'message': f'Database error occurred: {e.args[1]}'}), 500
    except Exception as e:
        print(f"General error fetching pending users: {e}")
        return jsonify({'message': 'Server error, please try again later.'}), 500
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
                return jsonify({'message': 'User not found.'}), 404
            if user['onay'] == 1:
                return jsonify({'message': 'User already approved.'}), 400 

            sql = "UPDATE users SET onay = 1 WHERE id = %s"
            cursor.execute(sql, (user_id,))
            connection.commit()

        return jsonify({'message': 'User successfully approved!'}), 200

    except pymysql.Error as e:
        print(f"Database error approving user: {e}")
        return jsonify({'message': f'Database error occurred: {e.args[1]}'}), 500
    except Exception as e:
        print(f"General error approving user: {e}")
        return jsonify({'message': 'Server error, please try again later.'}), 500
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
                print(f"DEBUG: Reassigned {cursor.rowcount} projects from user {user_id} to {default_manager_id}")
            else:
                cursor.execute("DELETE FROM projects WHERE project_manager_id = %s", (user_id,))
                print(f"DEBUG: Deleted {cursor.rowcount} projects for user {user_id} (no manager to reassign to)")

            cursor.execute("DELETE FROM tasks WHERE assigned_user_id = %s", (user_id,))
            print(f"DEBUG: Deleted {cursor.rowcount} tasks for user {user_id}")

            sql = "DELETE FROM users WHERE id = %s"
            cursor.execute(sql, (user_id,))
            connection.commit()
            print(f"DEBUG: Deleted user {user_id}")

        return jsonify({'message': 'User successfully deleted!'}), 200

    except pymysql.Error as e:
        print(f"Database error deleting user: {e}")
        return jsonify({'message': f'Database error occurred: {e.args[1]}'}), 500
    except Exception as e:
        print(f"General error deleting user: {e}")
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
    print("Error: 'turkey_locations.json' file is not in JSON format or is corrupted.")
    TURKEY_LOCATIONS = {"Türkiye": {"iller": {"Varsayılan İl": []}}} 
except Exception as e:
    print(f"Unexpected error loading location data: {e}")
    TURKEY_LOCATIONS = {"Türkiye": {"iller": {"Varsayılan İl": []}}} 


@app.route('/api/role-permissions', methods=['GET'])
def get_permissions_by_role():
    """Fetches permissions for a given role."""
    role_name = request.args.get('role')
    if not role_name:
        return jsonify({'message': 'Role name required'}), 400

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
        return jsonify({'message': 'Please fill in all required fields.'}), 400

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            existing_user = cursor.fetchone()
            if existing_user:
                return jsonify({'message': 'This email address is already in use.'}), 409

            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            sql = """
            INSERT INTO users (fullname, email, phone, password, role, profile_picture, hide_email, hide_phone)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (fullname, email, phone, hashed_password, role, profile_picture, hide_email, hide_phone))
            connection.commit()
        return jsonify({'message': 'Registration successful!'}), 201
    except pymysql.Error as e:
        print(f"Database registration error: {e}")
        if e.args[0] == 1062:
            return jsonify({'message': 'This email address is already in use.'}), 409
        return jsonify({'message': f'Database error occurred: {e.args[1]}'}), 500
    except Exception as e:
        print(f"General registration error: {e}")
        return jsonify({'message': 'Server error, please try again later.'}), 500
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
        return jsonify({'message': 'Please enter your email and password.'}), 400

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Fetch all user details including new fields
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
            del user['password'] 

            return jsonify({
                'message': 'Login successful!',
                'user': user 
            }), 200

    except pymysql.Error as e:
        print(f"Database login error: {e}")
        return jsonify({'message': f'Database error occurred: {e.args[1]}'}), 500
    except Exception as e:
        print(f"General login error: {e}")
        return jsonify({'message': 'Server error, please try again later.'}), 500
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

            log_activity(
                user_id=user_id,
                title='New Customer Added',
                description=f'New customer "{customer_name}" added.',
                icon='fas fa-user-plus'
            )

        return jsonify({'message': 'Customer successfully added!', 'customerId': new_customer_id}), 201

    except pymysql.Error as e:
        print(f"Database error adding customer: {e}")
        if e.args[0] == 1062:
            return jsonify({'message': 'This email or company name is already registered.'}), 409
        return jsonify({'message': f'Database error occurred: {e.args[1]}'}), 500
    except Exception as e:
        print(f"General error adding customer: {e}")
        return jsonify({'message': 'Server error, please try again later.'}), 500
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
        print(f"Database error fetching customers: {e}")
        return jsonify({'message': f'Database error occurred: {e.args[1]}'}), 500
    except Exception as e:
        print(f"General error fetching customers: {e}")
        return jsonify({'message': 'Server error, please try again later.'}), 500
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
                return jsonify({'message': 'Customer not found.'}), 404

        return jsonify(customer), 200
    except pymysql.Error as e:
        print(f"Database error fetching customer details: {e}")
        return jsonify({'message': f'Database error occurred: {e.args[1]}'}), 500
    except Exception as e:
        print(f"General error fetching customer details: {e}")
        return jsonify({'message': 'Server error, please try again later.'}), 500
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
        return jsonify({'message': 'User ID missing.'}), 400
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
                return jsonify({'message': 'No field specified for update.'}), 400

            sql = f"UPDATE customers SET {', '.join(updates)} WHERE customer_id = %s"
            params.append(customer_id)

            cursor.execute(sql, tuple(params))
            connection.commit()

            if cursor.rowcount == 0:
                return jsonify({'message': 'Customer data is already up-to-date or no changes were made.'}), 200

            log_activity(
                user_id=user_id,
                title='Customer Updated',
                description=f'Customer "{old_customer_name}" information updated.',
                icon='fas fa-user-edit'
            )

        return jsonify({'message': 'Customer successfully updated!'}), 200

    except pymysql.Error as e:
        print(f"Database error updating customer: {e}")
        if e.args[0] == 1062:
            return jsonify({'message': 'This email or company name is already registered.'}), 409
        return jsonify({'message': f'Database error occurred: {e.args[1]}'}), 500
    except Exception as e:
        print(f"General error updating customer: {e}")
        return jsonify({'message': 'Server error, please try again later.'}), 500
    finally:
        if connection:
            connection.close()

@app.route('/api/customers/<int:customer_id>', methods=['DELETE'])
def delete_customer(customer_id):
    """Deletes a customer from the database."""
    user_id = request.args.get('user_id') 
    if not user_id:
        return jsonify({'message': 'User ID missing.'}), 400

    customer_name = "Unknown Customer" 
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
            
            log_activity(
                user_id=user_id,
                title='Customer Deleted',
                description=f'Customer "{customer_name}" deleted.',
                icon='fas fa-user-minus'
            )

        return jsonify({'message': 'Customer successfully deleted!'}), 200

    except pymysql.Error as e:
        print(f"Database error deleting customer: {e}")
        if e.args[0] == 1451: 
            return jsonify({'message': 'There are projects associated with this customer. Please delete the related projects first.'}), 409
        return jsonify({'message': f'Database error occurred: {e.args[1]}'}), 500
    except Exception as e:
        print(f"General error deleting customer: {e}")
        return jsonify({'message': 'Server error, please try again later.'}), 500
    finally:
        if connection:
            connection.close()


# List All Projects API
@app.route('/api/projects', methods=['GET'])
def get_projects():
    """Fetches a list of all projects with their associated customer and manager names."""
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # First, update project statuses based on dates
            cursor.execute("""
                UPDATE projects
                SET status = CASE
                    WHEN status = 'Tamamlandı' THEN 'Tamamlandı' 
                    WHEN CURDATE() < DATE(meeting_date) THEN 'Planlama Aşamasında'
                    WHEN CURDATE() >= DATE(start_date) AND CURDATE() <= DATE(end_date) THEN 'Aktif'
                    WHEN CURDATE() > DATE(end_date) AND status != 'Tamamlandı' THEN 'Gecikti'
                    ELSE status 
                END
                WHERE status != 'Tamamlandı'; 
            """)
            connection.commit() 

            sql = """
            SELECT p.project_id, p.project_name, p.reference_no, p.description, p.contract_date,
                    p.meeting_date, p.start_date, p.end_date, p.project_location, p.status,
                    c.customer_name, u.fullname AS project_manager_name, c.customer_id, u.id AS project_manager_user_id,
                    (SELECT COUNT(*) FROM project_progress pp WHERE pp.project_id = p.project_id AND pp.delay_days > 0) AS has_step_delay,
                    (SELECT IFNULL(SUM(pp.delay_days),0) FROM project_progress pp WHERE pp.project_id = p.project_id) AS delay_days
            FROM projects p
            JOIN customers c ON p.customer_id = c.customer_id
            JOIN users u ON p.project_manager_id = u.id
            ORDER BY p.created_at DESC
            """
            cursor.execute(sql)
            projects_data = cursor.fetchall()

            projects_to_update_with_step_delay_status = []
            for project in projects_data:
                original_status = project['status']
                new_status = original_status

                if original_status == 'Aktif' and project['has_step_delay'] > 0:
                    new_status = 'Aktif (İş Gecikmeli)'
                elif original_status == 'Planlama Aşamasında' and project['has_step_delay'] > 0:
                    new_status = 'Planlama (İş Gecikmeli)'

                if new_status != original_status:
                    projects_to_update_with_step_delay_status.append({'project_id': project['project_id'], 'status': new_status})

                # Convert datetime.date objects to ISO format strings for JSON serialization
                project['contract_date'] = project['contract_date'].isoformat() if isinstance(project['contract_date'], datetime.date) else None
                project['meeting_date'] = project['meeting_date'].isoformat() if isinstance(project['meeting_date'], datetime.date) else None
                project['start_date'] = project['start_date'].isoformat() if isinstance(project['start_date'], datetime.date) else None
                project['end_date'] = project['end_date'].isoformat() if isinstance(project['end_date'], datetime.date) else None

            # Apply status updates if any projects need it
            if projects_to_update_with_step_delay_status:
                update_sql = "UPDATE projects SET status = %s WHERE project_id = %s"
                for proj_info in projects_to_update_with_step_delay_status:
                    cursor.execute(update_sql, (proj_info['status'], proj_info['project_id']))
                connection.commit() 

        return jsonify(projects_data), 200
    except pymysql.Error as e:
        print(f"Database error fetching projects: {e}")
        return jsonify({'message': f'Database error occurred: {e.args[1]}'}), 500
    except Exception as e:
        print(f"General error fetching projects: {e}")
        return jsonify({'message': 'Server error, please try again later.'}), 500
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
                return jsonify({'message': 'Project not found.'}), 404

            # Convert datetime.date objects to ISO format strings for JSON serialization
            project['contract_date'] = project['contract_date'].isoformat() if isinstance(project['contract_date'], datetime.date) else None
            project['meeting_date'] = project['meeting_date'].isoformat() if isinstance(project['meeting_date'], datetime.date) else None
            project['start_date'] = project['start_date'].isoformat() if isinstance(project['start_date'], datetime.date) else None
            project['end_date'] = project['end_date'].isoformat() if isinstance(project['end_date'], datetime.date) else None

        return jsonify(project), 200
    except pymysql.Error as e:
        print(f"Database error fetching project details: {e}")
        return jsonify({'message': f'Database error occurred: {e.args[1]}'}), 500
    except Exception as e:
        print(f"General error fetching project details: {e}")
        return jsonify({'message': 'Server error, please try again later.'}), 500
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
            print(f"Notification sent: User ID: {user_id}, Title: '{title}', Message: '{message}'")
    except pymysql.Error as e:
        print(f"Database error sending notification: {e}")
    except Exception as e:
        print(f"General error sending notification: {e}")
    finally:
        if connection:
            connection.close()

# Update Project API (PUT) - for projects table
@app.route('/api/projects/<int:project_id>', methods=['PUT'])
def update_project(project_id):
    """Updates an existing project's information."""
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
    user_id = data.get('user_id') # ID of the user performing the update

    if not user_id: 
        return jsonify({'message': 'User ID missing.'}), 400

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Get existing project information
            cursor.execute("SELECT project_name, project_manager_id FROM projects WHERE project_id = %s", (project_id,))
            existing_project_info = cursor.fetchone()
            if not existing_project_info:
                return jsonify({'message': 'Project not found.'}), 404
            old_project_name = existing_project_info['project_name']
            project_manager_id = existing_project_info['project_manager_id']

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
                return jsonify({'message': 'No field specified for update.'}), 400

            sql = f"UPDATE projects SET {', '.join(updates)} WHERE project_id = %s"
            params.append(project_id)

            cursor.execute(sql, tuple(params))
            connection.commit()

            if cursor.rowcount == 0:
                return jsonify({'message': 'Project data is already up-to-date or no changes were made.'}), 200

            log_activity(
                user_id=user_id,
                title='Project Updated',
                description=f'Project "{old_project_name}" information updated.',
                icon='fas fa-edit'
            )
            
            # Send notification to project manager
            send_notification(
                project_manager_id,
                "Project Updated",
                f"The project '{project_name}' you are managing has been updated."
            )

        return jsonify({'message': 'Project successfully updated!'}), 200

    except pymysql.Error as e:
        print(f"Database error updating project: {e}")
        return jsonify({'message': f'Database error occurred: {e.args[1]}'}), 500
    except Exception as e:
        print(f"General error updating project: {e}")
        return jsonify({'message': 'Server error, please try again later.'}), 500
    finally:
        if connection:
            connection.close()

# Delete Project API (DELETE)
@app.route('/api/projects/<int:project_id>', methods=['DELETE'])
def delete_project_api(project_id):
    """Deletes a project from the database."""
    user_id = request.args.get('user_id') 
    if not user_id:
        return jsonify({'message': 'User ID missing.'}), 400

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

            log_activity(
                user_id=user_id,
                title='Project Deleted',
                description=f'Project "{project_name}" deleted.',
                icon='fas fa-trash'
            )

            # Send notification to project manager
            send_notification(
                project_manager_id,
                "Project Deleted",
                f"The project '{project_name}' you are managing has been deleted."
            )
           
        return jsonify({'message': 'Project successfully deleted!'}), 200

    except pymysql.Error as e:
        print(f"Database error deleting project: {e}")
        if e.args[0] == 1451: 
            return jsonify({'message': 'There are projects associated with this customer. Please delete the related projects first.'}), 409
        return jsonify({'message': f'Database error occurred: {e.args[1]}'}), 500
    except Exception as e:
        print(f"General error deleting project: {e}")
        return jsonify({'message': 'Server error, please try again later.'}), 500
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
        print(f"Database error fetching managers: {e}")
        return jsonify({'message': f'Database error occurred: {e.args[1]}'}), 500
    except Exception as e:
        print(f"General error fetching managers: {e}")
        return jsonify({'message': 'Server error, please try again later.'}), 500
    finally:
        if connection:
            connection.close()

# API endpoint to provide location data
@app.route('/api/locations/turkey', methods=['GET'])
def get_turkey_locations():
    """Returns Turkey's location data (provinces and districts)."""
    if not TURKEY_LOCATIONS:
        return jsonify({'message': 'Location data could not be loaded or is empty.'}), 500
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
        print(f"Database error fetching statistics: {e}")
        return jsonify({'message': f'Database error occurred: {e.args[1]}'}), 500
    except Exception as e:
        print(f"General error fetching statistics: {e}")
        return jsonify({'message': 'Server error, please try again later.'}), 500
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
        print(f"Database error (recent_activities): {e}")
        return jsonify({"error": "Database error occurred."}), 500
    except Exception as e:
        print(f"Unknown error (recent_activities): {e}")
        return jsonify({"error": "An unknown server error occurred."}), 500
    finally:
        if connection: 
            connection.close()


# Helper function to log a new activity
def log_activity(user_id, title, description, icon, is_read=0):
    """Logs a new activity in the activities table."""
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            user_fullname = "Unknown User"
            if user_id:
                cursor.execute("SELECT fullname FROM users WHERE id = %s", (user_id,))
                user = cursor.fetchone()
                if user:
                    user_fullname = user['fullname']

            # Remove potential (ID: X) from description if present
            cleaned_description = re.sub(r' \(ID: \d+\)', '', description)

            full_description = f"{user_fullname} tarafından: {cleaned_description}" # Turkish translation for "by"

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
    start_date = data.get('startDate')
    end_date = data.get('endDate')
    project_location = data.get('projectLocation')
    status = data.get('status', 'Planlama Aşamasında') 

    user_id = data.get('user_id') # User ID adding the project (for activity log)

    if not all([project_name, customer_id, project_manager_id]): # user_id check comes from frontend
        return jsonify({'message': 'Project name, customer, and project manager are required.'}), 400

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

            # Send notification to project manager
            send_notification(
                project_manager_id,
                "New Project Assigned",
                f"A new project has been assigned to you: '{project_name}'."
            )

        log_activity(
            user_id=user_id,
            title='New Project Added',
            description=f'New project "{project_name}" created.',
            icon='fas fa-plus'
        )
        return jsonify({"message": "Project successfully added", "projectId": new_project_id}), 201
    except pymysql.Error as e:
        print(f"Database error adding project: {e}")
        return jsonify({'message': f'Database error occurred: {e.args[1]}'}), 500
    except Exception as e:
        print(f"General error adding project: {e}")
        return jsonify({'message': 'Server error, please try again later.'}), 500
    finally:
        if connection:
            connection.close()

# API to log PDF Report Creation Activity (to be called from frontend)
@app.route('/api/log_pdf_report', methods=['POST'])
def log_pdf_report_api():
    """Logs the creation of a PDF report as an activity."""
    data = request.get_json()
    user_id = data.get('user_id')
    report_type = data.get('report_type', 'General Report') 
    project_name = data.get('project_name') 

    if not user_id:
        return jsonify({'message': 'User ID missing.'}), 400

    description_text = f'PDF file of "{report_type}" report created.'
    if project_name:
        description_text = f'PDF report created for project "{project_name}".'

    try:
        log_activity(
            user_id=user_id,
            title='PDF Report Created',
            description=description_text,
            icon='fas fa-file-pdf'
        )
        return jsonify({'message': 'PDF report activity successfully logged.'}), 200
    except Exception as e:
        print(f"Error logging PDF report activity: {e}")
        return jsonify({'message': 'Error logging PDF report activity.'}), 500


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
        print(f"Database error fetching progress step: {e}")
        return jsonify({'message': f'Database error occurred: {e.args[1]}'}), 500
    except Exception as e:
        print(f"General error fetching progress step: {e}")
        return jsonify({'message': 'Server error, please try again later.'}), 500
    finally:
        if connection:
            connection.close()

# Add New Project Progress Step API (called from projects.html)
@app.route('/api/projects/<int:project_id>/progress', methods=['POST'])
def add_project_progress_step_from_modal():
    """Adds a new progress step to a project."""
    data = request.get_json()
    project_id = data.get('project_id') # Get project_id from data, not URL
    step_name = data.get('step_name')
    description = data.get('description')
    start_date_str = data.get('start_date')
    end_date_str = data.get('end_date')

    if not all([project_id, step_name, start_date_str, end_date_str]):
        return jsonify({'message': 'Project ID, title, start and end date are required.'}), 400

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
                    "Project Progress Step Added",
                    f"A new progress step ('{step_name}') has been added to project '{project_name}'."
                )

        return jsonify({'message': 'Progress step successfully added!', 'progress_id': new_progress_id}), 201
    except pymysql.Error as e:
        print(f"Database error adding progress step: {e}")
        return jsonify({'message': f'Database error occurred: {e.args[1]}'}), 500
    except Exception as e:
        print(f"General error adding progress step: {e}")
        return jsonify({'message': 'Server error, please try again later.'}), 500
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
        return jsonify({'message': 'Title, start and end date are required.'}), 400

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Get project ID and title of the existing progress step
            cursor.execute("SELECT project_id, title FROM project_progress WHERE progress_id = %s", (progress_id,))
            existing_step = cursor.fetchone()
            if not existing_step:
                return jsonify({'message': 'Progress step not found.'}), 404

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
                return jsonify({'message': 'Progress step data is already up-to-date or no changes were made.'}), 200

            # Send notification to project manager
            cursor.execute("SELECT project_manager_id, project_name FROM projects WHERE project_id = %s", (current_project_id,))
            project_info = cursor.fetchone()
            if project_info:
                project_manager_id = project_info['project_manager_id']
                project_name = project_info['project_name']
                send_notification(
                    project_manager_id,
                    "Project Progress Step Updated",
                    f"The progress step '{step_name}' in project '{project_name}' has been updated."
                )

        return jsonify({'message': 'Progress step successfully updated!'}), 200
    except pymysql.Error as e:
        print(f"Database error updating progress step: {e}")
        return jsonify({'message': f'Database error occurred: {e.args[1]}'}), 500
    except Exception as e:
        print(f"General error updating progress step: {e}")
        return jsonify({'message': 'Server error, please try again later.'}), 500
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
                return jsonify({'message': 'Progress step could not be deleted or not found.'}), 404
            
            current_project_id = step_info['project_id']
            step_name = step_info['title']

            sql = "DELETE FROM project_progress WHERE progress_id = %s"
            cursor.execute(sql, (progress_id,))
            connection.commit()

            if cursor.rowcount == 0:
                return jsonify({'message': 'Progress step could not be deleted or not found.'}), 404

            # Send notification to project manager
            cursor.execute("SELECT project_manager_id, project_name FROM projects WHERE project_id = %s", (current_project_id,))
            project_info = cursor.fetchone()
            if project_info:
                project_manager_id = project_info['project_manager_id']
                project_name = project_info['project_name']
                send_notification(
                    project_manager_id,
                    "Project Progress Step Deleted",
                    f"The progress step '{step_name}' in project '{project_name}' has been deleted."
                )

        return jsonify({'message': 'Progress step successfully deleted!'}), 200
    except pymysql.Error as e:
        print(f"Database error deleting progress step: {e}")
        return jsonify({'message': f'Database error occurred: {e.args[1]}'}), 500
    except Exception as e:
        print(f"General error deleting progress step: {e}")
        return jsonify({'message': 'Server error, please try again later.'}), 500
    finally:
        if connection:
            connection.close()

@app.route('/api/user-info', methods=['GET'])
def get_user_info():
    """Fetches detailed information for a single user."""
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'message': 'User ID missing'}), 400

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Fetch all user fields including new ones
            cursor.execute("SELECT id, fullname, email, phone, role, profile_picture, hide_email, hide_phone, created_at FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            if not user:
                return jsonify({'message': 'User not found'}), 404
            
            # Convert datetime objects to string for JSON serialization
            if 'created_at' in user and isinstance(user['created_at'], datetime.datetime):
                user['created_at'] = user['created_at'].isoformat()

            return jsonify(user), 200
    except Exception as e:
        print(f"General error fetching user info: {e}")
        return jsonify({'message': 'Server error, please try again later.'}), 500
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
            # Fetch all user fields including new ones
            cursor.execute("SELECT id, fullname, email, phone, role, profile_picture, hide_email, hide_phone, created_at FROM users")
            users = cursor.fetchall()
            
            # Convert datetime objects to string for JSON serialization
            for user in users:
                if 'created_at' in user and isinstance(user['created_at'], datetime.datetime):
                    user['created_at'] = user['created_at'].isoformat()

            return jsonify(users), 200
    except pymysql.Error as e:
        print(f"Database error fetching all users: {e}")
        return jsonify({'message': f'Database error occurred: {e.args[1]}'}), 500
    except Exception as e:
        print(f"General error fetching all users: {e}")
        return jsonify({'message': 'Server error, please try again later.'}), 500
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
        return jsonify({'message': 'All fields are required!'}), 400

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
        return jsonify({'message': 'User successfully added!'}), 201
    except pymysql.Error as e:
        print(f"Database error adding user: {e}")
        if e.args[0] == 1062:
            return jsonify({'message': 'This email address is already in use.'}), 409
        return jsonify({'message': f'Database error occurred: {e.args[1]}'}), 500
    except Exception as e:
        print(f"General error adding user: {e}")
        return jsonify({'message': 'Server error, please try again later.'}), 500
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
