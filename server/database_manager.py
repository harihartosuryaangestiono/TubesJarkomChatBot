"""
Database manager untuk server chat server
Tujuan: Mengurus semua operasi di SQLite database untuk user, room, dan history chat
"""

import sqlite3
import os
import json
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from contextlib import contextmanager

from utils import log_event


class DatabaseManager:
    """Mengurus operasi2 pada DB SQLite yang diperuntukan aplikasi."""
    
    def __init__(self, db_path: str = "database/chat_app.db"):
        """db_path: Path ke file database SQLite"""
        self.db_path = db_path
        self._ensure_db_directory()
        self._init_database()
    
    def _ensure_db_directory(self):
        """Ensure the database directory exists."""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
    
    @contextmanager
    def _get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def _init_database(self):
        """Initialize database tables."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # tabel User
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    is_active INTEGER DEFAULT 0
                )
            ''')
            
            # Table Room
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS rooms (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    owner_username TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active INTEGER DEFAULT 1,
                    is_closed INTEGER DEFAULT 0,
                    FOREIGN KEY (owner_username) REFERENCES users(username)
                )
            ''')
            
            # Tabel sejarah chat
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chat_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    room_name TEXT NOT NULL,
                    sender_username TEXT NOT NULL,
                    message TEXT,
                    message_type TEXT DEFAULT 'text',
                    file_path TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (room_name) REFERENCES rooms(name),
                    FOREIGN KEY (sender_username) REFERENCES users(username)
                )
            ''')
            
            # Table member Room (siapa yang join room apa)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS room_members (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    room_name TEXT NOT NULL,
                    username TEXT NOT NULL,
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    left_at TIMESTAMP,
                    is_kicked INTEGER DEFAULT 0,
                    FOREIGN KEY (room_name) REFERENCES rooms(name),
                    FOREIGN KEY (username) REFERENCES users(username),
                    UNIQUE(room_name, username, joined_at)
                )
            ''')
            
            conn.commit()
            log_event("DATABASE", "Database initialized successfully")
    
    # Operasi untuk User
    def create_user(self, username: str) -> Tuple[bool, str]:
        """
        Create a new user.
        
        Args:
            username: Username to create
        
        Returns:
            Tuple of (success, message)
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO users (username, last_login, is_active) VALUES (?, ?, 1)",
                    (username, datetime.now())
                )
                conn.commit()
                log_event("DATABASE", f"User created: {username}")
                return True, "User created successfully"
        except sqlite3.IntegrityError:
            return False, "Username already exists"
        except Exception as e:
            log_event("DATABASE", f"Error creating user: {e}", "error")
            return False, f"Error: {str(e)}"
    
    def user_exists(self, username: str) -> bool:
        """Check if a user exists in the database."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM users WHERE username = ?", (username,))
            return cursor.fetchone() is not None
    
    def set_user_active(self, username: str, active: bool = True):
        """Set user's active status."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if active:
                cursor.execute(
                    "UPDATE users SET is_active = 1, last_login = ? WHERE username = ?",
                    (datetime.now(), username)
                )
            else:
                cursor.execute(
                    "UPDATE users SET is_active = 0 WHERE username = ?",
                    (username,)
                )
            conn.commit()
    
    def get_user_stats(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user statistics."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM users WHERE username = ?",
                (username,)
            )
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    # Operasi untuk Room
    def create_room(self, room_name: str, owner_username: str) -> Tuple[bool, str]:
        """
        Create a new room.
        
        Args:
            room_name: Name of the room
            owner_username: Username of the room owner
        
        Returns:
            Tuple of (success, message)
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO rooms (name, owner_username) VALUES (?, ?)",
                    (room_name, owner_username)
                )
                conn.commit()
                log_event("DATABASE", f"Room created: {room_name} by {owner_username}")
                return True, "Room created successfully"
        except sqlite3.IntegrityError:
            return False, "Room name already exists"
        except Exception as e:
            log_event("DATABASE", f"Error creating room: {e}", "error")
            return False, f"Error: {str(e)}"
    
    def delete_room(self, room_name: str) -> bool:
        """Delete a room from the database."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM rooms WHERE name = ?", (room_name,))
                conn.commit()
                log_event("DATABASE", f"Room deleted: {room_name}")
                return True
        except Exception as e:
            log_event("DATABASE", f"Error deleting room: {e}", "error")
            return False
    
    def close_room(self, room_name: str) -> bool:
        """Mark a room as closed."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE rooms SET is_closed = 1, is_active = 0 WHERE name = ?",
                    (room_name,)
                )
                conn.commit()
                log_event("DATABASE", f"Room closed: {room_name}")
                return True
        except Exception as e:
            log_event("DATABASE", f"Error closing room: {e}", "error")
            return False
    
    def room_exists(self, room_name: str) -> bool:
        """Check if a room exists."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM rooms WHERE name = ?", (room_name,))
            return cursor.fetchone() is not None
    
    def get_room(self, room_name: str) -> Optional[Dict[str, Any]]:
        """Get room details."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM rooms WHERE name = ?",
                (room_name,)
            )
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    def get_all_rooms(self) -> List[Dict[str, Any]]:
        """Get all active rooms."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM rooms WHERE is_active = 1 AND is_closed = 0"
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def is_room_owner(self, room_name: str, username: str) -> bool:
        """Check if user is room owner."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT 1 FROM rooms WHERE name = ? AND owner_username = ?",
                (room_name, username)
            )
            return cursor.fetchone() is not None
    
    # Operasi untuk Chat History
    def save_message(
        self,
        room_name: str,
        sender_username: str,
        message: str,
        message_type: str = "text",
        file_path: Optional[str] = None
    ) -> bool:
        """Save a message to chat history."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """INSERT INTO chat_history 
                       (room_name, sender_username, message, message_type, file_path) 
                       VALUES (?, ?, ?, ?, ?)""",
                    (room_name, sender_username, message, message_type, file_path)
                )
                conn.commit()
                return True
        except Exception as e:
            log_event("DATABASE", f"Error saving message: {e}", "error")
            return False
    
    def get_room_history(self, room_name: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get chat history for a room."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT * FROM chat_history 
                   WHERE room_name = ? 
                   ORDER BY timestamp DESC 
                   LIMIT ?""",
                (room_name, limit)
            )
            rows = cursor.fetchall()
            return [dict(row) for row in reversed(rows)]
    
    def clear_room_history(self, room_name: str) -> bool:
        """Clear chat history for a room."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM chat_history WHERE room_name = ?", (room_name,))
                conn.commit()
                return True
        except Exception as e:
            log_event("DATABASE", f"Error clearing history: {e}", "error")
            return False
    
    # Operasi untuk handle member2 di Room
    def add_room_member(self, room_name: str, username: str) -> bool:
        """Record a user joining a room."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO room_members (room_name, username) VALUES (?, ?)",
                    (room_name, username)
                )
                conn.commit()
                return True
        except Exception as e:
            log_event("DATABASE", f"Error adding room member: {e}", "error")
            return False
    
    def remove_room_member(
        self,
        room_name: str,
        username: str,
        is_kicked: bool = False
    ) -> bool:
        """Record a user leaving a room."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """UPDATE room_members 
                       SET left_at = ?, is_kicked = ? 
                       WHERE room_name = ? AND username = ? AND left_at IS NULL""",
                    (datetime.now(), 1 if is_kicked else 0, room_name, username)
                )
                conn.commit()
                return True
        except Exception as e:
            log_event("DATABASE", f"Error removing room member: {e}", "error")
            return False
    
    def get_room_member_history(self, room_name: str) -> List[Dict[str, Any]]:
        """Get member history for a room."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT * FROM room_members 
                   WHERE room_name = ? 
                   ORDER BY joined_at DESC""",
                (room_name,)
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def get_user_joined_rooms(self, username: str) -> List[str]:
        """Get list of rooms a user has joined."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT DISTINCT room_name FROM room_members 
                   WHERE username = ? AND left_at IS NULL""",
                (username,)
            )
            rows = cursor.fetchall()
            return [row['room_name'] for row in rows]
    
    # Data chatbot, yaitu jumlah user, jumlah chat, jumlah ruangan aktif
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM rooms WHERE is_active = 1")
            room_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM chat_history")
            message_count = cursor.fetchone()[0]
            
            return {
                "total_users": user_count,
                "active_rooms": room_count,
                "total_messages": message_count
            }
