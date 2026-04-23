import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from WebScrappingAPI_Countrys.Germany.scholarship import scrape_scholarships

# Exempo básico
def test_scrape_returns_list():
    results = scrape_scholarships(max_scholarships=3)

    assert isinstance(results, list)
    assert len(results) > 0


# Como os dados estão estruturados
def test_scholarship_fields():
    results = scrape_scholarships(max_scholarships=1)
    s = results[0]

    assert hasattr(s, "name")
    assert hasattr(s, "value")
    assert hasattr(s, "date")
    assert hasattr(s, "requirements")


# Scraping mais bruto
def test_daad_listing():
    raw = scrape_scholarships(max_pages=1)

    assert isinstance(raw, list)
    assert len(raw) > 0
    assert "name" in raw[0]