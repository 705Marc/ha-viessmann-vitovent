"""Buttons for Vitovent maintenance actions."""

from dataclasses import dataclass

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import VitoventCoordinator
from .entity import VitoventEntity


@dataclass(frozen=True, kw_only=True)
class _ButtonDescription(ButtonEntityDescription):
    """Description of a writable Vitovent register."""

    address: int
    command_value: int


def ButtonDescription(
    name: str, unique_id: str, address: int, command_value: int
) -> _ButtonDescription:
    """Create a writable Vitovent register description."""
    return _ButtonDescription(
        key=unique_id, name=name, address=address, command_value=command_value
    )


BUTTONS = (
    ButtonDescription(
        "Filterwechsel Durchgeführt",
        "lueftung_filterwechsel_durchgefuehrt_button",
        2003,
        2,
    ),
    ButtonDescription(
        "Filterwechsel Quittieren",
        "lueftung_filterwechsel_quittieren_button",
        8004,
        57343,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Vitovent buttons."""
    async_add_entities(
        [VitoventButton(entry.runtime_data, description) for description in BUTTONS]
    )


class VitoventButton(VitoventEntity, ButtonEntity):
    """A maintenance button backed by a holding register."""

    def __init__(
        self, coordinator: VitoventCoordinator, description: _ButtonDescription
    ) -> None:
        """Initialize a maintenance button."""
        super().__init__(coordinator, description.key)
        self.entity_description = description
        self._attr_name = description.name
        self._register_addresses = frozenset({description.address})

    async def async_press(self) -> None:
        """Handle the button press."""
        await self.coordinator.unit.write_register(
            self.entity_description.address, self.entity_description.command_value
        )
        await self.coordinator.async_request_refresh()
