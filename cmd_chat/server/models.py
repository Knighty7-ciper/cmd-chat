from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum
import uuid
import json


class MessageType(str, Enum):
    TEXT = "text"
    SYSTEM = "system"
    EMOJI = "emoji"
    FILE = "file"
    COMMAND = "command"


class UserStatus(str, Enum):
    ONLINE = "online"
    AWAY = "away"
    OFFLINE = "offline"
    BUSY = "busy"


class RoomType(str, Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    DIRECT = "direct"


class User(BaseModel):
    """User model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    status: UserStatus = UserStatus.ONLINE
    joined_at: datetime = Field(default_factory=datetime.utcnow)
    last_seen: datetime = Field(default_factory=datetime.utcnow)
    ip_address: Optional[str] = None
    is_admin: bool = False
    
    @validator('username')
    def validate_username(cls, v):
        if not v or len(v.strip()) < 2:
            raise ValueError('Username must be at least 2 characters')
        if len(v) > 20:
            raise ValueError('Username too long')
        # Allow alphanumeric, underscores, hyphens only
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Username can only contain letters, numbers, underscores, and hyphens')
        return v.strip()


class Room(BaseModel):
    """Room model with multiple room support"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    type: RoomType = RoomType.PUBLIC
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    description: str = ""
    is_active: bool = True
    member_count: int = 0
    max_members: int = 50
    password: Optional[str] = None  # For private rooms
    
    @validator('name')
    def validate_room_name(cls, v):
        if not v or len(v.strip()) < 1:
            raise ValueError('Room name is required')
        if len(v) > 30:
            raise ValueError('Room name too long')
        return v.strip()

    def to_dict(self) -> Dict[str, Any]:
        """Convert room to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "description": self.description,
            "is_active": self.is_active,
            "member_count": self.member_count,
            "max_members": self.max_members
        }


class Message(BaseModel):
    """Message model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    room_id: str
    user_id: str
    username: str
    content: str
    message_type: MessageType = MessageType.TEXT
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    is_encrypted: bool = True
    reply_to: Optional[str] = None  # ID of message being replied to
    file_url: Optional[str] = None  # For file messages
    
    @validator('content')
    def validate_content(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Message cannot be empty')
        if len(v) > 1000:
            raise ValueError('Message too long')
        return v.strip()

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "room_id": self.room_id,
            "user_id": self.user_id,
            "username": self.username,
            "content": self.content,
            "message_type": self.message_type,
            "timestamp": self.timestamp.isoformat(),
            "is_encrypted": self.is_encrypted,
            "reply_to": self.reply_to,
            "file_url": self.file_url
        }


class RoomHistory(BaseModel):
    """Persistent room history for message persistence"""
    room_id: str
    messages: List[Message] = Field(default_factory=list)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    message_count: int = 0
    max_messages: int = 10000
    
    def add_message(self, message: Message):
        """Add message with automatic cleanup"""
        self.messages.append(message)
        self.message_count += 1
        self.last_updated = datetime.utcnow()
        
        # Keep only the most recent messages to prevent memory issues
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]
    
    def get_recent_messages(self, limit: int = 50) -> List[Message]:
        """Get recent messages from history"""
        return self.messages[-limit:] if limit > 0 else self.messages
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert history to dictionary"""
        return {
            "room_id": self.room_id,
            "messages": [msg.to_dict() for msg in self.messages],
            "last_updated": self.last_updated.isoformat(),
            "message_count": self.message_count
        }


class ConnectionInfo(BaseModel):
    """WebSocket connection information"""
    user_id: str
    room_id: str
    connected_at: datetime = Field(default_factory=datetime.utcnow)
    last_ping: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True


# Response models for API
class JoinRoomResponse(BaseModel):
    success: bool
    room: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
    user_count: int = 0
    recent_messages: List[Dict[str, Any]] = []


class MessageResponse(BaseModel):
    success: bool
    message: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class ErrorResponse(BaseModel):
    error: str
    details: Optional[str] = None


class SystemMessage(BaseModel):
    """System-generated messages"""
    type: str  # join, leave, rename, etc.
    username: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    message: str
    room_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "username": self.username,
            "timestamp": self.timestamp.isoformat(),
            "message": self.message,
            "room_id": self.room_id
        }


class RoomListResponse(BaseModel):
    """Response for listing available rooms"""
    rooms: List[Dict[str, Any]]
    total_rooms: int


# For backward compatibility
class LegacyMessage(BaseModel):
    """Backward compatible message model"""
    message: str 