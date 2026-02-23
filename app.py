import os
import re
from flask import Flask, render_template, request, session, redirect, url_for
from openai import OpenAI

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "opti_pro_2026")

# FIXED: Corrected the keyword argument to 'api_key'
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

VALID_KEYS = ["OPTI-1234", "OPTI-5678", "VIP-ACCESS", "OPTI-2026-X"]

def clean_markdown(text):
    # Removes **bold**, *italics*, and bullet asterisks for a clean terminal look
    return re.sub(r'\*+', '', text)

@app.route('/')
def login():
    if "user_key" in session: return redirect(url_for('opti_chat'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear() # Standard session termination
    return redirect(url_for('login'))

@app.route('/opti', methods=['POST'])
def handle_login():
    user_key = request.form.get('license_id', '').strip().upper()
    if user_key in VALID_KEYS:
        session["user_key"] = user_key
        # Initial AI prompt without asterisks
        session["history"] = [{"role": "assistant", "content": "Neural Link Established. To begin your optimization journey, please provide your Specs, Platform, and Favorite Games."}]
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
        "content": """You are Opti AI. NO MARKDOWN. NO ASTERISKS. Use plain professional text. 
        Flow:
        1. Acknowledge specs, then ASK: 'What kind of optimizations do you want? (General Windows, Advanced Windows, Internet/Wifi, or BIOS)'.
        2. Do not give tips until they pick a category.
        3. End every optimization with ratings: [EFF: X/5] [RSK: Y/5]."""
    }

    history.append({"role": "user", "content": user_query})
    try:
        response = client.chat.completions.create(model="gpt-4o", messages=[system_msg] + history[-10:])
        raw_ai_msg = response.choices[0].message.content
        
        # Clean the message before sending to the UI
        clean_msg = clean_markdown(raw_ai_msg)
        
        history.append({"role": "assistant", "content": clean_msg})
        session["history"] = history
        return clean_msg
    except Exception as e:
        return f"System Error: {str(e)}"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
