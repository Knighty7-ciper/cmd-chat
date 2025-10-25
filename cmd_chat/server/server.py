import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Set
from functools import partial
from datetime import datetime, timedelta

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from sanic.worker.loader import AppLoader
from sanic.response import HTTPResponse
from sanic import Sanic, Request, response, Websocket

from cmd_chat.server.models import (
    Message, User, Room, RoomHistory, ConnectionInfo,
    JoinRoomResponse, MessageResponse, ErrorResponse,
    SystemMessage, RoomListResponse, LegacyMessage, MessageType
)


# Global state management
class ServerState:
    """Centralized server state management"""
    def __init__(self):
        # Core data stores
        self.messages: Dict[str, List[Message]] = {}  # room_id -> messages
        self.users: Dict[str, User] = {}  # user_id -> user
        self.rooms: Dict[str, Room] = {}  # room_id -> room
        self.connections: Dict[str, ConnectionInfo] = {}  # user_id -> connection info
        self.room_histories: Dict[str, RoomHistory] = {}  # room_id -> history
        
        # WebSocket connections
        self.active_connections: Dict[str, Set[Websocket]] = {}  # room_id -> websockets
        self.user_websockets: Dict[str, Websocket] = {}  # user_id -> websocket
        
        # Security
        self.symmetric_key = Fernet.generate_key()
        self.fernet = Fernet(self.symmetric_key)
        
        # Performance tracking
        self.message_rate_limits: Dict[str, List[float]] = {}  # user_id -> timestamps
        
        # Default room
        self._create_default_rooms()
    
    def _create_default_rooms(self):
        """Create default rooms on startup"""
        default_rooms = [
            {"name": "general", "type": "public", "description": "General chat room"},
            {"name": "random", "type": "public", "description": "Random discussions"},
            {"name": "tech", "type": "public", "description": "Technology discussions"}
        ]
        
        for room_data in default_rooms:
            room = Room(
                name=room_data["name"],
                type=room_data["type"],
                created_by="system",
                description=room_data["description"]
            )
            self.rooms[room.id] = room
            self.messages[room.id] = []
            self.room_histories[room.id] = RoomHistory(room_id=room.id)
            self.active_connections[room.id] = set()


# Initialize global state
SERVER_STATE = ServerState()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _check_password(request: Request, expected: str | None) -> bool:
    """Password checking with better security"""
    if not expected:
        return True
    
    # Check various parameter locations
    password = (
        request.args.get("password") or
        (request.form.get("password") if hasattr(request, "form") else None) or
        request.json.get("password") if request.json and "password" in request.json else None
    )
    
    return password == expected


def _get_str_arg(request: Request, name: str) -> str | None:
    """Get string argument from request with fallback chain"""
    return (
        request.form.get(name) or 
        request.args.get(name) or 
        (request.json.get(name) if request.json and name in request.json else None)
    )


def _serialize_message(message: Message) -> dict:
    """Serialize message for JSON transmission"""
    return {
        "id": message.id,
        "room_id": message.room_id,
        "user_id": message.user_id,
        "username": message.username,
        "content": message.content,
        "message_type": message.message_type,
        "timestamp": message.timestamp.isoformat(),
        "is_encrypted": message.is_encrypted
    }


def _check_rate_limit(user_id: str, limit: int = 10, window: int = 60) -> bool:
    """Check if user is within rate limits"""
    now = time.time()
    user_timestamps = SERVER_STATE.message_rate_limits.get(user_id, [])
    
    # Remove old timestamps
    user_timestamps = [ts for ts in user_timestamps if now - ts < window]
    SERVER_STATE.message_rate_limits[user_id] = user_timestamps
    
    # Check if over limit
    if len(user_timestamps) >= limit:
        return False
    
    # Add current timestamp
    user_timestamps.append(now)
    SERVER_STATE.message_rate_limits[user_id] = user_timestamps
    return True


def _create_system_message(msg_type: str, username: str, room_id: str, content: str) -> Message:
    """Create a system message"""
    return Message(
        room_id=room_id,
        user_id="system",
        username="System",
        content=content,
        message_type=MessageType.SYSTEM
    )


def _broadcast_to_room(room_id: str, data: dict):
    """Broadcast data to all connections in a room"""
    if room_id not in SERVER_STATE.active_connections:
        return
    
    # Serialize data
    serialized = json.dumps(data)
    
    # Send to all active connections
    disconnected = []
    for ws in SERVER_STATE.active_connections[room_id]:
        try:
            asyncio.create_task(ws.send(serialized))
        except Exception as e:
            logger.error(f"Failed to send to websocket: {e}")
            disconnected.append(ws)
    
    # Clean up disconnected websockets
    for ws in disconnected:
        SERVER_STATE.active_connections[room_id].discard(ws)


def attach_endpoints(app: Sanic):
    """Attach all endpoints to the Sanic app"""
    
    # === WebSocket Endpoints ===
    
    @app.websocket("/talk")
    async def talk_ws_view(request: Request, ws: Websocket) -> HTTPResponse:
        """WebSocket endpoint for sending messages"""
        try:
            # Authentication check
            if not _check_password(request, app.ctx.ADMIN_PASSWORD):
                await ws.close(code=4001, reason="unauthorized")
                return
            
            # Parse connection parameters
            room_id = request.args.get("room_id") or "general"  # Default to general room
            username = request.args.get("username") or "unknown"
            
            # Create user if not exists
            user_id = f"{request.ip}:{username}"
            if user_id not in SERVER_STATE.users:
                user = User(username=username, ip_address=request.ip)
                SERVER_STATE.users[user_id] = user
            
            # Add connection
            if room_id not in SERVER_STATE.active_connections:
                SERVER_STATE.active_connections[room_id] = set()
            
            SERVER_STATE.active_connections[room_id].add(ws)
            SERVER_STATE.user_websockets[user_id] = ws
            
            # Store connection info
            SERVER_STATE.connections[user_id] = ConnectionInfo(
                user_id=user_id,
                room_id=room_id,
                connected_at=datetime.utcnow()
            )
            
            # Send welcome message
            welcome_msg = {
                "type": "connected",
                "room_id": room_id,
                "user_count": len(SERVER_STATE.active_connections[room_id]),
                "timestamp": datetime.utcnow().isoformat()
            }
            await ws.send(json.dumps(welcome_msg))
            
            # Handle incoming messages
            async for message_data in ws:
                try:
                    # Parse incoming message
                    data = json.loads(message_data)
                    
                    # Check if it's a close signal
                    if data.get("action") == "close":
                        break
                    
                    # Rate limiting check
                    if not _check_rate_limit(user_id):
                        await ws.send(json.dumps({"error": "Rate limit exceeded"}))
                        continue
                    
                    # Create and store message
                    message = Message(
                        room_id=room_id,
                        user_id=user_id,
                        username=username,
                        content=data.get("text", ""),
                        message_type=MessageType.TEXT
                    )
                    
                    # Add to room messages
                    if room_id not in SERVER_STATE.messages:
                        SERVER_STATE.messages[room_id] = []
                    
                    SERVER_STATE.messages[room_id].append(message)
                    
                    # Add to history if enabled
                    if room_id in SERVER_STATE.room_histories:
                        SERVER_STATE.room_histories[room_id].add_message(message)
                    
                    # Broadcast to room
                    _broadcast_to_room(room_id, {
                        "type": "message",
                        "message": _serialize_message(message)
                    })
                    
                    # Send confirmation
                    await ws.send(json.dumps({"status": "ok", "message_id": message.id}))
                    
                except json.JSONDecodeError:
                    await ws.send(json.dumps({"error": "Invalid JSON"}))
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    await ws.send(json.dumps({"error": "Message processing failed"}))
                    
        except Exception as e:
            logger.error(f"WebSocket connection error: {e}")
        finally:
            # Cleanup
            if user_id in SERVER_STATE.user_websockets:
                del SERVER_STATE.user_websockets[user_id]
            if user_id in SERVER_STATE.connections:
                del SERVER_STATE.connections[user_id]
            if room_id in SERVER_STATE.active_connections:
                SERVER_STATE.active_connections[room_id].discard(ws)


    @app.websocket("/update")
    async def update_ws_view(request: Request, ws: Websocket) -> HTTPResponse:
        """WebSocket for receiving updates"""
        try:
            if not _check_password(request, app.ctx.ADMIN_PASSWORD):
                await ws.close(code=4001, reason="unauthorized")
                return
            
            room_id = request.args.get("room_id") or "general"
            
            if room_id not in SERVER_STATE.active_connections:
                SERVER_STATE.active_connections[room_id] = set()
            
            SERVER_STATE.active_connections[room_id].add(ws)
            
            # Send current room state
            room_data = {
                "type": "room_update",
                "room": {
                    "id": room_id,
                    "name": SERVER_STATE.rooms.get(room_id, {}).name if room_id in SERVER_STATE.rooms else room_id,
                    "member_count": len(SERVER_STATE.active_connections[room_id])
                },
                "recent_messages": [
                    _serialize_message(msg) for msg in 
                    SERVER_STATE.messages.get(room_id, [])[-50:]  # Last 50 messages
                ],
                "timestamp": datetime.utcnow().isoformat()
            }
            await ws.send(json.dumps(room_data))
            
            # Keep connection alive with periodic updates
            while True:
                try:
                    # Send periodic heartbeat
                    heartbeat = {
                        "type": "heartbeat",
                        "user_count": len(SERVER_STATE.active_connections[room_id]),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    await ws.send(json.dumps(heartbeat))
                    await asyncio.sleep(30)  # 30 second heartbeat
                    
                except Exception as e:
                    logger.error(f"Heartbeat error: {e}")
                    break
                    
        except Exception as e:
            logger.error(f"Update WebSocket error: {e}")
        finally:
            SERVER_STATE.active_connections[room_id].discard(ws)


    # === REST API Endpoints ===
    
    @app.route('/get_key', methods=['GET', 'POST'])
    async def get_key_view(request: Request) -> HTTPResponse:
        """Key exchange endpoint"""
        try:
            if not _check_password(request, app.ctx.ADMIN_PASSWORD):
                return response.json({"error": "unauthorized"}, status=401)

            # Handle multiple input methods
            pubkey_bytes = None
            
            # Check files
            if "pubkey" in request.files and request.files.get("pubkey"):
                f = request.files.get("pubkey")
                if isinstance(f, list):
                    f = f[0]
                pubkey_bytes = f.body

            # Check form data
            if pubkey_bytes is None:
                raw = request.form.get("pubkey")
                if raw:
                    pubkey_bytes = raw if isinstance(raw, bytes) else str(raw).encode()

            # Check query params
            if pubkey_bytes is None:
                raw = request.args.get("pubkey")
                if raw:
                    pubkey_bytes = raw.encode()
            
            # Check JSON body
            if pubkey_bytes is None and request.json:
                raw = request.json.get("pubkey")
                if raw:
                    pubkey_bytes = raw.encode() if isinstance(raw, str) else raw

            if not pubkey_bytes:
                return response.json({"error": "public key is required"}, status=400)

            # Load and validate public key
            try:
                public_key = serialization.load_pem_public_key(pubkey_bytes)
            except Exception as e:
                return response.json({"error": f"invalid public key: {e}"}, status=400)

            # Encrypt symmetric key using modern RSA
            encrypted_key = public_key.encrypt(
                SERVER_STATE.symmetric_key,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )

            username = _get_str_arg(request, "username") or "unknown"
            
            # Store user info
            user_id = f"{request.ip}, {username}"
            if user_id not in SERVER_STATE.users:
                SERVER_STATE.users[user_id] = User(
                    username=username, 
                    ip_address=request.ip
                )

            return response.raw(encrypted_key)
            
        except Exception as e:
            logger.error(f"Key exchange error: {e}")
            return response.json({"error": "key exchange failed"}, status=500)


    @app.route('/rooms', methods=['GET'])
    async def list_rooms(request: Request) -> HTTPResponse:
        """List all available rooms"""
        try:
            rooms_list = []
            for room in SERVER_STATE.rooms.values():
                if room.is_active:
                    room_data = room.to_dict()
                    room_data["active_users"] = len(SERVER_STATE.active_connections.get(room.id, set()))
                    rooms_list.append(room_data)
            
            return response.json({
                "rooms": rooms_list,
                "total": len(rooms_list)
            })
        except Exception as e:
            logger.error(f"List rooms error: {e}")
            return response.json({"error": "failed to list rooms"}, status=500)


    @app.route('/rooms', methods=['POST'])
    async def create_room(request: Request) -> HTTPResponse:
        """Create a new room"""
        try:
            if not _check_password(request, app.ctx.ADMIN_PASSWORD):
                return response.json({"error": "unauthorized"}, status=401)
            
            data = request.json or {}
            name = data.get("name", "").strip()
            room_type = data.get("type", "public")
            description = data.get("description", "")
            created_by = _get_str_arg(request, "username") or "unknown"
            
            if not name:
                return response.json({"error": "room name is required"}, status=400)
            
            # Create room
            room = Room(
                name=name,
                type=room_type,
                created_by=created_by,
                description=description
            )
            
            SERVER_STATE.rooms[room.id] = room
            SERVER_STATE.messages[room.id] = []
            SERVER_STATE.room_histories[room.id] = RoomHistory(room_id=room.id)
            SERVER_STATE.active_connections[room.id] = set()
            
            return response.json({
                "success": True,
                "room": room.to_dict()
            })
            
        except Exception as e:
            logger.error(f"Create room error: {e}")
            return response.json({"error": "failed to create room"}, status=500)


    @app.route('/health', methods=['GET'])
    async def health_check(request: Request) -> HTTPResponse:
        """Health check endpoint"""
        return response.json({
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "active_rooms": len([r for r in SERVER_STATE.rooms.values() if r.is_active]),
            "total_users": len(SERVER_STATE.users),
            "active_connections": sum(len(conns) for conns in SERVER_STATE.active_connections.values())
        })


def create_app(app_name: str, admin_password: str | None) -> Sanic:
    """Create and configure the Sanic app"""
    app = Sanic(app_name)
    app.config.OAS = False
    app.ctx.ADMIN_PASSWORD = admin_password
    
    # Add CORS headers for web interface
    @app.middleware("response")
    async def add_cors_headers(request, response):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    
    attach_endpoints(app)
    return app


def run_server(host: str, port: int, dev: bool = False, admin_password: str | None = None) -> None:
    """Server startup with better error handling"""
    try:
        logger.info(f"Starting CMD Chat Server on {host}:{port}")
        logger.info(f"Password protection: {'Enabled' if admin_password else 'Disabled'}")
        logger.info(f"Development mode: {dev}")
        
        # Create app
        loader = AppLoader(factory=partial(create_app, "CMD_SERVER", admin_password))
        app = loader.load()
        
        # Prepare server
        app.prepare(host=host, port=port, dev=dev)
        
        # Log startup info
        logger.info("Server startup complete")
        logger.info(f"Default rooms: {', '.join([r.name for r in SERVER_STATE.rooms.values()])}")
        
        # Start server
        Sanic.serve(primary=app, app_loader=loader)
        
    except Exception as e:
        logger.error(f"Server startup failed: {e}")
        raise
