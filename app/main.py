"""Startpunt: bouw de app en verbind controller, modellen en services."""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import ROOT, minors_path
from app.controllers.routes import create_router
from app.services.conversation import ConversationEngine
from app.services.llm import LLMService
from app.services.recommender import load_minors

app = FastAPI(title="Minorly")

# Het bestand wordt één keer bij de start gelezen. Na een nieuwe scrape is een
# serverherstart nodig om de dataset te verversen.
minors = load_minors(minors_path())
engine = ConversationEngine(minors, LLMService())

app.include_router(create_router(engine))
app.mount("/static", StaticFiles(directory=ROOT / "app/static"), name="static")
