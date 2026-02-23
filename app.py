import os
import re
from flask import Flask, render_template, request, session, redirect, url_for
from openai import OpenAI

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "opti_premium_final_2026")
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

VALID_KEYS = ["OPTI-1234", "OPTI-5678", "VIP-ACCESS"]

# THE ORIGINAL FULL-SCOPE PROMPT
SYSTEM_PROMPTS = {
    "optimizer": """You are the Global Optimization Architect. 
    - WINDOWS: Kernel tweaks, BCDEDIT, Registry debloating, Process Lasso logic, stripping GPU drivers.
    - MAC: macOS Tahoe, Game Mode deep-dive, GPTK 4.0 translation layer tweaks, thermals.
    - CONSOLE: VRR/ALLM, 120Hz/40fps modes, internal SSD speed requirements, DNS/MTU networking.
    - BIOS: C-States, Re-size BAR, XMP/DOCP. 
    RULES: No asterisks (**). Use emojis. Be technical but clear.""",
    
    "pro": """You are the Pro Settings Expert. 
    Use data from prosettings.net. Provide DPI, Sensitivity, and Video Settings for the top 1% (e.g., Tenz, m0nesy).
    RULES: No asterisks (**). Use emojis. Be concise."""
}

@app.route('/dashboard')
def dashboard():
    if "user_key" not in session: return redirect(url_for('login'))
    
    # Initialize separate histories
    if "opti_history" not in session:
        session["opti_history"] = [{"role": "assistant", "content": "⚡ **System Online.** Welcome to the Architect core. To begin, please provide your **Specs**, **Platform** (Win/Mac/Console), and the **Games** you want to optimize."}]
    if "pro_history" not in session:
        session["pro_history"] = [{"role": "assistant", "content": "🎮 **Pro Data Engine Active.** Which game are we looking at today? (e.g., Valorant, CS2)"}]
    
    return render_template('index.html', user_id=session["user_key"])

@app.route('/ask', methods=['POST'])
def ask_ai():
    if "user_key" not in session: return "Unauthorized", 401
    
    user_query = request.form.get('query')
    mode = request.form.get('mode', 'optimizer')
    history_key = "opti_history" if mode == "optimizer" else "pro_history"
    history = session.get(history_key, [])

    history.append({"role": "user", "content": user_query})
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": SYSTEM_PROMPTS[mode]}] + history[-10:],
            temperature=0.4
        )
        ai_msg = re.sub(r'\*+', '', response.choices[0].message.content)
        history.append({"role": "assistant", "content": ai_msg})
        session[history_key] = history
        return ai_msg
    except Exception as e:
        return f"System Error: {str(e)}"

# Standard Login/Logout Routes remain unchanged
