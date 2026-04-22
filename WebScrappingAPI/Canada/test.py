# import requests
# from bs4 import BeautifulSoup
# from fastapi import FastAPI, HTTPException
# from typing import Optional, List, Dict
# import re
# import time
# import json

# app = FastAPI()

# # Headers mais completos para evitar bloqueios
# HEADERS = {
#     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
#     "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
#     "Accept-Language": "en-US,en;q=0.9",
#     "Accept-Encoding": "gzip, deflate, br",
#     "Connection": "keep-alive",
#     "Upgrade-Insecure-Requests": "1",
#     "Sec-Fetch-Dest": "document",
#     "Sec-Fetch-Mode": "navigate",
#     "Sec-Fetch-Site": "none"
# }

# class University:
#     def __init__(self, name, city, climate, nationalPosition, internationalPosition, documents, type, scholarships, site):
#         self.name = name
#         self.city = city
#         self.climate = climate
#         self.nationalPosition = nationalPosition
#         self.internationalPosition = internationalPosition
#         self.documents = documents
#         self.type = type
#         self.scholarships = scholarships
#         self.site = site
    
#     def to_dict(self):
#         return {
#             "name": self.name,
#             "city": self.city,
#             "climate": self.climate,
#             "nationalPosition": self.nationalPosition,
#             "internationalPosition": self.internationalPosition,
#             "documents": self.documents,
#             "type": self.type,
#             "scholarships": self.scholarships,
#             "site": self.site
#         }


# class UniversityScraper:
#     def __init__(self):
#         self.headers = HEADERS
#         self.session = requests.Session()
#         self.session.headers.update(HEADERS)
        
#     def fetch_page(self, url: str, delay: float = 1.0) -> Optional[BeautifulSoup]:
#         """Faz requisição e retorna o BeautifulSoup ou None em caso de erro"""
#         time.sleep(delay)  # Respeita rate limiting
        
#         try:
#             response = self.session.get(url, timeout=15, allow_redirects=True)
#             response.raise_for_status()
#             return BeautifulSoup(response.text, 'html.parser')
#         except requests.exceptions.HTTPError as e:
#             print(f"Erro de Status: {e.response.status_code} ao acessar {url}")
#             return None
#         except Exception as e:
#             print(f"Erro inesperado ao acessar {url}: {e}")
#             return None
    
#     def get_university_basic_info(self, url: str) -> Dict:
#         """Extrai informações básicas do site da universidade"""
#         soup = self.fetch_page(url)
#         if not soup:
#             return {}
        
#         # Busca o nome da universidade
#         name = soup.title.string if soup.title else "Universidade Desconhecida"
#         name = name.strip().split('|')[0].split('-')[0].strip()
        
#         return {
#             "name": name,
#             "site": url
#         }
    
#     def get_ranking_from_wikipedia(self, university_name: str) -> Dict:
#         """
#         Busca ranking na Wikipedia (fonte mais acessível)
#         """
#         search_name = university_name.replace(' ', '_')
#         url = f"https://en.wikipedia.org/wiki/{search_name}"
        
#         soup = self.fetch_page(url)
#         if not soup:
#             return {}
        
#         rankings = {}
        
#         # Procura por tabelas de informação (infobox)
#         infobox = soup.find('table', {'class': 'infobox'})
#         if infobox:
#             rows = infobox.find_all('tr')
#             for row in rows:
#                 text = row.get_text().lower()
                
#                 # Procura por rankings
#                 if 'qs' in text or 'world' in text:
#                     numbers = re.findall(r'\b(\d+)\b', text)
#                     if numbers and 'ranking' in text:
#                         try:
#                             rank = int(numbers[0])
#                             if rank < 1000:  # Filtro básico
#                                 rankings['internationalPosition'] = rank
#                                 break
#                         except:
#                             pass
        
#         return rankings
    
#     def get_ranking_from_cwur(self, university_name: str) -> Dict:
#         """
#         Center for World University Rankings - geralmente mais acessível
#         """
#         url = "https://cwur.org/2024-25.php"
        
#         soup = self.fetch_page(url)
#         if not soup:
#             return {}
        
#         # Procura pela universidade na tabela
#         tables = soup.find_all('table')
#         for table in tables:
#             rows = table.find_all('tr')
#             for row in rows:
#                 if university_name.lower() in row.get_text().lower():
#                     # Pega o primeiro número da linha (geralmente é o ranking)
#                     numbers = re.findall(r'\b(\d+)\b', row.get_text())
#                     if numbers:
#                         return {'internationalPosition': int(numbers[0])}
        
#         return {}
    
#     def search_scholarships_on_site(self, university_url: str, soup: BeautifulSoup = None) -> List[str]:
#         """
#         Busca informações sobre bolsas diretamente no site
#         """
#         if not soup:
#             soup = self.fetch_page(university_url)
            
#         if not soup:
#             return []
        
#         scholarships = []
        
#         # Procura por links relacionados a bolsas
#         scholarship_keywords = ['scholarship', 'financial-aid', 'funding', 'award', 'bursary']
        
#         links = soup.find_all('a', href=True)
#         scholarship_urls = []
        
#         for link in links:
#             href = link['href'].lower()
#             text = link.get_text().lower()
            
#             if any(keyword in href or keyword in text for keyword in scholarship_keywords):
#                 # Constrói URL completa
#                 if href.startswith('http'):
#                     scholarship_urls.append(href)
#                 elif href.startswith('/'):
#                     base_url = university_url.rstrip('/')
#                     scholarship_urls.append(base_url + href)
        
#         # Visita as primeiras 3 URLs encontradas
#         for url in scholarship_urls[:3]:
#             page_soup = self.fetch_page(url, delay=2)
#             if page_soup:
#                 text = page_soup.get_text().lower()
                
#                 if 'merit' in text:
#                     scholarships.append("Merit-based scholarships")
#                 if 'need-based' in text or 'financial need' in text:
#                     scholarships.append("Need-based financial aid")
#                 if 'international student' in text and 'scholarship' in text:
#                     scholarships.append("International student scholarships")
#                 if 'entrance' in text and ('scholarship' in text or 'award' in text):
#                     scholarships.append("Entrance scholarships")
#                 if 'graduate' in text and ('funding' in text or 'scholarship' in text):
#                     scholarships.append("Graduate funding")
                
#                 # Se já encontrou alguma coisa, para
#                 if scholarships:
#                     break
        
#         return list(set(scholarships))
    
#     def get_university_type_from_site(self, soup: BeautifulSoup) -> str:
#         """Tenta identificar se a universidade é pública ou privada"""
#         if not soup:
#             return "Não especificado"
        
#         text = soup.get_text().lower()
        
#         if 'public university' in text or 'state university' in text:
#             return "Pública"
#         elif 'private university' in text or 'independent university' in text:
#             return "Privada"
        
#         return "Não especificado"
    
#     def scrape_university(self, university_url: str, university_name: str = None, 
#                          city: str = None, climate: str = None) -> University:
#         """
#         Função principal que agrega dados de múltiplas fontes
#         """
#         print(f"\n🔍 Iniciando scraping de: {university_url}")
        
#         # 1. Dados básicos do site da universidade
#         soup = self.fetch_page(university_url)
#         basic_info = self.get_university_basic_info(university_url)
#         name = university_name or basic_info.get("name", "Universidade Desconhecida")
        
#         print(f"✓ Nome identificado: {name}")
        
#         # 2. Tipo da universidade
#         university_type = self.get_university_type_from_site(soup)
#         print(f"✓ Tipo: {university_type}")
        
#         # 3. Ranking internacional (tentando múltiplas fontes)
#         print("🔍 Buscando ranking internacional...")
        
#         international_rank = None
        
#         # Tenta Wikipedia primeiro (mais confiável e acessível)
#         wiki_data = self.get_ranking_from_wikipedia(name)
#         international_rank = wiki_data.get("internationalPosition")
        
#         if international_rank:
#             print(f"✓ Ranking encontrado na Wikipedia: #{international_rank}")
#         else:
#             # Tenta CWUR
#             cwur_data = self.get_ranking_from_cwur(name)
#             international_rank = cwur_data.get("internationalPosition")
#             if international_rank:
#                 print(f"✓ Ranking encontrado no CWUR: #{international_rank}")
#             else:
#                 print("⚠ Ranking internacional não encontrado")
        
#         # 4. Informações sobre bolsas
#         print("🔍 Buscando informações sobre bolsas...")
#         scholarships = self.search_scholarships_on_site(university_url, soup)
        
#         if scholarships:
#             print(f"✓ Bolsas encontradas: {', '.join(scholarships)}")
#         else:
#             print("⚠ Informações sobre bolsas não encontradas no site")
#             scholarships = ["Consulte o site oficial para informações sobre bolsas"]
        
#         # 5. Dados adicionais (podem ser parametrizados)
#         documents = [
#             "Passaporte",
#             "Histórico Escolar Traduzido",
#             "Diploma ou Certificado de Conclusão",
#             "Cartas de Recomendação",
#             "Statement of Purpose / Personal Statement",
#             "Teste de Proficiência em Inglês (TOEFL/IELTS/Duolingo)",
#             "Currículo/CV"
#         ]
        
#         # 6. Cria objeto University
#         university = University(
#             name=name,
#             city=city or "Não especificado",
#             climate=climate or "Não especificado",
#             nationalPosition=None,  # Precisa ser fornecido ou pesquisado separadamente
#             internationalPosition=international_rank,
#             documents=documents,
#             type=university_type,
#             scholarships=scholarships,
#             site=university_url
#         )
        
#         print(f"✅ Scraping concluído!\n")
#         return university


# # Configurações pré-definidas para universidades conhecidas
# UNIVERSITY_CONFIGS = {
#     "uoft": {
#         "url": "https://www.utoronto.ca/",
#         "name": "University of Toronto",
#         "city": "Toronto",
#         "climate": "Continental úmido (verões quentes e úmidos, invernos frios e nevados)",
#         "nationalPosition": 1
#     },
#     "ubc": {
#         "url": "https://www.ubc.ca/",
#         "name": "University of British Columbia",
#         "city": "Vancouver",
#         "climate": "Oceânico temperado (invernos amenos e chuvosos, verões agradáveis)",
#         "nationalPosition": 2
#     },
#     "mcgill": {
#         "url": "https://www.mcgill.ca/",
#         "name": "McGill University",
#         "city": "Montreal",
#         "climate": "Continental úmido (verões quentes, invernos muito frios)",
#         "nationalPosition": 3
#     }
# }

# # Instância global do scraper
# scraper = UniversityScraper()


# @app.get("/scrape/university")
# def scrape_university_endpoint(url: str, name: Optional[str] = None, 
#                                city: Optional[str] = None, climate: Optional[str] = None):
#     """
#     Endpoint para fazer scraping de uma universidade
    
#     Parâmetros:
#     - url: URL do site da universidade
#     - name: Nome da universidade (opcional)
#     - city: Cidade (opcional)
#     - climate: Clima (opcional)
#     """
#     try:
#         university = scraper.scrape_university(url, name, city, climate)
#         return university.to_dict()
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Erro ao fazer scraping: {str(e)}")


# @app.get("/scrape/{university_code}")
# def scrape_predefined_university(university_code: str):
#     """Endpoint para universidades pré-configuradas (uoft, ubc, mcgill, etc)"""
    
#     if university_code not in UNIVERSITY_CONFIGS:
#         raise HTTPException(status_code=404, detail=f"Universidade '{university_code}' não configurada")
    
#     config = UNIVERSITY_CONFIGS[university_code]
    
#     university = scraper.scrape_university(
#         config["url"],
#         config["name"],
#         config["city"],
#         config["climate"]
#     )
    
#     # Adiciona posição nacional se disponível
#     if "nationalPosition" in config:
#         university.nationalPosition = config["nationalPosition"]
    
#     return university.to_dict()


# def main():
#     # Teste do scraper com University of Toronto
#     config = UNIVERSITY_CONFIGS["ubc"] 
    
#     university = scraper.scrape_university(
#         config["url"],
#         config["name"],
#         config["city"],
#         config["climate"]
#     )
    
#     university.nationalPosition = config["nationalPosition"]
    
#     print("=" * 60)
#     print("RESUMO DOS DADOS COLETADOS")
#     print("=" * 60)
#     print(f"Nome: {university.name}")
#     print(f"Cidade: {university.city}")
#     print(f"Clima: {university.climate}")
#     print(f"Posição Nacional: #{university.nationalPosition}" if university.nationalPosition else "Posição Nacional: N/A")
#     print(f"Posição Internacional: #{university.internationalPosition}" if university.internationalPosition else "Posição Internacional: N/A")
#     print(f"Tipo: {university.type}")
#     print(f"\nDocumentos necessários:")
#     for doc in university.documents:
#         print(f"  • {doc}")
#     print(f"\nBolsas disponíveis:")
#     for scholarship in university.scholarships:
#         print(f"  • {scholarship}")
#     print(f"\nSite: {university.site}")
#     print("=" * 60)


# if __name__ == "__main__":
#     main()