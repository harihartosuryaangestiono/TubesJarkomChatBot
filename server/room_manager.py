"""
- Untuk server chat
- Tujuan: 
    - Mengurus pembuatan dan pengelolaan Room
    - User tracking di memory
"""

import threading
from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

from utils import log_event, PacketType, create_packet, NotificationType


@dataclass
class Room:
    """Merepresentasikan 1 chatroom"""
    name: str
    owner: str
    created_at: datetime = field(default_factory=datetime.now)
    members: Dict[str, 'ClientHandler'] = field(default_factory=dict)
    is_closed: bool = False
    typing_users: Set[str] = field(default_factory=set)
    lock: threading.Lock = field(default_factory=threading.Lock)

    def add_member(self, username: str, client_handler: 'ClientHandler'):
        """Tambah member ke chatroom."""
        with self.lock:
            self.members[username] = client_handler

    def remove_member(self, username: str):
        """Remove member dari chatroom."""
        with self.lock:
            if username in self.members:
                del self.members[username]
            self.typing_users.discard(username)

    def get_member_count(self) -> int:
        """Get jumlah member dalam chatroom"""
        with self.lock:
            return len(self.members)

    def get_members_list(self) -> List[str]:
        """Get list of member usernames."""
        with self.lock:
            return list(self.members.keys())

    def broadcast(self, packet: Dict[str, Any], exclude_username: Optional[str] = None):
        """Broadcast sebuah paket ke semua member"""
        with self.lock:
            for username, handler in self.members.items():
                if username != exclude_username:
                    try:
                        handler.send_packet(packet)
                    except Exception as e:
                        log_event("ROOM", f"Failed to send to {username}: {e}", "error")

    def add_typing_user(self, username: str):
        """Tambahkan user ke typing set."""
        with self.lock:
            self.typing_users.add(username)

    def remove_typing_user(self, username: str):
        """Remove user dari typing set."""
        with self.lock:
            self.typing_users.discard(username)

    def get_typing_users(self) -> List[str]:
        """Get list user" yang sedang mengetik."""
        with self.lock:
            return list(self.typing_users)


class RoomManager:
    """Mengurus semua chat room di memory."""

    def __init__(self, database_manager):
        self.db = database_manager
        self.rooms: Dict[str, Room] = {}
        self.lock = threading.Lock()
        self.user_current_room: Dict[str, str] = {}  # Setiap user ada di room mana

    def create_room(self, room_name: str, owner: str) -> tuple[bool, str, Optional[Room]]:
        """
        Catatan:
            room_name: Nama pemilik Room
            owner: Username pemilik Room
        """
        with self.lock:
            if room_name in self.rooms:
                return False, "Room already exists", None

            # Create du database
            success, message = self.db.create_room(room_name, owner)
            if not success:
                return False, message, None

            # Create di memori
            room = Room(name=room_name, owner=owner)
            self.rooms[room_name] = room

            log_event("ROOM", f"Room created: {room_name} by {owner}")
            return True, "Room created successfully", room

    def get_room(self, room_name: str) -> Optional[Room]:
        """Get a room by name."""
        with self.lock:
            return self.rooms.get(room_name)

    def room_exists(self, room_name: str) -> bool:
        """Check if a room exists."""
        with self.lock:
            return room_name in self.rooms

    def delete_room(self, room_name: str) -> bool:
        """Delete a room permanently."""
        with self.lock:
            if room_name not in self.rooms:
                return False

            room = self.rooms[room_name]
            
            # Kirim notifikasi ke semua member
            notification = create_packet(PacketType.NOTIFICATION, {
                "notification_type": NotificationType.ROOM_DELETED.value,
                "room": room_name,
                "message": f"Room '{room_name}' has been deleted by the owner"
            })
            room.broadcast(notification)

            # Remove semua member
            for username in list(room.members.keys()):
                self.user_current_room.pop(username, None)

            # Hapus dari database
            self.db.delete_room(room_name)
            
            # Hapus dari memory
            del self.rooms[room_name]

            log_event("ROOM", f"Room deleted: {room_name}")
            return True

    def close_room(self, room_name: str, closer_username: str) -> bool:
        """Close a room (members return to lobby)."""
        with self.lock:
            if room_name not in self.rooms:
                return False

            room = self.rooms[room_name]
            room.is_closed = True

            # Kirim notif ke semua member
            notification = create_packet(PacketType.NOTIFICATION, {
                "notification_type": NotificationType.ROOM_CLOSED.value,
                "room": room_name,
                "message": f"Room '{room_name}' has been closed by the owner"
            })
            room.broadcast(notification)

            # Remove semua member
            members_list = list(room.members.keys())
            for username in members_list:
                room.remove_member(username)
                self.user_current_room.pop(username, None)
                self.db.remove_room_member(room_name, username)

            # Close in database
            self.db.close_room(room_name)

            # Remove dari Room-room yang sedang aktif
            del self.rooms[room_name]

            log_event("ROOM", f"Room closed: {room_name} by {closer_username}")
            return True

    def join_room(
        self,
        room_name: str,
        username: str,
        client_handler: 'ClientHandler'
    ) -> tuple[bool, str]:
        """
        Menambahkan user ke sebuah chatroom
        
        Catatan:
            room_name: Nama chatroom
            username: Username user
            client_handler: Client handler untuk user
        
        Return: Tuple of (success, message)
        """
        with self.lock:
            if room_name not in self.rooms:
                return False, "Room does not exist"

            room = self.rooms[room_name]
            
            if room.is_closed:
                return False, "Room is closed"

            if username in room.members:
                return False, "Already in this room"

            # Kalau User sedang ada di Room, keluar dari room tersebut 
            if username in self.user_current_room:
                current_room_name = self.user_current_room[username]
                self._leave_room_internal(current_room_name, username)

            # Add ke room yang baru
            room.add_member(username, client_handler)
            self.user_current_room[username] = room_name
            self.db.add_room_member(room_name, username)

            # Notify member2 lain
            notification = create_packet(PacketType.NOTIFICATION, {
                "notification_type": NotificationType.USER_JOINED.value,
                "room": room_name,
                "username": username,
                "message": f"{username} joined the room"
            })
            room.broadcast(notification, exclude_username=username)

            log_event("ROOM", f"{username} joined room: {room_name}")
            return True, "Joined room successfully"

    def leave_room(self, room_name: str, username: str) -> bool:
        """Remove a user from a room."""
        with self.lock:
            return self._leave_room_internal(room_name, username)

    def _leave_room_internal(self, room_name: str, username: str) -> bool:
        """Internal method to remove user from room (must hold lock)."""
        if room_name not in self.rooms:
            return False

        room = self.rooms[room_name]
        
        if username not in room.members:
            return False

        # Remove dari room
        room.remove_member(username)
        self.user_current_room.pop(username, None)
        self.db.remove_room_member(room_name, username)

        # Pastikan room kosong dan tidak dimiliki siapa-siapa 
        if room.get_member_count() == 0 and room.owner != username:
            # (opsional) auto-delete chatroom-chatroom kosong
            pass

        # Notify member lain
        notification = create_packet(PacketType.NOTIFICATION, {
            "notification_type": NotificationType.USER_LEFT.value,
            "room": room_name,
            "username": username,
            "message": f"{username} left the room"
        })
        room.broadcast(notification, exclude_username=username)

        log_event("ROOM", f"{username} left room: {room_name}")
        return True

    def kick_user(
        self,
        room_name: str,
        kicker_username: str,
        target_username: str
    ) -> tuple[bool, str]:
        """        
        Cat:
            room_name: Nama chatroom
            kicker_username: Username yang melakukan kick
            target_username: Username yang dikick
        
        Return: Tuple of (success, message)
        """
        with self.lock:
            if room_name not in self.rooms:
                return False, "Room does not exist"

            room = self.rooms[room_name]

            # Kicker harus owner
            if room.owner != kicker_username:
                return False, "Only room owner can kick users"

            if target_username not in room.members:
                return False, "User is not in this room"

            if target_username == kicker_username:
                return False, "Cannot kick yourself"

            # Get client handlernya target 
            target_handler = room.members.get(target_username)

            # Remove dari room
            room.remove_member(target_username)
            self.user_current_room.pop(target_username, None)
            self.db.remove_room_member(room_name, target_username, is_kicked=True)

            # Notify user yang dikeluarkan
            kick_notification = create_packet(PacketType.NOTIFICATION, {
                "notification_type": NotificationType.USER_KICKED.value,
                "room": room_name,
                "message": f"You have been kicked from '{room_name}'"
            })
            if target_handler:
                try:
                    target_handler.send_packet(kick_notification)
                except Exception as e:
                    log_event("ROOM", f"Failed to notify kicked user: {e}", "error")

            # Notify member lain
            notification = create_packet(PacketType.NOTIFICATION, {
                "notification_type": NotificationType.USER_KICKED.value,
                "room": room_name,
                "username": target_username,
                "message": f"{target_username} was kicked from the room"
            })
            room.broadcast(notification)

            log_event("ROOM", f"{target_username} was kicked from {room_name} by {kicker_username}")
            return True, f"{target_username} has been kicked"

    def get_room_info(self, room_name: str) -> Optional[Dict[str, Any]]:
        with self.lock:
            if room_name not in self.rooms:
                return None

            room = self.rooms[room_name]
            return {
                "name": room.name,
                "owner": room.owner,
                "member_count": room.get_member_count(),
                "members": room.get_members_list(),
                "created_at": room.created_at.isoformat(),
                "is_closed": room.is_closed
            }

    def get_all_rooms_info(self) -> List[Dict[str, Any]]:
        """Informasi semua room YANG AKTIF."""
        with self.lock:
            return [
                {
                    "name": room.name,
                    "owner": room.owner,
                    "member_count": room.get_member_count(),
                    "created_at": room.created_at.isoformat()
                }
                for room in self.rooms.values()
                if not room.is_closed
            ]

    def broadcast_to_room(
        self,
        room_name: str,
        packet: Dict[str, Any],
        exclude_username: Optional[str] = None
    ) -> bool:
        """Broadcast paket ke semua member sebuah Room."""
        with self.lock:
            if room_name not in self.rooms:
                return False

            room = self.rooms[room_name]
            room.broadcast(packet, exclude_username)
            return True

    def get_user_room(self, username: str) -> Optional[str]:
        with self.lock:
            return self.user_current_room.get(username)

    def is_room_owner(self, room_name: str, username: str) -> bool:
        with self.lock:
            if room_name not in self.rooms:
                return False
            return self.rooms[room_name].owner == username

    def handle_user_disconnect(self, username: str):
        with self.lock:
            # Jika user sedang berada di chatroom, keluarkan
            if username in self.user_current_room:
                room_name = self.user_current_room[username]
                self._leave_room_internal(room_name, username)

            # Tandai user sebagai non-aktif in database
            self.db.set_user_active(username, False)

        log_event("ROOM", f"User disconnected: {username}")

    def get_typing_users(self, room_name: str) -> List[str]:
        with self.lock:
            if room_name not in self.rooms:
                return []
            return self.rooms[room_name].get_typing_users()

    def set_user_typing(self, room_name: str, username: str, is_typing: bool):
        with self.lock:
            if room_name not in self.rooms:
                return

            room = self.rooms[room_name]
            if is_typing:
                room.add_typing_user(username)
            else:
                room.remove_typing_user(username)
