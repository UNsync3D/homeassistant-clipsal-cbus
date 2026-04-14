"""Config flow for Clipsal C-Bus integration."""
import json
import logging

import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT

from .const import DOMAIN, DEFAULT_PORT

_LOGGER = logging.getLogger(__name__)


async def _test_connection(host: str, port: int) -> tuple[bool, str]:
    """Test connection to the 5500SHAC by opening a WebSocket."""
    url = f"ws://{host}:{port}/scada-vis/objects/ws"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(
                url,
                timeout=aiohttp.ClientTimeout(total=8),
                heartbeat=None,
            ) as ws:
                msg = await ws.receive(timeout=6.0)
                if msg.type in (aiohttp.WSMsgType.TEXT, aiohttp.WSMsgType.BINARY):
                    raw = msg.data if isinstance(msg.data, str) else msg.data.decode("utf-8", errors="ignore")
                    json_start = raw.find("{")
                    if json_start == -1:
                        return False, "invalid_response"
                    try:
                        json.loads(raw[json_start:])
                        return True, ""
                    except json.JSONDecodeError:
                        return False, "invalid_response"
                elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                    return False, "cannot_connect"
                return False, "invalid_response"
    except aiohttp.ClientConnectorError:
        return False, "cannot_connect"
    except aiohttp.ServerTimeoutError:
        return False, "cannot_connect"
    except TimeoutError:
        return False, "cannot_connect"


class CbusConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Clipsal C-Bus integration."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            port = user_input[CONF_PORT]
            try:
                success, error_key = await _test_connection(host, port)
                if not success:
                    errors["base"] = error_key
            except Exception:
                _LOGGER.exception("Unexpected error during C-Bus config flow")
                errors["base"] = "unknown"

            if not errors:
                await self.async_set_unique_id(f"cbus_{host}_{port}")
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"Clipsal C-Bus ({host})",
                    data={CONF_HOST: host, CONF_PORT: port},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_HOST, default="192.168.1.250"): str,
                vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
            }),
            errors=errors,
        )
