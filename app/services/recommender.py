import json
import re
import unicodedata
from pathlib import Path

# Stop words in Dutch and English that are too common to be useful for matching.
STOP = {
    "de", "het", "een", "en", "of", "ik", "wil", "graag", "iets", "meer", "met", "voor", "van", "in", "op", "naar",
    "over", "mijn", "dat", "die", "bij", "als", "ook", "the", "and", "for", "you", "this"
}

# Tokenize a string into lowercase words, removing diacritics and filtering out stop words and short words.
def tokens(value: str) -> set[str]:
    value = "".join(c for c in unicodedata.normalize("NFKD", value.lower()) if not unicodedata.combining(c))
    return {w for w in re.findall(r"[a-z0-9]+", value) if len(w) > 2 and w not in STOP}

# Load a list of minors from a JSON file, ensuring each entry has the required fields and is unique by ID.
def load_minors(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))

    # Validate that the loaded data is a list of dictionaries with required keys and unique IDs.
    if not isinstance(data, list):
        raise ValueError("Minorbestand moet een JSON-lijst zijn")

    seen = set()
    result = []
    # Filter out invalid entries and duplicates based on the "id" field.
    for item in data:
        if not isinstance(item, dict) or not item.get("id") or not item.get("name") or not item.get("url"):
            continue

        if item["id"] in seen:
            continue

        seen.add(item["id"])
        result.append(item)

    return result

# Rank a list of minors based on how well they match a user's profile, considering interests, development goals, study background, and preferences.
def rank(profile, minors: list[dict], limit: int = 3, excluded_ids: set[str] | None = None) -> list[dict]:
    # Initialize the set of excluded IDs to avoid recommending minors that the user has already seen or rejected.
    excluded_ids = excluded_ids or set()
    found = []
    interest_words = tokens(" ".join(profile.interests))

    # Remove common words from the development goal to focus on more specific terms for matching.
    goal_words = tokens(profile.development_goal) - {"verdiepen", "verbreden", "nieuws", "nieuw"}

    # Remove common words from the study field to focus on more specific terms for matching.
    study_words = tokens(profile.study)

    # Remove common words from the avoid list to focus on more specific terms for filtering out minors.
    avoid_words = tokens(" ".join(profile.avoid))

    # Iterate through each minor and calculate a score based on how well it matches the user's profile, while also considering any exclusions or avoidances.
    for minor in minors:
        # Skip any minors that are in the excluded list to avoid recommending them again.
        if minor["id"] in excluded_ids:
            continue

        # Tokenize the title, tags, and description of the minor to create a set of words for matching against the user's profile.
        title = tokens(minor.get("name") or "")
        tags = tokens(" ".join(minor.get("tags") or []))
        desc = tokens(minor.get("description") or "")
        whole = title | tags | desc

        # Skip any minors that contain words the user wants to avoid, ensuring that the recommendations align with their preferences.
        if avoid_words & whole:
            continue

        matched_interests = interest_words & whole
        matched_goal = goal_words & whole
        matched_study = study_words & whole

        # Calculate a score for the minor based on the number of matched interests, development goals, and study background, with caps on the maximum points awarded for each category.
        score = min(50, sum(18 if w in title or w in tags else 8 for w in matched_interests))
        score += min(15, len(matched_goal) * 5)
        score += min(15, len(matched_study) * 5)


        reasons = []
        for word in sorted(matched_interests)[:2]:
            field = "titel of tags" if word in title or word in tags else "omschrijving"
            reasons.append(f"{word} komt terug in de {field}")
        if matched_goal:
            reasons.append("Je ontwikkeldoel sluit aan bij de inhoud")
        if matched_study:
            reasons.append("Er is inhoudelijke overlap met je opleiding")
        loc = tokens(minor.get("location") or "")
        if profile.location_preferences and any(tokens(p) & loc for p in profile.location_preferences):
            score += 10
            reasons.append("Locatie komt overeen met je voorkeur")
        mode = tokens(minor.get("study_mode") or "") | tokens(minor.get("language") or "")
        if profile.study_mode_preferences and any(tokens(p) & mode for p in profile.study_mode_preferences):
            score += 10
            reasons.append("Onderwijsvorm of taal komt overeen")
        if not matched_interests and not matched_goal:
            continue
        found.append(
            {"minor": minor, "score": min(100, score), "reasons": reasons or ["Inhoud sluit deels aan op je profiel"]})
    found.sort(key=lambda item: (-item["score"], item["minor"]["name"]))
    return found[:max(0, min(3, limit))]
