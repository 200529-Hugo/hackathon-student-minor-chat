from app.services.validation import safe_selection, validate_selection


def test_fabricated_minor_is_rejected():
    candidate = {"minor": {"id": "real", "name": "Echte minor"}, "score": 80, "reasons": []}
    assert not validate_selection(["invented"], [candidate["minor"]])
    assert safe_selection(["invented"], [candidate]) == [candidate]
