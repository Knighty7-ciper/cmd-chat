import ast
import time
import threading
import json
import sys
import signal
import socket
from typing import Optional, Dict, List, Any
from datetime import datetime

from websocket import create_connection, WebSocketConnectionClosedException, WebSocketTimeoutException
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.markdown import Markdown

from cmd_chat.client.core.crypto import CryptoServiceExtended
from cmd_chat.client.core.default_renderer import DefaultClientRenderer
from cmd_chat.client.core.rich_renderer import RichClientRenderer
from cmd_chat.client.config import UI_CONFIG, COMMANDS, Theme, EMOJI_CONFIG, NETWORK_CONFIG, RENDER_TIME

from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)


class Client(CryptoServiceExtended, RichClientRenderer):
    """Client with multiple rooms and better UX"""
    
    def __init__(
        self,
        server: str,
        port: int,
        username: str,
        password: Optional[str] = None,
        theme: str = "dark"
    ):
        super().__init__()
        self.server = server
        self.port = port
        self.username = username
        self.password = password or ""
        self.theme = theme
        self.current_room = "general"
        self.base_url = f"http://{self.server}:{self.port}"
        self.ws_url = f"ws://{self.server}:{self.port}"
        
        # State management
        self.rooms: Dict[str, Dict[str, Any]] = {}
        self.message_history: List[Dict[str, Any]] = []
        self.user_list: List[str] = []
        self.connection_status = "disconnected"
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = NETWORK_CONFIG["max_retries"]
        
        # UI state
        self.console = Console(width=80, theme="monokai" if theme == "neon" else None)
        self.is_running = True
        self.message_buffer = []
        
        # Performance tracking
        self.last_ping_time = time.time()
        self.message_count = 0
        self.start_time = time.time()
        
        # Initialize rooms
        self._initialize_default_rooms()

    def _initialize_default_rooms(self):
        """Initialize default room configuration"""
        self.rooms = {
            "general": {"name": "General Chat", "active": True, "user_count": 0},
            "random": {"name": "Random Discussions", "active": True, "user_count": 0},
            "tech": {"name": "Tech Talk", "active": True, "user_count": 0}
        }

    def _ws_full(self, path: str) -> str:
        """Generate full WebSocket URL with parameters"""
        params = f"?password={self.password}&username={self.username}&room_id={self.current_room}"
        return f"{self.ws_url}{path}{params}"

    def _connect_ws(self, path: str, retries: int = 5, backoff: float = 1.0):
        """WebSocket connection with better error handling"""
        last_exc = None
        
        for attempt in range(retries):
            try:
                self._update_connection_status("connecting")
                
                # Add connection timeout
                ws = create_connection(
                    self._ws_full(path),
                    timeout=NETWORK_CONFIG["connection_timeout"],
                    sock_options=((socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1),)
                )
                
                self._update_connection_status("connected")
                self.reconnect_attempts = 0
                return ws
                
            except WebSocketTimeoutException as exc:
                last_exc = exc
                self._display_error(f"Connection timeout (attempt {attempt + 1}/{retries})")
                
            except ConnectionRefusedError as exc:
                last_exc = exc
                self._display_error(f"Connection refused - is server running? (attempt {attempt + 1}/{retries})")
                
            except Exception as exc:
                last_exc = exc
                self._display_error(f"Connection error: {exc} (attempt {attempt + 1}/{retries})")
            
            if attempt < retries - 1:
                wait_time = backoff * (2 ** attempt)  # Exponential backoff
                self._display_info(f"Retrying in {wait_time:.1f} seconds...")
                time.sleep(wait_time)
        
        # Max retries reached
        self._update_connection_status("failed")
        raise ConnectionError(f"Failed to connect after {retries} attempts: {last_exc}")

    def _update_connection_status(self, status: str):
        """Update and display connection status"""
        self.connection_status = status
        status_colors = {
            "connected": "✅",
            "connecting": "🔄",
            "disconnected": "❌",
            "failed": "💥",
            "reconnecting": "🔁"
        }
        
        if status in status_colors:
            self._display_status(f"{status_colors[status]} {status.capitalize()}")

    def _display_status(self, message: str):
        """Display status message in terminal"""
        if UI_CONFIG["enable_colors"]:
            print(f"\r{Style.DIM}{datetime.now().strftime('%H:%M:%S')} {message}{Style.RESET_ALL}", end="", flush=True)
        else:
            print(f"\r{datetime.now().strftime('%H:%M:%S')} {message}", end="", flush=True)

    def _display_info(self, message: str):
        """Display informational message"""
        if UI_CONFIG["enable_colors"]:
            print(f"\n{Fore.BLUE}ℹ️  {message}{Style.RESET_ALL}")
        else:
            print(f"\n[INFO] {message}")

    def _display_error(self, message: str):
        """Display error message"""
        if UI_CONFIG["enable_colors"]:
            print(f"\n{Fore.RED}❌ {message}{Style.RESET_ALL}")
        else:
            print(f"\n[ERROR] {message}")

    def _display_success(self, message: str):
        """Display success message"""
        if UI_CONFIG["enable_colors"]:
            print(f"\n{Fore.GREEN}✅ {message}{Style.RESET_ALL}")
        else:
            print(f"\n[SUCCESS] {message}")

    def _display_warning(self, message: str):
        """Display warning message"""
        if UI_CONFIG["enable_colors"]:
            print(f"\n{Fore.YELLOW}⚠️  {message}{Style.RESET_ALL}")
        else:
            print(f"\n[WARNING] {message}")

    def _handle_command(self, command: str) -> bool:
        """Handle user commands"""
        command = command.lower().strip()
        
        # Check if it's a command
        if not command.startswith('/'):
            return False
        
        # Remove leading slash
        cmd = command[1:].split()[0] if command[1:] else ""
        
        # Find matching command
        for cmd_name, aliases in COMMANDS.items():
            if cmd in aliases:
                return self._execute_command(cmd_name, command)
        
        # Unknown command
        self._display_warning(f"Unknown command: /{cmd}")
        self._display_info("Type /help for available commands")
        return True

    def _execute_command(self, cmd_name: str, full_command: str) -> bool:
        """Execute a specific command"""
        try:
            if cmd_name == "quit":
                return self._cmd_quit()
            elif cmd_name == "help":
                return self._cmd_help()
            elif cmd_name == "clear":
                return self._cmd_clear()
            elif cmd_name == "rooms":
                return self._cmd_rooms()
            elif cmd_name == "join":
                return self._cmd_join(full_command)
            elif cmd_name == "users":
                return self._cmd_users()
            elif cmd_name == "me":
                return self._cmd_me(full_command)
            elif cmd_name == "nick":
                return self._cmd_nick(full_command)
            elif cmd_name == "theme":
                return self._cmd_theme(full_command)
            elif cmd_name == "status":
                return self._cmd_status()
            elif cmd_name == "history":
                return self._cmd_history()
        except Exception as e:
            self._display_error(f"Command execution failed: {e}")
        
        return True

    def _cmd_quit(self) -> bool:
        """Quit command"""
        self._display_info("Goodbye! 👋")
        self.is_running = False
        return False

    def _cmd_help(self) -> bool:
        """Help command"""
        help_text = """
# CMD Chat - Available Commands

## Basic Commands
- `/quit` or `/q` - Leave the chat
- `/help` or `/h` - Show this help
- `/clear` or `/cls` - Clear the screen
- `/status` - Show connection status

## Room Management  
- `/rooms` or `/r` - List available rooms
- `/join <room>` or `/j <room>` - Join a room
- `/users` or `/u` - Show users in current room

## Message Commands
- `/me <action>` - Send an action message
- `/nick <name>` - Change your nickname
- `/history` - Show message history

## UI Commands
- `/theme <name>` - Change color theme (dark, light, colorful, neon)

## Tips
- Use Tab for auto-completion
- Press Ctrl+C to quit
- Messages are automatically encrypted
- Multiple rooms supported!

Type any command to get started!
        """
        
        self.console.print(Panel(Markdown(help_text), title="📚 Help", border_style="cyan"))
        return True

    def _cmd_clear(self) -> bool:
        """Clear command"""
        if hasattr(self, 'clear_console'):
            self.clear_console()
        else:
            import os
            os.system('cls' if os.name == 'nt' else 'clear')
        return True

    def _cmd_rooms(self) -> bool:
        """List rooms command"""
        table = Table(title="🏠 Available Rooms", show_header=True)
        table.add_column("Room", style="cyan", no_wrap=True)
        table.add_column("Users", style="green")
        table.add_column("Status", style="yellow")
        
        for room_id, room_info in self.rooms.items():
            status = "🟢 Active" if room_info.get("active", False) else "🔴 Inactive"
            user_count = room_info.get("user_count", 0)
            table.add_row(room_info["name"], str(user_count), status)
        
        self.console.print(table)
        self._display_info(f"Current room: {self.current_room}")
        return True

    def _cmd_join(self, full_command: str) -> bool:
        """Join room command"""
        parts = full_command.split()
        if len(parts) < 2:
            self._display_warning("Usage: /join <room_name>")
            return True
        
        room_name = " ".join(parts[1:])  # Support room names with spaces
        if room_name in self.rooms:
            old_room = self.current_room
            self.current_room = room_name
            self._display_success(f"Switched from {old_room} to {room_name}")
            return True
        else:
            self._display_warning(f"Room '{room_name}' not found")
            self._display_info("Use /rooms to see available rooms")
            return True

    def _cmd_users(self) -> bool:
        """Users command"""
        if self.user_list:
            table = Table(title="👥 Users in Room", show_header=True)
            table.add_column("Username", style="green")
            
            for username in self.user_list:
                is_self = username == self.username
                display_name = f"{username} (you)" if is_self else username
                table.add_row(display_name)
            
            self.console.print(table)
        else:
            self._display_info("No users in this room yet")
        return True

    def _cmd_me(self, full_command: str) -> bool:
        """Action command"""
        action = full_command[4:].strip()  # Remove "/me "
        if not action:
            self._display_warning("Usage: /me <action>")
            return True
        
        # This would need to be sent as a special message type
        self._display_info(f"* {self.username} {action}")
        return True

    def _cmd_nick(self, full_command: str) -> bool:
        """Change nickname command"""
        parts = full_command.split(maxsplit=1)
        if len(parts) < 2:
            self._display_warning("Usage: /nick <new_username>")
            return True
        
        new_name = parts[1].strip()
        if len(new_name) < 2:
            self._display_warning("Username must be at least 2 characters")
            return True
        
        old_name = self.username
        self.username = new_name
        self._display_success(f"Changed username from {old_name} to {new_name}")
        return True

    def _cmd_theme(self, full_command: str) -> bool:
        """Change theme command"""
        parts = full_command.split(maxsplit=1)
        if len(parts) < 2:
            available = ", ".join([t.value for t in Theme])
            self._display_info(f"Available themes: {available}")
            return True
        
        theme_name = parts[1].lower().strip()
        try:
            self.theme = Theme(theme_name)
            self._display_success(f"Changed theme to {theme_name}")
            return True
        except ValueError:
            self._display_warning(f"Unknown theme: {theme_name}")
            return True

    def _cmd_status(self) -> bool:
        """Status command"""
        uptime = time.time() - self.start_time
        minutes = int(uptime // 60)
        seconds = int(uptime % 60)
        
        status_info = f"""
📊 Connection Status
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🌐 Server: {self.server}:{self.port}
🏠 Current Room: {self.current_room}
👤 Username: {self.username}
🔌 Connection: {self.connection_status}
📨 Messages: {self.message_count}
⏰ Uptime: {minutes}m {seconds}s
🔄 Reconnects: {self.reconnect_attempts}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        """
        
        self.console.print(Panel(status_info.strip(), title="📊 Status", border_style="cyan"))
        return True

    def _cmd_history(self) -> bool:
        """Message history command"""
        if not self.message_history:
            self._display_info("No messages in history")
            return True
        
        # Show last 10 messages
        recent = self.message_history[-10:]
        for msg in recent:
            timestamp = datetime.fromisoformat(msg["timestamp"]).strftime("%H:%M:%S")
            self.console.print(f"[dim]{timestamp}[/] [cyan]{msg['username']}[/]: {msg['content']}")
        
        return True

    def send_info(self):
        """Message sending with better error handling"""
        ws = None
        try:
            # Connect to talk WebSocket
            self._update_connection_status("connecting")
            ws = self._connect_ws("/talk")
            
            self._display_success("Connected to chat server!")
            self._display_info("Type /help for commands. Press Ctrl+C to quit.")
            
            # Handle keyboard interrupt gracefully
            def signal_handler(sig, frame):
                self._display_info("\nReceived interrupt signal...")
                self.is_running = False
                if ws:
                    try:
                        ws.send(json.dumps({"action": "close"}))
                        ws.close()
                    except:
                        pass
                sys.exit(0)
            
            signal.signal(signal.SIGINT, signal_handler)
            
            # Message input loop
            while self.is_running:
                try:
                    # Get user input
                    user_input = Prompt.ask(
                        f"[bold cyan]{self.username}[/]@[bold yellow]{self.current_room}[/]",
                        default=""
                    )
                    
                    if user_input.lower() in ['q', 'quit', 'exit']:
                        break
                    
                    if not user_input.strip():
                        continue
                    
                    # Handle commands
                    if self._handle_command(user_input):
                        continue
                    
                    # Process emoji shortcuts
                    processed_input = user_input
                    for shortcut, emoji in EMOJI_CONFIG["emoji_shortcuts"].items():
                        processed_input = processed_input.replace(shortcut, emoji)
                    
                    # Send message
                    if len(processed_input) > 1000:
                        self._display_warning("Message too long (max 1000 characters)")
                        continue
                    
                    # Encrypt and send
                    encrypted_message = self._encrypt(processed_input)
                    socket_message = json.dumps({
                        "text": encrypted_message,
                        "username": self.username,
                        "room_id": self.current_room,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    
                    ws.send(socket_message)
                    self.message_count += 1
                    
                except KeyboardInterrupt:
                    break
                except WebSocketConnectionClosedException:
                    self._display_warning("Connection lost. Attempting to reconnect...")
                    if ws:
                        try:
                            ws.close()
                        except:
                            pass
                    ws = None
                    time.sleep(2)
                    continue
                except Exception as e:
                    self._display_error(f"Send error: {e}")
                    time.sleep(1)
                    continue
                    
        except Exception as e:
            self._display_error(f"Critical error: {e}")
        finally:
            # Cleanup
            self._update_connection_status("disconnecting")
            if ws:
                try:
                    ws.send(json.dumps({"action": "close"}))
                    ws.close()
                except:
                    pass
            self._update_connection_status("disconnected")

    def run(self):
        """Main client execution"""
        try:
            self._display_info("Starting CMD Chat...")
            self._display_info(f"Connecting to {self.server}:{self.port}")
            
            # Start message receiving thread
            receive_thread = threading.Thread(target=self.receive_messages, daemon=True)
            receive_thread.start()
            
            # Start sending messages
            self.send_info()
            
        except Exception as e:
            self._display_error(f"Client startup failed: {e}")
            raise

    def receive_messages(self):
        """Receive messages in separate thread"""
        ws = None
        while self.is_running:
            try:
                if ws is None:
                    ws = self._connect_ws("/update")
                
                while self.is_running:
                    try:
                        data = ws.recv()
                        message_data = json.loads(data)
                        
                        if message_data.get("type") == "message":
                            self._process_received_message(message_data)
                        elif message_data.get("type") == "heartbeat":
                            self.last_ping_time = time.time()
                        elif message_data.get("type") == "room_update":
                            self._process_room_update(message_data)
                            
                    except WebSocketConnectionClosedException:
                        self._display_warning("Message connection lost")
                        ws = None
                        break
                    except json.JSONDecodeError:
                        self._display_warning("Invalid message received")
                    except Exception as e:
                        self._display_error(f"Receive error: {e}")
                        time.sleep(1)
                        
            except Exception as e:
                self._display_error(f"Receive connection error: {e}")
                time.sleep(2)
        
        if ws:
            try:
                ws.close()
            except:
                pass

    def _process_received_message(self, message_data: dict):
        """Process a received message"""
        try:
            message_info = message_data.get("message", {})
            content = self._decrypt(message_info.get("content", ""))
            username = message_info.get("username", "Unknown")
            timestamp = message_info.get("timestamp", "")
            message_id = message_info.get("id", "")
            
            # Add to history
            self.message_history.append({
                "id": message_id,
                "username": username,
                "content": content,
                "timestamp": timestamp
            })
            
            # Display message
            self._display_message(username, content, timestamp)
            
        except Exception as e:
            self._display_error(f"Message processing error: {e}")

    def _process_room_update(self, update_data: dict):
        """Process room update information"""
        try:
            room_info = update_data.get("room", {})
            recent_messages = update_data.get("recent_messages", [])
            user_count = update_data.get("user_count", 0)
            
            # Update room info
            if room_info:
                room_id = room_info.get("id", self.current_room)
                if room_id in self.rooms:
                    self.rooms[room_id]["user_count"] = user_count
            
            # Process recent messages
            for msg_data in recent_messages:
                if msg_data.get("id") not in [m.get("id") for m in self.message_history]:
                    self._process_received_message({"message": msg_data})
                    
        except Exception as e:
            self._display_error(f"Room update error: {e}")

    def _display_message(self, username: str, content: str, timestamp: str = ""):
        """Display a message with formatting"""
        try:
            # Parse timestamp
            if timestamp and UI_CONFIG["show_timestamps"]:
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    time_str = dt.strftime("%H:%M:%S")
                except:
                    time_str = datetime.now().strftime("%H:%M:%S")
            else:
                time_str = datetime.now().strftime("%H:%M:%S")
            
            # Format message
            if username == "System":
                # System message
                if UI_CONFIG["enable_colors"]:
                    print(f"\n{Fore.YELLOW}[{time_str}] 🔧 {content}{Style.RESET_ALL}")
                else:
                    print(f"\n[{time_str}] SYSTEM: {content}")
            elif username == self.username:
                # Own message
                if UI_CONFIG["enable_colors"]:
                    print(f"\n{Fore.CYAN}[{time_str}] 💬 {username}: {content}{Style.RESET_ALL}")
                else:
                    print(f"\n[{time_str}] {username}: {content}")
            else:
                # Other user message
                if UI_CONFIG["enable_colors"]:
                    print(f"\n{Fore.GREEN}[{time_str}] {username}: {content}{Style.RESET_ALL}")
                else:
                    print(f"\n[{time_str}] {username}: {content}")
            
        except Exception as e:
            print(f"\n[ERROR] Failed to display message: {e}")


# Backward compatibility alias

    """Backward compatible client class"""
    pass

    def update_info(self):
        ws = self._connect_ws("/update")
        last_try = None
        try:
            while not self.__stop_threads:
                try:
                    time.sleep(RENDER_TIME)
                    raw = ws.recv()
                    if isinstance(raw, bytes):
                        raw = raw.decode("utf-8")
                    response = ast.literal_eval(raw)
                    if last_try == response:
                        continue
                    last_try = response
                    self.clear_console()
                    if len(last_try["messages"]) > 0:
                        self.print_chat(response=last_try)
                except (WebSocketConnectionClosedException, ConnectionResetError, ConnectionAbortedError, OSError):
                    try:
                        if ws:
                            try:
                                ws.close()
                            except Exception:
                                pass
                        ws = self._connect_ws("/update")
                        continue
                    except Exception:
                        print("Connection lost: can't establish update channel")
                        self.__stop_threads = True
                        break
                except KeyboardInterrupt:
                    self.__stop_threads = True
                    try:
                        ws.send(self.close_response)
                        ws.close()
                    except Exception:
                        pass
                    break
        finally:
            try:
                ws.close()
            except Exception:
                pass

    def _validate_keys(self) -> None:
        self._request_key(
            url=f"{self.base_url}/get_key",
            username=self.username,
            password=self.password
        )
        self._remove_keys()

    def run(self):
        self._validate_keys()
        threads = [
            threading.Thread(target=self.send_info, daemon=True),
            threading.Thread(target=self.update_info, daemon=True)
        ]
        for th in threads:
            th.start()
        for th in threads:
            th.join()
