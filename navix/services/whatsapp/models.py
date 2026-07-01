from dataclasses import dataclass, field
from typing import List, Optional, Any, Dict
from enum import Enum
from datetime import datetime

class MessageType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    VOICE_NOTE = "voice_note"
    DOCUMENT = "document"
    LOCATION = "location"
    CONTACT = "contact"
    STICKER = "sticker"
    GIF = "gif"
    POLL = "poll"
    STATUS = "status"
    SYSTEM = "system"
    UNKNOWN = "unknown"

@dataclass
class Attachment:
    url: Optional[str] = None
    file_path: Optional[str] = None
    mime_type: Optional[str] = None
    thumbnail_url: Optional[str] = None

@dataclass
class PollOption:
    name: str
    votes: int = 0

@dataclass
class Message:
    id: str
    chat_id: str
    sender: str
    sender_name: str
    type: MessageType
    timestamp: datetime
    content: str = ""
    is_from_me: bool = False
    is_forwarded: bool = False
    reply_to: Optional['Message'] = None
    attachments: List[Attachment] = field(default_factory=list)
    poll_options: List[PollOption] = field(default_factory=list)
    raw_data: Optional[Dict[str, Any]] = None

@dataclass
class Chat:
    id: str
    name: str
    is_group: bool
    unread_count: int
    last_message: Optional[Message] = None
