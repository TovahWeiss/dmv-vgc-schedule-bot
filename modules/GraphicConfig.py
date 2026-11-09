from dataclasses import asdict, dataclass


@dataclass
class GraphicConfig:
    embedH: int
    embedW: int
    headerHeight: int
    margin: int
    headerFont: str
    fontFamily: str
    rowHeight: int
    rowScheduleStart: int
    logoSize: int
    cornerRadius: int
    logoPath: str
    cupIconPath: str
    chalIconPath: str
    unknownIconPath: str

    @classmethod
    def from_dict(cls, data):
        return cls(**data)

    def to_dict(self):
        return asdict(self)
