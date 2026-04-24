"""
Web scraping das universidades alemãs: LMU Munich, TUM e Humboldt University of Berlin.
Focado em: Logs detalhados, Fallback Robusto e integração com o Backend.
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

# Dados Mockados (Fallback) - Garantia de funcionamento do App
UNIVERSITIES_META = {
    "LMU Munich": {
        "name": "Ludwig Maximilian University of Munich",
        "city": "Munich",
        "climate_fallback": "Invernos frios e verões amenos",
        "nationalPosition": 2,
        "internationalPosition": 38,
        "documents": ["Transcrições Acadêmicas", "Proeficiência em Inglês ou Alemão"],
        "type": "Universidade de Pesquisa Pública",
        "acceptanceRate": 0.10,
        "site": "https://www.lmu.de/en/",
    },
    "TUM": {
        "name": "Technical University of Munich",
        "city": "Munich",
        "climate_fallback": "Invernos frios e verões amenos",
        "nationalPosition": 1,
        "internationalPosition": 28,
        "documents": ["Transcrições Acadêmicas", "Carta de Motivação", "Currículo", "Proeficiência em Inglês ou Alemão"],
        "type": "Universidade Técnica Pública",
        "acceptanceRate": 0.8,
        "site": "https://www.tum.de/en/",
    },
    "Humboldt Berlin": {
        "name": "Humboldt University of Berlin",
        "city": "Berlin",
        "climate_fallback": "Invernos frios, verões quentes",
        "nationalPosition": 3,
        "internationalPosition": 61,
        "documents": ["Degree certificate Certificate", "Proeficiência em Inglês ou Alemão", "Cópia do passaporte"],
        "type": "Universidade de Pesquisa Pública",
        "acceptanceRate": 0.18,
        "site": "https://www.hu-berlin.de/en",
    }
}

# --- Helpers ---

def get(url: str) -> Optional[requests.Response]:
    time.sleep(REQUEST_DELAY)
    try:
        resp = requests.get(url, headers=HEADERS, timeout=12)
        resp.raise_for_status()
        return resp
    except Exception as exc:
        print(f"[ERRO DE REQUISIÇÃO] {url}: {exc}")
        return None

def clean(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()

# --- Scrapers Integrados ---

def scrape_climate(city: str, fallback_text: str) -> str:
    url = f"https://wttr.in/{city.replace(' ', '+')}?format=j1"
    resp = get(url)
    if not resp:
        return f"{fallback_text} (Fallback)"
    try:
        data = resp.json()
        current = data["current_condition"][0]
        temp_c = current["temp_C"]
        desc = current["weatherDesc"][0]["value"]
        return f"{desc}, {temp_c}°C (Live)"
    except:
        return fallback_text

def scrape_live_documents(url: str, fallback_docs: List[str]) -> List[str]:
    """Tenta capturar documentos da página oficial de admissão."""
    resp = get(url)
    if not resp:
        return fallback_docs
    
    try:
        soup = BeautifulSoup(resp.text, "html.parser")
        docs = []
        # Procura por itens de lista que mencionem documentos comuns
        for item in soup.find_all("li"):
            text = clean(item.get_text())
            if any(kw in text.lower() for kw in ["certificate", "transcript", "cv", "passport", "proof"]):
                if 10 < len(text) < 100: # Evita pegar parágrafos gigantes
                    docs.append(text)
        
        if len(docs) > 2:
            print(f"{len(docs)} documentos capturados via Scraping.")
            return docs[:8]
    except:
        pass
    return fallback_docs

# --- Orquestrador ---

def scrape_germany_university(key: str) -> university_service.University:
    meta = UNIVERSITIES_META[key]
    print(f"PROCESSANDO: {meta['name']}")

    # 1. Clima
    print(f"  → Buscando clima em {meta['city']}...")
    climate = scrape_climate(meta["city"], meta["climate_fallback"])

    # 2. Documentos ao vivo
    print(f"  → Sincronizando documentos de admissão...")
    live_docs = scrape_live_documents(meta["site"], meta["documents"])

    # Criando o objeto University (seguindo sua classe Backend)
    uni = university_service.University(
        name=meta["name"],
        city=meta["city"],
        climate=climate,
        nationalPosition=meta["nationalPosition"],
        internationalPosition=meta["internationalPosition"],
        documents=live_docs,
        type=meta["type"],
        scholarships=[], 
        acceptanceRate=meta["acceptanceRate"],
        site=meta["site"],
    )

    # PINTANDO OS DADOS NO TERMINAL
    print(f"\nDADOS CONSOLIDADOS:")
    print(f"{uni.name}")
    print(f"{uni.city}")
    print(f"{uni.climate}")
    print(f"Nacional: {uni.nationalPosition}")
    print(f"Internacional: {uni.internationalPosition}")
    print(f"{uni.type}")
    print(f"{', '.join(uni.documents[:3])}...")
    print(f"{uni.site}")

    return uni

def scrape_all_germany_universities() -> List[university_service.University]:
    return [scrape_germany_university(name) for name in UNIVERSITIES_META]

if __name__ == "__main__":
    print("Iniciando Motor de Busca: Universidades Alemanha...")
    results = scrape_all_germany_universities()
    print(f"SUCESSO: {len(results)} universidades alemãs integradas.")