"""
Login window untuk chat client
Menangani user authentication dan koneksi ke server
"""

import sys
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QFrame, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QPixmap

from styles import get_style, COLORS


class LoginWindow(QDialog):
    """Login dialog untuk chat application."""
    
    def __init__(self, client, parent=None):
        """
        Inisialisasi login window
        
        Args:
            client: ChatClient instance
            parent: Parent widget
        """
        super().__init__(parent)
        self.client = client
        self.setup_ui()
        self.connect_signals()
        self.attempting_login = False
    
    def setup_ui(self):
        """Setup user interface"""
        self.setWindowTitle("Multiple Chat Rooms - Login")
        self.setFixedSize(450, 550)
        self.setStyleSheet(get_style("login"))
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        
        # Spacer di atas
        layout.addSpacerItem(QSpacerItem(
            20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding
        ))
        
        # Logo / Title
        title_label = QLabel("Multiple Chat Rooms")
        title_label.setObjectName("title")
        title_label.setAlignment(Qt.AlignCenter)
        title_font = QFont("Segoe UI", 24, QFont.Bold)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Subtitle
        subtitle_label = QLabel("Welcome back! Let's connect you to the server.")
        subtitle_label.setObjectName("subtitle")
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setWordWrap(True)
        layout.addWidget(subtitle_label)
        
        # Spacer
        layout.addSpacerItem(QSpacerItem(
            20, 30, QSizePolicy.Minimum, QSizePolicy.Fixed
        ))
        
        # Server connection frame
        connection_frame = QFrame()
        connection_frame.setObjectName("frame")
        connection_layout = QVBoxLayout(connection_frame)
        connection_layout.setSpacing(15)
        
        # Server address
        server_label = QLabel("SERVER ADDRESS")
        server_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 12px; font-weight: bold;")
        connection_layout.addWidget(server_label)
        
        server_layout = QHBoxLayout()
        
        self.host_input = QLineEdit()
        self.host_input.setPlaceholderText("127.0.0.1")
        self.host_input.setText("127.0.0.1")
        server_layout.addWidget(self.host_input, 2)
        
        colon_label = QLabel(":")
        colon_label.setStyleSheet(f"color: {COLORS['text_secondary']}; padding: 0 5px;")
        server_layout.addWidget(colon_label)
        
        self.port_input = QLineEdit()
        self.port_input.setPlaceholderText("5000")
        self.port_input.setText("5000")
        self.port_input.setMaximumWidth(80)
        server_layout.addWidget(self.port_input, 1)
        
        connection_layout.addLayout(server_layout)
        
        layout.addWidget(connection_frame)
        
        # Username frame
        username_frame = QFrame()
        username_frame.setObjectName("frame")
        username_layout = QVBoxLayout(username_frame)
        username_layout.setSpacing(15)
        
        # Username label
        username_label = QLabel("USERNAME")
        username_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 12px; font-weight: bold;")
        username_layout.addWidget(username_label)
        
        # Username input
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter your username...")
        self.username_input.setMaxLength(20)
        username_layout.addWidget(self.username_input)
        
        # Hint label
        hint_label = QLabel("Username must be 3-20 characters, alphanumeric only.")
        hint_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px;")
        username_layout.addWidget(hint_label)
        
        layout.addWidget(username_frame)
        
        # Spacer
        layout.addSpacerItem(QSpacerItem(
            20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed
        ))
        
        # Tombol onnect 
        self.connect_btn = QPushButton("Connect & Login")
        self.connect_btn.setCursor(Qt.PointingHandCursor)
        self.connect_btn.setMinimumHeight(45)
        layout.addWidget(self.connect_btn)
        
        # Label loading (awalnya hidden)
        self.loading_label = QLabel("Connecting to server...")
        self.loading_label.setAlignment(Qt.AlignCenter)
        self.loading_label.setStyleSheet(f"color: {COLORS['accent']}; font-size: 14px;")
        self.loading_label.hide()
        layout.addWidget(self.loading_label)
        
        # Spacer at bottom
        layout.addSpacerItem(QSpacerItem(
            20, 60, QSizePolicy.Minimum, QSizePolicy.Expanding
        ))
        
        # Footer
        footer_label = QLabel("Multiple Chat Rooms v1.0 | Socket Programming Project")
        footer_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 10px;")
        footer_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(footer_label)
        
        # Set focus
        self.username_input.setFocus()
    
    def connect_signals(self):
        """Connect signals dan slots"""
        self.connect_btn.clicked.connect(self.on_connect_clicked)
        self.username_input.returnPressed.connect(self.on_connect_clicked)
        
        # Client signals
        self.client.connected.connect(self.on_connected)
        self.client.disconnected.connect(self.on_disconnected)
        self.client.login_response.connect(self.on_login_response)
        self.client.error_occurred.connect(self.on_error)
    
    def on_connect_clicked(self):
        """menangani connect button click"""
        if self.attempting_login:
            return
        
        # Get inputs
        host = self.host_input.text().strip() or "127.0.0.1"
        try:
            port = int(self.port_input.text().strip() or "5000")
        except ValueError:
            self.show_error("Invalid port number")
            return
        
        username = self.username_input.text().strip()
        
        # Validasi username
        if not username:
            self.show_error("Please enter a username")
            return
        
        if len(username) < 3:
            self.show_error("Username must be at least 3 characters")
            return
        
        if len(username) > 20:
            self.show_error("Username must be at most 20 characters")
            return
        
        if not username.replace("_", "").isalnum():
            self.show_error("Username can only contain letters, numbers, and underscores")
            return
        
        # Update client settings
        self.client.host = host
        self.client.port = port
        
        # Tampilkan loading
        self.attempting_login = True
        self.set_controls_enabled(False)
        self.loading_label.setText("Connecting to server...")
        self.loading_label.show()
        
        # Coba untuk connect
        if not self.client.connect_to_server():
            self.attempting_login = False
            self.set_controls_enabled(True)
            self.loading_label.hide()
    
    def set_controls_enabled(self, enabled: bool):
        """Enable/disable controls"""
        self.host_input.setEnabled(enabled)
        self.port_input.setEnabled(enabled)
        self.username_input.setEnabled(enabled)
        self.connect_btn.setEnabled(enabled)
        if enabled:
            self.connect_btn.setText("Connect & Login")
        else:
            self.connect_btn.setText("Connecting...")
    
    def on_connected(self):
        """Menangani Koneksi sukses"""
        self.loading_label.setText("Connected! Logging in...")
        
        # Kirim login request
        QTimer.singleShot(500, lambda: self.client.login(
            self.username_input.text().strip()
        ))
    
    def on_disconnected(self, message: str):
        """Menangani disconnection"""
        self.attempting_login = False
        self.set_controls_enabled(True)
        self.loading_label.hide()
        
        if not self.isHidden():
            self.show_error(f"Connection lost: {message}")
    
    def on_login_response(self, success: bool, message: str, username: str):
        """Menangani login response"""
        if success:
            self.loading_label.setText("Login successful!")
            self.client.username = username
            
            # IMPORTANT: Set attempting_login ke False agar closeEvent tidak disconnect
            self.attempting_login = False
            
            # Tutup dialog dengan sukses
            QTimer.singleShot(500, self.accept)
        else:
            self.attempting_login = False
            self.set_controls_enabled(True)
            self.loading_label.hide()
            self.show_error(f"Login failed: {message}")
    
    def on_error(self, message: str):
        """Menangani error"""
        if not self.attempting_login:
            self.show_error(message)
        elif "Failed to connect" in message:
            self.attempting_login = False
            self.set_controls_enabled(True)
            self.loading_label.hide()
            self.show_error(message)
    
    def show_error(self, message: str):
        """Tampilkan error message"""
        QMessageBox.critical(self, "Error", message)
    
    def closeEvent(self, event):
        """Menangani dialog close"""
        if self.attempting_login:
            self.client.disconnect()
        event.accept()
