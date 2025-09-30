from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, abort, session
import os, sqlite3, string, random
# .env dosyasını yükle
load_dotenv()

db_path = os.path.join("/tmp", "urls.db")

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "supersecretkey")  # .env'den al

def generate_short_code(length=6):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

# Veritabanı oluştur
conn = sqlite3.connect(db_path)
c = conn.cursor()
c.execute("""
    CREATE TABLE IF NOT EXISTS urls (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        long_url TEXT NOT NULL,
        short_code TEXT UNIQUE NOT NULL
    )
""")
conn.commit()
conn.close()

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        long_url = request.form["long_url"]

        conn = sqlite3.connect(DATABASE_URL)
        c = conn.cursor()

        # Yeni short code üret
        short_code = generate_short_code()

        c.execute("INSERT INTO urls (long_url, short_code) VALUES (?, ?)",
                  (long_url, short_code))
        conn.commit()
        conn.close()

        # Short URL'yi session ile sakla
        session["short_url"] = request.host_url + short_code

        # Redirect ile result sayfasına gönder
        return redirect("/result")

    return render_template("index.html")


@app.route("/result")
def result():
    if "short_url" not in session:
        return redirect("/")

    short_url = session.pop("short_url")  # Tek kullanımlık
    return render_template("result.html", short_url=short_url)


@app.route("/<short_code>")
def redirect_to_url(short_code):
    conn = sqlite3.connect(DATABASE_URL)
    c = conn.cursor()
    c.execute("SELECT long_url FROM urls WHERE short_code = ?", (short_code,))
    row = c.fetchone()
    conn.close()

    if row:
        return redirect(row[0])
    else:
        abort(404)


@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404


if __name__ == "__main__":
    # Debug kapalı, local test için
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)), debug=False)
