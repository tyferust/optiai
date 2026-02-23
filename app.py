import os
import re
import time
from flask import Flask, render_template, request, session, redirect, url_for
from openai import OpenAI

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "opti_pro_2026")
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# TOPIC RESTRICTION LOGIC
SYSTEM_PROMPT = """You are Opti AI, a specialized gaming performance architect. 
STRICT RULES:
1. ONLY answer questions about PC optimization, gaming performance, BIOS, and network latency.
2. If a user asks about food, history, general life, or anything unrelated to optimization, 
   REFUSE politely with: 'I am optimized only for performance tuning. Please stay on topic.'
3. NO markdown (no asterisks **). Use clean, plain text with emojis.
4. Always follow the onboarding flow: Specs -> Category Selection -> Tips."""

@app.route('/ask', methods=['POST'])
def ask_ai():
    if "user_key" not in session: return "Unauthorized", 401
    user_query = request.form.get('query')
    history = session.get("history", [])

    # Keep only the last 5 exchanges for context
    history.append({"role": "user", "content": user_query})
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o", 
            messages=[{"role": "system", "content": SYSTEM_PROMPT}] + history[-10:],
            temperature=0.3 # Lower temperature for less random/off-topic behavior
        )
        ai_msg = re.sub(r'\*+', '', response.choices[0].message.content) # Clean text
        
        history.append({"role": "assistant", "content": ai_msg})
        session["history"] = history
        return ai_msg
    except Exception as e:
        return f"Neural Error: {str(e)}"
