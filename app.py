import os
import re
from flask import Flask, render_template, request, session, redirect, url_for
from openai import OpenAI

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "opti_premium_2026")

# FIX 1: Corrected 'api_key' to prevent the TypeError crash
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Strict System Prompt to prevent random off-topic answers
SYSTEM_PROMPT = (
    "You are Opti AI. ONLY answer questions about PC optimization, Windows, and gaming performance. "
    "If asked about other topics, refuse politely. NO asterisks (**) in your output. Use emojis."
)

@app.route('/')
def login():
    if "user_key" in session: return redirect(url_for('opti_chat'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/opti', methods=['POST'])
def handle_login():
    user_key = request.form.get('license_id', '').strip().upper()
    if user_key:
        session["user_key"] = user_key
        session["history"] = [{"role": "assistant", "content": "⚡ System Online. Please provide your Specs, Platform, and Favorite Games."}]
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
    history.append({"role": "user", "content": user_query})
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o", 
            messages=[{"role": "system", "content": SYSTEM_PROMPT}] + history[-10:],
            temperature=0.3
        )
        # Strip asterisks for clean formatting
        clean_msg = re.sub(r'\*+', '', response.choices[0].message.content)
        history.append({"role": "assistant", "content": clean_msg})
        session["history"] = history
        return clean_msg
    except Exception as e:
        return f"System Error: {str(e)}"

if __name__ == "__main__":
    # FIX 2: Bind to 0.0.0.0 and use the Render PORT environment variable
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
