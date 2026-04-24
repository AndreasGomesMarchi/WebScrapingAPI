class Scholarship:
    def __init__(self, name, value, date, about, requirements, area, type, site):
        self.name = name
        self.value = value
        self.date = date
        self.about = about
        self.requirements = requirements
        self.area = area
        self.type = type
        self.site = site

    def __str__(self): 
        return f"Scholarship(name={self.name}, value={self.value}, date={self.date}, about={self.about}, requirements={self.requirements}, area={self.area}, type_={self.type}, site={self.site})"
