# management.py
from flask import Blueprint, request

# Blueprint oluşturuyoruz
management_bp = Blueprint('management', __name__)

@management_bp.route("/login_backend", methods=["POST"])
def login_backend():
    email = request.form.get("email")
    password = request.form.get("password")

    if email == "12345678@gmail.com" and password == "12345678":
        return "Giriş başarılı!"
    else:
        return "Giriş başarısız, lütfen bilgilerinizi kontrol edin."
