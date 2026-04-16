from __future__ import annotations

from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DEFAULT_NAME, DOMAIN
from .coordinator import VoltraCoordinator


class VoltraEntity(CoordinatorEntity[VoltraCoordinator]):
    _attr_has_entity_name = True

    def __init__(self, coordinator: VoltraCoordinator, key: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.data.address}_{key}".lower()

    @property
    def device_info(self) -> DeviceInfo:
        state = self.coordinator.data
        return DeviceInfo(
            identifiers={(DOMAIN, state.address)},
            connections={(CONNECTION_BLUETOOTH, state.address)},
            manufacturer="Beyond Power",
            model="Voltra",
            name=state.display_name or DEFAULT_NAME,
        )

    @property
    def available(self) -> bool:
        return self.coordinator.data.available


class VoltraControlEntity(VoltraEntity):
    @property
    def available(self) -> bool:
        state = self.coordinator.data
        return state.available and state.protocol_validated and bool(state.ready)
