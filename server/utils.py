"""
Function-function utility dan constant untuk server chat 
Mengandung tipe paket, helper functions, dan keperluan logging
"""

import json
import logging
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional

# Konfigurasi logging
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
    """Tipe-tipe paket untuk komunikasi client-server"""
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
    Catatan:
        packet_type: Jenis paket
        data: Paket data/payload
        timestamp: (opsional) timestamp -> auto-generated jika tidak diberikan
    
    Return: Dictionary yang merepresentasikan paket
    """
    return {
        "type": packet_type.value if isinstance(packet_type, PacketType) else packet_type,
        "timestamp": timestamp or datetime.now().isoformat(),
        **data
    }


def encode_packet(packet: Dict[str, Any]) -> bytes:
    """
    Encode sebuah packet menjadi bytes untuk transmisi
    packet: Dictionary packet
    """
    return json.dumps(packet).encode('utf-8')


def decode_packet(data: bytes) -> Optional[Dict[str, Any]]:
    """
    Decode bytes ke packet dictionary.
    Return: hasil decode packet dictionary --> jika gagal tidak return apa-apa
    """
    try:
        return json.loads(data.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        logger.error(f"Failed to decode packet: {e}")
        return None


def get_current_timestamp() -> str:
    """Get timestamp current (ISO format)"""
    return datetime.now().isoformat()


def format_timestamp(iso_timestamp: str) -> str:
    """Format ISO timestamp ke human-readable format"""
    try:
        dt = datetime.fromisoformat(iso_timestamp)
        return dt.strftime("%H:%M:%S")
    except (ValueError, TypeError):
        return "Unknown"


def log_event(event_type: str, details: str, level: str = "info"):
    log_message = f"[{event_type}] {details}"
    if level == "info":
        logger.info(log_message)
    elif level == "warning":
        logger.warning(log_message)
    elif level == "error":
        logger.error(log_message)
    elif level == "debug":
        logger.debug(log_message)


# Konfigurasi server 
DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 5000
BUFFER_SIZE = 4096
MAX_CONNECTIONS = 100

# Setting file transfer
FILE_CHUNK_SIZE = 8192
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
ALLOWED_FILE_TYPES = {
    'image': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'],
    'document': ['.pdf', '.doc', '.docx', '.txt', '.rtf'],
    'archive': ['.zip', '.rar', '.7z'],
    'other': ['.mp3', '.mp4', '.avi', '.mov']
}


def validate_username(username: str) -> tuple[bool, str]:
    if not username:
        return False, "Username tidak boleh kosong"
    
    if len(username) < 3:
        return False, "Username >= 3 characters"
    
    if len(username) > 20:
        return False, "Username <= 20 characters"
    
    if not username.isalnum() and not all(c.isalnum() or c == '_' for c in username):
        return False, "Username hanya dapat mengandung huruf, angka, underscore"
    
    return True, ""


def validate_room_name(room_name: str) -> tuple[bool, str]:
    """Memastikan format nama Room sudah valid """
    if not room_name:
        return False, "Room name tidak boleh kosong"
    
    if len(room_name) < 2:
        return False, "Room name >= 2 characters"
    
    if len(room_name) > 30:
        return False, "Room name <= 30 characters"
    
    return True, ""
