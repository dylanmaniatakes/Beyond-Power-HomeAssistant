from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from homeassistant.components.cover import (
    ATTR_POSITION,
    CoverEntity,
    CoverEntityDescription,
    CoverEntityFeature,
)
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


def _value_to_position(value: float, minimum: float, maximum: float) -> int:
    if maximum <= minimum:
        return 0
    return round(((value - minimum) / (maximum - minimum)) * 100)


def _position_to_value(position: int, minimum: float, maximum: float) -> float:
    bounded = max(0, min(100, position))
    return minimum + ((maximum - minimum) * bounded / 100)


@dataclass(frozen=True, kw_only=True)
class VoltraCoverDescription(CoverEntityDescription):
    current_value_fn: Callable[[VoltraState], float | None]
    set_value_fn: Callable[[VoltraCoordinator, float], Awaitable[None]]
    min_value: float
    max_value: float
    unit: str
    available_fn: Callable[[VoltraState], bool] | None = None


DESCRIPTIONS: tuple[VoltraCoverDescription, ...] = (
    VoltraCoverDescription(
        key="target_load_cover",
        name="Weight position",
        icon="mdi:dumbbell",
        current_value_fn=lambda state: state.weight_lb,
        set_value_fn=lambda coordinator, value: coordinator.client.async_set_target_load(value),
        min_value=5,
        max_value=200,
        unit="lb",
        available_fn=_is_strength_context,
    ),
    VoltraCoverDescription(
        key="chains_cover",
        name="Chains position",
        icon="mdi:link-variant",
        entity_category=EntityCategory.CONFIG,
        current_value_fn=lambda state: state.chains_weight_lb,
        set_value_fn=lambda coordinator, value: coordinator.client.async_set_chains_weight(value),
        min_value=0,
        max_value=200,
        unit="lb",
        available_fn=_is_strength,
    ),
    VoltraCoverDescription(
        key="eccentric_cover",
        name="Eccentric position",
        icon="mdi:arrow-collapse-down",
        entity_category=EntityCategory.CONFIG,
        current_value_fn=lambda state: state.eccentric_weight_lb,
        set_value_fn=lambda coordinator, value: coordinator.client.async_set_eccentric_weight(value),
        min_value=-200,
        max_value=200,
        unit="lb",
        available_fn=_is_strength,
    ),
    VoltraCoverDescription(
        key="band_force_cover",
        name="Band force position",
        icon="mdi:sine-wave",
        current_value_fn=lambda state: state.resistance_band_max_force_lb,
        set_value_fn=lambda coordinator, value: coordinator.client.async_set_resistance_band_force(value),
        min_value=15,
        max_value=200,
        unit="lb",
        available_fn=_is_resistance_band,
    ),
    VoltraCoverDescription(
        key="band_length_cover",
        name="Band length position",
        icon="mdi:ruler",
        entity_category=EntityCategory.CONFIG,
        current_value_fn=lambda state: _cm_to_inches(state.resistance_band_length_cm),
        set_value_fn=lambda coordinator, value: coordinator.client.async_set_resistance_band_length(_inches_to_cm(value)),
        min_value=20,
        max_value=102,
        unit="in",
        available_fn=lambda state: _is_resistance_band(state) and not bool(state.resistance_band_by_range_of_motion),
    ),
    VoltraCoverDescription(
        key="damper_cover",
        name="Damper position",
        icon="mdi:fan",
        current_value_fn=lambda state: float(state.damper_level_index + 1) if state.damper_level_index is not None else None,
        set_value_fn=lambda coordinator, value: coordinator.client.async_set_damper_level(value - 1),
        min_value=1,
        max_value=10,
        unit="level",
        available_fn=_is_damper,
    ),
    VoltraCoverDescription(
        key="target_speed_cover",
        name="Target speed position",
        icon="mdi:speedometer",
        current_value_fn=lambda state: _mms_to_ms(state.isokinetic_target_speed_mms),
        set_value_fn=lambda coordinator, value: coordinator.client.async_set_isokinetic_target_speed(_ms_to_mms(value)),
        min_value=0.10,
        max_value=2.0,
        unit="m/s",
        available_fn=_is_isokinetic,
    ),
    VoltraCoverDescription(
        key="speed_limit_cover",
        name="Speed limit position",
        icon="mdi:ray-end-arrow",
        entity_category=EntityCategory.CONFIG,
        current_value_fn=lambda state: _mms_to_ms(state.isokinetic_speed_limit_mms),
        set_value_fn=lambda coordinator, value: coordinator.client.async_set_isokinetic_speed_limit(_ms_to_mms(value)),
        min_value=0,
        max_value=2.0,
        unit="m/s",
        available_fn=lambda state: _is_isokinetic(state) and state.isokinetic_mode != 1,
    ),
    VoltraCoverDescription(
        key="constant_resistance_cover",
        name="Constant resistance position",
        icon="mdi:weight-pound",
        entity_category=EntityCategory.CONFIG,
        current_value_fn=lambda state: state.isokinetic_constant_resistance_lb,
        set_value_fn=lambda coordinator, value: coordinator.client.async_set_isokinetic_constant_resistance(value),
        min_value=5,
        max_value=100,
        unit="lb",
        available_fn=lambda state: _is_isokinetic(state) and state.isokinetic_mode == 1,
    ),
    VoltraCoverDescription(
        key="max_eccentric_load_cover",
        name="Max eccentric load position",
        icon="mdi:weight-pound",
        entity_category=EntityCategory.CONFIG,
        current_value_fn=lambda state: state.isokinetic_max_eccentric_load_lb,
        set_value_fn=lambda coordinator, value: coordinator.client.async_set_isokinetic_max_eccentric_load(value),
        min_value=5,
        max_value=200,
        unit="lb",
        available_fn=lambda state: _is_isokinetic(state) and state.isokinetic_mode != 1,
    ),
    VoltraCoverDescription(
        key="cable_offset_cover",
        name="Cable offset position",
        icon="mdi:camera-control",
        entity_category=EntityCategory.CONFIG,
        current_value_fn=lambda state: state.cable_offset_cm,
        set_value_fn=lambda coordinator, value: coordinator.client.async_set_cable_offset(value),
        min_value=0,
        max_value=260,
        unit="cm",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: VoltraCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(VoltraValueCover(coordinator, description) for description in DESCRIPTIONS)


class VoltraValueCover(VoltraControlEntity, CoverEntity):
    entity_description: VoltraCoverDescription
    _attr_supported_features = (
        CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE | CoverEntityFeature.SET_POSITION
    )

    def __init__(self, coordinator: VoltraCoordinator, description: VoltraCoverDescription) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def available(self) -> bool:
        if not super().available:
            return False
        predicate = self.entity_description.available_fn
        return predicate(self.coordinator.data) if predicate is not None else True

    @property
    def current_cover_position(self) -> int | None:
        value = self.entity_description.current_value_fn(self.coordinator.data)
        if value is None:
            return None
        return _value_to_position(
            value,
            self.entity_description.min_value,
            self.entity_description.max_value,
        )

    @property
    def is_closed(self) -> bool | None:
        position = self.current_cover_position
        if position is None:
            return None
        return position <= 0

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        value = self.entity_description.current_value_fn(self.coordinator.data)
        return {
            "native_value": value,
            "native_unit_of_measurement": self.entity_description.unit,
        }

    async def async_open_cover(self, **kwargs) -> None:
        await self.entity_description.set_value_fn(
            self.coordinator,
            self.entity_description.max_value,
        )

    async def async_close_cover(self, **kwargs) -> None:
        await self.entity_description.set_value_fn(
            self.coordinator,
            self.entity_description.min_value,
        )

    async def async_set_cover_position(self, **kwargs) -> None:
        position = kwargs[ATTR_POSITION]
        native_value = _position_to_value(
            position,
            self.entity_description.min_value,
            self.entity_description.max_value,
        )
        await self.entity_description.set_value_fn(self.coordinator, native_value)
