#!/usr/bin/env python3
"""
Chat Client - Multiple Chat Rooms Application
Main client entry point with PyQt5 GUI.

Author: Multiple Chat Rooms Team
Version: 1.0.0
"""

import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from client_network import ChatClient
from login_window import LoginWindow
from lobby_window import LobbyWindow
from chat_window import ChatWindow


class ChatApplication:
    """
    Main application controller.
    Manages window transitions and client state.
    """
    
    def __init__(self):
        """Initialize application."""
        self.app = QApplication(sys.argv)
        self.client = ChatClient()
        self.current_window = None
        self.chat_window = None
        
        # Set font dalam aplikasi
        font = QFont("Segoe UI", 10)
        self.app.setFont(font)
        
        # Set style aplikasi
        self.app.setStyle('Fusion')
    
    def run(self):
        """Start the application."""
        self.show_login()
        return self.app.exec_()
    
    def show_login(self):
        """Show login window."""
        self.current_window = LoginWindow(self.client)
        self.current_window.show()
        
        # Hubungkan ke lobby setelah login berhasil
        self.client.login_response.connect(self.on_login_success)
    
    def on_login_success(self, success: bool, message: str, username: str):
        """Handle successful login."""
        if success:
            # Tutup login window
            if self.current_window:
                self.current_window.close()
                self.current_window = None
            
            # Tampilkan lobby
            self.show_lobby()
    
    def show_lobby(self):
        """Show lobby window."""
        self.current_window = LobbyWindow(self.client)
        self.current_window.join_room_requested.connect(self.on_join_room)
        self.current_window.show()
        
        # Menghubungkan sinyal join room
        self.client.room_joined.connect(self.on_room_joined)
    
    def on_join_room(self, room_name: str):
        """Handle join room request from lobby."""
        pass  # Diatasi oleh room_joined signal
    
    def on_room_joined(
        self,
        success: bool,
        message: str,
        room_name: str,
        history: list,
        members: list,
        owner: str,
        is_owner: bool
    ):
        """Handle room join response."""
        if success:
            # Sembunyikan lobby
            if self.current_window:
                self.current_window.hide()
            
            # Tampilkan chat window
            self.chat_window = ChatWindow(self.client, room_name, is_owner)
            self.chat_window.back_to_lobby.connect(self.on_back_to_lobby)
            
            # memuat histori chat 
            for msg in history:
                sender = msg.get("sender_username", "Unknown")
                content = msg.get("message", "")
                timestamp = msg.get("timestamp", "")
                msg_type = msg.get("message_type", "text")
                
                is_own = sender == self.client.username
                self.chat_window.add_message(sender, content, timestamp, is_own)
            
            # Tambahkan pesan sistem pertama
            self.chat_window.add_system_message(f"Joined room: {room_name}")
            
            self.chat_window.show()
    
    def on_back_to_lobby(self):
        """Handle return to lobby from chat."""
        if self.chat_window:
            self.chat_window.close()
            self.chat_window = None
        
        # Tampilkan lobby lagi
        if self.current_window:
            self.current_window.show()
            self.current_window.refresh_room_list()


def print_client_info():
    """Print client startup information."""
    print(r"""
     ____ _           _   _             _____ _ _            _   
    / ___| |__   __ _| |_(_)_ __   __ _|  ___(_) | ___ _ __ | |_ 
   | |   | '_ \ / _` | __| | '_ \ / _` | |_  | | |/ _ \ '_ \| __|
   | |___| | | | (_| | |_| | | | | (_| |  _| | | |  __/ | | | |_ 
    \____|_| |_|\__,_|\__|_|_| |_|\__, |_|   |_|_|\___|_| |_|\__|
                                 |___/                           
    """)
    print("Multiple Chat Rooms Client v1.0.0")
    print("Built with Python & PyQt5")
    print("-" * 50)


def main():
    """Main entry point."""
    import argparse
    
    # Membaca argumen dari command line
    parser = argparse.ArgumentParser(description="Multiple Chat Rooms Client")
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Server host address (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5000,
        help="Server port (default: 5000)"
    )
    args = parser.parse_args()
    
    # Print info client 
    print_client_info()
    
    # buat dan jalankan application
    app = ChatApplication()
    
    # Set default host/port dari args
    app.client.host = args.host
    app.client.port = args.port
    
    try:
        sys.exit(app.run())
    except KeyboardInterrupt:
        print("\nInterrupted by user")


if __name__ == "__main__":
    main()
