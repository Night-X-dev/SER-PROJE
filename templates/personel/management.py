from flask import Flask, render_template

app = Flask(__name__)

@app.route("/personel")
def personel_index():
    return render_template("personel/index.html")

if __name__ == "__main__":
    app.run()
