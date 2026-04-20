import os
import time
import requests
import json
from flask import Flask, render_template, request
from dotenv import load_dotenv

# 1. Load the secrets from your .env file
load_dotenv()

app = Flask(__name__)

# 2. Get the API Key safely from the environment
API_KEY = os.getenv("OPENROUTER_API_KEY")

@app.route("/", methods=["GET", "POST"])
def index():
    explanation = ""
    if request.method == "POST":
        code = request.form.get("code")
        lang = request.form.get("language", "Auto Detect")

        # UPDATED APRIL 2026 STABLE FREE MODELS
        # If the first one fails, it tries the second, then the third...
        models_to_try = [
            "qwen/qwen3-coder:free",            # Best for programming
            "google/gemma-4-26b-a4b-it:free",   # High speed / New
            "meta-llama/llama-3.3-70b-instruct:free",
            "openrouter/free"                   # Auto-fallback
        ]

        success = False
        last_error_code = ""

        for model_id in models_to_try:
            try:
                headers = {
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "http://localhost:5000", # Required by OpenRouter
                    "X-Title": "Nexus AI Decoder"
                }

                payload = {
                    "model": model_id,
                    "messages": [
                        {"role": "system", "content": "You are a professional code architect. Explain the logic of the code provided clearly and simply.The explannation should be very simple and clear"},
                        {"role": "user", "content": f"Language: {lang}\nCode:\n{code}"}
                    ]
                }

                response = requests.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    data=json.dumps(payload),
                    timeout=10
                )

                if response.status_code == 200:
                    data = response.json()
                    explanation = data["choices"][0]["message"]["content"]
                    # Formatting for our Typewriter effect in HTML
                    explanation = explanation.replace("\n", "<br>")
                    success = True
                    break
                elif response.status_code == 429:
                    # Rate limited? Wait a moment and try the next model
                    time.sleep(1)
                    continue
                else:
                    last_error_code = str(response.status_code)

            except Exception as e:
                last_error_code = "Connection Timeout"
                continue

        if not success:
            explanation = f"SYSTEM_HALT: Error {last_error_code}. All AI nodes busy or API Key invalid."

    return render_template("index.html", explanation=explanation)

if __name__ == "__main__":
    app.run(debug=True)
