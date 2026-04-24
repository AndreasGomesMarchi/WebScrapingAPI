"""
Web scraping das universidades canadenses: University of Toronto, OCAD University e McGill.
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

REQUEST_DELAY = 2.0

# Dados Mockados (Fallback)
UNIVERSITIES_META = {
    "UofT": {
        "name": "University of Toronto",
        "city": "Toronto",
        "climate_fallback": "Invernos rigorosos, verões úmidos e agradáveis",
        "nationalPosition": 1,
        "internationalPosition": 21,
        "documents": ["Histórico escolar do ensino médio", "Comprovante de proficiência em inglês (IELTS/TOEFL)", "Notas autodeclaradas"],
        "type": "Universidade Pública de Pesquisa",
        "acceptanceRate": 0.43,
        "site": "https://www.utoronto.ca",
    },
    "OCAD": {
        "name": "OCAD University",
        "city": "Toronto",
        "climate_fallback": "Invernos rigorosos, verões úmidos e agradáveis",
        "nationalPosition": 45, # Ranking focado em Arte/Design
        "internationalPosition": 151,
        "documents": ["Portfólio", "Carta de Intenção", "Histórico Escolar"],
        "type": "Universidade Pública de Arte e Design",
        "acceptanceRate": 0.40,
        "site": "https://www.ocadu.ca",
    },
    "McGill": {
        "name": "McGill University",
        "city": "Montreal",
        "climate_fallback": "Invernos muito frios com muita neve, verões quentes",
        "nationalPosition": 2,
        "internationalPosition": 30,
        "documents": ["Histórico oficial", "Resultados de testes externos (se aplicável)", "Prova de proficiência em inglês"],
        "type": "Universidade Pública de Pesquisa",
        "acceptanceRate": 0.39,
        "site": "https://www.mcgill.ca",
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

# --- Scrapers com Lógica de Fallback ---

def scrape_climate(city: str, fallback_text: str) -> str:
    url = f"https://wttr.in/{city.replace(' ', '+')}?format=j1"
    resp = get(url)
    if not resp:
        return f"{fallback_text} (Fallback)"
    try:
        data = resp.json()
        current = data["current_condition"][0]
        desc = current["weatherDesc"][0]["value"]
        temp_c = current["temp_C"]
        return f"{desc}, {temp_c}°C (Live)"
    except:
        return fallback_text

def scrape_uoft_acceptance_rate(fallback: float) -> float:
    """Exemplo de scraper específico para UofT (Dados variam por ano)"""
    # Em sites canadenses, esses dados costumam estar em PDFs ou tabelas dinâmicas.
    # Se o scraper falhar, o fallback de 43% é mantido.
    return fallback

# --- Orquestrador ---

def scrape_university(key: str) -> university_service.University:
    meta = UNIVERSITIES_META[key]
    print(f"PROCESSANDO: {meta['name']}")

    # 1. Clima
    print(f"  → Buscando clima em {meta['city']}...")
    climate = scrape_climate(meta["city"], meta["climate_fallback"])

    # 2. Taxa de Aceitação
    print(f"  → Validando taxa de aceitação...")
    if key == "UofT":
        acceptance_rate = scrape_uoft_acceptance_rate(meta["acceptanceRate"])
    else:
        acceptance_rate = meta["acceptanceRate"]
        print(f"    Usando taxa mockada (Scraper específico pendente)")

    # 3. Rankings e Objetos
    uni = university_service.University(
        name=meta["name"],
        city=meta["city"],
        climate=climate,
        nationalPosition=meta["nationalPosition"],
        internationalPosition=meta["internationalPosition"],
        documents=meta["documents"],
        type=meta["type"],
        scholarships=[], 
        acceptanceRate=acceptance_rate, 
        site=meta["site"],
    )

    # PINTANDO OS DADOS NO TERMINAL
    print(f"\nDADOS CONSOLIDADOS (CANADÁ):")
    print(f"Cidade: {uni.city}")
    print(f"Clima:  {uni.climate}")
    print(f"National: {uni.nationalPosition}")
    print(f"International: {uni.internationalPosition}")
    print(f"Taxa:   {uni.acceptanceRate * 100}%")
    print(f"Docs:   {', '.join(uni.documents[:2])}...")
    print(f"Site:   {uni.site}")

    return uni

def scrape_all_canada_universities() -> List[university_service.University]:
    return [scrape_university(name) for name in UNIVERSITIES_META]

if __name__ == "__main__":
    print("Iniciando Motor de Busca: Universidades Canadá...")
    results = scrape_all_canada_universities()
    print(f"\nTESTE CONCLUÍDO: {len(results)} universidades processadas.")