from __future__ import annotations

import asyncio
from dataclasses import replace
import logging
import time
from typing import TYPE_CHECKING, Any

from bleak import BleakClient
from bleak.exc import BleakError
from homeassistant.components import bluetooth
from homeassistant.exceptions import HomeAssistantError

try:
    from bleak_retry_connector import BleakClientWithServiceCache, establish_connection
except ImportError:  # pragma: no cover - depends on Home Assistant runtime
    BleakClientWithServiceCache = BleakClient
    establish_connection = None

from .const import (
    BOOTSTRAP_WRITE_PACING_SECONDS,
    CONFIRMED_RESPONSE_CHARACTERISTIC_UUIDS,
    CONNECT_RETRY_BASE_DELAY_SECONDS,
    CONNECT_RETRY_MAX_DELAY_SECONDS,
    NOTIFY_CHARACTERISTIC_UUIDS,
    PROTOCOL_RETRY_INTERVAL_SECONDS,
    VOLTRA_COMMAND_CHARACTERISTIC_UUID,
    VOLTRA_TRANSPORT_CHARACTERISTIC_UUID,
)
from .models import VoltraState
from .protocol import (
    AUTO_ISOKINETIC_SPEED_MMS,
    CMD_BULK_PARAM_WRITE,
    CMD_PARAM_READ,
    CMD_PARAM_WRITE,
    CMD_SET_DEVICE_NAME,
    CMD_TELEMETRY,
    DEFAULT_CUSTOM_CURVE_POINTS,
    DEFAULT_CUSTOM_CURVE_RANGE_OF_MOTION_IN,
    DEFAULT_CUSTOM_CURVE_RESISTANCE_LIMIT_LB,
    DEFAULT_CUSTOM_CURVE_RESISTANCE_MIN_LB,
    DEFAULT_ROWING_RESISTANCE_LEVEL,
    DEFAULT_ROWING_SIMULATED_WEAR_LEVEL,
    FITNESS_MODE_ISOMETRIC_ARMED,
    FITNESS_MODE_ROWING_ACTIVE,
    FITNESS_MODE_TEST_SCREEN,
    FITNESS_MODE_STRENGTH_LOADED,
    FITNESS_MODE_STRENGTH_READY,
    FrameAssembler,
    ISOKINETIC_MENU_CONSTANT_RESISTANCE,
    ISOKINETIC_MENU_ISOKINETIC,
    MAX_CABLE_OFFSET_CM,
    MAX_CUSTOM_CURVE_RANGE_OF_MOTION_IN,
    MAX_CUSTOM_CURVE_RESISTANCE_LIMIT_LB,
    MAX_ECCENTRIC_WEIGHT_LB,
    MAX_EXTRA_WEIGHT_LB,
    MAX_ISOKINETIC_MAX_ECCENTRIC_LOAD_LB,
    MAX_ISOKINETIC_SPEED_MMS,
    MAX_ISOKINETIC_CONSTANT_RESISTANCE_LB,
    MAX_ROWING_SELECTOR_LEVEL,
    MAX_RESISTANCE_BAND_FORCE_LB,
    MAX_RESISTANCE_BAND_LENGTH_CM,
    MAX_TARGET_LB,
    MIN_CABLE_OFFSET_CM,
    MIN_CUSTOM_CURVE_RANGE_OF_MOTION_IN,
    MIN_CUSTOM_CURVE_RESISTANCE_LIMIT_LB,
    MIN_CUSTOM_CURVE_RESISTANCE_SPAN_LB,
    MIN_ECCENTRIC_WEIGHT_LB,
    MIN_EXTRA_WEIGHT_LB,
    MIN_ISOKINETIC_MAX_ECCENTRIC_LOAD_LB,
    MIN_ISOKINETIC_SPEED_MMS,
    MIN_ISOKINETIC_CONSTANT_RESISTANCE_LB,
    MIN_ROWING_SELECTOR_LEVEL,
    MIN_RESISTANCE_BAND_FORCE_LB,
    MIN_RESISTANCE_BAND_LENGTH_CM,
    MIN_TARGET_LB,
    MODE_FEATURE_STATUS_PARAMS,
    OFFICIAL_BOOTSTRAP_PACKETS,
    PARAM_BP_BASE_WEIGHT,
    PARAM_BP_CHAINS_WEIGHT,
    PARAM_BP_ECCENTRIC_WEIGHT,
    PARAM_BP_SET_FITNESS_MODE,
    PARAM_BP_RUNTIME_POSITION_CM,
    PARAM_POWER_OFF_LOGO_EN,
    PARAM_EP_ISOKINETIC_TARGET_SPEED_MMS,
    PARAM_EP_RESISTANCE_BAND_INVERSE,
    PARAM_EP_SCR_SWITCH,
    PARAM_FITNESS_ASSIST_MODE,
    PARAM_FITNESS_DAMPER_RATIO_IDX,
    PARAM_FITNESS_INVERSE_CHAIN,
    PARAM_FITNESS_ROWING_DAMPER_RATIO_IDX,
    PARAM_FITNESS_WORKOUT_STATE,
    PARAM_ISOKINETIC_ECC_CONST_WEIGHT,
    PARAM_ISOKINETIC_ECC_MODE,
    PARAM_ISOKINETIC_ECC_OVERLOAD_WEIGHT,
    PARAM_ISOKINETIC_ECC_SPEED_LIMIT,
    PARAM_MC_DEFAULT_OFFLEN_CM,
    PARAM_EP_ROW_CHAIN_GEAR,
    PARAM_RESISTANCE_BAND_ALGORITHM,
    PARAM_RESISTANCE_BAND_LEN,
    PARAM_RESISTANCE_BAND_LEN_BY_ROM,
    PARAM_RESISTANCE_BAND_MAX_FORCE,
    PARAM_RESISTANCE_EXPERIENCE,
    ROWING_ONGOING_UI,
    ROWING_SCREEN_ID,
    STARTUP_IMAGE_CHUNK_DATA_BYTES,
    STARTUP_IMAGE_STATE_PARAMS,
    STATUS_REFRESH_PARAMS,
    WORKOUT_STATE_ACTIVE,
    WORKOUT_STATE_CUSTOM_CURVE,
    WORKOUT_STATE_DAMPER,
    WORKOUT_STATE_INACTIVE,
    WORKOUT_STATE_ISOKINETIC,
    WORKOUT_STATE_ISOMETRIC,
    WORKOUT_STATE_ROWING,
    WORKOUT_STATE_RESISTANCE_BAND,
    apply_packet_to_state,
    build_custom_curve_bulk_subscribe_payload,
    build_custom_curve_vendor_preset_payload,
    build_device_name_payload,
    build_enter_custom_curve_payload,
    build_enter_row_payload,
    build_frame,
    build_param_read_frame,
    build_param_write_frame,
    build_row_bulk_subscribe_payload,
    build_set_fitness_data_notify_hz_payload,
    build_set_fitness_data_notify_subscribe_payload,
    build_set_rowing_resistance_level_payload,
    build_set_rowing_simulated_wear_level_payload,
    build_startup_image_apply_payload,
    build_startup_image_chunk_payload,
    build_startup_image_finalize_payload,
    build_startup_image_header_payload,
    build_trigger_row_start_screen_payload,
    build_vendor_state_refresh_frame,
    encode_int16_le,
    encode_uint16_le,
    encode_uint32_le,
    is_isokinetic_workout_state,
    parse_startup_image_ack_code,
    rowing_selector_wire_index,
    startup_image_frame_type,
)

if TYPE_CHECKING:
    from bleak.backends.characteristic import BleakGATTCharacteristic
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)
PARAM_READ_FRAME_IDS_PER_CHUNK = 2
ISOMETRIC_VENDOR_REFRESH_INTERVAL_SECONDS = 0.5
ISOMETRIC_VENDOR_REFRESH_BURST_SECONDS = 3.0
ROW_VENDOR_REFRESH_BURST_SECONDS = 12.0
CONNECTED_IDLE_LOOP_INTERVAL_SECONDS = 1.0


class VoltraApiError(HomeAssistantError):
    """Raised when the VOLTRA integration cannot complete a requested action."""


class VoltraBleClient:
    def __init__(
        self,
        hass: HomeAssistant,
        address: str,
        configured_name: str | None,
        update_callback,
    ) -> None:
        self._hass = hass
        self._address = address.upper()
        self._configured_name = configured_name
        self._update_callback = update_callback
        self._state = VoltraState(
            address=self._address,
            configured_name=configured_name,
            device_name=configured_name,
        )
        self._client: BleakClient | None = None
        self._command_characteristic: Any = None
        self._transport_characteristic: Any = None
        self._runner_task: asyncio.Task[None] | None = None
        self._notification_task: asyncio.Task[None] | None = None
        self._stop_event = asyncio.Event()
        self._disconnect_event = asyncio.Event()
        self._write_lock = asyncio.Lock()
        self._notification_queue: asyncio.Queue[tuple[int, str, bytes]] = asyncio.Queue()
        self._assemblers: dict[str, FrameAssembler] = {}
        self._isometric_vendor_refresh_until = 0.0
        self._startup_image_poll_tasks: set[asyncio.Task[None]] = set()
        self._connection_epoch = 0
        self._sequence = 7

    @property
    def state(self) -> VoltraState:
        return self._state

    async def async_start(self) -> None:
        if self._runner_task is not None:
            return
        self._stop_event.clear()
        self._ensure_notification_processor()
        self._push_state(replace(self._state, status_message="Starting VOLTRA Bluetooth client."))
        self._runner_task = self._hass.async_create_task(self._run())

    async def async_stop(self) -> None:
        self._stop_event.set()
        if self._runner_task is not None:
            self._runner_task.cancel()
            try:
                await self._runner_task
            except asyncio.CancelledError:
                pass
            self._runner_task = None
        await self._async_disconnect_internal()
        await self._async_stop_notification_processor()

    async def async_refresh_status(self) -> None:
        self._require_connected()
        if not self._state.protocol_validated:
            await self._async_send_bootstrap()
            return
        await self._async_write_frames(
            self._build_chunked_param_read_frames(
                STATUS_REFRESH_PARAMS,
                "refresh mode feature state",
            ),
        )

    async def async_set_workout_mode(self, option: str) -> None:
        if option == "Inactive":
            await self.async_exit_workout()
        elif option == "Weight Training":
            await self.async_set_strength_mode()
        elif option == "Resistance Band":
            await self.async_enter_resistance_band_mode()
        elif option == "Rowing":
            await self.async_enter_row_mode()
        elif option == "Damper":
            await self.async_enter_damper_mode()
        elif option == "Custom Curve":
            await self.async_enter_custom_curve_mode()
        elif option == "Isokinetic":
            await self.async_enter_isokinetic_mode()
        elif option == "Isometric Test":
            await self.async_enter_isometric_mode()
        else:
            raise VoltraApiError(f"Unsupported workout mode: {option}")

    async def async_set_custom_curve_point(self, index: int, value_percent: float) -> None:
        self._require_control_ready("Custom Curve is not ready yet.")
        if index not in range(0, len(self._state.custom_curve_points)):
            raise VoltraApiError(f"Unsupported Custom Curve point index: {index}")
        points = list(self._state.custom_curve_points)
        points[index] = max(0.0, min(1.0, float(value_percent) / 100.0))
        self._push_state(replace(self._state, custom_curve_points=tuple(points)))

    async def async_set_custom_curve_resistance_min(self, value: float) -> None:
        self._require_control_ready("Custom Curve is not ready yet.")
        current_limit = self._state.custom_curve_resistance_limit_lb or DEFAULT_CUSTOM_CURVE_RESISTANCE_LIMIT_LB
        maximum = max(
            MIN_CUSTOM_CURVE_RESISTANCE_LIMIT_LB,
            current_limit - MIN_CUSTOM_CURVE_RESISTANCE_SPAN_LB,
        )
        normalized = self._clamp_round(value, MIN_CUSTOM_CURVE_RESISTANCE_LIMIT_LB, maximum)
        self._push_state(replace(self._state, custom_curve_resistance_min_lb=normalized))

    async def async_set_custom_curve_resistance_limit(self, value: float) -> None:
        self._require_control_ready("Custom Curve is not ready yet.")
        current_min = self._state.custom_curve_resistance_min_lb or DEFAULT_CUSTOM_CURVE_RESISTANCE_MIN_LB
        minimum = min(
            MAX_CUSTOM_CURVE_RESISTANCE_LIMIT_LB,
            current_min + MIN_CUSTOM_CURVE_RESISTANCE_SPAN_LB,
        )
        normalized = self._clamp_round(value, minimum, MAX_CUSTOM_CURVE_RESISTANCE_LIMIT_LB)
        self._push_state(replace(self._state, custom_curve_resistance_limit_lb=normalized))

    async def async_set_custom_curve_range_of_motion(self, value: float) -> None:
        self._require_control_ready("Custom Curve is not ready yet.")
        normalized = self._clamp_round(
            value,
            MIN_CUSTOM_CURVE_RANGE_OF_MOTION_IN,
            MAX_CUSTOM_CURVE_RANGE_OF_MOTION_IN,
        )
        self._push_state(replace(self._state, custom_curve_range_of_motion_in=normalized))

    async def async_set_rowing_target_meters(self, target_meters: int | None) -> None:
        self._require_control_ready("Row target is not ready yet.")
        if target_meters not in (None, 50, 100, 500, 1000, 2000, 5000):
            raise VoltraApiError(f"Unsupported Row target distance: {target_meters}")
        self._push_state(replace(self._state, rowing_target_meters=target_meters))

    async def async_set_target_load(self, value: float) -> None:
        await self._async_send_param_write(
            param_id=PARAM_BP_BASE_WEIGHT,
            value=encode_uint16_le(self._clamp_round(value, MIN_TARGET_LB, MAX_TARGET_LB)),
            label="set target load",
        )

    async def async_set_device_name(self, name: str) -> None:
        self._require_connected()
        trimmed = name.strip()
        try:
            payload = build_device_name_payload(trimmed)
        except ValueError as err:
            raise VoltraApiError(str(err)) from err
        frame = build_frame(
            cmd=CMD_SET_DEVICE_NAME,
            payload=payload,
            seq=self._next_sequence(),
        )
        async with self._write_lock:
            await self._async_write_frame_to_characteristic_locked(
                label=f'set device name to "{trimmed}"',
                frame=frame,
                characteristic=self._command_characteristic or VOLTRA_COMMAND_CHARACTERISTIC_UUID,
            )

        self._configured_name = trimmed
        self._push_state(
            replace(
                self._state,
                configured_name=trimmed,
                device_name=trimmed,
                status_message=f'Queued device rename to "{trimmed}".',
            ),
        )

    async def async_upload_startup_image(self, jpeg_bytes: bytes) -> None:
        self._require_connected()
        if not jpeg_bytes:
            raise VoltraApiError("Startup image is empty.")

        chunks = [
            jpeg_bytes[index : index + STARTUP_IMAGE_CHUNK_DATA_BYTES]
            for index in range(0, len(jpeg_bytes), STARTUP_IMAGE_CHUNK_DATA_BYTES)
        ]
        if not chunks or len(chunks) > 0xFFFF:
            raise VoltraApiError(f"Startup image chunk count is invalid: {len(chunks)}.")

        self._cancel_startup_image_state_polls()
        self._push_state(
            replace(
                self._state,
                startup_image_upload_status="queued",
                startup_image_upload_bytes=len(jpeg_bytes),
                startup_image_upload_chunks_total=len(chunks),
                startup_image_upload_chunks_acked=0,
                startup_image_last_ack=None,
                status_message=f"Queued startup image upload ({len(jpeg_bytes)} bytes, {len(chunks)} chunks).",
            ),
        )

        frames: list[tuple[str, bytes, int | None]] = [
            (
                "enable startup image display",
                build_param_write_frame(
                    PARAM_POWER_OFF_LOGO_EN,
                    bytes((0x01,)),
                    self._next_sequence(),
                ),
                None,
            ),
            (
                "startup image header",
                build_frame(
                    cmd=CMD_STARTUP_IMAGE,
                    payload=build_startup_image_header_payload(jpeg_bytes, len(chunks)),
                    seq=self._next_sequence(),
                ),
                None,
            ),
        ]
        for index, chunk in enumerate(chunks, start=1):
            payload = build_startup_image_chunk_payload(index, chunk)
            frames.append(
                (
                    f"startup image chunk {index}/{len(chunks)}",
                    build_frame(
                        cmd=CMD_STARTUP_IMAGE,
                        payload=payload,
                        seq=self._next_sequence(),
                        frame_type=startup_image_frame_type(payload),
                    ),
                    index,
                ),
            )
        frames.extend(
            [
                (
                    "startup image finalize",
                    build_frame(
                        cmd=CMD_STARTUP_IMAGE,
                        payload=build_startup_image_finalize_payload(),
                        seq=self._next_sequence(),
                    ),
                    None,
                ),
                (
                    "startup image apply",
                    build_frame(
                        cmd=CMD_STARTUP_IMAGE,
                        payload=build_startup_image_apply_payload(),
                        seq=self._next_sequence(),
                    ),
                    None,
                ),
            ],
        )
        await self._async_write_startup_image_frames(frames, len(chunks))

    async def async_set_assist_mode(self, enabled: bool) -> None:
        self._require_strength_mode("change Assist mode")
        await self._async_send_param_write(
            param_id=PARAM_FITNESS_ASSIST_MODE,
            value=bytes((1 if enabled else 0,)),
            label="set Assist mode",
        )

    async def async_set_chains_weight(self, value: float) -> None:
        self._require_strength_mode("change Chains")
        base_weight = self._base_weight_for_strength_features()
        max_value = min(base_weight, MAX_TARGET_LB - base_weight)
        normalized = self._clamp_round(value, MIN_EXTRA_WEIGHT_LB, max(MIN_EXTRA_WEIGHT_LB, max_value))
        await self._async_send_param_write(
            param_id=PARAM_BP_CHAINS_WEIGHT,
            value=encode_uint16_le(normalized),
            label="set Chains weight",
        )

    async def async_set_eccentric_weight(self, value: float) -> None:
        self._require_strength_mode("change Eccentric")
        base_weight = self._base_weight_for_strength_features()
        minimum = max(MIN_ECCENTRIC_WEIGHT_LB, -base_weight)
        maximum = min(MAX_ECCENTRIC_WEIGHT_LB, base_weight)
        normalized = self._clamp_round(value, minimum, maximum)
        await self._async_send_param_write(
            param_id=PARAM_BP_ECCENTRIC_WEIGHT,
            value=encode_int16_le(normalized),
            label="set Eccentric weight",
        )

    async def async_set_inverse_chains(self, enabled: bool) -> None:
        self._require_strength_mode("change Inverse Chains")
        await self._async_send_param_write(
            param_id=PARAM_FITNESS_INVERSE_CHAIN,
            value=bytes((1 if enabled else 0,)),
            label="set Inverse Chains",
        )

    async def async_set_resistance_experience(self, intense: bool) -> None:
        self._require_active_workout("change Resistance Experience")
        await self._async_send_param_write(
            param_id=PARAM_RESISTANCE_EXPERIENCE,
            value=bytes((0 if intense else 1,)),
            label="set Resistance Experience",
        )

    async def async_set_resistance_band_inverse(self, enabled: bool) -> None:
        self._require_workout_state(WORKOUT_STATE_RESISTANCE_BAND, "Resistance Band")
        await self._async_send_param_write(
            param_id=PARAM_EP_RESISTANCE_BAND_INVERSE,
            value=bytes((1 if enabled else 0,)),
            label="set Resistance Band inverse",
        )

    async def async_set_resistance_band_by_rom(self, enabled: bool) -> None:
        self._require_workout_state(WORKOUT_STATE_RESISTANCE_BAND, "Resistance Band")
        await self._async_send_param_write(
            param_id=PARAM_RESISTANCE_BAND_LEN_BY_ROM,
            value=bytes((1 if enabled else 0,)),
            label="set Resistance Band by-ROM",
        )

    async def async_set_resistance_band_curve_algorithm(self, logarithm: bool) -> None:
        self._require_workout_state(WORKOUT_STATE_RESISTANCE_BAND, "Resistance Band")
        await self._async_send_param_write(
            param_id=PARAM_RESISTANCE_BAND_ALGORITHM,
            value=bytes((1 if logarithm else 0,)),
            label="set Resistance Band curve",
        )

    async def async_enter_resistance_band_mode(self) -> None:
        await self._async_send_param_writes(
            [
                (
                    "enter Resistance Band",
                    PARAM_FITNESS_WORKOUT_STATE,
                    bytes((WORKOUT_STATE_RESISTANCE_BAND,)),
                ),
                (
                    "ready current mode",
                    PARAM_BP_SET_FITNESS_MODE,
                    encode_uint16_le(FITNESS_MODE_STRENGTH_READY),
                ),
            ],
        )

    async def async_enter_row_mode(self) -> None:
        self._require_control_ready("Row Mode is not ready yet.")
        rowing_resistance_level = self._state.rowing_resistance_level or DEFAULT_ROWING_RESISTANCE_LEVEL
        rowing_simulated_wear_level = self._state.rowing_simulated_wear_level or DEFAULT_ROWING_SIMULATED_WEAR_LEVEL
        self._push_state(
            replace(
                self._state,
                workout_mode="Rowing, Ready",
                workout_state=WORKOUT_STATE_ROWING,
                fitness_mode=FITNESS_MODE_STRENGTH_READY,
                can_load=True,
                safety_reasons=("Ready for current mode load.",),
                load_engaged=False,
                ready=True,
                rowing_resistance_level=rowing_resistance_level,
                rowing_simulated_wear_level=rowing_simulated_wear_level,
                rowing_distance_meters=None,
                rowing_elapsed_millis=None,
                rowing_pace_500_millis=None,
                rowing_average_pace_500_millis=None,
                rowing_stroke_rate_spm=None,
                rowing_drive_force_lb=None,
                rowing_telemetry_start_millis=None,
                rowing_last_stroke_start_millis=None,
                rowing_distance_samples_meters=(),
                rowing_force_samples_lb=(),
                rowing_force_last_chunk_index=None,
                app_current_screen_id=None,
                fitness_ongoing_ui=None,
                set_count=0,
                rep_count=0,
                rep_phase="Ready",
            ),
        )
        frames: list[tuple[str, bytes]] = [
            (
                "subscribe Row fitness data stream",
                build_frame(
                    cmd=CMD_PARAM_WRITE,
                    payload=build_set_fitness_data_notify_subscribe_payload(),
                    seq=self._next_sequence(),
                ),
            ),
            (
                "bulk subscribe Row params",
                build_frame(
                    cmd=CMD_BULK_PARAM_WRITE,
                    payload=build_row_bulk_subscribe_payload(),
                    seq=self._next_sequence(),
                ),
            ),
            (
                "set Row fitness data notify hz",
                build_frame(
                    cmd=CMD_PARAM_WRITE,
                    payload=build_set_fitness_data_notify_hz_payload(),
                    seq=self._next_sequence(),
                ),
            ),
            (
                f"set Row resistance level ({rowing_resistance_level})",
                build_frame(
                    cmd=CMD_PARAM_WRITE,
                    payload=build_set_rowing_resistance_level_payload(rowing_resistance_level),
                    seq=self._next_sequence(),
                ),
            ),
            (
                f"set Row simulated wear ({rowing_simulated_wear_level})",
                build_frame(
                    cmd=CMD_PARAM_WRITE,
                    payload=build_set_rowing_simulated_wear_level_payload(rowing_simulated_wear_level),
                    seq=self._next_sequence(),
                ),
            ),
            (
                "enter Row Mode",
                build_frame(
                    cmd=CMD_PARAM_WRITE,
                    payload=build_enter_row_payload(),
                    seq=self._next_sequence(),
                ),
            ),
            (
                "refresh Row monitor stream",
                build_frame(
                    cmd=CMD_TELEMETRY,
                    payload=bytes((0x13, 0x01)),
                    seq=self._next_sequence(),
                ),
            ),
        ]
        frames.extend(self._build_chunked_param_read_frames(MODE_FEATURE_STATUS_PARAMS, "read Row mode feature state"))
        await self._async_write_frames(frames)
        self._extend_isometric_vendor_refresh_burst(ROW_VENDOR_REFRESH_BURST_SECONDS)

    async def async_start_row(self, target_meters: int | None = None) -> None:
        self._require_control_ready("Rowing is not ready yet.")
        resolved_target = self._state.rowing_target_meters if target_meters is None else target_meters
        if resolved_target not in (None, 50, 100, 500, 1000, 2000, 5000):
            raise VoltraApiError(f"Unsupported Row target distance: {resolved_target}")
        if self._state.workout_state != WORKOUT_STATE_ROWING:
            await self.async_enter_row_mode()

        start_millis = int(time.time() * 1000)
        row_target_label = "Just Row" if resolved_target is None else f"{resolved_target} m row"
        self._push_state(
            replace(
                self._state,
                workout_mode="Rowing, Live",
                workout_state=WORKOUT_STATE_ROWING,
                fitness_mode=FITNESS_MODE_ROWING_ACTIVE,
                can_load=False,
                safety_reasons=(f"{row_target_label} is live.",),
                load_engaged=True,
                ready=False,
                rowing_target_meters=resolved_target,
                rowing_distance_meters=None,
                rowing_elapsed_millis=None,
                rowing_pace_500_millis=None,
                rowing_average_pace_500_millis=None,
                rowing_stroke_rate_spm=None,
                rowing_drive_force_lb=None,
                rowing_telemetry_start_millis=start_millis,
                rowing_last_stroke_start_millis=None,
                rowing_distance_samples_meters=(),
                rowing_force_samples_lb=(),
                rowing_force_last_chunk_index=None,
                app_current_screen_id=ROWING_SCREEN_ID,
                fitness_ongoing_ui=ROWING_ONGOING_UI,
                set_count=0,
                rep_count=0,
                rep_phase="Ready",
            ),
        )
        frames = [
            (
                "trigger Row start screen action",
                build_frame(
                    cmd=CMD_PARAM_WRITE,
                    payload=build_trigger_row_start_screen_payload(resolved_target),
                    seq=self._next_sequence(),
                ),
            ),
            (
                "refresh Row monitor stream",
                build_frame(
                    cmd=CMD_TELEMETRY,
                    payload=bytes((0x13, 0x01)),
                    seq=self._next_sequence(),
                ),
            ),
        ]
        frames.extend(self._build_chunked_param_read_frames(MODE_FEATURE_STATUS_PARAMS, "read Row mode feature state"))
        await self._async_write_frames(frames)
        self._extend_isometric_vendor_refresh_burst(ROW_VENDOR_REFRESH_BURST_SECONDS)

    async def async_set_rowing_resistance_level(self, value: float) -> None:
        self._require_control_ready("Row resistance is not ready yet.")
        normalized = self._clamp_round(value, MIN_ROWING_SELECTOR_LEVEL, MAX_ROWING_SELECTOR_LEVEL)
        self._push_state(replace(self._state, rowing_resistance_level=normalized))
        await self._async_send_param_write(
            param_id=PARAM_FITNESS_ROWING_DAMPER_RATIO_IDX,
            value=bytes((rowing_selector_wire_index(normalized),)),
            label=f"set Row resistance level ({normalized})",
        )

    async def async_set_rowing_simulated_wear_level(self, value: float) -> None:
        self._require_control_ready("Row simulated wear is not ready yet.")
        normalized = self._clamp_round(value, MIN_ROWING_SELECTOR_LEVEL, MAX_ROWING_SELECTOR_LEVEL)
        self._push_state(replace(self._state, rowing_simulated_wear_level=normalized))
        await self._async_send_param_write(
            param_id=PARAM_EP_ROW_CHAIN_GEAR,
            value=bytes((rowing_selector_wire_index(normalized),)),
            label=f"set Row simulated wear ({normalized})",
        )

    async def async_apply_custom_curve(self) -> None:
        await self._async_queue_custom_curve_mode()

    async def async_enter_custom_curve_mode(self) -> None:
        await self._async_queue_custom_curve_mode()

    async def _async_queue_custom_curve_mode(self) -> None:
        self._require_control_ready("Custom Curve is not ready yet.")
        points = tuple(float(point) for point in self._state.custom_curve_points)
        resistance_min_lb = self._state.custom_curve_resistance_min_lb or DEFAULT_CUSTOM_CURVE_RESISTANCE_MIN_LB
        resistance_limit_lb = self._state.custom_curve_resistance_limit_lb or DEFAULT_CUSTOM_CURVE_RESISTANCE_LIMIT_LB
        range_of_motion_in = self._state.custom_curve_range_of_motion_in or DEFAULT_CUSTOM_CURVE_RANGE_OF_MOTION_IN
        try:
            vendor_payload = build_custom_curve_vendor_preset_payload(
                points=points,
                resistance_min_lb=resistance_min_lb,
                resistance_limit_lb=resistance_limit_lb,
                range_of_motion_in=range_of_motion_in,
            )
        except ValueError as err:
            raise VoltraApiError(str(err)) from err

        self._push_state(
            replace(
                self._state,
                workout_mode="Custom Curve, Ready",
                workout_state=WORKOUT_STATE_CUSTOM_CURVE,
                fitness_mode=FITNESS_MODE_STRENGTH_READY,
                can_load=True,
                safety_reasons=("Ready for current mode load.",),
                load_engaged=False,
                ready=True,
                custom_curve_points=points,
                custom_curve_resistance_min_lb=resistance_min_lb,
                custom_curve_resistance_limit_lb=resistance_limit_lb,
                custom_curve_range_of_motion_in=range_of_motion_in,
                force_lb=None,
                rowing_distance_meters=None,
                rowing_elapsed_millis=None,
                rowing_pace_500_millis=None,
                rowing_average_pace_500_millis=None,
                rowing_stroke_rate_spm=None,
                rowing_drive_force_lb=None,
                rowing_telemetry_start_millis=None,
                rowing_last_stroke_start_millis=None,
                rowing_distance_samples_meters=(),
                rowing_force_samples_lb=(),
                rowing_force_last_chunk_index=None,
                app_current_screen_id=None,
                fitness_ongoing_ui=None,
                set_count=0,
                rep_count=0,
                rep_phase="Ready",
            ),
        )
        frames: list[tuple[str, bytes]] = [
            (
                "subscribe Custom Curve fitness data stream",
                build_frame(
                    cmd=CMD_PARAM_WRITE,
                    payload=build_set_fitness_data_notify_subscribe_payload(),
                    seq=self._next_sequence(),
                ),
            ),
            (
                "bulk subscribe Custom Curve params",
                build_frame(
                    cmd=CMD_BULK_PARAM_WRITE,
                    payload=build_custom_curve_bulk_subscribe_payload(),
                    seq=self._next_sequence(),
                ),
            ),
            (
                "set Custom Curve fitness data notify hz",
                build_frame(
                    cmd=CMD_PARAM_WRITE,
                    payload=build_set_fitness_data_notify_hz_payload(),
                    seq=self._next_sequence(),
                ),
            ),
            (
                f"set Custom Curve resistance min ({resistance_min_lb} lb)",
                build_param_write_frame(PARAM_BP_BASE_WEIGHT, encode_uint16_le(resistance_min_lb), self._next_sequence()),
            ),
            (
                "upload Custom Curve",
                build_frame(
                    cmd=CMD_TELEMETRY,
                    payload=vendor_payload,
                    seq=self._next_sequence(),
                ),
            ),
            (
                "enter Custom Curve",
                build_frame(
                    cmd=CMD_PARAM_WRITE,
                    payload=build_enter_custom_curve_payload(),
                    seq=self._next_sequence(),
                ),
            ),
        ]
        frames.extend(self._build_chunked_param_read_frames(MODE_FEATURE_STATUS_PARAMS, "read Custom Curve mode feature state"))
        await self._async_write_frames(frames)

    async def async_enter_damper_mode(self) -> None:
        await self._async_send_param_write(
            param_id=PARAM_FITNESS_WORKOUT_STATE,
            value=bytes((WORKOUT_STATE_DAMPER,)),
            label="enter Damper mode",
        )

    async def async_enter_isokinetic_mode(self) -> None:
        await self._async_send_param_write(
            param_id=PARAM_FITNESS_WORKOUT_STATE,
            value=bytes((WORKOUT_STATE_ISOKINETIC,)),
            label="enter Isokinetic mode",
        )

    async def async_enter_isometric_mode(self) -> None:
        self._isometric_vendor_refresh_until = 0.0
        await self._async_send_param_write(
            param_id=PARAM_FITNESS_WORKOUT_STATE,
            value=bytes((WORKOUT_STATE_ISOMETRIC,)),
            label="enter Isometric Test",
        )

    async def async_set_damper_level(self, value: float) -> None:
        self._require_workout_state(WORKOUT_STATE_DAMPER, "Damper")
        await self._async_send_param_write(
            param_id=PARAM_FITNESS_DAMPER_RATIO_IDX,
            value=bytes((self._clamp_round(value, 0, 9),)),
            label="set Damper level",
        )

    async def async_set_resistance_band_force(self, value: float) -> None:
        self._require_workout_state(WORKOUT_STATE_RESISTANCE_BAND, "Resistance Band")
        await self._async_send_param_write(
            param_id=PARAM_RESISTANCE_BAND_MAX_FORCE,
            value=encode_uint16_le(
                self._clamp_round(value, MIN_RESISTANCE_BAND_FORCE_LB, MAX_RESISTANCE_BAND_FORCE_LB),
            ),
            label="set Resistance Band force",
        )

    async def async_set_resistance_band_length(self, value: float) -> None:
        self._require_workout_state(WORKOUT_STATE_RESISTANCE_BAND, "Resistance Band")
        await self._async_send_param_write(
            param_id=PARAM_RESISTANCE_BAND_LEN,
            value=encode_uint16_le(
                self._clamp_round(value, MIN_RESISTANCE_BAND_LENGTH_CM, MAX_RESISTANCE_BAND_LENGTH_CM),
            ),
            label="set Resistance Band length",
        )

    async def async_set_isokinetic_menu(self, option: str) -> None:
        self._require_workout_state(WORKOUT_STATE_ISOKINETIC, "Isokinetic")
        value = (
            ISOKINETIC_MENU_CONSTANT_RESISTANCE
            if option == "Constant Resistance"
            else ISOKINETIC_MENU_ISOKINETIC
        )
        await self._async_send_param_write(
            param_id=PARAM_ISOKINETIC_ECC_MODE,
            value=bytes((value,)),
            label="set Isokinetic submenu",
        )

    async def async_set_isokinetic_target_speed(self, value: float) -> None:
        self._require_workout_state(WORKOUT_STATE_ISOKINETIC, "Isokinetic")
        await self._async_send_param_write(
            param_id=PARAM_EP_ISOKINETIC_TARGET_SPEED_MMS,
            value=encode_uint32_le(self._clamp_round(value, MIN_ISOKINETIC_SPEED_MMS, MAX_ISOKINETIC_SPEED_MMS)),
            label="set Isokinetic target speed",
        )

    async def async_set_isokinetic_speed_limit(self, value: float) -> None:
        self._require_workout_state(WORKOUT_STATE_ISOKINETIC, "Isokinetic")
        normalized = AUTO_ISOKINETIC_SPEED_MMS if value <= 0 else self._clamp_round(
            value,
            MIN_ISOKINETIC_SPEED_MMS,
            MAX_ISOKINETIC_SPEED_MMS,
        )
        await self._async_send_param_write(
            param_id=PARAM_ISOKINETIC_ECC_SPEED_LIMIT,
            value=encode_uint16_le(normalized),
            label="set Isokinetic speed limit",
        )

    async def async_set_isokinetic_constant_resistance(self, value: float) -> None:
        self._require_workout_state(WORKOUT_STATE_ISOKINETIC, "Isokinetic")
        await self._async_send_param_write(
            param_id=PARAM_ISOKINETIC_ECC_CONST_WEIGHT,
            value=encode_uint16_le(
                self._clamp_round(
                    value,
                    MIN_ISOKINETIC_CONSTANT_RESISTANCE_LB,
                    MAX_ISOKINETIC_CONSTANT_RESISTANCE_LB,
                ),
            ),
            label="set constant resistance",
        )

    async def async_set_isokinetic_max_eccentric_load(self, value: float) -> None:
        self._require_workout_state(WORKOUT_STATE_ISOKINETIC, "Isokinetic")
        await self._async_send_param_write(
            param_id=PARAM_ISOKINETIC_ECC_OVERLOAD_WEIGHT,
            value=encode_uint16_le(
                self._clamp_round(
                    value,
                    MIN_ISOKINETIC_MAX_ECCENTRIC_LOAD_LB,
                    MAX_ISOKINETIC_MAX_ECCENTRIC_LOAD_LB,
                ),
            ),
            label="set max eccentric load",
        )

    async def async_set_cable_offset(self, value: float) -> None:
        await self._async_send_param_write(
            param_id=PARAM_MC_DEFAULT_OFFLEN_CM,
            value=encode_uint16_le(self._clamp_round(value, MIN_CABLE_OFFSET_CM, MAX_CABLE_OFFSET_CM)),
            label="set cable offset",
        )

    async def async_trigger_cable_length_mode(self) -> None:
        self._require_active_workout("open Cable Length")
        await self._async_send_param_write(
            param_id=PARAM_EP_SCR_SWITCH,
            value=bytes((0x00, 0x10, 0x00, 0x01)),
            label="trigger cable length mode",
        )

    async def async_set_strength_mode(self) -> None:
        await self._async_send_param_writes(
            [
                ("enter Weight Training", PARAM_FITNESS_WORKOUT_STATE, bytes((WORKOUT_STATE_ACTIVE,))),
                (
                    "set strength mode",
                    PARAM_BP_SET_FITNESS_MODE,
                    encode_uint16_le(FITNESS_MODE_STRENGTH_READY),
                ),
            ],
        )

    async def async_exit_workout(self) -> None:
        await self._async_send_param_write(
            param_id=PARAM_FITNESS_WORKOUT_STATE,
            value=bytes((WORKOUT_STATE_INACTIVE,)),
            label="exit workout",
        )

    async def async_load(self) -> None:
        self._require_control_ready("Load is unavailable")
        if not self._state.can_load:
            raise VoltraApiError("; ".join(self._state.safety_reasons))
        if self._state.workout_state == WORKOUT_STATE_ROWING:
            await self.async_start_row(self._state.rowing_target_meters)
            return
        if self._state.workout_state == WORKOUT_STATE_ISOMETRIC:
            self._extend_isometric_vendor_refresh_burst()
            await self._async_write_frames(
                [
                    (
                        "read Isometric cable position",
                        build_param_read_frame(
                            (PARAM_MC_DEFAULT_OFFLEN_CM, PARAM_BP_RUNTIME_POSITION_CM),
                            self._next_sequence(),
                        ),
                    ),
                    (
                        "arm Isometric Test",
                        build_param_write_frame(
                            PARAM_BP_SET_FITNESS_MODE,
                            encode_uint16_le(FITNESS_MODE_ISOMETRIC_ARMED),
                            self._next_sequence(),
                        ),
                    ),
                    (
                        "refresh Isometric vendor state stream",
                        build_vendor_state_refresh_frame(self._next_sequence()),
                    ),
                ],
            )
            return
        if self._state.workout_state == WORKOUT_STATE_CUSTOM_CURVE:
            await self._async_write_frames(
                [
                    (
                        "read Custom Curve cable position",
                        build_param_read_frame(
                            (PARAM_MC_DEFAULT_OFFLEN_CM, PARAM_BP_RUNTIME_POSITION_CM),
                            self._next_sequence(),
                        ),
                    ),
                    (
                        "load Custom Curve",
                        build_param_write_frame(
                            PARAM_BP_SET_FITNESS_MODE,
                            encode_uint16_le(FITNESS_MODE_STRENGTH_LOADED),
                            self._next_sequence(),
                        ),
                    ),
                    (
                        "refresh Custom Curve vendor state stream",
                        build_vendor_state_refresh_frame(self._next_sequence()),
                    ),
                ],
            )
            return
        writes: list[tuple[str, int, bytes]] = []
        if self._state.workout_state in (None, WORKOUT_STATE_INACTIVE):
            writes.append(
                ("re-enter Weight Training", PARAM_FITNESS_WORKOUT_STATE, bytes((WORKOUT_STATE_ACTIVE,))),
            )
        writes.append(
            ("load", PARAM_BP_SET_FITNESS_MODE, encode_uint16_le(FITNESS_MODE_STRENGTH_LOADED)),
        )
        await self._async_send_param_writes(writes)

    async def async_unload(self) -> None:
        self._isometric_vendor_refresh_until = 0.0
        if self._state.workout_state == WORKOUT_STATE_ROWING or bool(self._state.workout_mode and self._state.workout_mode.startswith("Rowing")):
            self._push_state(
                replace(
                    self._state,
                    workout_mode="Rowing, Ready",
                    workout_state=WORKOUT_STATE_ROWING,
                    fitness_mode=FITNESS_MODE_STRENGTH_READY,
                    can_load=True,
                    safety_reasons=("Rowing is ready. Start Row again before another row.",),
                    load_engaged=False,
                    ready=True,
                    rowing_telemetry_start_millis=None,
                    rowing_last_stroke_start_millis=None,
                    rowing_drive_force_lb=None,
                    rep_phase="Ready",
                ),
            )
        elif self._state.workout_state == WORKOUT_STATE_CUSTOM_CURVE or bool(self._state.workout_mode and self._state.workout_mode.startswith("Custom Curve")):
            self._push_state(
                replace(
                    self._state,
                    workout_mode="Custom Curve, Ready",
                    workout_state=WORKOUT_STATE_CUSTOM_CURVE,
                    fitness_mode=FITNESS_MODE_STRENGTH_READY,
                    can_load=True,
                    safety_reasons=("Ready for current mode load.",),
                    load_engaged=False,
                    ready=True,
                    force_lb=None,
                    rep_phase="Ready",
                ),
            )
        await self._async_send_param_write(
            param_id=PARAM_BP_SET_FITNESS_MODE,
            value=encode_uint16_le(FITNESS_MODE_STRENGTH_READY),
            label="unload",
        )

    async def _run(self) -> None:
        retry_delay = CONNECT_RETRY_BASE_DELAY_SECONDS
        while not self._stop_event.is_set():
            try:
                await self._async_connect()
                retry_delay = CONNECT_RETRY_BASE_DELAY_SECONDS
                while not self._stop_event.is_set():
                    interval = self._background_refresh_interval()
                    try:
                        await asyncio.wait_for(self._disconnect_event.wait(), timeout=interval)
                        break
                    except TimeoutError:
                        if self._stop_event.is_set():
                            break
                        try:
                            if self._should_run_isometric_vendor_refresh():
                                await self._async_send_isometric_vendor_refresh()
                            elif not self._state.protocol_validated:
                                await self.async_refresh_status()
                        except VoltraApiError as err:
                            _LOGGER.debug("VOLTRA refresh skipped: %s", err)
                        except BleakError as err:
                            if self._client is None or not self._client.is_connected or self._disconnect_event.is_set():
                                raise
                            _LOGGER.debug(
                                "VOLTRA background exchange failed without disconnect for %s: %s",
                                self._address,
                                err,
                            )
                            self._push_state(
                                replace(
                                    self._state,
                                    last_error=str(err),
                                    status_message=f"VOLTRA background exchange failed: {err}",
                                ),
                            )
            except asyncio.CancelledError:
                raise
            except Exception as err:  # noqa: BLE001
                _LOGGER.warning("VOLTRA connect loop error for %s: %s", self._address, err)
                self._push_state(
                    replace(
                        self._state,
                        available=False,
                        connected=False,
                        protocol_validated=False,
                        last_error=str(err),
                        status_message=f"Reconnect failed: {err}",
                    ),
                )
            finally:
                await self._async_disconnect_internal()

            if self._stop_event.is_set():
                break

            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=retry_delay)
            except TimeoutError:
                retry_delay = min(retry_delay * 2, CONNECT_RETRY_MAX_DELAY_SECONDS)

    async def _async_connect(self) -> None:
        self._disconnect_event = asyncio.Event()
        self._clear_notification_queue()
        ble_device = bluetooth.async_ble_device_from_address(
            self._hass,
            self._address,
            connectable=True,
        )
        if ble_device is None:
            raise VoltraApiError(
                "VOLTRA is not currently reachable from a connectable Bluetooth adapter."
            )
        self._push_state(
            replace(
                self._state,
                available=False,
                connected=False,
                protocol_validated=False,
                last_error=None,
                status_message="Connecting to VOLTRA over Bluetooth.",
            ),
        )
        client = await self._async_establish_connection(ble_device)
        self._client = client
        self._connection_epoch += 1
        connection_epoch = self._connection_epoch
        self._command_characteristic = client.services.get_characteristic(
            VOLTRA_COMMAND_CHARACTERISTIC_UUID,
        )
        self._transport_characteristic = client.services.get_characteristic(
            VOLTRA_TRANSPORT_CHARACTERISTIC_UUID,
        )
        self._assemblers.clear()
        for characteristic_uuid in NOTIFY_CHARACTERISTIC_UUIDS:
            try:
                characteristic = client.services.get_characteristic(characteristic_uuid) or characteristic_uuid
                await client.start_notify(
                    characteristic,
                    lambda c, d, epoch=connection_epoch: self._notification_handler(epoch, c, d),
                )
            except BleakError as err:
                _LOGGER.debug("VOLTRA start_notify failed for %s: %s", characteristic_uuid, err)

        self._push_state(
            replace(
                self._state,
                available=True,
                connected=True,
                protocol_validated=False,
                last_error=None,
                status_message="Connected. Sending VOLTRA bootstrap.",
            ),
        )
        await self._async_send_bootstrap()

    async def _async_establish_connection(self, ble_device: Any) -> BleakClient:
        if establish_connection is not None:
            return await establish_connection(
                BleakClientWithServiceCache,
                ble_device,
                ble_device.name or self._configured_name or "Beyond Power Voltra",
                disconnected_callback=self._handle_disconnect,
                max_attempts=3,
            )

        client = BleakClient(ble_device, disconnected_callback=self._handle_disconnect)
        await client.connect(timeout=10.0)
        return client

    async def _async_send_bootstrap(self) -> None:
        frames = [(packet.label, packet.frame) for packet in OFFICIAL_BOOTSTRAP_PACKETS[:-1]]
        frames.extend(
            self._build_chunked_param_read_frames(
                MODE_FEATURE_STATUS_PARAMS,
                "read mode feature state",
            ),
        )
        await self._async_write_frames(frames)

    async def _async_send_param_write(
        self,
        *,
        param_id: int,
        value: bytes,
        label: str,
    ) -> None:
        await self._async_send_param_writes([(label, param_id, value)])

    async def _async_send_param_writes(
        self,
        writes: list[tuple[str, int, bytes]],
    ) -> None:
        self._require_control_ready("VOLTRA control is not ready yet")
        frames: list[tuple[str, bytes]] = []
        for label, param_id, value in writes:
            frames.append((label, build_param_write_frame(param_id, value, self._next_sequence())))
        frames.extend(
            self._build_chunked_param_read_frames(
                MODE_FEATURE_STATUS_PARAMS,
                "read back mode feature state",
            ),
        )
        await self._async_write_frames(frames)

    async def _async_write_frames(self, frames: list[tuple[str, bytes]]) -> None:
        self._require_connected()
        async with self._write_lock:
            for index, (label, frame) in enumerate(frames):
                await self._async_write_frame_locked(label, frame)
                if index < len(frames) - 1:
                    await asyncio.sleep(BOOTSTRAP_WRITE_PACING_SECONDS)

    async def _async_write_startup_image_frames(
        self,
        frames: list[tuple[str, bytes, int | None]],
        chunk_count: int,
    ) -> None:
        self._require_connected()
        async with self._write_lock:
            for index, (label, frame, chunk_index) in enumerate(frames):
                if chunk_index is None:
                    status = f"Writing {label}."
                elif chunk_index == 1 or chunk_index == chunk_count or chunk_index % 10 == 0:
                    status = f"Writing startup image chunk {chunk_index}/{chunk_count}."
                else:
                    status = None
                if status is not None:
                    self._push_state(
                        replace(
                            self._state,
                            startup_image_upload_status="uploading",
                            status_message=status,
                        ),
                    )
                await self._async_write_frame_to_characteristic_locked(
                    label=label,
                    frame=frame,
                    characteristic=self._transport_characteristic or VOLTRA_TRANSPORT_CHARACTERISTIC_UUID,
                    update_status=False,
                )
                if index < len(frames) - 1:
                    await asyncio.sleep(BOOTSTRAP_WRITE_PACING_SECONDS)
        self._push_state(
            replace(
                self._state,
                startup_image_upload_status="sent",
                status_message="Startup image upload sent. Waiting for VOLTRA apply acknowledgement.",
            ),
        )

    async def _async_write_frame_locked(self, label: str, frame: bytes) -> None:
        await self._async_write_frame_to_characteristic_locked(
            label=label,
            frame=frame,
            characteristic=self._transport_characteristic or VOLTRA_TRANSPORT_CHARACTERISTIC_UUID,
        )

    async def _async_write_frame_to_characteristic_locked(
        self,
        *,
        label: str,
        frame: bytes,
        characteristic: Any,
        update_status: bool = True,
    ) -> None:
        self._require_connected()
        assert self._client is not None
        if update_status:
            self._push_state(replace(self._state, status_message=f"Writing {label}."))
        await self._client.write_gatt_char(
            characteristic,
            frame,
            response=self._characteristic_supports_response(characteristic),
        )

    def _notification_handler(
        self,
        connection_epoch: int,
        characteristic: BleakGATTCharacteristic,
        data: bytearray,
    ) -> None:
        if self._stop_event.is_set():
            return
        characteristic_uuid = str(characteristic.uuid).lower()
        payload = bytes(data)
        self._hass.loop.call_soon_threadsafe(
            self._enqueue_notification,
            connection_epoch,
            characteristic_uuid,
            payload,
        )

    async def _async_process_notification(self, characteristic_uuid: str, data: bytes) -> None:
        assembler = self._assemblers.setdefault(characteristic_uuid, FrameAssembler())
        frames = assembler.accept(data)
        for frame in frames:
            startup_image_ack_code = parse_startup_image_ack_code(frame)
            next_state = apply_packet_to_state(self._state, frame)
            if startup_image_ack_code is not None:
                next_state = self._apply_startup_image_ack(next_state, startup_image_ack_code)
            if characteristic_uuid in CONFIRMED_RESPONSE_CHARACTERISTIC_UUIDS and next_state != self._state:
                next_state = replace(
                    next_state,
                    protocol_validated=True,
                    available=True,
                    connected=True,
                    status_message=(
                        next_state.status_message
                        if startup_image_ack_code is not None
                        else "VOLTRA protocol validated."
                    ),
                )
            elif next_state != self._state:
                next_state = replace(
                    next_state,
                    available=True,
                    connected=True,
                )
            self._push_state(next_state)

    def _handle_disconnect(self, _: BleakClient) -> None:
        self._hass.loop.call_soon_threadsafe(self._disconnect_event.set)
        self._hass.loop.call_soon_threadsafe(
            self._hass.async_create_task,
            self._async_mark_disconnected(),
        )

    async def _async_mark_disconnected(self) -> None:
        self._push_state(
            replace(
                self._state,
                available=False,
                connected=False,
                protocol_validated=False,
                status_message="VOLTRA disconnected. Reconnecting.",
            ),
        )

    def _apply_startup_image_ack(self, state: VoltraState, ack_code: int) -> VoltraState:
        if ack_code == 0x03:
            acked = (state.startup_image_upload_chunks_acked or 0) + 1
            total = state.startup_image_upload_chunks_total
            suffix = f"/{total}" if total is not None else ""
            return replace(
                state,
                startup_image_upload_status="acknowledging",
                startup_image_upload_chunks_acked=acked,
                startup_image_last_ack="chunk",
                status_message=f"VOLTRA acknowledged startup image chunk {acked}{suffix}.",
            )
        if ack_code == 0x04:
            return replace(
                state,
                startup_image_upload_status="finalized",
                startup_image_last_ack="finalize",
                status_message="VOLTRA acknowledged startup image finalize.",
            )
        if ack_code == 0x05:
            self._schedule_startup_image_post_apply_follow_up()
            return replace(
                state,
                startup_image_upload_status="accepted",
                startup_image_last_ack="apply",
                status_message="VOLTRA accepted startup image transfer. Check the device for confirmation.",
            )
        return replace(
            state,
            startup_image_last_ack=f"0x{ack_code:02X}",
            status_message=f"VOLTRA sent startup image acknowledgement 0x{ack_code:02X}.",
        )

    def _schedule_startup_image_post_apply_follow_up(self) -> None:
        self._cancel_startup_image_state_polls()
        self._track_startup_image_task(
            self._async_startup_image_follow_up_write(
                "ensure startup image display remains enabled",
                build_param_write_frame(
                    PARAM_POWER_OFF_LOGO_EN,
                    bytes((0x01,)),
                    self._next_sequence(),
                ),
            ),
        )
        for delay, label in (
            (2.0, "read startup image state 2s after apply"),
            (8.0, "read startup image state 8s after apply"),
            (30.0, "read startup image state 30s after apply"),
        ):
            self._track_startup_image_task(self._async_delayed_startup_image_state_read(delay, label))

    def _track_startup_image_task(self, coro) -> None:
        task = self._hass.async_create_task(coro)
        self._startup_image_poll_tasks.add(task)
        task.add_done_callback(self._startup_image_poll_tasks.discard)

    async def _async_startup_image_follow_up_write(self, label: str, frame: bytes) -> None:
        try:
            await self._async_write_frames([(label, frame)])
        except (BleakError, VoltraApiError) as err:
            _LOGGER.debug("VOLTRA startup image follow-up write skipped for %s: %s", self._address, err)

    async def _async_delayed_startup_image_state_read(self, delay: float, label: str) -> None:
        try:
            await asyncio.sleep(delay)
            await self._async_write_frames(
                self._build_chunked_param_read_frames(
                    STARTUP_IMAGE_STATE_PARAMS,
                    label,
                ),
            )
        except (BleakError, VoltraApiError) as err:
            _LOGGER.debug("VOLTRA startup image state poll skipped for %s: %s", self._address, err)

    def _cancel_startup_image_state_polls(self) -> None:
        for task in tuple(self._startup_image_poll_tasks):
            task.cancel()
        self._startup_image_poll_tasks.clear()

    async def _async_disconnect_internal(self) -> None:
        client = self._client
        self._client = None
        self._connection_epoch += 1
        self._command_characteristic = None
        self._transport_characteristic = None
        self._isometric_vendor_refresh_until = 0.0
        self._cancel_startup_image_state_polls()
        self._clear_notification_queue()
        self._assemblers.clear()
        if client is None:
            return
        try:
            await client.disconnect()
        except BleakError:
            pass

    def _push_state(self, state: VoltraState) -> None:
        self._state = state
        self._update_callback(state)

    def _ensure_notification_processor(self) -> None:
        if self._notification_task is None or self._notification_task.done():
            self._notification_task = self._hass.async_create_task(self._async_notification_processor())

    async def _async_stop_notification_processor(self) -> None:
        task = self._notification_task
        self._notification_task = None
        self._clear_notification_queue()
        if task is None:
            return
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    def _enqueue_notification(
        self,
        connection_epoch: int,
        characteristic_uuid: str,
        payload: bytes,
    ) -> None:
        if self._stop_event.is_set():
            return
        self._notification_queue.put_nowait((connection_epoch, characteristic_uuid, payload))

    def _clear_notification_queue(self) -> None:
        while not self._notification_queue.empty():
            try:
                self._notification_queue.get_nowait()
                self._notification_queue.task_done()
            except asyncio.QueueEmpty:
                break

    async def _async_notification_processor(self) -> None:
        while True:
            connection_epoch, characteristic_uuid, payload = await self._notification_queue.get()
            try:
                if connection_epoch != self._connection_epoch:
                    continue
                await self._async_process_notification(characteristic_uuid, payload)
            except asyncio.CancelledError:
                raise
            except Exception as err:  # noqa: BLE001
                _LOGGER.debug(
                    "VOLTRA notification processing failed for %s on %s: %s",
                    self._address,
                    characteristic_uuid,
                    err,
                )
                self._push_state(
                    replace(
                        self._state,
                        last_error=str(err),
                        status_message=f"VOLTRA notification processing failed: {err}",
                    ),
                )
            finally:
                self._notification_queue.task_done()

    def _next_sequence(self) -> int:
        sequence = self._sequence
        self._sequence = (self._sequence + 1) & 0xFFFF
        return sequence

    def _background_refresh_interval(self) -> float:
        if self._should_run_isometric_vendor_refresh():
            return ISOMETRIC_VENDOR_REFRESH_INTERVAL_SECONDS
        if self._state.protocol_validated:
            return CONNECTED_IDLE_LOOP_INTERVAL_SECONDS
        return PROTOCOL_RETRY_INTERVAL_SECONDS

    def _should_run_isometric_vendor_refresh(self) -> bool:
        refresh_window_open = time.monotonic() < self._isometric_vendor_refresh_until
        row_monitor_active = (
            self._state.workout_state == WORKOUT_STATE_ROWING
            and bool(self._state.workout_mode and self._state.workout_mode.startswith("Rowing"))
            and refresh_window_open
        )
        return (
            self._state.connected
            and self._state.protocol_validated
            and (
                row_monitor_active
                or (
                    self._state.workout_state == WORKOUT_STATE_ISOMETRIC
                    and (
                        refresh_window_open
                        or self._state.load_engaged is True
                        or self._state.isometric_current_force_n is not None
                        or self._state.fitness_mode == FITNESS_MODE_TEST_SCREEN
                    )
                )
            )
        )

    def _extend_isometric_vendor_refresh_burst(self, duration: float = ISOMETRIC_VENDOR_REFRESH_BURST_SECONDS) -> None:
        self._isometric_vendor_refresh_until = max(
            self._isometric_vendor_refresh_until,
            time.monotonic() + duration,
        )

    async def _async_send_isometric_vendor_refresh(self) -> None:
        self._require_connected()
        async with self._write_lock:
            await self._async_write_frame_to_characteristic_locked(
                label="refresh Isometric vendor state stream",
                frame=build_vendor_state_refresh_frame(self._next_sequence()),
                characteristic=self._transport_characteristic or VOLTRA_TRANSPORT_CHARACTERISTIC_UUID,
                update_status=False,
            )

    @staticmethod
    def _characteristic_supports_response(characteristic: Any) -> bool:
        properties = {
            str(prop).lower()
            for prop in getattr(characteristic, "properties", [])
        }
        return (
            True
            if "write" in properties
            else False
            if "write-without-response" in properties or "write_no_response" in properties
            else True
        )

    def _build_chunked_param_read_frames(
        self,
        param_ids: tuple[int, ...] | list[int],
        label: str,
    ) -> list[tuple[str, bytes]]:
        normalized = tuple(param_ids)
        frames: list[tuple[str, bytes]] = []
        for index in range(0, len(normalized), PARAM_READ_FRAME_IDS_PER_CHUNK):
            chunk = normalized[index : index + PARAM_READ_FRAME_IDS_PER_CHUNK]
            chunk_number = index // PARAM_READ_FRAME_IDS_PER_CHUNK + 1
            chunk_label = label if len(normalized) <= PARAM_READ_FRAME_IDS_PER_CHUNK else f"{label} ({chunk_number})"
            frames.append((chunk_label, build_param_read_frame(chunk, self._next_sequence())))
        return frames

    def _require_connected(self) -> None:
        if self._client is None or not self._client.is_connected:
            raise VoltraApiError("VOLTRA is not connected.")

    def _require_control_ready(self, message: str) -> None:
        self._require_connected()
        if not self._state.protocol_validated:
            raise VoltraApiError(message)

    def _require_active_workout(self, label: str) -> None:
        self._require_control_ready(f"Cannot {label.lower()} until the protocol is validated.")
        if self._state.workout_state in (None, WORKOUT_STATE_INACTIVE):
            raise VoltraApiError(f"Enter a workout mode before trying to {label.lower()}.")

    def _require_workout_state(self, workout_state: int, workout_name: str) -> None:
        self._require_control_ready(f"{workout_name} control is not ready yet.")
        if self._state.workout_state != workout_state:
            raise VoltraApiError(f"Enter {workout_name} before changing that control.")

    def _require_strength_mode(self, label: str) -> None:
        self._require_control_ready(f"Cannot {label.lower()} yet.")
        if self._state.workout_state != WORKOUT_STATE_ACTIVE:
            raise VoltraApiError("Enter Weight Training before changing that control.")

    def _base_weight_for_strength_features(self) -> int:
        base_weight = self._state.weight_lb
        if base_weight is None:
            raise VoltraApiError("VOLTRA has not reported a base weight yet.")
        return self._clamp_round(base_weight, MIN_TARGET_LB, MAX_TARGET_LB)

    @staticmethod
    def _clamp_round(value: float, minimum: int, maximum: int) -> int:
        return max(minimum, min(maximum, round(value)))
