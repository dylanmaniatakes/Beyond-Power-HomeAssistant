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
from .protocol import WORKOUT_STATE_DAMPER, WORKOUT_STATE_ISOKINETIC, WORKOUT_STATE_ISOMETRIC


@dataclass(frozen=True, kw_only=True)
class VoltraSensorDescription(SensorEntityDescription):
    value_fn: Callable[[VoltraState], str | int | float | None]
    available_fn: Callable[[VoltraState], bool] | None = None


def _is_power_workout(state: VoltraState) -> bool:
    return state.workout_state in (WORKOUT_STATE_DAMPER, WORKOUT_STATE_ISOKINETIC)


def _isometric_metrics_type_label(metrics_type: int | None) -> str | None:
    if metrics_type is None:
        return None
    if metrics_type == 0:
        return "Force"
    if metrics_type == 1:
        return "Weight"
    return str(metrics_type)


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
        device_class=SensorDeviceClass.DISTANCE,
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
        key="rowing_distance",
        name="Row distance",
        device_class=SensorDeviceClass.DISTANCE,
        native_unit_of_measurement="m",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda state: state.rowing_distance_meters,
        available_fn=lambda state: state.workout_state == 3 or state.rowing_distance_meters is not None,
    ),
    VoltraSensorDescription(
        key="rowing_elapsed",
        name="Row elapsed",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement="s",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda state: round(state.rowing_elapsed_millis / 1000, 1) if state.rowing_elapsed_millis is not None else None,
        available_fn=lambda state: state.workout_state == 3 or state.rowing_elapsed_millis is not None,
    ),
    VoltraSensorDescription(
        key="rowing_pace_500",
        name="Row pace /500 m",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement="s",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda state: round(state.rowing_pace_500_millis / 1000, 1) if state.rowing_pace_500_millis is not None else None,
        available_fn=lambda state: state.workout_state == 3 or state.rowing_pace_500_millis is not None,
    ),
    VoltraSensorDescription(
        key="rowing_average_pace_500",
        name="Row average pace /500 m",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement="s",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda state: round(state.rowing_average_pace_500_millis / 1000, 1) if state.rowing_average_pace_500_millis is not None else None,
        available_fn=lambda state: state.workout_state == 3 or state.rowing_average_pace_500_millis is not None,
    ),
    VoltraSensorDescription(
        key="rowing_stroke_rate",
        name="Row stroke rate",
        icon="mdi:counter",
        native_unit_of_measurement="spm",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda state: state.rowing_stroke_rate_spm,
        available_fn=lambda state: state.workout_state == 3 or state.rowing_stroke_rate_spm is not None,
    ),
    VoltraSensorDescription(
        key="rowing_drive_force",
        name="Row drive force",
        icon="mdi:weight-pound",
        native_unit_of_measurement="lb",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda state: state.rowing_drive_force_lb,
        available_fn=lambda state: state.workout_state == 3 or state.rowing_drive_force_lb is not None,
    ),
    VoltraSensorDescription(
        key="workout_live_force",
        name="Workout live force",
        icon="mdi:weight-pound",
        native_unit_of_measurement="lb",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda state: state.workout_live_force_lb,
    ),
    VoltraSensorDescription(
        key="workout_peak_force",
        name="Workout peak force",
        icon="mdi:chart-line",
        native_unit_of_measurement="lb",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda state: state.workout_peak_force_lb,
    ),
    VoltraSensorDescription(
        key="workout_peak_power",
        name="Workout peak power",
        icon="mdi:flash",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement="W",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda state: state.workout_peak_power_watts,
    ),
    VoltraSensorDescription(
        key="workout_time_to_peak",
        name="Workout time to peak",
        icon="mdi:timer-outline",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement="s",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda state: round(state.workout_time_to_peak_millis / 1000, 2) if state.workout_time_to_peak_millis is not None else None,
    ),
    VoltraSensorDescription(
        key="isometric_current_force",
        name="Isometric current force",
        icon="mdi:weight-pound",
        native_unit_of_measurement="N",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda state: state.isometric_display_current_force_n,
        available_fn=lambda state: state.workout_state == 8 or state.isometric_display_current_force_n is not None,
    ),
    VoltraSensorDescription(
        key="isometric_peak_force",
        name="Isometric peak force",
        icon="mdi:chart-line",
        native_unit_of_measurement="N",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda state: state.isometric_display_peak_force_n,
        available_fn=lambda state: state.workout_state == 8 or state.isometric_display_peak_force_n is not None,
    ),
    VoltraSensorDescription(
        key="isometric_rfd_0_100_ms",
        name="Isometric RFD 0-100 ms",
        icon="mdi:chart-timeline-variant",
        native_unit_of_measurement="N/s",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda state: state.isometric_rfd_100_n_per_s,
        available_fn=lambda state: state.workout_state == 8 or state.isometric_rfd_100_n_per_s is not None,
    ),
    VoltraSensorDescription(
        key="isometric_time_to_peak",
        name="Isometric time to peak",
        icon="mdi:timer-outline",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement="s",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda state: round(state.isometric_time_to_peak_millis / 1000, 2) if state.isometric_time_to_peak_millis is not None else None,
        available_fn=lambda state: state.workout_state == 8 or state.isometric_time_to_peak_millis is not None,
    ),
    VoltraSensorDescription(
        key="isometric_impulse_0_100_ms",
        name="Isometric impulse 0-100 ms",
        icon="mdi:pulse",
        native_unit_of_measurement="N*s",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda state: state.isometric_impulse_100_n_seconds,
        available_fn=lambda state: state.workout_state == 8 or state.isometric_impulse_100_n_seconds is not None,
    ),
    VoltraSensorDescription(
        key="isometric_peak_relative_force",
        name="Isometric peak relative force",
        icon="mdi:percent",
        native_unit_of_measurement="%",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda state: state.isometric_display_peak_relative_force_percent,
        available_fn=lambda state: state.workout_state == 8 or state.isometric_display_peak_relative_force_percent is not None,
    ),
    VoltraSensorDescription(
        key="isometric_elapsed",
        name="Isometric elapsed",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement="s",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda state: round(state.isometric_display_elapsed_millis / 1000, 1) if state.isometric_display_elapsed_millis is not None else None,
        available_fn=lambda state: state.workout_state == 8 or state.isometric_display_elapsed_millis is not None,
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
        key="isometric_metrics_type",
        name="Isometric metrics type",
        icon="mdi:label-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda state: _isometric_metrics_type_label(state.isometric_metrics_type),
        available_fn=lambda state: state.workout_state == WORKOUT_STATE_ISOMETRIC or state.isometric_metrics_type is not None,
    ),
    VoltraSensorDescription(
        key="isometric_body_weight",
        name="Isometric body weight",
        icon="mdi:scale-bathroom",
        native_unit_of_measurement="lb",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda state: state.isometric_body_weight_lb,
        available_fn=lambda state: state.workout_state == WORKOUT_STATE_ISOMETRIC or state.isometric_body_weight_lb is not None,
    ),
    VoltraSensorDescription(
        key="isometric_waveform_samples",
        name="Isometric waveform samples",
        icon="mdi:chart-timeline-variant",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda state: len(state.isometric_waveform_samples_n),
        available_fn=lambda state: state.workout_state == 8 or bool(state.isometric_waveform_samples_n),
    ),
    VoltraSensorDescription(
        key="isometric_carrier_force",
        name="Isometric carrier force",
        icon="mdi:pulse",
        native_unit_of_measurement="N",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda state: state.isometric_carrier_force_n,
        available_fn=lambda state: state.workout_state == 8 or state.isometric_carrier_force_n is not None,
    ),
    VoltraSensorDescription(
        key="isometric_carrier_status_primary",
        name="Isometric carrier status primary",
        icon="mdi:numeric",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda state: state.isometric_carrier_status_primary,
        available_fn=lambda state: state.workout_state == 8 or state.isometric_carrier_status_primary is not None,
    ),
    VoltraSensorDescription(
        key="isometric_carrier_status_secondary",
        name="Isometric carrier status secondary",
        icon="mdi:numeric",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda state: state.isometric_carrier_status_secondary,
        available_fn=lambda state: state.workout_state == 8 or state.isometric_carrier_status_secondary is not None,
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
                "row_target_meters": state.rowing_target_meters,
                "app_current_screen_id": state.app_current_screen_id,
                "fitness_ongoing_ui": state.fitness_ongoing_ui,
            }
            if state.last_error is not None:
                attributes["last_error"] = state.last_error
            if state.device_name is not None:
                attributes["device_name"] = state.device_name
            if state.safety_reasons:
                attributes["safety_reasons"] = list(state.safety_reasons)
            return attributes
        if self.entity_description.key == "isometric_waveform_samples":
            return {
                "last_chunk_index": state.isometric_waveform_last_chunk_index,
                "average_step_millis": state.isometric_waveform_average_step_millis,
                "graph_max_force_n": state.isometric_graph_max_force_n,
            }
        if self.entity_description.key == "isometric_body_weight":
            return {
                "body_weight_n": state.isometric_body_weight_n,
                "body_weight_100g": state.isometric_body_weight_100g,
                "metrics_type": _isometric_metrics_type_label(state.isometric_metrics_type),
            }
        return None
