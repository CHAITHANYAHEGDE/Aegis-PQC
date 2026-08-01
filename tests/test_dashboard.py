from fastapi.testclient import TestClient

from module4_dashboard import app

client = TestClient(app)


def test_websocket_broadcast():
    with client.websocket_connect("/ws") as websocket:
        # Trigger an attack simulate
        response = client.post("/api/simulate-attack?attack_type=constant")
        assert response.status_code == 200
        data = response.json()
        assert "predicted_status" in data

        # Read from websocket
        ws_data = websocket.receive_json()
        assert ws_data["algorithm"] == "ML-KEM-512"
        assert ws_data["attack_profile"] == "timing"


def test_model_selection():
    res = client.get("/api/stats")
    assert res.status_code == 200
    stats = res.json()
    assert "available_models" in stats

    if stats["available_models"]:
        model_to_select = stats["available_models"][0]
        select_res = client.post(f"/api/model/select?model_name={model_to_select}")
        assert select_res.status_code == 200
        assert select_res.json()["active_model"] == model_to_select


def test_run_normal():
    response = client.post("/api/run-normal")
    assert response.status_code == 200
    data = response.json()
    assert "measured" in data
    assert "execution_time_us" in data["measured"]


def test_export_endpoints():
    json_res = client.get("/api/export/json")
    assert json_res.status_code == 200

    csv_res = client.get("/api/export/csv")
    assert csv_res.status_code == 200
    assert "text/csv" in csv_res.headers["content-type"]
