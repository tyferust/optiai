import os
import psycopg2
from flask import Flask, render_template, request, session, redirect, url_for
from openai import OpenAI

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "opti_premium_2026")
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

DB_URL = os.environ.get("DATABASE_URL")

def get_db_connection():
    return psycopg2.connect(DB_URL, connect_timeout=10)

@app.route('/')
def login():
    if "user_key" in session: return redirect(url_for('opti_chat'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear() # Clears license and chat history
    return redirect(url_for('login'))

@app.route('/opti', methods=['POST'])
def handle_login():
    user_key = request.form.get('license_id', '').strip().upper()
    valid_keys = ["OPTI-1234", "OPTI-5678", "VIP-ACCESS", "OPTI-2026-X"]

    if user_key in valid_keys:
        session["user_key"] = user_key
        # Initial greeting forces the onboarding flow
        session["history"] = [{"role": "assistant", "content": "System Initialized. To begin your optimization journey, please provide your **Specs (CPU/GPU/RAM)**, **Platform**, and **Favorite Games**."}]
        return redirect(url_for('opti_chat'))
    return "Invalid Key."

@app.route('/dashboard')
def opti_chat():
    if "user_key" not in session: return redirect(url_for('login'))
    return render_template('index.html', user_id=session["user_key"], initial_msg=session["history"][0]["content"])

@app.route('/ask', methods=['POST'])
def ask_ai():
    if "user_key" not in session: return "Unauthorized", 401
    user_query = request.form.get('query')
    history = session.get("history", [])

    system_msg = {
        "role": "system", 
        "content": """You are Opti AI. Follow this workflow strictly:
        1. On the FIRST user message (Specs/Games), acknowledge them briefly, then ASK: 'What kind of optimizations do you want? (General Windows, Advanced Windows, Internet/Wifi, or BIOS)'.
        2. Do NOT provide tips until the user has chosen one of those categories.
        3. Once a category is chosen, provide elite, surgical tips.
        4. ALWAYS end every optimization response with ratings: [EFF: X/5] [RSK: Y/5]."""
    }

    history.append({"role": "user", "content": user_query})
    try:
        response = client.chat.completions.create(model="gpt-4o", messages=[system_msg] + history[-10:])
        ai_msg = response.choices[0].message.content
        history.append({"role": "assistant", "content": ai_msg})
        session["history"] = history
        return ai_msg
    except Exception as e:
        return f"AI Error: {str(e)}"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
