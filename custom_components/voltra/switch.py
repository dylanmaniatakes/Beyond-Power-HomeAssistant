from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import VoltraCoordinator
from .entity import VoltraControlEntity
from .models import VoltraState


def _is_strength(state: VoltraState) -> bool:
    return state.workout_state == 1


def _is_active_workout(state: VoltraState) -> bool:
    return state.workout_state not in (None, 0)


def _is_resistance_band(state: VoltraState) -> bool:
    return state.workout_state == 2


def _is_isokinetic(state: VoltraState) -> bool:
    return state.workout_state == 7


def _workout_mode_is(state: VoltraState, workout_state: int) -> bool:
    return state.workout_state == workout_state


async def _async_exit_if_in_mode(coordinator: VoltraCoordinator, workout_state: int) -> None:
    if coordinator.data.workout_state == workout_state:
        await coordinator.client.async_exit_workout()


@dataclass(frozen=True, kw_only=True)
class VoltraSwitchDescription(SwitchEntityDescription):
    is_on_fn: Callable[[VoltraState], bool | None]
    turn_on_fn: Callable[[VoltraCoordinator], Awaitable[None]]
    turn_off_fn: Callable[[VoltraCoordinator], Awaitable[None]]
    available_fn: Callable[[VoltraState], bool] | None = None


DESCRIPTIONS: tuple[VoltraSwitchDescription, ...] = (
    VoltraSwitchDescription(
        key="load_engaged",
        name="Load",
        icon="mdi:weight-lifter",
        is_on_fn=lambda state: state.load_engaged,
        turn_on_fn=lambda coordinator: coordinator.client.async_load(),
        turn_off_fn=lambda coordinator: coordinator.client.async_unload(),
    ),
    VoltraSwitchDescription(
        key="weight_training_mode",
        name="Weight Training mode",
        icon="mdi:dumbbell",
        is_on_fn=lambda state: _workout_mode_is(state, 1),
        turn_on_fn=lambda coordinator: coordinator.client.async_set_strength_mode(),
        turn_off_fn=lambda coordinator: _async_exit_if_in_mode(coordinator, 1),
    ),
    VoltraSwitchDescription(
        key="resistance_band_mode",
        name="Resistance Band mode",
        icon="mdi:sine-wave",
        is_on_fn=lambda state: _workout_mode_is(state, 2),
        turn_on_fn=lambda coordinator: coordinator.client.async_enter_resistance_band_mode(),
        turn_off_fn=lambda coordinator: _async_exit_if_in_mode(coordinator, 2),
    ),
    VoltraSwitchDescription(
        key="damper_mode",
        name="Damper mode",
        icon="mdi:fan",
        is_on_fn=lambda state: _workout_mode_is(state, 4),
        turn_on_fn=lambda coordinator: coordinator.client.async_enter_damper_mode(),
        turn_off_fn=lambda coordinator: _async_exit_if_in_mode(coordinator, 4),
    ),
    VoltraSwitchDescription(
        key="isokinetic_mode_switch",
        name="Isokinetic mode",
        icon="mdi:speedometer",
        is_on_fn=lambda state: _workout_mode_is(state, 7),
        turn_on_fn=lambda coordinator: coordinator.client.async_enter_isokinetic_mode(),
        turn_off_fn=lambda coordinator: _async_exit_if_in_mode(coordinator, 7),
    ),
    VoltraSwitchDescription(
        key="isometric_test_mode",
        name="Isometric Test mode",
        icon="mdi:chart-line",
        is_on_fn=lambda state: _workout_mode_is(state, 8),
        turn_on_fn=lambda coordinator: coordinator.client.async_enter_isometric_mode(),
        turn_off_fn=lambda coordinator: _async_exit_if_in_mode(coordinator, 8),
    ),
    VoltraSwitchDescription(
        key="assist_mode",
        name="Assist",
        icon="mdi:hand-back-right",
        entity_category=EntityCategory.CONFIG,
        is_on_fn=lambda state: state.assist_mode_enabled,
        turn_on_fn=lambda coordinator: coordinator.client.async_set_assist_mode(True),
        turn_off_fn=lambda coordinator: coordinator.client.async_set_assist_mode(False),
        available_fn=_is_strength,
    ),
    VoltraSwitchDescription(
        key="inverse_chains",
        name="Inverse chains",
        icon="mdi:link",
        entity_category=EntityCategory.CONFIG,
        is_on_fn=lambda state: state.inverse_chains,
        turn_on_fn=lambda coordinator: coordinator.client.async_set_inverse_chains(True),
        turn_off_fn=lambda coordinator: coordinator.client.async_set_inverse_chains(False),
        available_fn=_is_strength,
    ),
    VoltraSwitchDescription(
        key="intense_experience",
        name="Intense experience",
        icon="mdi:fire",
        entity_category=EntityCategory.CONFIG,
        is_on_fn=lambda state: state.resistance_experience_intense,
        turn_on_fn=lambda coordinator: coordinator.client.async_set_resistance_experience(True),
        turn_off_fn=lambda coordinator: coordinator.client.async_set_resistance_experience(False),
        available_fn=_is_active_workout,
    ),
    VoltraSwitchDescription(
        key="inverse_resistance",
        name="Inverse resistance",
        icon="mdi:swap-horizontal",
        entity_category=EntityCategory.CONFIG,
        is_on_fn=lambda state: state.resistance_band_inverse,
        turn_on_fn=lambda coordinator: coordinator.client.async_set_resistance_band_inverse(True),
        turn_off_fn=lambda coordinator: coordinator.client.async_set_resistance_band_inverse(False),
        available_fn=_is_resistance_band,
    ),
    VoltraSwitchDescription(
        key="logarithmic_curve",
        name="Logarithmic curve",
        icon="mdi:function-variant",
        entity_category=EntityCategory.CONFIG,
        is_on_fn=lambda state: state.resistance_band_curve_logarithm,
        turn_on_fn=lambda coordinator: coordinator.client.async_set_resistance_band_curve_algorithm(True),
        turn_off_fn=lambda coordinator: coordinator.client.async_set_resistance_band_curve_algorithm(False),
        available_fn=_is_resistance_band,
    ),
    VoltraSwitchDescription(
        key="rom_progressive_length",
        name="ROM progressive length",
        icon="mdi:chart-bell-curve",
        entity_category=EntityCategory.CONFIG,
        is_on_fn=lambda state: state.resistance_band_by_range_of_motion,
        turn_on_fn=lambda coordinator: coordinator.client.async_set_resistance_band_by_rom(True),
        turn_off_fn=lambda coordinator: coordinator.client.async_set_resistance_band_by_rom(False),
        available_fn=_is_resistance_band,
    ),
    VoltraSwitchDescription(
        key="constant_resistance_mode",
        name="Constant resistance mode",
        icon="mdi:swap-horizontal-bold",
        entity_category=EntityCategory.CONFIG,
        is_on_fn=lambda state: state.isokinetic_mode == 1,
        turn_on_fn=lambda coordinator: coordinator.client.async_set_isokinetic_menu("Constant Resistance"),
        turn_off_fn=lambda coordinator: coordinator.client.async_set_isokinetic_menu("Isokinetic"),
        available_fn=_is_isokinetic,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: VoltraCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(VoltraSwitch(coordinator, description) for description in DESCRIPTIONS)


class VoltraSwitch(VoltraControlEntity, SwitchEntity):
    entity_description: VoltraSwitchDescription

    def __init__(self, coordinator: VoltraCoordinator, description: VoltraSwitchDescription) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def available(self) -> bool:
        if not super().available:
            return False
        predicate = self.entity_description.available_fn
        return predicate(self.coordinator.data) if predicate is not None else True

    @property
    def is_on(self) -> bool | None:
        return self.entity_description.is_on_fn(self.coordinator.data)

    async def async_turn_on(self, **kwargs) -> None:
        await self.entity_description.turn_on_fn(self.coordinator)

    async def async_turn_off(self, **kwargs) -> None:
        await self.entity_description.turn_off_fn(self.coordinator)
