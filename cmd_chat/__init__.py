import asyncio
import argparse
import sys
import os
from pathlib import Path
from cmd_chat.server.server import run_server
from cmd_chat.client.client import Client

def print_banner():
    """Print startup banner"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                    CMD Chat                         ║
║                    Version 2.0.0                            ║
║                                                              ║
║  🔒 End-to-end encrypted messaging                          ║
║  🏠 Multiple rooms support                                  ║
║  🎨 Rich terminal interface                                 ║
║  ⚡ Real-time communication                                 ║
║  🛡️  Memory-only data storage                               ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def print_welcome_message():
    """Print welcome message"""
    welcome = """
🚀 Welcome to CMD Chat!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✨ Features:
• Multiple chat rooms (general, random, tech)
• Beautiful color themes (dark, light, colorful, neon)
• Real-time user list and room status
• Encrypted messaging with modern cryptography
• Rich command system (/help for commands)
• Message history and user management

💡 Quick Start:
1. Start server: python cmd_chat.py serve 0.0.0.0 8000 --password yourpass
2. Connect client: python cmd_chat.py connect localhost 8000 alice yourpass
3. Type /help for available commands

🔐 Security: All messages are encrypted end-to-end
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    """
    print(welcome)

def run_http_server(ip: str, port: int, password: str | None, 
                   rooms: list[str] | None = None, 
                   enable_history: bool = True) -> None:
    """Server startup with room configuration"""
    print(f"\n🖥️  Starting CMD Chat Server...")
    print(f"📍 Address: {ip}:{port}")
    print(f"🔑 Password protection: {'✅ Enabled' if password else '❌ Disabled'}")
    print(f"📚 History retention: {'✅ Enabled' if enable_history else '❌ Disabled'}")
    if rooms:
        print(f"🏠 Default rooms: {', '.join(rooms)}")
    print(f"\n⚡ Server is starting up...")
    
    try:
        run_server(ip, int(port), False, password)
    except KeyboardInterrupt:
        print("\n\n👋 Server shutdown requested. Goodbye!")
    except Exception as e:
        print(f"\n❌ Server failed to start: {e}")
        sys.exit(1)

async def run_client(username: str, server: str, port: int, password: str | None, 
                    theme: str = "dark", room: str = "general") -> None:
    """Client startup with theme and room options"""
    print_welcome_message()
    
    try:
        client = Client(
            server=server, 
            port=port, 
            username=username, 
            password=password,
            theme=theme
        )
        
        # Set initial room
        client.current_room = room
        
        print(f"\n🔗 Connecting to {server}:{port} as '{username}'...")
        print(f"🎨 Theme: {theme}")
        print(f"🏠 Room: {room}")
        print(f"\n{'='*50}")
        
        client.run()
        
    except KeyboardInterrupt:
        print("\n\n👋 Connection interrupted. Goodbye!")
    except ConnectionError as e:
        print(f"\n❌ Connection failed: {e}")
        print("💡 Make sure the server is running and password is correct")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Client error: {e}")
        sys.exit(1)

async def run() -> None:
    """Main function with new options"""
    parser = argparse.ArgumentParser(
        description='Command-line Chat Application',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start server
  python cmd_chat.py serve 0.0.0.0 8000 --password mypass
  
  # Connect with default settings
  python cmd_chat.py connect localhost 8000 alice mypass
  
  # Connect with custom theme and room
  python cmd_chat.py connect localhost 8000 bob mypass --theme colorful --room tech
  
  # List available options
  python cmd_chat.py --help
        """
    )
    
    # Global options
    parser.add_argument('--version', action='version', version='CMD Chat v2.0.0')
    
    subparsers = parser.add_subparsers(dest='command', required=True)

    # Server command
    serve_p = subparsers.add_parser('serve', help='Run chat server')
    serve_p.add_argument('ip_address', help='IP address to bind to (e.g., 0.0.0.0, localhost)')
    serve_p.add_argument('port', type=int, help='Port number to listen on')
    serve_p.add_argument('--password', '-p', required=False, 
                        help='Admin password required for clients (recommended)')
    serve_p.add_argument('--rooms', nargs='+', default=['general', 'random', 'tech'],
                        help='Default rooms to create (default: general random tech)')
    serve_p.add_argument('--no-history', action='store_true',
                        help='Disable message history retention')
    serve_p.add_argument('--dev', action='store_true',
                        help='Enable development mode (debug logging)')

    # Client command
    connect_p = subparsers.add_parser('connect', help='Connect to chat server')
    connect_p.add_argument('ip_address', help='Server IP address or hostname')
    connect_p.add_argument('port', type=int, help='Server port')
    connect_p.add_argument('username', help='Your username')
    connect_p.add_argument('password', nargs='?', default=None,
                          help='Password to authenticate with server')
    
    # Client options
    connect_p.add_argument('--theme', choices=['dark', 'light', 'colorful', 'neon'], 
                          default='dark', help='Color theme for the interface')
    connect_p.add_argument('--room', default='general',
                          help='Initial room to join (default: general)')
    connect_p.add_argument('--no-colors', action='store_true',
                          help='Disable colored output')
    connect_p.add_argument('--show-timestamps', action='store_true', default=True,
                          help='Show message timestamps')
    connect_p.add_argument('--compact', action='store_true',
                          help='Use compact message layout')

    # Info command
    info_p = subparsers.add_parser('info', help='Show application information')
    info_p.add_argument('--config', action='store_true',
                       help='Show current configuration')

    args = parser.parse_args()

    # Handle info command
    if args.command == 'info':
        print_banner()
        print("📖 CMD Chat Information:")
        print(f"• Version: 2.0.0")
        print(f"• Cryptography: RSA 2048-bit + AES-128")
        print(f"• WebSocket Protocol: With rooms")
        print(f"• UI Framework: Rich + Colorama")
        print(f"• Features: Multi-room, themes, commands, history")
        print(f"• Security: Memory-only storage, E2E encryption")
        
        if args.config:
            print("\n⚙️  Current Configuration:")
            print("• Default theme: dark")
            print("• Default room: general")
            print("• Max message length: 1000 chars")
            print("• Rate limit: 10 messages/minute")
            print("• History retention: Configurable")
        return

    # Handle serve command
    if args.command == 'serve':
        run_http_server(
            args.ip_address, 
            args.port, 
            args.password,
            args.rooms,
            not args.no_history
        )
        return

    # Handle connect command
    if args.command == 'connect':
        # Validate arguments
        if not args.username.strip():
            print("❌ Username cannot be empty")
            sys.exit(1)
        
        if len(args.username) > 20:
            print("❌ Username too long (max 20 characters)")
            sys.exit(1)
        
        # Check username format
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', args.username):
            print("❌ Username can only contain letters, numbers, underscores, and hyphens")
            sys.exit(1)
        
        await run_client(
            args.username.strip(),
            args.ip_address, 
            int(args.port), 
            args.password,
            args.theme,
            args.room
        )
        return

def main():
    """Main entry point"""
    try:
        print_banner()
        asyncio.run(run())
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
