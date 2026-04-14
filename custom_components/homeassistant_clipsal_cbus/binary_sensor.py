"""Binary sensor platform for Clipsal C-Bus motion and alarms."""
from __future__ import annotations
from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import DOMAIN, APP_LIGHTING, APP_SECURITY, MOTION_SENSORS, ALARMS
from .coordinator import CbusCoordinator, SIGNAL_STATE_UPDATED


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up binary sensors from a config entry."""
    coordinator: CbusCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[BinarySensorEntity] = []
    entities += [
        CbusBinarySensor(coordinator, APP_LIGHTING, g, n, BinarySensorDeviceClass.MOTION)
        for g, n in MOTION_SENSORS.items()
    ]
    entities += [
        CbusBinarySensor(
            coordinator, APP_SECURITY, g, n,
            BinarySensorDeviceClass.SMOKE if dc == "smoke" else BinarySensorDeviceClass.GAS
        )
        for g, (n, dc) in ALARMS.items()
    ]
    async_add_entities(entities)


class CbusBinarySensor(BinarySensorEntity):
    """Representation of a Clipsal C-Bus binary sensor."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: CbusCoordinator, app: int, group: int,
                 name: str, device_class: BinarySensorDeviceClass) -> None:
        self._coordinator = coordinator
        self._app = app
        self._group = group
        self._attr_name = name
        self._attr_unique_id = f"cbus_binary_{app}_{group}"
        self._attr_device_class = device_class
        self._is_on = False

    @property
    def is_on(self) -> bool:
        return self._is_on

    @callback
    def _handle_update(self, level: int) -> None:
        self._is_on = level > 0
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(async_dispatcher_connect(
            self.hass, f"{SIGNAL_STATE_UPDATED}_{self._app}_{self._group}", self._handle_update
        ))
        if (v := self._coordinator.get_level(self._app, self._group)) is not None:
            self._is_on = v > 0
