import re

from app.models import Profile, Session
from app.services.recommender import rank

WELCOME = ("Hallo, ik ben MinorMatch, een AI-assistent die je helpt bij het ontdekken van een minor. "
           "Deel liever geen gevoelige persoonsgegevens. Welke opleiding volg je nu?")


class ConversationEngine:
    """Service: bepaalt de volgende vraag of zoekt opnieuw na een vervolgvraag."""

    def __init__(self, minors, llm):
        # Eén engine per serverproces. Een serverherstart wist daardoor alle sessies.
        self.minors = minors
        self.llm = llm
        self.sessions: dict[str, Session] = {}

    def reset(self, session_id: str):
        """Verwijder ook het profiel en de laatst getoonde aanbevelingen."""
        self.sessions.pop(session_id, None)

    def _answer(self, session, reply, recommendations=None, needs_more=True):
        return {"reply": reply, "profile": session.profile.model_dump(),
                "recommendations": recommendations or [], "needs_more_information": needs_more}

    def _recommend(self, session):
        # Eerst lokaal zoeken. De LLM ziet uitsluitend deze kandidaten en mag
        # geen nieuwe minorrecords aan de lijst toevoegen.
        candidates = rank(session.profile, self.minors, excluded_ids=session.excluded_ids)
        selected = self.llm.generate_response(session.profile, candidates)
        session.last_recommendations = selected
        session.stage = "results"
        if not selected:
            return self._answer(session,
                                "Ik vind in de lokale dataset geen passende minor. Welke interesse of voorkeur wil je aanpassen? Je kunt ook je studieadviseur vragen.",
                                needs_more=True)
        quantity = "mogelijkheid" if len(selected) == 1 else "mogelijkheden"
        return self._answer(session,
                            f"Ik vond {len(selected)} {quantity} in de lokale dataset. Bekijk de kaarten en controleer de gegevens op Kies op Maat.",
                            selected, False)

    def chat(self, session_id: str, message: str):
        """Verwerk één bericht binnen de huidige gespreksfase."""
        session = self.sessions.setdefault(session_id, Session())
        value = message.strip()
        low = value.lower()
        if low in {"start", "hallo", "hoi", "hey"} and session.stage == "study":
            return self._answer(session, WELCOME)
        if re.search(r"gegarandeerd|garantie|zeker toegelaten|toelating", low):
            return self._answer(session,
                                "Toelating kan ik niet garanderen. Controleer de actuele eisen op de officiële Kies op Maat-pagina en bespreek ze met je studieadviseur.",
                                session.last_recommendations, session.stage != "results")
        if session.stage == "study":
            if len(value) < 2 or "weet niet" in low:
                return self._answer(session, "Welke opleiding volg je nu? Een globale studierichting is genoeg.")
            session.profile.study = value
            session.stage = "interests"
            return self._answer(session, "Waar zou je tijdens je minor graag meer over willen leren?")
        if session.stage == "interests":
            if "weet niet" in low or len(value) < 3:
                return self._answer(session,
                                    "Dat is prima. Denk aan onderwerpen als creativiteit, duurzaamheid of ondernemen. Welk onderwerp spreekt je het meest aan?")
            session.profile.interests = [v.strip() for v in re.split(r",| en | of |/", value) if v.strip()]
            session.stage = "goal"
            return self._answer(session,
                                "Wil je vooral verdiepen binnen je huidige richting of juist iets nieuws ontdekken?")
        if session.stage == "goal":
            if "weet niet" in low:
                return self._answer(session,
                                    "Wil je ongeveer binnen je opleiding blijven, of liever een nieuwe richting verkennen?")
            session.profile.development_goal = value
            session.stage = "preferences"
            return self._answer(session,
                                "Heb je een voorkeur voor locatie, onderwijsvorm of taal? Zeg gerust 'geen voorkeur'.")
        if session.stage == "preferences":
            self._update_preferences(session.profile, value)
            return self._recommend(session)
        # Na de vier profielvragen interpreteren we vervolgvragen over de
        # getoonde kaarten en aangepaste voorkeuren.
        ordinal = {"eerste": 0, "tweede": 1, "derde": 2}
        if "vertel meer" in low or "meer over" in low:
            index = next((number for word, number in ordinal.items() if word in low), 0)
            if index < len(session.last_recommendations):
                minor = session.last_recommendations[index]["minor"]
                details = minor.get("description") or "Er is geen omschrijving beschikbaar."
                return self._answer(session,
                                    f"{minor['name']}: {details} Bekijk de officiële pagina voor actuele voorwaarden: {minor['url']}",
                                    session.last_recommendations, False)
            return self._answer(session, "Die optie staat niet in de huidige aanbevelingen. Welke kaart bedoel je?",
                                session.last_recommendations, False)
        if "deze spreekt me niet aan" in low or "andere opties" in low:
            if "deze spreekt" in low and session.last_recommendations:
                session.excluded_ids.add(session.last_recommendations[0]["minor"]["id"])
            else:
                session.excluded_ids.update(item["minor"]["id"] for item in session.last_recommendations)
            return self._recommend(session)
        self._update_preferences(session.profile, value)
        if "creatie" in low or "creatief" in low:
            session.profile.interests.append("creatief ontwerp")
        elif not re.search(r"utrecht|amsterdam|rotterdam|breda|online|deeltijd|voltijd|nederlands|engels", low):
            session.profile.interests.append(value)
        session.excluded_ids.clear()
        return self._recommend(session)

    @staticmethod
    def _update_preferences(profile, value):
        """Haal eenvoudige praktische voorkeuren uit vrije tekst."""
        low = value.lower()
        for city in ("Utrecht", "Amsterdam", "Rotterdam", "Breda", "Arnhem", "Zwolle", "Den Haag"):
            if city.lower() in low:
                profile.location_preferences = [city]
        for mode in ("online", "deeltijd", "voltijd", "Nederlands", "Engels"):
            if mode.lower() in low:
                profile.study_mode_preferences = [mode]
        for pattern in (r"minder ([\w-]+)", r"geen ([\w-]+)", r"zonder ([\w-]+)"):
            match = re.search(pattern, low)
            if match and match.group(1) != "voorkeur":
                profile.avoid.append(match.group(1))
