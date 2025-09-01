from flask import Flask, render_template, request

app = Flask(__name__)

@app.route("/login_backend", methods=["POST"])
def login_backend():
    email = request.form.get("email")
    password = request.form.get("password")
    return f"Gelen veriler: Email: {email}, Password: {password}"

@app.route("/")
def login_page():
    return render_template("personel/login.html")

if __name__ == "__main__":
    app.run(debug=True)
