import os
import psycopg2
from flask import Flask, render_template, request, session, redirect, url_for
from openai import OpenAI

app = Flask(__name__)
# Security: Use an environment variable for the secret key in production
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "opti_ultra_premium_2026")
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# --- DATABASE SETUP ---
DB_URL = os.environ.get("DATABASE_URL")

def get_db_connection():
    # connect_timeout prevents the "infinite loading" if the DB is slow
    return psycopg2.connect(DB_URL, connect_timeout=5)

def init_db():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        # Creates the table to lock keys to specific IP addresses
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
        print(f"DATABASE INITIALIZATION ERROR: {e}")

# Initialize the DB on startup
if DB_URL:
    init_db()

# --- ACCESS CONTROL ---
# Updated with your new Master Key
VALID_KEYS = ["OPTI-1234", "OPTI-5678", "VIP-ACCESS", "OPTI-2026-X"]

@app.route('/')
def login():
    if "user_key" in session:
        return redirect(url_for('opti_chat'))
    return render_template('login.html')

@app.route('/opti', methods=['POST'])
def handle_login():
    user_key = request.form.get('license_id')
    user_ip = request.remote_addr # Captures user's IP for the lock

    if user_key not in VALID_KEYS:
        return "Invalid License Key. Access Denied."

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT user_ip FROM license_claims WHERE license_key = %s", (user_key,))
        result = cur.fetchone()

        if result:
            # If the key is already in the DB, check if the IP matches
            if result[0] != user_ip:
                cur.close()
                conn.close()
                return "ACCESS DENIED: This key is already locked to another device."
        else:
            # If it's a new key, lock it to this IP
            cur.execute("INSERT INTO license_claims (license_key, user_ip) VALUES (%s, %s)", (user_key, user_ip))
            conn.commit()
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Database login error: {e}")
        # If DB fails, we still allow login for now so the site doesn't crash
    
    session["user_key"] = user_key
    session["history"] = [{"role": "assistant", "content": "System Initialized. I am Opti AI. Please provide your Specs (CPU, GPU, RAM) and Platform to begin optimization."}]
    return redirect(url_for('opti_chat'))

@app.route('/dashboard')
def opti_chat():
    if "user_key" not in session:
        return redirect(url_for('login'))
    return render_template('index.html', user_id=session["user_key"], initial_msg=session["history"][0]["content"])

# --- AI LOGIC ---
@app.route('/ask', methods=['POST'])
def ask_ai():
    if "user_key" not in session: return "Unauthorized", 401
    
    user_query = request.form.get('query')
    history = session.get("history", [])
    
    system_msg = {
        "role": "system", 
        "content": """You are Opti AI, a specialized hardware performance architect.
        1. Provide elite, spec-specific optimization tips.
        2. Use bullet points for readability.
        3. MANDATORY: At the end of every optimization, you MUST provide ratings in this format:
           [EFF: X] [RSK: Y] (Where X and Y are numbers 1-5)."""
    }

    history.append({"role": "user", "content": user_query})

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[system_msg] + history[-6:] # Keeps the last 6 messages for context
        )
        ai_msg = response.choices[0].message.content
        history.append({"role": "assistant", "content": ai_msg})
        session["history"] = history
        return ai_msg
    except Exception as e:
        return f"AI Error: {str(e)}"

# --- PORT FIX FOR RENDER ---
if __name__ == "__main__":
    # This solves the "No open HTTP ports detected" error
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
