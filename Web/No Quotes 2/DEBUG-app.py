import os
import time
import pymysql
from flask import Flask, redirect, render_template, render_template_string, request, session, url_for

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MYSQL_HOST = "127.0.0.1"
MYSQL_PORT = 3306
MYSQL_USER = "ctf"
MYSQL_PASSWORD = "ctf"
MYSQL_DATABASE = "ctf"

app = Flask(__name__)
app.secret_key = os.urandom(24)


def get_db_connection():
    return pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE,
        autocommit=True,
    )


def ensure_db() -> None:
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(255) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL
                )
                """
            )
            cur.execute("SELECT 1 FROM users WHERE username = %s", ("test",))
            exists = cur.fetchone()
            if not exists:
                cur.execute(
                    "INSERT INTO users (username, password) VALUES (%s, %s)",
                    ("test", "test"),
                )
    finally:
        conn.close()

def waf(value: str) -> bool:
    blacklist = ["'", '"']
    # debug added
    print(f"[DEBUG] WAF input: {repr(value)}", flush=True)
    return any(char in value for char in blacklist)


@app.get("/")
def index():
    return render_template("login.html")


@app.post("/login")
def login():
    # DEBUG ONLY - added these lines
    print("\n" + "="*80, flush=True)
    print("[DEBUG LOGIN] Starting login process", flush=True)

    username = request.form.get("username", "")
    password = request.form.get("password", "")

    # DEBUG ONLY
    print(f"[DEBUG LOGIN] Raw username: {repr(username)}", flush=True)
    print(f"[DEBUG LOGIN] Raw password: {repr(password)}", flush=True)

    if waf(username) or waf(password):
        # DEBUG ONLY
        print("[DEBUG LOGIN] Blocked by WAF", flush=True)
        return render_template(
            "login.html",
            error="No quotes allowed!",
            username=username,
        )
    query = (
        "SELECT username, password FROM users "
        f"WHERE username = ('{username}') AND password = ('{password}')"
    )
    # DEBUG ONLY
    print(f"[DEBUG LOGIN] SQL Query: {query}", flush=True)
    print(f"[DEBUG LOGIN] Query repr: {repr(query)}", flush=True)
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            # DEBUG ONLY
            print("[DEBUG LOGIN] Executing query...", flush=True)
            cur.execute(query)
            row = cur.fetchone()
            # DEBUG ONLY
            print(f"[DEBUG LOGIN] Query result: {row}", flush=True)
            if row:
                print(f"[DEBUG LOGIN] Row[0]: {repr(row[0])}", flush=True)
                print(f"[DEBUG LOGIN] Row[1]: {repr(row[1])}", flush=True)
    except pymysql.MySQLError as e:
        # DEBUG ONLY
        print(f"[DEBUG LOGIN] MySQL Error: {e}", flush=True)
        return render_template(
            "login.html",
            error=f"Invalid credentials.",
            username=username,
        )
    finally:
        try:
            conn.close()
        except Exception:
            pass

    if not row:
        # DEBUG ONLY
        print("[DEBUG LOGIN] No rows returned", flush=True)
        return render_template(
            "login.html",
            error="Invalid credentials.",
            username=username,
        )
    # DEBUG ONLY
    print(f"[DEBUG LOGIN] Checking: username '{repr(username)}' == row[0] '{repr(row[0])}'", flush=True)
    print(f"[DEBUG LOGIN] Checking: password '{repr(password)}' == row[1] '{repr(row[1])}'", flush=True)

    if not username == row[0] or not password == row[1]:
        # DEBUG ONLY
        print("[DEBUG LOGIN] Username/password don't match", flush=True)
        return render_template(
            "login.html",
            error="Invalid credentials.",
            username=username,
        )
    # DEBUG ONLY
    print(f"[DEBUG LOGIN] Login successful! Session user: {row[0]}", flush=True)
    session["user"] = row[0]

    # DEBUG ONLY
    print("="*80 + "\n", flush=True)
    return redirect(url_for("home"))


@app.get("/home")
def home():
    # DEBUG ONLY
    print("\n[DEBUG HOME] Accessing home page", flush=True)
    if not session.get("user"):
        # DEBUG ONLY
        print("[DEBUG HOME] No user in session", flush=True)
        return redirect(url_for("index"))

    # DEBUG ONLY
    print(f"[DEBUG HOME] User in session: {repr(session.get('user'))}", flush=True)

    return render_template_string(open("templates/home.html").read() % session["user"])


@app.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


if __name__ == "__main__":
    ensure_db()
    app.run(host="0.0.0.0", port=5000, debug=False)
