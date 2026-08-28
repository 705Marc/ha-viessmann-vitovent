"""Config flow for the Vitovent integration."""

import asyncio
import logging
from typing import Any

from modbus_connection import ModbusError, ModbusTcpParams
import voluptuous as vol

from homeassistant.components.modbus import async_get_temporary_unit
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv

from .const import CONF_SLAVE, DEFAULT_PORT, DEFAULT_SLAVE, DOMAIN

_LOGGER = logging.getLogger(__name__)

DEVICE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): cv.port,
        vol.Required(CONF_SLAVE, default=DEFAULT_SLAVE): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=247)
        ),
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect to the Vitovent gateway."""
    host = data[CONF_HOST]
    port = data[CONF_PORT]

    try:
        # Test TCP connection to the Modbus gateway / Vitovent interface
        async with async_get_temporary_unit(
            hass,
            ModbusTcpParams(host=host, port=port),
            data[CONF_SLAVE],
        ) as unit:
            await asyncio.wait_for(unit.read_holding_registers(1009, 1), timeout=5.0)
    except (TimeoutError, OSError, ModbusError) as err:
        raise CannotConnect from err

    return {"title": "Vitovent 300-C Modbus"}


class VitoventFlowHandler(ConfigFlow, domain=DOMAIN):
    """Config flow for Vitovent."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a flow initialized by the user."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id("Vitovent")
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=DEVICE_SCHEMA, errors=errors
        )


class CannotConnect(Exception):
    """Error to indicate we cannot connect."""
