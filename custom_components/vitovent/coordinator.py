"""Data coordinator for Vitovent Modbus devices."""

import asyncio
from datetime import datetime, timedelta
import logging

from modbus_connection import ModbusError, ModbusTcpParams

from homeassistant.components.modbus import async_get_unit
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)

REGISTER_ADDRESSES = frozenset(
    {
        1000,
        1001,
        1002,
        1005,
        1006,
        1007,
        1009,
        1010,
        1011,
        1013,
        1014,
        1016,
        1017,
        1021,
        1024,
        1040,
        1045,
        1046,
        2000,
        2001,
        2002,
        2003,
        6004,
        6501,
        6502,
        6503,
        6504,
        6505,
        6506,
        6507,
        6508,
        8004,
        8005,
    }
)
INITIAL_REGISTER_ADDRESSES = frozenset(
    {1009, 1010, 1011, 1013, 1014, 1040, 2002, 2003, 8004, 6004, 1024, 1046, 1021}
)
MAX_CACHE_AGE = timedelta(minutes=3)


class VitoventCoordinator(DataUpdateCoordinator[dict[int, int]]):
    """Poll the registers exposed by a Vitovent Modbus gateway."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, slave: int) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(seconds=SCAN_INTERVAL),
        )
        self.unit = async_get_unit(
            hass,
            entry,
            ModbusTcpParams(host=entry.data[CONF_HOST], port=entry.data[CONF_PORT]),
            slave,
        )
        self._failed_addresses: set[int] = set()
        self._initial_refresh = True
        # Speichert Tupel aus (Wert, Zeitstempel) für jede Registeradresse
        self._cached_values: dict[int, tuple[int, datetime]] = {}

    async def _async_update_data(self) -> dict[int, int]:
        """Read all configured registers in parallel."""
        data: dict[int, int] = {}
        now = datetime.now()
        addresses = (
            INITIAL_REGISTER_ADDRESSES if self._initial_refresh else REGISTER_ADDRESSES
        )
        self._initial_refresh = False

        async def fetch_register(address: int):
            try:
                value = (await self.unit.read_holding_registers(address, 1))[0]
                return address, value, None
            except ModbusError as err:
                return address, None, err

        # Alle Register parallel via asyncio.gather abfragen
        results = await asyncio.gather(*(fetch_register(addr) for addr in addresses))

        for address, value, err in results:
            if err is not None:
                if address not in self._failed_addresses:
                    _LOGGER.warning(
                        "Unable to read Vitovent register %s: %s", address, err
                    )
                self._failed_addresses.add(address)

                # Prüfen, ob ein gültiger Cache-Wert innerhalb des 3-Minuten-Fensters existiert
                if address in self._cached_values:
                    cached_value, cached_time = self._cached_values[address]
                    if now - cached_time <= MAX_CACHE_AGE:
                        data[address] = cached_value
                        _LOGGER.debug(
                            "Using cached value %s for register %s (age: %s)",
                            cached_value,
                            address,
                            now - cached_time,
                        )
            else:
                self._failed_addresses.discard(address)
                data[address] = value
                self._cached_values[address] = (value, now)

        if not data:
            raise UpdateFailed("Unable to read any Vitovent registers")
        return data
