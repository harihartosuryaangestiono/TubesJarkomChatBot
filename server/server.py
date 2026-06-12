#!/usr/bin/env python3
"""
Tujuan:
- Entry point utama ke server
- Menghandle koneksi client
- Menghandle sistem chat

Version: 1.0.0
"""

import socket
import threading
import sys
import signal
from typing import Dict, Optional

from utils import (
    DEFAULT_HOST, DEFAULT_PORT, MAX_CONNECTIONS, BUFFER_SIZE,
    log_event, PacketType, create_packet, NotificationType
)
from database_manager import DatabaseManager
from room_manager import RoomManager
from client_handler import ClientHandler


class ChatServer:
    """    
    Mengurus:
    - Koneksi client
    - User authentication
    - Manajemen Room
    - Message broadcasting
    - 'Graceful shutdown'
    """

    def __init__(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT):
        """
         Menginisialisasi server        
        Cat:
            host: Host address di mana default 0.0.0.0
            port: Port number di mana default 5000
        """
        self.host = host
        self.port = port
        self.server_socket: Optional[socket.socket] = None
        self.is_running = False
        
        # Inisialisasi database
        self.db = DatabaseManager()
        
        # Inisialisasi room manager
        self.room_manager = RoomManager(self.db)
        
        # Track client2 yang terhubung
        self.clients: Dict[str, ClientHandler] = {}
        self.clients_lock = threading.Lock()
        
        log_event("SERVER", f"Server initialized on {host}:{port}")

    def start(self):
        """Start the chat server."""
        try:
            # Create server socket
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # Bind ke host address
            self.server_socket.bind((self.host, self.port))
            
            # Pantau/listen untuk koneksi 
            self.server_socket.listen(MAX_CONNECTIONS)
            self.is_running = True
            
            log_event("SERVER", f"Server started on {self.host}:{self.port}")
            print(f"\n{'='*50}")
            print(f"Chat Server Running")
            print(f"Host: {self.host}")
            print(f"Port: {self.port}")
            print(f"{'='*50}\n")
            
            # Setup signal handler 
            # Dipakai untuk graceful shutdown
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
            
            # Accept loop koneksi
            while self.is_running:
                try:
                    # Terima koneksi baru
                    client_socket, address = self.server_socket.accept()
                    client_socket.settimeout(60)  # 60 second timeout
                    
                    log_event("SERVER", f"New connection from {address}")
                    
                    # Create & start client handler
                    client_handler = ClientHandler(
                        client_socket=client_socket,
                        address=address,
                        server=self,
                        room_manager=self.room_manager,
                        database_manager=self.db
                    )
                    client_handler.start()
                    
                except socket.timeout:
                    continue
                except OSError:
                    # Socket closed
                    break
                except Exception as e:
                    log_event("SERVER", f"Error accepting connection: {e}", "error")
                    
        except Exception as e:
            log_event("SERVER", f"Server error: {e}", "error")
            print(f"Server error: {e}")
        finally:
            self.shutdown()

    def stop(self):
        """Stop the server gracefully."""
        log_event("SERVER", "Stopping server...")
        self.is_running = False
        
        # Tutup server socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
            self.server_socket = None

    def shutdown(self):
        """Full server shutdown with cleanup."""
        log_event("SERVER", "Shutting down server...")
        
        # Berhenti accept koneksi baru
        self.stop()
        
        # Disconnect semua client
        with self.clients_lock:
            clients_to_disconnect = list(self.clients.values())
        
        for client in clients_to_disconnect:
            try:
                # Notify client bahwa server shutdown
                shutdown_packet = create_packet(PacketType.NOTIFICATION, {
                    "notification_type": "server_shutdown",
                    "message": "Server is shutting down"
                })
                client.send_packet(shutdown_packet)
                client.disconnect()
            except:
                pass
        
        # Clear dictionary client
        with self.clients_lock:
            self.clients.clear()
        
        # Data/stat final tentang chatroom
        stats = self.db.get_stats()
        log_event("SERVER", f"Final stats - Users: {stats['total_users']}, "
                           f"Rooms: {stats['active_rooms']}, "
                           f"Messages: {stats['total_messages']}")
        
        log_event("SERVER", "Server shutdown complete")
        print("\nServer stopped.")

    def _signal_handler(self, signum, frame):
        """Handle signal sistem untuk graceful shutdown."""
        signal_name = "SIGINT" if signum == signal.SIGINT else "SIGTERM"
        log_event("SERVER", f"Received {signal_name}, shutting down...")
        print(f"\nReceived {signal_name}, shutting down gracefully...")
        self.stop()

    def register_user(self, username: str, client_handler: ClientHandler):
        """
        Register user --yang terotentikasi--
        """
        with self.clients_lock:
            self.clients[username] = client_handler
        
        log_event("SERVER", f"User registered: {username}")
        print(f"[+] User logged in: {username}")

    def unregister_user(self, username: str):
        """ Unregister user yang disconnected  """
        with self.clients_lock:
            if username in self.clients:
                del self.clients[username]
        
        log_event("SERVER", f"User unregistered: {username}")
        print(f"[-] User logged out: {username}")

    def is_username_taken(self, username: str) -> bool:
        with self.clients_lock:
            return username in self.clients

    def get_active_users(self):
        """Mengembalikan username dari user-user aktif"""
        with self.clients_lock:
            return list(self.clients.keys())

    def get_user_handler(self, username: str) -> Optional[ClientHandler]:
        with self.clients_lock:
            return self.clients.get(username)

    def get_stats(self) -> Dict:
        with self.clients_lock:
            active_users = len(self.clients)
        
        db_stats = self.db.get_stats()
        
        return {
            "active_connections": active_users,
            **db_stats
        }


def print_server_info():
    """Print info server di startup."""
    print(r"""
    __  __       _ _   _ _    _ _    _ _            _____ _           _   
    |  \/  |     | | | (_) |  | | |  | (_)          / ____| |         | |  
    | \  / | ___ | | |_ _| |__| | |__| |_ _ __ ___ | |    | |__   __ _| |_ 
    | |\/| |/ _ \| | __| |  __  |  __  | | '_ ` _ \| |    | '_ \ / _` | __|
    | |  | | (_) | | |_| | |  | | |  | | | | | | | | |____| | | | (_| | |_ 
    |_|  |_|\___/|_|\__|_|_|  |_|_|  |_|_|_| |_| |_|\_____|_| |_|\__,_|\__|
    """)
    print("DodoTalk Server v1.0.0")
    print("(˶ˆᗜˆ˵) Built with Python Socket Programming!!! (˶ˆᗜˆ˵)")
    print("-" * 50)


def main():
    import argparse
    
    # Parsing argumen cmd line 
    parser = argparse.ArgumentParser(description="Multiple Chat Rooms Server")
    parser.add_argument(
        "--host",
        default=DEFAULT_HOST,
        help=f"Host address to bind to (default: {DEFAULT_HOST})"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"Port number to listen on (default: {DEFAULT_PORT})"
    )
    args = parser.parse_args()
    
    # Print server info
    print_server_info()
    
    # Create & start server
    server = ChatServer(host=args.host, port=args.port)
    
    try:
        server.start()
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    finally:
        server.shutdown()


if __name__ == "__main__":
    main()
