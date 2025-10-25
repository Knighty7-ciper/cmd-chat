from colorama import Fore, Back, Style
from enum import Enum
from typing import Dict, Any


class Theme(str, Enum):
    """Available color themes"""
    DARK = "dark"
    LIGHT = "light" 
    COLORFUL = "colorful"
    NEON = "neon"


# Color schemes
COLORS = {
    # Default dark theme
    "dark": {
        "text_color": Fore.WHITE,
        "text_background": Back.BLACK,
        "my_username_color": Fore.CYAN,
        "other_username_color": Fore.GREEN,
        "system_color": Fore.YELLOW,
        "error_color": Fore.RED,
        "success_color": Fore.GREEN,
        "warning_color": Fore.YELLOW,
        "info_color": Fore.BLUE,
        "room_color": Fore.MAGENTA,
        "time_color": Style.DIM,
        "border_color": Style.DIM,
        "header_color": Fore.CYAN + Style.BRIGHT,
        "highlight_color": Fore.YELLOW + Style.BRIGHT,
        "command_color": Fore.CYAN,
        "mention_color": Fore.YELLOW + Style.BRIGHT
    },
    
    # Light theme
    "light": {
        "text_color": Fore.BLACK,
        "text_background": Back.WHITE,
        "my_username_color": Fore.BLUE,
        "other_username_color": Fore.BLACK,
        "system_color": Fore.BLUE,
        "error_color": Fore.RED,
        "success_color": Fore.GREEN,
        "warning_color": Fore.YELLOW,
        "info_color": Fore.BLUE,
        "room_color": Fore.MAGENTA,
        "time_color": Style.DIM,
        "border_color": Style.DIM,
        "header_color": Fore.BLUE + Style.BRIGHT,
        "highlight_color": Fore.BLUE,
        "command_color": Fore.BLUE,
        "mention_color": Fore.RED
    },
    
    # Colorful theme
    "colorful": {
        "text_color": Fore.WHITE,
        "text_background": Back.BLACK,
        "my_username_color": Fore.CYAN + Style.BRIGHT,
        "other_username_color": Fore.GREEN + Style.BRIGHT,
        "system_color": Fore.YELLOW + Style.BRIGHT,
        "error_color": Fore.RED + Style.BRIGHT,
        "success_color": Fore.GREEN + Style.BRIGHT,
        "warning_color": Fore.YELLOW + Style.BRIGHT,
        "info_color": Fore.BLUE + Style.BRIGHT,
        "room_color": Fore.MAGENTA + Style.BRIGHT,
        "time_color": Style.DIM + Fore.WHITE,
        "border_color": Fore.CYAN,
        "header_color": Fore.YELLOW + Style.BRIGHT,
        "highlight_color": Fore.CYAN + Style.BRIGHT,
        "command_color": Fore.CYAN + Style.BRIGHT,
        "mention_color": Fore.YELLOW + Style.BRIGHT
    },
    
    # Neon theme
    "neon": {
        "text_color": Fore.BLACK,
        "text_background": Back.BLACK,
        "my_username_color": Fore.CYAN + Style.BRIGHT,
        "other_username_color": Fore.GREEN + Style.BRIGHT,
        "system_color": Fore.YELLOW + Style.BRIGHT,
        "error_color": Fore.RED + Style.BRIGHT,
        "success_color": Fore.GREEN + Style.BRIGHT,
        "warning_color": Fore.YELLOW + Style.BRIGHT,
        "info_color": Fore.BLUE + Style.BRIGHT,
        "room_color": Fore.MAGENTA + Style.BRIGHT,
        "time_color": Style.DIM + Fore.CYAN,
        "border_color": Fore.CYAN + Style.BRIGHT,
        "header_color": Fore.CYAN + Style.BRIGHT,
        "highlight_color": Fore.YELLOW + Style.BRIGHT,
        "command_color": Fore.CYAN + Style.BRIGHT,
        "mention_color": Fore.YELLOW + Style.BRIGHT
    }
}

# UI Configuration
UI_CONFIG = {
    # Display settings
    "theme": Theme.DARK,
    "enable_colors": True,
    "show_timestamps": True,
    "show_usernames": True,
    "show_room_indicators": True,
    "max_message_length": 80,
    "max_display_messages": 20,
    
    # Animation settings
    "typing_animation": True,
    "message_popup": True,
    "smooth_scroll": True,
    
    # Buffer settings
    "message_buffer": 100,
    "chat_buffer": 50,
    
    # Performance
    "render_time": 0.02,  # Reduced for smoother experience
    "ping_interval": 30,
    
    # Layout
    "show_user_count": True,
    "show_room_list": True,
    "split_screen": False,
    "fullscreen_messages": False
}

# Command aliases for user convenience
COMMANDS = {
    "quit": ["quit", "q", "exit", "leave"],
    "help": ["help", "h", "?"],
    "clear": ["clear", "cls"],
    "rooms": ["rooms", "r", "room"],
    "join": ["join", "j", "go"],
    "users": ["users", "u", "who"],
    "me": ["me", "action"],
    "nick": ["nick", "name", "username"],
    "theme": ["theme", "colors", "style"],
    "status": ["status", "s"],
    "history": ["history", "hist", "log"]
}

# Room management
ROOM_CONFIG = {
    "default_room": "general",
    "show_room_on_join": True,
    "auto_join_default": True,
    "room_list_limit": 10
}

# Emoji and reactions
EMOJI_CONFIG = {
    "enable_emojis": True,
    "emoji_shortcuts": {
        ":)": "😊",
        ":(": "😢",
        ":D": "😃",
        ":P": "😛",
        ":o": "😮",
        ":O": "😮",
        "<3": "❤️",
        ":)": "🙂",
        ":|": "😐",
        ";)": "😉",
        ":D": "😄",
        ":S": "😕",
        ":'\")": "😢"
    }
}

# Keyboard shortcuts
KEYBOARD_SHORTCUTS = {
    "Ctrl+C": "quit",
    "Ctrl+L": "clear",
    "Ctrl+R": "rooms",
    "Ctrl+H": "help",
    "Tab": "auto_complete",
    "Up": "history_up",
    "Down": "history_down"
}

# Network settings
NETWORK_CONFIG = {
    "connection_timeout": 10,
    "reconnect_attempts": 5,
    "reconnect_delay": 2,
    "heartbeat_interval": 30,
    "max_retries": 3,
    "buffer_size": 4096
}

# Security settings
SECURITY_CONFIG = {
    "enable_encryption": True,
    "verify_certificates": True,
    "sanitize_input": True,
    "max_message_rate": 10,  # per minute
    "block_malicious": True
}

# Legacy compatibility constants
RENDER_TIME = 0.03
MESSAGES_TO_SHOW = 20
THEME = Theme  # Alias for backward compatibility

# Legacy color mappings for backward compatibility
LEGACY_COLORS = {
    "ip_color": "green",
    "username_color": "cyan"
}