# MinorMatch workflow

Dit diagram toont de runtime-flow. De browser is de view, de FastAPI-routes zijn de controller, het profiel en de minorrecords zijn de modellen, en de services voeren gesprek, ranking en validatie uit.

```mermaid
flowchart TD
    A[App start] --> B[Laad lokale minors.json]
    B --> C[Browser toont AI- en privacyverklaring]
    C --> D[Student typt of drukt op microfoon]
    D --> E[Controller ontvangt POST /api/chat]
    E --> F[Conversation service haalt tijdelijke sessie op]
    F --> G{Profiel compleet?}
    G -- Nee --> H[Stel één vervolgvraag]
    H --> D
    G -- Ja --> I[Recommendation service filtert en rangschikt lokale minoren]
    I --> J{Kandidaten gevonden?}
    J -- Nee --> K[Meld onzekerheid en vraag voorkeur aan te passen]
    K --> D
    J -- Ja --> L{LLM geconfigureerd?}
    L -- Nee --> M[Deterministische topselectie]
    L -- Ja --> N[Ollama of OpenAI-compatible service kiest alleen kandidaat-ID's]
    N --> O{ID's geldig en toegestaan?}
    O -- Nee --> M
    O -- Ja --> P[Geselecteerde lokale records]
    M --> Q[Maximaal 3 kaarten met score, redenen en bronlink]
    P --> Q
    Q --> R[Browser toont resultaat en spreekt antwoord uit]
    R --> S{Vervolgvraag of reset?}
    S -- Vervolgvraag --> D
    S -- Reset --> T[POST /api/reset wist sessie uit geheugen]
    T --> C
```

## AI-modus

- Met `OLLAMA_BASE_URL` gebruikt de app Ollama om alleen bestaande kandidaat-ID's te selecteren.
- Zonder Ollama kan een OpenAI-compatible endpoint worden gebruikt wanneer `OPENAI_BASE_URL` en `OPENAI_API_KEY` zijn ingesteld.
- Zonder provider of bij een fout gebruikt de app deterministische regels. Dat is een veilige fallback, geen generatieve AI.
- Namen, details en matchredenen komen altijd uit lokale records en ranking. De LLM mag geen nieuwe minor aanmaken.
