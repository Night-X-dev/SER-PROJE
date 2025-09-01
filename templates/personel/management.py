from flask import Flask, render_template, request

app = Flask(__name__)

@app.route("/login_backend", methods=["POST"])
def login_backend():
    email = request.form.get("email")
    password = request.form.get("password")
    # Şimdi bu veriyi test edebiliriz
    return f"Gelen veriler: Email: {email}, Password: {password}"

@app.route("/")
def login_page():
    return render_template("login.html")
