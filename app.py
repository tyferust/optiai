import os
from flask import Flask, render_template, request, session, redirect, url_for
from openai import OpenAI

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "opti_ultra_secret_2026")
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# SECURITY: This dictionary tracks who owns which code
# In a real big business, we'd use a database, but this works for starting out!
CLAIMED_KEYS = {} 
VALID_KEYS = ["OPTI-1234", "OPTI-5678", "VIP-ACCESS", "TEST-99"]

@app.route('/')
def login():
    if "user_key" in session:
        return redirect(url_for('opti_chat'))
    return render_template('login.html')

@app.route('/opti', methods=['POST'])
def handle_login():
    user_key = request.form.get('license_id')
    user_ip = request.remote_addr # Tracks their basic connection ID

    if user_key in VALID_KEYS:
        # Check if the key is already taken by someone else
        if user_key in CLAIMED_KEYS and CLAIMED_KEYS[user_key] != user_ip:
            return "This license is already in use on another device."
        
        # Claim the key for this user
        CLAIMED_KEYS[user_key] = user_ip
        session["user_key"] = user_key
        return redirect(url_for('opti_chat'))
    
    return "Invalid License Key."

@app.route('/dashboard')
def opti_chat():
    if "user_key" not in session:
        return redirect(url_for('login'))
    return render_template('index.html', user_id=session["user_key"])

@app.route('/ask', methods=['POST'])
def ask_ai():
    if "user_key" not in session: return "Unauthorized", 401
    user_query = request.form.get('query')
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system", 
                    "content": "You are Opti AI. Respond in clean, plain text. NEVER use hashtags (#) or bold stars (**). Use clear spacing and bullet points only. Sound like an elite PC tuner."
                },
                {"role": "user", "content": user_query}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
