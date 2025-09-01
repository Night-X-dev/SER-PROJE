from flask import Blueprint, render_template, redirect, url_for, session, flash, request, jsonify
import pymysql.cursors
import os
from dotenv import load_dotenv
from functools import wraps

# Load environment variables
load_dotenv()

# Create Blueprint
management_bp = Blueprint(
    'management',
    __name__,
    template_folder='templates/personel',
    static_folder='static',
    static_url_path='/personel/static',
    url_prefix='/personel'
)

# Database connection
def get_db_connection():
    return pymysql.connect(
        host=os.getenv("MYSQL_HOST_NEW", "localhost"),
        user=os.getenv("MYSQL_USER_NEW", "serik"),
        password=os.getenv("MYSQL_PASSWORD_NEW", "Ser.1712_"),
        database=os.getenv("MYSQL_DATABASE_NEW", "ser_ik"),
        port=int(os.getenv("MYSQL_PORT_NEW", 3306)),
        cursorclass=pymysql.cursors.DictCursor
    )

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'personel_logged_in' not in session:
            return redirect(url_for('management.login'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@management_bp.route('/')
def index():
    if 'personel_logged_in' in session:
        return redirect(url_for('management.dashboard'))
    return redirect(url_for('management.login'))

@management_bp.route('/login', methods=['GET', 'POST'])
@management_bp.route('/login.html', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            # Get form data
            data = request.get_json() if request.is_json else request.form
            email = data.get('email')
            password = data.get('password')
            
            # Debug log
            print(f"Login attempt - Email: {email}")
            
            # Simple authentication (replace with database check in production)
            if email == "admin@example.com" and password == "admin123":
                session['personel_logged_in'] = True
                session['personel_email'] = email
                
                # Return JSON response for AJAX requests
                if request.is_json:
                    return jsonify({
                        "success": True, 
                        "redirect": url_for('management.dashboard', _external=True)
                    })
                # Redirect for form submissions
                return redirect(url_for('management.dashboard'))
            else:
                error_msg = "Geçersiz e-posta veya şifre!"
                if request.is_json:
                    return jsonify({"success": False, "message": error_msg}), 401
                flash(error_msg, 'error')
                
        except Exception as e:
            error_msg = f"Bir hata oluştu: {str(e)}"
            print(error_msg)
            if request.is_json:
                return jsonify({"success": False, "message": error_msg}), 500
            flash(error_msg, 'error')
    
    # For GET request, render the login page
    return render_template('personel/login.html')

@management_bp.route('/logout')
def logout():
    session.pop('personel_logged_in', None)
    session.pop('personel_email', None)
    return redirect(url_for('management.login'))

@management_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('personel/dashboard.html')

@management_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # TODO: Implement password change logic
        if new_password == confirm_password:
            flash('Şifre başarıyla değiştirildi!', 'success')
            return redirect(url_for('management.dashboard'))
        else:
            flash('Yeni şifreler eşleşmiyor!', 'danger')
    
    return render_template('change_password.html')

# API Endpoints
@management_bp.route('/api/test-db')
def test_db():
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SHOW TABLES;")
            tables = cursor.fetchall()
        return jsonify({"status": "success", "tables": tables})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        if 'conn' in locals():
            conn.close()
