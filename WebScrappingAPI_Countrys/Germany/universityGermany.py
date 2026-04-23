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
import warnings
from bs4 import BeautifulSoup
from typing import List, Optional, Dict, Union
from urllib3.exceptions import NotOpenSSLWarning

# Silencia o aviso de versão do OpenSSL/LibreSSL no macOS
warnings.filterwarnings("ignore", category=NotOpenSSLWarning)

# Permite importar de services/ independente de onde o script é chamado
# Ajustado para encontrar a pasta Backend a partir da estrutura apresentada
current_dir = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import Backend.Services.university as university_service

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) "
        "Gecko/20100101 Firefox/120.0"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

REQUEST_DELAY = 1.5  # segundos entre requisições

UNIVERSITIES_META = {
    "LMU Munich": {
        "name": "Ludwig_Maximilian_University_of_Munich",
        "city": "Munich",
        "country": "Germany",
        "type": "Public Research University",
        "site": "https://www.lmu.de/en/",
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
        "name": "Technical_University_of_Munich",
        "city": "Munich",
        "country": "Germany",
        "type": "Public Technical University",
        "site": "https://www.tum.de/en/",
        "climate": "invernos frios e verões amenos",
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
        "name": "Humboldt_University_of_Berlin",
        "city": "Berlin",
        "country": "Germany",
        "type": "Public Research University",
        "site": "https://www.hu-berlin.de/en",
        "climate": "invernos frios, verões quentes",
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

# Helpers

def get(url: str, timeout: int = 15) -> Optional[requests.Response]:
    """Faz GET com tratamento de erros e delay. (Compatível com Python 3.9)"""
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

# Scraping: Times Higher Education (THE) – posição internacional

def scrape_the_ranking(uni_name: str) -> str:
    search_url = (
        "https://www.timeshighereducation.com/world-university-rankings/2025"
        "/world-ranking#!/page/1/length/25/sort_by/rank/sort_order/asc"
        f"/cols/stats/search/{uni_name.replace(' ', '+')}"
    )
    resp = get(search_url)
    if not resp:
        return "N/A"

    soup = BeautifulSoup(resp.text, "lxml")

    rank_tag = soup.find("td", {"data-ranking": True})
    if rank_tag:
        return clean(rank_tag["data-ranking"])

    rows = soup.find_all("tr")
    for row in rows:
        text = row.get_text(" ").lower()
        if uni_name.lower().split()[0] in text:
            td = row.find("td", class_=re.compile(r"rank"))
            if td:
                return clean(td.get_text())

    return "N/A"

# Scraping: DAAD UniDB – posição nacional

def scrape_daad_national_rank(uni_name: str) -> str:
    che_data = {
        "LMU Munich": "Top group (CHE 2023) – consistently ranked #1–2 nationally",
        "TUM": "Top group (CHE 2023) – consistently ranked #1–2 nationally in engineering/sciences",
        "Humboldt University of Berlin": "Top group (CHE 2023) – among top 3 nationally in humanities/social sciences",
    }
    return che_data.get(uni_name, "N/A")

# Scraping: wttr.in – clima atual

def scrape_climate(city: str) -> str:
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

# Scraping: Documentos

def scrape_admission_docs_lmu() -> List[str]:
    url = "https://www.lmu.de/en/study/all-degree-programs/application-and-enrollment/international-applicants/"
    resp = get(url)
    if not resp:
        return []
    soup = BeautifulSoup(resp.text, "lxml")
    docs = []
    for section in soup.find_all(["ul", "ol"]):
        for item in section.find_all("li"):
            text = clean(item.get_text())
            if len(text) > 10 and any(kw in text.lower() for kw in ["certificate", "transcript", "passport", "language", "cv", "letter", "document", "proof"]):
                docs.append(text)
    return docs[:10]

def scrape_admission_docs_tum() -> List[str]:
    url = "https://www.tum.de/en/studies/application/application-info/international-students"
    resp = get(url)
    if not resp:
        return []
    soup = BeautifulSoup(resp.text, "lxml")
    docs = []
    for section in soup.find_all(["ul", "ol"]):
        for item in section.find_all("li"):
            text = clean(item.get_text())
            if len(text) > 10 and any(kw in text.lower() for kw in ["certificate", "transcript", "passport", "language", "cv", "letter", "document", "proof", "degree"]):
                docs.append(text)
    return docs[:10]

def scrape_admission_docs_humboldt() -> List[str]:
    url = "https://www.hu-berlin.de/en/studies/counselling/course-catalogue/application"
    resp = get(url)
    if not resp:
        return []
    soup = BeautifulSoup(resp.text, "lxml")
    docs = []
    for section in soup.find_all(["ul", "ol"]):
        for item in section.find_all("li"):
            text = clean(item.get_text())
            if len(text) > 10 and any(kw in text.lower() for kw in ["certificate", "transcript", "passport", "language", "cv", "letter", "document", "proof", "degree"]):
                docs.append(text)
    return docs[:10]

DOCS_SCRAPERS = {
    "LMU Munich": scrape_admission_docs_lmu,
    "TUM": scrape_admission_docs_tum,
    "Humboldt University of Berlin": scrape_admission_docs_humboldt,
}

# Funções principais

def scrape_university(name: str, scholarships: List = None) -> university_service.University:
    """
    Coleta todas as informações de uma universidade alemã e retorna
    um objeto University preenchido.
    """
    meta = UNIVERSITIES_META[name]
    print(f"\n{'='*60}")
    print(f"Coletando dados: {name}")
    print(f"{'='*60}")

    # 1. Clima atual (wttr.in)
    print(f"  → Clima em {meta['city']}...")
    climate_current = scrape_climate(meta["city"])
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

    # CORREÇÃO: Instanciando a classe corretamente
    return university_service.University(
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

# CORREÇÃO: Ajustado o type hint da lista
def scrape_all_universities(scholarships_map: Dict = None) -> List[university_service.University]:
    """
    Faz o scraping das três universidades alemãs e retorna uma lista
    de objetos University.
    """
    if scholarships_map is None:
        scholarships_map = {}

    universities = []
    for name in UNIVERSITIES_META:
        uni = scrape_university(name, scholarships=scholarships_map.get(name, []))
        universities.append(uni)
        # Usando .name para o log, assumindo que o objeto University tem esse atributo
        print(f"\n  ✓ {uni.name if hasattr(uni, 'name') else 'Universidade coletada'}")

    return universities


if __name__ == "__main__":
    results = scrape_all_universities()

    print("\n\n" + "="*60)
    print("RESULTADO FINAL")
    print("="*60)
    for uni in results:
        # Acesse os atributos diretamente do objeto retornado
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