# management.py
import os
import pymysql.cursors
from dotenv import load_dotenv
from flask import Blueprint, request, jsonify, render_template


load_dotenv()

# Blueprint oluştur
management_bp = Blueprint(
    'management',
    __name__,
    template_folder='templates/personel',
    static_folder='static',  # sadece 'static' yaz
    static_url_path='/personel/static'  # URL’de bu path kullanılacak
)
# Yeni veritabanı bağlantısı
def get_db_connection():
    connection = pymysql.connect(
        host=os.getenv("MYSQL_HOST_NEW", "localhost"),
        user=os.getenv("MYSQL_USER_NEW", "serik"),
        password=os.getenv("MYSQL_PASSWORD_NEW", "Ser.1712_"),
        database=os.getenv("MYSQL_DATABASE_NEW", "ser_ik"),
        port=int(os.getenv("MYSQL_PORT_NEW", 3306)),
        cursorclass=pymysql.cursors.DictCursor
    )
    return connection
management_bp = Blueprint(
    'management',
    __name__,
    template_folder='templates/personel',  # blueprint templates path
    static_folder='static',
    static_url_path='/personel/static'
)
@management_bp.route('/login.html')
def serve_personel_login_page():
    return render_template('login.html')  # sadece 'login.html', çünkü blueprint template_folder zaten 'templates/personel'
@management_bp.route("/login_backend", methods=["POST"])
def login_backend():
    email = request.form.get("email")
    password = request.form.get("password")

    if email == "12345678@gmail.com" and password == "12345678":
        return "Giriş başarılı!"
    else:
        return "Giriş başarısız, lütfen bilgilerinizi kontrol edin."

@management_bp.route('/test_db')
def test_db():
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SHOW TABLES;")
        tables = cursor.fetchall()
    conn.close()
    return jsonify(tables)
