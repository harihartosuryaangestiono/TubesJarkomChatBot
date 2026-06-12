"""
Chat window untuk chat client
Main chat interface dengan message display, user list, dan input
"""

import os
import base64
from datetime import datetime
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QListWidget, QListWidgetItem, QMessageBox,
    QMenu, QAction, QFileDialog, QScrollArea, QFrame, QSpacerItem,
    QSizePolicy, QTextEdit, QDialog, QGridLayout, QApplication
)
from PyQt5.QtCore import Qt, QTimer, QSize, pyqtSignal
from PyQt5.QtGui import QFont, QPixmap, QImage, QBrush, QColor

from styles import get_style, COLORS, EMOJIS


class EmojiPicker(QDialog):
    """Emoji picker dialog"""
    
    emoji_selected = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Emoji")
        self.setFixedSize(350, 400)
        self.setStyleSheet(get_style("emoji"))
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Grid untuk emojis
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        grid_widget = QWidget()
        grid = QGridLayout(grid_widget)
        grid.setSpacing(5)
        
        row, col = 0, 0
        for emoji in EMOJIS:
            btn = QPushButton(emoji)
            btn.setFixedSize(40, 40)
            btn.clicked.connect(lambda checked, e=emoji: self.select_emoji(e))
            grid.addWidget(btn, row, col)
            col += 1
            if col >= 7:
                col = 0
                row += 1
        
        scroll.setWidget(grid_widget)
        layout.addWidget(scroll)
    
    def select_emoji(self, emoji: str):
        """Menangani emoji selection"""
        self.emoji_selected.emit(emoji)
        self.accept()


class MessageBubble(QFrame):
    """Custom message bubble widget"""
    
    def __init__(self, sender: str, message: str, timestamp: str, is_own: bool, parent=None):
        super().__init__(parent)
        self.is_own = is_own
        self.setup_ui(sender, message, timestamp)
    
    def setup_ui(self, sender: str, message: str, timestamp: str):
        # Set style berdasarkan sender
        if self.is_own:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {COLORS['bubble_own']};
                    border-radius: 16px;
                    padding: 2px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {COLORS['bubble_other']};
                    border-radius: 16px;
                    padding: 2px;
                }}
            """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(4)
        
        # Nama sender (hanya untuk user selain sender)
        if not self.is_own:
            sender_label = QLabel(sender)
            sender_label.setStyleSheet(f"""
                color: {COLORS['accent']};
                font-weight: bold;
                font-size: 12px;
            """)
            layout.addWidget(sender_label)
        
        # Message
        message_label = QLabel(message)
        message_label.setWordWrap(True)
        message_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        
        if self.is_own:
            message_label.setStyleSheet(f"""
                color: white;
                font-size: 14px;
            """)
        else:
            message_label.setStyleSheet(f"""
                color: {COLORS['text_primary']};
                font-size: 14px;
            """)
        
        message_label.setMaximumWidth(500)
        layout.addWidget(message_label)
        
        # Timestamp
        time_str = self._format_timestamp(timestamp)
        time_label = QLabel(time_str)
        time_label.setStyleSheet(f"""
            color: {'rgba(255,255,255,0.7)' if self.is_own else COLORS['text_muted']};
            font-size: 10px;
        """)
        layout.addWidget(time_label)
    
    def _format_timestamp(self, timestamp: str) -> str:
        """Format ISO timestamp to readable format."""
        try:
            dt = datetime.fromisoformat(timestamp)
            return dt.strftime("%H:%M")
        except:
            return "--:--"


class SystemMessage(QLabel):
    """System notification message"""
    
    def __init__(self, message: str, parent=None):
        super().__init__(parent)
        self.setText(message)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet(f"""
            color: {COLORS['text_muted']};
            font-size: 12px;
            padding: 8px 16px;
            background-color: {COLORS['bg_tertiary']};
            border-radius: 12px;
        """)
        self.setMaximumWidth(400)


class ChatWindow(QMainWindow):
    """Main chat room window"""
    
    back_to_lobby = pyqtSignal()
    
    def __init__(self, client, room_name: str, is_owner: bool = False, parent=None):
        """
        Initialize chat window.
        
        Args:
            client: ChatClient instance
            room_name: Name of the room
            is_owner: Whether current user is room owner
            parent: Parent widget
        """
        super().__init__(parent)
        self.client = client
        self.room_name = room_name
        self.is_owner = is_owner
        self.users = []
        self.typing_users = []
        self.setup_ui()
        self.connect_signals()
        
        # Typing timer
        self.typing_timer = QTimer()
        self.typing_timer.timeout.connect(self.stop_typing)
        self.typing_timer.setSingleShot(True)
    
    def setup_ui(self):
        """Setup user interface"""
        self.setWindowTitle(f"{self.room_name} - Multiple Chat Rooms")
        self.setMinimumSize(1100, 700)
        self.setStyleSheet(get_style("chat"))
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        
        # Layout utama
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Area chat
        chat_area = QWidget()
        chat_area.setObjectName("chat_area")
        chat_layout = QVBoxLayout(chat_area)
        chat_layout.setContentsMargins(0, 0, 0, 0)
        chat_layout.setSpacing(0)
        
        # Header
        header = QWidget()
        header.setObjectName("header")
        header.setFixedHeight(60)
        header.setStyleSheet(f"""
            background-color: {COLORS['bg_tertiary']};
            border-bottom: 1px solid {COLORS['border']};
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 10, 20, 10)
        
        # Room info
        room_info = QVBoxLayout()
        room_name_label = QLabel(f"# {self.room_name}")
        room_name_label.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            font-weight: bold;
            font-size: 16px;
        """)
        room_info.addWidget(room_name_label)
        
        self.room_status = QLabel("Connected")
        self.room_status.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 12px;")
        room_info.addWidget(self.room_status)
        
        header_layout.addLayout(room_info)
        header_layout.addStretch()
        
        # Kontrol pemilik
        if self.is_owner:
            owner_menu = QPushButton("⚙ Owner Controls")
            owner_menu.setObjectName("secondary")
            owner_menu.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['bg_secondary']};
                    color: {COLORS['text_primary']};
                    border: 1px solid {COLORS['border_light']};
                    border-radius: 4px;
                    padding: 8px 16px;
                }}
                QPushButton:hover {{
                    background-color: {COLORS['bg_tertiary']};
                }}
            """)
            
            # Menu create 
            menu = QMenu(self)
            menu.setStyleSheet(f"""
                QMenu {{
                    background-color: {COLORS['bg_secondary']};
                    border: 1px solid {COLORS['border']};
                    color: {COLORS['text_primary']};
                }}
                QMenu::item:selected {{
                    background-color: {COLORS['accent']};
                }}
            """)
            
            close_action = QAction("Close Room", self)
            close_action.triggered.connect(self.close_room)
            menu.addAction(close_action)
            
            delete_action = QAction("Delete Room", self)
            delete_action.triggered.connect(self.delete_room)
            menu.addAction(delete_action)
            
            owner_menu.setMenu(menu)
            header_layout.addWidget(owner_menu)
        
        # Tombol leave
        leave_btn = QPushButton("Leave Room")
        leave_btn.setObjectName("secondary")
        leave_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['accent_danger']};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background-color: #D84040;
            }}
        """)
        leave_btn.clicked.connect(self.leave_room)
        header_layout.addWidget(leave_btn)
        
        chat_layout.addWidget(header)
        
        # Area messages scroll 
        self.messages_scroll = QScrollArea()
        self.messages_scroll.setWidgetResizable(True)
        self.messages_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.messages_scroll.setStyleSheet(f"background-color: {COLORS['bg_primary']};")
        
        # Messages container
        self.messages_container = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_container)
        self.messages_layout.setAlignment(Qt.AlignTop)
        self.messages_layout.setSpacing(10)
        self.messages_layout.setContentsMargins(20, 20, 20, 20)
        self.messages_layout.addStretch()
        
        self.messages_scroll.setWidget(self.messages_container)
        chat_layout.addWidget(self.messages_scroll, stretch=1)
        
        # Typing indicator
        self.typing_label = QLabel("")
        self.typing_label.setStyleSheet(f"""
            color: {COLORS['text_muted']};
            font-size: 12px;
            font-style: italic;
            padding: 5px 20px;
        """)
        chat_layout.addWidget(self.typing_label)
        
        # Input area
        input_area = QWidget()
        input_area.setObjectName("input_area")
        input_area.setFixedHeight(80)
        input_layout = QHBoxLayout(input_area)
        input_layout.setContentsMargins(20, 15, 20, 15)
        input_layout.setSpacing(10)
        
        # Tombol emoji 
        emoji_btn = QPushButton("😊")
        emoji_btn.setObjectName("emoji_btn")
        emoji_btn.setFixedSize(40, 40)
        emoji_btn.setCursor(Qt.PointingHandCursor)
        emoji_btn.clicked.connect(self.show_emoji_picker)
        input_layout.addWidget(emoji_btn)
        
        # File button
        file_btn = QPushButton("📎")
        file_btn.setObjectName("file_btn")
        file_btn.setFixedSize(40, 40)
        file_btn.setCursor(Qt.PointingHandCursor)
        file_btn.clicked.connect(self.send_file)
        input_layout.addWidget(file_btn)
        
        # Message input
        self.message_input = QLineEdit()
        self.message_input.setObjectName("message_input")
        self.message_input.setPlaceholderText("Type a message...")
        self.message_input.returnPressed.connect(self.send_message)
        self.message_input.textChanged.connect(self.on_typing)
        input_layout.addWidget(self.message_input, stretch=1)
        
        # Tombol send 
        send_btn = QPushButton("Send")
        send_btn.setObjectName("send_btn")
        send_btn.setFixedWidth(80)
        send_btn.setCursor(Qt.PointingHandCursor)
        send_btn.clicked.connect(self.send_message)
        input_layout.addWidget(send_btn)
        
        chat_layout.addWidget(input_area)
        main_layout.addWidget(chat_area, stretch=1)
        
        # Sidebar (list user)
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(220)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(15, 20, 15, 20)
        sidebar_layout.setSpacing(15)
        
        # Header user list 
        users_header = QLabel("MEMBERS")
        users_header.setStyleSheet(f"""
            color: {COLORS['text_muted']};
            font-size: 12px;
            font-weight: bold;
        """)
        sidebar_layout.addWidget(users_header)
        
        # User count
        self.user_count_label = QLabel("0 members")
        self.user_count_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px;")
        sidebar_layout.addWidget(self.user_count_label)
        
        # User list
        self.user_list = QListWidget()
        self.user_list.setObjectName("user_list")
        self.user_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.user_list.customContextMenuRequested.connect(self.show_user_context_menu)
        sidebar_layout.addWidget(self.user_list)
        
        main_layout.addWidget(sidebar)
        
        # Set focus
        self.message_input.setFocus()
    
    def connect_signals(self):
        """Connect signals dan slots"""
        # Client signals
        self.client.message_received.connect(self.on_message_received)
        self.client.typing_indicator.connect(self.on_typing_indicator)
        self.client.user_list_updated.connect(self.on_user_list_updated)
        self.client.notification_received.connect(self.on_notification)
        self.client.file_received.connect(self.on_file_received)
        self.client.kicked_from_room.connect(self.on_kicked)
        self.client.room_closed.connect(self.on_room_closed)
        self.client.disconnected.connect(self.on_disconnected)
        self.client.error_occurred.connect(self.on_error)
    
    def add_message(self, sender: str, message: str, timestamp: str, is_own: bool = False):
        """Menambah message bubble ke chat"""
        bubble = MessageBubble(sender, message, timestamp, is_own)
        
        # Create layout untuk penyelarasan 
        bubble_layout = QHBoxLayout()
        if is_own:
            bubble_layout.addStretch()
            bubble_layout.addWidget(bubble)
        else:
            bubble_layout.addWidget(bubble)
            bubble_layout.addStretch()
        
        # Tambahkan ke tata letak pesan (sebelum bagian spacer di akhir)
        self.messages_layout.insertLayout(
            self.messages_layout.count() - 1, bubble_layout
        )
        
        # Scroll ke paling bawah
        QTimer.singleShot(100, self.scroll_to_bottom)
    
    def add_system_message(self, message: str):
        """Menambahkan system message"""
        sys_msg = SystemMessage(message)
        layout = QHBoxLayout()
        layout.addStretch()
        layout.addWidget(sys_msg)
        layout.addStretch()
        
        self.messages_layout.insertLayout(
            self.messages_layout.count() - 1, layout
        )
        
        QTimer.singleShot(100, self.scroll_to_bottom)
    
    def scroll_to_bottom(self):
        """Scroll messages ke paling bawah"""
        scrollbar = self.messages_scroll.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def send_message(self):
        """Kirim pesan"""
        message = self.message_input.text().strip()
        if message:
            self.client.send_message(self.room_name, message)
            self.message_input.clear()
            self.stop_typing()
    
    def on_typing(self):
        """Menangani typing di input field"""
        if self.message_input.text():
            self.client.send_typing(self.room_name)
            self.typing_timer.start(3000)  # Berhenti mengetik setelah 3 detik
    
    def stop_typing(self):
        """Kirim stop typing indicator"""
        self.client.stop_typing(self.room_name)
    
    def show_emoji_picker(self):
        """Menampilkan emoji picker dialog"""
        picker = EmojiPicker(self)
        picker.emoji_selected.connect(self.insert_emoji)
        picker.exec_()
    
    def insert_emoji(self, emoji: str):
        """Insert emoji ke input field"""
        self.message_input.insert(emoji)
        self.message_input.setFocus()
    
    def send_file(self):
        """Kirim file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select File to Send",
            "", "Images (*.png *.jpg *.jpeg *.gif);;Documents (*.pdf *.txt *.doc *.docx);;All Files (*.*)"
        )
        
        if file_path:
            try:
                # Cek ukuran file
                size = os.path.getsize(file_path)
                if size > 50 * 1024 * 1024:  # limit 50MB 
                    QMessageBox.warning(self, "File Too Large", "File must be smaller than 50MB")
                    return
                
                # Baca dan kirim file
                with open(file_path, 'rb') as f:
                    file_data = f.read()
                
                file_name = os.path.basename(file_path)
                
                # Menentukan tipe file
                ext = os.path.splitext(file_name)[1].lower()
                if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                    file_type = "image"
                elif ext in ['.pdf', '.doc', '.docx', '.txt']:
                    file_type = "document"
                else:
                    file_type = "file"
                
                # Kirim permintaan/penawaran pengiriman file terlebih dahulu
                self.client.send_file_offer(self.room_name, file_name, size, file_type)
                
                # Kirim file sebenarnya
                self.client.send_file(self.room_name, file_name, file_data, file_type)
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to send file: {str(e)}")
    
    def leave_room(self):
        """Meninggalkan room"""
        reply = QMessageBox.question(
            self, "Leave Room",
            f"Leave {self.room_name}?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.client.leave_room(self.room_name)
            self.back_to_lobby.emit()
            self.close()
    
    def close_room(self):
        """Menutup room (khusus owner)"""
        reply = QMessageBox.warning(
            self, "Close Room",
            f"Close room '{self.room_name}'?\n\nAll members will be returned to the lobby.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.client.close_room(self.room_name)
    
    def delete_room(self):
        """Hapus room (khusus owner)"""
        reply = QMessageBox.critical(
            self, "Delete Room",
            f"Delete room '{self.room_name}' permanently?\n\nThis cannot be undone!",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.client.delete_room(self.room_name)
    
    def show_user_context_menu(self, position):
        """Tampilkan context menu untuk user list"""
        if not self.is_owner:
            return
        
        item = self.user_list.itemAt(position)
        if item:
            username = item.text()
            if username == self.client.username:
                return
            
            menu = QMenu(self)
            menu.setStyleSheet(f"""
                QMenu {{
                    background-color: {COLORS['bg_secondary']};
                    border: 1px solid {COLORS['border']};
                    color: {COLORS['text_primary']};
                }}
                QMenu::item:selected {{
                    background-color: {COLORS['accent']};
                }}
            """)
            
            kick_action = QAction(f"Kick {username}", self)
            kick_action.triggered.connect(lambda: self.kick_user(username))
            menu.addAction(kick_action)
            
            menu.exec_(self.user_list.viewport().mapToGlobal(position))
    
    def kick_user(self, username: str):
        """Kick user dari room"""
        reply = QMessageBox.question(
            self, "Kick User",
            f"Kick {username} from the room?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.client.kick_user(self.room_name, username)
    
    # Signal handlers
    def on_message_received(self, room: str, sender: str, message: str, timestamp: str):
        """Menangani pesan masuk"""
        if room == self.room_name:
            is_own = sender == self.client.username
            self.add_message(sender, message, timestamp, is_own)
    
    def on_typing_indicator(self, room: str, typing_users: list):
        """Menangani typing indicator"""
        if room == self.room_name:
            self.typing_users = [u for u in typing_users if u != self.client.username]
            self.update_typing_indicator()
    
    def update_typing_indicator(self):
        """Update typing indicator label"""
        if self.typing_users:
            if len(self.typing_users) == 1:
                self.typing_label.setText(f"{self.typing_users[0]} is typing...")
            elif len(self.typing_users) == 2:
                self.typing_label.setText(f"{self.typing_users[0]} and {self.typing_users[1]} are typing...")
            else:
                self.typing_label.setText("Several people are typing...")
        else:
            self.typing_label.setText("")
    
    def on_user_list_updated(self, room: str, users: list):
        """Menangani user list update"""
        if room == self.room_name or room == "":
            self.users = users
            self.update_user_list()
    
    def update_user_list(self):
        """Update user list widget"""
        self.user_list.clear()
        
        for username in sorted(self.users):
            item = QListWidgetItem(username)
            
            if username == self.client.username:
                item.setText(f"{username} (You)")
                item.setForeground(QBrush(QColor(COLORS['accent'])))
            
            if self.is_owner and username == self.client.username:
                item.setText(f"{username} (You, Owner)")
            elif username == self.client.username:
                item.setText(f"{username} (Owner)")
            
            self.user_list.addItem(item)
        
        self.user_count_label.setText(f"{len(self.users)} member{'s' if len(self.users) != 1 else ''}")
    
    def on_notification(self, notif_type: str, room: str, message: str):
        """Menangani system notification"""
        if room == self.room_name or notif_type in ["user_joined", "user_left", "user_kicked"]:
            self.add_system_message(message)
            
            # Refresh list user
            self.client.request_user_list(self.room_name)
    
    def on_file_received(self, room: str, sender: str, file_name: str, file_type: str, file_data: str):
        """Menangani received file"""
        if room == self.room_name:
            if file_type == "image":
                # Tampilkan image
                try:
                    image_data = base64.b64decode(file_data)
                    image = QImage()
                    image.loadFromData(image_data)
                    pixmap = QPixmap.fromImage(image)
                    
                    # Ubah ukuran jika terlalu besar
                    if pixmap.width() > 400:
                        pixmap = pixmap.scaledToWidth(400, Qt.SmoothTransformation)
                    
                    # Membuat label dengan gambar
                    img_label = QLabel()
                    img_label.setPixmap(pixmap)
                    
                    layout = QHBoxLayout()
                    if sender == self.client.username:
                        layout.addStretch()
                    layout.addWidget(img_label)
                    if sender != self.client.username:
                        layout.addStretch()
                    
                    self.messages_layout.insertLayout(
                        self.messages_layout.count() - 1, layout
                    )
                    
                    self.add_system_message(f"{sender} shared an image: {file_name}")
                    
                except Exception as e:
                    self.add_message(sender, f"[File: {file_name}]", "", sender == self.client.username)
            else:
                self.add_message(sender, f"[File: {file_name}]", "", sender == self.client.username)
    
    def on_kicked(self, room: str, message: str):
        """Menangani saat di kick dari room"""
        if room == self.room_name:
            QMessageBox.warning(self, "Kicked", message)
            self.back_to_lobby.emit()
            self.close()
    
    def on_room_closed(self, room: str, message: str):
        """Menangani room being closed"""
        if room == self.room_name:
            QMessageBox.information(self, "Room Closed", message)
            self.back_to_lobby.emit()
            self.close()
    
    def on_disconnected(self, message: str):
        """Menangani disconnection"""
        QMessageBox.warning(self, "Disconnected", message)
        self.back_to_lobby.emit()
        self.close()
    
    def on_error(self, message: str):
        """Menangani error"""
        # Hanya menampilkan error yang kritis
        if "kick" in message.lower() or "close" in message.lower():
            QMessageBox.critical(self, "Error", message)
    
    def closeEvent(self, event):
        """Menangani window close"""
        # Jangan putuskan koneksi, cukup keluar dari ruangan
        self.client.leave_room(self.room_name)
        self.back_to_lobby.emit()
        event.accept()
