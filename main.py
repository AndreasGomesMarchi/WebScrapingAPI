"""
Main Orchestrator: Consolida dados de EUA, Alemanha e Canadá.
Converte objetos Python em JSON e prepara para o Supabase.
"""

import os
import sys
from typing import List, Dict

# Adiciona a pasta onde o main.py está ao caminho de busca do Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# --- Imports dos Scrapers e Dados ---

from WebScrapingAPI_Countrys.Germany.universityGermany import scrape_all_germany_universities
from WebScrapingAPI_Countrys.Germany.scholarshipGermany import scrape_all_germany_scholarships
# from WebScrapingAPI_Countrys.Germany.countryGermany import country_germany

from WebScrapingAPI_Countrys.Canada.universityCanadaSoup import scrape_all_canada_universities
from WebScrapingAPI_Countrys.Canada.scholarshipCanadaSoup import scrape_all_canada_scholarships
# from Canada.countryCanada import country_canada

from WebScrapingAPI_Countrys.EUA.UniversityEua import scrape_all_usa_universities
from WebScrapingAPI_Countrys.EUA.scholarshipsEUA import scrape_all_usa_scholarships
# from WebScrapingAPI_Countrys.EUA.countryEUA import country_usa

# --- Helper de Conversão ---

def to_dict(obj):
    """
    Converte recursivamente objetos de classe em dicionários.
    Isso é o que o Supabase/JSON precisam.
    """
    if isinstance(obj, list):
        return [to_dict(i) for i in obj]
    if hasattr(obj, "__dict__"):
        data = dict(
            (key, to_dict(value))
            for key, value in obj.__dict__.items()
        )
        return data
    return obj

# --- Consolidação ---

def collect_everything():
    print("Iniciando consolidação global de dados...")

    # # 1. Coleta de Países
    # countries_data = [
    #     to_dict(country_germany),
    #     to_dict(country_canada),
    #     to_dict(country_usa)
    # ]

    # 2. Coleta de Universidades
    print("  → Raspando universidades...")
    all_unis = []
    all_unis.extend(scrape_all_germany_universities())
    all_unis.extend(scrape_all_canada_universities())
    all_unis.extend(scrape_all_usa_universities())
    
    unis_data = [to_dict(u) for u in all_unis]

    # 3. Coleta de Bolsas (Caso existam separadas das universidades)
    # Aqui você seguiria a mesma lógica se tiver uma tabela só para bolsas
    all_scholarships = []
    all_scholarships.extend(scrape_all_germany_scholarships())
    all_scholarships.extend(scrape_all_canada_scholarships())
    all_scholarships.extend(scrape_all_usa_scholarships())

    scholarships_data = [to_dict(s) for s in all_scholarships]

    return unis_data, scholarships_data

# --- Integração Supabase (Mock por enquanto) ---

def sync_with_supabase(table_name: str, json_data: List[Dict]):
    """
    Aqui entrará a lógica de 'upsert' do Supabase.
    """
    print(f"  → Sincronizando {len(json_data)} registros na tabela '{table_name}'...")
    # Exemplo: supabase.table(table_name).upsert(json_data).execute()
    pass

# --- Execução Principal ---

if __name__ == "__main__":
    # 1. Busca todos os dados
    universities, scholarships = collect_everything()

    print(f"\nConsolidação concluída!")
    print(f"Universidades carregadas: {len(universities)}")
    print(f"Bolsas carregadas: {len(scholarships)}")

    # 2. Envia para o Banco de Dados
    # sync_with_supabase("countries", countries)
    # sync_with_supabase("universities", universities)
    # sync_with_supabase("scholarships", scholarships)

    print("\nProcesso finalizado com sucesso.")





































# import sys
# import os
# import fastapi

# # Importando os modelos
# from Backend.Services.country import Country

# # ==============================================================================
# # IMPORTAÇÕES DOS SCRAPERS DA EQUIPE
# # ==============================================================================
# from WebScrappingAPI_Countrys.Canada.universityScrapper import get_university_data as get_canada_university
# from WebScrappingAPI_Countrys.Canada.countryCanada import canada as canada_country
# from WebScrappingAPI_Countrys.Canada.scholarshipsCanada import get_scholarships_canada
# # from WebScrappingAPI.EUA.universityScrapper import get_usa_data
# # from WebScrappingAPI.Europa.universityScrapper import get_europe_data

# app = fastapi.FastAPI()


# # ==============================================================================
# # FUNÇÕES CONSTRUTORAS POR PAÍS
# # ==============================================================================

# def build_canada_data():
#     """Constrói o objeto do Canadá e aciona todos os seus scrapers de universidades."""
    
#     universities = []
#     scholarships = []
    
#     # Scrapers de bolsas do Canadá
#     try:
#         canada_scholarships = get_scholarships_canada()
#         scholarships = [vars(s) for s in canada_scholarships]
#     except Exception as e:
#         print(f"Erro ao raspar dados de bolsas (Canadá): {e}")
    
#     # Scrapers do Canadá
#     try:
#         uoft = get_canada_university("https://www.utoronto.ca/", "University of Toronto", "Toronto", "University of Toronto")
#         if uoft:
#             universities.append(uoft.__dict__)
#     except Exception as e:
#         print(f"Erro ao raspar dados da UofT (Canadá): {e}")

#     try:
#         ocad = get_canada_university("https://www.ocadu.ca/", "OCAD University", "Toronto", "OCAD University")
#         if ocad:
#             universities.append(ocad.__dict__)
#     except Exception as e:
#         print(f"Erro ao raspar dados da OCAD (Canadá): {e}")

#     try:
#         mcgill = get_canada_university("https://www.mcgill.ca/", "McGill University", "Montreal", "McGill University", climate="Frio Extremo")
#         if mcgill:
#             universities.append(mcgill.__dict__)
#     except Exception as e:
#         print(f"Erro ao raspar dados da McGill (Canadá): {e}")

    
#     canada_data = canada_country.__dict__.copy()
#     canada_data["scholarships"] = scholarships
    
#     return {
#         "country":  canada_data,
#         "universities": universities
#     }

# # def build_usa_data():
# #     usa = Country(...)
# #     universities = [ ... ]
# #     return {"country": usa.__dict__, "universities": universities}


# # ==============================================================================
# # ROTAS DA API
# # ==============================================================================

# @app.get("/")
# def get_all_data():
#     """Rota principal que compõe e retorna os dados de TODOS os países e universidades."""
#     all_data = []
    
#     # A equipe deve registrar suas funções construtoras nesta lista:
#     country_builders = [
#         build_canada_data,
#         # build_usa_data,
#         # build_europe_data,
#     ]
    
#     for builder in country_builders:
#         try:
#             data = builder()
#             all_data.append(data)
#         except Exception as e:
#             print(f"Erro ao processar dados de um país: {e}")
            
#     return all_data