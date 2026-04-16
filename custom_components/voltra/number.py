from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from homeassistant.components.number import NumberEntity, NumberEntityDescription, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import VoltraCoordinator
from .entity import VoltraControlEntity
from .models import VoltraState


def _is_strength_context(state: VoltraState) -> bool:
    return state.workout_state in (None, 0, 1)


def _is_strength(state: VoltraState) -> bool:
    return state.workout_state == 1


def _is_resistance_band(state: VoltraState) -> bool:
    return state.workout_state == 2


def _is_damper(state: VoltraState) -> bool:
    return state.workout_state == 4


def _is_isokinetic(state: VoltraState) -> bool:
    return state.workout_state == 7


def _cm_to_inches(value_cm: float | None) -> float | None:
    if value_cm is None:
        return None
    return float(round(value_cm / 2.54))


def _inches_to_cm(value_inches: float) -> float:
    return round(value_inches * 2.54)


def _mms_to_ms(value_mms: int | None) -> float | None:
    if value_mms is None:
        return None
    return round(value_mms / 1000, 2)


def _ms_to_mms(value_ms: float) -> float:
    return round(value_ms * 1000)


@dataclass(frozen=True, kw_only=True)
class VoltraNumberDescription(NumberEntityDescription):
    value_fn: Callable[[VoltraState], float | None]
    set_fn: Callable[[VoltraCoordinator, float], Awaitable[None]]
    available_fn: Callable[[VoltraState], bool] | None = None


DESCRIPTIONS: tuple[VoltraNumberDescription, ...] = (
    VoltraNumberDescription(
        key="target_load",
        name="Target load",
        icon="mdi:dumbbell",
        native_min_value=5,
        native_max_value=200,
        native_step=1,
        native_unit_of_measurement="lb",
        mode=NumberMode.SLIDER,
        value_fn=lambda state: state.weight_lb,
        set_fn=lambda coordinator, value: coordinator.client.async_set_target_load(value),
        available_fn=_is_strength_context,
    ),
    VoltraNumberDescription(
        key="chains_weight",
        name="Chains",
        icon="mdi:link-variant",
        native_min_value=0,
        native_max_value=200,
        native_step=1,
        native_unit_of_measurement="lb",
        mode=NumberMode.SLIDER,
        entity_category=EntityCategory.CONFIG,
        value_fn=lambda state: state.chains_weight_lb,
        set_fn=lambda coordinator, value: coordinator.client.async_set_chains_weight(value),
        available_fn=_is_strength,
    ),
    VoltraNumberDescription(
        key="eccentric_weight",
        name="Eccentric",
        icon="mdi:arrow-collapse-down",
        native_min_value=-200,
        native_max_value=200,
        native_step=1,
        native_unit_of_measurement="lb",
        mode=NumberMode.SLIDER,
        entity_category=EntityCategory.CONFIG,
        value_fn=lambda state: state.eccentric_weight_lb,
        set_fn=lambda coordinator, value: coordinator.client.async_set_eccentric_weight(value),
        available_fn=_is_strength,
    ),
    VoltraNumberDescription(
        key="resistance_band_force",
        name="Band force",
        icon="mdi:sine-wave",
        native_min_value=15,
        native_max_value=200,
        native_step=1,
        native_unit_of_measurement="lb",
        mode=NumberMode.SLIDER,
        value_fn=lambda state: state.resistance_band_max_force_lb,
        set_fn=lambda coordinator, value: coordinator.client.async_set_resistance_band_force(value),
        available_fn=_is_resistance_band,
    ),
    VoltraNumberDescription(
        key="resistance_band_length",
        name="Band length",
        icon="mdi:ruler",
        native_min_value=20,
        native_max_value=102,
        native_step=1,
        native_unit_of_measurement="in",
        mode=NumberMode.SLIDER,
        entity_category=EntityCategory.CONFIG,
        value_fn=lambda state: _cm_to_inches(state.resistance_band_length_cm),
        set_fn=lambda coordinator, value: coordinator.client.async_set_resistance_band_length(_inches_to_cm(value)),
        available_fn=lambda state: _is_resistance_band(state) and not bool(state.resistance_band_by_range_of_motion),
    ),
    VoltraNumberDescription(
        key="damper_level",
        name="Damper level",
        icon="mdi:fan",
        native_min_value=1,
        native_max_value=10,
        native_step=1,
        mode=NumberMode.SLIDER,
        value_fn=lambda state: float(state.damper_level_index + 1) if state.damper_level_index is not None else None,
        set_fn=lambda coordinator, value: coordinator.client.async_set_damper_level(value - 1),
        available_fn=_is_damper,
    ),
    VoltraNumberDescription(
        key="isokinetic_target_speed",
        name="Target speed",
        icon="mdi:speedometer",
        native_min_value=0.10,
        native_max_value=2.0,
        native_step=0.05,
        native_unit_of_measurement="m/s",
        mode=NumberMode.SLIDER,
        value_fn=lambda state: _mms_to_ms(state.isokinetic_target_speed_mms),
        set_fn=lambda coordinator, value: coordinator.client.async_set_isokinetic_target_speed(_ms_to_mms(value)),
        available_fn=_is_isokinetic,
    ),
    VoltraNumberDescription(
        key="isokinetic_speed_limit",
        name="Speed limit",
        icon="mdi:ray-end-arrow",
        native_min_value=0,
        native_max_value=2.0,
        native_step=0.05,
        native_unit_of_measurement="m/s",
        mode=NumberMode.SLIDER,
        entity_category=EntityCategory.CONFIG,
        value_fn=lambda state: _mms_to_ms(state.isokinetic_speed_limit_mms),
        set_fn=lambda coordinator, value: coordinator.client.async_set_isokinetic_speed_limit(_ms_to_mms(value)),
        available_fn=lambda state: _is_isokinetic(state) and state.isokinetic_mode != 1,
    ),
    VoltraNumberDescription(
        key="isokinetic_constant_resistance",
        name="Constant resistance",
        icon="mdi:weight-pound",
        native_min_value=5,
        native_max_value=100,
        native_step=1,
        native_unit_of_measurement="lb",
        mode=NumberMode.SLIDER,
        entity_category=EntityCategory.CONFIG,
        value_fn=lambda state: state.isokinetic_constant_resistance_lb,
        set_fn=lambda coordinator, value: coordinator.client.async_set_isokinetic_constant_resistance(value),
        available_fn=lambda state: _is_isokinetic(state) and state.isokinetic_mode == 1,
    ),
    VoltraNumberDescription(
        key="isokinetic_max_eccentric_load",
        name="Max eccentric load",
        icon="mdi:weight-pound",
        native_min_value=5,
        native_max_value=200,
        native_step=1,
        native_unit_of_measurement="lb",
        mode=NumberMode.SLIDER,
        entity_category=EntityCategory.CONFIG,
        value_fn=lambda state: state.isokinetic_max_eccentric_load_lb,
        set_fn=lambda coordinator, value: coordinator.client.async_set_isokinetic_max_eccentric_load(value),
        available_fn=lambda state: _is_isokinetic(state) and state.isokinetic_mode != 1,
    ),
    VoltraNumberDescription(
        key="cable_offset",
        name="Cable offset",
        icon="mdi:camera-control",
        native_min_value=0,
        native_max_value=260,
        native_step=1,
        native_unit_of_measurement="cm",
        mode=NumberMode.BOX,
        entity_category=EntityCategory.CONFIG,
        value_fn=lambda state: state.cable_offset_cm,
        set_fn=lambda coordinator, value: coordinator.client.async_set_cable_offset(value),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: VoltraCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(VoltraNumber(coordinator, description) for description in DESCRIPTIONS)


class VoltraNumber(VoltraControlEntity, NumberEntity):
    entity_description: VoltraNumberDescription

    def __init__(self, coordinator: VoltraCoordinator, description: VoltraNumberDescription) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def available(self) -> bool:
        if not super().available:
            return False
        predicate = self.entity_description.available_fn
        return predicate(self.coordinator.data) if predicate is not None else True

    @property
    def native_value(self) -> float | None:
        return self.entity_description.value_fn(self.coordinator.data)

    async def async_set_native_value(self, value: float) -> None:
        await self.entity_description.set_fn(self.coordinator, value)
