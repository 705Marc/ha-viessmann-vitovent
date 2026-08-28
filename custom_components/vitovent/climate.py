"""Climate control for Vitovent."""

from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import VitoventCoordinator
from .entity import VitoventEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Vitovent climate control."""
    async_add_entities([VitoventClimate(entry.runtime_data)])


class VitoventClimate(VitoventEntity, ClimateEntity):
    """Vitovent temperature control."""

    _attr_name = "Klimasteuerung"
    _attr_hvac_mode = HVACMode.HEAT_COOL
    _attr_hvac_modes = [HVACMode.HEAT_COOL]
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_min_temp = 10
    _attr_max_temp = 30
    _attr_target_temperature_step = 0.5
    _register_addresses = frozenset({1024, 6004})

    def __init__(self, coordinator: VitoventCoordinator) -> None:
        """Initialize climate control."""
        super().__init__(coordinator, "lueftung_klimasteuerung")

    @property
    def current_temperature(self) -> float:
        """Return the room temperature."""
        return self.coordinator.data[1024] / 10

    @property
    def target_temperature(self) -> float:
        """Return the configured target temperature."""
        return self.coordinator.data[6004] / 10

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set the target temperature."""
        await self.coordinator.unit.write_register(
            6004, round(kwargs[ATTR_TEMPERATURE] * 10)
        )
        await self.coordinator.async_request_refresh()
