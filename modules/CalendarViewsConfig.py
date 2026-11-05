from dataclasses import asdict, dataclass


@dataclass
class CalendarViewsConfig:
    schedView: str
    friendlySchedView: str
    allCalView: str
    premierSync: str
    friendlySync: str

    @classmethod
    def from_dict(cls, data):
        return cls(**data)

    def to_dict(self):
        return asdict(self)
