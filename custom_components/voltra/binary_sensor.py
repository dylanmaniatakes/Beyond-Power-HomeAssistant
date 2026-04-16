from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import VoltraCoordinator
from .entity import VoltraEntity
from .models import VoltraState


@dataclass(frozen=True, kw_only=True)
class VoltraBinarySensorDescription(BinarySensorEntityDescription):
    value_fn: Callable[[VoltraState], bool | None]


DESCRIPTIONS: tuple[VoltraBinarySensorDescription, ...] = (
    VoltraBinarySensorDescription(
        key="can_load",
        name="Ready to load",
        icon="mdi:weight-lifter",
        value_fn=lambda state: state.can_load,
    ),
    VoltraBinarySensorDescription(
        key="loaded",
        name="Loaded",
        icon="mdi:weight-lifter",
        value_fn=lambda state: state.load_engaged,
    ),
    VoltraBinarySensorDescription(
        key="connected",
        name="Connected",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda state: state.connected,
    ),
    VoltraBinarySensorDescription(
        key="protocol_validated",
        name="Control ready",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda state: state.ready if state.ready is not None else state.protocol_validated,
    ),
    VoltraBinarySensorDescription(
        key="low_battery",
        name="Low battery",
        device_class=BinarySensorDeviceClass.BATTERY,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda state: state.low_battery,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: VoltraCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(VoltraBinarySensor(coordinator, description) for description in DESCRIPTIONS)


class VoltraBinarySensor(VoltraEntity, BinarySensorEntity):
    entity_description: VoltraBinarySensorDescription

    def __init__(self, coordinator: VoltraCoordinator, description: VoltraBinarySensorDescription) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def available(self) -> bool:
        if self.entity_description.key in {"can_load", "loaded", "connected", "protocol_validated"}:
            return True
        return super().available

    @property
    def is_on(self) -> bool | None:
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, object] | None:
        state = self.coordinator.data
        if self.entity_description.key == "can_load":
            return {
                "reasons": list(state.safety_reasons),
                "status": state.status_message,
            }
        return None
