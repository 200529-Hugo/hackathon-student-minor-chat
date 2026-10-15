"""Conservative Kies op Maat scraper. Run from the project root."""
import argparse
import json
import logging
import re
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

BASE = "https://accept.kiesopmaat.nl/modules/"
HEADERS = {"User-Agent": "Minorly/0.1 (educational, low-rate scraper; contact via project README)"}
LOG = logging.getLogger("scraper")


def fetch(session, url):
    response = session.get(url, headers=HEADERS, timeout=15)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def detail_links(soup, base_url=BASE):
    """Detail paths observed as /modules/<org>/<programme>/<numeric-id>/."""
    found = []
    for a in soup.select('a[href*="/modules/"]'):
        url = urljoin(base_url, a.get("href", ""))
        if re.search(r"/modules/[^/]+/[^/]+/\d+/?$", urlparse(url).path):
            if url not in found:
                found.append(url)
    return found


def labelled_value(soup, label):
    # KOM detail pages have presented these as label: value in side information.
    for node in soup.find_all(string=re.compile(r"^\s*" + re.escape(label) + r"\s*:", re.I)):
        text = node.parent.get_text(" ", strip=True)
        match = re.search(re.escape(label) + r"\s*:\s*(.*)", text, re.I)
        if match and match.group(1):
            return match.group(1).strip()
        sibling = node.parent.find_next_sibling()
        if sibling:
            return sibling.get_text(" ", strip=True) or None
    return None


def section(soup, heading):
    for h in soup.select("h2, h3"):
        if heading.lower() in h.get_text(" ", strip=True).lower():
            chunks = []
            for sibling in h.next_siblings:
                if getattr(sibling, "name", None) in {"h2", "h3"}:
                    break
                text = sibling.get_text(" ", strip=True) if hasattr(sibling, "get_text") else str(sibling).strip()
                if text:
                    chunks.append(text)
            return " ".join(chunks)[:1200] or None
    return None


def parse_detail(soup, url):
    title = next((h for h in soup.find_all("h1") if h.get_text(" ", strip=True).lower() != "kies op maat"), None)
    if not title:
        return None
    path = urlparse(url).path.strip("/").split("/")
    if len(path) < 4:
        return None
    # Limit the description to the first prose paragraphs after the title.
    paragraphs = []
    for node in title.next_elements:
        if getattr(node, "name", None) in {"h2", "h3"}:
            break
        if getattr(node, "name", None) == "p":
            value = node.get_text(" ", strip=True)
            if value:
                paragraphs.append(value)
        if len(" ".join(paragraphs)) > 900:
            break
    institution = None
    for logo in soup.select('img[alt*="logo"]'):
        name = logo.get("alt", "").removeprefix("logo ").strip()
        if name and name.lower() not in {"surf", "kies op maat"}:
            institution = name
            break
    result = {
        "id": f"{path[1]}-{path[-1]}", "name": title.get_text(" ", strip=True),
        "institution": institution, "description": " ".join(paragraphs)[:1200] or None,
        "location": labelled_value(soup, "Plaats"),
        "language": labelled_value(soup, "Voertaal"),
        "study_mode": labelled_value(soup, "Onderwijsvorm"),
        "period": labelled_value(soup, "Onderwijsperiodes"),
        "credits": labelled_value(soup, "Aantal EC"),
        "admission_requirements": section(soup, "Ingangseisen"),
        "tags": [], "url": url,
    }
    if result["period"] and "nog geen" in result["period"].lower():
        result["period"] = None
    return result


def scrape(limit, delay, pages, base_url=BASE):
    records = []
    visited = set()
    with requests.Session() as session:
        for page in range(1, pages + 1):
            listing_url = base_url + f"?type=m&page={page}"
            try:
                soup = fetch(session, listing_url)
            except requests.RequestException as exc:
                LOG.warning("Overzichtspagina %s mislukt: %s", page, type(exc).__name__)
                break
            links = detail_links(soup, base_url)
            if not links:
                LOG.warning("Geen detail-links gevonden op pagina %s; controleer HTML-selectors", page)
                break
            for url in links:
                if url in visited:
                    continue
                visited.add(url)
                time.sleep(delay)
                try:
                    record = parse_detail(fetch(session, url), url)
                    if record:
                        records.append(record)
                except requests.RequestException as exc:
                    LOG.warning("Detailpagina overgeslagen (%s): %s", url, type(exc).__name__)
                if len(records) >= limit:
                    return records
            time.sleep(delay)
    return records


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--output", type=Path, default=Path("data/minors.json"))
    parser.add_argument("--delay", type=float, default=1.5)
    parser.add_argument("--pages", type=int, default=20)
    parser.add_argument("--base-url", default=BASE, help="Overzichts-URL; standaard productieomgeving")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    if args.limit < 1 or args.delay < 1 or args.pages < 1:
        parser.error("limit, delay en pages moeten positief zijn; delay minimaal 1 seconde")
    records = scrape(args.limit, args.delay, args.pages, args.base_url)
    if not records:
        raise SystemExit("Geen records gevonden. Bestaand bestand blijft ongewijzigd.")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    LOG.info("%d records geschreven naar %s", len(records), args.output)


if __name__ == "__main__":
    main()
