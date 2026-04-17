from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import VoltraCoordinator
from .entity import VoltraEntity
from .models import VoltraState


@dataclass(frozen=True, kw_only=True)
class VoltraButtonDescription(ButtonEntityDescription):
    press_fn: Callable[[VoltraCoordinator], Awaitable[None]]
    available_fn: Callable[[VoltraState], bool] | None = None


DESCRIPTIONS: tuple[VoltraButtonDescription, ...] = (
    VoltraButtonDescription(
        key="refresh_status",
        name="Refresh status",
        icon="mdi:refresh",
        entity_category=EntityCategory.DIAGNOSTIC,
        press_fn=lambda coordinator: coordinator.client.async_refresh_status(),
        available_fn=lambda state: state.connected,
    ),
    VoltraButtonDescription(
        key="trigger_cable_length_mode",
        name="Adjust cable length",
        icon="mdi:tape-measure",
        press_fn=lambda coordinator: coordinator.client.async_trigger_cable_length_mode(),
        available_fn=lambda state: state.protocol_validated and state.workout_state not in (None, 0),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: VoltraCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(VoltraButton(coordinator, description) for description in DESCRIPTIONS)


class VoltraButton(VoltraEntity, ButtonEntity):
    entity_description: VoltraButtonDescription

    def __init__(self, coordinator: VoltraCoordinator, description: VoltraButtonDescription) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def available(self) -> bool:
        if not super().available:
            return False
        predicate = self.entity_description.available_fn
        return predicate(self.coordinator.data) if predicate is not None else True

    async def async_press(self) -> None:
        await self.entity_description.press_fn(self.coordinator)
