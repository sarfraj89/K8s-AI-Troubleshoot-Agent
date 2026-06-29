"""Optional InsForge realtime progress publisher."""

from __future__ import annotations

from typing import Any

from loguru import logger

from app.core.config import settings

try:
    import socketio
except ImportError:  # pragma: no cover - depends on optional runtime install
    socketio = None


class ProgressPublisher:
    """Publishes investigation progress to an InsForge realtime channel.

    The publisher is deliberately best-effort. Investigation should still work
    if InsForge realtime is not configured or the websocket is unavailable.
    """

    def __init__(self, channel: str | None):
        self.channel = channel
        self.enabled = bool(channel and settings.INSFORGE_URL and socketio)
        self.client: Any | None = None

    def __enter__(self) -> "ProgressPublisher":
        if not self.enabled:
            return self

        auth: dict[str, str] = {}
        if settings.INSFORGE_API_KEY:
            auth["apiKey"] = settings.INSFORGE_API_KEY
        elif settings.INSFORGE_ANON_KEY:
            auth["token"] = settings.INSFORGE_ANON_KEY
        else:
            logger.warning("InsForge realtime disabled: no API key or anon key configured")
            self.enabled = False
            return self

        try:
            self.client = socketio.Client(reconnection=False, request_timeout=5)
            self.client.connect(settings.INSFORGE_URL, auth=auth, wait_timeout=5)
            response = self.client.call(
                "realtime:subscribe",
                {"channel": self.channel},
                timeout=5,
            )
            if not response or not response.get("ok"):
                logger.warning("InsForge realtime subscribe failed: {}", response)
                self.close()
        except Exception as exc:
            logger.warning("InsForge realtime connection failed: {}", exc)
            self.close()

        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def publish(self, step: str, status: str, message: str = "") -> None:
        if not self.client or not self.channel:
            return

        try:
            self.client.emit(
                "realtime:publish",
                {
                    "channel": self.channel,
                    "event": "progress",
                    "payload": {
                        "step": step,
                        "status": status,
                        "message": message,
                    },
                },
            )
        except Exception as exc:
            logger.warning("Failed to publish progress update: {}", exc)

    def close(self) -> None:
        if not self.client:
            return

        try:
            if self.channel:
                self.client.emit("realtime:unsubscribe", {"channel": self.channel})
            self.client.disconnect()
        except Exception:
            pass
        finally:
            self.client = None
