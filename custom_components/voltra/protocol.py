from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from enum import Enum
import re

from .models import VoltraState

CMD_PARAM_READ = 0x0F
CMD_ASYNC_STATE = 0x10
CMD_PARAM_WRITE = 0x11
CMD_SERIAL_INFO = 0x19
CMD_HANDSHAKE_CHECK = 0x27
CMD_DEVICE_NAME = 0x4F
CMD_COMMON_STATE = 0x74
CMD_FIRMWARE_INFO = 0x77
CMD_DEVICE_STATE = 0xA7
CMD_TELEMETRY = 0xAA
CMD_ACTIVATION = 0xAB
CMD_ISOMETRIC_STREAM = 0xB4

APP_SENDER = 0xAA
DEVICE_RECEIVER = 0x10
PROTO = 0x0020

MIN_TARGET_LB = 5
MAX_TARGET_LB = 200
MIN_EXTRA_WEIGHT_LB = 0
MAX_EXTRA_WEIGHT_LB = 200
MIN_ECCENTRIC_WEIGHT_LB = -200
MAX_ECCENTRIC_WEIGHT_LB = 200
MIN_RESISTANCE_BAND_FORCE_LB = 15
MAX_RESISTANCE_BAND_FORCE_LB = 200
MIN_RESISTANCE_BAND_LENGTH_CM = 50
MAX_RESISTANCE_BAND_LENGTH_CM = 260
MIN_ISOKINETIC_CONSTANT_RESISTANCE_LB = 5
MAX_ISOKINETIC_CONSTANT_RESISTANCE_LB = 100
MIN_ISOKINETIC_MAX_ECCENTRIC_LOAD_LB = 5
MAX_ISOKINETIC_MAX_ECCENTRIC_LOAD_LB = 200
AUTO_ISOKINETIC_SPEED_MMS = 0
MIN_ISOKINETIC_SPEED_MMS = 100
MAX_ISOKINETIC_SPEED_MMS = 2000
MIN_CABLE_OFFSET_CM = 0
MAX_CABLE_OFFSET_CM = 260

PARAM_BP_RUNTIME_POSITION_CM = 0x3E82
PARAM_BP_RUNTIME_WIRE_WEIGHT_LBS = 0x3E83
PARAM_BP_BASE_WEIGHT = 0x3E86
PARAM_BP_CHAINS_WEIGHT = 0x3E87
PARAM_BP_ECCENTRIC_WEIGHT = 0x3E88
PARAM_BP_SET_FITNESS_MODE = 0x3E89
PARAM_BMS_RSOC_LEGACY = 0x1B5D
PARAM_BMS_RSOC = 0x4E2D
PARAM_FITNESS_WORKOUT_STATE = 0x4FB0
PARAM_FITNESS_DAMPER_RATIO_IDX = 0x5103
PARAM_FITNESS_ASSIST_MODE = 0x5106
PARAM_EP_SCR_SWITCH = 0x5165
PARAM_RESISTANCE_EXPERIENCE = 0x52CA
PARAM_EP_RESISTANCE_BAND_INVERSE = 0x52E3
PARAM_EP_ISOKINETIC_TARGET_SPEED_MMS = 0x5350
PARAM_RESISTANCE_BAND_ALGORITHM = 0x5361
PARAM_RESISTANCE_BAND_MAX_FORCE = 0x5362
PARAM_RESISTANCE_BAND_LEN_BY_ROM = 0x53B6
PARAM_RESISTANCE_BAND_LEN = 0x53B7
PARAM_FITNESS_INVERSE_CHAIN = 0x53B0
PARAM_WEIGHT_TRAINING_EXTRA_MODE = 0x53C6
PARAM_ISOMETRIC_MAX_DURATION = 0x53D2
PARAM_ISOKINETIC_ECC_MODE = 0x5410
PARAM_ISOKINETIC_ECC_SPEED_LIMIT = 0x5411
PARAM_ISOKINETIC_ECC_CONST_WEIGHT = 0x5412
PARAM_ISOKINETIC_ECC_OVERLOAD_WEIGHT = 0x5413
PARAM_ISOMETRIC_MAX_FORCE = 0x5431
PARAM_QUICK_CABLE_ADJUSTMENT = 0x54BC
PARAM_MC_DEFAULT_OFFLEN_CM = 0x506A

FITNESS_MODE_STRENGTH_READY = 0x0004
FITNESS_MODE_STRENGTH_LOADED = 0x0005
FITNESS_MODE_TEST_SCREEN = 0x0085

ISOKINETIC_MENU_ISOKINETIC = 0x00
ISOKINETIC_MENU_CONSTANT_RESISTANCE = 0x01

WORKOUT_STATE_INACTIVE = 0x00
WORKOUT_STATE_ACTIVE = 0x01
WORKOUT_STATE_RESISTANCE_BAND = 0x02
WORKOUT_STATE_DAMPER = 0x04
WORKOUT_STATE_ISOKINETIC = 0x07
WORKOUT_STATE_ISOMETRIC = 0x08

MODE_FEATURE_STATUS_PARAMS: tuple[int, ...] = (
    PARAM_BP_BASE_WEIGHT,
    PARAM_RESISTANCE_BAND_MAX_FORCE,
    PARAM_RESISTANCE_BAND_ALGORITHM,
    PARAM_RESISTANCE_BAND_LEN,
    PARAM_RESISTANCE_BAND_LEN_BY_ROM,
    PARAM_RESISTANCE_EXPERIENCE,
    PARAM_FITNESS_ASSIST_MODE,
    PARAM_EP_RESISTANCE_BAND_INVERSE,
    PARAM_FITNESS_DAMPER_RATIO_IDX,
    PARAM_ISOKINETIC_ECC_MODE,
    PARAM_EP_ISOKINETIC_TARGET_SPEED_MMS,
    PARAM_ISOKINETIC_ECC_SPEED_LIMIT,
    PARAM_ISOKINETIC_ECC_CONST_WEIGHT,
    PARAM_ISOKINETIC_ECC_OVERLOAD_WEIGHT,
    PARAM_ISOMETRIC_MAX_FORCE,
    PARAM_ISOMETRIC_MAX_DURATION,
    PARAM_BP_CHAINS_WEIGHT,
    PARAM_BP_ECCENTRIC_WEIGHT,
    PARAM_FITNESS_INVERSE_CHAIN,
    PARAM_WEIGHT_TRAINING_EXTRA_MODE,
    PARAM_BP_SET_FITNESS_MODE,
    PARAM_FITNESS_WORKOUT_STATE,
    PARAM_BP_RUNTIME_POSITION_CM,
    PARAM_MC_DEFAULT_OFFLEN_CM,
    PARAM_QUICK_CABLE_ADJUSTMENT,
)

BATTERY_STATUS_PARAMS: tuple[int, ...] = (
    PARAM_BMS_RSOC,
    PARAM_BMS_RSOC_LEGACY,
)

STATUS_REFRESH_PARAMS: tuple[int, ...] = BATTERY_STATUS_PARAMS + MODE_FEATURE_STATUS_PARAMS

LOW_BATTERY_THRESHOLD_PERCENT = 15
LB_TO_NEWTONS = 4.4482216152605

SERIAL_REGEX = re.compile(r"M?B[0-9A-Z]{10,}")
FIRMWARE_REGEX = re.compile(r"(?:EP|BP|MainControlv|MotorControl|BMS|PMU)[0-9A-Za-z.-]*\d+\.\d+")
PRINTABLE_ASCII_RANGE = range(32, 127)
MIN_PRINTABLE_SEGMENT_CHARS = 2


class ParamType(str, Enum):
    UINT8 = "uint8"
    UINT16 = "uint16"
    INT16 = "int16"
    UINT32 = "uint32"


@dataclass(frozen=True, slots=True)
class ParamDefinition:
    param_type: ParamType
    length: int


@dataclass(frozen=True, slots=True)
class ParsedVoltraPacket:
    declared_length: int
    total_length: int
    packet_type: int
    header_checksum: int
    sender_id: int
    receiver_id: int
    sequence: int
    channel: int
    protocol: int
    command_id: int
    payload: bytes
    crc16: int
    length_matches: bool


@dataclass(frozen=True, slots=True)
class BootstrapPacket:
    label: str
    frame: bytes


PARAM_REGISTRY: dict[int, ParamDefinition] = {
    PARAM_BMS_RSOC: ParamDefinition(ParamType.UINT8, 1),
    PARAM_BMS_RSOC_LEGACY: ParamDefinition(ParamType.UINT8, 1),
    PARAM_BP_RUNTIME_POSITION_CM: ParamDefinition(ParamType.INT16, 2),
    PARAM_BP_RUNTIME_WIRE_WEIGHT_LBS: ParamDefinition(ParamType.INT16, 2),
    PARAM_BP_BASE_WEIGHT: ParamDefinition(ParamType.UINT16, 2),
    PARAM_BP_CHAINS_WEIGHT: ParamDefinition(ParamType.UINT16, 2),
    PARAM_BP_ECCENTRIC_WEIGHT: ParamDefinition(ParamType.INT16, 2),
    PARAM_BP_SET_FITNESS_MODE: ParamDefinition(ParamType.UINT16, 2),
    PARAM_MC_DEFAULT_OFFLEN_CM: ParamDefinition(ParamType.UINT16, 2),
    PARAM_FITNESS_WORKOUT_STATE: ParamDefinition(ParamType.UINT8, 1),
    PARAM_FITNESS_DAMPER_RATIO_IDX: ParamDefinition(ParamType.UINT8, 1),
    PARAM_FITNESS_ASSIST_MODE: ParamDefinition(ParamType.UINT8, 1),
    PARAM_RESISTANCE_EXPERIENCE: ParamDefinition(ParamType.UINT8, 1),
    PARAM_EP_RESISTANCE_BAND_INVERSE: ParamDefinition(ParamType.UINT8, 1),
    PARAM_EP_ISOKINETIC_TARGET_SPEED_MMS: ParamDefinition(ParamType.UINT32, 4),
    PARAM_RESISTANCE_BAND_ALGORITHM: ParamDefinition(ParamType.UINT8, 1),
    PARAM_RESISTANCE_BAND_MAX_FORCE: ParamDefinition(ParamType.UINT16, 2),
    PARAM_RESISTANCE_BAND_LEN_BY_ROM: ParamDefinition(ParamType.UINT8, 1),
    PARAM_RESISTANCE_BAND_LEN: ParamDefinition(ParamType.UINT16, 2),
    PARAM_FITNESS_INVERSE_CHAIN: ParamDefinition(ParamType.UINT8, 1),
    PARAM_WEIGHT_TRAINING_EXTRA_MODE: ParamDefinition(ParamType.UINT8, 1),
    PARAM_ISOMETRIC_MAX_DURATION: ParamDefinition(ParamType.UINT16, 2),
    PARAM_ISOKINETIC_ECC_MODE: ParamDefinition(ParamType.UINT8, 1),
    PARAM_ISOKINETIC_ECC_SPEED_LIMIT: ParamDefinition(ParamType.UINT16, 2),
    PARAM_ISOKINETIC_ECC_CONST_WEIGHT: ParamDefinition(ParamType.UINT16, 2),
    PARAM_ISOKINETIC_ECC_OVERLOAD_WEIGHT: ParamDefinition(ParamType.UINT16, 2),
    PARAM_ISOMETRIC_MAX_FORCE: ParamDefinition(ParamType.UINT16, 2),
    PARAM_QUICK_CABLE_ADJUSTMENT: ParamDefinition(ParamType.UINT8, 1),
}


class FrameAssembler:
    def __init__(self) -> None:
        self._pending = b""

    def accept(self, fragment: bytes) -> list[bytes]:
        if not fragment:
            return []

        buffer = self._pending + fragment
        self._pending = b""
        frames: list[bytes] = []

        while buffer:
            if buffer[0] != 0x55:
                frames.append(buffer)
                return frames
            if len(buffer) < 3:
                self._pending = buffer
                return frames

            expected_length = expected_frame_length(buffer)
            if expected_length is None or expected_length < 13:
                frames.append(buffer)
                return frames
            if len(buffer) < expected_length:
                self._pending = buffer
                return frames

            frames.append(buffer[:expected_length])
            buffer = buffer[expected_length:]

        return frames

    def clear(self) -> None:
        self._pending = b""


def build_param_read_frame(param_ids: tuple[int, ...] | list[int], seq: int) -> bytes:
    return build_frame(
        cmd=CMD_PARAM_READ,
        payload=build_param_read_payload(param_ids),
        seq=seq,
    )


def build_param_write_frame(param_id: int, value_bytes: bytes, seq: int) -> bytes:
    return build_frame(
        cmd=CMD_PARAM_WRITE,
        payload=build_param_write_payload(param_id, value_bytes),
        seq=seq,
    )


def build_frame(
    *,
    cmd: int,
    payload: bytes,
    seq: int,
    sender: int = APP_SENDER,
    receiver: int = DEVICE_RECEIVER,
    proto: int = PROTO,
) -> bytes:
    length = 11 + len(payload) + 2
    if length > 0xFF:
        raise ValueError(f"VOLTRA frame is too large: {length} bytes")

    crc8_header = bytes((0x55, length, 0x04))
    body = bytearray(length - 2)
    body[0] = 0x55
    body[1] = length
    body[2] = 0x04
    body[3] = crc8(crc8_header)
    body[4] = sender & 0xFF
    body[5] = receiver & 0xFF
    body[6] = seq & 0xFF
    body[7] = (seq >> 8) & 0xFF
    body[8] = proto & 0xFF
    body[9] = (proto >> 8) & 0xFF
    body[10] = cmd & 0xFF
    body[11:] = payload

    crc = crc16(bytes(body))
    return bytes(body) + bytes((crc & 0xFF, (crc >> 8) & 0xFF))


def build_param_read_payload(param_ids: tuple[int, ...] | list[int]) -> bytes:
    normalized = tuple(param_ids)
    if not normalized:
        raise ValueError("At least one VOLTRA parameter id is required")
    return encode_uint16_le(len(normalized)) + b"".join(encode_uint16_le(param_id) for param_id in normalized)


def build_param_write_payload(param_id: int, value_bytes: bytes) -> bytes:
    return bytes((0x01, 0x00)) + encode_uint16_le(param_id) + value_bytes


def encode_uint16_le(value: int) -> bytes:
    return int(value).to_bytes(2, byteorder="little", signed=False)


def encode_int16_le(value: int) -> bytes:
    return int(value).to_bytes(2, byteorder="little", signed=True)


def encode_uint32_le(value: int) -> bytes:
    return int(value).to_bytes(4, byteorder="little", signed=False)


def crc8(data: bytes) -> int:
    crc = 0xEE
    for byte in data:
        crc ^= _reflect(byte, 8)
        for _ in range(8):
            if crc & 0x80:
                crc = ((crc << 1) ^ 0x31) & 0xFF
            else:
                crc = (crc << 1) & 0xFF
    return _reflect(crc, 8)


def crc16(data: bytes) -> int:
    crc = 0x496C
    for byte in data:
        crc ^= _reflect(byte, 8) << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return _reflect(crc, 16)


def _reflect(value: int, width: int) -> int:
    reflected = 0
    working = value
    for _ in range(width):
        reflected = (reflected << 1) | (working & 1)
        working >>= 1
    return reflected


OFFICIAL_BOOTSTRAP_PACKETS: tuple[BootstrapPacket, ...] = (
    BootstrapPacket(
        label="commonHandshake app hello",
        frame=bytes.fromhex("552904c90110000020004f69506164000000000000000000000000000000000084ab1a5f292001ea4f"),
    ),
    BootstrapPacket(
        label="commonConnectRequest",
        frame=bytes.fromhex("550f0801aad200002000ff00aa0419"),
    ),
    BootstrapPacket(
        label="handshake finish/check",
        frame=bytes.fromhex("551f044eaa10000020002781105eab9ef41c864ff5877a9c8c1d5f0d603e86"),
    ),
    BootstrapPacket(
        label="read common state",
        frame=bytes.fromhex("550d0433aa10000020007403bc"),
    ),
    BootstrapPacket(
        label="read firmware page 0",
        frame=bytes.fromhex("550e0466aa100100200077003889"),
    ),
    BootstrapPacket(
        label="read firmware page 1",
        frame=bytes.fromhex("550e0466aa10020020007701cc94"),
    ),
    BootstrapPacket(
        label="read serial page",
        frame=bytes.fromhex("550e0466aa100300200019002b7e"),
    ),
    BootstrapPacket(
        label="read activation/security page",
        frame=bytes.fromhex("550e0466aa1004002000ab01ad7a"),
    ),
    BootstrapPacket(
        label="read battery state",
        frame=build_param_read_frame(BATTERY_STATUS_PARAMS, seq=0x05),
    ),
    BootstrapPacket(
        label="read mode feature state",
        frame=build_param_read_frame(MODE_FEATURE_STATUS_PARAMS, seq=0x06),
    ),
)


def expected_frame_length(header: bytes) -> int | None:
    if len(header) < 3 or header[0] != 0x55:
        return None
    declared_length = header[1]
    packet_type = header[2]
    if packet_type == 0x09:
        return 0x100 + declared_length
    return declared_length


def parse_packet(frame: bytes) -> ParsedVoltraPacket | None:
    if len(frame) < 13 or frame[0] != 0x55:
        return None

    declared_length = frame[1]
    packet_type = frame[2]
    total_length = expected_frame_length(frame)
    if total_length is None:
        return None

    return ParsedVoltraPacket(
        declared_length=declared_length,
        total_length=total_length,
        packet_type=packet_type,
        header_checksum=frame[3],
        sender_id=frame[4],
        receiver_id=frame[5],
        sequence=frame[6],
        channel=frame[7],
        protocol=frame[8] | (frame[9] << 8),
        command_id=frame[10],
        payload=frame[11:-2],
        crc16=frame[-2] | (frame[-1] << 8),
        length_matches=len(frame) == total_length,
    )


def apply_packet_to_state(
    current: VoltraState,
    frame: bytes,
    *,
    now: datetime | None = None,
) -> VoltraState:
    packet = parse_packet(frame)
    if packet is None:
        return current

    timestamp = now or datetime.now(timezone.utc)
    params = decode_params(packet)
    printable_segments = printable_ascii_segments(packet.payload)

    serial_number = _first_regex_match(SERIAL_REGEX, printable_segments)
    firmware_parts = list(dict.fromkeys(_all_regex_matches(FIRMWARE_REGEX, printable_segments)))
    device_name = printable_segments[0] if packet.command_id == CMD_DEVICE_NAME and printable_segments else None

    battery_percent = _parse_battery(packet, params)
    activation_state = _parse_activation_state(packet)
    base_weight_lb = _get_uint16(params, PARAM_BP_BASE_WEIGHT)
    chains_weight_lb = _get_uint16(params, PARAM_BP_CHAINS_WEIGHT)
    eccentric_weight_lb = _get_int16(params, PARAM_BP_ECCENTRIC_WEIGHT)
    inverse_chains = _bool_from_uint8(_get_uint8(params, PARAM_FITNESS_INVERSE_CHAIN))
    wire_weight_lb = _get_int16(params, PARAM_BP_RUNTIME_WIRE_WEIGHT_LBS)
    cable_length_cm = _get_int16(params, PARAM_BP_RUNTIME_POSITION_CM)
    cable_offset_cm = _get_uint16(params, PARAM_MC_DEFAULT_OFFLEN_CM)
    resistance_band_max_force_lb = _get_uint16(params, PARAM_RESISTANCE_BAND_MAX_FORCE)
    resistance_band_length_cm = _get_uint16(params, PARAM_RESISTANCE_BAND_LEN)
    resistance_band_by_rom = _bool_from_uint8(_get_uint8(params, PARAM_RESISTANCE_BAND_LEN_BY_ROM))
    resistance_band_inverse = _bool_from_uint8(_get_uint8(params, PARAM_EP_RESISTANCE_BAND_INVERSE))
    resistance_band_curve_logarithm = _parse_band_curve(_get_uint8(params, PARAM_RESISTANCE_BAND_ALGORITHM))
    resistance_experience_intense = _parse_resistance_experience(_get_uint8(params, PARAM_RESISTANCE_EXPERIENCE))
    quick_cable_adjustment = _bool_from_uint8(_get_uint8(params, PARAM_QUICK_CABLE_ADJUSTMENT))
    damper_level_index = _get_uint8(params, PARAM_FITNESS_DAMPER_RATIO_IDX)
    assist_mode_enabled = _parse_assist_mode(_get_uint8(params, PARAM_FITNESS_ASSIST_MODE))
    weight_training_extra_mode = _get_uint8(params, PARAM_WEIGHT_TRAINING_EXTRA_MODE)
    isokinetic_mode = _get_uint8(params, PARAM_ISOKINETIC_ECC_MODE)
    isokinetic_target_speed_mms = _get_uint32(params, PARAM_EP_ISOKINETIC_TARGET_SPEED_MMS)
    isokinetic_speed_limit_mms = _get_uint16(params, PARAM_ISOKINETIC_ECC_SPEED_LIMIT)
    isokinetic_constant_resistance_lb = _get_uint16(params, PARAM_ISOKINETIC_ECC_CONST_WEIGHT)
    isokinetic_max_eccentric_load_lb = _get_uint16(params, PARAM_ISOKINETIC_ECC_OVERLOAD_WEIGHT)
    isometric_max_force_lb = _get_uint16(params, PARAM_ISOMETRIC_MAX_FORCE)
    isometric_max_duration_seconds = _get_uint16(params, PARAM_ISOMETRIC_MAX_DURATION)
    fitness_mode = _get_uint16(params, PARAM_BP_SET_FITNESS_MODE)
    workout_state = _get_uint8(params, PARAM_FITNESS_WORKOUT_STATE)
    rep_telemetry = _parse_rep_telemetry(packet)
    isometric_telemetry = _parse_isometric_telemetry(packet, current, timestamp)
    workout_mode = workout_mode_label(fitness_mode, workout_state)

    leaving_isometric = workout_state is not None and workout_state != WORKOUT_STATE_ISOMETRIC

    next_state = replace(
        current,
        device_name=device_name or current.device_name,
        last_updated=timestamp,
        battery_percent=battery_percent if battery_percent is not None else current.battery_percent,
        firmware_version=_merge_firmware_parts(current.firmware_version, firmware_parts),
        serial_number=serial_number or current.serial_number,
        activation_state=activation_state or current.activation_state,
        cable_length_cm=_coalesce_float(cable_length_cm, current.cable_length_cm),
        cable_offset_cm=_coalesce_float(cable_offset_cm, current.cable_offset_cm),
        force_lb=_coalesce_float(wire_weight_lb, current.force_lb),
        weight_lb=_coalesce_float(base_weight_lb, current.weight_lb),
        resistance_band_max_force_lb=_coalesce_float(resistance_band_max_force_lb, current.resistance_band_max_force_lb),
        resistance_band_length_cm=_coalesce_float(resistance_band_length_cm, current.resistance_band_length_cm),
        resistance_band_by_range_of_motion=(
            resistance_band_by_rom
            if resistance_band_by_rom is not None
            else current.resistance_band_by_range_of_motion
        ),
        resistance_band_inverse=(
            resistance_band_inverse
            if resistance_band_inverse is not None
            else current.resistance_band_inverse
        ),
        resistance_band_curve_logarithm=(
            resistance_band_curve_logarithm
            if resistance_band_curve_logarithm is not None
            else current.resistance_band_curve_logarithm
        ),
        resistance_experience_intense=(
            resistance_experience_intense
            if resistance_experience_intense is not None
            else current.resistance_experience_intense
        ),
        quick_cable_adjustment=(
            quick_cable_adjustment
            if quick_cable_adjustment is not None
            else current.quick_cable_adjustment
        ),
        damper_level_index=damper_level_index if damper_level_index is not None else current.damper_level_index,
        assist_mode_enabled=assist_mode_enabled if assist_mode_enabled is not None else current.assist_mode_enabled,
        chains_weight_lb=_coalesce_float(chains_weight_lb, current.chains_weight_lb),
        eccentric_weight_lb=_coalesce_float(eccentric_weight_lb, current.eccentric_weight_lb),
        inverse_chains=inverse_chains if inverse_chains is not None else current.inverse_chains,
        weight_training_extra_mode=(
            weight_training_extra_mode
            if weight_training_extra_mode is not None
            else current.weight_training_extra_mode
        ),
        isokinetic_mode=isokinetic_mode if isokinetic_mode is not None else current.isokinetic_mode,
        isokinetic_target_speed_mms=(
            isokinetic_target_speed_mms
            if isokinetic_target_speed_mms is not None
            else current.isokinetic_target_speed_mms
        ),
        isokinetic_speed_limit_mms=(
            isokinetic_speed_limit_mms
            if isokinetic_speed_limit_mms is not None
            else current.isokinetic_speed_limit_mms
        ),
        isokinetic_constant_resistance_lb=_coalesce_float(
            isokinetic_constant_resistance_lb,
            current.isokinetic_constant_resistance_lb,
        ),
        isokinetic_max_eccentric_load_lb=_coalesce_float(
            isokinetic_max_eccentric_load_lb,
            current.isokinetic_max_eccentric_load_lb,
        ),
        isometric_max_force_lb=_coalesce_float(isometric_max_force_lb, current.isometric_max_force_lb),
        isometric_max_duration_seconds=(
            isometric_max_duration_seconds
            if isometric_max_duration_seconds is not None
            else current.isometric_max_duration_seconds
        ),
        isometric_current_force_n=(
            None
            if leaving_isometric
            else (
                isometric_telemetry.current_force_n
                if isometric_telemetry is not None
                else current.isometric_current_force_n
            )
        ),
        isometric_peak_force_n=(
            None
            if leaving_isometric
            else (
                isometric_telemetry.peak_force_n
                if isometric_telemetry is not None
                else current.isometric_peak_force_n
            )
        ),
        isometric_elapsed_millis=(
            None
            if leaving_isometric
            else (
                isometric_telemetry.elapsed_millis
                if isometric_telemetry is not None
                else current.isometric_elapsed_millis
            )
        ),
        isometric_telemetry_tick=(
            None
            if leaving_isometric
            else (
                isometric_telemetry.tick
                if isometric_telemetry is not None
                else current.isometric_telemetry_tick
            )
        ),
        isometric_telemetry_start_tick=(
            None
            if leaving_isometric
            else (
                isometric_telemetry.start_tick
                if isometric_telemetry is not None
                else current.isometric_telemetry_start_tick
            )
        ),
        set_count=rep_telemetry.set_count if rep_telemetry is not None else current.set_count,
        rep_count=rep_telemetry.count if rep_telemetry is not None else current.rep_count,
        rep_phase=rep_telemetry.phase if rep_telemetry is not None else current.rep_phase,
        workout_mode=workout_mode or current.workout_mode,
        fitness_mode=fitness_mode if fitness_mode is not None else current.fitness_mode,
        workout_state=workout_state if workout_state is not None else current.workout_state,
    )
    return compute_safety(next_state)


def decode_params(packet: ParsedVoltraPacket) -> dict[int, int]:
    if packet.command_id not in (CMD_PARAM_READ, CMD_ASYNC_STATE):
        return {}

    payload = packet.payload
    start_offset = _param_list_start_offset(packet.command_id, payload)
    if len(payload) < start_offset + 2:
        return {}

    count = int.from_bytes(payload[start_offset:start_offset + 2], byteorder="little", signed=False)
    offset = start_offset + 2
    values: dict[int, int] = {}

    for _ in range(count):
        if offset + 2 > len(payload):
            return values
        param_id = int.from_bytes(payload[offset:offset + 2], byteorder="little", signed=False)
        offset += 2
        definition = PARAM_REGISTRY.get(param_id)
        if definition is None or definition.length <= 0 or offset + definition.length > len(payload):
            return values
        raw_value = payload[offset:offset + definition.length]
        values[param_id] = _decode_little_endian(definition, raw_value)
        offset += definition.length

    return values


def _param_list_start_offset(command_id: int, payload: bytes) -> int:
    if command_id != CMD_PARAM_READ or len(payload) < 5 or payload[0] != 0x00:
        return 0
    first_param_id = int.from_bytes(payload[3:5], byteorder="little", signed=False)
    return 1 if first_param_id in PARAM_REGISTRY else 0


def _decode_little_endian(definition: ParamDefinition, raw_value: bytes) -> int:
    if definition.param_type == ParamType.UINT8:
        return int.from_bytes(raw_value, byteorder="little", signed=False)
    if definition.param_type == ParamType.UINT16:
        return int.from_bytes(raw_value, byteorder="little", signed=False)
    if definition.param_type == ParamType.INT16:
        return int.from_bytes(raw_value, byteorder="little", signed=True)
    if definition.param_type == ParamType.UINT32:
        return int.from_bytes(raw_value, byteorder="little", signed=False)
    raise ValueError(f"Unsupported VOLTRA parameter type: {definition.param_type}")


def compute_safety(state: VoltraState) -> VoltraState:
    battery_percent = state.battery_percent
    fitness_mode = state.fitness_mode
    workout_state = state.workout_state
    target_load_lb = state.weight_lb
    in_resistance_band = workout_state == WORKOUT_STATE_RESISTANCE_BAND
    workout_session_active = workout_state is not None and workout_state != WORKOUT_STATE_INACTIVE
    low_battery = battery_percent < LOW_BATTERY_THRESHOLD_PERCENT if battery_percent is not None else state.low_battery
    parsed_device_state = fitness_mode is not None and workout_state is not None

    reasons: list[str] = []
    if low_battery is True:
        reasons.append(f"Battery is below {LOW_BATTERY_THRESHOLD_PERCENT}%.")
    if state.activation_state == "Activated":
        pass
    elif state.activation_state == "Not activated":
        reasons.append("VOLTRA is not activated.")
    else:
        reasons.append("Activation state unknown.")

    if fitness_mode is None:
        reasons.append("Fitness mode unknown.")
    elif is_load_engaged_for_workout_state(fitness_mode, workout_state):
        reasons.append("VOLTRA appears loaded; unload before loading again.")
    elif not is_ready_for_workout_state(fitness_mode, workout_state):
        reasons.append(f"Current mode is not ready for load (mode={fitness_mode}).")

    if workout_state is None:
        reasons.append("Workout state unknown.")
    elif not workout_session_active:
        reasons.append("Workout session is inactive. Choose a mode first.")

    if in_resistance_band:
        band_force = state.resistance_band_max_force_lb
        if band_force is None:
            reasons.append("Resistance Band force is unknown.")
        else:
            if band_force < MIN_RESISTANCE_BAND_FORCE_LB:
                reasons.append(f"Resistance Band force is below {MIN_RESISTANCE_BAND_FORCE_LB} lb.")
            if band_force > MAX_RESISTANCE_BAND_FORCE_LB:
                reasons.append(f"Resistance Band force is above {MAX_RESISTANCE_BAND_FORCE_LB} lb.")
    else:
        if target_load_lb is None:
            reasons.append("Target load is not set on the VOLTRA.")
        elif target_load_lb < MIN_TARGET_LB:
            reasons.append(f"Target load is below {MIN_TARGET_LB} lb.")
        elif target_load_lb > MAX_TARGET_LB:
            reasons.append(f"Target load is above {MAX_TARGET_LB} lb.")

    if state.locked is True:
        reasons.append("VOLTRA lock is active.")
    if state.child_locked is True:
        reasons.append("Child lock is active.")
    if state.active_ota is True:
        reasons.append("OTA/update state is active.")

    can_load = not reasons
    return replace(
        state,
        can_load=can_load,
        safety_reasons=("Ready for current mode load.",) if can_load else tuple(reasons),
        low_battery=low_battery,
        parsed_device_state=parsed_device_state,
        load_engaged=(
            is_load_engaged_for_workout_state(fitness_mode, workout_state)
            if fitness_mode is not None
            else state.load_engaged
        ),
        ready=(
            is_ready_for_workout_state(fitness_mode, workout_state)
            if fitness_mode is not None
            else state.ready
        ),
    )


def normalized_fitness_mode(mode: int | None) -> int | None:
    return mode & 0xFF if mode is not None else None


def is_ready_fitness_mode(mode: int | None) -> bool:
    return normalized_fitness_mode(mode) == FITNESS_MODE_STRENGTH_READY


def is_loaded_fitness_mode(mode: int | None) -> bool:
    return normalized_fitness_mode(mode) == FITNESS_MODE_STRENGTH_LOADED


def is_isometric_screen_mode(mode: int | None) -> bool:
    return normalized_fitness_mode(mode) == FITNESS_MODE_TEST_SCREEN


def is_load_engaged_for_workout_state(mode: int | None, workout_state: int | None) -> bool:
    if workout_state == WORKOUT_STATE_ISOMETRIC:
        return normalized_fitness_mode(mode) == FITNESS_MODE_STRENGTH_LOADED
    return is_loaded_fitness_mode(mode)


def is_ready_for_workout_state(mode: int | None, workout_state: int | None) -> bool:
    normalized = normalized_fitness_mode(mode)
    if workout_state == WORKOUT_STATE_ISOMETRIC:
        return normalized == FITNESS_MODE_STRENGTH_READY or is_isometric_screen_mode(mode)
    return normalized == FITNESS_MODE_STRENGTH_READY


def is_isokinetic_workout_state(workout_state: int | None) -> bool:
    return workout_state == WORKOUT_STATE_ISOKINETIC


def workout_mode_label(mode: int | None, workout_state: int | None) -> str | None:
    if mode is None and workout_state is None:
        return None

    if workout_state == WORKOUT_STATE_RESISTANCE_BAND:
        return f"Resistance Band, {_readiness_label(mode, workout_state)}"
    if workout_state == WORKOUT_STATE_DAMPER:
        return f"Damper, {_readiness_label(mode, workout_state)}"
    if workout_state == WORKOUT_STATE_ISOKINETIC:
        return f"Isokinetic, {_readiness_label(mode, workout_state)}"
    if workout_state == WORKOUT_STATE_ISOMETRIC:
        return f"Isometric Test, {_readiness_label(mode, workout_state)}"

    normalized = normalized_fitness_mode(mode)
    if normalized == FITNESS_MODE_STRENGTH_READY:
        mode_text = "Strength ready"
    elif normalized == FITNESS_MODE_STRENGTH_LOADED:
        mode_text = "Strength loaded"
    elif mode is None:
        mode_text = "Unknown mode"
    else:
        mode_text = f"Fitness mode {mode}"

    if workout_state == WORKOUT_STATE_INACTIVE:
        state_text = "session inactive"
    elif workout_state == WORKOUT_STATE_ACTIVE:
        state_text = "session active"
    elif workout_state is None:
        state_text = "state unknown"
    else:
        state_text = f"state {workout_state}"
    return f"{mode_text}, {state_text}"


def _readiness_label(mode: int | None, workout_state: int | None) -> str:
    if workout_state == WORKOUT_STATE_ISOMETRIC and is_load_engaged_for_workout_state(mode, workout_state):
        return "Loaded"
    if is_ready_for_workout_state(mode, workout_state):
        return "Ready"
    if is_load_engaged_for_workout_state(mode, workout_state):
        return "Loaded"
    if mode is None:
        return "state unknown"
    return f"mode {mode}"


def printable_ascii_segments(data: bytes) -> list[str]:
    segments: list[str] = []
    current: list[str] = []
    for byte in data:
        if byte in PRINTABLE_ASCII_RANGE:
            current.append(chr(byte))
        else:
            if len(current) >= MIN_PRINTABLE_SEGMENT_CHARS:
                segments.append("".join(current))
            current = []
    if len(current) >= MIN_PRINTABLE_SEGMENT_CHARS:
        segments.append("".join(current))
    return segments


def _first_regex_match(pattern: re.Pattern[str], segments: list[str]) -> str | None:
    for segment in segments:
        match = pattern.search(segment)
        if match is not None:
            return match.group(0)
    return None


def _all_regex_matches(pattern: re.Pattern[str], segments: list[str]) -> list[str]:
    matches: list[str] = []
    for segment in segments:
        matches.extend(match.group(0) for match in pattern.finditer(segment))
    return matches


def _merge_firmware_parts(existing: str | None, new_parts: list[str]) -> str | None:
    merged = []
    if existing:
        merged.extend(part for part in existing.split(" / ") if part)
    merged.extend(part for part in new_parts if part)
    deduped = list(dict.fromkeys(merged))
    return " / ".join(deduped) if deduped else existing


def _parse_battery(packet: ParsedVoltraPacket, params: dict[int, int]) -> int | None:
    if packet.command_id not in (CMD_ASYNC_STATE, CMD_PARAM_READ):
        return None
    for param_id in BATTERY_STATUS_PARAMS:
        value = _get_uint8(params, param_id)
        if value is not None and 0 <= value <= 100:
            return value
    return None


def _parse_activation_state(packet: ParsedVoltraPacket) -> str | None:
    if packet.command_id != CMD_ACTIVATION or len(packet.payload) < 2 or packet.payload[0] != 0:
        return None
    if packet.payload[1] == 1:
        return "Activated"
    if packet.payload[1] == 0:
        return "Not activated"
    return None


def _parse_band_curve(value: int | None) -> bool | None:
    if value == 0:
        return False
    if value == 1:
        return True
    return None


def _parse_resistance_experience(value: int | None) -> bool | None:
    if value == 0:
        return True
    if value == 1:
        return False
    return None


def _parse_assist_mode(value: int | None) -> bool | None:
    if value == 1:
        return True
    if value in (0, 8):
        return False
    return None


def _bool_from_uint8(value: int | None) -> bool | None:
    if value is None:
        return None
    return value == 1


@dataclass(frozen=True, slots=True)
class RepTelemetry:
    set_count: int
    count: int
    phase: str


@dataclass(frozen=True, slots=True)
class IsometricTelemetry:
    current_force_n: float | None
    peak_force_n: float | None
    elapsed_millis: int | None
    tick: int
    start_tick: int | None


def _parse_rep_telemetry(packet: ParsedVoltraPacket) -> RepTelemetry | None:
    payload = packet.payload
    if packet.command_id != CMD_TELEMETRY or len(payload) < 6:
        return None
    if payload[0] != 0x81 or payload[1] != 0x2B:
        return None

    set_count = payload[3]
    rep_count = int.from_bytes(payload[4:6], byteorder="big", signed=False)
    if not (0 <= set_count <= 1000 and 0 <= rep_count <= 10_000):
        return None
    return RepTelemetry(
        set_count=set_count,
        count=rep_count,
        phase=_rep_phase_label(payload[2]),
    )


def _parse_isometric_telemetry(
    packet: ParsedVoltraPacket,
    current: VoltraState,
    now: datetime,
) -> IsometricTelemetry | None:
    return _parse_legacy_isometric_telemetry(packet, current) or _parse_b4_isometric_telemetry(packet, current, now)


def _parse_legacy_isometric_telemetry(
    packet: ParsedVoltraPacket,
    current: VoltraState,
) -> IsometricTelemetry | None:
    payload = packet.payload
    if packet.command_id != CMD_TELEMETRY or len(payload) < 45:
        return None
    if payload[0] != 0x81 or payload[1] != 0x2B:
        return None
    if any(byte != 0 for byte in payload[2:11]) or any(byte != 0 for byte in payload[31:43]):
        return None

    tick = _u32le(payload, 27)
    status_primary = _u16le(payload, 11)
    status_secondary = _u16le(payload, 13)
    active_frame = status_secondary == 2 and 0 <= status_primary <= 6
    if not active_frame:
        if status_secondary in (4, 10):
            return IsometricTelemetry(
                current_force_n=None,
                peak_force_n=current.isometric_peak_force_n,
                elapsed_millis=current.isometric_elapsed_millis,
                tick=tick,
                start_tick=None,
            )
        return None

    current_force_n = _u16le(payload, 43) / 10.0
    starting_new_attempt = (
        current.isometric_current_force_n is None or current.isometric_telemetry_start_tick is None
    )
    start_tick = tick if starting_new_attempt else current.isometric_telemetry_start_tick or tick
    elapsed_millis = max(0, tick - start_tick)
    peak_force_n = (
        current_force_n
        if starting_new_attempt
        else max(current.isometric_peak_force_n or current_force_n, current_force_n)
    )
    return IsometricTelemetry(
        current_force_n=current_force_n,
        peak_force_n=peak_force_n,
        elapsed_millis=elapsed_millis,
        tick=tick,
        start_tick=start_tick,
    )


def _parse_b4_isometric_telemetry(
    packet: ParsedVoltraPacket,
    current: VoltraState,
    now: datetime,
) -> IsometricTelemetry | None:
    payload = packet.payload
    if packet.command_id != CMD_ISOMETRIC_STREAM or len(payload) != 8:
        return None
    if _u16le(payload, 2) not in {0x0004, 0x0005, 0x0006, 0x0007}:
        return None
    if not 40 <= _u16le(payload, 6) <= 60:
        return None

    current_force_lb = float(_u16le(payload, 0))
    if not 0.0 <= current_force_lb <= 220.0:
        return None

    current_force_n = current_force_lb * LB_TO_NEWTONS
    now_millis = int(now.timestamp() * 1000)
    starting_new_attempt = (
        current.isometric_current_force_n is None or current.isometric_telemetry_start_tick is None
    )
    start_tick = now_millis if starting_new_attempt else current.isometric_telemetry_start_tick or now_millis
    elapsed_millis = max(0, now_millis - start_tick)
    peak_force_n = (
        current_force_n
        if starting_new_attempt
        else max(current.isometric_peak_force_n or current_force_n, current_force_n)
    )
    return IsometricTelemetry(
        current_force_n=current_force_n,
        peak_force_n=peak_force_n,
        elapsed_millis=elapsed_millis,
        tick=now_millis,
        start_tick=start_tick,
    )


def _rep_phase_label(phase: int) -> str:
    if phase == 0:
        return "Idle"
    if phase == 1:
        return "Pull"
    if phase == 2:
        return "Transition"
    if phase == 3:
        return "Return"
    return f"Phase {phase}"


def _u16le(payload: bytes, offset: int) -> int:
    if offset + 1 >= len(payload):
        return -1
    return int.from_bytes(payload[offset:offset + 2], byteorder="little", signed=False)


def _u32le(payload: bytes, offset: int) -> int:
    if offset + 3 >= len(payload):
        return -1
    return int.from_bytes(payload[offset:offset + 4], byteorder="little", signed=False)


def _get_uint8(values: dict[int, int], param_id: int) -> int | None:
    value = values.get(param_id)
    return value if value is not None and 0 <= value <= 0xFF else None


def _get_uint16(values: dict[int, int], param_id: int) -> int | None:
    value = values.get(param_id)
    return value if value is not None and 0 <= value <= 0xFFFF else None


def _get_uint32(values: dict[int, int], param_id: int) -> int | None:
    value = values.get(param_id)
    return value if value is not None and 0 <= value <= 0xFFFF_FFFF else None


def _get_int16(values: dict[int, int], param_id: int) -> int | None:
    value = values.get(param_id)
    return value if value is not None and -(2**15) <= value <= (2**15 - 1) else None


def _coalesce_float(value: int | float | None, current: float | None) -> float | None:
    return float(value) if value is not None else current
