from dataclasses import asdict, dataclass
import re

nonPremierEventType = 'nonpremier VG'

@dataclass
class CalendarPerson:
    email: str
    displayName: str | None = None
    self: bool | None = None

    @classmethod
    def from_dict(cls, data):
        return cls(**data)

    def to_dict(self):
        return {key: value for key, value in asdict(self).items() if value is not None}


@dataclass
class CalendarTime:
    dateTime: str | None = None
    date: str | None = None
    timeZone: str | None = None

    @classmethod
    def from_dict(cls, data):
        return cls(**data)

    def to_dict(self):
        return {key: value for key, value in asdict(self).items() if value is not None}


@dataclass
class CalendarReminders:
    useDefault: bool

    @classmethod
    def from_dict(cls, data):
        return cls(**data)


@dataclass
class GoogleCalendarEvent:
    kind: str
    etag: str
    id: str
    status: str
    htmlLink: str
    created: str
    updated: str
    summary: str
    description: str
    location: str
    creator: CalendarPerson
    organizer: CalendarPerson
    start: CalendarTime
    end: CalendarTime
    iCalUID: str
    sequence: int
    reminders: CalendarReminders
    eventType: str

    @classmethod
    def from_dict(cls, data):
        event_data = data.copy()
        event_data["creator"] = CalendarPerson.from_dict(data["creator"])
        event_data["organizer"] = CalendarPerson.from_dict(data["organizer"])
        event_data["start"] = CalendarTime.from_dict(data["start"])
        event_data["end"] = CalendarTime.from_dict(data["end"])
        event_data["reminders"] = CalendarReminders.from_dict(data["reminders"])
        return cls(**event_data)

    def to_dict(self):
        event_data = asdict(self)
        event_data["creator"] = self.creator.to_dict()
        event_data["organizer"] = self.organizer.to_dict()
        event_data["start"] = self.start.to_dict()
        event_data["end"] = self.end.to_dict()
        return event_data

    def isNonPremier(self) -> bool:
        return nonPremierEventType in self.description
    
    def hasSanctionedUrl(e: GoogleCalendarEvent) -> bool:
        tournamentUrlEnding = r"/[0-9]{2}-[0-9]{1,2}-[0-9]*/"
        guidSearch = re.search(tournamentUrlEnding,  e.description)
        if guidSearch:
            return True
        return False
    
    def getEventTz(self) -> str:
        if self.isNonPremier() and not self.hasSanctionedUrl():
            return 'UTC'
        return 'America/New_York'