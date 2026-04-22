# https://www.educanada.ca/scholarships-bourses/can/institutions/elap-pfla.aspx?lang=eng
# https://www.educanada.ca/scholarships-bourses/can/institutions/study-in-canada-sep-etudes-au-canada-pct.aspx?lang=eng
# https://www.educanada.ca/scholarships-bourses/non_can/ccsep-peucc.aspx?lang=eng


import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import requests
from fastapi import FastAPI
from bs4 import BeautifulSoup
from Backend.Services.country import Country
from Backend.Services.scholarships import Scholarship

app = FastAPI()


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def get_scholarships_canada():
    urls = [
        "https://www.educanada.ca/scholarships-bourses/can/institutions/elap-pfla.aspx?lang=eng",
        "https://www.educanada.ca/scholarships-bourses/can/institutions/study-in-canada-sep-etudes-au-canada-pct.aspx?lang=eng",
        "https://www.educanada.ca/scholarships-bourses/non_can/ccsep-peucc.aspx?lang=eng"
    ]
    
    scholarships_list = []

    for url in urls:
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            # 1. Nome (Geralmente no H1)
            name = soup.find('h1').get_text(strip=True) if soup.find('h1') else "N/A" # type: ignore

            # Função auxiliar para pegar texto após um cabeçalho H2, H3 ou texto em negrito
            def get_section_text(keywords):
                for tag in soup.find_all(['h2', 'h3', 'h4', 'strong', 'b', 'p']):
                    text = tag.get_text(strip=True).lower()
                    
                    # Evita capturar rodapés do site (ex: "About EduCanada")
                    if "educanada" in text or "government" in text:
                        continue
                        
                    if any(key.lower() in text for key in keywords) and len(text) < 150:
                        content = []
                        
                        # Se a tag for um parágrafo longo, ela mesma pode conter a informação
                        if tag.name == 'p' and len(tag.get_text(strip=True)) > 50:
                            content.append(tag.get_text(" ", strip=True))

                        next_node = tag.find_next_sibling()
                        
                        # Se achou uma tag strong, o irmão a ser iterado é o do parágrafo pai
                        if tag.name in ['strong', 'b'] and tag.parent:
                            next_node = tag.parent.find_next_sibling()
                            
                        count = 0
                        while next_node and count < 15: # Limite de nós para evitar capturar a página toda
                            if next_node.name in ['h2', 'h3', 'h4', 'h1']:
                                break
                            
                            if next_node.name == 'p' and next_node.find('strong') and len(next_node.get_text(strip=True)) < 60:
                                break
                                
                            if next_node.name in ['p', 'ul', 'ol', 'div', 'li']:
                                text_content = next_node.get_text(" ", strip=True)
                                if text_content:
                                    content.append(text_content)
                                    
                            next_node = next_node.find_next_sibling()
                            count += 1
                            
                        res = " ".join(content).strip()
                        if res:
                            return res
                return "N/A"

            # 2. Extração dos campos baseada nos H2s da página
            about = get_section_text(["Objectives", "Description"])
            requirements = get_section_text(["Eligibility"])
            value = get_section_text(["Value"])
            date = get_section_text(["Deadline", "Key dates"])
            area = get_section_text(["Fields"])
            
            # 3. Definindo o tipo (inferido pelo título ou URL)
            scholarship_type = "Exchange Program" if "exchange" in about.lower() else "Scholarship"

            # Criando o objeto
            scholarship_obj = Scholarship(
                name=name,
                value=value,
                date=date,
                about=about,
                requirements=requirements,
                area=area,
                type=scholarship_type,
                site=url
            )
            
            scholarships_list.append(scholarship_obj)

        except Exception as e:
            print(f"Erro ao processar {url}: {e}")

    return scholarships_list

# Exemplo de uso para sua API FastAPI:
@app.get("/scholarships/canada")
def read_scholarships():
    data = get_scholarships_canada()
    # Para o FastAPI retornar JSON, convertemos os objetos em dicionários
    return [vars(s) for s in data]

if __name__ == "__main__":
    scholarships = get_scholarships_canada()
    for s in scholarships:
        print(s)
