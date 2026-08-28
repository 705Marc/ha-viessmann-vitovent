"""Selects for Vitovent maintenance actions."""

from dataclasses import dataclass

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import VitoventCoordinator
from .entity import VitoventEntity

# Zuordnung der Optionen für das Betriebsmodus-Select
OPTIONS_MAP = {
    "Abschaltbetrieb": 0,
    "Stufe 1": 1,
    "Stufe 2": 2,
    "Stufe 3": 3,
    "Stufe 4": 4,
}


@dataclass(frozen=True, kw_only=True)
class _SelectDescription(SelectEntityDescription):
    """Description of a writable Vitovent register."""

    read_address: int
    write_address: int
    options_icons: dict[str, str] | None = None  # Neu: Mapping für Optionen -> Icons


def SelectDescription(
    name: str,
    unique_id: str,
    read_address: int,
    write_address: int,
    options_icons: dict[str, str] | None = None,  # Neu
) -> _SelectDescription:
    """Create a writable Vitovent register description."""
    return _SelectDescription(
        key=unique_id,
        name=name,
        read_address=read_address,
        write_address=write_address,
        options=list(OPTIONS_MAP.keys()),
        options_icons=options_icons,  # Neu
    )


SELECTS = (
    SelectDescription(
        name="Betriebsmodus",
        unique_id="betriebsmodus",
        read_address=1009,
        write_address=2002,
        options_icons={
            "Abschaltbetrieb": "mdi:fan-off",
            "Stufe 1": "mdi:fan-speed-1",
            "Stufe 2": "mdi:fan-speed-2",
            "Stufe 3": "mdi:fan-speed-3",
            "Stufe 4": "mdi:fan-plus",
        },
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Vitovent Selects."""
    async_add_entities(
        [VitoventSelect(entry.runtime_data, description) for description in SELECTS]
    )


class VitoventSelect(VitoventEntity, SelectEntity):
    """A maintenance Select backed by a holding register."""

    entity_description: _SelectDescription

    def __init__(
        self, coordinator: VitoventCoordinator, description: _SelectDescription
    ) -> None:
        """Initialize a maintenance Select."""
        super().__init__(coordinator, description.key)
        self.entity_description = description
        self._attr_name = description.name
        self._register_addresses = frozenset(
            {description.read_address, description.write_address}
        )

    @property
    def current_option(self) -> str | None:
        """Return the selected entity option based on the read register."""
        value = self.coordinator.data.get(self.entity_description.read_address)
        if value is None:
            return None

        for opt_text, opt_val in OPTIONS_MAP.items():
            if opt_val == value:
                return opt_text
        return None

    @property
    def icon(self) -> str | None:
        """Return the icon based on the current option."""
        if (
            self.entity_description.options_icons
            and (current := self.current_option)
            in self.entity_description.options_icons
        ):
            return self.entity_description.options_icons[current]
        return super().icon

    async def async_select_option(self, option: str) -> None:
        """Handle the selection of an option by writing to the write register."""
        if option not in OPTIONS_MAP:
            return

        command_value = OPTIONS_MAP[option]
        await self.coordinator.unit.write_register(
            self.entity_description.write_address, command_value
        )
        await self.coordinator.async_request_refresh()
