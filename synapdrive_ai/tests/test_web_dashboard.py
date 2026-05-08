from synapdrive_ai.interface import web_dashboard


def test_dashboard_home_route():
    client = web_dashboard.app.test_client()
    r = client.get("/")
    assert r.status_code == 200
    assert b"SynapDrive-AI Dashboard" in r.data


def test_dashboard_text_api():
    client = web_dashboard.app.test_client()
    r = client.post("/api/run/text", json={"text": "stop", "image": "hazard"})
    assert r.status_code == 200
    payload = r.get_json()
    assert "status" in payload
    assert "result" in payload
    assert payload["result"]["status"] in {"success", "blocked"}


def test_dashboard_log_api():
    client = web_dashboard.app.test_client()
    # generate one action so log is non-empty
    client.post("/api/run/text", json={"text": "move left", "image": "road"})

    r = client.get("/api/log")
    assert r.status_code == 200
    payload = r.get_json()
    assert "count" in payload
    assert "log" in payload
    assert isinstance(payload["log"], list)


def test_dashboard_assurance_api():
    client = web_dashboard.app.test_client()
    client.post("/api/run/text", json={"text": "move left", "image": "road"})

    r = client.get("/api/assurance")
    assert r.status_code == 200
    payload = r.get_json()
    assert "report" in payload
    assert "receipts" in payload
    assert payload["report"]["total_cycles"] >= 1
    assert isinstance(payload["receipts"], list)
