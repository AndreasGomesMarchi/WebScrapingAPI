class Scholarship:
    def __init__(self, name, value, date, about, requirements, area, type, site):
        self.name = name # Nome da Bolsa
        self.value = value # Valor da Bolsa
        self.date = date # data limite para se inscrever a bolsa
        self.about = about # Sobre a bolsa
        self.requirements = requirements # O que é necessário para se inscrever nesta bolsa
        self.area = area # Artes, Ciência da Computação, engenharia, etc.
        self.type = type # Ex: Bolsa por mérito 
        self.site = site # Site da bolsa de estudo

    def __str__(self):
        return f"Scholarship(name={self.name}, value={self.value}, date={self.date}, about={self.about}, requirements={self.requirements}, area={self.area}, type_={self.type}, site={self.site})"
