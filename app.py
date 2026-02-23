import os
from flask import Flask, render_template, request, session, redirect, url_for
from openai import OpenAI

app = Flask(__name__)
# This secret key is needed for the login system to remember users
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "optiai_secure_key_2026")

# 1. SETUP OPENAI
# This connects to the API key you added in your Render Environment Variables
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# 2. YOUR LICENSE KEYS
# These are the codes your friends will use to log in
VALID_KEYS = ["OPTI-1234", "OPTI-5678", "VIP-ACCESS"]

@app.route('/')
def login():
    if "user" in session:
        return redirect(url_for('opti_chat'))
    return render_template('login.html')

@app.route('/opti', methods=['POST'])
def handle_login():
    user_key = request.form.get('license_id')
    if user_key in VALID_KEYS:
        session["user"] = user_key
        return redirect(url_for('opti_chat'))
    else:
        return "Invalid License Key. Please check your code or contact support."

@app.route('/dashboard')
def opti_chat():
    if "user" not in session:
        return redirect(url_for('login'))
    return render_template('index.html', user_id=session["user"])

@app.route('/ask', methods=['POST'])
def ask_ai():
    if "user" not in session:
        return "Unauthorized", 401
    
    user_query = request.form.get('query')

    try:
        # This sends the user's question to the AI
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are Opti AI, a world-class PC optimization expert. You provide advanced tips on Windows registry tweaks, NVIDIA settings, and network latency reduction to help gamers get the highest FPS and lowest input lag."},
                {"role": "user", "content": user_query}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI Error: {str(e)}"

# 3. THE RENDER PORT FIX
# This tells the app to listen on the specific port Render requires (10000)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
