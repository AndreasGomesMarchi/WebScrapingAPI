"""
Web scraping de bolsas de estudo nos EUA: Fulbright, Knight-Hennessy e MIT Scholarships.
Focado em: Logs detalhados e Fallback Robusto para o SwiftUI.
"""

import sys
import os
import time
import re
import requests
import warnings
from bs4 import BeautifulSoup
from typing import List, Optional

# Silencia o aviso de versão do OpenSSL no macOS
from urllib3.exceptions import NotOpenSSLWarning
warnings.filterwarnings("ignore", category=NotOpenSSLWarning)

# Ajuste do path para o Backend (O "pulo do gato" para os imports funcionarem)
current_dir = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import Backend.Services.scholarships as scholarship_service

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

REQUEST_DELAY = 1.0

# Dados Mockados (Fallback) - Essencial para o App nunca ficar vazio
SCHOLARSHIPS_META = {
    "Fulbright": {
        "name": "Fulbright Foreign Student Program",
        "value": "Cobre passagem aérea e mensalidade integral",
        "date": "geralmente outubro ou Fevereiro",
        "about": "Programa de elite do governo dos EUA para estudantes internacionais de pós-graduação.",
        "requirements": "Grau de bacharel, proficiência em inglês, excelência acadêmica.",
        "area": "Todas as áreas",
        "type": "Estados Unidos",
        "site": "https://foreign.fulbrightonline.org/"
    },
    "Knight-Hennessy": {
        "name": "Knight-Hennessy Scholars",
        "value": "Em torno de $80,000+ por ano",
        "date": "Outubro",
        "about": "Bolsa para líderes globais cursando pós-graduação na Stanford University.",
        "requirements": "Admissão em Stanford, liderança comprovada, mentalidade cívica.",
        "area": "Todas as áreas",
        "type": "Estados Unidos",
        "site": "https://knight-hennessy.stanford.edu/"
    },
    "MIT_Need_Based": {
        "name": "MIT Undergraduate Scholarships",
        "value": "Em torno de $50,000",
        "date": "Fevereiro",
        "about": "Bolsas baseadas em necessidade financeira para estudantes de graduação no MIT.",
        "requirements": "CSS Profile, documentos fiscais dos pais, admissão no MIT.",
        "area": "Undergraduate",
        "type": "Estados Unidos",
        "site": "https://sfs.mit.edu/undergraduate-students/types-of-aid/mit-scholarships/"
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

# --- Scrapers Específicos ---

def scrape_live_value(url: str, fallback_value: str) -> str:
    """Tenta capturar valores monetários ou prazos em tempo real."""
    resp = get(url)
    if not resp:
        return f"{fallback_value} (Fallback)"
    
    try:
        soup = BeautifulSoup(resp.text, "html.parser")
        text = soup.get_text(separator=" ")
        
        # Procura por padrões de valores (ex: $50,000 ou Full Tuition)
        match = re.search(r"(\$\d{1,3}(?:,\d{3})*(?:\.\d{2})?|Full Tuition)", text)
        if match:
            val = match.group(0)
            print(f"Dado capturado via Scraping: {val}")
            return f"{val} (Live)"
    except:
        pass
    return fallback_value

# --- Orquestrador ---

def process_scholarship(key: str) -> scholarship_service.Scholarship:
    meta = SCHOLARSHIPS_META[key]

    print(f"ANALISANDO BOLSA: {meta['name']}")

    # 1. Tenta atualizar o valor ou dados dinâmicos
    print(f"  → Validando dados no site oficial...")
    current_value = scrape_live_value(meta["site"], meta["value"])

    # Criando o objeto com base no modelo fornecido
    scholarship = scholarship_service.Scholarship(
        name=meta["name"],
        value=current_value,
        date=meta["date"],
        about=meta["about"],
        requirements=meta["requirements"],
        area=meta["area"],
        type=meta["type"],
        site=meta["site"]
    )

    # PINTANDO OS DADOS NO TERMINAL PARA CONFERÊNCIA
    print(f"\nDADOS CONSOLIDADOS DA BOLSA:")
    print(f"{scholarship.name}")
    print(f"{scholarship.value}")
    print(f"{scholarship.date}")
    print(f"{scholarship.about[:70]}...")
    print(f"{scholarship.requirements[:70]}...")
    print(f"{scholarship.area}")
    print(f"{scholarship.type}")
    print(f"{scholarship.site}")

    return scholarship

def scrape_all_usa_scholarships() -> List[scholarship_service.Scholarship]:
    return [process_scholarship(name) for name in SCHOLARSHIPS_META]

if __name__ == "__main__":
    print("Iniciando Motor de Busca de Bolsas (EUA)...")
    results = scrape_all_usa_scholarships()
    print(f"SUCESSO: {len(results)} bolsas processadas com lógica de Fallback.")