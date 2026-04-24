"""
Web scraping de bolsas de estudo na Alemanha: DAAD, Humboldt e Deutschlandstipendium.
Focado em: Logs detalhados, integração com DAAD e Fallback Robusto.
"""

# Esse WebScrapping nao vai funcionar pois o DAAD tem as informacoes em JS, precisando de outra biblioteca para funcionar (como Selenium ou Playwright). O código abaixo é um exemplo de como seria a estrutura, mas o scraper live do DAAD não funcionará sem ajustes.
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

# Ajuste do path para o Backend
current_dir = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import Backend.Services.scholarships as scholarship_service

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

REQUEST_DELAY = 2.0

# URL de busca do DAAD (bolsas para Alemanha)
DAAD_URL = "https://www2.daad.de/deutschland/stipendium/datenbank/en/21148-scholarship-database/"

# Dados Mockados (Fallback) - Se o DAAD falhar, seu App continua funcional
SCHOLARSHIPS_META = {
    "DAAD_Master": {
        "name": "DAAD Study Scholarship (Master's)",
        "value": "Em torno de €934/mês + auxílio viagem",
        "date": "15 de Novembro",
        "about": "Suporte para graduados estrangeiros completarem um mestrado integral na Alemanha.",
        "requirements": "Bacharelado completo, 2 anos de experiência profissional (para alguns cursos), Inglês ou Alemão B2.",
        "area": "Todas as áreas",
        "type": "Alemanha",
        "site": "https://www2.daad.de/deutschland/stipendium/datenbank/en/21148-scholarship-database/"
    },
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

# --- Scraper Live (DAAD) ---

def scrape_daad_live_count() -> str:
    """Tenta verificar quantas bolsas estão ativas hoje no portal DAAD."""
    resp = get(DAAD_URL)
    if not resp:
        return "Disponibilidade sob consulta"
    
    try:
        soup = BeautifulSoup(resp.text, "html.parser")
        # Tenta achar o contador de resultados do DAAD
        count_tag = soup.find(class_=re.compile(r"result-count|total-results", re.I))
        if count_tag:
            count = clean(count_tag.get_text())
            print(f"DAAD Live: {count} programas encontrados.")
            return f"Ativa ({count} opções)"
    except:
        pass
    return "Ativa (Portal DAAD)"

# --- Orquestrador ---

def process_germany_scholarship(key: str) -> scholarship_service.Scholarship:
    meta = SCHOLARSHIPS_META[key]

    print(f"ANALISANDO BOLSA ALEMÃ: {meta['name']}")

    # 1. Tenta validar status ao vivo se for DAAD
    status_ou_valor = meta["value"]
    if "DAAD" in meta["name"]:
        print(f"  → Checando portal DAAD em tempo real...")
        status_live = scrape_daad_live_count()
        if "opções" in status_live:
            status_ou_valor = f"{meta['value']} | {status_live}"

    # Criando o objeto Scholarship
    scholarship = scholarship_service.Scholarship(
        name=meta["name"],
        value=status_ou_valor,
        date=meta["date"],
        about=meta["about"],
        requirements=meta["requirements"],
        area=meta["area"],
        type=meta["type"],
        site=meta["site"]
    )

    # PINTANDO OS DADOS NO TERMINAL (Debugging visual)
    print(f"\nDADOS CONSOLIDADOS (GERMANY):")
    print(f"{scholarship.name}")
    print(f"{scholarship.value}")
    print(f"{scholarship.date}")
    print(f"{scholarship.about[:75]}...")
    print(f"{scholarship.area}")
    print(f"{scholarship.type}")
    print(f"{scholarship.site}")

    return scholarship

def scrape_all_germany_scholarships() -> List[scholarship_service.Scholarship]:
    return [process_germany_scholarship(key) for key in SCHOLARSHIPS_META]

if __name__ == "__main__":
    print("Iniciando Motor de Busca de Bolsas (ALEMANHA)...")
    results = scrape_all_germany_scholarships()
    print(f"SUCESSO: {len(results)} bolsas alemãs processadas.")