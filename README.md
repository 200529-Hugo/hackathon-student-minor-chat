# MinorMatch

Een Nederlandstalige, spraakgestuurde PoC voor HBO-studenten die een minor verkennen. De app vraagt eerst naar opleiding, interesses, ontwikkeldoel en eventuele praktische voorkeuren. Daarna toont hij maximaal drie matches uit een lokale Kies op Maat-dataset. Iedere kaart bevat herleidbare redenen en een bronlink.

## Architectuur

Vanilla HTML/CSS/JavaScript gebruikt de Web Speech API en praat met FastAPI. De code volgt een kleine MVC-indeling: `app/models.py` beschrijft het profiel en de sessie, `app/controllers/routes.py` behandelt HTTP, `app/static/` is de view en `app/services/` bevat de gespreks-, ranking-, LLM- en validatielogica. `app/main.py` verbindt deze onderdelen. Meer in [docs/architecture.md](docs/architecture.md), de [Mermaid-flowchart](docs/flowchart.md) en [docs/prompt-charter.md](docs/prompt-charter.md).

## Installatie en starten

Python 3.12+ is nodig. Voer de commando's uit in `minor-match/`.

```sh
python -m venv .venv
```

Windows:

```bat
.venv\Scripts\activate
```

macOS/Linux:

```sh
source .venv/bin/activate
```

```sh
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open [http://localhost:8000](http://localhost:8000). Controleer [health](http://localhost:8000/api/health) voor het aantal geladen records. Run tests met `pytest -q`.

## Dataset en scraper

`data/minors.json` is de actieve lokale dataset. Het bestand bevat momenteel 100 records uit een rustige scrape van de bereikbare acceptatieomgeving van Kies op Maat. Een eerdere ruwe scrape van 30 records staat in `data/scraped_minors.json`. `data/sample_minors.json` bevat vier handmatig gecontroleerde demo-records als fallback. Dit is **geen volledige productie-scrape**. De bronpagina's kunnen veranderen; controleer de actuele gegevens voor gebruik. De app blijft werken zonder netwerkverbinding.

Voor een nieuwe lokale scrape van de productiebron:

```sh
python scraper/scrape_kiesopmaat.py --limit 100 --output data/minors.json
```

De scraper gebruikt `requests` en BeautifulSoup, een user-agent, een time-out, foutafhandeling, minimaal één seconde pauze en geen parallelle requests. Hij volgt pagina's via `?type=m&page=N` en detail-URL's in het patroon `/modules/<organisatie>/<opleiding>/<id>/`. Hij schrijft alleen gevonden tekst en `null` of `[]` voor ontbrekende velden. Controleer bij een wijziging van de Kies op Maat-HTML de selectors in het script. De productie-URL gaf tijdens ontwikkeling HTTP 401 met browser-verificatie. Gebruik dan expliciet de bereikbare acceptatieomgeving:

```sh
python scraper/scrape_kiesopmaat.py --limit 100 --output data/minors.json --base-url https://acceptatie.kiesopmaat.nl/modules/
```

Herstart na een succesvolle scrape de app. Als `data/minors.json` ontbreekt, gebruikt de app automatisch `data/sample_minors.json`.

## Environment variables

Zie `.env.example`. Variabelen worden via de shell gezet; het `.env`-bestand wordt niet automatisch gelezen.

| Variabele | Betekenis |
| --- | --- |
| `MINORS_FILE` | Pad naar lokale JSON-dataset, relatief aan projectroot of absoluut |
| `OLLAMA_BASE_URL`, `OLLAMA_MODEL` | Optionele Ollama-selector; heeft voorrang |
| `OPENAI_BASE_URL`, `OPENAI_API_KEY`, `OPENAI_MODEL` | Optionele OpenAI-compatible selector |

Zonder provider, bij ontbrekende sleutel of bij een fout gebruikt de app vaste Nederlandse teksten en de transparante ranking. Geen betaalde dienst is nodig.

### Is dit Ollama of regelgebaseerd?

Standaard is de PoC **regelgebaseerd**: de services stellen vaste vragen, rangschikken lokale JSON-records en formuleren veilige antwoorden. Dit is geen actieve generatieve AI. Zet `OLLAMA_BASE_URL` om Ollama te gebruiken; dan mag Ollama uitsluitend ID's kiezen uit de lokaal gevonden topkandidaten. Als Ollama niet bereikbaar is, valt de app terug op de regelgebaseerde selectie. Een OpenAI-compatible endpoint werkt alleen wanneer `OPENAI_BASE_URL` én `OPENAI_API_KEY` zijn ingesteld. De app leest `.env` niet automatisch; exporteer variabelen in de shell voordat je `uvicorn` start.

Bijvoorbeeld met een lokaal draaiende Ollama-server en beschikbaar model:

```sh
export OLLAMA_BASE_URL=http://localhost:11434
export OLLAMA_MODEL=llama3.2
uvicorn app.main:app --reload
```

`GET /api/health` toont `configured_ai_mode`. Dit zegt welke provider is ingesteld, niet of die bereikbaar was voor een afzonderlijk antwoord; bij een netwerk- of modelfout gebruikt dat antwoord de deterministische fallback.

## Browser en privacy

Spraakherkenning gebruikt `SpeechRecognition` of `webkitSpeechRecognition` met `nl-NL`; ondersteuning verschilt per browser. Tekstinvoer blijft altijd beschikbaar. Voorlezen gebruikt `speechSynthesis` en probeert een Nederlandse stem. De microfoon luistert alleen na een klik en staat uit tijdens voorlezen. Er is geen automatische continue opname.

De server bewaart geen persoonsgegevens of gesprekshistorie op schijf. Sessies leven alleen in het serverproces en worden verwijderd met Nieuw gesprek. Er zijn geen analytics of cookies. Voer geen gevoelige persoonsgegevens in. Sommige browsers verwerken spraak via hun eigen dienst; raadpleeg het browserprivacybeleid.

## Vier handmatige demo-testcases

Deze vaste voorbeelden verwijzen naar de vier records in `data/sample_minors.json`. Start voor een voorspelbare hackathon-demo met `MINORS_FILE=data/sample_minors.json uvicorn app.main:app --reload` (macOS/Linux). Zonder deze instelling gebruikt de app de actuele `data/minors.json`; de namen in de voorbeelden hoeven daar niet in voor te komen.

1. **ICT / ondernemen.** Antwoord: `ICT`, `ondernemen en innovatie`, `verbreden`, `geen voorkeur`. Verwacht onder meer de lokaal aanwezige minor Ondernemen; zeg daarna `Ik wil minder programmeren` of `Geef me andere opties`.
2. **CMD / duurzaamheid.** Antwoord: `CMD`, `duurzaamheid en creatief`, `verbreden`, `Utrecht`. Verwacht Arts and Ecology als passende lokale optie; vraag `Vertel meer over de eerste`.
3. **Onzeker.** Antwoord: `ICT`, `Ik weet niet wat ik wil`. Verwacht een vervolgvraag en nog geen aanbevelingen.
4. **Toelating.** Vraag na een resultaat: `Kan ik gegarandeerd worden toegelaten?` Verwacht geen garantie en een verwijzing naar de bron en studieadviseur.

## Bekende beperkingen en anti-hallucinatie

De demo-dataset is klein en de ranking gebruikt eenvoudige tokens; synoniemen en taalfouten kunnen een match missen. Scores zijn relatieve heuristiek, geen geschiktheidspercentage. De productie-HTML kan veranderen. Een live scrape en browser-spraak zijn in deze omgeving niet end-to-end geverifieerd.

Nooit wordt een willekeurige minornaam uit een LLM-antwoord getoond. Alleen lokaal geladen records worden gerangschikt; een optionele LLM mag uitsluitend IDs uit de topkandidaten teruggeven. Ongeldige of onbekende IDs vallen terug op de deterministische selectie. Ontbrekende gegevens worden niet aangevuld. Controleer toelating en actuele details altijd bij Kies op Maat of de studieadviseur.
