import os
import psycopg2
from flask import Flask, render_template, request, session, redirect, url_for
from openai import OpenAI

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "opti_ultra_premium_2026")
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# DATABASE CONNECTION
DB_URL = os.environ.get("DATABASE_URL")

def get_db_connection():
    # Use a timeout so it doesn't spin forever on a white screen
    return psycopg2.connect(DB_URL, connect_timeout=10)

def init_db():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS license_claims (
                license_key TEXT PRIMARY KEY,
                user_ip TEXT
            )
        ''')
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"DB INIT ERROR: {e}")

if DB_URL:
    init_db()

# MASTER KEYS (Make sure these are EXACTLY what you type)
VALID_KEYS = ["OPTI-1234", "OPTI-5678", "VIP-ACCESS", "OPTI-2026-X"]

@app.route('/')
def login():
    # If already logged in, skip the login screen
    if "user_key" in session:
        return redirect(url_for('opti_chat'))
    return render_template('login.html')

@app.route('/opti', methods=['POST'])
def handle_login():
    # Force uppercase and remove spaces to prevent "Invalid Key" errors
    user_key = request.form.get('license_id', '').strip().upper()
    user_ip = request.remote_addr

    if user_key not in VALID_KEYS:
        return f"Invalid License Key: {user_key}. Please go back and try again."

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT user_ip FROM license_claims WHERE license_key = %s", (user_key,))
        result = cur.fetchone()

        if result:
            # Check if this key is already locked to another IP
            if result[0] != user_ip:
                cur.close()
                conn.close()
                return "ACCESS DENIED: Key locked to another device."
        else:
            # Lock the key to this IP for the first time
            cur.execute("INSERT INTO license_claims (license_key, user_ip) VALUES (%s, %s)", (user_key, user_ip))
            conn.commit()
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"DB ACCESS ERROR: {e}")
        # If the DB fails, we allow login as a fallback so the site works
    
    session["user_key"] = user_key
    session["history"] = [{"role": "assistant", "content": "System Initialized. I am Opti AI. Please provide your Specs (CPU, GPU, RAM) to begin."}]
    return redirect(url_for('opti_chat'))

@app.route('/dashboard')
def opti_chat():
    if "user_key" not in session:
        return redirect(url_for('login'))
    return render_template('index.html', user_id=session["user_key"], initial_msg=session["history"][0]["content"])

@app.route('/ask', methods=['POST'])
def ask_ai():
    if "user_key" not in session: return "Unauthorized", 401
    user_query = request.form.get('query')
    history = session.get("history", [])
    
    system_msg = {"role": "system", "content": "You are Opti AI. Use bullet points. End with [EFF: X] [RSK: Y]."}
    history.append({"role": "user", "content": user_query})

    try:
        response = client.chat.completions.create(model="gpt-4o", messages=[system_msg] + history[-6:])
        ai_msg = response.choices[0].message.content
        history.append({"role": "assistant", "content": ai_msg})
        session["history"] = history
        return ai_msg
    except Exception as e:
        return f"AI Error: {str(e)}"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
