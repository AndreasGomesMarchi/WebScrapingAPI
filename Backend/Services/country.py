class Country:
    def __init__(
            self, name, currency, housing_cost, transportation_cost, health_cost, internet_cost, documents, scholarships=None):
        self.name = name
        self.currency = currency
        self.housing_cost = housing_cost
        self.transportation_cost = transportation_cost
        self.health_cost = health_cost
        self.internet_cost = internet_cost
        self.documents = documents
        self.scholarships = scholarships if scholarships is not None else []

    def __str__(self) -> str:
        return f"Country(name={self.name}, currency={self.currency}, housing_cost={self.housing_cost}, transportation_cost={self.transportation_cost}, health_cost={self.health_cost}, internet_cost={self.internet_cost}, documents={self.documents}, scholarships={self.scholarships})"