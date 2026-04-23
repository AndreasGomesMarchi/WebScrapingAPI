class University:
    def __init__(self, name, city, climate, nationalPosition, internationalPosition, documents, type, scholarships, site, acceptanceRate):
        self.name = name
        self.city = city
        self.climate = climate
        self.nationalPosition = nationalPosition
        self.internationalPosition = internationalPosition
        self.documents = documents
        self.type = type
        self.scholarships = scholarships
        self.acceptanceRate = acceptanceRate
        self.site = site

    def __str__(self) -> str:
        return f"University(name={self.name}, city={self.city}, climate={self.climate}, nationalPosition={self.nationalPosition}, internationalPosition={self.internationalPosition}, documents={self.documents}, type={self.type}, scholarships={self.scholarships}, site={self.site})"