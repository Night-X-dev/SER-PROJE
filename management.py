# management.py
from flask import Blueprint, request
import pymysql
import os
import urllib.parse

# Blueprint oluşturuyoruz
management_bp = Blueprint('management', __name__)

def get_db_connection():
    """Yeni veritabanına bağlanmak için fonksiyon"""
    connection = None
    try:
        # Ortam değişkenlerinden bağlantı bilgilerini al
        host = os.getenv("MYSQL_HOST", "localhost")
        port = int(os.getenv("MYSQL_PORT", 3306))
        user = os.getenv("MYSQL_USER", "ser")
        password = os.getenv("MYSQL_PASSWORD", "Ser.1712_")
        database = os.getenv("MYSQL_DATABASE", "yeni_veritabani")

        connection = pymysql.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            port=port,
            cursorclass=pymysql.cursors.DictCursor
        )
        return connection
    except Exception as e:
        print(f"DB connection error: {e}")
        if connection:
            connection.close()
        raise

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
    return {"tables": tables}