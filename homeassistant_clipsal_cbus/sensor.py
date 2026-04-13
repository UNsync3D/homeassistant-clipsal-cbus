"""Sensor platform for Clipsal C-Bus temperature sensors."""
from __future__ import annotations
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import DOMAIN, APP_USER_PARAM, AC_ZONES
from .coordinator import CbusCoordinator, SIGNAL_STATE_UPDATED


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up temperature sensors from a config entry."""
    coordinator: CbusCoordinator = hass.data[DOMAIN][entry.entry_id]
    seen: set[int] = set()
    entities = []
    for zone_name, z in AC_ZONES.items():
        group = z["cur_temp_group"]
        if group not in seen:
            seen.add(group)
            entities.append(CbusTempSensor(coordinator, group, f"{zone_name} Temperature"))
    async_add_entities(entities)


class CbusTempSensor(SensorEntity):
    """Representation of a Clipsal C-Bus temperature sensor."""

    _attr_has_entity_name = True
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(self, coordinator: CbusCoordinator, group: int, name: str) -> None:
        self._coordinator = coordinator
        self._group = group
        self._attr_name = name
        self._attr_unique_id = f"cbus_temp_{group}"
        self._attr_native_value = None

    @callback
    def _handle_update(self, level: int) -> None:
        self._attr_native_value = float(level)
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(async_dispatcher_connect(
            self.hass, f"{SIGNAL_STATE_UPDATED}_{APP_USER_PARAM}_{self._group}", self._handle_update
        ))
        if (v := self._coordinator.get_level(APP_USER_PARAM, self._group)) is not None:
            self._attr_native_value = float(v)
