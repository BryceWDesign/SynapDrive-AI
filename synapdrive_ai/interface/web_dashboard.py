from __future__ import annotations

from flask import Flask, jsonify, render_template, request

from synapdrive_ai.pipeline import SynapDrivePipeline

app = Flask(__name__)

# IMPORTANT: use no-delay mode so:
# - local dev feels snappy
# - tests don’t sleep for simulated actuation
pipeline = SynapDrivePipeline(simulate_delay=False)


@app.get("/")
def home():
    return render_template("index.html")


@app.get("/api/log")
def get_log():
    log = pipeline.get_action_log()
    return jsonify({"count": len(log), "log": log[-50:]})


@app.get("/api/assurance")
def get_assurance():
    return jsonify(
        {
            "report": pipeline.get_assurance_report(),
            "receipts": pipeline.get_assurance_log()[-50:],
        }
    )


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
    app.run(host="127.0.0.1", port=5055, debug=True)


if __name__ == "__main__":
    main()
