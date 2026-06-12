"""
Network client module untuk chat application
Menangani socket connection dan komunikasi dengan server
"""

import socket
import threading
import json
import base64
from typing import Callable, Optional, Dict, Any
from datetime import datetime

from PyQt5.QtCore import QObject, pyqtSignal


class ChatClient(QObject):
    """
    Network client untuk komunikasi chat server 
    Menggunakan Qt signals untuk integrasi GUI 
    """
    
    # Sinyal untuk update GUI 
    connected = pyqtSignal()
    disconnected = pyqtSignal(str)
    login_response = pyqtSignal(bool, str, str)
    room_list_received = pyqtSignal(list)
    room_created = pyqtSignal(bool, str, str)
    room_joined = pyqtSignal(bool, str, str, list, list, str, bool)
    room_left = pyqtSignal(bool, str)
    message_received = pyqtSignal(str, str, str, str)
    typing_indicator = pyqtSignal(str, list)
    user_list_updated = pyqtSignal(str, list)
    notification_received = pyqtSignal(str, str, str)
    error_occurred = pyqtSignal(str)
    file_received = pyqtSignal(str, str, str, str, str)
    kicked_from_room = pyqtSignal(str, str)
    room_closed = pyqtSignal(str, str)
    
    def __init__(self, host: str = "127.0.0.1", port: int = 5000):
        """
        Inisialisasi chat client
        
        Args:
            host: Server host address
            port: Server port number
        """
        super().__init__()
        self.host = host
        self.port = port
        self.socket: Optional[socket.socket] = None
        self.username: Optional[str] = None
        self.is_connected = False
        self.receive_thread: Optional[threading.Thread] = None
        self.lock = threading.Lock()
    
    def connect_to_server(self) -> bool:
        """Connect chat server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.socket.settimeout(30)
            self.is_connected = True
            
            # Start receive thread
            self.receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
            self.receive_thread.start()
            
            self.connected.emit()
            return True
        except Exception as e:
            self.error_occurred.emit(f"Failed to connect: {str(e)}")
            return False
    
    def disconnect(self):
        """Disconnect dari server"""
        self.is_connected = False
        
        if self.socket:
            try:
                # kirim disconnect packet
                self._send_packet({
                    "type": "disconnect",
                    "timestamp": datetime.now().isoformat()
                })
                self.socket.close()
            except:
                pass
            self.socket = None
        
        self.disconnected.emit("Disconnected from server")
    
    def login(self, username: str):
        """Kirim login request"""
        self.username = username
        self._send_packet({
            "type": "login",
            "username": username,
            "timestamp": datetime.now().isoformat()
        })
    
    def create_room(self, room_name: str):
        """Kirim create room request"""
        self._send_packet({
            "type": "create_room",
            "room_name": room_name,
            "timestamp": datetime.now().isoformat()
        })
    
    def join_room(self, room_name: str):
        """Kiriim join room request"""
        self._send_packet({
            "type": "join_room",
            "room_name": room_name,
            "timestamp": datetime.now().isoformat()
        })
    
    def leave_room(self, room_name: str):
        """Kirim leave room request"""
        self._send_packet({
            "type": "leave_room",
            "room_name": room_name,
            "timestamp": datetime.now().isoformat()
        })
    
    def send_message(self, room: str, message: str, message_type: str = "text"):
        """Kirim a chat message"""
        self._send_packet({
            "type": "message",
            "room": room,
            "message": message,
            "message_type": message_type,
            "timestamp": datetime.now().isoformat()
        })
    
    def send_typing(self, room: str):
        """Kirim typing indicator"""
        self._send_packet({
            "type": "typing",
            "room": room,
            "timestamp": datetime.now().isoformat()
        })
    
    def stop_typing(self, room: str):
        """Kirim stop typing indicator"""
        self._send_packet({
            "type": "typing_stop",
            "room": room,
            "timestamp": datetime.now().isoformat()
        })
    
    def request_room_list(self):
        """Request list ruangan tersedia"""
        self._send_packet({
            "type": "room_list",
            "timestamp": datetime.now().isoformat()
        })
    
    def request_user_list(self, room: str):
        """Request list user dalam room"""
        self._send_packet({
            "type": "user_list",
            "room": room,
            "timestamp": datetime.now().isoformat()
        })
    
    def kick_user(self, room: str, target_username: str):
        """Kick user dari room"""
        self._send_packet({
            "type": "kick_user",
            "room": room,
            "target_username": target_username,
            "timestamp": datetime.now().isoformat()
        })
    
    def close_room(self, room: str):
        """Tutup room"""
        self._send_packet({
            "type": "close_room",
            "room": room,
            "timestamp": datetime.now().isoformat()
        })
    
    def delete_room(self, room: str):
        """Hapus room"""
        self._send_packet({
            "type": "delete_room",
            "room": room,
            "timestamp": datetime.now().isoformat()
        })
    
    def send_file_offer(self, room: str, file_name: str, file_size: int, file_type: str):
        """Offer file untuk transfer"""
        self._send_packet({
            "type": "file_offer",
            "room": room,
            "file_name": file_name,
            "file_size": file_size,
            "file_type": file_type,
            "timestamp": datetime.now().isoformat()
        })
    
    def send_file(self, room: str, file_name: str, file_data: bytes, file_type: str):
        """Kirim file ke room"""
        # Encode file data menuju base64
        encoded_data = base64.b64encode(file_data).decode('utf-8')
        
        self._send_packet({
            "type": "file",
            "room": room,
            "file_name": file_name,
            "file_data": encoded_data,
            "file_type": file_type,
            "timestamp": datetime.now().isoformat()
        })
    
    def _send_packet(self, packet: Dict[str, Any]):
        """Kirim packet ke server"""
        with self.lock:
            if self.socket and self.is_connected:
                try:
                    data = json.dumps(packet).encode('utf-8')
                    self.socket.send(data)
                except Exception as e:
                    self.error_occurred.emit(f"Send error: {str(e)}")
                    self.is_connected = False
    
    def _receive_loop(self):
        """Main menerima loop running di thread terpisah"""
        while self.is_connected:
            try:
                data = self.socket.recv(4096)
                if not data:
                    break
                
                # Decode dan proses packet
                packet = json.loads(data.decode('utf-8'))
                self._process_packet(packet)
                
            except socket.timeout:
                continue
            except json.JSONDecodeError:
                continue
            except Exception as e:
                if self.is_connected:
                    self.error_occurred.emit(f"Receive error: {str(e)}")
                break
        
        self.is_connected = False
        self.disconnected.emit("Connection lost")
    
    def _process_packet(self, packet: Dict[str, Any]):
        """Process menerima packet"""
        packet_type = packet.get("type")
        
        if packet_type == "login_response":
            success = packet.get("success", False)
            message = packet.get("message", "")
            username = packet.get("username", "")
            self.login_response.emit(success, message, username)
        
        elif packet_type == "room_list_response":
            rooms = packet.get("rooms", [])
            self.room_list_received.emit(rooms)
        
        elif packet_type == "create_room_response":
            success = packet.get("success", False)
            message = packet.get("message", "")
            room_name = packet.get("room", "")
            self.room_created.emit(success, message, room_name)
        
        elif packet_type == "join_room_response":
            success = packet.get("success", False)
            message = packet.get("message", "")
            room_name = packet.get("room", "")
            history = packet.get("history", [])
            members = packet.get("members", [])
            owner = packet.get("owner", "")
            is_owner = packet.get("is_owner", False)
            self.room_joined.emit(success, message, room_name, history, members, owner, is_owner)
        
        elif packet_type == "leave_room_response":
            success = packet.get("success", False)
            message = packet.get("message", "")
            self.room_left.emit(success, message)
        
        elif packet_type == "message":
            room = packet.get("room", "")
            sender = packet.get("sender", "")
            message = packet.get("message", "")
            timestamp = packet.get("timestamp", "")
            self.message_received.emit(room, sender, message, timestamp)
        
        elif packet_type == "typing":
            room = packet.get("room", "")
            typing_users = packet.get("typing_users", [])
            self.typing_indicator.emit(room, typing_users)
        
        elif packet_type == "typing_stop":
            room = packet.get("room", "")
            typing_users = packet.get("typing_users", [])
            self.typing_indicator.emit(room, typing_users)
        
        elif packet_type == "user_list_response":
            room = packet.get("room", "")
            users = packet.get("users", [])
            self.user_list_updated.emit(room, users)
        
        elif packet_type == "notification":
            notif_type = packet.get("notification_type", "")
            room = packet.get("room", "")
            message = packet.get("message", "")
            
            self.notification_received.emit(notif_type, room, message)
            
            # Handle notifikasi spesifik 
            if notif_type == "user_kicked":
                username = packet.get("username", "")
                self.kicked_from_room.emit(room, message)
            elif notif_type == "room_closed":
                self.room_closed.emit(room, message)
        
        elif packet_type == "error":
            message = packet.get("message", "Unknown error")
            self.error_occurred.emit(message)
        
        elif packet_type == "success":
            message = packet.get("message", "")
            # Dapat memancarkan/mengirim sinyal keberhasilan umum di sini
        
        elif packet_type == "file":
            room = packet.get("room", "")
            sender = packet.get("sender", "")
            file_name = packet.get("file_name", "")
            file_type = packet.get("file_type", "")
            file_data = packet.get("file_data", "")
            timestamp = packet.get("timestamp", "")
            self.file_received.emit(room, sender, file_name, file_type, file_data)
        
        elif packet_type == "file_offer":
            # File offer dari user lain
            room = packet.get("room", "")
            sender = packet.get("sender", "")
            file_name = packet.get("file_name", "")
            file_size = packet.get("file_size", 0)
            file_type = packet.get("file_type", "")
            # Dapat menampilkan dialog file offer di sini
