"""Sensors for Vitovent."""

from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import VitoventCoordinator
from .entity import VitoventEntity


@dataclass(frozen=True, kw_only=True)
class _SensorDescription(SensorEntityDescription):
    """Description of a Vitovent register sensor."""

    address: int
    scale: float = 1
    entity_registry_enabled_default: bool = True
    entity_category: EntityCategory | None = None
    icon: str | None = None


def SensorDescription(
    name: str,
    unique_id: str,
    address: int,
    unit: str | None = None,
    scale: float = 1,
    device_class: SensorDeviceClass | None = None,
    entity_registry_enabled_default: bool = True,
    entity_category: EntityCategory | None = None,
    icon: str | None = None,
) -> _SensorDescription:
    """Create a Vitovent register sensor description."""
    return _SensorDescription(
        key=unique_id,
        name=name,
        native_unit_of_measurement=unit,
        device_class=device_class,
        address=address,
        scale=scale,
        entity_registry_enabled_default=entity_registry_enabled_default,
        entity_category=entity_category,
        icon=icon,
    )


SENSORS = (
    SensorDescription(
        "Aktuelle Lüfterstufe",
        "lueftung_aktuelle_luefterstufe",
        1009,
        "Stufe",
        icon="mdi:fan",
    ),
    SensorDescription(
        "Volumenstrom Eingang",
        "lueftung_volumenstrom_eingang",
        1010,
        "m³/h",
        icon="mdi:weather-windy",
    ),
    SensorDescription(
        "Ventilatordrehzahl Eingang",
        "lueftung_register_1011",
        1011,
        "u/min",
        icon="mdi:refresh",
    ),
    SensorDescription(
        "Volumenstrom Ausgang",
        "lueftung_volumenstrom_ausgang",
        1013,
        "m³/h",
        icon="mdi:weather-windy",
    ),
    SensorDescription(
        "Ventilatordrehzahl Ausgang",
        "lueftung_register_1014",
        1014,
        "u/min",
        icon="mdi:refresh",
    ),
    SensorDescription(
        "Außentemperatur",
        "lueftung_aussentemperatur",
        1021,
        UnitOfTemperature.CELSIUS,
        0.1,
        SensorDeviceClass.TEMPERATURE,
    ),
    SensorDescription(
        "Raumtemperatur",
        "lueftung_raumtemperatur",
        1024,
        UnitOfTemperature.CELSIUS,
        0.1,
        SensorDeviceClass.TEMPERATURE,
    ),
    SensorDescription(
        "Tage bis Filterwechsel",
        "lueftung_tage_bis_filterwechsel",
        1040,
        "Tage",
        icon="mdi:air-filter",
    ),
    SensorDescription(
        "Elektrisches Vorheizregister",
        "lueftung_elektrisches_vorheizregister",
        1046,
        "%",
        icon="mdi:heat-wave",
    ),
    SensorDescription(
        "Filterwechsel durchgeführt",
        "lueftung_filterwechsel_durchgefuehrt_sensor",
        2003,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:air-filter",
    ),
    SensorDescription(
        "UNIX Timestamp HIGH-Word",
        "lueftung_unix_timestamp_high_word",
        8000,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorDescription(
        "Unix Timestamp Low-Word",
        "lueftung_unix_timestamp_low_word",
        8001,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorDescription(
        "Uhrzeit einstellen High-Word",
        "lueftung_uhrzeit_einstellen_high_word",
        8002,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorDescription(
        "Uhrzeit einstellen Low-Word",
        "lueftung_uhrzeit_einstellen_low_word",
        8003,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorDescription(
        "Filterwechsel quittieren",
        "lueftung_filterwechsel_quittieren_sensor",
        8004,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:air-filter",
    ),
)

UNKNOWN_SENSORS = tuple(
    SensorDescription(
        f"Register {address}",
        f"lueftung_register_{address}",
        address,
        entity_registry_enabled_default=False,
        entity_category=EntityCategory.DIAGNOSTIC,
    )
    for address in (
        1000,
        1001,
        1002,
        1005,
        1006,
        1007,
        1016,
        1017,
        1045,
        2000,
        2001,
        6501,
        6502,
        6503,
        6504,
        6505,
        6506,
        6507,
        6508,
        8005,
    )
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Vitovent sensors."""

    sensors = [
        VitoventSensor(entry.runtime_data, description)
        for description in (*SENSORS, *UNKNOWN_SENSORS)
    ]

    async_add_entities(sensors)


class VitoventSensor(VitoventEntity, SensorEntity):
    """A sensor backed by a Vitovent holding register."""

    entity_description: _SensorDescription

    def __init__(
        self, coordinator: VitoventCoordinator, description: _SensorDescription
    ) -> None:
        """Initialize a register sensor."""
        super().__init__(coordinator, description.key)
        self.entity_description = description
        self._attr_name = description.name
        self._attr_native_unit_of_measurement = description.native_unit_of_measurement
        self._attr_device_class = description.device_class
        self._attr_entity_registry_enabled_default = (
            description.entity_registry_enabled_default
        )
        self._register_addresses = frozenset({description.address})

    @property
    def native_value(self) -> int | float:
        """Return the scaled register value."""
        value = self.coordinator.data[self.entity_description.address]
        return value * self.entity_description.scale
