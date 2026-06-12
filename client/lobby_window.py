"""
Lobby window untuk chat client
Menampilkan ruangan tersedia dan memperbolehkan pembuatan/join rooms
"""

import sys
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QListWidget, QListWidgetItem, QMessageBox,
    QInputDialog, QLineEdit, QFrame, QSpacerItem, QSizePolicy,
    QMenu, QAction, QStyledItemDelegate
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QFont, QColor, QBrush

from styles import get_style, COLORS


class RoomListItem(QWidget):
    """Custom widget untuk room list items"""
    
    def __init__(self, room_name: str, owner: str, member_count: int, parent=None):
        super().__init__(parent)
        self.room_name = room_name
        self.setup_ui(owner, member_count)
    
    def setup_ui(self, owner: str, member_count: int):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(15)
        
        # Room icon/indicator
        icon_label = QLabel("#")
        icon_label.setStyleSheet(f"""
            background-color: {COLORS['accent']};
            color: white;
            border-radius: 12px;
            padding: 4px 8px;
            font-weight: bold;
            font-size: 12px;
        """)
        icon_label.setFixedSize(24, 24)
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)
        
        # Room info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        
        # Room name
        name_label = QLabel(self.room_name)
        name_label.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            font-weight: bold;
            font-size: 14px;
        """)
        info_layout.addWidget(name_label)
        
        # Room details
        details_label = QLabel(f"Owner: {owner} • {member_count} member{'s' if member_count != 1 else ''}")
        details_label.setStyleSheet(f"""
            color: {COLORS['text_muted']};
            font-size: 11px;
        """)
        info_layout.addWidget(details_label)
        
        layout.addLayout(info_layout, stretch=1)
        
        # Tombol join 
        self.join_btn = QPushButton("Join")
        self.join_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['accent']};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent_hover']};
            }}
        """)
        self.join_btn.setCursor(Qt.PointingHandCursor)
        layout.addWidget(self.join_btn)


class LobbyWindow(QMainWindow):
    """Lobby window showing available rooms"""
    
    join_room_requested = pyqtSignal(str)
    
    def __init__(self, client, parent=None):
        """
        Initialize lobby window.
        
        Args:
            client: ChatClient instance
            parent: Parent widget
        """
        super().__init__(parent)
        self.client = client
        self.current_rooms = []
        self.setup_ui()
        self.connect_signals()
        self.refresh_room_list()
    
    def setup_ui(self):
        """Setup the user interface"""
        self.setWindowTitle(f"Multiple Chat Rooms - Lobby ({self.client.username})")
        self.setMinimumSize(900, 650)
        self.setStyleSheet(get_style("lobby"))
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        
        # Main layout
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Sidebar
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(250)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(20, 20, 20, 20)
        sidebar_layout.setSpacing(20)
        
        # App title di sidebar
        title_label = QLabel("Chat Rooms")
        title_label.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            font-weight: bold;
            font-size: 18px;
        """)
        sidebar_layout.addWidget(title_label)
        
        # User info
        user_frame = QFrame()
        user_frame.setStyleSheet(f"""
            background-color: {COLORS['bg_tertiary']};
            border-radius: 8px;
            padding: 10px;
        """)
        user_layout = QVBoxLayout(user_frame)
        
        user_label = QLabel("Logged in as:")
        user_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px;")
        user_layout.addWidget(user_label)
        
        username_label = QLabel(self.client.username)
        username_label.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            font-weight: bold;
            font-size: 14px;
        """)
        user_layout.addWidget(username_label)
        
        sidebar_layout.addWidget(user_frame)
        
        # Spacer
        sidebar_layout.addSpacerItem(QSpacerItem(
            20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding
        ))
        
        # Tombol disconnect 
        disconnect_btn = QPushButton("Disconnect")
        disconnect_btn.setObjectName("danger")
        disconnect_btn.setCursor(Qt.PointingHandCursor)
        disconnect_btn.clicked.connect(self.on_disconnect)
        sidebar_layout.addWidget(disconnect_btn)
        
        main_layout.addWidget(sidebar)
        
        # Area konten utama
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(30, 30, 30, 30)
        content_layout.setSpacing(20)
        
        # Header
        header = QWidget()
        header.setObjectName("header")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 20, 20, 20)
        
        # Header title
        header_title = QLabel("Available Rooms")
        header_title.setObjectName("title")
        header_title.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            font-weight: bold;
            font-size: 20px;
        """)
        header_layout.addWidget(header_title)
        
        header_layout.addSpacerItem(QSpacerItem(
            40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum
        ))
        
        # Tombol refresh 
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.setObjectName("secondary")
        self.refresh_btn.setCursor(Qt.PointingHandCursor)
        self.refresh_btn.clicked.connect(self.refresh_room_list)
        header_layout.addWidget(self.refresh_btn)
        
        # Tombol create room 
        self.create_btn = QPushButton("+ Create Room")
        self.create_btn.setCursor(Qt.PointingHandCursor)
        self.create_btn.clicked.connect(self.on_create_room)
        header_layout.addWidget(self.create_btn)
        
        content_layout.addWidget(header)
        
        # Room list
        room_list_label = QLabel("Select a room to join or create a new one:")
        room_list_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px;")
        content_layout.addWidget(room_list_label)
        
        # Room list widget
        self.room_list = QListWidget()
        self.room_list.setSpacing(5)
        self.room_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {COLORS['bg_secondary']};
                border: none;
                border-radius: 8px;
                padding: 10px;
            }}
            QListWidget::item {{
                background-color: {COLORS['bg_tertiary']};
                border-radius: 6px;
                margin-bottom: 6px;
                padding: 0px;
            }}
            QListWidget::item:hover {{
                background-color: {COLORS['bg_input']};
            }}
            QListWidget::item:selected {{
                background-color: {COLORS['bg_input']};
                border: 2px solid {COLORS['accent']};
            }}
        """)
        self.room_list.itemClicked.connect(self.on_room_selected)
        content_layout.addWidget(self.room_list)
        
        # Status bar
        self.status_label = QLabel("Connected to server")
        self.status_label.setStyleSheet(f"color: {COLORS['accent_success']}; font-size: 12px;")
        content_layout.addWidget(self.status_label)
        
        main_layout.addWidget(content, stretch=1)
    
    def connect_signals(self):
        """Connect signals dan slots"""
        # Client signals
        self.client.room_list_received.connect(self.on_room_list_received)
        self.client.room_created.connect(self.on_room_created)
        self.client.disconnected.connect(self.on_disconnected)
        self.client.error_occurred.connect(self.on_error)
    
    def refresh_room_list(self):
        """Request room list dari server"""
        self.status_label.setText("Refreshing room list...")
        self.status_label.setStyleSheet(f"color: {COLORS['accent_info']};")
        self.client.request_room_list()
    
    def on_room_list_received(self, rooms):
        """Menangani room list response"""
        self.current_rooms = rooms
        self.update_room_list()
        self.status_label.setText(f"{len(rooms)} room(s) available")
        self.status_label.setStyleSheet(f"color: {COLORS['accent_success']};")
    
    def update_room_list(self):
        """Update room list widget"""
        self.room_list.clear()
        
        if not self.current_rooms:
            # Tampilkan empty state
            empty_item = QListWidgetItem("No rooms available. Create one!")
            empty_item.setFlags(Qt.NoItemFlags)
            empty_item.setTextAlignment(Qt.AlignCenter)
            self.room_list.addItem(empty_item)
            return
        
        for room in self.current_rooms:
            room_name = room.get("name", "Unknown")
            owner = room.get("owner", "Unknown")
            member_count = room.get("member_count", 0)
            
            # Create custom widget untuk room
            room_widget = RoomListItem(room_name, owner, member_count)
            room_widget.join_btn.clicked.connect(
                lambda checked, r=room_name: self.join_room(r)
            )
            
            # Add ke list
            item = QListWidgetItem()
            item.setSizeHint(room_widget.sizeHint())
            item.setData(Qt.UserRole, room_name)
            self.room_list.addItem(item)
            self.room_list.setItemWidget(item, room_widget)
    
    def on_room_selected(self, item):
        """Menangani room selection"""
        room_name = item.data(Qt.UserRole)
        if room_name:
            self.join_room(room_name)
    
    def join_room(self, room_name: str):
        """Join room"""
        self.status_label.setText(f"Joining room: {room_name}...")
        self.client.join_room(room_name)
    
    def on_create_room(self):
        """Tampilkan create room dialog"""
        room_name, ok = QInputDialog.getText(
            self, "Create Room", "Enter room name:",
            QLineEdit.Normal, ""
        )
        
        if ok and room_name:
            room_name = room_name.strip()
            if room_name:
                if len(room_name) < 2:
                    QMessageBox.warning(self, "Invalid Name", "Room name must be at least 2 characters.")
                    return
                if len(room_name) > 30:
                    QMessageBox.warning(self, "Invalid Name", "Room name must be at most 30 characters.")
                    return
                
                self.status_label.setText(f"Creating room: {room_name}...")
                self.client.create_room(room_name)
    
    def on_room_created(self, success: bool, message: str, room_name: str):
        """Menangani room creation response"""
        if success:
            self.status_label.setText(f"Room '{room_name}' created!")
            QMessageBox.information(self, "Success", f"Room '{room_name}' created successfully!")
        else:
            self.status_label.setText("Failed to create room")
            QMessageBox.critical(self, "Error", message)
    
    def on_disconnect(self):
        """Menangani disconnect button"""
        reply = QMessageBox.question(
            self, "Disconnect",
            "Are you sure you want to disconnect?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.client.disconnect()
            self.close()
    
    def on_disconnected(self, message: str):
        """Menangani disconnection"""
        QMessageBox.warning(self, "Disconnected", f"Lost connection to server: {message}")
        self.close()
    
    def on_error(self, message: str):
        """Menangani error"""
        self.status_label.setText(f"Error: {message}")
        self.status_label.setStyleSheet(f"color: {COLORS['accent_danger']};")
        QMessageBox.critical(self, "Error", message)
    
    def closeEvent(self, event):
        """Menangani window close."""
        self.client.disconnect()
        event.accept()
