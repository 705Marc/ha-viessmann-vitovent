"""Shared Vitovent entity helpers."""

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import VitoventCoordinator


class VitoventEntity(CoordinatorEntity[VitoventCoordinator]):
    """Base entity for Vitovent devices."""

    _attr_has_entity_name = True
    _register_addresses: frozenset[int] = frozenset()

    def __init__(self, coordinator: VitoventCoordinator, unique_id: str) -> None:
        """Initialize a Vitovent entity."""
        super().__init__(coordinator)
        self._attr_unique_id = unique_id

    @property
    def device_info(self) -> DeviceInfo:
        """Return the Vitovent device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.config_entry.entry_id)},
            manufacturer="Viessmann",
            model="Vitovent",
        )

    @property
    def available(self) -> bool:
        """Return whether all registers used by the entity are available."""
        return (
            super().available
            and self._register_addresses <= self.coordinator.data.keys()
        )
