"""
Utility functions and constants for the chat server.
Contains packet types, helper functions, and logging utilities.
"""

import json
import logging
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('server.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class PacketType(Enum):
    """Packet types for client-server communication."""
    LOGIN = "login"
    LOGIN_RESPONSE = "login_response"
    CREATE_ROOM = "create_room"
    CREATE_ROOM_RESPONSE = "create_room_response"
    JOIN_ROOM = "join_room"
    JOIN_ROOM_RESPONSE = "join_room_response"
    LEAVE_ROOM = "leave_room"
    LEAVE_ROOM_RESPONSE = "leave_room_response"
    MESSAGE = "message"
    TYPING = "typing"
    TYPING_STOP = "typing_stop"
    KICK_USER = "kick_user"
    CLOSE_ROOM = "close_room"
    DELETE_ROOM = "delete_room"
    ROOM_LIST = "room_list"
    ROOM_LIST_RESPONSE = "room_list_response"
    USER_LIST = "user_list"
    USER_LIST_RESPONSE = "user_list_response"
    NOTIFICATION = "notification"
    FILE = "file"
    FILE_OFFER = "file_offer"
    FILE_ACCEPT = "file_accept"
    ERROR = "error"
    SUCCESS = "success"
    DISCONNECT = "disconnect"


class NotificationType(Enum):
    """Types of system notifications."""
    USER_JOINED = "user_joined"
    USER_LEFT = "user_left"
    USER_KICKED = "user_kicked"
    ROOM_CLOSED = "room_closed"
    ROOM_DELETED = "room_deleted"
    FILE_SHARED = "file_shared"


def create_packet(
    packet_type: PacketType,
    data: Dict[str, Any],
    timestamp: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a standardized packet.
    
    Args:
        packet_type: Type of the packet
        data: Packet data/payload
        timestamp: Optional timestamp (auto-generated if not provided)
    
    Returns:
        Dictionary representing the packet
    """
    return {
        "type": packet_type.value if isinstance(packet_type, PacketType) else packet_type,
        "timestamp": timestamp or datetime.now().isoformat(),
        **data
    }


def encode_packet(packet: Dict[str, Any]) -> bytes:
    """
    Encode a packet to bytes for transmission.
    
    Args:
        packet: Dictionary packet to encode
    
    Returns:
        Encoded bytes
    """
    return json.dumps(packet).encode('utf-8')


def decode_packet(data: bytes) -> Optional[Dict[str, Any]]:
    """
    Decode bytes to a packet dictionary.
    
    Args:
        data: Bytes to decode
    
    Returns:
        Decoded packet dictionary or None if decoding fails
    """
    try:
        return json.loads(data.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        logger.error(f"Failed to decode packet: {e}")
        return None


def get_current_timestamp() -> str:
    """Get current timestamp in ISO format."""
    return datetime.now().isoformat()


def format_timestamp(iso_timestamp: str) -> str:
    """Format ISO timestamp to human-readable format."""
    try:
        dt = datetime.fromisoformat(iso_timestamp)
        return dt.strftime("%H:%M:%S")
    except (ValueError, TypeError):
        return "Unknown"


def log_event(event_type: str, details: str, level: str = "info"):
    """Log server events."""
    log_message = f"[{event_type}] {details}"
    if level == "info":
        logger.info(log_message)
    elif level == "warning":
        logger.warning(log_message)
    elif level == "error":
        logger.error(log_message)
    elif level == "debug":
        logger.debug(log_message)


# Server configuration
DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 5000
BUFFER_SIZE = 4096
MAX_CONNECTIONS = 100

# File transfer settings
FILE_CHUNK_SIZE = 8192
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
ALLOWED_FILE_TYPES = {
    'image': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'],
    'document': ['.pdf', '.doc', '.docx', '.txt', '.rtf'],
    'archive': ['.zip', '.rar', '.7z'],
    'other': ['.mp3', '.mp4', '.avi', '.mov']
}


def validate_username(username: str) -> tuple[bool, str]:
    """
    Validate username format.
    
    Args:
        username: Username to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not username:
        return False, "Username cannot be empty"
    
    if len(username) < 3:
        return False, "Username must be at least 3 characters"
    
    if len(username) > 20:
        return False, "Username must be at most 20 characters"
    
    if not username.isalnum() and not all(c.isalnum() or c == '_' for c in username):
        return False, "Username can only contain letters, numbers, and underscores"
    
    return True, ""


def validate_room_name(room_name: str) -> tuple[bool, str]:
    """
    Validate room name format.
    
    Args:
        room_name: Room name to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not room_name:
        return False, "Room name cannot be empty"
    
    if len(room_name) < 2:
        return False, "Room name must be at least 2 characters"
    
    if len(room_name) > 30:
        return False, "Room name must be at most 30 characters"
    
    return True, ""
