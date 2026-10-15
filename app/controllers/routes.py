"""Controller: vertaalt HTTP-verzoeken naar service-aanroepen."""

from fastapi import APIRouter
from fastapi.responses import FileResponse

from app.config import ROOT
from app.models import ChatRequest, ResetRequest
from app.services.conversation import ConversationEngine


def create_router(engine: ConversationEngine) -> APIRouter:
    """Maak routes met dezelfde engine, zodat alle verzoeken een sessie delen."""
    router = APIRouter()

    @router.get("/")
    def index():
        # De HTML/CSS/JS vormen de view. De controller levert alleen de pagina.
        return FileResponse(ROOT / "app/static/index.html")

    @router.get("/api/health")
    def health():
        return {"status": "ok", "dataset_count": len(engine.minors),
                "configured_ai_mode": engine.llm.configured_mode}

    @router.get("/api/minors/count")
    def minor_count():
        return {"count": len(engine.minors)}

    @router.post("/api/chat")
    def chat(request: ChatRequest):
        # Geen gesprekslogica in de route; de service verwerkt de fase en ranking.
        return engine.chat(request.session_id, request.message)

    @router.post("/api/reset")
    def reset(request: ResetRequest):
        engine.reset(request.session_id)
        return {"reset": True}

    return router
