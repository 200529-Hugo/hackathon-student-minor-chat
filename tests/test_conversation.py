from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app, engine
from app.services.conversation import ConversationEngine
from app.services.llm import LLMService
from app.services.recommender import load_minors


def test_asks_when_interests_missing():
    minors = load_minors(Path(__file__).resolve().parents[1] / "data/sample_minors.json")
    conversation = ConversationEngine(minors, LLMService())
    conversation.chat("a", "ICT")
    result = conversation.chat("a", "Ik weet niet wat ik wil")
    assert result["needs_more_information"] is True
    assert result["recommendations"] == []
    assert "onderwerp" in result["reply"].lower()


def test_reset_erases_session_state():
    client = TestClient(app)
    client.post("/api/chat", json={"session_id": "reset-test", "message": "ICT"})
    assert "reset-test" in engine.sessions
    assert client.post("/api/reset", json={"session_id": "reset-test"}).json() == {"reset": True}
    assert "reset-test" not in engine.sessions


def test_controller_exposes_configured_mode_and_dataset_count():
    health = TestClient(app).get("/api/health")
    assert health.status_code == 200
    assert health.json()["dataset_count"] == len(engine.minors)
    assert health.json()["configured_ai_mode"] in {"deterministic", "ollama", "openai-compatible"}


def test_guarantee_answer_and_demo_flow():
    client = TestClient(app)
    sid = "demo-test"
    for message in ("ICT", "ondernemen en innovatie", "verbreden", "geen voorkeur"):
        result = client.post("/api/chat", json={"session_id": sid, "message": message}).json()
    assert result["recommendations"]
    assert all(item["minor"] in engine.minors for item in result["recommendations"])
    answer = client.post("/api/chat", json={"session_id": sid, "message": "Kan ik gegarandeerd worden toegelaten?"}).json()
    assert "niet garanderen" in answer["reply"]
    client.post("/api/reset", json={"session_id": sid})
