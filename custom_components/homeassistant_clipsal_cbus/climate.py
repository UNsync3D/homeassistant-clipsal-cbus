"""Climate platform for Clipsal C-Bus air conditioning zones."""
from __future__ import annotations
from homeassistant.components.climate import (
    ClimateEntity, ClimateEntityFeature, HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import DOMAIN, APP_COOLMASTER, APP_USER_PARAM, AC_ZONES
from .coordinator import CbusCoordinator, SIGNAL_STATE_UPDATED


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up climate entities from a config entry."""
    coordinator: CbusCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        CbusClimate(coordinator, name, cfg)
        for name, cfg in AC_ZONES.items()
    )


class CbusClimate(ClimateEntity):
    """Representation of a Clipsal C-Bus air conditioning zone."""

    _attr_has_entity_name = True
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_hvac_modes = [
        HVACMode.OFF, HVACMode.COOL, HVACMode.HEAT,
        HVACMode.FAN_ONLY, HVACMode.DRY, HVACMode.AUTO,
    ]
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.FAN_MODE
        | ClimateEntityFeature.TURN_ON
        | ClimateEntityFeature.TURN_OFF
    )
    _attr_fan_modes = ["low", "medium", "high", "auto"]
    _attr_min_temp = 16
    _attr_max_temp = 30
    _attr_target_temperature_step = 1.0

    def __init__(self, coordinator: CbusCoordinator, zone_name: str, zone_cfg: dict) -> None:
        self._coordinator = coordinator
        self._zone = zone_cfg
        self._mode_map     = zone_cfg["mode_map"]
        self._fan_map      = zone_cfg["fan_map"]
        self._fan_map_inv  = {v: k for k, v in zone_cfg["fan_map"].items()}
        self._hvac_to_cbus = zone_cfg["hvac_to_cbus"]
        self._attr_name = f"{zone_name} AC"
        self._attr_unique_id = f"cbus_climate_{zone_name.lower().replace(' ', '_')}"
        self._power_on = False
        self._hvac_mode = HVACMode.OFF
        self._fan_mode = "auto"
        self._current_temp: float | None = None
        self._target_temp: float | None = None

    @property
    def hvac_mode(self) -> HVACMode:
        return self._hvac_mode if self._power_on else HVACMode.OFF

    @property
    def fan_mode(self) -> str:
        return self._fan_mode

    @property
    def current_temperature(self) -> float | None:
        return self._current_temp

    @property
    def target_temperature(self) -> float | None:
        return self._target_temp

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set the HVAC mode."""
        if hvac_mode == HVACMode.OFF:
            await self._coordinator.async_write(APP_COOLMASTER, self._zone["power"], 0)
        else:
            mode_val = self._hvac_to_cbus.get(hvac_mode.value, 20)
            await self._coordinator.async_write(APP_COOLMASTER, self._zone["power"], 255)
            await self._coordinator.async_write(APP_COOLMASTER, self._zone["mode"], mode_val)

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """Set the fan mode."""
        fan_val = self._fan_map_inv.get(fan_mode, 20)
        await self._coordinator.async_write(APP_COOLMASTER, self._zone["fan"], fan_val)

    async def async_set_temperature(self, **kwargs) -> None:
        """Set the target temperature by pulsing temp up/down commands."""
        target = kwargs.get("temperature")
        if target is None or self._target_temp is None:
            return
        delta = round(target - self._target_temp)
        if delta == 0:
            return
        group = self._zone["temp_up"] if delta > 0 else self._zone["temp_down"]
        for _ in range(abs(delta)):
            await self._coordinator.async_write(APP_COOLMASTER, group, 1)

    @callback
    def _handle_power_update(self, level: int) -> None:
        self._power_on = level > 0
        if not self._power_on:
            self._hvac_mode = HVACMode.OFF
        self.async_write_ha_state()

    @callback
    def _handle_mode_update(self, level: int) -> None:
        mode_str = self._mode_map.get(level, "cool")
        self._hvac_mode = {
            "off": HVACMode.OFF, "cool": HVACMode.COOL, "heat": HVACMode.HEAT,
            "fan_only": HVACMode.FAN_ONLY, "dry": HVACMode.DRY, "auto": HVACMode.AUTO,
        }.get(mode_str, HVACMode.COOL)
        self.async_write_ha_state()

    @callback
    def _handle_fan_update(self, level: int) -> None:
        self._fan_mode = self._fan_map.get(level, "auto")
        self.async_write_ha_state()

    @callback
    def _handle_temp_update(self, level: int) -> None:
        self._current_temp = float(level)
        self.async_write_ha_state()

    @callback
    def _handle_set_temp_update(self, level: int) -> None:
        self._target_temp = float(level)
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Subscribe to state updates when entity is added."""
        z = self._zone
        self.async_on_remove(async_dispatcher_connect(self.hass,
            f"{SIGNAL_STATE_UPDATED}_{APP_COOLMASTER}_{z['power']}", self._handle_power_update))
        self.async_on_remove(async_dispatcher_connect(self.hass,
            f"{SIGNAL_STATE_UPDATED}_{APP_COOLMASTER}_{z['mode']}", self._handle_mode_update))
        self.async_on_remove(async_dispatcher_connect(self.hass,
            f"{SIGNAL_STATE_UPDATED}_{APP_COOLMASTER}_{z['fan']}", self._handle_fan_update))
        self.async_on_remove(async_dispatcher_connect(self.hass,
            f"{SIGNAL_STATE_UPDATED}_{APP_USER_PARAM}_{z['cur_temp_group']}", self._handle_temp_update))
        self.async_on_remove(async_dispatcher_connect(self.hass,
            f"{SIGNAL_STATE_UPDATED}_{APP_USER_PARAM}_{z['set_temp_group']}", self._handle_set_temp_update))

        if (v := self._coordinator.get_level(APP_COOLMASTER, z["power"])) is not None:
            self._power_on = v > 0
        if (v := self._coordinator.get_level(APP_COOLMASTER, z["mode"])) is not None:
            self._handle_mode_update(v)
        if (v := self._coordinator.get_level(APP_COOLMASTER, z["fan"])) is not None:
            self._handle_fan_update(v)
        if (v := self._coordinator.get_level(APP_USER_PARAM, z["cur_temp_group"])) is not None:
            self._current_temp = float(v)
        if (v := self._coordinator.get_level(APP_USER_PARAM, z["set_temp_group"])) is not None:
            self._target_temp = float(v)
