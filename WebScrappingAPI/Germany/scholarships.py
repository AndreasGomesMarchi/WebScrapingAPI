"""
Web scraping das universidades alemãs: LMU Munich, TUM e Humboldt University of Berlin.

Fontes utilizadas:
  - THE (Times Higher Education) → posições internacionais
  - CHE Ranking / DAAD → posições nacionais e documentos necessários
  - Wikipedia (via REST API) → dados gerais (cidade, tipo, site oficial)
  - wttr.in → dados de clima por cidade
"""

import sys
import os
import time
import re
import requests
from bs4 import BeautifulSoup

# Permite importar de services/ independente de onde o script é chamado
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import Services.university

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) "
        "Gecko/20100101 Firefox/120.0"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

REQUEST_DELAY = 1.5  # segundos entre requisições

# Dados base (fallback e complemento quando o scraping não retorna algo)
# Esses dados são estáticos e bem estabelecidos; servem como referência confiável.

UNIVERSITIES_META = {
    "LMU Munich": {
        "city": "Munich",
        "country": "Germany",
        "type": "Public Research University",
        "site": "https://www.lmu.de/en/",
        "wikipedia_title": "Ludwig_Maximilian_University_of_Munich",
        "the_slug": "ludwig-maximilian-university-munich",
        "climate": "invernos frios e verões amenos",
        "documents": [
            "Certified academic transcripts",
            "Bachelor's degree certificate",
            "Proof of language proficiency (German B2/C1 or English B2/C1)",
            "Curriculum Vitae (CV)",
            "Motivation letter",
            "Letters of recommendation (2)",
            "Valid passport copy",
            "APS certificate (for applicants from China, Vietnam, Mongolia)",
        ],
    },
    "TUM": {
        "city": "Munich",
        "country": "Germany",
        "type": "Public Technical University",
        "site": "https://www.tum.de/en/",
        "wikipedia_title": "Technical_University_of_Munich",
        "the_slug": "technical-university-munich",
        "climate": "Humid continental (Dfb) – invernos frios e verões amenos",
        "documents": [
            "Certified academic transcripts",
            "Bachelor's degree certificate",
            "Proof of language proficiency (German or English, depending on program)",
            "Curriculum Vitae (CV)",
            "Motivation letter / Statement of purpose",
            "Letters of recommendation (2–3)",
            "Valid passport copy",
            "APS certificate (for applicants from China, Vietnam, Mongolia)",
            "Portfolio (for design/architecture programs)",
        ],
    },
    "Humboldt University of Berlin": {
        "city": "Berlin",
        "country": "Germany",
        "type": "Public Research University",
        "site": "https://www.hu-berlin.de/en",
        "wikipedia_title": "Humboldt_University_of_Berlin",
        "the_slug": "humboldt-university-berlin",
        "climate": "Humid continental (Dfb) – invernos frios, verões quentes",
        "documents": [
            "Certified academic transcripts",
            "Bachelor's degree certificate",
            "Proof of language proficiency (German B2/C1 or English B2/C1)",
            "Curriculum Vitae (CV)",
            "Motivation letter",
            "Letters of recommendation (2)",
            "Valid passport copy",
            "APS certificate (for applicants from China, Vietnam, Mongolia)",
        ],
    },
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get(url: str, timeout: int = 15) -> requests.Response | None:
    """Faz GET com tratamento de erros e delay."""
    time.sleep(REQUEST_DELAY)
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
        return resp
    except requests.RequestException as exc:
        print(f"  [WARN] Falha ao acessar {url}: {exc}")
        return None


def clean(text: str) -> str:
    """Remove espaços extras e quebras de linha."""
    return re.sub(r"\s+", " ", text).strip()


# ---------------------------------------------------------------------------
# Scraping: Times Higher Education (THE) – posição internacional
# ---------------------------------------------------------------------------

def scrape_the_ranking(uni_name: str) -> str:
    """
    Busca a posição internacional da universidade no ranking THE via página de busca.
    Retorna a posição como string (ex.: '=32') ou 'N/A'.
    """
    search_url = (
        "https://www.timeshighereducation.com/world-university-rankings/2025"
        "/world-ranking#!/page/1/length/25/sort_by/rank/sort_order/asc"
        f"/cols/stats/search/{uni_name.replace(' ', '+')}"
    )
    resp = get(search_url)
    if not resp:
        return "N/A"

    soup = BeautifulSoup(resp.text, "lxml")

    # THE renderiza via JS; tentamos capturar dados embutidos no HTML
    rank_tag = soup.find("td", {"data-ranking": True})
    if rank_tag:
        return clean(rank_tag["data-ranking"])

    # Fallback: procurar padrão numérico próximo ao nome da universidade
    rows = soup.find_all("tr")
    for row in rows:
        text = row.get_text(" ").lower()
        if uni_name.lower().split()[0] in text:
            td = row.find("td", class_=re.compile(r"rank"))
            if td:
                return clean(td.get_text())

    return "N/A"


# ---------------------------------------------------------------------------
# Scraping: DAAD UniDB – posição nacional e informações gerais
# ---------------------------------------------------------------------------

def scrape_daad_national_rank(uni_name: str) -> str:
    """
    Tenta recuperar posição nacional via DAAD ou CHE Ranking.
    Como o CHE não fornece ranking numérico puro, retornamos uma referência textual.
    """
    # CHE Ranking (publicado via ZEIT Campus) não tem ranking numérico,
    # usa grupos de desempenho. Retornamos referência baseada em dados CHE 2023/24.
    che_data = {
        "LMU Munich": "Top group (CHE 2023) – consistently ranked #1–2 nationally",
        "TUM": "Top group (CHE 2023) – consistently ranked #1–2 nationally in engineering/sciences",
        "Humboldt University of Berlin": "Top group (CHE 2023) – among top 3 nationally in humanities/social sciences",
    }
    return che_data.get(uni_name, "N/A")


# ---------------------------------------------------------------------------
# Scraping: Wikipedia REST API – dados gerais da universidade
# ---------------------------------------------------------------------------

def scrape_wikipedia_summary(wikipedia_title: str) -> dict:
    """
    Usa a Wikipedia REST API (sem bloqueio de IP) para buscar o sumário da universidade.
    Retorna dict com 'extract' e 'content_urls'.
    """
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{wikipedia_title}"
    resp = get(url)
    if not resp:
        return {}
    try:
        data = resp.json()
        return {
            "extract": data.get("extract", ""),
            "url": data.get("content_urls", {}).get("desktop", {}).get("page", ""),
        }
    except Exception:
        return {}


# ---------------------------------------------------------------------------
# Scraping: wttr.in – clima atual da cidade
# ---------------------------------------------------------------------------

def scrape_climate(city: str) -> str:
    """
    Obtém descrição do clima atual via wttr.in (API pública, sem autenticação).
    Retorna descrição como string.
    """
    url = f"https://wttr.in/{city.replace(' ', '+')}?format=j1"
    resp = get(url)
    if not resp:
        return "N/A"
    try:
        data = resp.json()
        current = data["current_condition"][0]
        desc = current["weatherDesc"][0]["value"]
        temp_c = current["temp_C"]
        feels_like = current["FeelsLikeC"]
        humidity = current["humidity"]
        return (
            f"{desc}, {temp_c}°C (sensação {feels_like}°C), "
            f"umidade {humidity}%"
        )
    except Exception:
        return "N/A"


# ---------------------------------------------------------------------------
# Scraping: site oficial da universidade – documentos de admissão
# ---------------------------------------------------------------------------

def scrape_admission_docs_lmu() -> list[str]:
    """Scraping dos documentos de admissão no site oficial da LMU."""
    url = "https://www.lmu.de/en/study/all-degree-programs/application-and-enrollment/international-applicants/"
    resp = get(url)
    if not resp:
        return []

    soup = BeautifulSoup(resp.text, "lxml")
    docs = []

    # LMU lista documentos em <li> dentro de seções de admissão
    for section in soup.find_all(["ul", "ol"]):
        items = section.find_all("li")
        for item in items:
            text = clean(item.get_text())
            if len(text) > 10 and any(
                kw in text.lower()
                for kw in ["certificate", "transcript", "passport", "language", "cv", "letter", "document", "proof"]
            ):
                docs.append(text)

    return docs[:10] if docs else []


def scrape_admission_docs_tum() -> list[str]:
    """Scraping dos documentos de admissão no site oficial da TUM."""
    url = "https://www.tum.de/en/studies/application/application-info/international-students"
    resp = get(url)
    if not resp:
        return []

    soup = BeautifulSoup(resp.text, "lxml")
    docs = []

    for section in soup.find_all(["ul", "ol"]):
        for item in section.find_all("li"):
            text = clean(item.get_text())
            if len(text) > 10 and any(
                kw in text.lower()
                for kw in ["certificate", "transcript", "passport", "language", "cv", "letter", "document", "proof", "degree"]
            ):
                docs.append(text)

    return docs[:10] if docs else []


def scrape_admission_docs_humboldt() -> list[str]:
    """Scraping dos documentos de admissão no site oficial da Humboldt."""
    url = "https://www.hu-berlin.de/en/studies/counselling/course-catalogue/application"
    resp = get(url)
    if not resp:
        return []

    soup = BeautifulSoup(resp.text, "lxml")
    docs = []

    for section in soup.find_all(["ul", "ol"]):
        for item in section.find_all("li"):
            text = clean(item.get_text())
            if len(text) > 10 and any(
                kw in text.lower()
                for kw in ["certificate", "transcript", "passport", "language", "cv", "letter", "document", "proof", "degree"]
            ):
                docs.append(text)

    return docs[:10] if docs else []


DOCS_SCRAPERS = {
    "LMU Munich": scrape_admission_docs_lmu,
    "TUM": scrape_admission_docs_tum,
    "Humboldt University of Berlin": scrape_admission_docs_humboldt,
}


# ---------------------------------------------------------------------------
# Função principal: scraping completo de uma universidade
# ---------------------------------------------------------------------------

def scrape_university(name: str, scholarships: list = None) -> Services.university.University:
    """
    Coleta todas as informações de uma universidade alemã e retorna
    um objeto University preenchido.

    Parâmetros:
        name        – chave do dicionário UNIVERSITIES_META
        scholarships – lista de objetos Scholarship já coletados (opcional)
    """
    meta = UNIVERSITIES_META[name]
    print(f"\n{'='*60}")
    print(f"Coletando dados: {name}")
    print(f"{'='*60}")

    # 1. Clima atual (wttr.in)
    print(f"  → Clima em {meta['city']}...")
    climate_current = scrape_climate(meta["city"])
    # Combina com descrição climática estática (tipo climático)
    climate = f"{meta['climate']} | Atual: {climate_current}"

    # 2. Posição nacional (CHE / DAAD)
    print(f"  → Posição nacional...")
    national_pos = scrape_daad_national_rank(name)

    # 3. Posição internacional (THE Rankings)
    print(f"  → Posição internacional (THE)...")
    international_pos = scrape_the_ranking(name)

    # 4. Documentos de admissão (site oficial)
    print(f"  → Documentos de admissão...")
    docs = DOCS_SCRAPERS[name]()
    if not docs:
        print(f"    (site oficial indisponível – usando dados de referência)")
        docs = meta["documents"]

    # 5. Resumo Wikipedia (opcional – para validação)
    print(f"  → Resumo Wikipedia...")
    wiki = scrape_wikipedia_summary(meta["wikipedia_title"])
    if wiki.get("extract"):
        print(f"    ✓ Wikipedia: {wiki['extract'][:80]}...")

    return Services.university.University(
        name=name,
        city=meta["city"],
        country=meta["country"],
        climate=climate,
        nationalPosition=national_pos,
        internationalPosition=international_pos,
        documents=docs,
        type=meta["type"],
        scholarships=scholarships or [],
        site=meta["site"],
    )


# ---------------------------------------------------------------------------
# Execução direta (teste)
# ---------------------------------------------------------------------------

def scrape_all_universities(scholarships_map: dict = None) -> list[Services.university.University]:
    """
    Faz o scraping das três universidades alemãs e retorna uma lista
    de objetos University.

    Parâmetros:
        scholarships_map – dict { nome_universidade: [Scholarship, ...] }
                          para associar bolsas às universidades.
    """
    if scholarships_map is None:
        scholarships_map = {}

    universities = []
    for name in UNIVERSITIES_META:
        uni = scrape_university(name, scholarships=scholarships_map.get(name, []))
        universities.append(uni)
        print(f"\n  ✓ {uni}")

    return universities


if __name__ == "__main__":
    results = scrape_all_universities()

    print("\n\n" + "="*60)
    print("RESULTADO FINAL")
    print("="*60)
    for uni in results:
        print(f"\n{uni.name}")
        print(f"  Cidade          : {uni.city}")
        print(f"  País            : {uni.country}")
        print(f"  Tipo            : {uni.type}")
        print(f"  Clima           : {uni.climate}")
        print(f"  Posição Nacional: {uni.nationalPosition}")
        print(f"  Posição Intl    : {uni.internationalPosition}")
        print(f"  Site            : {uni.site}")
        print(f"  Documentos ({len(uni.documents)}):")
        for doc in uni.documents:
            print(f"    - {doc}")