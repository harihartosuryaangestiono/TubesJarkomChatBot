# Multiple Chat Rooms

Aplikasi desktop chatting multi-user berbasis room/chat room dengan arsitektur client-server menggunakan Python socket programming.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![PyQt5](https://img.shields.io/badge/PyQt5-5.15+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## 📋 Fitur Utama

### Core Features
- **Login User** - Sistem autentikasi dengan username unik
- **Lobby System** - Halaman utama menampilkan daftar room
- **Create Room** - Membuat room baru dengan pemilik sebagai admin
- **Multiple Chat Rooms** - Beberapa user dalam satu room, pesan realtime
- **User List** - Daftar user aktif dengan notifikasi join/leave
- **Chat UI Modern** - Bubble chat dengan timestamp dan auto-scroll
- **Leave Room** - Keluar dari room dengan notifikasi
- **Owner Controls** - Kick user, tutup room, hapus room

### Fitur Tambahan
- **Database SQLite** - Penyimpanan user, room, dan riwayat chat
- **File Transfer** - Kirim gambar dan file dalam room
- **Emoji Support** - Emoji picker dengan 100+ emoji
- **Dark Mode UI** - Tema gelap modern seperti Discord/Telegram
- **Typing Indicator** - Menampilkan "User is typing..."

## 🏗️ Struktur Project

```
Tubes_Jarkom/
│
├── server/
│   ├── server.py           # Entry point server
│   ├── room_manager.py     # Manajemen room
│   ├── client_handler.py   # Handler koneksi client
│   ├── database_manager.py # Operasi database
│   └── utils.py            # Utility functions
│
├── client/
│   ├── client.py           # Entry point client
│   ├── client_network.py   # Network layer
│   ├── login_window.py     # UI Login
│   ├── lobby_window.py     # UI Lobby
│   ├── chat_window.py      # UI Chat Room
│   └── styles.py           # Tema dan stylesheet
│
├── database/
│   └── chat_app.db         # SQLite database (auto-generated)
│
├── docs/
│   └── architecture.png    # Diagram arsitektur
│
├── README.md
├── requirements.txt
└── .gitignore
```

## 🚀 Cara Menjalankan

### Prerequisites
- Python 3.8 atau lebih tinggi
- PyQt5

### Installation

1. **Clone atau extract project**
```bash
cd Tubes_Jarkom
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

### Menjalankan Server

```bash
cd server
python server.py
```

**Optional arguments:**
```bash
python server.py --host 0.0.0.0 --port 5000
```

Server akan berjalan pada:
- Default: `127.0.0.1:5000`
- Dapat diakses dari komputer lain dalam jaringan yang sama

### Menjalankan Client

**Client 1:**
```bash
cd client
python client.py
```

**Client 2 (komputer lain dalam jaringan):**
```bash
cd client
python client.py --host 192.168.1.x --port 5000
```

*(Ganti `192.168.1.x` dengan IP address server)*

## 📡 Alur Komunikasi Socket

### Arsitektur Client-Server

```
┌─────────────────┐         TCP Socket         ┌─────────────────┐
│  CLIENT 1       │◄──────────────────────────►│                 │
│  (PyQt5 GUI)    │                            │   SERVER        │
├─────────────────┤                            │   (Python)      │
│  CLIENT 2       │◄──────────────────────────►│   - Threading   │
│  (PyQt5 GUI)    │                            │   - Room Manager│
├─────────────────┤                            │   - Database    │
│  CLIENT N       │◄──────────────────────────►│                 │
│  (PyQt5 GUI)    │                            │                 │
└─────────────────┘                            └─────────────────┘
```

### Format Paket JSON

Setiap komunikasi menggunakan format JSON:

```json
{
    "type": "message",
    "room": "Room1",
    "sender": "Andi",
    "message": "Halo semua!",
    "timestamp": "2024-01-20T14:30:00"
}
```

### Jenis Paket

| Paket | Deskripsi |
|-------|-----------|
| `login` | Autentikasi user |
| `create_room` | Buat room baru |
| `join_room` | Gabung ke room |
| `leave_room` | Keluar dari room |
| `message` | Kirim pesan chat |
| `typing` | Indikator sedang mengetik |
| `kick_user` | Kick user dari room |
| `close_room` | Tutup room |
| `room_list` | Minta daftar room |
| `file` | Transfer file |
| `notification` | Notifikasi sistem |

## 🎨 Tampilan UI

### 1. Login Window
- Modern dark theme
- Input server address dan username
- Validasi realtime
- Loading indicator

### 2. Lobby Window
- Sidebar navigasi
- List room dengan info (nama, owner, jumlah member)
- Tombol create room dan refresh
- Status koneksi

### 3. Chat Window
- Panel chat dengan bubble messages
- Sidebar daftar user
- Input area dengan emoji picker dan file upload
- Typing indicator
- Owner controls menu

## 🗄️ Database Schema

### Tabel Users
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active INTEGER DEFAULT 0
);
```

### Tabel Rooms
```sql
CREATE TABLE rooms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    owner_username TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active INTEGER DEFAULT 1,
    is_closed INTEGER DEFAULT 0
);
```

### Tabel Chat History
```sql
CREATE TABLE chat_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_name TEXT NOT NULL,
    sender_username TEXT NOT NULL,
    message TEXT,
    message_type TEXT DEFAULT 'text',
    file_path TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 👥 Pembagian Tugas (3 Anggota)

### Anggota 1: Server & Networking
**Tanggung Jawab:**
- Implementasi `server.py` (main server)
- Implementasi `client_handler.py` (threading per client)
- Implementasi `utils.py` (packet handling)
- Testing koneksi multi-client
- Dokumentasi alur socket

**File:**
- `server/server.py`
- `server/client_handler.py`
- `server/utils.py`

### Anggota 2: Database & Room Management
**Tanggung Jawab:**
- Implementasi `database_manager.py` (SQLite)
- Implementasi `room_manager.py` (logic room)
- Design database schema
- Implementasi fitur owner (kick, close, delete)
- Testing persistensi data

**File:**
- `server/database_manager.py`
- `server/room_manager.py`
- `database/chat_app.db`

### Anggota 3: Client GUI & User Experience
**Tanggung Jawab:**
- Implementasi `client_network.py` (network client)
- Implementasi `login_window.py` (UI login)
- Implementasi `lobby_window.py` (UI lobby)
- Implementasi `chat_window.py` (UI chat)
- Implementasi `styles.py` (tema dark mode)
- Emoji picker dan file transfer
- Testing UI/UX

**File:**
- `client/client_network.py`
- `client/client.py`
- `client/login_window.py`
- `client/lobby_window.py`
- `client/chat_window.py`
- `client/styles.py`

## 🔧 Troubleshooting

### Server tidak bisa diakses dari komputer lain
1. Pastikan firewall mengizinkan port 5000
2. Gunakan IP address lokal (cek dengan `ipconfig` / `ifconfig`)
3. Jalankan server dengan `--host 0.0.0.0`

### ModuleNotFoundError
```bash
pip install PyQt5
```

### Database locked
- Hentikan semua client dan server
- Hapus file `database/chat_app.db`
- Jalankan ulang server (database akan dibuat otomatis)

## 📊 Testing Checklist

- [x] Server bisa dijalankan
- [x] Client bisa connect ke server
- [x] Login dengan username unik
- [x] Membuat room baru
- [x] Join room
- [x] Mengirim pesan realtime
- [x] Menerima pesan dari user lain
- [x] Notifikasi user join/leave
- [x] Chat history persisten
- [x] Owner bisa kick user
- [x] Owner bisa close room
- [x] Owner bisa delete room
- [x] Typing indicator berfungsi
- [x] Emoji picker berfungsi
- [x] File transfer berfungsi
- [x] Multi-client dalam satu room
- [x] Multiple rooms aktif bersamaan

## 📄 Lisensi

Project ini dibuat untuk keperluan akademik mata kuliah Jaringan Komputer.

## 🙏 Credits

- Python 3.x
- PyQt5
- SQLite3

---

**Kelompok Jaringan Komputer**  
*Tugas Besar - Multiple Chat Rooms*  
Dibuat dengan ❤️ menggunakan Python
