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
# THIS SHOULD BE A SECURE AND UNPREDICTABLE STRING!
app.secret_key = os.getenv("SECRET_KEY", "supersecretkeythatshouldbemorecomplex") 
CORS(app, resources={r"/*": {"origins": ["https://37.148.213.89:8000", "http://serotomasyon.tr"]}}, supports_credentials=True)
@app.route('/')
def serve_welcome_page():
    """Directs root URL (/) requests to the welcome.html page."""
    return render_template('welcome.html')

@app.route('/login.html') 
def serve_login_page():
    """Directs /login.html requests to the login.html page."""
    return render_template('login.html')

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
        # If a single URL environment variable like MySQL_PUBLIC_URL is used, it tries to parse it.
        # Assuming XCloud does not provide such a URL, this part will likely not work.
        # But keeping it as it was in your code.
        public_url = os.getenv("MYSQL_PUBLIC_URL")
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
                print(f"ERROR: Could not parse MYSQL_PUBLIC_URL: {url_parse_e}. Falling back to fixed values or individual environment variables.")
                # Fallback to fixed values or individual environment variables in case of URL parsing error
                host = os.getenv("MYSQL_HOST", "localhost")
                port = int(os.getenv("MYSQL_PORT", 3306))
                user = os.getenv("MYSQL_USER", "admin") # Updated
                password = os.getenv("MYSQL_PASSWORD", "Ser171234") # Updated
                database = os.getenv("MYSQL_DATABASE", "ser_db") # Updated
                print(f"DEBUG: Using environment variables or fixed values: Host={host}, Port={port}, User={user}, DB={database}")
        else:
            print("DEBUG: MYSQL_PUBLIC_URL not found or empty. Using environment variables or fixed values.")
            # If MYSQL_PUBLIC_URL is not present or empty, use individual environment variables.
            # If environment variables are also not present, use the fixed values specified here.
            host = os.getenv("MYSQL_HOST", "localhost")
            port = int(os.getenv("MYSQL_PORT", 3306))
            user = os.getenv("MYSQL_USER", "admin") # Updated
            password = os.getenv("MYSQL_PASSWORD", "Ser171234") # Updated
            database = os.getenv("MYSQL_DATABASE", "ser_db") # Updated
            print(f"DEBUG: Using environment variables or fixed values: Host={host}, Port={port}, User={user}, DB={database}")

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

# Helper function: Checks if a role has a specific permission
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

@app.route('/api/update_user_profile', methods=['POST'])
def update_user_profile():
    """Updates user profile information, including profile picture and visibility settings.
    Personal details (full name, email, phone, role) are no longer updated via this endpoint,
    as the frontend modal for these fields has been removed."""
    data = request.get_json()
    user_id = data.get('userId')
    profile_picture = data.get('profile_picture')
    hide_email = data.get('hide_email')
    hide_phone = data.get('hide_phone')

    if not user_id:
        return jsonify({'message': 'User ID is missing.'}), 400

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

            if profile_picture is not None:
                if profile_picture == "null":
                    updates.append("profile_picture = NULL")
                    message_parts.append("Profile Picture Removed")
                elif profile_picture != user['profile_picture']:
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
                 final_message = "No changes found to update."

            return jsonify({'message': final_message}), 200

    except pymysql.Error as e:
        print(f"Database error while updating profile: {e}")
        return jsonify({'message': f'Database error occurred: {e.args[1]}'}), 500
    except Exception as e:
        print(f"General error while updating profile: {e}")
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
        print(f"Database error while approving user: {e}")
        return jsonify({'message': f'Database error occurred: {e.args[1]}'}), 500
    except Exception as e:
        print(f"General error while approving user: {e}")
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
    """Registers a new user."""
    data = request.get_json()
    fullname = data.get('fullname')
    email = data.get('email')
    phone = data.get('phone', '')
    password = data.get('password')
    role = data.get('role', 'Employee') # Default position if not provided
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
            # To call your own API, Flask's test client or requests library can be used.
            # Here, an internal call is simulated using Flask's test_client.
            # It might be more appropriate to call the add_activity function directly instead of making an actual HTTP request.
            # However, if add_activity is designed as an HTTP endpoint, such a call might make sense.
            # For simplicity and to avoid circular dependencies, I am leaving a note assuming add_activity will be called externally
            # instead of calling log_activity directly.
            # If add_activity is not called from the frontend, this logging operation will not be performed.
            # In this case, calling log_activity directly might be more appropriate.

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
                p.status,
                c.customer_name,
                u.fullname AS project_manager_name,
                c.customer_id,
                u.id AS project_manager_user_id,
                -- Get the latest progress title and delay days
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
                # Set project status based on the latest progress title
                # If there is no latest progress, use the project's own status
                display_status = project['last_progress_title'] if project['last_progress_title'] else project['status']

                # If there is a delay in the latest step, update the status
                if project['last_progress_delay_days'] is not None and project['last_progress_delay_days'] > 0:
                    display_status += ' (Delayed)'

                project['display_status'] = display_status # Add as a new field

                # Convert datetime.date objects to ISO formatted strings for JSON serialization
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

            # Convert datetime.date objects to ISO formatted strings for JSON serialization
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
        print(f"Database error while sending notification: {e}")
    except Exception as e:
        print(f"General error while sending notification: {e}")
    finally:
        if connection:
            connection.close()

# Project Update API (PUT) - for projects table
# Find the update_project function in app.py and update it as follows:

@app.route('/api/projects/<int:project_id>', methods=['PUT'])
def update_project(project_id):
    data = request.get_json()
    print(f"DEBUG: Raw JSON data received by update_project: {data}")
    print(f"DEBUG: Project ID to be updated: {project_id}")

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

    # Get customer_id here
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

    print(f"DEBUG: Processed values: "
          f"name='{project_name}', ref='{reference_no}', description='{description}', "
          f"contract='{contract_date}', meeting='{meeting_date}', start='{start_date}', end='{end_date}', "
          f"location='{project_location}', status='{status}', customer_id='{customer_id_new}', manager_id='{project_manager_id_new}', user_id='{user_id}'")

    if not user_id:
        print("ERROR: User ID is missing.")
        return jsonify({'message': 'User ID is missing.'}), 400

    connection = None
    try:
        connection = get_db_connection()
        print("DEBUG: Database connection established.")
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT project_name, reference_no, description, contract_date, meeting_date,
                       start_date, end_date, project_location, status, customer_id, project_manager_id
                FROM projects WHERE project_id = %s
            """, (project_id,))
            existing_project_info = cursor.fetchone()
            print(f"DEBUG: Existing project information: {existing_project_info}")

            if not existing_project_info:
                print("ERROR: Project not found.")
                return jsonify({'message': 'Project not found.'}), 404

            old_project_name = existing_project_info['project_name']
            old_reference_no = existing_project_info['reference_no']
            old_description = existing_project_info['description']
            old_contract_date = existing_project_info['contract_date'].isoformat() if isinstance(existing_project_info['contract_date'], datetime.date) else None
            old_meeting_date = existing_project_info['meeting_date'].isoformat() if isinstance(existing_project_info['meeting_date'], datetime.date) else None
            old_start_date = existing_project_info['start_date'].isoformat() if isinstance(existing_project_info['start_date'], datetime.date) else None
            old_end_date = existing_project_info['end_date'].isoformat() if isinstance(existing_project_info['end_date'], datetime.date) else None
            old_project_location = existing_project_info['project_location']
            old_status = existing_project_info['status']
            old_customer_id = existing_project_info['customer_id'] # Old customer ID
            old_project_manager_id = existing_project_info['project_manager_id']

            print(f"DEBUG: Old values: "
                  f"name='{old_project_name}', ref='{old_reference_no}', description='{old_description}', "
                  f"contract='{old_contract_date}', meeting='{old_meeting_date}', start='{old_start_date}', end='{old_end_date}', "
                  f"location='{old_project_location}', status='{old_status}', customer_id='{old_customer_id}', manager_id='{old_project_manager_id}'")

            updates = []
            params = []

            # Comparison logic
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

            # Customer ID update added
            if customer_id_new != old_customer_id:
                updates.append("customer_id = %s")
                params.append(customer_id_new)

            if project_manager_id_new != old_project_manager_id:
                updates.append("project_manager_id = %s")
                params.append(project_manager_id_new)

            if not updates:
                print("DEBUG: No information to update, returning 200.")
                return jsonify({'message': 'No information to update.'}), 200

            sql = f"UPDATE projects SET {', '.join(updates)} WHERE project_id = %s"
            params.append(project_id)
            print(f"DEBUG: Generated SQL: {sql}")
            print(f"DEBUG: SQL parameters: {tuple(params)}")

            cursor.execute(sql, tuple(params))
            connection.commit()
            print(f"DEBUG: Database update completed. Rows affected: {cursor.rowcount}")

            if cursor.rowcount == 0:
                print("DEBUG: Project data is already up to date or no changes were made, returning 200.")
                return jsonify({'message': 'Project data is already up to date or no changes were made.'}), 200

        return jsonify({'message': 'Project successfully updated!'}), 200

    except pymysql.Error as e:
        print(f"DATABASE ERROR (update_project): {e}")
        return jsonify({'message': f'Database error occurred: {e.args[1]}'}), 500
    except Exception as e:
        print(f"GENERAL ERROR (update_project): {e}")
        return jsonify({'message': 'Server error, please try again later.'}), 500
    finally:
        if connection:
            connection.close()
            print("DEBUG: Database connection closed.")

# Project Delete API (DELETE)
@app.route('/api/projects/<int:project_id>', methods=['DELETE'])
def delete_project_api(project_id):
    """Deletes a project from the database."""
    data = request.get_json() # Get user_id from DELETE request body
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({'message': 'User ID is missing.'}), 400

    project_name = "Unknown Project" # Default value for logging
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
                project_manager_id,
                "Project Deleted",
                f"The project '{project_name}' you managed has been deleted." # Message updated
            )

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
        if connection:
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
@app.route('/api/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    """Retrieves various statistics for the dashboard."""
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(project_id) AS count FROM projects WHERE status IN ('Active', 'Active (Work Delayed)')")
            active_projects = cursor.fetchone()['count']

            cursor.execute("SELECT COUNT(project_id) AS count FROM projects WHERE status = 'Completed'")
            completed_projects = cursor.fetchone()['count']

            cursor.execute("SELECT COUNT(project_id) AS count FROM projects WHERE status IN ('Delayed', 'Active (Work Delayed)')")
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
        print(f"Database error while fetching statistics: {e}")
        return jsonify({'message': f'Database error occurred: {e.args[1]}'}), 500
    except Exception as e:
        print(f"General error while fetching statistics: {e}")
        return jsonify({'message': 'Server error, please try again later.'}), 500
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
    status = data.get('status', 'In Planning Phase') # Default status if not provided

    user_id = data.get('user_id') # User ID who added the project (for activity log)

    if not all([project_name, customer_id, project_manager_id, start_date_str, end_date_str]): # Date checks added
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
            connection.commit()
            new_project_id = cursor.lastrowid

            # Process and add project progress steps
            progress_steps = data.get('progressSteps', [])
            last_step_end_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date() # Start with project start date

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
                # Calculate delay based on the end date of the previous step or the project's start date
                if last_step_end_date:
                    time_diff = (new_step_start_date - last_step_end_date).days
                    if time_diff > 1: # If there is a gap of more than 1 day, a delay has occurred
                        delay_days = time_diff - 1

                sql_insert_progress = """
                INSERT INTO project_progress (project_id, title, description, start_date, end_date, delay_days)
                VALUES (%s, %s, %s, %s, %s, %s)
                """
                cursor.execute(sql_insert_progress, (new_project_id, step_title, step_description, step_start_date_str, step_end_date_str, delay_days))
                connection.commit() # Commit each step or commit once after the loop

                last_step_end_date = step_end_date # Update last_step_end_date for the next iteration

            # Send notification to project manager
            if project_manager_id: # project_manager_id is not in project_info, it should be fetched from projects table
                send_notification(
                    project_manager_id,
                    "New Project Assigned",
                    f"A new project has been assigned to you: '{project_name}'."
                )

        activity_data = {
            'user_id': user_id,
            'title': 'New Project Added',
            'description': f'New project named "{project_name}" created.',
            'icon': 'fas fa-plus'
        }
        # Call add_activity API
        return jsonify({"message": "Project successfully added", "projectId": new_project_id}), 201
    except pymysql.Error as e:
        print(f"Database error while adding project: {e}")
        return jsonify({'message': f'Database error occurred: {e.args[1]}'}), 500
    except Exception as e:
        print(f"General error while adding project: {e}")
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
        print(f"Database error while fetching progress steps: {e}")
        return jsonify({'message': f'Database error occurred: {e.args[1]}'}), 500
    except Exception as e:
        print(f"General error while fetching progress steps: {e}")
        return jsonify({'message': 'Server error, please try again later.'}), 500
    finally:
        if connection:
            connection.close()
@app.route('/api/projects/<int:project_id>/progress', methods=['POST'])
def add_project_progress_step_from_modal(project_id):
    """Adds a new progress step to a project."""
    data = request.get_json()
    step_name = data.get('step_name')
    description = data.get('description')
    start_date_str = data.get('start_date')
    end_date_str = data.get('end_date')
    user_id = session.get('user_id') # Get user ID from session

    if not all([project_id, step_name, start_date_str, end_date_str, user_id]):
        return jsonify({'message': 'Project ID, title, start, end date, and user ID are required.'}), 400

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Get project name
            cursor.execute("SELECT project_name, project_manager_id FROM projects WHERE project_id = %s", (project_id,))
            project_info = cursor.fetchone()
            project_name = project_info['project_name'] if project_info else f"ID: {project_id}"
            project_manager_id = project_info['project_manager_id'] if project_info else None


            # Find the existing end date of the project (to calculate delay days)
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

            sql_insert = """
            INSERT INTO project_progress (project_id, title, description, start_date, end_date, delay_days)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            # new_project_id yerine project_id kullanıldı
            cursor.execute(sql_insert, (project_id, step_name, description, start_date_str, end_date_str, delay_days))
            new_progress_id = cursor.lastrowid
            connection.commit()

            # Send notification to project manager
            if project_manager_id:
                send_notification(
                    project_manager_id,
                    "Project Progress Step Added",
                    f"A new work step named '{step_name}' has been added to the project '{project_name}' you managed." # Message updated
                )

            activity_data = {
                'user_id': user_id,
                'title': 'Work Step Added',
                'description': f"A new work step named '{step_name}' has been added to the project '{project_name}'.",
                'icon': 'fas fa-plus-circle'
            }
            # Call add_activity API

        return jsonify({'message': 'Progress step successfully added!', 'progress_id': new_progress_id}), 201
    except pymysql.Error as e:
        print(f"Database error while adding progress step: {e}")
        return jsonify({'message': f'Database error occurred: {e.args[1]}'}), 500
    except Exception as e:
        print(f"General error while adding progress step: {e}")
        return jsonify({'message': 'Server error, please try again later.'}), 500
    finally:
        if connection:
            connection.close()

# API to update project progress step
@app.route('/api/progress/<int:progress_id>', methods=['PUT'])
def update_project_progress_step(progress_id):
    """Updates an existing project progress step."""
    data = request.get_json()
    step_name = data.get('step_name')
    description = data.get('description')
    start_date_str = data.get('start_date')
    end_date_str = data.get('end_date')
    user_id = session.get('user_id') # Get user ID from session

    if not all([step_name, start_date_str, end_date_str, user_id]):
        return jsonify({'message': 'Title, start, end date, and user ID are required.'}), 400

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Get the project ID and title of the existing progress step
            cursor.execute("SELECT project_id, title FROM project_progress WHERE progress_id = %s", (progress_id,))
            existing_step = cursor.fetchone()
            if not existing_step:
                return jsonify({'message': 'Progress step not found.'}), 404

            current_project_id = existing_step['project_id']
            old_step_name = existing_step['title'] # Get old step name

            # Get project name and manager
            cursor.execute("SELECT project_name, project_manager_id FROM projects WHERE project_id = %s", (current_project_id,))
            project_info = cursor.fetchone()
            project_name = project_info['project_name'] if project_info else f"ID: {current_project_id}"
            project_manager_id = project_info['project_manager_id'] if project_info else None


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
                return jsonify({'message': 'Progress step data is already up to date or no changes were made.'}), 200

            # Send notification to project manager
            if project_manager_id:
                send_notification(
                    project_manager_id,
                    "Project Progress Step Updated",
                    f"The work step '{step_name}' in the project '{project_name}' you managed has been updated." # Message updated
                )

            activity_data = {
                'user_id': user_id,
                'title': 'Work Step Updated',
                'description': f"The work step '{old_step_name}' in project '{project_name}' has been updated to '{step_name}'.",
                'icon': 'fas fa-edit'
            }
            # Call add_activity API

        return jsonify({'message': 'Progress step successfully updated!'}), 200
    except pymysql.Error as e:
        print(f"Database error while updating progress step: {e}")
        return jsonify({'message': f'Database error occurred: {e.args[1]}'}), 500
    except Exception as e:
        print(f"General error while updating progress step: {e}")
        return jsonify({'message': 'Server error, please try again later.'}), 500
    finally:
        if connection:
            connection.close()

# API to delete project progress step
@app.route('/api/progress/<int:progress_id>', methods=['DELETE'])
def delete_project_progress_step(progress_id):
    """Deletes a project progress step."""
    user_id = session.get('user_id') # Get user ID from session

    if not user_id:
        return jsonify({'message': 'User ID is missing.'}), 400

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Get project ID and title of the step to be deleted
            cursor.execute("SELECT project_id, title FROM project_progress WHERE progress_id = %s", (progress_id,))
            step_info = cursor.fetchone()
            if not step_info:
                return jsonify({'message': 'Progress step could not be deleted or not found.'}), 404

            current_project_id = step_info['project_id']
            step_name = step_info['title']

            # Get project name and manager
            cursor.execute("SELECT project_name, project_manager_id FROM projects WHERE project_id = %s", (current_project_id,))
            project_info = cursor.fetchone()
            project_name = project_info['project_name'] if project_info else f"ID: {current_project_id}"
            project_manager_id = project_info['project_manager_id'] if project_info else None

            sql = "DELETE FROM project_progress WHERE progress_id = %s"
            cursor.execute(sql, (progress_id,))
            connection.commit()

            if cursor.rowcount == 0:
                return jsonify({'message': 'Progress step could not be deleted or not found.'}), 404

            # Send notification to project manager
            if project_manager_id:
                send_notification(
                    project_manager_id,
                    "Project Progress Step Deleted",
                    f"The work step '{step_name}' in the project '{project_name}' you managed has been deleted." # Message updated
                )

            activity_data = {
                'user_id': user_id,
                'title': 'Work Step Deleted',
                'description': f"The work step '{step_name}' in project '{project_name}' has been deleted.",
                'icon': 'fas fa-trash-alt'
            }
            # Call add_activity API

        return jsonify({'message': 'Progress step successfully deleted!'}), 200
    except pymysql.Error as e:
        print(f"Database error while deleting progress step: {e}")
        return jsonify({'message': f'Database error occurred: {e.args[1]}'}), 500
    except Exception as e:
        print(f"General error while deleting progress step: {e}")
        return jsonify({'message': 'Server error, please try again later.'}), 500
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

@app.route('/ayarlar')
def ayarlar_page():
    """Renders the settings page."""
    return render_template('ayarlar.html')

@app.route('/api/roles', methods=['GET'])
def get_distinct_roles():
    """Retrieves distinct roles from the users table (excluding 'Admin')."""
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            sql = "SELECT DISTINCT role FROM users WHERE role != 'Admin'"
            cursor.execute(sql)
            roles = [row['role'] for row in cursor.fetchall()]

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
                color = "#2ed573" # Low priority
                if task['priority'] == "high":
                    color = "#ff4757"
                elif task['priority'] == "medium":
                    color = "#ffa502"

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
                # Color assignment based on project status
                project_color = "#005c9d" # Default
                if "Delayed" in project['status']:
                    project_color = "#ff4757" # Red
                elif project['status'] == 'Completed':
                    project_color = "#2ed573" # Green
                elif project['status'] == 'Active':
                    project_color = "#0980d3" # Blue

                events.append({
                    'id': f"project-{project['project_id']}", # Add type to ID
                    'title': f"Project: {project['project_name']}",
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

            # Send notification to the newly assigned user
            send_notification(
                assigned_user_id,
                "New Task Assigned",
                f"A new task has been assigned to you: '{title}'."
            )

        return jsonify({'message': 'Task successfully added!'}), 201
    except Exception as e:
        print(f"Error adding task: {e}")
        return jsonify({'message': 'Error adding task.'}), 500
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

            cursor.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
            connection.commit()

            # Send notification to the assigned user (if different from deleter)
            if user_id != task_info['assigned_user_id']:
                send_notification(
                    task_info['assigned_user_id'],
                    "Task Deleted",
                    f"The task '{task_info['title']}' assigned to you has been deleted."
                )
            # If the creator is different from assigned user and deleter, notify creator too
            if user_id != task_info['created_by'] and task_info['created_by'] != task_info['assigned_user_id']:
                 send_notification(
                    task_info['created_by'],
                    "Task Deleted",
                    f"The task '{task_info['title']}' you created has been deleted."
                )


        return jsonify({'message': 'Task successfully deleted!'}), 200
    except Exception as e:
        print(f"Error deleting task: {e}")
        return jsonify({'message': 'Error deleting task.'}), 500
    finally:
        if connection:
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
    """Retrieves performance metrics for employees (project managers)."""
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = """
            SELECT
                u.fullname AS manager_name,
                COUNT(DISTINCT p.project_id) AS total_projects,
                SUM(CASE
                        WHEN p.status = 'Completed' AND (\
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
            WHERE u.role IN ('Teknisyen', 'Tekniker', 'Mühendis', 'Müdür', 'Proje Yöneticisi')
            GROUP BY u.fullname
            """
            cursor.execute(sql)
            result = cursor.fetchall()
            return jsonify(result)
    finally:
        if connection:
            connection.close()

##if __name__ == '__main__':
  ##  app.run(host='0.0.0.0', port=3001, debug=True)
