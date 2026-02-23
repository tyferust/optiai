import os
import sqlite3
from flask import Flask, render_template, request, session, redirect, url_for
from openai import OpenAI

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "ultra_secure_opti_2026")
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

DATABASE = 'optiai.db'

# --- DATABASE SETUP ---
def init_db():
    """Creates the database table if it doesn't exist yet."""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    # This table stores the Key and the IP address that first used it
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS license_claims (
            license_key TEXT PRIMARY KEY,
            user_ip TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Run the database setup immediately
init_db()

# --- THE LOGIC ---
VALID_KEYS = ["OPTI-1234", "OPTI-5678", "VIP-ACCESS"]

@app.route('/')
def login():
    if "user_key" in session:
        return redirect(url_for('opti_chat'))
    return render_template('login.html')

@app.route('/opti', methods=['POST'])
def handle_login():
    user_key = request.form.get('license_id')
    user_ip = request.remote_addr # Tracks their specific device

    if user_key not in VALID_KEYS:
        return "Invalid License Key."

    # Check the database to see if someone already claimed this key
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT user_ip FROM license_claims WHERE license_key = ?", (user_key,))
    result = cursor.fetchone()

    if result:
        # Key has been used before. Is it the same person?
        if result[0] != user_ip:
            conn.close()
            return "ACCESS DENIED: This key is already locked to another device."
    else:
        # First time this key is used! Lock it to this IP.
        cursor.execute("INSERT INTO license_claims (license_key, user_ip) VALUES (?, ?)", (user_key, user_ip))
        conn.commit()
    
    conn.close()
    session["user_key"] = user_key
    return redirect(url_for('opti_chat'))

@app.route('/dashboard')
def opti_chat():
    if "user_key" not in session:
        return redirect(url_for('login'))
    return render_template('index.html', user_id=session["user_key"])

@app.route('/ask', methods=['POST'])
def ask_ai():
    if "user_key" not in session: return "Unauthorized", 401
    user_query = request.form.get('query')
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are Opti AI. Respond in clean, plain text. No hashtags. Neat spacing only."},
                {"role": "user", "content": user_query}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI Error: {str(e)}"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
