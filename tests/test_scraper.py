from bs4 import BeautifulSoup

from scraper.scrape_kiesopmaat import detail_links, parse_detail


def test_detail_parser_skips_site_heading_and_unknown_period():
    html = '''<h1>Kies op maat</h1><a href="/modules/che/-/144244/">Open</a>
    <h1>Ondernemen</h1><p>Leer ondernemen.</p><h2>Ingangseisen</h2><p>Propedeuse.</p>
    <div>Onderwijsperiodes : Nog geen onderwijsperiode bekend</div>
    <img alt="logo Surf"><img alt="logo Christelijke Hogeschool Ede">'''
    soup = BeautifulSoup(html, "html.parser")
    url = "https://acceptatie.kiesopmaat.nl/modules/che/-/144244/"
    assert detail_links(soup, "https://acceptatie.kiesopmaat.nl/modules/") == [url]
    record = parse_detail(soup, url)
    assert record["name"] == "Ondernemen"
    assert record["institution"] == "Christelijke Hogeschool Ede"
    assert record["period"] is None
