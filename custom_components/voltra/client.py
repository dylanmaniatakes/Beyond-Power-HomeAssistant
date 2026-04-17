from __future__ import annotations

import asyncio
from dataclasses import replace
import logging
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
    PERIODIC_REFRESH_INTERVAL_SECONDS,
    PROTOCOL_RETRY_INTERVAL_SECONDS,
    VOLTRA_TRANSPORT_CHARACTERISTIC_UUID,
)
from .models import VoltraState
from .protocol import (
    AUTO_ISOKINETIC_SPEED_MMS,
    BATTERY_STATUS_PARAMS,
    CMD_PARAM_READ,
    FITNESS_MODE_STRENGTH_LOADED,
    FITNESS_MODE_STRENGTH_READY,
    FrameAssembler,
    ISOKINETIC_MENU_CONSTANT_RESISTANCE,
    ISOKINETIC_MENU_ISOKINETIC,
    MAX_CABLE_OFFSET_CM,
    MAX_ECCENTRIC_WEIGHT_LB,
    MAX_EXTRA_WEIGHT_LB,
    MAX_ISOKINETIC_MAX_ECCENTRIC_LOAD_LB,
    MAX_ISOKINETIC_SPEED_MMS,
    MAX_ISOKINETIC_CONSTANT_RESISTANCE_LB,
    MAX_RESISTANCE_BAND_FORCE_LB,
    MAX_RESISTANCE_BAND_LENGTH_CM,
    MAX_TARGET_LB,
    MIN_CABLE_OFFSET_CM,
    MIN_ECCENTRIC_WEIGHT_LB,
    MIN_EXTRA_WEIGHT_LB,
    MIN_ISOKINETIC_MAX_ECCENTRIC_LOAD_LB,
    MIN_ISOKINETIC_SPEED_MMS,
    MIN_ISOKINETIC_CONSTANT_RESISTANCE_LB,
    MIN_RESISTANCE_BAND_FORCE_LB,
    MIN_RESISTANCE_BAND_LENGTH_CM,
    MIN_TARGET_LB,
    MODE_FEATURE_STATUS_PARAMS,
    OFFICIAL_BOOTSTRAP_PACKETS,
    PARAM_BP_BASE_WEIGHT,
    PARAM_BP_CHAINS_WEIGHT,
    PARAM_BP_ECCENTRIC_WEIGHT,
    PARAM_BP_SET_FITNESS_MODE,
    PARAM_EP_ISOKINETIC_TARGET_SPEED_MMS,
    PARAM_EP_RESISTANCE_BAND_INVERSE,
    PARAM_EP_SCR_SWITCH,
    PARAM_FITNESS_ASSIST_MODE,
    PARAM_FITNESS_DAMPER_RATIO_IDX,
    PARAM_FITNESS_INVERSE_CHAIN,
    PARAM_FITNESS_WORKOUT_STATE,
    PARAM_ISOKINETIC_ECC_CONST_WEIGHT,
    PARAM_ISOKINETIC_ECC_MODE,
    PARAM_ISOKINETIC_ECC_OVERLOAD_WEIGHT,
    PARAM_ISOKINETIC_ECC_SPEED_LIMIT,
    PARAM_MC_DEFAULT_OFFLEN_CM,
    PARAM_RESISTANCE_BAND_ALGORITHM,
    PARAM_RESISTANCE_BAND_LEN,
    PARAM_RESISTANCE_BAND_LEN_BY_ROM,
    PARAM_RESISTANCE_BAND_MAX_FORCE,
    PARAM_RESISTANCE_EXPERIENCE,
    STATUS_REFRESH_PARAMS,
    WORKOUT_STATE_ACTIVE,
    WORKOUT_STATE_DAMPER,
    WORKOUT_STATE_INACTIVE,
    WORKOUT_STATE_ISOKINETIC,
    WORKOUT_STATE_ISOMETRIC,
    WORKOUT_STATE_RESISTANCE_BAND,
    apply_packet_to_state,
    build_param_read_frame,
    build_param_write_frame,
    encode_int16_le,
    encode_uint16_le,
    encode_uint32_le,
    is_isokinetic_workout_state,
)

if TYPE_CHECKING:
    from bleak.backends.characteristic import BleakGATTCharacteristic
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)
PARAM_READ_FRAME_IDS_PER_CHUNK = 2


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
        self._transport_characteristic: Any = None
        self._runner_task: asyncio.Task[None] | None = None
        self._stop_event = asyncio.Event()
        self._disconnect_event = asyncio.Event()
        self._write_lock = asyncio.Lock()
        self._assemblers: dict[str, FrameAssembler] = {}
        self._sequence = 7

    @property
    def state(self) -> VoltraState:
        return self._state

    async def async_start(self) -> None:
        if self._runner_task is not None:
            return
        self._stop_event.clear()
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
        elif option == "Damper":
            await self.async_enter_damper_mode()
        elif option == "Isokinetic":
            await self.async_enter_isokinetic_mode()
        elif option == "Isometric Test":
            await self.async_enter_isometric_mode()
        else:
            raise VoltraApiError(f"Unsupported workout mode: {option}")

    async def async_set_target_load(self, value: float) -> None:
        await self._async_send_param_write(
            param_id=PARAM_BP_BASE_WEIGHT,
            value=encode_uint16_le(self._clamp_round(value, MIN_TARGET_LB, MAX_TARGET_LB)),
            label="set target load",
        )

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
        if self._state.workout_state == WORKOUT_STATE_ISOMETRIC:
            await self._async_send_param_write(
                param_id=PARAM_BP_SET_FITNESS_MODE,
                value=encode_uint16_le(FITNESS_MODE_STRENGTH_LOADED),
                label="load Isometric Test",
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
                    interval = (
                        PERIODIC_REFRESH_INTERVAL_SECONDS
                        if self._state.protocol_validated
                        else PROTOCOL_RETRY_INTERVAL_SECONDS
                    )
                    try:
                        await asyncio.wait_for(self._disconnect_event.wait(), timeout=interval)
                        break
                    except TimeoutError:
                        if self._stop_event.is_set():
                            break
                        try:
                            await self.async_refresh_status()
                        except VoltraApiError as err:
                            _LOGGER.debug("VOLTRA refresh skipped: %s", err)
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
        self._transport_characteristic = client.services.get_characteristic(
            VOLTRA_TRANSPORT_CHARACTERISTIC_UUID,
        )
        self._assemblers.clear()
        for characteristic_uuid in NOTIFY_CHARACTERISTIC_UUIDS:
            try:
                characteristic = client.services.get_characteristic(characteristic_uuid) or characteristic_uuid
                await client.start_notify(characteristic, self._notification_handler)
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

    async def _async_write_frame_locked(self, label: str, frame: bytes) -> None:
        self._require_connected()
        assert self._client is not None
        self._push_state(replace(self._state, status_message=f"Writing {label}."))
        characteristic = self._transport_characteristic or VOLTRA_TRANSPORT_CHARACTERISTIC_UUID
        properties = {
            str(prop).lower()
            for prop in getattr(characteristic, "properties", [])
        }
        response = (
            True
            if "write" in properties
            else False
            if "write-without-response" in properties or "write_no_response" in properties
            else True
        )
        await self._client.write_gatt_char(
            characteristic,
            frame,
            response=response,
        )

    def _notification_handler(
        self,
        characteristic: BleakGATTCharacteristic,
        data: bytearray,
    ) -> None:
        characteristic_uuid = str(characteristic.uuid).lower()
        self._hass.loop.call_soon_threadsafe(
            self._hass.async_create_task,
            self._async_process_notification(characteristic_uuid, bytes(data)),
        )

    async def _async_process_notification(self, characteristic_uuid: str, data: bytes) -> None:
        assembler = self._assemblers.setdefault(characteristic_uuid, FrameAssembler())
        frames = assembler.accept(data)
        for frame in frames:
            next_state = apply_packet_to_state(self._state, frame)
            if characteristic_uuid in CONFIRMED_RESPONSE_CHARACTERISTIC_UUIDS and next_state != self._state:
                next_state = replace(
                    next_state,
                    protocol_validated=True,
                    available=True,
                    connected=True,
                    status_message="VOLTRA protocol validated.",
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

    async def _async_disconnect_internal(self) -> None:
        client = self._client
        self._client = None
        self._transport_characteristic = None
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

    def _next_sequence(self) -> int:
        sequence = self._sequence
        self._sequence = (self._sequence + 1) & 0xFFFF
        return sequence

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
