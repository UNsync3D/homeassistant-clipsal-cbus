"""Switch platform for Clipsal C-Bus fans and scenes."""
from __future__ import annotations
from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import DOMAIN, APP_LIGHTING, APP_SCENES, FANS, SCENES
from .coordinator import CbusCoordinator, SIGNAL_STATE_UPDATED


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up fans and scenes from a config entry."""
    coordinator: CbusCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[SwitchEntity] = []
    entities += [CbusFan(coordinator, g, n) for g, n in FANS.items()]
    entities += [CbusScene(coordinator, g, n) for g, n in SCENES.items()]
    async_add_entities(entities)


class CbusFan(SwitchEntity):
    """Representation of a Clipsal C-Bus fan."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:fan"

    def __init__(self, coordinator: CbusCoordinator, group: int, name: str) -> None:
        self._coordinator = coordinator
        self._group = group
        self._attr_name = name
        self._attr_unique_id = f"cbus_fan_{group}"
        self._is_on = False

    @property
    def is_on(self) -> bool:
        return self._is_on

    async def async_turn_on(self, **kwargs) -> None:
        await self._coordinator.async_write(APP_LIGHTING, self._group, 255)

    async def async_turn_off(self, **kwargs) -> None:
        await self._coordinator.async_write(APP_LIGHTING, self._group, 0)

    @callback
    def _handle_update(self, level: int) -> None:
        self._is_on = level > 0
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(async_dispatcher_connect(
            self.hass, f"{SIGNAL_STATE_UPDATED}_{APP_LIGHTING}_{self._group}", self._handle_update
        ))
        if (v := self._coordinator.get_level(APP_LIGHTING, self._group)) is not None:
            self._is_on = v > 0


class CbusScene(SwitchEntity):
    """Representation of a Clipsal C-Bus scene trigger."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:palette"

    def __init__(self, coordinator: CbusCoordinator, group: int, name: str) -> None:
        self._coordinator = coordinator
        self._group = group
        self._attr_name = f"Scene: {name}"
        self._attr_unique_id = f"cbus_scene_{group}"

    @property
    def is_on(self) -> bool:
        return False

    async def async_turn_on(self, **kwargs) -> None:
        await self._coordinator.async_write(APP_SCENES, self._group, 255)

    async def async_turn_off(self, **kwargs) -> None:
        pass

    async def async_added_to_hass(self) -> None:
        pass
