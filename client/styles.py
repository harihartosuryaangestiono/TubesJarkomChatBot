"""
Styles dan themes untuk UI chat client.
Menggunakan modern dark theme mirip dengan Discord/Telegram.
"""

# Color Palette - Dark Theme
COLORS = {
    # Background colors
    "bg_primary": "#36393F",        # Main background
    "bg_secondary": "#2F3136",      # Secondary background
    "bg_tertiary": "#202225",       # Tertiary background
    "bg_input": "#40444B",          # Input field background
    
    # Text colors
    "text_primary": "#FFFFFF",      # Primary text
    "text_secondary": "#B9BBBE",    # Secondary text
    "text_muted": "#72767D",        # Muted text
    
    # Accent colors
    "accent": "#5865F2",            # Primary accent (Discord purple)
    "accent_hover": "#4752C4",      # Accent hover state
    "accent_success": "#43B581",     # Success green
    "accent_warning": "#FAA61A",     # Warning orange
    "accent_danger": "#F04747",      # Danger red
    "accent_info": "#4FC3F7",        # Info blue
    
    # Message bubbles
    "bubble_own": "#5865F2",         # Own message bubble
    "bubble_other": "#40444B",       # Others message bubble
    
    # Border colors
    "border": "#202225",
    "border_light": "#4F545C",
    
    # Status colors
    "online": "#43B581",
    "away": "#FAA61A",
    "offline": "#747F8D",
}

# Stylesheets
LOGIN_STYLE = f"""
QDialog {{
    background-color: {COLORS["bg_primary"]};
    border-radius: 8px;
}}

QLabel {{
    color: {COLORS["text_primary"]};
    font-family: 'Segoe UI', 'Helvetica Neue', sans-serif;
}}

QLabel#title {{
    font-size: 24px;
    font-weight: bold;
    color: {COLORS["text_primary"]};
}}

QLabel#subtitle {{
    font-size: 14px;
    color: {COLORS["text_secondary"]};
}}

QLineEdit {{
    background-color: {COLORS["bg_input"]};
    color: {COLORS["text_primary"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 4px;
    padding: 10px;
    font-size: 14px;
}}

QLineEdit:focus {{
    border: 2px solid {COLORS["accent"]};
}}

QPushButton {{
    background-color: {COLORS["accent"]};
    color: white;
    border: none;
    border-radius: 4px;
    padding: 12px 24px;
    font-size: 14px;
    font-weight: bold;
}}

QPushButton:hover {{
    background-color: {COLORS["accent_hover"]};
}}

QPushButton:pressed {{
    background-color: {COLORS["accent"]};
}}

QPushButton#secondary {{
    background-color: {COLORS["bg_secondary"]};
    border: 1px solid {COLORS["border_light"]};
}}

QPushButton#secondary:hover {{
    background-color: {COLORS["bg_tertiary"]};
}}
"""

LOBBY_STYLE = f"""
QMainWindow {{
    background-color: {COLORS["bg_primary"]};
}}

QWidget {{
    background-color: {COLORS["bg_primary"]};
    font-family: 'Segoe UI', 'Helvetica Neue', sans-serif;
}}

QWidget#sidebar {{
    background-color: {COLORS["bg_secondary"]};
}}

QWidget#header {{
    background-color: {COLORS["bg_tertiary"]};
    border-bottom: 1px solid {COLORS["border"]};
}}

QLabel {{
    color: {COLORS["text_primary"]};
}}

QLabel#title {{
    font-size: 18px;
    font-weight: bold;
}}

QLabel#room_name {{
    font-size: 16px;
    font-weight: bold;
    color: {COLORS["text_primary"]};
}}

QLabel#room_info {{
    font-size: 12px;
    color: {COLORS["text_muted"]};
}}

QPushButton {{
    background-color: {COLORS["accent"]};
    color: white;
    border: none;
    border-radius: 4px;
    padding: 10px 20px;
    font-weight: bold;
}}

QPushButton:hover {{
    background-color: {COLORS["accent_hover"]};
}}

QPushButton#secondary {{
    background-color: {COLORS["bg_secondary"]};
    border: 1px solid {COLORS["border_light"]};
}}

QPushButton#secondary:hover {{
    background-color: {COLORS["bg_tertiary"]};
}}

QPushButton#danger {{
    background-color: {COLORS["accent_danger"]};
}}

QPushButton#danger:hover {{
    background-color: #D84040;
}}

QListWidget {{
    background-color: {COLORS["bg_secondary"]};
    border: none;
    border-radius: 8px;
    padding: 8px;
}}

QListWidget::item {{
    background-color: {COLORS["bg_tertiary"]};
    border-radius: 4px;
    padding: 12px;
    margin-bottom: 4px;
    color: {COLORS["text_primary"]};
}}

QListWidget::item:hover {{
    background-color: {COLORS["bg_input"]};
}}

QListWidget::item:selected {{
    background-color: {COLORS["accent"]};
}}

QLineEdit {{
    background-color: {COLORS["bg_input"]};
    color: {COLORS["text_primary"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 4px;
    padding: 10px;
}}

QScrollBar:vertical {{
    background-color: {COLORS["bg_secondary"]};
    width: 12px;
    border-radius: 6px;
}}

QScrollBar::handle:vertical {{
    background-color: {COLORS["bg_tertiary"]};
    border-radius: 6px;
    min-height: 20px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {COLORS["bg_input"]};
}}
"""

CHAT_STYLE = f"""
QWidget {{
    background-color: {COLORS["bg_primary"]};
    font-family: 'Segoe UI', 'Helvetica Neue', sans-serif;
}}

QWidget#chat_area {{
    background-color: {COLORS["bg_primary"]};
}}

QWidget#sidebar {{
    background-color: {COLORS["bg_secondary"]};
    border-left: 1px solid {COLORS["border"]};
}}

QWidget#input_area {{
    background-color: {COLORS["bg_secondary"]};
    border-top: 1px solid {COLORS["border"]};
}}

QTextEdit#chat_display {{
    background-color: {COLORS["bg_primary"]};
    color: {COLORS["text_primary"]};
    border: none;
    padding: 10px;
}}

QLineEdit#message_input {{
    background-color: {COLORS["bg_input"]};
    color: {COLORS["text_primary"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 20px;
    padding: 12px 16px;
    font-size: 14px;
}}

QLineEdit#message_input:focus {{
    border: 2px solid {COLORS["accent"]};
}}

QPushButton#send_btn {{
    background-color: {COLORS["accent"]};
    color: white;
    border: none;
    border-radius: 20px;
    padding: 12px 20px;
    font-weight: bold;
}}

QPushButton#emoji_btn {{
    background-color: transparent;
    color: {COLORS["text_secondary"]};
    border: none;
    font-size: 20px;
}}

QPushButton#emoji_btn:hover {{
    color: {COLORS["text_primary"]};
}}

QPushButton#file_btn {{
    background-color: transparent;
    color: {COLORS["text_secondary"]};
    border: none;
    font-size: 16px;
}}

QPushButton#file_btn:hover {{
    color: {COLORS["text_primary"]};
}}

QLabel#username_label {{
    color: {COLORS["text_primary"]};
    font-weight: bold;
    font-size: 14px;
}}

QLabel#timestamp_label {{
    color: {COLORS["text_muted"]};
    font-size: 11px;
}}

QLabel#message_label {{
    color: {COLORS["text_primary"]};
    font-size: 14px;
    padding: 8px 12px;
    border-radius: 16px;
}}

QLabel#message_label_own {{
    background-color: {COLORS["bubble_own"]};
    color: white;
}}

QLabel#message_label_other {{
    background-color: {COLORS["bubble_other"]};
}}

QListWidget#user_list {{
    background-color: {COLORS["bg_secondary"]};
    border: none;
    color: {COLORS["text_secondary"]};
}}

QListWidget#user_list::item {{
    padding: 8px;
    border-radius: 4px;
}}

QListWidget#user_list::item:hover {{
    background-color: {COLORS["bg_tertiary"]};
    color: {COLORS["text_primary"]};
}}

QLabel#typing_indicator {{
    color: {COLORS["text_muted"]};
    font-size: 12px;
    font-style: italic;
}}

QLabel#system_message {{
    color: {COLORS["text_muted"]};
    font-size: 12px;
    padding: 4px;
}}

QScrollBar:vertical {{
    background-color: {COLORS["bg_secondary"]};
    width: 10px;
    border-radius: 5px;
}}

QScrollBar::handle:vertical {{
    background-color: {COLORS["bg_tertiary"]};
    border-radius: 5px;
    min-height: 20px;
}}

QMenu {{
    background-color: {COLORS["bg_secondary"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 4px;
}}

QMenu::item {{
    color: {COLORS["text_primary"]};
    padding: 8px 24px;
}}

QMenu::item:selected {{
    background-color: {COLORS["accent"]};
}}
"""

EMOJI_PICKER_STYLE = f"""
QWidget {{
    background-color: {COLORS["bg_secondary"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 8px;
}}

QPushButton {{
    background-color: transparent;
    border: none;
    font-size: 20px;
    padding: 8px;
}}

QPushButton:hover {{
    background-color: {COLORS["bg_input"]};
    border-radius: 4px;
}}
"""

# Emoji list for picker
EMOJIS = [
    "😀", "😂", "🤣", "😃", "😄", "😅", "😆", "😉", "😊", "😋",
    "😎", "😍", "😘", "🥰", "😗", "😙", "😚", "🙂", "🤗", "🤩",
    "🤔", "🤨", "😐", "😑", "😶", "🙄", "😏", "😣", "😥", "😮",
    "🤐", "😯", "😪", "😫", "🥱", "😴", "😌", "😛", "😜", "😝",
    "🤤", "😒", "😓", "😔", "😕", "🙃", "🤑", "😲", "🙁", "😖",
    "😞", "😟", "😤", "😢", "😭", "😦", "😧", "😨", "😩", "🤯",
    "😬", "😰", "😱", "🥵", "🥶", "😳", "🤪", "😵", "🥴", "😠",
    "😡", "🤬", "😷", "🤒", "🤕", "🤢", "🤮", "🤧", "😇", "🥳",
    "🥺", "🤠", "🤡", "🤥", "🤫", "🤭", "🧐", "🤓", "😈", "👿",
    "👋", "🤚", "🖐", "✋", "🖖", "👌", "🤌", "🤏", "🤞", "🤟",
    "🤘", "🤙", "👈", "👉", "👆", "👇", "👍", "👎", "✊", "👊",
    "❤", "🧡", "💛", "💚", "💙", "💜", "🖤", "🤍", "🤎", "💔",
    "🔥", "⭐", "✨", "⚡", "💯", "💢", "💥", "💫", "💦", "💨",
    "🕐", "🕑", "🕒", "🕓", "🕔", "🕕", "🕖", "🕗", "🕘", "🕙",
]

def get_style(style_name: str) -> str:
    """Get stylesheet by name."""
    styles = {
        "login": LOGIN_STYLE,
        "lobby": LOBBY_STYLE,
        "chat": CHAT_STYLE,
        "emoji": EMOJI_PICKER_STYLE,
    }
    return styles.get(style_name, "")
