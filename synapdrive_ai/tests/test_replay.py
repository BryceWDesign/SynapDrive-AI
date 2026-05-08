from synapdrive_ai.bci.intent_generator import generate_intent
from synapdrive_ai.pipeline import SynapDrivePipeline
from synapdrive_ai.replay.recording import JsonlRecorder, iter_jsonl, make_record


def test_record_and_replay_roundtrip(tmp_path):
    rec_path = tmp_path / "runs.jsonl"

    pipe = SynapDrivePipeline(simulate_delay=False)
    intent_packet = generate_intent("move left")
    out = pipe.run_intent_packet(intent_packet, image_label="road")

    recorder = JsonlRecorder(rec_path)
    recorder.append(
        make_record(
            mode="text",
            raw_input={"text": "move left"},
            image_label="road",
            intent_packet=intent_packet,
            pipeline_output=out,
        )
    )

    records = list(iter_jsonl(rec_path))
    assert len(records) == 1
    r = records[0]
    assert r["schema"] == "synapdrive.replay.v1"
    assert r["mode"] == "text"
    assert "intent_packet" in r
    assert "output_summary" in r
    assert r["output_summary"]["assurance_passed"] is True
    assert isinstance(r["output_summary"]["assurance_receipt_id"], str)

    # Replay using the stored input intent_packet
    pipe2 = SynapDrivePipeline(simulate_delay=False)
    out2 = pipe2.run_intent_packet(r["intent_packet"], image_label=r.get("image_label"))

    # Compare stable fields (timestamps/durations can differ by design)
    assert out2["status"] == out["status"]
    assert out2["result"]["status"] == out["result"]["status"]
    assert out2["result"]["intent"] == out["result"]["intent"]
