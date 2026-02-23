import os
from flask import Flask, render_template, request
from openai import OpenAI

app = Flask(__name__)

# Render will provide the API Key through an environment variable
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# For now, we'll keep a list of IDs. You can add more here!
VALID_IDS = ["OPTI-1234", "OPTI-5678", "OPTI-GAMER"]

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/opti', methods=['POST'])
def opti_chat():
    user_id = request.form.get('license_id')
    
    if user_id not in VALID_IDS:
        return "Invalid License ID. Please buy access on Discord!"

    return render_template('index.html', user_id=user_id)

@app.route('/ask', methods=['POST'])
def ask():
    user_query = request.form.get('query')
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are Opti AI, a PC optimization expert. Give FPS-boosting tips."},
            {"role": "user", "content": user_query}
        ]
    )
    return response.choices[0].message.content

if __name__ == "__main__":
    app.run()