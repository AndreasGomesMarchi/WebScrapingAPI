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
from WebScrappingAPI.Canada.scholarshipsCanada import get_scholarships_canada
# from WebScrappingAPI.EUA.universityScrapper import get_usa_data
# from WebScrappingAPI.Europa.universityScrapper import get_europe_data

app = fastapi.FastAPI()


# ==============================================================================
# FUNÇÕES CONSTRUTORAS POR PAÍS
# ==============================================================================

def build_canada_data():
    """Constrói o objeto do Canadá e aciona todos os seus scrapers de universidades."""
    
    universities = []
    scholarships = []
    
    # Scrapers de bolsas do Canadá
    try:
        canada_scholarships = get_scholarships_canada()
        scholarships = [vars(s) for s in canada_scholarships]
    except Exception as e:
        print(f"Erro ao raspar dados de bolsas (Canadá): {e}")
    
    # Scrapers do Canadá
    try:
        uoft = get_canada_university("https://www.utoronto.ca/", "University of Toronto", "Toronto", "University of Toronto")
        if uoft:
            universities.append(uoft.__dict__)
    except Exception as e:
        print(f"Erro ao raspar dados da UofT (Canadá): {e}")

    try:
        ocad = get_canada_university("https://www.ocadu.ca/", "OCAD University", "Toronto", "OCAD University")
        if ocad:
            universities.append(ocad.__dict__)
    except Exception as e:
        print(f"Erro ao raspar dados da OCAD (Canadá): {e}")

    try:
        mcgill = get_canada_university("https://www.mcgill.ca/", "McGill University", "Montreal", "McGill University", climate="Frio Extremo")
        if mcgill:
            universities.append(mcgill.__dict__)
    except Exception as e:
        print(f"Erro ao raspar dados da McGill (Canadá): {e}")

    
    canada_data = canada_country.__dict__.copy()
    canada_data["scholarships"] = scholarships
    
    return {
        "country":  canada_data,
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