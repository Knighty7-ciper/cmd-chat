fFked this from  @emilycodestar and i think its really something everybody needs, esp at school, no internet access needed you just need to be in the same network now, n yes its fully functional. This is the updated version i ran some advancements to suite my needs and im finding it really helpful.


# CMD Chat v2.0

**CMD Chat** is a modern, feature-rich console communication platform with multiple rooms, beautiful UI, and enterprise-grade security. Building on the original concept while adding significant improvements for usability and functionality.

**Privacy**: Fully anonymous chat with end-to-end encryption, impossible to intercept or hand over. All data exists only in RAM and is wiped after the session ends. Message persistence with optional encrypted history.

---

## ✨ New Features (v2.0)

### 🏠 **Multiple Rooms Support**
- Create and join different chat rooms (general, random, tech)
- Switch between rooms seamlessly with `/join <room>`
- Room-specific user lists and message history
- Public and private room support

### 🎨 **Beautiful Rich Interface**
- **4 Color Themes**: Dark, Light, Colorful, and Neon
- Rich terminal formatting with panels, tables, and markdown
- Real-time user indicators and connection status
- Emoji support with keyboard shortcuts (`:)` → `😊`)
- Timestamp display and user @mentions

### 🛡️ **Security & Performance**
- **Upgraded Cryptography**: RSA 2048-bit (upgraded from 512)
- **Modern Encryption**: AES-128 with PBKDF2 key derivation
- **Rate Limiting**: Anti-spam protection (10 messages/minute)
- **Better Error Handling**: Robust reconnection with exponential backoff
- **Performance Optimized**: Smooth 60fps rendering, efficient memory usage

### 🧰 **Rich Command System**
- `/help` - Interactive help with examples
- `/rooms` - List available rooms with user counts
- `/join <room>` - Switch to a different room
- `/users` - Show who's in the current room
- `/theme <name>` - Change color theme
- `/nick <name>` - Change your username
- `/status` - Connection and performance statistics
- `/clear` - Clear the screen
- `/history` - View message history

### 📱 **User Experience**
- **Real-time Updates**: Live user list and room status
- **Connection Management**: Automatic reconnection with smart backoff
- **Message History**: Optional persistent encrypted history
- **Keyboard Shortcuts**: Ctrl+C to quit, Tab for auto-completion
- **System Messages**: Join/leave notifications
- **Status Indicators**: Connection status, uptime, message counts

---

## 🔒 Security Features

- **End-to-End Encryption**: RSA 2048-bit + AES-128 symmetric encryption
- **Memory-Only Storage**: Data wiped on session end
- **No Logging**: Zero persistent logs or traces
- **Perfect Forward Secrecy**: Each session uses fresh keys
- **Rate Limiting**: Anti-spam and DoS protection
- **Input Sanitization**: XSS and injection protection

---

## 🚀 Installation & Quick Start

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Knighty7-ciper/cmd-chat
   cd cmd-chat-main
   ```

2. **Install dependencies:**
   ```bash
   # Linux/macOS
   python -m venv venv && source venv/bin/activate && pip install -r requirements.txt
   
   # Windows (PowerShell)
   python -m venv venv; .\venv\Scripts\activate; pip install -r requirements.txt
   ```

### Quick Start Examples

#### **Start Server**
```bash
# Basic server with password protection
python cmd_chat.py serve 0.0.0.0 8000 --password mysecret

# Server with custom rooms
python cmd_chat.py serve 0.0.0.0 8000 --password mysecret --rooms general random tech dev

# Development server (no password, debug logging)
python cmd_chat.py serve localhost 8000 --dev
```

#### **Connect Client**
```bash
# Basic connection
python cmd_chat.py connect localhost 8000 alice mysecret

# With custom theme and initial room
python cmd_chat.py connect localhost 8000 bob mysecret --theme colorful --room tech

# No colors (plain text mode)
python cmd_chat.py connect localhost 8000 charlie mysecret --no-colors
```

---

## 🎮 Usage Examples

### **Room Management**
```
/rooms                 # List all available rooms
/join random          # Switch to 'random' room
/users                # See who's in current room
/status               # View connection stats
```

### **Customization**
```
/theme dark           # Switch to dark theme
/theme colorful       # Switch to colorful theme
/nick newname         # Change username
/clear                # Clear screen
```

### **Message Features**
- **Emoji Shortcuts**: Type `:)`, `:D`, `<3` for instant emoji
- **Actions**: `/me waves` for action messages
- **History**: `/history` to see recent messages
- **System Commands**: Automatic join/leave notifications

---

## 📋 Command Reference

### **Server Commands**
| Command | Description |
|---------|-------------|
| `python cmd_chat.py serve <ip> <port>` | Start server |
| `--password <pass>` | Set admin password |
| `--rooms <list>` | Custom default rooms |
| `--no-history` | Disable message history |

### **Client Commands**
| Command | Description | Aliases |
|---------|-------------|---------|
| `/help` | Show help menu | `/h`, `/?` |
| `/rooms` | List available rooms | `/r`, `/room` |
| `/join <room>` | Switch to room | `/j`, `/go` |
| `/users` | Show room users | `/u`, `/who` |
| `/theme <name>` | Change theme | `/colors`, `/style` |
| `/nick <name>` | Change username | `/name`, `/username` |
| `/status` | Show connection status | `/s` |
| `/clear` | Clear screen | `/cls` |
| `/history` | View message history | `/hist`, `/log` |
| `/quit` | Leave chat | `/q`, `/exit`, `/leave` |

### **Available Themes**
- `dark` - Classic dark theme (default)
- `light` - Clean light theme
- `colorful` - Vibrant color scheme
- `neon` - Bright neon cyberpunk style

---

## ⚙️ Advanced Configuration

### **Performance Settings**
- **Message Rate Limit**: 10 messages per minute per user
- **Max Message Length**: 1000 characters
- **History Retention**: Configurable (default: 10,000 messages)
- **Connection Timeout**: 10 seconds
- **Reconnect Attempts**: 5 with exponential backoff

### **Security Configuration**
- **Encryption**: RSA 2048-bit + AES-128
- **Key Derivation**: PBKDF2 with 100,000 iterations
- **Memory Wipe**: Automatic on session end
- **Input Sanitization**: Enabled by default

---

## 🏗️ Architecture

### **Server Components**
- **Sanic Web Framework**: High-performance async web server
- **WebSocket Management**: Real-time bidirectional communication
- **Room Management**: Multiple room support with user tracking
- **Cryptography Service**: RSA key exchange + AES encryption
- **Message History**: Optional persistent encrypted storage

### **Client Components**
- **Rich Terminal UI**: Beautiful formatting with colors and panels
- **WebSocket Client**: Robust connection management
- **Command Parser**: Interactive command system
- **Theme Engine**: Multiple color schemes
- **Message Renderer**: Real-time message display

---

## 🛠️ Development

### **File Structure**
```
cmd_chat/
├── __init__.py           # Main entry point
├── server/
│   ├── server.py         # Server with room support
│   ├── models.py         # Data models
│   └── services.py       # Legacy services (deprecated)
└── client/
    ├── client.py         # Client application
    ├── config.py         # UI and feature configuration
    └── core/
        ├── crypto.py     # Cryptography service
        ├── rich_renderer.py    # Rich terminal renderer
        └── default_renderer.py # Basic renderer
```

### **Environment Variables**
```bash
export CHAT_HOST=0.0.0.0          # Server host
export CHAT_PORT=8000             # Server port
export JWT_SECRET=your-secret     # JWT secret (production)
```

---

## 🔍 Troubleshooting

### **Common Issues**

**Connection Refused**
- Ensure server is running: `python cmd_chat.py serve localhost 8000 --password pass`
- Check firewall settings
- Verify IP and port are correct

**Authentication Failed**
- Double-check password matches server configuration
- Ensure password parameter is provided

**Themes Not Working**
- Install rich library: `pip install rich`
- Try `--no-colors` for plain text mode

**Performance Issues**
- Reduce message history: Use `--no-history` on server
- Limit concurrent users per room
- Check network connectivity

### **Debug Mode**
Enable debug logging:
```bash
python cmd_chat.py serve localhost 8000 --password pass --dev
```
