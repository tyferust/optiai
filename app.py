import os
import re
from flask import Flask, render_template, request, session, redirect, url_for
from openai import OpenAI

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "opti_premium_2026")
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# SECURITY FIX: Ensure these are the ONLY keys that work
VALID_KEYS = ["OPTI-1234", "OPTI-5678", "VIP-ACCESS"]

def clean_output(text):
    return re.sub(r'\*+', '', text)

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
    
    # FIXED: Strict validation check
    if user_key in VALID_KEYS:
        session["user_key"] = user_key
        session["history"] = [{"role": "assistant", "content": "⚡ System Online. Accessing Performance Core."}]
        return redirect(url_for('opti_chat'))
    
    # If key is not in the list, redirect back with an error (or simple return)
    return "Invalid License Key. Access Denied."

@app.route('/dashboard')
def opti_chat():
    if "user_key" not in session: return redirect(url_for('login'))
    return render_template('index.html', user_id=session["user_key"], initial_msg=session["history"][0]["content"])

@app.route('/ask', methods=['POST'])
def ask_ai():
    if "user_key" not in session: return "Unauthorized", 401
    user_query = request.form.get('query')
    mode = request.form.get('mode', 'optimizer') # Detect if user is in 'Pro Settings' tab
    history = session.get("history", [])

    # AI KNOWLEDGE BASE INSTRUCTIONS
    if mode == "pro":
        system_prompt = "You are the Pro Settings Expert. Using data from prosettings.net, provide specific mouse DPI, sensitivity, and video settings used by pro gamers. DO NOT answer general optimization questions here. ONLY talk about pro player gear and settings."
    else:
        system_prompt = "You are Opti AI. ONLY discuss PC optimization and latency. REFUSE questions about pro gamer settings in this mode. Use emojis, no asterisks."

    history.append({"role": "user", "content": user_query})
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o", 
            messages=[{"role": "system", "content": system_prompt}] + history[-10:],
            temperature=0.3
        )
        clean_msg = clean_output(response.choices[0].message.content)
        history.append({"role": "assistant", "content": clean_msg})
        session["history"] = history
        return clean_msg
    except Exception as e:
        return f"Neural Error: {str(e)}"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
