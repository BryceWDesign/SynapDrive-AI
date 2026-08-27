from synapdrive_ai.interface import web_dashboard


def test_dashboard_home_route() -> None:
    client = web_dashboard.app.test_client()
    response = client.get("/")
    assert response.status_code == 200
    assert b"SynapDrive-AI Dashboard" in response.data


def test_dashboard_text_api() -> None:
    client = web_dashboard.app.test_client()
    response = client.post("/api/run/text", json={"text": "stop", "image": "hazard"})
    assert response.status_code == 200
    payload = response.get_json()
    assert "status" in payload
    assert "result" in payload
    assert payload["result"]["status"] in {"success", "blocked"}


def test_dashboard_log_api() -> None:
    client = web_dashboard.app.test_client()
    client.post("/api/run/text", json={"text": "move left", "image": "road"})

    response = client.get("/api/log")
    assert response.status_code == 200
    payload = response.get_json()
    assert "count" in payload
    assert "log" in payload
    assert isinstance(payload["log"], list)


def test_dashboard_assurance_api() -> None:
    client = web_dashboard.app.test_client()
    client.post("/api/run/text", json={"text": "move left", "image": "road"})

    response = client.get("/api/assurance")
    assert response.status_code == 200
    payload = response.get_json()
    assert "report" in payload
    assert "receipts" in payload
    assert payload["report"]["total_cycles"] >= 1
    assert isinstance(payload["receipts"], list)


def test_dashboard_rejects_non_object_json() -> None:
    client = web_dashboard.app.test_client()
    response = client.post("/api/run/text", json=["move left"])
    assert response.status_code == 400
    assert response.get_json()["error"] == "invalid-request"


def test_dashboard_unknown_api_route_is_404() -> None:
    client = web_dashboard.app.test_client()
    response = client.get("/api/does-not-exist")
    assert response.status_code == 404
    assert response.get_json()["error"] == "not-found"
