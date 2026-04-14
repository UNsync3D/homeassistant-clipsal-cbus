"""Cover platform for Clipsal C-Bus blinds and curtains."""
from __future__ import annotations
from homeassistant.components.cover import CoverEntity, CoverEntityFeature, ATTR_POSITION
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import DOMAIN, APP_LIGHTING, BLINDS
from .coordinator import CbusCoordinator, SIGNAL_STATE_UPDATED


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up covers from a config entry."""
    coordinator: CbusCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        CbusBlind(coordinator, group, name)
        for group, name in BLINDS.items()
    )


class CbusBlind(CoverEntity):
    """Representation of a Clipsal C-Bus blind or curtain."""

    _attr_has_entity_name = True
    _attr_supported_features = (
        CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE | CoverEntityFeature.SET_POSITION
    )

    def __init__(self, coordinator: CbusCoordinator, group: int, name: str) -> None:
        self._coordinator = coordinator
        self._group = group
        self._attr_name = name
        self._attr_unique_id = f"cbus_cover_{group}"
        self._level = 0

    @property
    def current_cover_position(self) -> int:
        return round(self._level / 255 * 100)

    @property
    def is_closed(self) -> bool:
        return self._level == 0

    async def async_open_cover(self, **kwargs) -> None:
        await self._coordinator.async_write(APP_LIGHTING, self._group, 255)

    async def async_close_cover(self, **kwargs) -> None:
        await self._coordinator.async_write(APP_LIGHTING, self._group, 0)

    async def async_set_cover_position(self, **kwargs) -> None:
        level = round(kwargs[ATTR_POSITION] / 100 * 255)
        await self._coordinator.async_write(APP_LIGHTING, self._group, level)

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
