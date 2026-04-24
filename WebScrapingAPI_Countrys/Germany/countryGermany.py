from Backend.Services import country

germany = country.Country(
    name="Germany",
    currency="EUR",
    housing_cost=410, # Média de aluguel para estudantes (~€250–€550 dependendo da cidade) :contentReference[oaicite:1]{index=1}
    transportation_cost=89, # Média mensal (muitas vezes incluído no semestre) :contentReference[oaicite:2]{index=2}
    health_cost=100, # Seguro saúde obrigatório para estudantes :contentReference[oaicite:3]{index=3}
    internet_cost=32, # Internet + telefone médio :contentReference[oaicite:4]{index=4}
    documents=[
        "Passaporte",
        "Carta de Aceite da Universidade",
        "Comprovação Financeira (Blocked Account ~€11.904/ano)", 
        "Seguro Saúde",
        "Comprovante de Proficiência (IELTS/TOEFL ou Alemão)",
        "Formulário de Permissão de Residência"
    ]
)