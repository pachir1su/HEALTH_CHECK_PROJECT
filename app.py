import os
from flask import Flask, render_template, request, jsonify
import sensor_reader
import health_ai
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", pulse=sensor_reader.get_pulse())

@app.route("/chat", methods=["POST"])
def chat():
    symptom = request.json.get("symptom", "").strip()
    pulse   = sensor_reader.get_pulse()
    result  = health_ai.analyze(symptom, pulse)
    app.logger.debug(f"Received symptom={symptom!r}, pulse={pulse}, reply={result!r}")
    return jsonify({
        "pulse": pulse,
        "reply": result
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
