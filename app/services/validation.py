def validate_selection(selected_ids: list[str], allowed_minors: list[dict]) -> bool:
    """Controleer de grens tussen een LLM-antwoord en de lokale dataset."""
    allowed = {item["id"] for item in allowed_minors}
    return (isinstance(selected_ids, list) and 0 < len(selected_ids) <= 3
            and all(isinstance(value, str) for value in selected_ids)
            and len(selected_ids) == len(set(selected_ids))
            and all(value in allowed for value in selected_ids))


def safe_selection(selected_ids: list[str], candidates: list[dict]) -> list[dict]:
    """Gebruik bij ongeldige AI-output de veilige lokale topselectie."""
    allowed = [item["minor"] for item in candidates]
    if not validate_selection(selected_ids, allowed):
        return candidates[:3]
    by_id = {item["minor"]["id"]: item for item in candidates}
    return [by_id[minor_id] for minor_id in selected_ids]
