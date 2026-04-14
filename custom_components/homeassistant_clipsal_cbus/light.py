"""Light platform for Clipsal C-Bus."""
from __future__ import annotations
from homeassistant.components.light import LightEntity, ColorMode, ATTR_BRIGHTNESS
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import DOMAIN, APP_LIGHTING, LIGHTS
from .coordinator import CbusCoordinator, SIGNAL_STATE_UPDATED


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up lights from a config entry."""
    coordinator: CbusCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        CbusLight(coordinator, group, name)
        for group, name in LIGHTS.items()
    )


class CbusLight(LightEntity):
    """Representation of a Clipsal C-Bus dimmable light."""

    _attr_has_entity_name = True
    _attr_color_mode = ColorMode.BRIGHTNESS
    _attr_supported_color_modes = {ColorMode.BRIGHTNESS}

    def __init__(self, coordinator: CbusCoordinator, group: int, name: str) -> None:
        self._coordinator = coordinator
        self._group = group
        self._attr_name = name
        self._attr_unique_id = f"cbus_light_{group}"
        self._level = 0

    @property
    def is_on(self) -> bool:
        return self._level > 0

    @property
    def brightness(self) -> int:
        return self._level

    async def async_turn_on(self, **kwargs) -> None:
        await self._coordinator.async_write(APP_LIGHTING, self._group, kwargs.get(ATTR_BRIGHTNESS, 255))

    async def async_turn_off(self, **kwargs) -> None:
        await self._coordinator.async_write(APP_LIGHTING, self._group, 0)

    @callback
    def _handle_update(self, level: int) -> None:
        self._level = level
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(async_dispatcher_connect(
            self.hass, f"{SIGNAL_STATE_UPDATED}_{APP_LIGHTING}_{self._group}", self._handle_update
        ))
        if (v := self._coordinator.get_level(APP_LIGHTING, self._group)) is not None:
            self._level = v
