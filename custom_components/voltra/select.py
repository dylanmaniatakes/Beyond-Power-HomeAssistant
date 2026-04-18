from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import VoltraCoordinator
from .entity import VoltraControlEntity
from .models import VoltraState

WORKOUT_OPTIONS = (
    "Inactive",
    "Weight Training",
    "Resistance Band",
    "Damper",
    "Isokinetic",
    "Isometric Test",
)

ISOKINETIC_OPTIONS = (
    "Isokinetic",
    "Constant Resistance",
)

RESISTANCE_EXPERIENCE_OPTIONS = (
    "Standard",
    "Intense",
)

RESISTANCE_MODE_OPTIONS = (
    "Standard",
    "Inverse",
)

RESISTANCE_CURVE_OPTIONS = (
    "Power Law",
    "Logarithm",
)

PROGRESSIVE_LENGTH_OPTIONS = (
    "Band Length",
    "ROM",
)


def _is_active_workout(state: VoltraState) -> bool:
    return state.workout_state not in (None, 0)


def _is_resistance_band(state: VoltraState) -> bool:
    return state.workout_state == 2


def _is_isokinetic(state: VoltraState) -> bool:
    return state.workout_state == 7


def _current_workout_mode(state: VoltraState) -> str:
    if state.workout_state == 1:
        return "Weight Training"
    if state.workout_state == 2:
        return "Resistance Band"
    if state.workout_state == 4:
        return "Damper"
    if state.workout_state == 7:
        return "Isokinetic"
    if state.workout_state == 8:
        return "Isometric Test"
    return "Inactive"


def _current_isokinetic_mode(state: VoltraState) -> str:
    return "Constant Resistance" if state.isokinetic_mode == 1 else "Isokinetic"


def _current_resistance_experience(state: VoltraState) -> str:
    return "Intense" if state.resistance_experience_intense else "Standard"


def _current_resistance_mode(state: VoltraState) -> str:
    return "Inverse" if state.resistance_band_inverse else "Standard"


def _current_resistance_curve(state: VoltraState) -> str:
    return "Logarithm" if state.resistance_band_curve_logarithm else "Power Law"


def _current_progressive_length(state: VoltraState) -> str:
    return "ROM" if state.resistance_band_by_range_of_motion else "Band Length"


@dataclass(frozen=True, kw_only=True)
class VoltraSelectDescription(SelectEntityDescription):
    current_option_fn: Callable[[VoltraState], str]
    select_fn: Callable[[VoltraCoordinator, str], Awaitable[None]]
    available_fn: Callable[[VoltraState], bool] | None = None


DESCRIPTIONS: tuple[VoltraSelectDescription, ...] = (
    VoltraSelectDescription(
        key="workout_mode",
        name="Mode",
        icon="mdi:arm-flex",
        options=WORKOUT_OPTIONS,
        current_option_fn=_current_workout_mode,
        select_fn=lambda coordinator, option: coordinator.client.async_set_workout_mode(option),
    ),
    VoltraSelectDescription(
        key="resistance_experience",
        name="Resistance experience",
        icon="mdi:fire",
        options=RESISTANCE_EXPERIENCE_OPTIONS,
        entity_category=EntityCategory.CONFIG,
        current_option_fn=_current_resistance_experience,
        select_fn=lambda coordinator, option: coordinator.client.async_set_resistance_experience(option == "Intense"),
        available_fn=_is_active_workout,
    ),
    VoltraSelectDescription(
        key="resistance_mode",
        name="Resistance mode",
        icon="mdi:swap-horizontal",
        options=RESISTANCE_MODE_OPTIONS,
        entity_category=EntityCategory.CONFIG,
        current_option_fn=_current_resistance_mode,
        select_fn=lambda coordinator, option: coordinator.client.async_set_resistance_band_inverse(option == "Inverse"),
        available_fn=_is_resistance_band,
    ),
    VoltraSelectDescription(
        key="resistance_curve",
        name="Resistance curve",
        icon="mdi:function-variant",
        options=RESISTANCE_CURVE_OPTIONS,
        entity_category=EntityCategory.CONFIG,
        current_option_fn=_current_resistance_curve,
        select_fn=lambda coordinator, option: coordinator.client.async_set_resistance_band_curve_algorithm(option == "Logarithm"),
        available_fn=_is_resistance_band,
    ),
    VoltraSelectDescription(
        key="progressive_length",
        name="Progressive length",
        icon="mdi:chart-bell-curve",
        options=PROGRESSIVE_LENGTH_OPTIONS,
        entity_category=EntityCategory.CONFIG,
        current_option_fn=_current_progressive_length,
        select_fn=lambda coordinator, option: coordinator.client.async_set_resistance_band_by_rom(option == "ROM"),
        available_fn=_is_resistance_band,
    ),
    VoltraSelectDescription(
        key="isokinetic_mode",
        name="Isokinetic mode",
        icon="mdi:swap-horizontal-bold",
        options=ISOKINETIC_OPTIONS,
        entity_category=EntityCategory.CONFIG,
        current_option_fn=_current_isokinetic_mode,
        select_fn=lambda coordinator, option: coordinator.client.async_set_isokinetic_menu(option),
        available_fn=_is_isokinetic,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: VoltraCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(VoltraSelect(coordinator, description) for description in DESCRIPTIONS)


class VoltraSelect(VoltraControlEntity, SelectEntity):
    entity_description: VoltraSelectDescription

    def __init__(self, coordinator: VoltraCoordinator, description: VoltraSelectDescription) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def current_option(self) -> str:
        return self.entity_description.current_option_fn(self.coordinator.data)

    @property
    def available(self) -> bool:
        if not super().available:
            return False
        predicate = self.entity_description.available_fn
        return predicate(self.coordinator.data) if predicate is not None else True

    async def async_select_option(self, option: str) -> None:
        await self.entity_description.select_fn(self.coordinator, option)
