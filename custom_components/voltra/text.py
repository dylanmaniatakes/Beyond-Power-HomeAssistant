from __future__ import annotations

from homeassistant.components.text import TextEntity, TextMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DEFAULT_NAME, DOMAIN
from .coordinator import VoltraCoordinator
from .entity import VoltraEntity

DEVICE_NAME_PATTERN = r"^[A-Za-z][\x20-\x39\x3B-\x5B\x5D-\x7E]{0,19}$"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: VoltraCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([VoltraDeviceNameText(coordinator)])


class VoltraDeviceNameText(VoltraEntity, TextEntity):
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:rename"
    _attr_mode = TextMode.TEXT
    _attr_name = "Device name"
    _attr_native_max = 20
    _attr_native_min = 1
    _attr_pattern = DEVICE_NAME_PATTERN

    def __init__(self, coordinator: VoltraCoordinator) -> None:
        super().__init__(coordinator, "device_name")

    @property
    def native_value(self) -> str:
        state = self.coordinator.data
        return state.device_name or state.configured_name or DEFAULT_NAME

    @property
    def available(self) -> bool:
        return super().available and self.coordinator.data.connected

    async def async_set_value(self, value: str) -> None:
        trimmed = value.strip()
        await self.coordinator.client.async_set_device_name(trimmed)
        self.hass.config_entries.async_update_entry(
            self.coordinator.entry,
            title=trimmed,
            data={**self.coordinator.entry.data, CONF_NAME: trimmed},
        )
