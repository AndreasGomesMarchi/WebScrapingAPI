import requests
from bs4 import BeautifulSoup
from Backend.Services.university import University


def scrape_mit() -> University:
    """
    Faz o scraping do MIT e retorna um objeto University.
    Dados estáticos (nome, cidade, tipo) estão hardcoded pois não mudam.
    Apenas a taxa de aceitação é buscada dinamicamente.
    """

    acceptance_rate = _get_acceptance_rate()

    return University(
        name="Massachusetts Institute of Technology",
        city="Cambridge",
        country="United States",
        climate="Continental",
        nationalPosition=3,         # será substituído por scraper de rankings
        internationalPosition=1,    # será substituído por scraper de rankings
        documents=[
            "High school transcript",
            "SAT or ACT scores",
            "English proficiency (TOEFL/IELTS)",
            "Letters of recommendation",
            "Personal essays",
        ],
        type="private",
        scholarships=[
            "MIT Scholarship",
            "Fulbright Foreign Student Program",
            "MISTI Global Seed Funds",
        ],
        site="https://web.mit.edu",
        acceptanceRate=acceptance_rate,
    )


def _get_acceptance_rate() -> float | None:
    """Busca a taxa de aceitação na página de estatísticas do MIT."""
    try:
        url = "https://mitadmissions.org/apply/process/stats/"
        headers = {"User-Agent": "Mozilla/5.0 (compatible; ExchangeApp/1.0)"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        text = soup.get_text(separator=" ").lower()

        import re
        pattern = r"acceptance\s+rate[:\s]+(\d+[\.,]\d+)\s*%"
        match = re.search(pattern, text)

        if not match:
            pattern_alt = r"(\d+[\.,]\d+)\s*%\s+of\s+(applicants|students)"
            match = re.search(pattern_alt, text)

        if match:
            rate_str = match.group(1).replace(",", ".")
            return round(float(rate_str) / 100, 4)

    except Exception as e:
        print(f"[MIT] Falha ao buscar acceptance rate: {e}")

    return None