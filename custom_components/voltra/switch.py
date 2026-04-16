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


@dataclass(frozen=True, kw_only=True)
class VoltraSwitchDescription(SwitchEntityDescription):
    is_on_fn: Callable[[VoltraState], bool | None]
    turn_on_fn: Callable[[VoltraCoordinator], Awaitable[None]]
    turn_off_fn: Callable[[VoltraCoordinator], Awaitable[None]]
    available_fn: Callable[[VoltraState], bool] | None = None


DESCRIPTIONS: tuple[VoltraSwitchDescription, ...] = (
    VoltraSwitchDescription(
        key="load_engaged",
        name="Loaded",
        icon="mdi:weight-lifter",
        is_on_fn=lambda state: state.load_engaged,
        turn_on_fn=lambda coordinator: coordinator.client.async_load(),
        turn_off_fn=lambda coordinator: coordinator.client.async_unload(),
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
