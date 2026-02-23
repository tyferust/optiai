import os
import psycopg2
from flask import Flask, render_template, request, session, redirect, url_for
from openai import OpenAI

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "opti_elite_2026")
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# 1. DATABASE SETUP (Postgres)
DB_URL = os.environ.get("DATABASE_URL")

def get_db_connection():
    return psycopg2.connect(DB_URL)

def init_db():
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

init_db()

VALID_KEYS = ["OPTI-1234", "OPTI-5678", "VIP-ACCESS"]

# 2. ROUTES

@app.route('/')
def login():
    if "user_key" in session:
        return redirect(url_for('opti_chat'))
    return render_template('login.html')

@app.route('/opti', methods=['POST'])
def handle_login():
    user_key = request.form.get('license_id')
    user_ip = request.remote_addr

    if user_key not in VALID_KEYS:
        return "Invalid License Key."

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT user_ip FROM license_claims WHERE license_key = %s", (user_key,))
    result = cur.fetchone()

    if result:
        if result[0] != user_ip:
            cur.close()
            conn.close()
            return "ACCESS DENIED: This key is locked to another device."
    else:
        cur.execute("INSERT INTO license_claims (license_key, user_ip) VALUES (%s, %s)", (user_key, user_ip))
        conn.commit()
    
    cur.close()
    conn.close()
    session["user_key"] = user_key
    # Start the conversation by having the AI ask for specs
    session["history"] = [{"role": "assistant", "content": "System Initialized. I am Opti AI. Before we begin optimization, please provide your Specs (CPU, GPU, RAM) and your Platform (Windows 10/11, Console, etc.)."}]
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
    
    # SYSTEM PROMPT: Forces AI to use platform-specific advanced techniques
    system_msg = {
        "role": "system", 
        "content": """You are Opti AI, the world's most advanced PC performance architect. 
        INSTRUCTIONS:
        1. If the user hasn't provided specs yet, keep asking for them.
        2. Once specs are provided, use ELITE techniques (NVIDIA Profile Inspector, Registry Debloating, FilterKeys Setter, BIOS tweaks).
        3. Be extremely platform-specific (e.g., if they are on Windows 11, suggest 'Efficiency Mode' tweaks).
        4. Use neat spacing and bullet points. No hashtags."""
    }

    # Add user message to history
    history.append({"role": "user", "content": user_query})

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[system_msg] + history[-5:] # Sends the last 5 messages for memory
        )
        ai_msg = response.choices[0].message.content
        
        # Save response to history
        history.append({"role": "assistant", "content": ai_msg})
        session["history"] = history
        
        return ai_msg
    except Exception as e:
        return f"AI Error: {str(e)}"

@app.route('/admin-panel-99')
def admin_list():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM license_claims;")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return f"<h2>Claims:</h2>{str(rows)}"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
