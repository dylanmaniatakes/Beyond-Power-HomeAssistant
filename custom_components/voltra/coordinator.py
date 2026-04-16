from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .client import VoltraBleClient
from .models import VoltraState

_LOGGER = logging.getLogger(__name__)


class VoltraCoordinator(DataUpdateCoordinator[VoltraState]):
    def __init__(self, hass, entry: ConfigEntry) -> None:
        initial_state = VoltraState(
            address=entry.data["address"],
            configured_name=entry.data.get("name") or entry.title,
            device_name=entry.data.get("name") or entry.title,
        )
        super().__init__(hass, logger=_LOGGER, name=f"voltra_{entry.entry_id}")
        self.data = initial_state
        self.entry = entry
        self.client = VoltraBleClient(
            hass=hass,
            address=initial_state.address,
            configured_name=initial_state.configured_name,
            update_callback=self.async_set_updated_data,
        )

    async def async_start(self) -> None:
        await self.client.async_start()

    async def async_stop(self) -> None:
        await self.client.async_stop()
