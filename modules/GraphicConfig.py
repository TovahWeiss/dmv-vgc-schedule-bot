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
    imageBackground: str
    textPrimaryColor: str
    headerTextColor: str
    locationTextColor: str
    rowBackground: str
    highlightColor: str
    logoSize: int
    cornerRadius: int
    logoPath: str
    cupIconPath: str
    chalIconPath: str
    unknownIconPath: str
    headerGradientStartColor: str
    headerGradientEndColor: str
    graphicTitle: str

    @classmethod
    def from_dict(cls, data):
        return cls(**data)

    def to_dict(self):
        return asdict(self)
