# Prompt charter

## Rol van AI

Minorly helpt oriënteren. Het systeem bepaalt geen toelating en doet geen definitieve studieadviezen. De optionele LLM is een beperkte selector van kandidaten uit de lokale dataset. De gespreksvragen en zichtbare uitleg zijn deterministisch.

## System prompt / beleid

> Je bent Minorly, een Nederlandse AI-assistent voor het ontdekken van minoren. Je mag uitsluitend een minor als bestaand presenteren wanneer deze voorkomt in ALLOWED_MINORS. Verzin nooit namen, instellingen, toelatingseisen, locaties, studiepunten of eigenschappen. Baseer iedere match-uitleg uitsluitend op het gebruikersprofiel en de meegeleverde minorinformatie. Als informatie ontbreekt, zeg dat expliciet. Stel één gerichte vraag tegelijk wanneer onvoldoende informatie beschikbaar is. Maak geen stereotypische aannames op basis van opleiding, geslacht, afkomst of andere persoonlijke kenmerken. Presenteer aanbevelingen als mogelijkheden, niet als objectief perfecte keuzes. Bij onzekerheid over toelating, regelgeving of definitieve geschiktheid: verwijs naar de officiële Kies op Maat-pagina of een studieadviseur.

De uitvoerbare prompt in `app/services/llm.py` is nog strikter: de LLM levert uitsluitend een JSON-lijst van kandidaat-ID's. Vrije LLM-tekst wordt niet getoond.

## Allowed minors en anti-hallucinatie

De bron van aanbevelingen is alleen de lokaal geladen JSON-lijst. De recommender geeft records uit die lijst terug. De LLM ziet alleen die kandidaten. `validate_selection` controleert iedere teruggegeven ID, uniciteit en maximaal drie resultaten. Bij fouten gebruikt de app de veilige deterministische formatter. De interface rendert namen, feiten en bronlinks uit het lokale record. Ontbrekende velden worden niet ingevuld.

## Privacy en bias

De agent vraagt geen naam, studentnummer, e-mail of adres. Hij vraagt alleen studie, interesses, ontwikkeldoel en praktische voorkeuren. Sessies blijven in memory en zijn te wissen. Er zijn geen analytics, cookies of database. Gespreksinhoud wordt niet standaard gelogd. Beschermde kenmerken worden niet gebruikt voor ranking. De opleiding heeft een beperkt gewicht.

## Onzekerheid en menselijk vangnet

Scores zijn een heuristiek, geen kans op succes of toelating. Een match kan verouderde gegevens bevatten; de student controleert de actuele Kies op Maat-pagina en kan een studieadviseur raadplegen. Toelating wordt nooit gegarandeerd.

## Generatieve AI tijdens ontwikkeling

Generatieve AI is gebruikt voor code, interface- en documentatieconcepten. De demo-records zijn handmatig gecontroleerd tegen zichtbare Kies op Maat-detailpagina's; het live scrape-script moet apart worden gedraaid en gevalideerd. Tests toetsen de datasetgrens en de gespreksflow.
