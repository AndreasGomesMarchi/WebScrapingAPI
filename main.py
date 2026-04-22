import sys
import os
import fastapi

# Importando os modelos
from Backend.Services.country import Country

# ==============================================================================
# IMPORTAÇÕES DOS SCRAPERS DA EQUIPE
# ==============================================================================
from WebScrappingAPI.Canada.universityScrapper import get_university_data as get_canada_university
from WebScrappingAPI.Canada.countryCanada import canada as canada_country
# from WebScrappingAPI.EUA.universityScrapper import get_usa_data
# from WebScrappingAPI.Europa.universityScrapper import get_europe_data

app = fastapi.FastAPI()


# ==============================================================================
# FUNÇÕES CONSTRUTORAS POR PAÍS
# ==============================================================================

def build_canada_data():
    """Constrói o objeto do Canadá e aciona todos os seus scrapers de universidades."""
    
    universities = []
    
    # Scrapers do Canadá
    try:
        uoft = get_canada_university("https://www.utoronto.ca/")
        if uoft:
            universities.append(uoft.__dict__)
    except Exception as e:
        print(f"Erro ao raspar dados da UofT (Canadá): {e}")

    # Outras universidades do Canadá no futuro:
    # mcgill = get_mcgill_university() ...
    
    return {
        "country":  canada_country.__dict__,
        "universities": universities
    }

# def build_usa_data():
#     usa = Country(...)
#     universities = [ ... ]
#     return {"country": usa.__dict__, "universities": universities}


# ==============================================================================
# ROTAS DA API
# ==============================================================================

@app.get("/")
def get_all_data():
    """Rota principal que compõe e retorna os dados de TODOS os países e universidades."""
    all_data = []
    
    # A equipe deve registrar suas funções construtoras nesta lista:
    country_builders = [
        build_canada_data,
        # build_usa_data,
        # build_europe_data,
    ]
    
    for builder in country_builders:
        try:
            data = builder()
            all_data.append(data)
        except Exception as e:
            print(f"Erro ao processar dados de um país: {e}")
            
    return all_data