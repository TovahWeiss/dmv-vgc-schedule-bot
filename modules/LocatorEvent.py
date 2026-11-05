from dataclasses import asdict, dataclass
import re

nonPremierEventType = 'nonpremier VG'

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
    
    def isNonPremier(self) -> bool:
        return self.type == nonPremierEventType
    
    def hasSanctionedUrl(e: LocatorEvent) -> bool:
        tournamentUrlEnding = r"/[0-9]{2}-[0-9]{1,2}-[0-9]*/"
        guidSearch = re.search(tournamentUrlEnding,  e.pokemon_url)
        if guidSearch:
            return True
        return False
    
    def getEventTz(self) -> str:
        if self.isNonPremier() and not self.hasSanctionedUrl():
            return 'UTC'
        return 'America/New_York'