from dataclasses import asdict, dataclass


@dataclass
class MessageEmbedConfig:
    title: str
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


@dataclass
class MessageConfig:
    channelId: int
    messageId: int
    stateSelections: list[str]
    graphicTitle: str
    embed: MessageEmbedConfig

    @classmethod
    def from_dict(cls, data):
        message_data = dict(data)
        message_data["embed"] = MessageEmbedConfig.from_dict(message_data["embed"])
        return cls(**message_data)

    def to_dict(self):
        return asdict(self)
