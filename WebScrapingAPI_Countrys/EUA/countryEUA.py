from Backend.Services import country

usa = country.Country(
    name="United States",
    currency="USD",
    housing_cost=1500, # Média em cidades universitárias (pode variar muito)
    transportation_cost=100, # Transporte público ou custos com carro
    health_cost=200, # Seguro saúde obrigatório (bem caro nos EUA)
    internet_cost=70, # Média nacional
    documents=[
        "Passaporte",
        "Formulário I-20 (emitido pela universidade)",
        "Comprovação Financeira (Proof of Funds)",
        "Visto de Estudante (F-1 ou J-1)",
        "Comprovante de Pagamento SEVIS",
        "Carta de Aceite",
        "Comprovante de Proficiência (TOEFL/IELTS)"
    ]
)