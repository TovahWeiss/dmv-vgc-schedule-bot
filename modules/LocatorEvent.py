from dataclasses import asdict, dataclass


@dataclass
class LocatorEvent:
    type: str
    name: str
    date: str
    shop: str
    street_address: str
    state: str
    city: str
    postal_code: str
    country_code: str
    pokemon_url: str
    guid: str
    latitude: str
    longitude: str
    when: str
    status: str
    totalPlayers: str
    TCaccounts: str
    juniors: str
    seniors: str
    masters: str
    league: str
    category: str
    tournament_date: str
    tournament_completed: str
    date_added: str
    distance: str
    cost: str
    registration: str
    
    @classmethod
    def from_dict(cls, data):
        return cls(**data)

    def to_dict(self):
        return asdict(self)
