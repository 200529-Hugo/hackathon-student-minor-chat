from pathlib import Path

from app.models import Profile
from app.services.recommender import load_minors, rank

DATA = load_minors(Path(__file__).resolve().parents[1] / "data/sample_minors.json")


def test_only_dataset_records_and_max_three():
    result = rank(Profile(study="ICT", interests=["innovatie", "duurzaamheid", "creatief"], development_goal="verbreden"), DATA)
    assert len(result) <= 3
    assert {item["minor"]["id"] for item in result} <= {m["id"] for m in DATA}


def test_avoid_excludes_wrong_match():
    result = rank(Profile(study="ICT", interests=["mode", "creatief"], avoid=["mode"]), DATA)
    assert "hva-144248" not in {item["minor"]["id"] for item in result}
