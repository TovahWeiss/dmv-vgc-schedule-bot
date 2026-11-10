from dataclasses import asdict, dataclass
import re

nonPremierEventType = 'nonpremier VG'

tzDict = {
    "Connecticut": "America/New_York",
    "Delaware": "America/New_York",
    "Florida": "America/New_York",  
    "Georgia": "America/New_York",
    "Indiana": "America/Indiana/Indianapolis",  
    "Kentucky": "America/Kentucky/Louisville",
    "Massachusetts": "America/New_York",
    "Maryland": "America/New_York",
    "Maine": "America/New_York",
    "Michigan": "America/Detroit",    
    "North Carolina": "America/New_York",
    "New Hampshire": "America/New_York",
    "New Jersey": "America/New_York",
    "New York": "America/New_York",
    "Ohio": "America/New_York",
    "Pennsylvania": "America/New_York",
    "Rhode Island": "America/New_York",
    "South Carolina": "America/New_York",
    "Virginia": "America/New_York",
    "Vermont": "America/New_York",
    "West Virginia": "America/New_York",
    "District of Columbia": "America/New_York",

    "Alabama": "America/Chicago",
    "Arkansas": "America/Chicago",
    "Iowa": "America/Chicago",
    "Illinois": "America/Chicago",
    "Kansas": "America/Chicago",  
    "Louisiana": "America/Chicago",
    "Minnesota": "America/Chicago",
    "Missouri": "America/Chicago",
    "Mississippi": "America/Chicago",
    "North Dakota": "America/Chicago",  
    "Nebraska": "America/Chicago", 
    "Oklahoma": "America/Chicago",
    "South Dakota": "America/Chicago", 
    "Tennessee": "America/Chicago", 
    "Texas": "America/Chicago", 
    "Wisconsin": "America/Chicago",

    "Arizona": "America/Phoenix",   
    "Colorado": "America/Denver",
    "Idaho": "America/Boise",     
    "Montana": "America/Denver",
    "New Mexico": "America/Denver",
    "Nevada": "America/Los_Angeles",
    "Utah": "America/Denver",
    "Wyoming": "America/Denver",

    "California": "America/Los_Angeles",
    "Oregon": "America/Los_Angeles", 
    "Washington": "America/Los_Angeles",

    "Alaska": "America/Anchorage",  
    "Hawaii": "Pacific/Honolulu"
}


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
    
    def hasSanctionedUrl(self) -> bool:
        tournamentUrlEnding = r"/[0-9]{2}-[0-9]{1,2}-[0-9]*/"
        guidSearch = re.search(tournamentUrlEnding,  self.pokemon_url)
        if guidSearch:
            return True
        return False
    
    def getEventTz(self) -> str:
        if self.isNonPremier() and not self.hasSanctionedUrl():
            return 'UTC'
        tz = tzDict[self.state]
        if tz is None:
            return 'America/New_York'
        else:
            return tz