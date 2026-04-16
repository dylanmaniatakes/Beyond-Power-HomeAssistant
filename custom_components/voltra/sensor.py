from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
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
class VoltraSensorDescription(SensorEntityDescription):
    value_fn: Callable[[VoltraState], str | int | float | None]
    available_fn: Callable[[VoltraState], bool] | None = None


DESCRIPTIONS: tuple[VoltraSensorDescription, ...] = (
    VoltraSensorDescription(
        key="status",
        name="Status",
        icon="mdi:information-outline",
        value_fn=lambda state: state.status_message,
    ),
    VoltraSensorDescription(
        key="battery",
        name="Battery",
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="%",
        value_fn=lambda state: state.battery_percent,
    ),
    VoltraSensorDescription(
        key="force",
        name="Current force",
        icon="mdi:weight-pound",
        native_unit_of_measurement="lb",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda state: state.force_lb,
    ),
    VoltraSensorDescription(
        key="cable_length",
        name="Cable length",
        icon="mdi:ruler",
        native_unit_of_measurement="cm",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda state: state.cable_length_cm,
    ),
    VoltraSensorDescription(
        key="rep_count",
        name="Rep count",
        icon="mdi:counter",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda state: state.rep_count,
    ),
    VoltraSensorDescription(
        key="set_count",
        name="Set count",
        icon="mdi:counter",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda state: state.set_count,
    ),
    VoltraSensorDescription(
        key="rep_phase",
        name="Rep phase",
        icon="mdi:waveform",
        value_fn=lambda state: state.rep_phase,
    ),
    VoltraSensorDescription(
        key="isometric_current_force",
        name="Isometric current force",
        icon="mdi:weight-pound",
        native_unit_of_measurement="N",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda state: state.isometric_current_force_n,
        available_fn=lambda state: state.workout_state == 8 or state.isometric_current_force_n is not None,
    ),
    VoltraSensorDescription(
        key="isometric_peak_force",
        name="Isometric peak force",
        icon="mdi:chart-line",
        native_unit_of_measurement="N",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda state: state.isometric_peak_force_n,
        available_fn=lambda state: state.workout_state == 8 or state.isometric_peak_force_n is not None,
    ),
    VoltraSensorDescription(
        key="isometric_elapsed",
        name="Isometric elapsed",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement="s",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda state: round(state.isometric_elapsed_millis / 1000, 1) if state.isometric_elapsed_millis is not None else None,
        available_fn=lambda state: state.workout_state == 8 or state.isometric_elapsed_millis is not None,
    ),
    VoltraSensorDescription(
        key="isometric_max_force",
        name="Isometric max force",
        icon="mdi:weight-pound",
        native_unit_of_measurement="lb",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda state: state.isometric_max_force_lb,
        available_fn=lambda state: state.workout_state == 8 or state.isometric_max_force_lb is not None,
    ),
    VoltraSensorDescription(
        key="isometric_max_duration",
        name="Isometric max duration",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement="s",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda state: state.isometric_max_duration_seconds,
        available_fn=lambda state: state.workout_state == 8 or state.isometric_max_duration_seconds is not None,
    ),
    VoltraSensorDescription(
        key="serial_number",
        name="Serial number",
        icon="mdi:identifier",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda state: state.serial_number,
    ),
    VoltraSensorDescription(
        key="firmware_version",
        name="Firmware version",
        icon="mdi:chip",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda state: state.firmware_version,
    ),
    VoltraSensorDescription(
        key="activation_state",
        name="Activation state",
        icon="mdi:shield-check",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda state: state.activation_state,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: VoltraCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(VoltraSensor(coordinator, description) for description in DESCRIPTIONS)


class VoltraSensor(VoltraEntity, SensorEntity):
    entity_description: VoltraSensorDescription

    def __init__(self, coordinator: VoltraCoordinator, description: VoltraSensorDescription) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def available(self) -> bool:
        if self.entity_description.key == "status":
            return True
        if not super().available:
            return False
        predicate = self.entity_description.available_fn
        return predicate(self.coordinator.data) if predicate is not None else True

    @property
    def native_value(self) -> str | int | float | None:
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, object] | None:
        state = self.coordinator.data
        if self.entity_description.key == "status":
            attributes: dict[str, object] = {
                "connected": state.connected,
                "control_ready": state.protocol_validated,
                "workout_mode": state.workout_mode,
                "loaded": state.load_engaged,
                "ready_to_load": state.can_load,
            }
            if state.last_error is not None:
                attributes["last_error"] = state.last_error
            return attributes
        return None
