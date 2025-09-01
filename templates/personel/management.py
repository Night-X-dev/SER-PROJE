from flask import Flask, render_template, request

app = Flask(__name__)

@app.route("/personel")
def personel_index():
    return render_template("personel/index.html")

# Test route
@app.route("/test_backend", methods=["GET", "POST"])
def test_backend():
    if request.method == "POST":
        data = request.form.get("test_input")
        return f"Backend aldım: {data}"
    return '''
        <form method="post">
            <input name="test_input" placeholder="Bir şey yaz">
            <button type="submit">Gönder</button>
        </form>
    '''

if __name__ == "__main__":
    app.run()
