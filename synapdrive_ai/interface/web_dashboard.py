# synapdrive_ai/interface/web_dashboard.py

from __future__ import annotations

from flask import Flask, jsonify, render_template, request

from synapdrive_ai.pipeline import SynapDrivePipeline

app = Flask(__name__)
pipeline = SynapDrivePipeline()


@app.get("/")
def home():
    return render_template("index.html")


@app.get("/api/log")
def get_log():
    log = pipeline.get_action_log()
    return jsonify({"count": len(log), "log": log[-50:]})


@app.post("/api/run/text")
def run_text():
    data = request.get_json(force=True) or {}
    cmd = (data.get("text") or "").strip()
    image = data.get("image")
    out = pipeline.run_text_command(cmd, image_label=image)
    return jsonify(out)


@app.post("/api/run/signal")
def run_signal():
    data = request.get_json(force=True) or {}
    label = data.get("label")  # None or string
    image = data.get("image")
    out = pipeline.run_signal_event(label=label, image_label=image)
    return jsonify(out)


def main():
    # Local dev server. For production you'd use gunicorn, etc.
    app.run(host="127.0.0.1", port=5055, debug=True)


if __name__ == "__main__":
    main()
