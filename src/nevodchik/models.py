from pydantic.dataclasses import dataclass


@dataclass
class MessageText:
    proto: str
    sent_by: str  # hex without 0x
    heard_by: str  # hex without 0x
    ch_name: str
    rx_rssi: int
    rx_time: str
    hops: int
    text: str
    pass


@dataclass
class MessageInfo:
    proto: str
    node_id: str  # hex without 0x
    node_name: str  # readable name
    pass
