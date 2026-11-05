from dataclasses import asdict, dataclass


@dataclass
class CalendarConfig:
    state: str
    calendarId: str
    friendlyCalId: str
    color: str

    @classmethod
    def from_dict(cls, data):
        return cls(**data)

    def to_dict(self):
        return asdict(self)
