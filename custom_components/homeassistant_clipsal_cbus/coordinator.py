"""WebSocket coordinator for Clipsal C-Bus 5500SHAC."""
import asyncio
import json
import logging

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SIGNAL_STATE_UPDATED = f"{DOMAIN}_state_updated"
PING_INTERVAL = 10
RECONNECT_DELAY = 5


def encode_address(app: int, group: int, net: int = 0) -> int:
    """Encode a C-Bus group address to raw integer."""
    if app == 250:
        return (250 << 24) | group
    return (app << 24) | (net << 16) | (group << 8)


def decode_address(raw: int) -> tuple[int, int, int]:
    """Decode raw address to (app, net, group)."""
    app = (raw >> 24) & 0xFF
    if app == 250:
        return (250, 0, raw & 0xFFFFFF)
    net   = (raw >> 16) & 0xFF
    group = (raw >>  8) & 0xFF
    return (app, net, group)


def parse_level(app: int, datahex: str) -> int:
    """Parse level from datahex string.

    App 250 (User Parameter) temperatures are in the last byte.
    All other apps use the first byte.
    """
    try:
        if app == 250:
            return int(datahex[6:8], 16)
        return int(datahex[:2], 16)
    except (ValueError, IndexError):
        return 0


class CbusCoordinator:
    """Manages the persistent WebSocket connection to the Clipsal 5500SHAC."""

    def __init__(self, hass: HomeAssistant, host: str, port: int) -> None:
        """Initialise the coordinator."""
        self.hass = hass
        self.host = host
        self.port = port
        self._ws = None
        self._session: aiohttp.ClientSession | None = None
        self._running = False
        self._ping_task: asyncio.Task | None = None
        self._connect_task: asyncio.Task | None = None
        self.state: dict[tuple[int, int], int] = {}

    async def async_start(self) -> None:
        """Start the coordinator."""
        self._running = True
        self._session = aiohttp.ClientSession()
        self._connect_task = asyncio.ensure_future(self._connection_loop())

    async def async_stop(self) -> None:
        """Stop the coordinator and clean up."""
        self._running = False
        for task in (self._ping_task, self._connect_task):
            if task:
                task.cancel()
        if self._ws:
            await self._ws.close()
        if self._session:
            await self._session.close()

    async def _connection_loop(self) -> None:
        """Keep WebSocket connected, reconnecting on failure."""
        url = f"ws://{self.host}:{self.port}/scada-vis/objects/ws"
        while self._running:
            try:
                async with self._session.ws_connect(
                    url,
                    heartbeat=None,
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as ws:
                    self._ws = ws
                    _LOGGER.info("C-Bus WebSocket connected to %s", url)
                    self._ping_task = asyncio.ensure_future(self._ping_loop(ws))
                    async for msg in ws:
                        if msg.type in (aiohttp.WSMsgType.TEXT, aiohttp.WSMsgType.BINARY):
                            await self._handle_message(msg.data)
                        elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                            break
            except asyncio.CancelledError:
                return
            except Exception as err:
                _LOGGER.warning("C-Bus connection error: %s — reconnecting in %ds", err, RECONNECT_DELAY)

            if self._ping_task:
                self._ping_task.cancel()
                self._ping_task = None
            if self._running:
                await asyncio.sleep(RECONNECT_DELAY)

    async def _ping_loop(self, ws: aiohttp.ClientWebSocketResponse) -> None:
        """Send keepalive pings every 10 seconds."""
        try:
            while True:
                await asyncio.sleep(PING_INTERVAL)
                if not ws.closed:
                    await ws.send_str("ping")
        except asyncio.CancelledError:
            pass

    async def _handle_message(self, raw: bytes | str) -> None:
        """Parse an incoming C-Bus message and dispatch to entities."""
        if isinstance(raw, (bytes, bytearray)):
            raw = raw.decode("utf-8", errors="ignore")
        json_start = raw.find("{")
        if json_start == -1:
            return
        try:
            msg = json.loads(raw[json_start:])
        except json.JSONDecodeError:
            return
        if "auth" in msg:
            _LOGGER.debug("C-Bus auth token received")
            return
        if msg.get("type") != "groupwrite":
            return
        dstraw = msg.get("dstraw")
        datahex = msg.get("datahex", "")
        if dstraw is None or not datahex:
            return
        app, net, group = decode_address(dstraw)
        level = parse_level(app, datahex)
        self.state[(app, group)] = level
        signal = f"{SIGNAL_STATE_UPDATED}_{app}_{group}"
        async_dispatcher_send(self.hass, signal, level)
        _LOGGER.debug("C-Bus update: app=%d group=%d level=%d", app, group, level)

    async def async_write(self, app: int, group: int, value: int, net: int = 0) -> None:
        """Send a write command to a C-Bus group."""
        if not self._ws or self._ws.closed:
            _LOGGER.error("C-Bus WebSocket not connected — cannot write")
            return
        address = encode_address(app, group, net)
        cmd = {
            "address": address,
            "datatype": 5,
            "value": value,
            "type": "text",
            "update": False,
            "action": "write",
        }
        await self._ws.send_str(json.dumps(cmd))
        _LOGGER.debug("C-Bus write: app=%d group=%d value=%d", app, group, value)

    def get_level(self, app: int, group: int) -> int | None:
        """Get the current cached level for a group."""
        return self.state.get((app, group))
