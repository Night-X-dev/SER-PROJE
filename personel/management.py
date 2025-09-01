# Gerekli Flask modüllerini import ediyoruz
from flask import Flask, render_template, request, url_for, redirect

# Flask uygulamasını oluşturuyoruz.
# templates_folder parametresi, bu uygulama için şablonların hangi klasörde olduğunu belirtir.
# static_folder parametresi, statik dosyaların hangi klasörde olduğunu belirtir.
app = Flask(__name__, template_folder="templates/personel", static_folder="templates/personel/static")

# Giriş sayfasını gösteren rota.
# Bu rota, ana URL'ye (`/`) gelen istekleri karşılar ve `login.html` dosyasını render eder.
@app.route("/")
def login_page():
    # 'personel/login.html' yerine sadece 'login.html' dosyasını render eder.
    return render_template("login.html")

# Formdan gelen verileri işleyen rota.
# Sadece POST metodu ile erişime izin verir.
@app.route("/login_backend", methods=["POST"])
def login_backend():
    # POST isteği ile gönderilen form verilerini alır.
    email = request.form.get("email")
    password = request.form.get("password")

    # TEST amaçlı kullanıcı doğrulama
    # Kullanıcının istediği spesifik email ve şifre ile kontrol ediyoruz.
    if email == "12345678@gmail.com" and password == "12345678":
        # Doğru bilgiler girildiğinde
        return "Giriş başarılı!"
    else:
        # Yanlış bilgiler girildiğinde
        return "Giriş başarısız, lütfen bilgilerinizi kontrol edin."

# Bu kısım, dosya doğrudan çalıştırıldığında uygulamanın başlamasını sağlar.
if __name__ == "__main__":
    # Uygulamayı debug modunda çalıştırır.
    # 'debug=True' ile kodda yaptığınız değişiklikler otomatik olarak yeniden yüklenir.
    app.run(debug=True)
