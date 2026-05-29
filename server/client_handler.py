"""
Client handler for the chat server.
Manages individual client connections and message processing.
"""

import socket
import threading
import json
import os
from typing import Optional, Dict, Any
from datetime import datetime

from utils import (
    PacketType, NotificationType, create_packet, encode_packet,
    decode_packet, log_event, BUFFER_SIZE, FILE_CHUNK_SIZE, MAX_FILE_SIZE
)


class ClientHandler(threading.Thread):
    """Handles a single client connection."""

    def __init__(
        self,
        client_socket: socket.socket,
        address: tuple,
        server,
        room_manager,
        database_manager
    ):
        """
        Initialize client handler.
        
        Args:
            client_socket: Socket connection to client
            address: Client address tuple (ip, port)
            server: Reference to main server instance
            room_manager: RoomManager instance
            database_manager: DatabaseManager instance
        """
        super().__init__(daemon=True)
        self.client_socket = client_socket
        self.address = address
        self.server = server
        self.room_manager = room_manager
        self.db = database_manager
        
        self.username: Optional[str] = None
        self.is_authenticated = False
        self.is_running = True
        self.current_room: Optional[str] = None
        
        # File transfer settings
        self.file_transfer_dir = "file_transfers"
        os.makedirs(self.file_transfer_dir, exist_ok=True)

    def run(self):
        """Main client handling loop."""
        log_event("CLIENT", f"Client connected from {self.address}")
        
        try:
            while self.is_running:
                # Receive data from client
                data = self._receive_data()
                if not data:
                    break
                
                # Process the packet
                self._process_packet(data)
                
        except ConnectionResetError:
            log_event("CLIENT", f"Connection reset by {self.username or self.address}")
        except ConnectionAbortedError:
            log_event("CLIENT", f"Connection aborted by {self.username or self.address}")
        except Exception as e:
            log_event("CLIENT", f"Error handling client {self.username or self.address}: {e}", "error")
        finally:
            self._cleanup()

    def _receive_data(self) -> Optional[bytes]:
        """Receive data from client socket."""
        try:
            data = self.client_socket.recv(BUFFER_SIZE)
            if not data:
                return None
            return data
        except socket.timeout:
            return b""
        except Exception as e:
            log_event("CLIENT", f"Receive error: {e}", "error")
            return None

    def _process_packet(self, data: bytes):
        """Process received packet."""
        packet = decode_packet(data)
        if not packet:
            return

        packet_type = packet.get("type")
        
        # Log received packet (excluding file data)
        if packet_type != PacketType.FILE.value:
            log_event("PACKET", f"Received {packet_type} from {self.username or 'unknown'}")

        # Route to appropriate handler
        handlers = {
            PacketType.LOGIN.value: self._handle_login,
            PacketType.CREATE_ROOM.value: self._handle_create_room,
            PacketType.JOIN_ROOM.value: self._handle_join_room,
            PacketType.LEAVE_ROOM.value: self._handle_leave_room,
            PacketType.MESSAGE.value: self._handle_message,
            PacketType.TYPING.value: self._handle_typing,
            PacketType.TYPING_STOP.value: self._handle_typing_stop,
            PacketType.ROOM_LIST.value: self._handle_room_list,
            PacketType.USER_LIST.value: self._handle_user_list,
            PacketType.KICK_USER.value: self._handle_kick_user,
            PacketType.CLOSE_ROOM.value: self._handle_close_room,
            PacketType.DELETE_ROOM.value: self._handle_delete_room,
            PacketType.DISCONNECT.value: self._handle_disconnect,
            PacketType.FILE.value: self._handle_file,
            PacketType.FILE_OFFER.value: self._handle_file_offer,
        }

        handler = handlers.get(packet_type)
        if handler:
            handler(packet)
        else:
            log_event("PACKET", f"Unknown packet type: {packet_type}", "warning")

    def _handle_login(self, packet: Dict[str, Any]):
        """Handle user login."""
        username = packet.get("username", "").strip()
        
        # Validate username
        from utils import validate_username
        is_valid, error_msg = validate_username(username)
        
        if not is_valid:
            response = create_packet(PacketType.LOGIN_RESPONSE, {
                "success": False,
                "message": error_msg
            })
            self.send_packet(response)
            return

        # Check if username is already taken by active user
        if self.server.is_username_taken(username):
            response = create_packet(PacketType.LOGIN_RESPONSE, {
                "success": False,
                "message": "Username is already in use"
            })
            self.send_packet(response)
            return

        # Create or update user in database
        if not self.db.user_exists(username):
            success, _ = self.db.create_user(username)
            if not success:
                response = create_packet(PacketType.LOGIN_RESPONSE, {
                    "success": False,
                    "message": "Failed to create user"
                })
                self.send_packet(response)
                return
        else:
            self.db.set_user_active(username, True)

        # Set authenticated
        self.username = username
        self.is_authenticated = True
        self.server.register_user(username, self)

        response = create_packet(PacketType.LOGIN_RESPONSE, {
            "success": True,
            "message": "Login successful",
            "username": username
        })
        self.send_packet(response)
        
        log_event("AUTH", f"User logged in: {username}")

    def _handle_create_room(self, packet: Dict[str, Any]):
        """Handle room creation."""
        if not self._require_auth():
            return

        room_name = packet.get("room_name", "").strip()
        
        # Validate room name
        from utils import validate_room_name
        is_valid, error_msg = validate_room_name(room_name)
        
        if not is_valid:
            response = create_packet(PacketType.CREATE_ROOM_RESPONSE, {
                "success": False,
                "message": error_msg
            })
            self.send_packet(response)
            return

        # Create room
        success, message, room = self.room_manager.create_room(room_name, self.username)
        
        if success:
            # Auto-join creator to room
            self.room_manager.join_room(room_name, self.username, self)
            self.current_room = room_name

        response = create_packet(PacketType.CREATE_ROOM_RESPONSE, {
            "success": success,
            "message": message,
            "room": room_name if success else None
        })
        self.send_packet(response)

    def _handle_join_room(self, packet: Dict[str, Any]):
        """Handle room join request."""
        if not self._require_auth():
            return

        room_name = packet.get("room_name", "").strip()
        
        success, message = self.room_manager.join_room(room_name, self.username, self)
        
        if success:
            self.current_room = room_name
            
            # Get chat history
            history = self.db.get_room_history(room_name)
            
            # Get room info
            room_info = self.room_manager.get_room_info(room_name)
            
            response = create_packet(PacketType.JOIN_ROOM_RESPONSE, {
                "success": True,
                "message": message,
                "room": room_name,
                "history": history,
                "members": room_info.get("members", []) if room_info else [],
                "owner": room_info.get("owner") if room_info else None,
                "is_owner": room_info.get("owner") == self.username if room_info else False
            })
        else:
            response = create_packet(PacketType.JOIN_ROOM_RESPONSE, {
                "success": False,
                "message": message
            })
        
        self.send_packet(response)

    def _handle_leave_room(self, packet: Dict[str, Any]):
        """Handle room leave request."""
        if not self._require_auth():
            return

        room_name = packet.get("room_name", self.current_room)
        
        if room_name:
            success = self.room_manager.leave_room(room_name, self.username)
            if success:
                self.current_room = None

        response = create_packet(PacketType.LEAVE_ROOM_RESPONSE, {
            "success": True,
            "message": f"Left room: {room_name}"
        })
        self.send_packet(response)

    def _handle_message(self, packet: Dict[str, Any]):
        """Handle chat message."""
        if not self._require_auth():
            return

        room_name = packet.get("room")
        message = packet.get("message", "")
        message_type = packet.get("message_type", "text")

        if not room_name or not message:
            return

        # Verify user is in the room
        if self.current_room != room_name:
            error_packet = create_packet(PacketType.ERROR, {
                "message": "You are not in this room"
            })
            self.send_packet(error_packet)
            return

        # Save to database
        self.db.save_message(room_name, self.username, message, message_type)

        # Broadcast to room
        broadcast_packet = create_packet(PacketType.MESSAGE, {
            "room": room_name,
            "sender": self.username,
            "message": message,
            "message_type": message_type,
            "timestamp": datetime.now().isoformat()
        })
        self.room_manager.broadcast_to_room(room_name, broadcast_packet)

    def _handle_typing(self, packet: Dict[str, Any]):
        """Handle typing indicator."""
        if not self._require_auth():
            return

        room_name = packet.get("room")
        if room_name and self.current_room == room_name:
            self.room_manager.set_user_typing(room_name, self.username, True)
            
            # Broadcast typing status
            typing_packet = create_packet(PacketType.TYPING, {
                "room": room_name,
                "username": self.username,
                "typing_users": self.room_manager.get_typing_users(room_name)
            })
            self.room_manager.broadcast_to_room(
                room_name, typing_packet, exclude_username=self.username
            )

    def _handle_typing_stop(self, packet: Dict[str, Any]):
        """Handle typing stop indicator."""
        if not self._require_auth():
            return

        room_name = packet.get("room")
        if room_name and self.current_room == room_name:
            self.room_manager.set_user_typing(room_name, self.username, False)
            
            # Broadcast typing status
            typing_packet = create_packet(PacketType.TYPING_STOP, {
                "room": room_name,
                "username": self.username,
                "typing_users": self.room_manager.get_typing_users(room_name)
            })
            self.room_manager.broadcast_to_room(
                room_name, typing_packet, exclude_username=self.username
            )

    def _handle_room_list(self, packet: Dict[str, Any]):
        """Handle room list request."""
        if not self._require_auth():
            return

        rooms = self.room_manager.get_all_rooms_info()
        
        response = create_packet(PacketType.ROOM_LIST_RESPONSE, {
            "rooms": rooms
        })
        self.send_packet(response)

    def _handle_user_list(self, packet: Dict[str, Any]):
        """Handle user list request."""
        if not self._require_auth():
            return

        room_name = packet.get("room")
        
        if room_name:
            room_info = self.room_manager.get_room_info(room_name)
            users = room_info.get("members", []) if room_info else []
        else:
            users = list(self.server.get_active_users())

        response = create_packet(PacketType.USER_LIST_RESPONSE, {
            "room": room_name,
            "users": users
        })
        self.send_packet(response)

    def _handle_kick_user(self, packet: Dict[str, Any]):
        """Handle user kick request."""
        if not self._require_auth():
            return

        room_name = packet.get("room")
        target_username = packet.get("target_username")

        success, message = self.room_manager.kick_user(
            room_name, self.username, target_username
        )

        response = create_packet(PacketType.SUCCESS if success else PacketType.ERROR, {
            "message": message
        })
        self.send_packet(response)

    def _handle_close_room(self, packet: Dict[str, Any]):
        """Handle room close request."""
        if not self._require_auth():
            return

        room_name = packet.get("room")
        
        # Verify ownership
        if not self.room_manager.is_room_owner(room_name, self.username):
            error_packet = create_packet(PacketType.ERROR, {
                "message": "Only room owner can close the room"
            })
            self.send_packet(error_packet)
            return

        success = self.room_manager.close_room(room_name, self.username)
        
        if success:
            self.current_room = None

        response = create_packet(PacketType.SUCCESS if success else PacketType.ERROR, {
            "message": f"Room '{room_name}' closed successfully" if success else "Failed to close room"
        })
        self.send_packet(response)

    def _handle_delete_room(self, packet: Dict[str, Any]):
        """Handle room delete request."""
        if not self._require_auth():
            return

        room_name = packet.get("room")
        
        # Verify ownership
        if not self.room_manager.is_room_owner(room_name, self.username):
            error_packet = create_packet(PacketType.ERROR, {
                "message": "Only room owner can delete the room"
            })
            self.send_packet(error_packet)
            return

        success = self.room_manager.delete_room(room_name)
        
        if success:
            self.current_room = None

        response = create_packet(PacketType.SUCCESS if success else PacketType.ERROR, {
            "message": f"Room '{room_name}' deleted successfully" if success else "Failed to delete room"
        })
        self.send_packet(response)

    def _handle_file_offer(self, packet: Dict[str, Any]):
        """Handle file offer for transfer."""
        if not self._require_auth():
            return

        room_name = packet.get("room")
        file_name = packet.get("file_name")
        file_size = packet.get("file_size")
        file_type = packet.get("file_type")

        if not room_name or not file_name:
            return

        # Validate file size
        if file_size > MAX_FILE_SIZE:
            error_packet = create_packet(PacketType.ERROR, {
                "message": f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB"
            })
            self.send_packet(error_packet)
            return

        # Broadcast file offer to room
        offer_packet = create_packet(PacketType.FILE_OFFER, {
            "room": room_name,
            "sender": self.username,
            "file_name": file_name,
            "file_size": file_size,
            "file_type": file_type
        })
        self.room_manager.broadcast_to_room(room_name, offer_packet)

    def _handle_file(self, packet: Dict[str, Any]):
        """Handle file transfer."""
        if not self._require_auth():
            return

        room_name = packet.get("room")
        file_name = packet.get("file_name")
        file_data = packet.get("file_data")  # Base64 encoded
        file_type = packet.get("file_type", "unknown")

        if not room_name or not file_name or not file_data:
            return

        # Save file
        try:
            import base64
            file_bytes = base64.b64decode(file_data)
            
            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_filename = f"{timestamp}_{file_name}"
            file_path = os.path.join(self.file_transfer_dir, unique_filename)
            
            with open(file_path, 'wb') as f:
                f.write(file_bytes)

            # Save reference to database
            self.db.save_message(
                room_name, self.username, f"[File: {file_name}]",
                message_type="file", file_path=file_path
            )

            # Broadcast file to room
            broadcast_packet = create_packet(PacketType.FILE, {
                "room": room_name,
                "sender": self.username,
                "file_name": file_name,
                "file_type": file_type,
                "file_data": file_data,
                "timestamp": datetime.now().isoformat()
            })
            self.room_manager.broadcast_to_room(room_name, broadcast_packet)

            log_event("FILE", f"File transferred: {file_name} by {self.username}")

        except Exception as e:
            log_event("FILE", f"File transfer error: {e}", "error")
            error_packet = create_packet(PacketType.ERROR, {
                "message": f"File transfer failed: {str(e)}"
            })
            self.send_packet(error_packet)

    def _handle_disconnect(self, packet: Dict[str, Any]):
        """Handle client disconnect."""
        log_event("CLIENT", f"Client {self.username or self.address} requested disconnect")
        self.is_running = False

    def _require_auth(self) -> bool:
        """Check if client is authenticated."""
        if not self.is_authenticated:
            error_packet = create_packet(PacketType.ERROR, {
                "message": "Authentication required"
            })
            self.send_packet(error_packet)
            return False
        return True

    def send_packet(self, packet: Dict[str, Any]):
        """Send a packet to the client."""
        try:
            data = encode_packet(packet)
            self.client_socket.send(data)
        except Exception as e:
            log_event("CLIENT", f"Failed to send packet: {e}", "error")
            self.is_running = False

    def _cleanup(self):
        """Clean up when client disconnects."""
        log_event("CLIENT", f"Cleaning up client {self.username or self.address}")
        
        if self.username:
            # Handle room leave
            self.room_manager.handle_user_disconnect(self.username)
            
            # Unregister from server
            self.server.unregister_user(self.username)
        
        # Close socket
        try:
            self.client_socket.close()
        except:
            pass

    def disconnect(self):
        """Force disconnect the client."""
        self.is_running = False
        try:
            self.client_socket.close()
        except:
            pass
