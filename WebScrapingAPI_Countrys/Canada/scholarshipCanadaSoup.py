"""
Web scraping de bolsas de estudo no Canadá: University of Toronto, OCAD e McGill.
Focado em: Logs detalhados, Fallback Robusto e integração com o Backend.
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

REQUEST_DELAY = 1.0

# Dados Mockados (Fallback) - Essencial para o App nunca ficar vazio
SCHOLARSHIPS_META = {
    "LesterB_Pearson": {
        "name": "Lester B. Pearson International Scholarship (UofT)",
        "value": "Cobre mensalidade, livros e residência integral por 4 anos",
        "date": "Janeiro",
        "about": "A bolsa mais prestigiada da University of Toronto para estudantes internacionais de graduação.",
        "requirements": "Excelência acadêmica, criatividade, liderança, nomeação pela escola secundária.",
        "area": "Undergraduate",
        "type": "Canadá",
        "site": "https://future.utoronto.ca/pearson/about/"
    },
    "OCAD_International": {
        "name": "OCAD University International Student Scholarship",
        "value": "Varia entre $1,000 e $5,000",
        "date": "Sem prazo específico (Entrada automática)",
        "about": "Bolsas de entrada para novos estudantes internacionais de artes e design na OCAD.",
        "requirements": "Admissão na OCAD, portfólio de alta qualidade, excelência acadêmica anterior.",
        "area": "Arts & Design",
        "type": "Canadá",
        "site": "https://www.ocadu.ca/student-services/financial-aid/scholarships-awards"
    },
    "McGill_McCall_MacBain": {
        "name": "McCall MacBain Scholarships (McGill)",
        "value": "Mensalidade integral + $2,000 CAD por mês",
        "date": "Agosto a Setembro",
        "about": "Bolsa de liderança para mestrado ou cursos profissionais na McGill University.",
        "requirements": "Caráter excepcional, engajamento comunitário, potencial de liderança.",
        "area": "Graduate",
        "type": "Canadá",
        "site": "https://mccallmacbainscholars.org/"
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
    """Tenta capturar valores monetários (CAD$) ou palavras-chave em tempo real."""
    resp = get(url)
    if not resp:
        return f"{fallback_value} (Fallback)"
    
    try:
        soup = BeautifulSoup(resp.text, "html.parser")
        text = soup.get_text(separator=" ")
        
        # Procura por padrões de valores canadenses (ex: CAD$ 20,000 ou $15,000)
        match = re.search(r"((?:CAD\s?)?\$\d{1,3}(?:,\d{3})*(?:\.\d{2})?|Full Tuition|Fully Funded)", text)
        if match:
            val = match.group(0)
            print(f"Capturado via Scraping: {val}")
            return f"{val} (Live)"
    except:
        pass
    return fallback_value

# --- Orquestrador ---

def process_canada_scholarship(key: str) -> scholarship_service.Scholarship:
    meta = SCHOLARSHIPS_META[key]

    print(f"ANALISANDO BOLSA CANADENSE: {meta['name']}")

    # 1. Tenta atualizar o valor dinamicamente
    print(f"  → Validando dados no site oficial...")
    current_value = scrape_live_value(meta["site"], meta["value"])

    # Criando o objeto com base no modelo do Backend
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

    # PINTANDO OS DADOS NO TERMINAL
    print(f"\nDADOS CONSOLIDADOS (CANADA):")
    print(f"Nome:    {scholarship.name}")
    print(f"Valor:   {scholarship.value}")
    print(f"Prazo:   {scholarship.date}")
    print(f"Área:    {scholarship.area}")
    print(f"Site:    {scholarship.site}")

    return scholarship

def scrape_all_canada_scholarships() -> List[scholarship_service.Scholarship]:
    return [process_canada_scholarship(key) for key in SCHOLARSHIPS_META]

if __name__ == "__main__":
    print("Iniciando Motor de Busca de Bolsas (CANADÁ)...")
    results = scrape_all_canada_scholarships()
    print(f"SUCESSO: {len(results)} bolsas canadenses processadas.")