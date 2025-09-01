from flask import Flask, render_template, request, url_for

# Flask uygulamasını oluşturuyoruz.
# templates_folder ve static_folder parametreleri, Flask'a bu klasörlerin nerede olduğunu söyler.
# Burada Flask'ın kendisini başlattığı klasöre göre ayar yapıyoruz.
app = Flask(__name__, template_folder='templates/personel', static_folder='templates/personel/static')

# Ana sayfayı gösteren rota.
# Bu rota, ana URL'ye (`/`) gelen istekleri karşılar ve 'login.html' dosyasını gönderir.
@app.route("/")
def login_page():
    return render_template("login.html")

# Formdan gelen verileri işleyen rota.
# Sadece POST metodu ile erişime izin verir.
@app.route("/login_backend", methods=["POST"])
def login_backend():
    email = request.form.get("email")
    password = request.form.get("password")

    # Doğru kullanıcı adı ve şifreyi kontrol et
    if email == "12345678@gmail.com" and password == "12345678":
        return "Giriş başarılı!"
    else:
        return "Giriş başarısız, lütfen bilgilerinizi kontrol edin."

if __name__ == "__main__":
    app.run(debug=True)
