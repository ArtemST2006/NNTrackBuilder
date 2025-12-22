import asyncio
import json
import logging
from typing import Any, Callable, Dict, Optional

import websockets
from config import config
from websockets.exceptions import ConnectionClosed

logger = logging.getLogger(__name__)


class GatewayWebSocketClient:  # WebSocket клиент для подключения к API Gateway
    def __init__(self):
        # Подключение
        self.connection: Optional[websockets.WebSocketClientProtocol] = None
        self.connected: bool = False
        self.user_id: Optional[int] = None
        self.ws_url: Optional[str] = None

        # Состояние
        self.running: bool = False

        # Очередь для входящих сообщений
        self.incoming_queue: asyncio.Queue = asyncio.Queue()

        # Ожидающие задачи:
        self.waiting_tasks: Dict[str, asyncio.Future] = {}

        # Обработчики сообщений по типу
        self.message_handlers: Dict[str, Callable] = {}

        # Переподключение
        self.reconnect_attempts: int = 0
        self.max_reconnect_attempts: int = 5

        # Статистика
        self.messages_received: int = 0
        self.messages_sent: int = 0

    async def connect(self, user_id: int) -> bool:
        # Если уже подключены для этого пользователя
        if self.connected and self.user_id == user_id:
            return True

        # Закрываем старое соединение если есть
        if self.connection:
            await self.disconnect()

        self.user_id = user_id

        # Формируем URL WebSocket
        if config.API_GATEWAY_WS_URL:
            self.ws_url = f"{config.API_GATEWAY_WS_URL}/{user_id}"
        else:
            # Авто-генерация URL
            base_url = config.API_GATEWAY_URL
            if base_url.startswith("http://"):
                ws_base = base_url.replace("http://", "ws://")
            elif base_url.startswith("https://"):
                ws_base = base_url.replace("https://", "wss://")
            else:
                ws_base = f"ws://{base_url}"

            self.ws_url = f"{ws_base}/ws/{user_id}"

        try:
            logger.info(f"🌐 Подключаюсь к WebSocket API Gateway: {self.ws_url}")

            # Подключаемся с таймаутом
            self.connection = await websockets.connect(
                self.ws_url,
                ping_interval=20,
                ping_timeout=10,
                close_timeout=1,
                max_size=10 * 1024 * 1024,
            )

            self.connected = True
            self.running = True
            self.reconnect_attempts = 0

            # Запускаем задачи приема и обработки сообщений
            asyncio.create_task(self._receive_loop())
            asyncio.create_task(self._process_messages_loop())

            logger.info(f"✅ WebSocket подключен для user_id: {user_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Ошибка подключения WebSocket: {e}")
            self.connected = False
            self.running = False
            return False

    async def disconnect(self):
        self.running = False
        self.connected = False

        # Отменяем все ожидающие задачи
        for task_id, future in self.waiting_tasks.items():
            if not future.done():
                future.set_exception(ConnectionClosed(None, None, "Соединение закрыто"))

        self.waiting_tasks.clear()

        # Закрываем соединение
        if self.connection:
            try:
                await self.connection.close()
            except:
                pass
            self.connection = None

        # Очищаем очередь
        while not self.incoming_queue.empty():
            try:
                self.incoming_queue.get_nowait()
            except:
                break

        logger.info("🌐 WebSocket соединение закрыто")

    async def _receive_loop(self):
        while self.running and self.connected:
            try:
                # Получаем сообщение
                message = await self.connection.recv()

                # Кладем сообщение в очередь для обработки
                await self.incoming_queue.put(message)
                self.messages_received += 1

            except ConnectionClosed:
                logger.warning("📡 WebSocket соединение закрыто сервером")
                self.connected = False
                await self._handle_disconnection()
                break

            except Exception as e:
                if self.running:
                    logger.error(f"❌ Ошибка в receive_loop: {e}")
                    self.connected = False
                    await self._handle_disconnection()
                break

    async def _process_messages_loop(self):
        while self.running:
            try:
                # Ждем сообщение из очереди с таймаутом
                try:
                    message = await asyncio.wait_for(
                        self.incoming_queue.get(), timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue

                # Обрабатываем сообщение
                await self._process_message(message)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Ошибка в process_messages_loop: {e}")

    async def _process_message(self, message: str):
        try:
            data = json.loads(message)

            # Логируем полученное сообщение
            task_id = data.get("task_id")
            status = data.get("status")
            logger.debug(f"📨 Получено сообщение: task_id={task_id}, status={status}")

            # Если есть ожидающая задача - разбудить ее
            if task_id and task_id in self.waiting_tasks:
                future = self.waiting_tasks.pop(task_id)
                if not future.done():
                    future.set_result(data)
                logger.info(f"✅ Задача {task_id} завершена (status: {status})")

            # Вызываем обработчик по типу сообщения если есть
            handler = self.message_handlers.get(status)
            if handler:
                try:
                    await handler(data)
                except Exception as e:
                    logger.error(f"❌ Ошибка в обработчике сообщения: {e}")

            # Общий обработчик для всех сообщений
            handler_all = self.message_handlers.get("*")
            if handler_all:
                try:
                    await handler_all(data)
                except Exception as e:
                    logger.error(f"❌ Ошибка в общем обработчике: {e}")

        except json.JSONDecodeError:
            logger.error(f"❌ Невалидный JSON: {message[:100]}")
        except Exception as e:
            logger.error(f"❌ Ошибка обработки сообщения: {e}")

    async def _handle_disconnection(self):
        if self.reconnect_attempts < self.max_reconnect_attempts:
            self.reconnect_attempts += 1
            delay = config.WS_RECONNECT_DELAY * self.reconnect_attempts

            logger.info(
                f"🔄 Попытка переподключения {self.reconnect_attempts}/{self.max_reconnect_attempts} через {delay} сек"
            )

            await asyncio.sleep(delay)

            if self.user_id:
                await self.connect(self.user_id)
        else:
            logger.error(
                f"❌ Достигнут максимум попыток переподключения ({self.max_reconnect_attempts})"
            )

    async def wait_for_task(self, task_id: str, timeout: int = None) -> Dict[str, Any]:
        if not self.connected:
            return {
                "success": False,
                "status": "not_connected",
                "error": "WebSocket не подключен",
                "task_id": task_id,
            }

        if timeout is None:
            timeout = config.WS_TIMEOUT

        # Создаем Future для ожидания
        future = asyncio.get_event_loop().create_future()
        self.waiting_tasks[task_id] = future

        try:
            # Ждем с таймаутом
            result = await asyncio.wait_for(future, timeout=timeout)
            return result

        except asyncio.TimeoutError:
            # Удаляем из ожидающих
            if task_id in self.waiting_tasks:
                del self.waiting_tasks[task_id]

            return {
                "success": False,
                "status": "timeout",
                "task_id": task_id,
                "error": f"Таймаут ожидания ({timeout} сек)",
            }

        except Exception as e:
            if task_id in self.waiting_tasks:
                del self.waiting_tasks[task_id]

            return {
                "success": False,
                "status": "error",
                "task_id": task_id,
                "error": str(e),
            }

    def register_handler(self, message_type: str, handler: Callable):
        self.message_handlers[message_type] = handler
        logger.info(f"📋 Зарегистрирован обработчик для типа: {message_type}")

    async def send_message(self, data: dict) -> bool:
        if not self.connected:
            logger.error("❌ Не удалось отправить сообщение: WebSocket не подключен")
            return False

        try:
            message = json.dumps(data)
            await self.connection.send(message)
            self.messages_sent += 1
            logger.debug(f"📤 Отправлено сообщение: {data.get('type', 'unknown')}")
            return True

        except Exception as e:
            logger.error(f"❌ Ошибка отправки сообщения: {e}")
            return False

    def is_connected(self) -> bool:
        return self.connected and self.running

    async def ensure_connection(self, user_id: int) -> bool:
        if self.is_connected() and self.user_id == user_id:
            return True

        return await self.connect(user_id)

    def get_stats(self) -> Dict[str, Any]:
        return {
            "connected": self.connected,
            "user_id": self.user_id,
            "messages_received": self.messages_received,
            "messages_sent": self.messages_sent,
            "waiting_tasks": len(self.waiting_tasks),
            "reconnect_attempts": self.reconnect_attempts,
            "queue_size": self.incoming_queue.qsize(),
        }

    async def ping(self) -> bool:
        if not self.connected:
            return False

        try:
            await self.connection.ping()
            return True
        except:
            self.connected = False
            return False


# Глобальный экземпляр клиента
gateway_ws = GatewayWebSocketClient()
