"""
WebSocket 路由
"""

import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.logging import logger


class WSMessageType:
    """WebSocket 消息类型"""

    PING = "ping"
    PONG = "pong"
    MESSAGE = "message"
    WELCOME = "welcome"
    ECHO = "echo"
    BROADCAST = "broadcast"
    ERROR = "error"


class ConnectionManager:
    """WebSocket 连接管理器"""

    def __init__(self):
        self.active_connections: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket 客户端已连接，当前连接数: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket) -> None:
        self.active_connections.discard(websocket)
        logger.info(f"WebSocket 客户端已断开，当前连接数: {len(self.active_connections)}")

    async def send_personal_message(self, message: dict, websocket: WebSocket) -> None:
        await websocket.send_json(message)

    async def broadcast(self, message: dict) -> None:
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.add(connection)
        self.active_connections -= disconnected


manager = ConnectionManager()

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """基础 WebSocket 端点"""
    await manager.connect(websocket)

    try:
        await manager.send_personal_message(
            {
                "type": WSMessageType.WELCOME,
                "message": "欢迎连接 WebSocket 服务！",
                "connectionCount": len(manager.active_connections),
            },
            websocket,
        )

        while True:
            try:
                message = await asyncio.wait_for(websocket.receive_json(), timeout=60.0)

                msg_type = message.get("type")

                if msg_type == WSMessageType.PING:
                    await manager.send_personal_message({"type": WSMessageType.PONG}, websocket)

                elif msg_type == WSMessageType.MESSAGE:
                    content = message.get("content", "")
                    await manager.send_personal_message({"type": WSMessageType.ECHO, "content": content}, websocket)

                else:
                    await manager.send_personal_message(
                        {
                            "type": WSMessageType.ERROR,
                            "message": f"未知的消息类型: {msg_type}",
                        },
                        websocket,
                    )

            except TimeoutError:
                await manager.send_personal_message({"type": WSMessageType.PING}, websocket)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        manager.disconnect(websocket)
        logger.error(f"WebSocket 错误: {e}")


@router.websocket("/ws/broadcast")
async def websocket_broadcast_endpoint(websocket: WebSocket):
    """广播 WebSocket 端点"""
    await manager.connect(websocket)

    try:
        await manager.send_personal_message(
            {
                "type": WSMessageType.WELCOME,
                "message": "已连接到广播频道",
                "connectionCount": len(manager.active_connections),
            },
            websocket,
        )

        await manager.broadcast(
            {
                "type": WSMessageType.BROADCAST,
                "content": f"新用户加入，当前在线: {len(manager.active_connections)}",
            }
        )

        while True:
            try:
                message = await asyncio.wait_for(websocket.receive_json(), timeout=60.0)

                msg_type = message.get("type")

                if msg_type == WSMessageType.PING:
                    await manager.send_personal_message({"type": WSMessageType.PONG}, websocket)

                elif msg_type == WSMessageType.MESSAGE:
                    content = message.get("content", "")
                    await manager.broadcast({"type": WSMessageType.BROADCAST, "content": content})

            except TimeoutError:
                await manager.send_personal_message({"type": WSMessageType.PING}, websocket)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(
            {
                "type": WSMessageType.BROADCAST,
                "content": f"用户离开，当前在线: {len(manager.active_connections)}",
            }
        )
    except Exception as e:
        manager.disconnect(websocket)
        logger.error(f"WebSocket 广播端点错误: {e}")
