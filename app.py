import os
import re
from flask import Flask, render_template, request, session, redirect, url_for
from openai import OpenAI

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "opti_ultra_2026")
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# SECURITY: Authorized License Keys
VALID_KEYS = ["OPTI-1234", "OPTI-5678", "VIP-ACCESS", "BETA-TESTER"]

# THE MASTER BRAIN
SYSTEM_PROMPT = """You are Opti AI, the Performance Architect.
MODE 1: OPTIMIZER (ALL PLATFORMS)
- Cover PC (Kernel tweaks, BIOS, stripping drivers), MAC (GPTK 4.0, Thermal management), and CONSOLE (PS5 Pro, Xbox VRR/MTU). 
- Provide deeply technical advice, not basic tips.
MODE 2: PRO SETTINGS (DATA)
- Provide DPI, Sensitivity, and Video Settings for Pro players based on prosettings.net data.
- IMPORTANT: No asterisks (**). Use emojis. Be concise."""

@app.route('/')
def login():
    if "user_key" in session: return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/opti', methods=['POST'])
def handle_login():
    key = request.form.get('license_id', '').strip().upper()
    if key in VALID_KEYS:
        session["user_key"] = key
        session["history"] = []
        return redirect(url_for('dashboard'))
    return "ACCESS DENIED: Invalid License Key", 401

@app.route('/dashboard')
def dashboard():
    if "user_key" not in session: return redirect(url_for('login'))
    return render_template('index.html', user_id=session["user_key"])

@app.route('/ask', methods=['POST'])
def ask_ai():
    if "user_key" not in session: return "Unauthorized", 401
    
    user_query = request.form.get('query')
    mode = request.form.get('mode', 'optimizer')
    history = session.get("history", [])

    # STEP-BY-STEP PRO LOGIC
    if mode == "pro":
        pro_turns = [m for m in history if "[PRO]" in m.get('content', '')]
        if not pro_turns:
            response_text = "🎮 Pro Engine Active. What **Game** are we looking at? (e.g., CS2, Valorant)"
        elif len(pro_turns) == 1:
            response_text = f"Acknowledged. Which **Pro Player** do you want the settings for?"
        else:
            # Full AI completion for final settings
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": SYSTEM_PROMPT}] + history[-6:] + [{"role": "user", "content": user_query}]
            )
            response_text = re.sub(r'\*+', '', response.choices[0].message.content)
    else:
        # Standard Architect Mode
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": SYSTEM_PROMPT}] + history[-10:] + [{"role": "user", "content": user_query}]
        )
        response_text = re.sub(r'\*+', '', response.choices[0].message.content)

    # Update history with tags
    history.append({"role": "user", "content": user_query})
    history.append({"role": "assistant", "content": f"[{mode.upper()}] {response_text}"})
    session["history"] = history
    return response_text

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
