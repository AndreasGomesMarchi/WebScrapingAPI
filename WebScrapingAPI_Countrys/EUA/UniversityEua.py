"""
Web scraping das universidades americanas: MIT, Harvard e Stanford.
Focado em: Logs detalhados e Fallback Robusto.
"""

import sys
import os
import time
import re
import requests
import warnings
from bs4 import BeautifulSoup
from typing import List, Optional, Dict

# Silencia o aviso de versão do OpenSSL no macOS
from urllib3.exceptions import NotOpenSSLWarning
warnings.filterwarnings("ignore", category=NotOpenSSLWarning)

# Ajuste do path para o Backend
current_dir = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import Backend.Services.university as university_service

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

REQUEST_DELAY = 1.0

# Dados Mockados (Fallback)
UNIVERSITIES_META = {
    "MIT": {
        "name": "Massachusetts Institute of Technology",
        "city": "Cambridge",
        "climate_fallback": "Invernos rigorosos com neve, verões quentes",
        "nationalPosition": 3,
        "internationalPosition": 1,
        "documents": ["High school transcript", "SAT or ACT scores", "Letters of recommendation"],
        "type": "Private Research University",
        "acceptanceRate": 0.04,
        "site": "https://web.mit.edu",
    },
    "Harvard": {
        "name": "Harvard University",
        "city": "Cambridge",
        "climate_fallback": "Invernos rigorosos com neve, verões quentes",
        "nationalPosition": 1,
        "internationalPosition": 2,
        "documents": ["School Report", "SAT or ACT scores", "Teacher evaluations"],
        "type": "Private Research University",
        "acceptanceRate": 0.03,
        "site": "https://www.harvard.edu",
    },
    "Stanford": {
        "name": "Stanford University",
        "city": "Stanford",
        "climate_fallback": "Clima mediterrâneo, verões secos e invernos amenos",
        "nationalPosition": 4,
        "internationalPosition": 3,
        "documents": ["Official transcript", "Letters of recommendation", "SAT or ACT scores"],
        "type": "Private Research University",
        "acceptanceRate": 0.045,  
        "site": "https://www.stanford.edu",
    }
}

# --- Helpers ---

def get(url: str) -> Optional[requests.Response]:
    time.sleep(REQUEST_DELAY)
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        return resp
    except Exception as exc:
        print(f"[ERRO DE REQUISIÇÃO] {url}: {exc}")
        return None

def clean(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()

# --- Scrapers com Lógica de Fallback Integrada ---

def scrape_climate(city: str, fallback_text: str) -> str:
    url = f"https://wttr.in/{city.replace(' ', '+')}?format=j1"
    resp = get(url)
    if not resp:
        print(f"Usando clima mockado para {city}")
        return f"{fallback_text} (Dados de Fallback)"
    try:
        data = resp.json()
        current = data["current_condition"][0]
        desc = current["weatherDesc"][0]["value"]
        temp_c = current["temp_C"]
        return f"{desc}, {temp_c}°C (Live)"
    except:
        return fallback_text

def scrape_mit_acceptance_rate(fallback: float) -> float:
    url = "https://mitadmissions.org/apply/process/stats/"
    resp = get(url)
    if not resp: return fallback
    try:
        soup = BeautifulSoup(resp.text, "html.parser")
        text = soup.get_text(separator=" ").lower()
        match = re.search(r"acceptance\s+rate[:\s]+(\d+[\.,]\d+)\s*%", text)
        if match:
            val = round(float(match.group(1).replace(",", ".")) / 100, 4)
            print(f"Taxa capturada via Scraping: {val}")
            return val
    except:
        pass
    print(f"Usando taxa mockada: {fallback}")
    return fallback

# --- Orquestrador ---

def scrape_university(key: str) -> university_service.University:
    meta = UNIVERSITIES_META[key]
    print(f"\n{'='*60}")
    print(f"PROCESSANDO: {meta['name']}")
    print(f"{'='*60}")

    # 1. Clima
    print(f"  → Buscando clima...")
    climate = scrape_climate(meta["city"], meta["climate_fallback"])

    # 2. Taxa de Aceitação (Exemplo MIT)
    print(f"  → Buscando taxa de aceitação...")
    if key == "MIT":
        acceptance_rate = scrape_mit_acceptance_rate(meta["acceptanceRate"])
    else:
        # Para Harvard/Stanford você pode implementar os scrapers depois
        acceptance_rate = meta["acceptanceRate"]
        print(f"Usando taxa mockada (Scraper pendente)")

    # 3. Rankings (Mockados por enquanto, mas prontos para expansão)
    national_pos = meta["nationalPosition"]
    international_pos = meta["internationalPosition"]

    # Criando o objeto final
    uni = university_service.University(
        name=meta["name"],
        city=meta["city"],
        climate=climate,
        nationalPosition=national_pos,
        internationalPosition=international_pos,
        documents=meta["documents"],
        type=meta["type"],
        scholarships=[], 
        acceptanceRate=acceptance_rate, 
        site=meta["site"],
    )

    # PINTANDO OS DADOS NO TERMINAL PARA CONFERÊNCIA
    print(f"\nDADOS CONSOLIDADOS:")
    print(f"{uni.city}")
    print(f"{uni.climate}")
    print(f"{uni.nationalPosition}")
    print(f"{uni.internationalPosition}")
    print(f"{uni.acceptanceRate * 100}%")
    print(f"{uni.type}")
    print(f"{', '.join(uni.documents[:3])}")
    print(f"{uni.site}")

    return uni

def scrape_all_usa_universities() -> List[university_service.University]:
    return [scrape_university(name) for name in UNIVERSITIES_META]

if __name__ == "__main__":
    print("Iniciando Teste de Scraping EUA...")
    results = scrape_all_usa_universities()
    print(f"\n TESTE CONCLUÍDO: {len(results)} universidades processadas.")