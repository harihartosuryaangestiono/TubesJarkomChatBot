# Multiple Chat Rooms

Aplikasi desktop chatting multi-user berbasis room/chat room dengan arsitektur client-server menggunakan Python socket programming.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![PyQt5](https://img.shields.io/badge/PyQt5-5.15+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

-- Fitur Utama --
Login User — Setiap user masuk pakai username unik, jadi nggak ada yang namanya sama
Lobby — Halaman utama yang nampilkan semua room yang lagi aktif
Buat Room — Siapapun bisa buat room baru, dan yang buat otomatis jadi admin
Chat Multi-User — Banyak user bisa masuk ke room yang sama dan ngobrol secara realtime
Daftar User — Bisa lihat siapa aja yang lagi online di room, plus ada notifikasi kalau ada yang masuk atau keluar
UI Chat — Pesan ditampilkan dalam bentuk bubble dengan timestamp, dan otomatis scroll ke bawah
Keluar Room — Bisa keluar dari room kapan aja, dan user lain bakal dapat notifikasinya
Kontrol Admin — Yang punya room bisa kick user, tutup room, atau hapus room

-- Fitur Tambahan --
Database SQLite — Data user, room, dan riwayat chat disimpan secara persisten
Transfer File — Bisa kirim gambar atau file langsung di dalam room
Emoji — Ada emoji picker dengan 100+ pilihan emoji
Dark Mode — Tema gelap modern, tampilannya mirip Discord atau Telegram
Typing Indicator — Muncul tulisan "User is typing..." kalau ada yang lagi ngetik

-- Struktur Proyek --

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

-- Cara Menjalankan -- 
Prerequisite:
- >= Python 3.8 
- PyQt5

Instalasi:
1. Clone atau extract project
```bash
cd Tubes_Jarkom
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

Jalankan Server:
```bash
cd server
python server.py
```

**Untuk ganti host atau port, bisa menggunakan argumen opsional:**
```bash
python server.py --host 0.0.0.0 --port 5000
```

Server akan berjalan pada default: `127.0.0.1:5000`. Dapat diakses dari komputer lain dalam jaringan yang sama

Menjalankan Client
```bash
cd client
python client.py --host 192.168.1.x --port 5000
```

*(Ganti `192.168.1.x` dengan IP address server)*

-- Alur Komunikasi Socket --
Arsitektur Client-Server

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

Format Paket JSON
Semua komunikasi antara client dan server menggunakan format JSON, contohnya:

```json
{
    "type": "message",
    "room": "Room1",
    "sender": "Andi",
    "message": "Halo semua!",
    "timestamp": "2024-01-20T14:30:00"
}
```

Jenis Paket
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

-- Tampilan UI --
1. Login Window
Tampilan awal dengan dark theme. User bisa input alamat server dan username, ada validasi realtime dan loading indicator saat konek.
2. Lobby Window
Halaman utama setelah login. Ada sidebar navigasi, daftar room beserta info (nama, owner, jumlah member), tombol buat room baru, dan indikator status koneksi.
3. Chat Window
Tampilan ruang chat utama. Ada panel chat dengan bubble message, sidebar daftar user yang ada di room, area input lengkap dengan emoji picker dan tombol upload file, typing indicator, dan menu khusus buat owner room.

-- Skema DB --

Tabel User
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active INTEGER DEFAULT 0
);
```

Tabel Rooms
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

Tabel Chat History
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

-- Troubleshooting --

JIKA server tidak bisa diakses dari komputer lain
1) Pastikan firewall mengizinkan port 5000
2) Cek IP lokal kamu dengan ipconfig (Windows) atau ifconfig (Linux/Mac)
3) Jalankan server dengan --host 0.0.0.0 supaya bisa diakses dari luar

ModuleNotFoundError:
```bash
pip install PyQt5
```

| Database locked
- Hentikan semua client dan server
- Hapus file `database/chat_app.db`
- Jalankan ulang server (database akan dibuat otomatis)

-- Fungsionalitas -- 

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

---
