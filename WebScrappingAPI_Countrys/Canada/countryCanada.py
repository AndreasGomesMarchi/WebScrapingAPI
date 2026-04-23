from Backend.Services import country

canada = country.Country(
    name="Canada",
    currency="CAD",
    housing_cost=1250, # Média nacional para estudantes (quarto individual/shared)
    transportation_cost=120, # Média de passes mensais estudantis em grandes centros
    health_cost=85, # Seguro saúde internacional (média mensal de planos como UHIP/McGill)
    internet_cost=85, # Planos de alta velocidade (um dos mais caros do mundo)
    documents=[
    "Carta de Aceite (LOA)", 
    "Carta de Atestado Provincial (PAL)", # Novo requisito obrigatório desde 2024
    "Comprovação Financeira (Proof of Funds)", # Exigência atualizada: ~CAD $22,895 + anuidade
    "Passaporte",
    "Carta de Explicação (SOP/LOE)",
    "Exames Médicos"
    ]
)
