"""The Vitovent integration."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import CONF_SLAVE
from .coordinator import VitoventCoordinator

_PLATFORMS: list[Platform] = [
    Platform.BUTTON,
    Platform.CLIMATE,
    Platform.SELECT,
    Platform.SENSOR,
]


type VitoventConfigEntry = ConfigEntry[VitoventCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: VitoventConfigEntry) -> bool:
    """Set up Vitovent from a config entry."""

    coordinator = VitoventCoordinator(hass, entry, entry.data[CONF_SLAVE])
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, _PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: VitoventConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, _PLATFORMS)
