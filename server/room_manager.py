"""
Room manager for the chat server.
Handles room creation, management, and user tracking in memory.
"""

import threading
from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

from utils import log_event, PacketType, create_packet, NotificationType


@dataclass
class Room:
    """Represents a chat room."""
    name: str
    owner: str
    created_at: datetime = field(default_factory=datetime.now)
    members: Dict[str, 'ClientHandler'] = field(default_factory=dict)
    is_closed: bool = False
    typing_users: Set[str] = field(default_factory=set)
    lock: threading.Lock = field(default_factory=threading.Lock)

    def add_member(self, username: str, client_handler: 'ClientHandler'):
        """Add a member to the room."""
        with self.lock:
            self.members[username] = client_handler

    def remove_member(self, username: str):
        """Remove a member from the room."""
        with self.lock:
            if username in self.members:
                del self.members[username]
            self.typing_users.discard(username)

    def get_member_count(self) -> int:
        """Get the number of members in the room."""
        with self.lock:
            return len(self.members)

    def get_members_list(self) -> List[str]:
        """Get list of member usernames."""
        with self.lock:
            return list(self.members.keys())

    def broadcast(self, packet: Dict[str, Any], exclude_username: Optional[str] = None):
        """Broadcast a packet to all members."""
        with self.lock:
            for username, handler in self.members.items():
                if username != exclude_username:
                    try:
                        handler.send_packet(packet)
                    except Exception as e:
                        log_event("ROOM", f"Failed to send to {username}: {e}", "error")

    def add_typing_user(self, username: str):
        """Add user to typing set."""
        with self.lock:
            self.typing_users.add(username)

    def remove_typing_user(self, username: str):
        """Remove user from typing set."""
        with self.lock:
            self.typing_users.discard(username)

    def get_typing_users(self) -> List[str]:
        """Get list of users currently typing."""
        with self.lock:
            return list(self.typing_users)


class RoomManager:
    """Manages all chat rooms in memory."""

    def __init__(self, database_manager):
        """
        Initialize room manager.
        
        Args:
            database_manager: DatabaseManager instance for persistence
        """
        self.db = database_manager
        self.rooms: Dict[str, Room] = {}
        self.lock = threading.Lock()
        self.user_current_room: Dict[str, str] = {}  # Track which room each user is in

    def create_room(self, room_name: str, owner: str) -> tuple[bool, str, Optional[Room]]:
        """
        Create a new room.
        
        Args:
            room_name: Name of the room
            owner: Username of the room owner
        
        Returns:
            Tuple of (success, message, room_object)
        """
        with self.lock:
            if room_name in self.rooms:
                return False, "Room already exists", None

            # Create in database
            success, message = self.db.create_room(room_name, owner)
            if not success:
                return False, message, None

            # Create in memory
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
            
            # Notify all members
            notification = create_packet(PacketType.NOTIFICATION, {
                "notification_type": NotificationType.ROOM_DELETED.value,
                "room": room_name,
                "message": f"Room '{room_name}' has been deleted by the owner"
            })
            room.broadcast(notification)

            # Remove all members
            for username in list(room.members.keys()):
                self.user_current_room.pop(username, None)

            # Delete from database
            self.db.delete_room(room_name)
            
            # Remove from memory
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

            # Notify all members
            notification = create_packet(PacketType.NOTIFICATION, {
                "notification_type": NotificationType.ROOM_CLOSED.value,
                "room": room_name,
                "message": f"Room '{room_name}' has been closed by the owner"
            })
            room.broadcast(notification)

            # Remove all members
            members_list = list(room.members.keys())
            for username in members_list:
                room.remove_member(username)
                self.user_current_room.pop(username, None)
                self.db.remove_room_member(room_name, username)

            # Close in database
            self.db.close_room(room_name)

            # Remove from active rooms
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
        Add a user to a room.
        
        Args:
            room_name: Name of the room to join
            username: Username of the joining user
            client_handler: Client handler for the user
        
        Returns:
            Tuple of (success, message)
        """
        with self.lock:
            if room_name not in self.rooms:
                return False, "Room does not exist"

            room = self.rooms[room_name]
            
            if room.is_closed:
                return False, "Room is closed"

            if username in room.members:
                return False, "Already in this room"

            # Leave current room if in one
            if username in self.user_current_room:
                current_room_name = self.user_current_room[username]
                self._leave_room_internal(current_room_name, username)

            # Add to room
            room.add_member(username, client_handler)
            self.user_current_room[username] = room_name
            self.db.add_room_member(room_name, username)

            # Notify other members
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

        # Remove from room
        room.remove_member(username)
        self.user_current_room.pop(username, None)
        self.db.remove_room_member(room_name, username)

        # Check if room is empty and not owned
        if room.get_member_count() == 0 and room.owner != username:
            # Optionally auto-delete empty rooms
            pass

        # Notify other members
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
        Kick a user from a room.
        
        Args:
            room_name: Name of the room
            kicker_username: Username of the user performing the kick
            target_username: Username of the user to kick
        
        Returns:
            Tuple of (success, message)
        """
        with self.lock:
            if room_name not in self.rooms:
                return False, "Room does not exist"

            room = self.rooms[room_name]

            # Verify kicker is owner
            if room.owner != kicker_username:
                return False, "Only room owner can kick users"

            if target_username not in room.members:
                return False, "User is not in this room"

            if target_username == kicker_username:
                return False, "Cannot kick yourself"

            # Get target's client handler
            target_handler = room.members.get(target_username)

            # Remove from room
            room.remove_member(target_username)
            self.user_current_room.pop(target_username, None)
            self.db.remove_room_member(room_name, target_username, is_kicked=True)

            # Notify kicked user
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

            # Notify remaining members
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
        """Get room information."""
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
        """Get information about all active rooms."""
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
        """Broadcast a packet to all members of a room."""
        with self.lock:
            if room_name not in self.rooms:
                return False

            room = self.rooms[room_name]
            room.broadcast(packet, exclude_username)
            return True

    def get_user_room(self, username: str) -> Optional[str]:
        """Get the room name a user is currently in."""
        with self.lock:
            return self.user_current_room.get(username)

    def is_room_owner(self, room_name: str, username: str) -> bool:
        """Check if a user is the owner of a room."""
        with self.lock:
            if room_name not in self.rooms:
                return False
            return self.rooms[room_name].owner == username

    def handle_user_disconnect(self, username: str):
        """Handle user disconnection."""
        with self.lock:
            # Leave current room if in one
            if username in self.user_current_room:
                room_name = self.user_current_room[username]
                self._leave_room_internal(room_name, username)

            # Mark user as inactive in database
            self.db.set_user_active(username, False)

        log_event("ROOM", f"User disconnected: {username}")

    def get_typing_users(self, room_name: str) -> List[str]:
        """Get list of users typing in a room."""
        with self.lock:
            if room_name not in self.rooms:
                return []
            return self.rooms[room_name].get_typing_users()

    def set_user_typing(self, room_name: str, username: str, is_typing: bool):
        """Set typing status for a user."""
        with self.lock:
            if room_name not in self.rooms:
                return

            room = self.rooms[room_name]
            if is_typing:
                room.add_typing_user(username)
            else:
                room.remove_typing_user(username)
