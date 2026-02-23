import os
import re
from flask import Flask, render_template, request, session, redirect, url_for
from openai import OpenAI

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "opti_premium_v2")

# FIXED: Changed api_api_key to api_key to resolve the TypeError
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# TOPIC GUARDRAILS
SYSTEM_PROMPT = """You are Opti AI, a specialized PC optimization architect. 
RULES:
1. ONLY discuss PC optimization, BIOS tweaks, Windows settings, and latency.
2. If the user asks about ANY other topic (food, movies, etc.), reply: 'I am specialized only in performance tuning. Please stay on topic.'
3. NO asterisks (**). Use clean text with emojis.
4. Onboarding: Ask for Specs/Platform/Games first, then ask for a category."""

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
    # Replace with your actual key logic
    if user_key:
        session["user_key"] = user_key
        session["history"] = [{"role": "assistant", "content": "⚡ Neural Link Active. Provide your Specs, Platform, and Favorite Games to begin."}]
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
            messages=[{"role": "system", "content": SYSTEM_PROMPT}] + history[-6:],
            temperature=0.3 # Low temperature makes AI stick to rules better
        )
        clean_msg = clean_output(response.choices[0].message.content)
        history.append({"role": "assistant", "content": clean_msg})
        session["history"] = history
        return clean_msg
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == "__main__":
    # Render requires binding to 0.0.0.0 and the $PORT variable
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
