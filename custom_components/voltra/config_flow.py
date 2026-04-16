from __future__ import annotations

import re

from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigFlow
from homeassistant.const import CONF_ADDRESS, CONF_NAME
import voluptuous as vol

from .const import DEFAULT_NAME, DOMAIN

ADDRESS_RE = re.compile(r"^(?:[0-9A-F]{2}:){5}[0-9A-F]{2}$")


class VoltraConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._address: str | None = None
        self._name: str | None = None

    async def async_step_user(self, user_input=None):
        errors: dict[str, str] = {}
        if user_input is not None:
            address = user_input[CONF_ADDRESS].upper()
            if not ADDRESS_RE.match(address):
                errors["base"] = "invalid_address"
            else:
                await self.async_set_unique_id(address)
                self._abort_if_unique_id_configured()
                name = user_input.get(CONF_NAME) or DEFAULT_NAME
                return self.async_create_entry(
                    title=name,
                    data={
                        CONF_ADDRESS: address,
                        CONF_NAME: name,
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ADDRESS, default=self._address or ""): str,
                    vol.Optional(CONF_NAME, default=self._name or DEFAULT_NAME): str,
                },
            ),
            errors=errors,
        )

    async def async_step_bluetooth(
        self,
        discovery_info: bluetooth.BluetoothServiceInfoBleak,
    ):
        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()
        self._address = discovery_info.address.upper()
        self._name = discovery_info.name or DEFAULT_NAME
        self.context["title_placeholders"] = {
            "name": self._name,
            "address": self._address,
        }
        return await self.async_step_confirm()

    async def async_step_confirm(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(
                title=self._name or DEFAULT_NAME,
                data={
                    CONF_ADDRESS: self._address,
                    CONF_NAME: self._name or DEFAULT_NAME,
                },
            )

        self._set_confirm_only()
        return self.async_show_form(
            step_id="confirm",
            description_placeholders={
                "name": self._name or DEFAULT_NAME,
                "address": self._address or "",
            },
        )
