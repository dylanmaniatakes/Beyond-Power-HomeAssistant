from __future__ import annotations

from pathlib import Path

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
import voluptuous as vol

from .const import DOMAIN, PLATFORMS

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

SERVICE_UPLOAD_STARTUP_IMAGE = "upload_startup_image"
ATTR_ENTRY_ID = "entry_id"
ATTR_IMAGE_PATH = "image_path"
ATTR_PREPARE_IMAGE = "prepare_image"

UPLOAD_STARTUP_IMAGE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_IMAGE_PATH): cv.string,
        vol.Optional(ATTR_ENTRY_ID): cv.string,
        vol.Optional(ATTR_PREPARE_IMAGE, default=True): cv.boolean,
    },
)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    hass.data.setdefault(DOMAIN, {})
    if not hass.services.has_service(DOMAIN, SERVICE_UPLOAD_STARTUP_IMAGE):
        async def _handle_upload_startup_image(call: ServiceCall) -> None:
            await _async_handle_upload_startup_image(hass, call)

        hass.services.async_register(
            DOMAIN,
            SERVICE_UPLOAD_STARTUP_IMAGE,
            _handle_upload_startup_image,
            schema=UPLOAD_STARTUP_IMAGE_SCHEMA,
        )
    return True


async def _async_handle_upload_startup_image(hass: HomeAssistant, call: ServiceCall) -> None:
    from .coordinator import VoltraCoordinator
    from .startup_image import prepare_startup_image_bytes, validate_startup_jpeg_bytes

    coordinators: dict[str, VoltraCoordinator] = hass.data.get(DOMAIN, {})
    entry_id = call.data.get(ATTR_ENTRY_ID)
    if entry_id is not None:
        coordinator = coordinators.get(entry_id)
        if coordinator is None:
            raise HomeAssistantError(f"No Beyond Power Voltra config entry found for {entry_id}.")
    elif len(coordinators) == 1:
        coordinator = next(iter(coordinators.values()))
    else:
        raise HomeAssistantError("Choose a Beyond Power Voltra config entry for startup image upload.")

    configured_path = Path(call.data[ATTR_IMAGE_PATH]).expanduser()
    image_path = configured_path if configured_path.is_absolute() else Path(hass.config.path(str(configured_path)))
    prepare_image = call.data[ATTR_PREPARE_IMAGE]

    def _load_image() -> bytes:
        if not image_path.is_file():
            raise FileNotFoundError(f"Startup image file does not exist: {image_path}")
        source_bytes = image_path.read_bytes()
        if prepare_image:
            return prepare_startup_image_bytes(source_bytes)
        validate_startup_jpeg_bytes(source_bytes)
        return source_bytes

    try:
        jpeg_bytes = await hass.async_add_executor_job(_load_image)
    except (OSError, ValueError) as err:
        raise HomeAssistantError(str(err)) from err

    await coordinator.client.async_upload_startup_image(jpeg_bytes)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    from .coordinator import VoltraCoordinator

    coordinator = VoltraCoordinator(hass, entry)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await coordinator.async_start()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    from .coordinator import VoltraCoordinator

    coordinator: VoltraCoordinator = hass.data[DOMAIN][entry.entry_id]
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        await coordinator.async_stop()
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
