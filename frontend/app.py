from flask import Flask, render_template
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000/api/v1")

@app.route("/")
def index():
    return render_template("index.html", backend_url=BACKEND_URL)

@app.route("/auth")
def auth():
    return render_template("auth.html", backend_url=BACKEND_URL)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
