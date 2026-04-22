# https://www.utoronto.ca/

#Canadá: Universidade de Toronto, OCAD University e McGill

import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException
import sys
import os
from playwright.sync_api import sync_playwright

# Adiciona o diretório raiz do projeto ao sys.path para permitir a importação de Backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from Backend.Services.university import University

app = FastAPI()

# Definindo um cabeçalho que simula um navegador real
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def get_university_data(url: str):
    try:
        response = requests.get(url, headers=HEADERS, allow_redirects=True)
        # Se o site bloquear, isso vai nos dizer o porquê (ex: 403)
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print(f"Erro de Status: {e.response.status_code} ao acessar {url}")
        return None
    except Exception as e:
        print(f"Erro inesperado: {e}")
        return None

    # Usando o html.parser como você definiu
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Busca o título real da página para testar se o scraping funcionou
    titulo_real = soup.title.string if soup.title else "Sem título"


    data = {
        "nome": titulo_real.strip(),  # type: ignore
        "cidade": "Toronto",
        "pais": "Canadá",
        "tipo": "Pública",
        "site": url,
        "tags": ["Research", "Top Ranked"],
        "documentos": ["Passaporte", "Histórico Escolar"],
        "bolsas_atreladas": [] 
    }

    ranking = getRanking("University of Toronto")

    university = University(
        name=data["nome"],
        city=data["cidade"],
        climate="Temperado",
        nationalPosition=1,
        internationalPosition=ranking['ranking'] if ranking else "N/A",
        documents=data["documentos"],
        type=data["tipo"],
        scholarships=data["bolsas_atreladas"],
        site=data["site"]
    )
    
    return university

def getRanking(university_name: str):
    url = "https://www.timeshighereducation.com/world-university-rankings/latest/world-ranking"
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # Navega até o site e espera o carregamento inicial da página
            page.goto(url, wait_until="domcontentloaded")
            
            # Espera até que os elementos "tr.group" (as linhas da tabela) apareçam na tela
            page.wait_for_selector("tr.group", timeout=15000)
            
            # Pega todas as linhas
            rows = page.locator("tr.group")
            count = rows.count()
            
            for i in range(count):
                row = rows.nth(i)
                univ_link = row.locator("a.institution-link")
                
                if univ_link.count() > 0:
                    current_name = univ_link.inner_text().strip()
                    
                    if university_name.lower() in current_name.lower():
                        cells = row.locator("td")
                        
                        resultado = {
                            "ranking": cells.nth(0).inner_text().strip(),
                            "name": current_name,
                            "country": cells.nth(1).locator("a").nth(1).inner_text().strip(),
                            "scores": [cells.nth(j).inner_text().strip() for j in range(2, cells.count() - 1)]
                        }
                        browser.close()
                        return resultado
                        
            browser.close()
            return None
            
    except Exception as e:
        print(f"Erro ao usar o Playwright: {e}")
        return None



@app.get("/scrape/uoft")
def scrape_university():
    url = "https://www.utoronto.ca/"
    data = get_university_data(url)
    
    if not data:
        raise HTTPException(status_code=404, detail="Não foi possível acessar o site ou fomos bloqueados.")
        
    return data

def main():
    data = getRanking("University of Toronto")
    print(f"Dados coletados com sucesso: {data}")

if __name__ == "__main__":
    main()

    