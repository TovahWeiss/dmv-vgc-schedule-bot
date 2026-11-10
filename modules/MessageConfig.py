from dataclasses import asdict, dataclass


@dataclass
class MessageEmbedConfig:
    title: str
    schedView: str
    friendlySchedView: str
    allCalView: str

    @classmethod
    def from_dict(cls, data):
        return cls(**data)

    def to_dict(self):
        return asdict(self)

@dataclass
class MessageImageConfig:
    title: str
    headerGradientStartColor: str
    headerGradientEndColor: str
    imageBackgroundColor: str
    textPrimaryColor: str
    headerTextColor: str
    locationTextColor: str
    rowBackgroundColor: str
    highlightColor: str

    @classmethod
    def from_dict(cls, data):
        return cls(**data)

    def to_dict(self):
        return asdict(self)


@dataclass
class MessageConfig:
    guildId: int
    channelId: int
    messageId: int
    stateSelections: list[str]
    embed: MessageEmbedConfig
    image: MessageImageConfig

    @classmethod
    def from_dict(cls, data):
        message_data = dict(data)
        message_data["embed"] = MessageEmbedConfig.from_dict(message_data["embed"])
        message_data["image"] = MessageImageConfig.from_dict(message_data["image"])
        return cls(**message_data)

    def to_dict(self):
        return asdict(self)
