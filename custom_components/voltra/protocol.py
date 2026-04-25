from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from enum import Enum
from math import ceil
import re
from struct import pack

from .models import VoltraState

CMD_PARAM_READ = 0x0F
CMD_ASYNC_STATE = 0x10
CMD_PARAM_WRITE = 0x11
CMD_SERIAL_INFO = 0x19
CMD_HANDSHAKE_CHECK = 0x27
CMD_SET_DEVICE_NAME = 0x4E
CMD_DEVICE_NAME = 0x4F
CMD_COMMON_STATE = 0x74
CMD_FIRMWARE_INFO = 0x77
CMD_DEVICE_STATE = 0xA7
CMD_TELEMETRY = 0xAA
CMD_ACTIVATION = 0xAB
CMD_BULK_PARAM_WRITE = 0xAF
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
DEVICE_NAME_MAX_BYTES = 21
MIN_ROWING_SELECTOR_LEVEL = 1
MAX_ROWING_SELECTOR_LEVEL = 10
DEFAULT_ROWING_RESISTANCE_LEVEL = 4
DEFAULT_ROWING_SIMULATED_WEAR_LEVEL = 8
CUSTOM_CURVE_POINT_COUNT = 4
MIN_CUSTOM_CURVE_RESISTANCE_LIMIT_LB = 5
MAX_CUSTOM_CURVE_RESISTANCE_LIMIT_LB = 200
MIN_CUSTOM_CURVE_RESISTANCE_SPAN_LB = 20
DEFAULT_CUSTOM_CURVE_RESISTANCE_MIN_LB = 5
DEFAULT_CUSTOM_CURVE_RESISTANCE_LIMIT_LB = 100
MIN_CUSTOM_CURVE_RANGE_OF_MOTION_IN = 20
MAX_CUSTOM_CURVE_RANGE_OF_MOTION_IN = 118
DEFAULT_CUSTOM_CURVE_RANGE_OF_MOTION_IN = 117
ROWING_SCREEN_ID = 0x3E
ROWING_ONGOING_UI = 0x0303

PARAM_BP_RUNTIME_POSITION_CM = 0x3E82
PARAM_BP_RUNTIME_WIRE_WEIGHT_LBS = 0x3E83
PARAM_BP_BASE_WEIGHT = 0x3E86
PARAM_BP_CHAINS_WEIGHT = 0x3E87
PARAM_BP_ECCENTRIC_WEIGHT = 0x3E88
PARAM_BP_SET_FITNESS_MODE = 0x3E89
PARAM_BMS_RSOC_LEGACY = 0x1B5D
PARAM_BMS_RSOC = 0x4E2D
PARAM_FITNESS_WORKOUT_STATE = 0x4FB0
PARAM_APP_CUR_SCR_ID = 0x5011
PARAM_FITNESS_DAMPER_RATIO_IDX = 0x5103
PARAM_FITNESS_ASSIST_MODE = 0x5106
PARAM_EP_SCR_SWITCH = 0x5165
PARAM_EP_FITNESS_DATA_NOTIFY_HZ = 0x5182
PARAM_EP_FITNESS_DATA_NOTIFY_SUBSCRIBE = 0x5183
PARAM_RESISTANCE_EXPERIENCE = 0x52CA
PARAM_EP_RESISTANCE_BAND_INVERSE = 0x52E3
PARAM_EP_ISOKINETIC_TARGET_SPEED_MMS = 0x5350
PARAM_EP_MAX_ALLOWED_FORCE = 0x5314
PARAM_RESISTANCE_BAND_ALGORITHM = 0x5361
PARAM_RESISTANCE_BAND_MAX_FORCE = 0x5362
PARAM_FITNESS_ROWING_DAMPER_RATIO_IDX = 0x53A7
PARAM_EP_ROW_CHAIN_GEAR = 0x53AE
PARAM_RESISTANCE_BAND_LEN_BY_ROM = 0x53B6
PARAM_RESISTANCE_BAND_LEN = 0x53B7
PARAM_FITNESS_INVERSE_CHAIN = 0x53B0
PARAM_WEIGHT_TRAINING_EXTRA_MODE = 0x53C6
PARAM_ISOMETRIC_METRICS_TYPE = 0x53D1
PARAM_ISOMETRIC_MAX_DURATION = 0x53D2
PARAM_EP_ISOMETRIC_TESTING_BODY_WEIGHT_N = 0x535A
PARAM_EP_ISOMETRIC_TESTING_BODY_WEIGHT_100G = 0x535B
PARAM_EP_ISOMETRIC_TESTING_BODY_WEIGHT_LBS = 0x535C
PARAM_ISOKINETIC_ECC_MODE = 0x5410
PARAM_ISOKINETIC_ECC_SPEED_LIMIT = 0x5411
PARAM_ISOKINETIC_ECC_CONST_WEIGHT = 0x5412
PARAM_ISOKINETIC_ECC_OVERLOAD_WEIGHT = 0x5413
PARAM_ISOMETRIC_MAX_FORCE = 0x5431
PARAM_QUICK_CABLE_ADJUSTMENT = 0x54BC
PARAM_MC_DEFAULT_OFFLEN_CM = 0x506A
PARAM_FITNESS_ONGOING_UI = 0x5467

FITNESS_MODE_ISOMETRIC_ARMED = 0x0001
FITNESS_MODE_STRENGTH_READY = 0x0004
FITNESS_MODE_STRENGTH_LOADED = 0x0005
FITNESS_MODE_ROWING_ACTIVE = 0x0015
FITNESS_MODE_TEST_SCREEN = 0x0085

ISOKINETIC_MENU_ISOKINETIC = 0x00
ISOKINETIC_MENU_CONSTANT_RESISTANCE = 0x01

WORKOUT_STATE_INACTIVE = 0x00
WORKOUT_STATE_ACTIVE = 0x01
WORKOUT_STATE_RESISTANCE_BAND = 0x02
WORKOUT_STATE_ROWING = 0x03
WORKOUT_STATE_DAMPER = 0x04
WORKOUT_STATE_CUSTOM_CURVE = 0x06
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
    PARAM_EP_MAX_ALLOWED_FORCE,
    PARAM_FITNESS_DAMPER_RATIO_IDX,
    PARAM_ISOKINETIC_ECC_MODE,
    PARAM_EP_ISOKINETIC_TARGET_SPEED_MMS,
    PARAM_ISOKINETIC_ECC_SPEED_LIMIT,
    PARAM_ISOKINETIC_ECC_CONST_WEIGHT,
    PARAM_ISOKINETIC_ECC_OVERLOAD_WEIGHT,
    PARAM_ISOMETRIC_MAX_FORCE,
    PARAM_ISOMETRIC_METRICS_TYPE,
    PARAM_ISOMETRIC_MAX_DURATION,
    PARAM_EP_ISOMETRIC_TESTING_BODY_WEIGHT_N,
    PARAM_EP_ISOMETRIC_TESTING_BODY_WEIGHT_100G,
    PARAM_EP_ISOMETRIC_TESTING_BODY_WEIGHT_LBS,
    PARAM_BP_CHAINS_WEIGHT,
    PARAM_BP_ECCENTRIC_WEIGHT,
    PARAM_FITNESS_INVERSE_CHAIN,
    PARAM_WEIGHT_TRAINING_EXTRA_MODE,
    PARAM_FITNESS_ROWING_DAMPER_RATIO_IDX,
    PARAM_EP_ROW_CHAIN_GEAR,
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
TELEMETRY_REP_TYPE = 0x81
TELEMETRY_REP_LENGTH_MARKER = 0x2B
TELEMETRY_REP_PHASE_OFFSET = 2
TELEMETRY_SET_COUNT_OFFSET = 3
TELEMETRY_REP_COUNT_OFFSET = 4
TELEMETRY_ISOMETRIC_MIN_BYTES = 45
TELEMETRY_ISOMETRIC_SUMMARY_BYTES = 39
TELEMETRY_ISOMETRIC_STATUS_PRIMARY_OFFSET = 11
TELEMETRY_ISOMETRIC_STATUS_SECONDARY_OFFSET = 13
TELEMETRY_ISOMETRIC_TICK_OFFSET = 27
TELEMETRY_ISOMETRIC_FORCE_OFFSET = 43
TELEMETRY_ISOMETRIC_ACTIVE_MARKER = 2
TELEMETRY_ISOMETRIC_PROGRESS_MARKER = 3
TELEMETRY_ISOMETRIC_READY_MARKER = 4
TELEMETRY_ISOMETRIC_COARSE_LIVE_FORCE_MARKER = 1
TELEMETRY_ISOMETRIC_ARMED_MARKER = 10
TELEMETRY_ISOMETRIC_COMPLETED_MARKER = 11
TELEMETRY_ISOMETRIC_LIVE_FORCE_MARKER = 12
TELEMETRY_ISOMETRIC_EXTENDED_LIVE_FORCE_MARKERS = range(12, 16)
TELEMETRY_ISOMETRIC_SUMMARY_TYPE = 0x80
TELEMETRY_ISOMETRIC_SUMMARY_LENGTH_MARKER = 0x25
TELEMETRY_ISOMETRIC_SUMMARY_PEAK_FORCE_OFFSET = 23
TELEMETRY_ISOMETRIC_SUMMARY_PEAK_RELATIVE_FORCE_OFFSET = 29
TELEMETRY_ISOMETRIC_SUMMARY_DURATION_SECONDS_OFFSET = 33
TELEMETRY_ISOMETRIC_WAVEFORM_TYPE = 0x93
MAX_REASONABLE_SET_COUNT = 1_000
MAX_REASONABLE_REP_COUNT = 10_000
ISOMETRIC_SAMPLE_RATE_MIN = 40
ISOMETRIC_SAMPLE_RATE_MAX = 60
MAX_REASONABLE_ISOMETRIC_DURATION_SECONDS = 60
MAX_REASONABLE_ISOMETRIC_RELATIVE_FORCE_TENTHS_PERCENT = 1_000
MAX_REASONABLE_ISOMETRIC_FORCE_N = 2_000.0
MAX_REASONABLE_ISOMETRIC_GRAPH_FORCE_N = 2_000.0
MIN_REASONABLE_ISOMETRIC_BODY_WEIGHT_N = 100.0
MAX_REASONABLE_ISOMETRIC_BODY_WEIGHT_N = 5_000.0
ISOMETRIC_METRICS_TYPE_FORCE = 0
MAX_REASONABLE_ISOMETRIC_STATUS_WORD = 0x0200
MAX_REASONABLE_ISOMETRIC_AUX_WORD = 4_000
MAX_SUMMARY_RECONCILIATION_SPARSE_SAMPLES = 16
STALE_ISOMETRIC_SUMMARY_FORCE_TOLERANCE_N = 5.0
STALE_ISOMETRIC_SUMMARY_ELAPSED_TOLERANCE_MILLIS = 250
LEGACY_ISOMETRIC_PULL_FORCE_SCALE = 0.44482216152605
LEGACY_ISOMETRIC_COARSE_FORCE_SCALE = 1.067
ISOMETRIC_WAVEFORM_HEADER_BYTES = 6
MAX_ISOMETRIC_WAVEFORM_SAMPLES = 2_400
LEGACY_ISOMETRIC_STREAM_VARIANTS = frozenset({1, 2, 3})
TELEMETRY_ISOMETRIC_COARSE_LIVE_FORCE_RANGE_N = (1.0, MAX_REASONABLE_ISOMETRIC_FORCE_N)
TELEMETRY_ISOMETRIC_WAVEFORM_MARKERS = frozenset({0xCC, 0x82, 0xA8})
ISOMETRIC_VENDOR_REFRESH_PAYLOAD = bytes((0x13, 0x01))
DEFAULT_ISOMETRIC_GRAPH_MAX_FORCE_N = 276.0
ISOMETRIC_GRAPH_STEP_FORCE_N = 69.0
ISOMETRIC_WINDOW_100MS = 100
MIN_MEANINGFUL_ISOMETRIC_FORCE_N = 1.0
SPARSE_PEAK_SPIKE_RATIO = 1.55
SPARSE_PEAK_SPIKE_MIN_DELTA_N = 60.0
SPARSE_PEAK_RETAIN_FACTOR = 0.35
MAX_DENSE_ISOMETRIC_WAVEFORM_STEP_MILLIS = 25.0
CUSTOM_CURVE_B4_SHORT_BYTES = 8
CUSTOM_CURVE_B4_EXTENDED_BYTES = 12
CUSTOM_CURVE_B4_FORCE_MIRROR_TOLERANCE_TENTHS_LB = 2
CUSTOM_CURVE_VENDOR_STATUS_BYTES = 39
CUSTOM_CURVE_VENDOR_FORCE_OFFSET = 5
CUSTOM_CURVE_FORCE_TENTHS_PER_LB = 10.0
CUSTOM_CURVE_REP_ACTIVE_MARGIN_LB = 3.0
CUSTOM_CURVE_REP_ACTIVE_MULTIPLIER = 1.2
CUSTOM_CURVE_REP_RESET_MARGIN_LB = 1.0
CUSTOM_CURVE_REP_DIRECTION_DEADBAND_LB = 0.4
ROWING_STATUS_TYPE = 0x92
ROWING_WAVEFORM_TYPE = 0x93
ROWING_SUMMARY_TYPE = 0x95
ROWING_SUMMARY_LENGTH_MARKER = 0x25
ROWING_SUMMARY_MIN_BYTES = 39
ROWING_SUMMARY_STROKE_RATE_SPM_OFFSET = 2
ROWING_SUMMARY_CURRENT_PACE_TENTH_SECONDS_OFFSET = 3
ROWING_SUMMARY_AVERAGE_PACE_TENTH_SECONDS_OFFSET = 7
ROWING_SUMMARY_STROKE_COUNT_CENTI_OFFSET = 19
ROWING_SUMMARY_LEGACY_STROKE_RATE_CENTI_SPM_OFFSET = 23
ROWING_SUMMARY_DISTANCE_METERS_OFFSET = 35
ROWING_AA92_DISTANCE_OFFSET = 11
ROWING_FORCE_TENTHS_PER_LB = 10.0
POWER_WORKOUT_SUMMARY_TYPE = 0x85
POWER_WORKOUT_SUMMARY_LENGTH_MARKER = 0x5F
POWER_WORKOUT_SUMMARY_MIN_BYTES = 97
POWER_WORKOUT_SUMMARY_PEAK_FORCE_TENTHS_LB_OFFSET = 17
POWER_WORKOUT_SUMMARY_PEAK_POWER_WATTS_OFFSET = 21
POWER_WORKOUT_SUMMARY_TIME_TO_PEAK_CENTISECONDS_OFFSET = 69
POWER_WORKOUT_REP_SUMMARY_TYPE = 0x82
POWER_WORKOUT_REP_SUMMARY_LENGTH_MARKER = 0x3B
POWER_WORKOUT_REP_SUMMARY_MIN_BYTES = 61
POWER_WORKOUT_REP_SUMMARY_TIME_TO_PEAK_CENTISECONDS_OFFSET = 22
POWER_WORKOUT_LIVE_TYPE = 0x81
POWER_WORKOUT_LIVE_LENGTH_MARKER = 0x2B
POWER_WORKOUT_LIVE_MIN_BYTES = 45
POWER_WORKOUT_LIVE_FORCE_TENTHS_LB_OFFSET = 11
POWER_WORKOUT_LIVE_TICK_OFFSET = 27
POWER_WORKOUT_FORCE_TENTHS_PER_LB = 10.0
POWER_WORKOUT_PRIMARY_START_FORCE_TENTHS_LB = 60
POWER_WORKOUT_FALLBACK_START_FORCE_TENTHS_LB = 100
POWER_WORKOUT_RESET_FORCE_TENTHS_LB = 70
ROWING_ACTIVE_FORCE_LB = 3.0
ROWING_RESET_FORCE_LB = 1.5
ROWING_FORCE_DIRECTION_DEADBAND_LB = 0.4
ROWING_B4_SHORT_BYTES = 8
ROWING_WAVEFORM_HEADER_BYTES = 6
MAX_REASONABLE_ROWING_FORCE_TENTHS_LB = 4_000
MAX_REASONABLE_ROWING_DISTANCE_CENTIMETERS = 10_000_000
MAX_REASONABLE_ROWING_ELAPSED_MILLIS = 24 * 60 * 60 * 1000
MAX_ROWING_FORCE_SAMPLES = 1_200
MAX_ROWING_DISTANCE_SAMPLES = 1_200
MAX_REASONABLE_POWER_WORKOUT_FORCE_TENTHS_LB = 5_000
MAX_REASONABLE_POWER_WORKOUT_WATTS = 5_000
MAX_REASONABLE_POWER_WORKOUT_TIME_TO_PEAK_CENTISECONDS = 3_000
POWER_WORKOUT_SUMMARY_TIME_CORRECTION_MAX_DELTA_MILLIS = 150
MAX_REASONABLE_CUSTOM_CURVE_FORCE_TENTHS_LB = 2_000
CUSTOM_CURVE_ACTIVE_PHASES = frozenset({"Pull", "Return"})
CUSTOM_CURVE_WIRE_POINT_COUNT = 6
MAX_CUSTOM_CURVE_WIRE_RANGE_OF_MOTION_TENTHS_IN = 1170
CUSTOM_CURVE_WIRE_FULL_SCALE_SPAN_LB = 120.0
ROW_ACTION_START_JUST_ROW = 0x03
ROW_ACTION_SELECT_JUST_ROW = 0x04
ROW_ACTION_START_SELECTED_DISTANCE = 0x06
CUSTOM_CURVE_WIRE_X_POINTS = (
    0.16903418,
    0.33806837,
    0.50473505,
    0.6714017,
    0.83570087,
    1.0,
)
CUSTOM_CURVE_UI_X_POINTS = (
    0.0,
    0.33806837,
    0.6714017,
    1.0,
)
CUSTOM_CURVE_CAPTURED_WIRE_Y_POINTS = (
    0.123481624,
    0.24696325,
    0.41362992,
    0.5802966,
    0.7901483,
    1.0,
)
DEFAULT_CUSTOM_CURVE_POINTS = (0.0, 0.24696325, 0.5802966, 1.0)

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
    PARAM_APP_CUR_SCR_ID: ParamDefinition(ParamType.UINT8, 1),
    PARAM_FITNESS_DAMPER_RATIO_IDX: ParamDefinition(ParamType.UINT8, 1),
    PARAM_FITNESS_ROWING_DAMPER_RATIO_IDX: ParamDefinition(ParamType.UINT8, 1),
    PARAM_EP_ROW_CHAIN_GEAR: ParamDefinition(ParamType.UINT8, 1),
    PARAM_FITNESS_ASSIST_MODE: ParamDefinition(ParamType.UINT8, 1),
    PARAM_RESISTANCE_EXPERIENCE: ParamDefinition(ParamType.UINT8, 1),
    PARAM_EP_RESISTANCE_BAND_INVERSE: ParamDefinition(ParamType.UINT8, 1),
    PARAM_EP_ISOKINETIC_TARGET_SPEED_MMS: ParamDefinition(ParamType.UINT32, 4),
    PARAM_EP_MAX_ALLOWED_FORCE: ParamDefinition(ParamType.UINT16, 2),
    PARAM_RESISTANCE_BAND_ALGORITHM: ParamDefinition(ParamType.UINT8, 1),
    PARAM_RESISTANCE_BAND_MAX_FORCE: ParamDefinition(ParamType.UINT16, 2),
    PARAM_RESISTANCE_BAND_LEN_BY_ROM: ParamDefinition(ParamType.UINT8, 1),
    PARAM_RESISTANCE_BAND_LEN: ParamDefinition(ParamType.UINT16, 2),
    PARAM_FITNESS_INVERSE_CHAIN: ParamDefinition(ParamType.UINT8, 1),
    PARAM_WEIGHT_TRAINING_EXTRA_MODE: ParamDefinition(ParamType.UINT8, 1),
    PARAM_ISOMETRIC_METRICS_TYPE: ParamDefinition(ParamType.UINT8, 1),
    PARAM_EP_ISOMETRIC_TESTING_BODY_WEIGHT_N: ParamDefinition(ParamType.UINT32, 4),
    PARAM_EP_ISOMETRIC_TESTING_BODY_WEIGHT_100G: ParamDefinition(ParamType.UINT16, 2),
    PARAM_EP_ISOMETRIC_TESTING_BODY_WEIGHT_LBS: ParamDefinition(ParamType.UINT16, 2),
    PARAM_ISOMETRIC_MAX_DURATION: ParamDefinition(ParamType.UINT16, 2),
    PARAM_ISOKINETIC_ECC_MODE: ParamDefinition(ParamType.UINT8, 1),
    PARAM_ISOKINETIC_ECC_SPEED_LIMIT: ParamDefinition(ParamType.UINT16, 2),
    PARAM_ISOKINETIC_ECC_CONST_WEIGHT: ParamDefinition(ParamType.UINT16, 2),
    PARAM_ISOKINETIC_ECC_OVERLOAD_WEIGHT: ParamDefinition(ParamType.UINT16, 2),
    PARAM_ISOMETRIC_MAX_FORCE: ParamDefinition(ParamType.UINT16, 2),
    PARAM_QUICK_CABLE_ADJUSTMENT: ParamDefinition(ParamType.UINT8, 1),
    PARAM_FITNESS_ONGOING_UI: ParamDefinition(ParamType.UINT16, 2),
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


def build_device_name_payload(name: str) -> bytes:
    trimmed = name.strip()
    if not trimmed:
        raise ValueError("Device name must not be blank.")
    if len(trimmed) > 20:
        raise ValueError("Device name must be 20 characters or fewer.")
    if not trimmed[0].isalpha():
        raise ValueError("Device name must start with a letter.")
    if not all(
        ord(char) in PRINTABLE_ASCII_RANGE and char not in {":", "\\", "|"}
        for char in trimmed
    ):
        raise ValueError("Device name must use plain ASCII and cannot include :, \\, or |.")

    ascii_name = trimmed.encode("ascii")
    if len(ascii_name) > DEVICE_NAME_MAX_BYTES:
        raise ValueError("Device name exceeds the VOLTRA payload size.")
    return ascii_name + bytes(DEVICE_NAME_MAX_BYTES - len(ascii_name))


def build_vendor_state_refresh_frame(seq: int) -> bytes:
    return build_frame(
        cmd=CMD_TELEMETRY,
        payload=ISOMETRIC_VENDOR_REFRESH_PAYLOAD,
        seq=seq,
    )


def build_set_fitness_data_notify_subscribe_payload() -> bytes:
    return build_param_write_payload(
        PARAM_EP_FITNESS_DATA_NOTIFY_SUBSCRIBE,
        bytes((0xF5, 0x7B, 0x65, 0x00)),
    )


def build_set_fitness_data_notify_hz_payload() -> bytes:
    return build_param_write_payload(PARAM_EP_FITNESS_DATA_NOTIFY_HZ, bytes((0x28,)))


def build_enter_row_payload() -> bytes:
    return build_param_write_payload(PARAM_FITNESS_WORKOUT_STATE, bytes((WORKOUT_STATE_ROWING,)))


def build_enter_custom_curve_payload() -> bytes:
    return build_param_write_payload(PARAM_FITNESS_WORKOUT_STATE, bytes((WORKOUT_STATE_CUSTOM_CURVE,)))


def build_set_rowing_resistance_level_payload(level: int) -> bytes:
    return build_param_write_payload(
        PARAM_FITNESS_ROWING_DAMPER_RATIO_IDX,
        bytes((rowing_selector_wire_index(level),)),
    )


def build_set_rowing_simulated_wear_level_payload(level: int) -> bytes:
    return build_param_write_payload(
        PARAM_EP_ROW_CHAIN_GEAR,
        bytes((rowing_selector_wire_index(level),)),
    )


def build_trigger_row_start_screen_payload(target_meters: int | None) -> bytes:
    return build_param_write_payload(
        PARAM_EP_SCR_SWITCH,
        bytes((row_start_action_code(target_meters), ROWING_SCREEN_ID, 0x00, 0x01)),
    )


def build_custom_curve_bulk_subscribe_payload() -> bytes:
    return bytes.fromhex(
        "024100b04f015053018153015153016e50017f5301a85101c45301115401883e01a75301065101645301853e"
        "01315401cf5301145401873e016a5001825201155401e14e01835101de5401525301823e01675401863e0155"
        "53018c5401e552012d4e011150011853015b53011353010f5401d25301245101195301893e01035101b65301"
        "4154018b5401ae53016f5001625301b05301c95301c85301df54010f5201025101145301b75301c753011254"
        "01215401c65301d45401c553018d5301135401105401"
    )


def build_row_bulk_subscribe_payload() -> bytes:
    return bytes.fromhex(
        "0241007f5301505301515301a85101525301c75301145301835101245101105401ae5301145401675401df54"
        "01b04f010f5401065101c85301cf5301823e01645301e55201185301125401c45301315401155401a75301"
        "863e012d4e01135301893e018252015b5301135401195301815301b65301555301883e01625301215401b0"
        "5301c95301de5401873e01e14e010f52018b5401c553018d5301025101415401d454011154016a5001c653"
        "01035101853e016f5001115001d253018c54016e5001b75301"
    )


def build_custom_curve_vendor_preset_payload(
    *,
    points: tuple[float, float, float, float] | list[float] = DEFAULT_CUSTOM_CURVE_POINTS,
    resistance_min_lb: int = DEFAULT_CUSTOM_CURVE_RESISTANCE_MIN_LB,
    resistance_limit_lb: int = DEFAULT_CUSTOM_CURVE_RESISTANCE_LIMIT_LB,
    range_of_motion_in: int = DEFAULT_CUSTOM_CURVE_RANGE_OF_MOTION_IN,
) -> bytes:
    normalized_points = tuple(float(point) for point in points)
    if len(normalized_points) != CUSTOM_CURVE_POINT_COUNT:
        raise ValueError(
            f"Custom Curve requires {CUSTOM_CURVE_POINT_COUNT} points, got {len(normalized_points)}.",
        )
    if not MIN_CUSTOM_CURVE_RESISTANCE_LIMIT_LB <= resistance_min_lb <= MAX_CUSTOM_CURVE_RESISTANCE_LIMIT_LB:
        raise ValueError(
            f"Custom Curve resistance minimum must be between {MIN_CUSTOM_CURVE_RESISTANCE_LIMIT_LB} and {MAX_CUSTOM_CURVE_RESISTANCE_LIMIT_LB} lb, got {resistance_min_lb}.",
        )
    if not MIN_CUSTOM_CURVE_RESISTANCE_LIMIT_LB <= resistance_limit_lb <= MAX_CUSTOM_CURVE_RESISTANCE_LIMIT_LB:
        raise ValueError(
            f"Custom Curve resistance limit must be between {MIN_CUSTOM_CURVE_RESISTANCE_LIMIT_LB} and {MAX_CUSTOM_CURVE_RESISTANCE_LIMIT_LB} lb, got {resistance_limit_lb}.",
        )
    if resistance_limit_lb - resistance_min_lb < MIN_CUSTOM_CURVE_RESISTANCE_SPAN_LB:
        raise ValueError(
            f"Custom Curve resistance range must span at least {MIN_CUSTOM_CURVE_RESISTANCE_SPAN_LB} lb, got {resistance_min_lb}..{resistance_limit_lb}.",
        )
    if not MIN_CUSTOM_CURVE_RANGE_OF_MOTION_IN <= range_of_motion_in <= MAX_CUSTOM_CURVE_RANGE_OF_MOTION_IN:
        raise ValueError(
            f"Custom Curve range of motion must be between {MIN_CUSTOM_CURVE_RANGE_OF_MOTION_IN} and {MAX_CUSTOM_CURVE_RANGE_OF_MOTION_IN} in, got {range_of_motion_in}.",
        )

    header = (
        bytes((0x06, 0x02, 0x00, 0x00))
        + encode_uint16_le(custom_curve_wire_range_of_motion_tenths_in(range_of_motion_in))
        + encode_uint16_le(resistance_limit_lb)
        + bytes((resistance_limit_lb & 0xFF, resistance_min_lb & 0xFF))
        + bytes.fromhex("e64e9cea030000000000000000")
    )
    wire_points = custom_curve_wire_points(
        points=normalized_points,
        resistance_min_lb=resistance_min_lb,
        resistance_limit_lb=resistance_limit_lb,
    )
    first_half = b"".join(
        encode_float32_le(x) + encode_float32_le(y)
        for x, y in wire_points[:3]
    )
    second_half = b"".join(
        encode_float32_le(x) + encode_float32_le(y)
        for x, y in wire_points[3:]
    )
    return header + first_half + bytes((0x0D,)) + second_half


def rowing_selector_wire_index(level: int) -> int:
    normalized_level = max(MIN_ROWING_SELECTOR_LEVEL, min(MAX_ROWING_SELECTOR_LEVEL, int(level)))
    return normalized_level - 1


def rowing_selector_display_level(wire_index: int | None) -> int | None:
    if wire_index is None or wire_index not in range(0, 10):
        return None
    return wire_index + 1


def row_start_action_code(target_meters: int | None) -> int:
    if target_meters is None:
        return ROW_ACTION_START_JUST_ROW
    if target_meters == 50:
        return ROW_ACTION_START_SELECTED_DISTANCE
    if target_meters == 100:
        return 0x07
    if target_meters == 500:
        return 0x08
    if target_meters == 1000:
        return 0x09
    if target_meters == 2000:
        return 0x0A
    if target_meters == 5000:
        return 0x0B
    raise ValueError(f"Unsupported Row target distance: {target_meters}")


def encode_float32_le(value: float) -> bytes:
    return pack("<f", float(value))


def custom_curve_wire_points(
    *,
    points: tuple[float, float, float, float],
    resistance_min_lb: int,
    resistance_limit_lb: int,
) -> tuple[tuple[float, float], ...]:
    normalized_points = tuple(max(0.0, min(1.0, point)) for point in points)
    if (
        normalized_points == DEFAULT_CUSTOM_CURVE_POINTS
        and resistance_min_lb == DEFAULT_CUSTOM_CURVE_RESISTANCE_MIN_LB
        and resistance_limit_lb == DEFAULT_CUSTOM_CURVE_RESISTANCE_LIMIT_LB
    ):
        return tuple(zip(CUSTOM_CURVE_WIRE_X_POINTS, CUSTOM_CURVE_CAPTURED_WIRE_Y_POINTS, strict=False))
    y_scale = (resistance_limit_lb - resistance_min_lb) / CUSTOM_CURVE_WIRE_FULL_SCALE_SPAN_LB
    return tuple(
        (x, interpolate_custom_curve_y(x, normalized_points) * y_scale)
        for x in CUSTOM_CURVE_WIRE_X_POINTS
    )


def interpolate_custom_curve_y(x: float, points: tuple[float, float, float, float]) -> float:
    if x <= CUSTOM_CURVE_UI_X_POINTS[0]:
        return points[0]
    for index in range(len(CUSTOM_CURVE_UI_X_POINTS) - 1):
        start_x = CUSTOM_CURVE_UI_X_POINTS[index]
        end_x = CUSTOM_CURVE_UI_X_POINTS[index + 1]
        if x <= end_x:
            span = end_x - start_x
            progress = 0.0 if span == 0 else (x - start_x) / span
            return points[index] + ((points[index + 1] - points[index]) * progress)
    return points[-1]


def custom_curve_wire_range_of_motion_tenths_in(range_of_motion_in: int) -> int:
    return min(range_of_motion_in * 10, MAX_CUSTOM_CURVE_WIRE_RANGE_OF_MOTION_TENTHS_IN)


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
    rowing_resistance_level = rowing_selector_display_level(_get_uint8(params, PARAM_FITNESS_ROWING_DAMPER_RATIO_IDX))
    rowing_simulated_wear_level = rowing_selector_display_level(_get_uint8(params, PARAM_EP_ROW_CHAIN_GEAR))
    assist_mode_enabled = _parse_assist_mode(_get_uint8(params, PARAM_FITNESS_ASSIST_MODE))
    weight_training_extra_mode = _get_uint8(params, PARAM_WEIGHT_TRAINING_EXTRA_MODE)
    app_current_screen_id = _get_uint8(params, PARAM_APP_CUR_SCR_ID)
    fitness_ongoing_ui = _get_uint16(params, PARAM_FITNESS_ONGOING_UI)
    max_allowed_force_lb = _get_uint16(params, PARAM_EP_MAX_ALLOWED_FORCE)
    isokinetic_mode = _get_uint8(params, PARAM_ISOKINETIC_ECC_MODE)
    isokinetic_target_speed_mms = _get_uint32(params, PARAM_EP_ISOKINETIC_TARGET_SPEED_MMS)
    isokinetic_speed_limit_mms = _get_uint16(params, PARAM_ISOKINETIC_ECC_SPEED_LIMIT)
    isokinetic_constant_resistance_lb = _get_uint16(params, PARAM_ISOKINETIC_ECC_CONST_WEIGHT)
    isokinetic_max_eccentric_load_lb = _get_uint16(params, PARAM_ISOKINETIC_ECC_OVERLOAD_WEIGHT)
    isometric_max_force_lb = _get_uint16(params, PARAM_ISOMETRIC_MAX_FORCE)
    isometric_max_duration_seconds = _get_uint16(params, PARAM_ISOMETRIC_MAX_DURATION)
    isometric_metrics_type = _get_uint8(params, PARAM_ISOMETRIC_METRICS_TYPE)
    isometric_body_weight_n = _get_uint32(params, PARAM_EP_ISOMETRIC_TESTING_BODY_WEIGHT_N)
    isometric_body_weight_100g = _get_uint16(params, PARAM_EP_ISOMETRIC_TESTING_BODY_WEIGHT_100G)
    isometric_body_weight_lb = _get_uint16(params, PARAM_EP_ISOMETRIC_TESTING_BODY_WEIGHT_LBS)
    fitness_mode = _get_uint16(params, PARAM_BP_SET_FITNESS_MODE)
    workout_state = _get_uint8(params, PARAM_FITNESS_WORKOUT_STATE)
    timestamp_millis = int(timestamp.timestamp() * 1000)

    current_was_in_isometric = bool(current.workout_mode and current.workout_mode.startswith("Isometric Test"))
    current_was_in_custom_curve = bool(current.workout_mode and current.workout_mode.startswith("Custom Curve"))
    current_was_in_rowing = bool(current.workout_mode and current.workout_mode.startswith("Rowing"))
    current_was_in_power_workout = bool(
        current.workout_mode
        and (
            current.workout_mode.startswith("Damper")
            or current.workout_mode.startswith("Isokinetic")
        ),
    )
    current_mode_is_known_non_isometric = current.workout_mode is not None and not current_was_in_isometric
    row_screen_state_seen = app_current_screen_id == ROWING_SCREEN_ID and fitness_ongoing_ui == ROWING_ONGOING_UI
    current_has_live_row_screen = (
        current.app_current_screen_id == ROWING_SCREEN_ID
        and current.fitness_ongoing_ui == ROWING_ONGOING_UI
    )
    packet_is_native_row_state = (
        workout_state == WORKOUT_STATE_ROWING
        or normalized_fitness_mode(fitness_mode) == FITNESS_MODE_ROWING_ACTIVE
    )
    packet_declares_non_row_workout = workout_state is not None and workout_state != WORKOUT_STATE_ROWING
    packet_has_rowing_telemetry = (
        (
            (current_was_in_rowing and current_has_live_row_screen and not packet_declares_non_row_workout)
            or row_screen_state_seen
            or packet_is_native_row_state
        )
        and (_has_native_rowing_summary_payload(packet) or _has_rowing_telemetry_payload(packet))
    )
    row_workout_state_bounce = False
    packet_is_rowing = (
        packet_is_native_row_state
        or row_screen_state_seen
        or packet_has_rowing_telemetry
        or row_workout_state_bounce
    )
    packet_is_isometric = (
        not packet_is_rowing
        and (
            workout_state == WORKOUT_STATE_ISOMETRIC
            or (workout_state is None and not current_mode_is_known_non_isometric)
        )
    )
    packet_is_custom_curve = (
        not packet_is_rowing
        and (
            workout_state == WORKOUT_STATE_CUSTOM_CURVE
            or (workout_state is None and current_was_in_custom_curve)
        )
    )
    packet_is_power_workout = (
        not packet_is_rowing
        and (
            workout_state in (WORKOUT_STATE_DAMPER, WORKOUT_STATE_ISOKINETIC)
            or (workout_state is None and current_was_in_power_workout)
        )
    )

    rep_telemetry = _parse_rep_telemetry(packet)
    custom_curve_telemetry = _parse_custom_curve_telemetry(packet, current) if packet_is_custom_curve else None
    rowing_telemetry = _parse_rowing_telemetry(packet, current, timestamp_millis) if packet_is_rowing else None
    power_workout_summary = _parse_power_workout_summary(packet) if packet_is_power_workout else None
    power_workout_telemetry = _parse_power_workout_telemetry(packet) if packet_is_power_workout else None
    isometric_telemetry = _parse_isometric_telemetry(packet, current, timestamp_millis) if packet_is_isometric else None
    isometric_waveform = _parse_isometric_waveform(packet, current) if packet_is_isometric else None
    workout_mode = (
        _row_workout_mode_label(fitness_mode)
        if packet_is_rowing and not row_workout_state_bounce
        else workout_mode_label(fitness_mode, workout_state)
    )

    leaving_isometric = workout_state is not None and workout_state != WORKOUT_STATE_ISOMETRIC
    entering_fresh_power_workout = (
        workout_state in (WORKOUT_STATE_DAMPER, WORKOUT_STATE_ISOKINETIC)
        and not current_was_in_power_workout
        and power_workout_summary is None
    )
    leaving_power_workout = (
        current_was_in_power_workout
        and workout_state is not None
        and workout_state not in (WORKOUT_STATE_DAMPER, WORKOUT_STATE_ISOKINETIC)
    )
    leaving_rowing = (
        current_was_in_rowing
        and workout_state is not None
        and workout_state not in (WORKOUT_STATE_ISOMETRIC, WORKOUT_STATE_ROWING)
        and not row_workout_state_bounce
    )
    retain_completed_isometric_attempt = (
        bool(current.isometric_waveform_samples_n)
        or current.isometric_peak_relative_force_percent is not None
    )
    has_collected_isometric_live_sample = (
        bool(current.isometric_waveform_samples_n)
        or current.isometric_peak_relative_force_percent is not None
        or current.isometric_telemetry_start_tick is not None
    )
    entering_fresh_isometric_screen = (
        workout_state == WORKOUT_STATE_ISOMETRIC
        and not current_was_in_isometric
        and current.isometric_current_force_n is None
        and current.isometric_telemetry_start_tick is None
        and not current.isometric_waveform_samples_n
        and isometric_telemetry is None
        and isometric_waveform is None
    )
    ready_isometric_without_telemetry = (
        workout_state == WORKOUT_STATE_ISOMETRIC
        and is_ready_for_workout_state(fitness_mode, workout_state)
        and isometric_telemetry is None
        and not has_collected_isometric_live_sample
    )
    current_has_rowing_telemetry = (
        current.rowing_distance_meters is not None
        or current.rowing_elapsed_millis is not None
        or current.rowing_pace_500_millis is not None
        or current.rowing_average_pace_500_millis is not None
        or current.rowing_stroke_rate_spm is not None
        or current.rowing_drive_force_lb is not None
        or bool(current.rowing_distance_samples_meters)
        or bool(current.rowing_force_samples_lb)
        or (current.rep_count or 0) > 0
    )
    ready_rowing_without_telemetry = (
        packet_is_rowing
        and workout_state == WORKOUT_STATE_ROWING
        and is_ready_for_workout_state(fitness_mode, workout_state)
        and rowing_telemetry is None
        and not current_has_rowing_telemetry
    )
    completed_legacy_isometric_attempt = (
        isometric_telemetry is not None
        and isometric_telemetry.current_force_n is None
        and isometric_telemetry.carrier_status_secondary == TELEMETRY_ISOMETRIC_COMPLETED_MARKER
    )
    merged_isometric_metrics_type = (
        isometric_metrics_type if isometric_metrics_type is not None else current.isometric_metrics_type
    )
    merged_isometric_body_weight_n = (
        float(isometric_body_weight_n) if isometric_body_weight_n is not None else current.isometric_body_weight_n
    )
    merged_isometric_body_weight_100g = (
        isometric_body_weight_100g if isometric_body_weight_100g is not None else current.isometric_body_weight_100g
    )
    merged_isometric_body_weight_lb = (
        float(isometric_body_weight_lb) if isometric_body_weight_lb is not None else current.isometric_body_weight_lb
    )
    merged_isometric_peak_force_n = (
        None
        if entering_fresh_isometric_screen or (leaving_isometric and not retain_completed_isometric_attempt)
        else (
            current.isometric_peak_force_n
            if leaving_isometric and retain_completed_isometric_attempt
            else (
                isometric_telemetry.peak_force_n
                if isometric_telemetry is not None and isometric_telemetry.peak_force_n is not None
                else (
                    current.isometric_peak_force_n
                    if isometric_telemetry is None or has_collected_isometric_live_sample
                    else None
                )
            )
        )
    )
    merged_isometric_peak_relative_force_percent = (
        None
        if entering_fresh_isometric_screen or (leaving_isometric and not retain_completed_isometric_attempt)
        else (
            current.isometric_peak_relative_force_percent
            if leaving_isometric and retain_completed_isometric_attempt
            else (
                isometric_telemetry.peak_relative_force_percent
                if isometric_telemetry is not None
                and (
                    isometric_telemetry.starting_new_attempt
                    or isometric_telemetry.peak_relative_force_percent is not None
                )
                else current.isometric_peak_relative_force_percent
            )
        )
    )
    if merged_isometric_peak_relative_force_percent is None:
        merged_isometric_peak_relative_force_percent = _derive_isometric_peak_relative_force_percent(
            peak_force_n=merged_isometric_peak_force_n,
            body_weight_n=merged_isometric_body_weight_n,
            metrics_type=merged_isometric_metrics_type,
        )
    current_peak_force_for_summary_reconciliation = current.isometric_peak_force_n
    summary_peak_force_for_reconciliation = (
        isometric_telemetry.peak_force_n
        if isometric_telemetry is not None
        else None
    )
    power_previous_force_tenths = (
        round(current.workout_live_force_lb * POWER_WORKOUT_FORCE_TENTHS_PER_LB)
        if current.workout_live_force_lb is not None
        else None
    )
    power_start_threshold_tenths = (
        _power_workout_start_threshold_tenths(
            previous_force_tenths_lb=power_previous_force_tenths,
            current_force_tenths_lb=power_workout_telemetry.force_tenths_lb,
            has_active_pull=current.workout_pull_start_tick is not None,
            phase=rep_telemetry.phase if rep_telemetry is not None else current.rep_phase,
        )
        if power_workout_telemetry is not None
        else None
    )
    power_crossed_start_threshold = power_start_threshold_tenths is not None
    power_interpolated_start_tick = (
        _interpolate_power_workout_start_tick(
            start_force_tenths_lb=(
                power_start_threshold_tenths
                if power_start_threshold_tenths is not None
                else POWER_WORKOUT_FALLBACK_START_FORCE_TENTHS_LB
            ),
            previous_force_tenths_lb=power_previous_force_tenths,
            previous_tick=current.workout_live_tick,
            current_force_tenths_lb=power_workout_telemetry.force_tenths_lb,
            current_tick=power_workout_telemetry.tick,
        )
        if power_workout_telemetry is not None and power_crossed_start_threshold
        else None
    )
    power_reset_pull = (
        power_workout_telemetry is not None
        and power_workout_telemetry.force_tenths_lb <= POWER_WORKOUT_RESET_FORCE_TENTHS_LB
        and current.workout_pull_start_tick is not None
        and current.workout_peak_force_tick is not None
    )
    resolved_power_start_tick = (
        None
        if leaving_power_workout or entering_fresh_power_workout
        else power_interpolated_start_tick
        if power_crossed_start_threshold
        else None
        if power_reset_pull
        else current.workout_pull_start_tick
    )
    active_power_start_tick = (
        power_interpolated_start_tick if power_crossed_start_threshold else current.workout_pull_start_tick
    )
    should_use_live_power_peak = (
        power_workout_telemetry is not None
        and active_power_start_tick is not None
        and power_workout_telemetry.force_tenths_lb >= POWER_WORKOUT_PRIMARY_START_FORCE_TENTHS_LB
        and (
            power_crossed_start_threshold
            or current.workout_peak_force_tick is None
            or current.workout_peak_force_lb is None
            or power_workout_telemetry.force_lb > current.workout_peak_force_lb
        )
    )
    live_power_time_to_peak_millis = (
        max(0, power_workout_telemetry.tick - active_power_start_tick)
        if should_use_live_power_peak and power_workout_telemetry is not None and active_power_start_tick is not None
        else None
    )
    summary_power_time_to_peak_millis = _corrected_power_workout_summary_time_to_peak_millis(
        power_workout_summary,
        current.workout_time_to_peak_millis,
    )
    should_rescale_sparse_waveform_to_summary = (
        isometric_telemetry is not None
        and isometric_telemetry.peak_relative_force_percent is not None
        and isometric_telemetry.current_force_n is None
        and current.isometric_current_force_n is None
        and current_peak_force_for_summary_reconciliation is not None
        and summary_peak_force_for_reconciliation is not None
        and 1 <= len(current.isometric_waveform_samples_n) <= MAX_SUMMARY_RECONCILIATION_SPARSE_SAMPLES
        and current_peak_force_for_summary_reconciliation
        > summary_peak_force_for_reconciliation + STALE_ISOMETRIC_SUMMARY_FORCE_TOLERANCE_N
    )
    if (
        should_rescale_sparse_waveform_to_summary
        and current_peak_force_for_summary_reconciliation is not None
        and summary_peak_force_for_reconciliation is not None
        and current_peak_force_for_summary_reconciliation > 0.0
        and summary_peak_force_for_reconciliation > 0.0
    ):
        scale = summary_peak_force_for_reconciliation / current_peak_force_for_summary_reconciliation
        rescaled_sparse_waveform_samples = tuple(max(sample * scale, 0.0) for sample in current.isometric_waveform_samples_n)
    else:
        rescaled_sparse_waveform_samples = current.isometric_waveform_samples_n

    if entering_fresh_isometric_screen:
        isometric_waveform_samples_n: tuple[float, ...] = ()
    elif leaving_isometric and retain_completed_isometric_attempt:
        isometric_waveform_samples_n = current.isometric_waveform_samples_n
    elif leaving_isometric:
        isometric_waveform_samples_n = ()
    elif isometric_waveform is not None:
        isometric_waveform_samples_n = isometric_waveform.samples_n
    elif isometric_telemetry is not None and isometric_telemetry.current_force_n is not None:
        base_samples = () if isometric_telemetry.starting_new_attempt else current.isometric_waveform_samples_n
        isometric_waveform_samples_n = (base_samples + (isometric_telemetry.current_force_n,))[-MAX_ISOMETRIC_WAVEFORM_SAMPLES:]
    elif should_rescale_sparse_waveform_to_summary:
        isometric_waveform_samples_n = rescaled_sparse_waveform_samples
    else:
        isometric_waveform_samples_n = current.isometric_waveform_samples_n

    if entering_fresh_isometric_screen:
        isometric_waveform_last_chunk_index = None
    elif leaving_isometric and retain_completed_isometric_attempt:
        isometric_waveform_last_chunk_index = current.isometric_waveform_last_chunk_index
    elif leaving_isometric:
        isometric_waveform_last_chunk_index = None
    elif isometric_waveform is not None:
        isometric_waveform_last_chunk_index = isometric_waveform.last_chunk_index
    elif isometric_telemetry is not None and isometric_telemetry.starting_new_attempt:
        isometric_waveform_last_chunk_index = None
    else:
        isometric_waveform_last_chunk_index = current.isometric_waveform_last_chunk_index

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
        force_lb=(
            rowing_telemetry.force_lb
            if rowing_telemetry is not None and rowing_telemetry.force_lb is not None
            else (
                custom_curve_telemetry.force_lb
                if custom_curve_telemetry is not None
                else _coalesce_float(wire_weight_lb, current.force_lb)
            )
        ),
        weight_lb=_coalesce_float(base_weight_lb, current.weight_lb),
        resistance_band_max_force_lb=_coalesce_float(resistance_band_max_force_lb, current.resistance_band_max_force_lb),
        resistance_band_length_cm=_coalesce_float(resistance_band_length_cm, current.resistance_band_length_cm),
        resistance_band_by_range_of_motion=(
            resistance_band_by_rom if resistance_band_by_rom is not None else current.resistance_band_by_range_of_motion
        ),
        resistance_band_inverse=(
            resistance_band_inverse if resistance_band_inverse is not None else current.resistance_band_inverse
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
            quick_cable_adjustment if quick_cable_adjustment is not None else current.quick_cable_adjustment
        ),
        damper_level_index=damper_level_index if damper_level_index is not None else current.damper_level_index,
        rowing_resistance_level=(
            rowing_resistance_level if rowing_resistance_level is not None else current.rowing_resistance_level
        ),
        rowing_simulated_wear_level=(
            rowing_simulated_wear_level if rowing_simulated_wear_level is not None else current.rowing_simulated_wear_level
        ),
        assist_mode_enabled=assist_mode_enabled if assist_mode_enabled is not None else current.assist_mode_enabled,
        chains_weight_lb=_coalesce_float(chains_weight_lb, current.chains_weight_lb),
        eccentric_weight_lb=_coalesce_float(eccentric_weight_lb, current.eccentric_weight_lb),
        inverse_chains=inverse_chains if inverse_chains is not None else current.inverse_chains,
        weight_training_extra_mode=(
            weight_training_extra_mode if weight_training_extra_mode is not None else current.weight_training_extra_mode
        ),
        app_current_screen_id=(
            None
            if leaving_rowing and app_current_screen_id is None
            else app_current_screen_id if app_current_screen_id is not None else current.app_current_screen_id
        ),
        fitness_ongoing_ui=(
            None
            if leaving_rowing and fitness_ongoing_ui is None
            else fitness_ongoing_ui if fitness_ongoing_ui is not None else current.fitness_ongoing_ui
        ),
        custom_curve_resistance_min_lb=(
            base_weight_lb
            if packet_is_custom_curve and base_weight_lb is not None
            else current.custom_curve_resistance_min_lb
        ),
        custom_curve_resistance_limit_lb=(
            max_allowed_force_lb
            if packet_is_custom_curve and max_allowed_force_lb is not None
            else current.custom_curve_resistance_limit_lb
        ),
        isokinetic_mode=isokinetic_mode if isokinetic_mode is not None else current.isokinetic_mode,
        isokinetic_target_speed_mms=(
            isokinetic_target_speed_mms if isokinetic_target_speed_mms is not None else current.isokinetic_target_speed_mms
        ),
        isokinetic_speed_limit_mms=(
            isokinetic_speed_limit_mms if isokinetic_speed_limit_mms is not None else current.isokinetic_speed_limit_mms
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
        isometric_metrics_type=merged_isometric_metrics_type,
        isometric_body_weight_n=merged_isometric_body_weight_n,
        isometric_body_weight_100g=merged_isometric_body_weight_100g,
        isometric_body_weight_lb=merged_isometric_body_weight_lb,
        isometric_current_force_n=(
            None
            if entering_fresh_isometric_screen or leaving_isometric or ready_isometric_without_telemetry or completed_legacy_isometric_attempt
            else (
                isometric_telemetry.current_force_n
                if isometric_telemetry is not None and isometric_telemetry.current_force_n is not None
                else (
                    current.isometric_current_force_n
                    if isometric_telemetry is None or has_collected_isometric_live_sample
                    else None
                )
            )
        ),
        isometric_peak_force_n=(
            merged_isometric_peak_force_n
        ),
        isometric_peak_relative_force_percent=(
            merged_isometric_peak_relative_force_percent
        ),
        isometric_elapsed_millis=(
            None
            if entering_fresh_isometric_screen or (leaving_isometric and not retain_completed_isometric_attempt)
            else (
                current.isometric_elapsed_millis
                if leaving_isometric and retain_completed_isometric_attempt
                else (
                    isometric_telemetry.elapsed_millis
                    if isometric_telemetry is not None and isometric_telemetry.elapsed_millis is not None
                    else (
                        current.isometric_elapsed_millis
                        if isometric_telemetry is None or has_collected_isometric_live_sample
                        else None
                    )
                )
            )
        ),
        isometric_telemetry_tick=(
            None
            if entering_fresh_isometric_screen or leaving_isometric
            else (isometric_telemetry.tick if isometric_telemetry is not None else current.isometric_telemetry_tick)
        ),
        isometric_telemetry_start_tick=(
            None
            if entering_fresh_isometric_screen or leaving_isometric
            else (isometric_telemetry.start_tick if isometric_telemetry is not None else current.isometric_telemetry_start_tick)
        ),
        isometric_carrier_force_n=(
            None
            if entering_fresh_isometric_screen or leaving_isometric
            else (
                isometric_telemetry.raw_carrier_force_n
                if isometric_telemetry is not None
                else current.isometric_carrier_force_n
            )
        ),
        isometric_carrier_status_primary=(
            None
            if entering_fresh_isometric_screen or leaving_isometric
            else (
                isometric_telemetry.carrier_status_primary
                if isometric_telemetry is not None
                else current.isometric_carrier_status_primary
            )
        ),
        isometric_carrier_status_secondary=(
            None
            if entering_fresh_isometric_screen or leaving_isometric
            else (
                isometric_telemetry.carrier_status_secondary
                if isometric_telemetry is not None
                else current.isometric_carrier_status_secondary
            )
        ),
        isometric_waveform_samples_n=isometric_waveform_samples_n,
        isometric_waveform_last_chunk_index=isometric_waveform_last_chunk_index,
        rowing_distance_meters=(
            None
            if ready_rowing_without_telemetry or leaving_rowing
            else (
                rowing_telemetry.distance_meters
                if rowing_telemetry is not None and rowing_telemetry.distance_meters is not None
                else current.rowing_distance_meters
            )
        ),
        rowing_elapsed_millis=(
            None
            if ready_rowing_without_telemetry or leaving_rowing
            else (
                rowing_telemetry.elapsed_millis
                if rowing_telemetry is not None and rowing_telemetry.elapsed_millis is not None
                else current.rowing_elapsed_millis
            )
        ),
        rowing_pace_500_millis=(
            None
            if ready_rowing_without_telemetry or leaving_rowing
            else (
                rowing_telemetry.pace_500_millis
                if rowing_telemetry is not None and rowing_telemetry.pace_500_millis is not None
                else current.rowing_pace_500_millis
            )
        ),
        rowing_average_pace_500_millis=(
            None
            if ready_rowing_without_telemetry or leaving_rowing
            else (
                rowing_telemetry.average_pace_500_millis
                if rowing_telemetry is not None and rowing_telemetry.average_pace_500_millis is not None
                else current.rowing_average_pace_500_millis
            )
        ),
        rowing_stroke_rate_spm=(
            None
            if ready_rowing_without_telemetry or leaving_rowing
            else (
                rowing_telemetry.stroke_rate_spm
                if rowing_telemetry is not None and rowing_telemetry.stroke_rate_spm is not None
                else current.rowing_stroke_rate_spm
            )
        ),
        rowing_drive_force_lb=(
            None
            if ready_rowing_without_telemetry or leaving_rowing
            else (
                rowing_telemetry.force_lb
                if rowing_telemetry is not None and rowing_telemetry.force_lb is not None
                else current.rowing_drive_force_lb
            )
        ),
        rowing_telemetry_start_millis=(
            None
            if ready_rowing_without_telemetry or leaving_rowing
            else (rowing_telemetry.start_millis if rowing_telemetry is not None else current.rowing_telemetry_start_millis)
        ),
        rowing_last_stroke_start_millis=(
            None
            if ready_rowing_without_telemetry or leaving_rowing
            else (
                rowing_telemetry.stroke_start_millis
                if rowing_telemetry is not None and rowing_telemetry.stroke_start_millis is not None
                else current.rowing_last_stroke_start_millis
            )
        ),
        rowing_distance_samples_meters=(
            ()
            if ready_rowing_without_telemetry or leaving_rowing
            else (
                rowing_telemetry.distance_samples_meters if rowing_telemetry is not None else current.rowing_distance_samples_meters
            )
        ),
        rowing_force_samples_lb=(
            ()
            if ready_rowing_without_telemetry or leaving_rowing
            else (rowing_telemetry.force_samples_lb if rowing_telemetry is not None else current.rowing_force_samples_lb)
        ),
        rowing_force_last_chunk_index=(
            None
            if ready_rowing_without_telemetry or leaving_rowing
            else (
                rowing_telemetry.last_chunk_index
                if rowing_telemetry is not None and rowing_telemetry.last_chunk_index is not None
                else current.rowing_force_last_chunk_index
            )
        ),
        workout_peak_force_lb=(
            None
            if leaving_power_workout or entering_fresh_power_workout
            else (
                power_workout_summary.peak_force_lb
                if power_workout_summary is not None and power_workout_summary.peak_force_lb is not None
                else (
                    power_workout_telemetry.force_lb
                    if should_use_live_power_peak and power_workout_telemetry is not None
                    else current.workout_peak_force_lb
                )
            )
        ),
        workout_peak_power_watts=(
            None
            if leaving_power_workout or entering_fresh_power_workout
            else (
                None
                if power_crossed_start_threshold
                else (
                    power_workout_summary.peak_power_watts
                    if power_workout_summary is not None and power_workout_summary.peak_power_watts is not None
                    else current.workout_peak_power_watts
                )
            )
        ),
        workout_time_to_peak_millis=(
            None
            if leaving_power_workout or entering_fresh_power_workout
            else (
                live_power_time_to_peak_millis
                if live_power_time_to_peak_millis is not None
                else (
                    summary_power_time_to_peak_millis
                    if summary_power_time_to_peak_millis is not None
                    else current.workout_time_to_peak_millis
                )
            )
        ),
        workout_live_force_lb=(
            None
            if leaving_power_workout or entering_fresh_power_workout
            else (
                power_workout_telemetry.force_lb
                if power_workout_telemetry is not None
                else current.workout_live_force_lb
            )
        ),
        workout_live_tick=(
            None
            if leaving_power_workout or entering_fresh_power_workout
            else (
                power_workout_telemetry.tick
                if power_workout_telemetry is not None
                else current.workout_live_tick
            )
        ),
        workout_pull_start_tick=resolved_power_start_tick,
        workout_peak_force_tick=(
            None
            if leaving_power_workout or entering_fresh_power_workout
            else (
                None
                if power_reset_pull
                else (
                    power_workout_telemetry.tick
                    if should_use_live_power_peak and power_workout_telemetry is not None
                    else current.workout_peak_force_tick
                )
            )
        ),
        set_count=(
            rep_telemetry.set_count if leaving_rowing and rep_telemetry is not None else
            0 if ready_rowing_without_telemetry else
            rowing_telemetry.set_count if rowing_telemetry is not None and rowing_telemetry.set_count is not None else
            custom_curve_telemetry.set_count if custom_curve_telemetry is not None else
            rep_telemetry.set_count if rep_telemetry is not None else
            current.set_count
        ),
        rep_count=(
            rep_telemetry.count if leaving_rowing and rep_telemetry is not None else
            0 if ready_rowing_without_telemetry else
            rowing_telemetry.rep_count if rowing_telemetry is not None and rowing_telemetry.rep_count is not None else
            custom_curve_telemetry.rep_count if custom_curve_telemetry is not None else
            rep_telemetry.count if rep_telemetry is not None else
            current.rep_count
        ),
        rep_phase=(
            rep_telemetry.phase if leaving_rowing and rep_telemetry is not None else
            "Ready" if ready_rowing_without_telemetry else
            rowing_telemetry.phase if rowing_telemetry is not None and rowing_telemetry.phase is not None else
            custom_curve_telemetry.phase if custom_curve_telemetry is not None else
            rep_telemetry.phase if rep_telemetry is not None else
            current.rep_phase
        ),
        workout_mode=(
            None if leaving_rowing and workout_mode is None else workout_mode or current.workout_mode
        ),
        fitness_mode=fitness_mode if fitness_mode is not None else current.fitness_mode,
        workout_state=workout_state if workout_state is not None else current.workout_state,
    )
    next_state = _apply_isometric_computed_metrics(next_state)
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
    elif workout_state == WORKOUT_STATE_ROWING:
        pass
    elif workout_state == WORKOUT_STATE_CUSTOM_CURVE:
        if state.custom_curve_resistance_limit_lb - state.custom_curve_resistance_min_lb < MIN_CUSTOM_CURVE_RESISTANCE_SPAN_LB:
            reasons.append(
                f"Custom Curve resistance range must span at least {MIN_CUSTOM_CURVE_RESISTANCE_SPAN_LB} lb.",
            )
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
        normalized = normalized_fitness_mode(mode)
        return normalized in (
            FITNESS_MODE_ISOMETRIC_ARMED,
            FITNESS_MODE_STRENGTH_LOADED,
            FITNESS_MODE_TEST_SCREEN,
        )
    if workout_state == WORKOUT_STATE_ROWING:
        return normalized_fitness_mode(mode) == FITNESS_MODE_ROWING_ACTIVE
    return is_loaded_fitness_mode(mode)


def is_ready_for_workout_state(mode: int | None, workout_state: int | None) -> bool:
    normalized = normalized_fitness_mode(mode)
    if workout_state == WORKOUT_STATE_ISOMETRIC:
        return normalized == FITNESS_MODE_STRENGTH_READY
    return normalized == FITNESS_MODE_STRENGTH_READY


def is_isokinetic_workout_state(workout_state: int | None) -> bool:
    return workout_state == WORKOUT_STATE_ISOKINETIC


def workout_mode_label(mode: int | None, workout_state: int | None) -> str | None:
    if mode is None and workout_state is None:
        return None

    if workout_state == WORKOUT_STATE_RESISTANCE_BAND:
        return f"Resistance Band, {_readiness_label(mode, workout_state)}"
    if workout_state == WORKOUT_STATE_ROWING:
        return _row_workout_mode_label(mode)
    if workout_state == WORKOUT_STATE_DAMPER:
        return f"Damper, {_readiness_label(mode, workout_state)}"
    if workout_state == WORKOUT_STATE_CUSTOM_CURVE:
        return f"Custom Curve, {_readiness_label(mode, workout_state)}"
    if workout_state == WORKOUT_STATE_ISOKINETIC:
        return f"Isokinetic, {_readiness_label(mode, workout_state)}"
    if workout_state == WORKOUT_STATE_ISOMETRIC:
        return f"Isometric Test, {_readiness_label(mode, workout_state)}"

    normalized = normalized_fitness_mode(mode)
    if normalized == FITNESS_MODE_STRENGTH_READY:
        mode_text = "Strength ready"
    elif normalized == FITNESS_MODE_STRENGTH_LOADED:
        mode_text = "Strength loaded"
    elif normalized == FITNESS_MODE_ROWING_ACTIVE:
        mode_text = "Rowing"
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


def _row_workout_mode_label(mode: int | None) -> str:
    if is_load_engaged_for_workout_state(mode, WORKOUT_STATE_ROWING):
        mode_text = "Live"
    elif is_ready_for_workout_state(mode, WORKOUT_STATE_ROWING):
        mode_text = "Ready"
    elif mode is None:
        mode_text = "state unknown"
    else:
        mode_text = f"mode {mode}"
    return f"Rowing, {mode_text}"


def _has_rowing_telemetry_payload(packet: ParsedVoltraPacket) -> bool:
    if packet.command_id == CMD_ISOMETRIC_STREAM:
        return len(packet.payload) == ROWING_B4_SHORT_BYTES
    if packet.command_id != CMD_TELEMETRY or not packet.payload:
        return False
    return packet.payload[0] in {ROWING_STATUS_TYPE, ROWING_WAVEFORM_TYPE, ROWING_SUMMARY_TYPE}


def _has_native_rowing_summary_payload(packet: ParsedVoltraPacket) -> bool:
    return (
        packet.command_id == CMD_TELEMETRY
        and len(packet.payload) >= ROWING_SUMMARY_MIN_BYTES
        and packet.payload[0] == ROWING_SUMMARY_TYPE
        and packet.payload[1] == ROWING_SUMMARY_LENGTH_MARKER
    )


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
class CustomCurveTelemetry:
    force_lb: float
    set_count: int
    rep_count: int
    phase: str


@dataclass(frozen=True, slots=True)
class IsometricTelemetry:
    current_force_n: float | None
    peak_force_n: float | None
    peak_relative_force_percent: float | None
    elapsed_millis: int | None
    tick: int
    start_tick: int | None
    starting_new_attempt: bool
    raw_carrier_force_n: float | None
    carrier_status_primary: int | None
    carrier_status_secondary: int | None


@dataclass(frozen=True, slots=True)
class IsometricWaveform:
    samples_n: tuple[float, ...]
    last_chunk_index: int


@dataclass(frozen=True, slots=True)
class IsometricForceSample:
    elapsed_millis: int
    force_n: float


@dataclass(frozen=True, slots=True)
class IsometricComputedMetrics:
    current_force_n: float | None
    peak_force_n: float | None
    duration_millis: int | None
    time_to_peak_millis: int | None
    rfd_100_n_per_s: float | None
    impulse_100_n_seconds: float | None
    graph_max_force_n: float
    waveform_average_step_millis: float | None


@dataclass(frozen=True, slots=True)
class RowingTelemetry:
    distance_meters: float | None
    elapsed_millis: int | None
    pace_500_millis: int | None
    average_pace_500_millis: int | None
    stroke_rate_spm: int | None
    force_lb: float | None
    start_millis: int
    stroke_start_millis: int | None
    distance_samples_meters: tuple[float, ...]
    force_samples_lb: tuple[float, ...]
    last_chunk_index: int | None
    set_count: int | None
    rep_count: int | None
    phase: str | None


@dataclass(frozen=True, slots=True)
class PowerWorkoutSummary:
    peak_force_lb: float | None
    peak_power_watts: int | None
    time_to_peak_millis: int | None
    allow_wide_lower_time_to_peak_correction: bool


@dataclass(frozen=True, slots=True)
class PowerWorkoutTelemetry:
    force_tenths_lb: int
    force_lb: float
    tick: int


def _apply_isometric_computed_metrics(state: VoltraState) -> VoltraState:
    samples = _build_isometric_force_samples(state)
    metrics = _compute_isometric_metrics(samples)
    has_trace_metrics = len(samples) >= 2
    has_waveform_trace = bool(samples)
    prefer_completed_summary = (
        state.isometric_current_force_n is None
        and state.isometric_peak_relative_force_percent is not None
        and state.isometric_peak_force_n is not None
        and state.isometric_elapsed_millis is not None
        and not has_trace_metrics
    )
    display_current_force_n = (
        metrics.current_force_n
        if state.isometric_current_force_n is not None and has_trace_metrics
        else state.isometric_current_force_n
    )
    display_peak_force_n = (
        state.isometric_peak_force_n
        if prefer_completed_summary
        else (
            metrics.peak_force_n or state.isometric_peak_force_n
            if has_trace_metrics or has_waveform_trace
            else state.isometric_peak_force_n or metrics.peak_force_n
        )
    )
    display_elapsed_millis = (
        state.isometric_elapsed_millis
        if prefer_completed_summary
        else (
            metrics.duration_millis or state.isometric_elapsed_millis
            if has_trace_metrics or has_waveform_trace
            else state.isometric_elapsed_millis or metrics.duration_millis
        )
    )
    display_peak_relative_force_percent = (
        state.isometric_peak_relative_force_percent
        if state.isometric_current_force_n is None
        else None
    )
    return replace(
        state,
        isometric_display_current_force_n=display_current_force_n,
        isometric_display_peak_force_n=display_peak_force_n,
        isometric_display_peak_relative_force_percent=display_peak_relative_force_percent,
        isometric_display_elapsed_millis=display_elapsed_millis,
        isometric_time_to_peak_millis=metrics.time_to_peak_millis,
        isometric_rfd_100_n_per_s=metrics.rfd_100_n_per_s,
        isometric_impulse_100_n_seconds=metrics.impulse_100_n_seconds,
        isometric_graph_max_force_n=metrics.graph_max_force_n,
        isometric_waveform_average_step_millis=metrics.waveform_average_step_millis,
    )


def _build_isometric_force_samples(state: VoltraState) -> list[IsometricForceSample]:
    samples: list[IsometricForceSample] = []
    waveform_samples = state.isometric_waveform_samples_n
    if waveform_samples:
        effective_duration_millis = (
            state.isometric_elapsed_millis
            if state.isometric_elapsed_millis is not None and state.isometric_elapsed_millis > 0
            else None
        )
        if len(waveform_samples) > 1 and effective_duration_millis is not None:
            step_millis = effective_duration_millis / (len(waveform_samples) - 1)
        else:
            step_millis = 4.0
        for index, force_n in enumerate(waveform_samples):
            samples.append(
                IsometricForceSample(
                    elapsed_millis=round(index * step_millis),
                    force_n=max(force_n, 0.0),
                ),
            )

    if state.load_engaged and state.isometric_current_force_n is not None and state.isometric_elapsed_millis is not None:
        next_sample = IsometricForceSample(
            elapsed_millis=state.isometric_elapsed_millis,
            force_n=max(state.isometric_current_force_n, 0.0),
        )
        if not samples:
            samples.append(next_sample)
        elif next_sample.elapsed_millis < samples[-1].elapsed_millis:
            samples = [next_sample]
        elif next_sample.elapsed_millis == samples[-1].elapsed_millis:
            samples[-1] = next_sample
        else:
            samples.append(next_sample)
    return samples


def _compute_isometric_metrics(samples: list[IsometricForceSample]) -> IsometricComputedMetrics:
    if not samples:
        return IsometricComputedMetrics(
            current_force_n=None,
            peak_force_n=None,
            duration_millis=None,
            time_to_peak_millis=None,
            rfd_100_n_per_s=None,
            impulse_100_n_seconds=None,
            graph_max_force_n=DEFAULT_ISOMETRIC_GRAPH_MAX_FORCE_N,
            waveform_average_step_millis=None,
        )

    ordered: list[IsometricForceSample] = []
    for sample in sorted(samples, key=lambda item: item.elapsed_millis):
        if ordered and ordered[-1].elapsed_millis == sample.elapsed_millis:
            ordered[-1] = sample
        else:
            ordered.append(sample)

    offset = ordered[0].elapsed_millis
    normalized = [
        IsometricForceSample(
            elapsed_millis=max(0, sample.elapsed_millis - offset),
            force_n=max(sample.force_n, 0.0),
        )
        for sample in ordered
    ]

    current_sample = normalized[-1]
    raw_peak = max(normalized, key=lambda item: item.force_n, default=None)
    peak_sample = _adjust_sparse_peak_sample(normalized, raw_peak) if raw_peak is not None else None
    graph_max_force_n = _compute_graph_max_force_n(normalized)
    waveform_average_step_millis = (
        sum(
            max(0, current.elapsed_millis - previous.elapsed_millis)
            for previous, current in zip(normalized, normalized[1:], strict=False)
        ) / (len(normalized) - 1)
        if len(normalized) > 1
        else None
    )
    has_dense_waveform = (
        waveform_average_step_millis is not None
        and waveform_average_step_millis <= MAX_DENSE_ISOMETRIC_WAVEFORM_STEP_MILLIS
    )

    if peak_sample is None or peak_sample.force_n < MIN_MEANINGFUL_ISOMETRIC_FORCE_N:
        return IsometricComputedMetrics(
            current_force_n=current_sample.force_n,
            peak_force_n=peak_sample.force_n if peak_sample is not None else None,
            duration_millis=current_sample.elapsed_millis,
            time_to_peak_millis=None,
            rfd_100_n_per_s=None,
            impulse_100_n_seconds=None,
            graph_max_force_n=graph_max_force_n,
            waveform_average_step_millis=waveform_average_step_millis,
        )

    duration_millis = current_sample.elapsed_millis
    time_to_peak_millis = peak_sample.elapsed_millis if has_dense_waveform else None
    if has_dense_waveform and duration_millis >= ISOMETRIC_WINDOW_100MS and len(normalized) >= 2:
        start_force_n = normalized[0].force_n
        force_at_100_n = _interpolate_isometric_force_at(normalized, ISOMETRIC_WINDOW_100MS)
        rfd_100_n_per_s = max(0.0, (force_at_100_n - start_force_n) / 0.1)
        impulse_100_n_seconds = max(
            0.0,
            _integrate_isometric_force_until(normalized, ISOMETRIC_WINDOW_100MS) / 1000.0,
        )
    else:
        rfd_100_n_per_s = None
        impulse_100_n_seconds = None

    return IsometricComputedMetrics(
        current_force_n=current_sample.force_n,
        peak_force_n=peak_sample.force_n,
        duration_millis=duration_millis,
        time_to_peak_millis=time_to_peak_millis,
        rfd_100_n_per_s=rfd_100_n_per_s,
        impulse_100_n_seconds=impulse_100_n_seconds,
        graph_max_force_n=graph_max_force_n,
        waveform_average_step_millis=waveform_average_step_millis,
    )


def _adjust_sparse_peak_sample(
    samples: list[IsometricForceSample],
    raw_peak: IsometricForceSample,
) -> IsometricForceSample:
    if len(samples) not in range(4, 9):
        return raw_peak
    peak_index = next(
        (
            index
            for index, sample in enumerate(samples)
            if sample.elapsed_millis == raw_peak.elapsed_millis and sample.force_n == raw_peak.force_n
        ),
        -1,
    )
    if peak_index <= 0 or peak_index >= len(samples) - 1:
        return raw_peak

    previous_sample = samples[peak_index - 1]
    next_sample = samples[peak_index + 1]
    neighbor_max_force_n = max(previous_sample.force_n, next_sample.force_n)
    neighbor_min_force_n = min(previous_sample.force_n, next_sample.force_n)
    isolated_spike = (
        raw_peak.force_n >= neighbor_max_force_n * SPARSE_PEAK_SPIKE_RATIO
        and (raw_peak.force_n - neighbor_min_force_n) >= SPARSE_PEAK_SPIKE_MIN_DELTA_N
    )
    if not isolated_spike:
        return raw_peak

    adjusted_force_n = neighbor_max_force_n + (
        (raw_peak.force_n - neighbor_max_force_n) * SPARSE_PEAK_RETAIN_FACTOR
    )
    return replace(raw_peak, force_n=adjusted_force_n)


def _compute_graph_max_force_n(samples: list[IsometricForceSample]) -> float:
    peak_force_n = max((sample.force_n for sample in samples), default=0.0)
    if peak_force_n <= DEFAULT_ISOMETRIC_GRAPH_MAX_FORCE_N:
        return DEFAULT_ISOMETRIC_GRAPH_MAX_FORCE_N
    return ceil(peak_force_n / ISOMETRIC_GRAPH_STEP_FORCE_N) * ISOMETRIC_GRAPH_STEP_FORCE_N


def _interpolate_isometric_force_at(
    samples: list[IsometricForceSample],
    target_millis: int,
) -> float:
    first_sample = samples[0]
    if target_millis <= first_sample.elapsed_millis:
        return first_sample.force_n
    previous_sample = first_sample
    for current_sample in samples[1:]:
        if target_millis <= current_sample.elapsed_millis:
            span_millis = max(1, current_sample.elapsed_millis - previous_sample.elapsed_millis)
            progress = (target_millis - previous_sample.elapsed_millis) / span_millis
            return previous_sample.force_n + (
                (current_sample.force_n - previous_sample.force_n) * progress
            )
        previous_sample = current_sample
    return samples[-1].force_n


def _integrate_isometric_force_until(
    samples: list[IsometricForceSample],
    target_millis: int,
) -> float:
    if len(samples) < 2:
        return 0.0
    area_n_millis = 0.0
    previous_sample = samples[0]
    for current_sample in samples[1:]:
        if target_millis <= previous_sample.elapsed_millis:
            break
        segment_end_millis = min(current_sample.elapsed_millis, target_millis)
        if segment_end_millis > previous_sample.elapsed_millis:
            end_force_n = (
                current_sample.force_n
                if segment_end_millis == current_sample.elapsed_millis
                else _interpolate_isometric_force_at(
                    [previous_sample, current_sample],
                    segment_end_millis,
                )
            )
            duration_millis = float(segment_end_millis - previous_sample.elapsed_millis)
            area_n_millis += ((previous_sample.force_n + end_force_n) / 2.0) * duration_millis
        if current_sample.elapsed_millis >= target_millis:
            break
        previous_sample = current_sample
    return area_n_millis


def _parse_rep_telemetry(packet: ParsedVoltraPacket) -> RepTelemetry | None:
    payload = packet.payload
    if packet.command_id != CMD_TELEMETRY or len(payload) < 6:
        return None
    if payload[0] != TELEMETRY_REP_TYPE or payload[1] != TELEMETRY_REP_LENGTH_MARKER:
        return None

    set_count = payload[TELEMETRY_SET_COUNT_OFFSET]
    rep_count = _u16be(payload, TELEMETRY_REP_COUNT_OFFSET)
    if not (0 <= set_count <= MAX_REASONABLE_SET_COUNT and 0 <= rep_count <= MAX_REASONABLE_REP_COUNT):
        return None
    return RepTelemetry(
        set_count=set_count,
        count=rep_count,
        phase=_rep_phase_label(payload[TELEMETRY_REP_PHASE_OFFSET]),
    )


def _parse_custom_curve_telemetry(
    packet: ParsedVoltraPacket,
    current: VoltraState,
) -> CustomCurveTelemetry | None:
    if packet.command_id == CMD_ISOMETRIC_STREAM:
        force_tenths_lb = _parse_custom_curve_b4_force_tenths_lb(packet.payload)
    elif packet.command_id == CMD_TELEMETRY:
        force_tenths_lb = _parse_custom_curve_vendor_force_tenths_lb(packet.payload)
    else:
        force_tenths_lb = None
    if force_tenths_lb is None or force_tenths_lb not in range(0, MAX_REASONABLE_CUSTOM_CURVE_FORCE_TENTHS_LB + 1):
        return None

    force_lb = force_tenths_lb / CUSTOM_CURVE_FORCE_TENTHS_PER_LB
    base_lb = (
        current.weight_lb
        if current.weight_lb is not None and 0.0 <= current.weight_lb <= float(MAX_CUSTOM_CURVE_RESISTANCE_LIMIT_LB)
        else float(DEFAULT_CUSTOM_CURVE_RESISTANCE_MIN_LB)
    )
    active_threshold_lb = max(
        base_lb + CUSTOM_CURVE_REP_ACTIVE_MARGIN_LB,
        base_lb * CUSTOM_CURVE_REP_ACTIVE_MULTIPLIER,
    )
    reset_threshold_lb = base_lb + CUSTOM_CURVE_REP_RESET_MARGIN_LB
    was_in_rep = current.rep_phase in CUSTOM_CURVE_ACTIVE_PHASES
    completed_rep = was_in_rep and force_lb <= reset_threshold_lb
    previous_force_lb = current.force_lb
    phase = (
        "Ready"
        if completed_rep or force_lb < active_threshold_lb
        else "Return"
        if previous_force_lb is not None and force_lb < previous_force_lb - CUSTOM_CURVE_REP_DIRECTION_DEADBAND_LB
        else "Pull"
    )
    rep_count = max(
        0,
        min(
            MAX_REASONABLE_REP_COUNT,
            (current.rep_count or 0) + (1 if completed_rep else 0),
        ),
    )
    if rep_count > 0:
        set_count = max(current.set_count or 1, 1)
    elif current.set_count is not None:
        set_count = current.set_count
    else:
        set_count = 0
    return CustomCurveTelemetry(
        force_lb=force_lb,
        set_count=set_count,
        rep_count=rep_count,
        phase=phase,
    )


def _parse_custom_curve_b4_force_tenths_lb(payload: bytes) -> int | None:
    if len(payload) not in (CUSTOM_CURVE_B4_SHORT_BYTES, CUSTOM_CURVE_B4_EXTENDED_BYTES):
        return None
    leading_force = _u16le(payload, 0)
    trailing_force = _u16le(payload, len(payload) - 2)
    if abs(leading_force - trailing_force) > CUSTOM_CURVE_B4_FORCE_MIRROR_TOLERANCE_TENTHS_LB:
        return None
    return leading_force


def _parse_custom_curve_vendor_force_tenths_lb(payload: bytes) -> int | None:
    if len(payload) != CUSTOM_CURVE_VENDOR_STATUS_BYTES:
        return None
    if payload[0] != TELEMETRY_ISOMETRIC_SUMMARY_TYPE:
        return None
    if payload[1] != TELEMETRY_ISOMETRIC_SUMMARY_LENGTH_MARKER:
        return None
    if payload[2] != WORKOUT_STATE_CUSTOM_CURVE:
        return None
    return _u16le(payload, CUSTOM_CURVE_VENDOR_FORCE_OFFSET)


def _parse_rowing_telemetry(
    packet: ParsedVoltraPacket,
    current: VoltraState,
    now_millis: int,
) -> RowingTelemetry | None:
    start_millis = current.rowing_telemetry_start_millis or now_millis
    if packet.command_id == CMD_ISOMETRIC_STREAM:
        return _parse_rowing_b4_telemetry(packet.payload, current, start_millis, now_millis)
    if packet.command_id != CMD_TELEMETRY or not packet.payload:
        return None
    packet_type = packet.payload[0]
    if packet_type == ROWING_STATUS_TYPE:
        return _parse_rowing_status_telemetry(packet.payload, current, start_millis, now_millis)
    if packet_type == ROWING_WAVEFORM_TYPE:
        return _parse_rowing_waveform_telemetry(packet.payload, current, start_millis, now_millis)
    if packet_type == ROWING_SUMMARY_TYPE:
        return _parse_rowing_summary_telemetry(packet.payload, current, start_millis)
    return None


def _parse_rowing_summary_telemetry(
    payload: bytes,
    current: VoltraState,
    start_millis: int,
) -> RowingTelemetry | None:
    if len(payload) < ROWING_SUMMARY_MIN_BYTES:
        return None
    if payload[0] != ROWING_SUMMARY_TYPE or payload[1] != ROWING_SUMMARY_LENGTH_MARKER:
        return None

    displayed_distance_value = _u32le(payload, ROWING_SUMMARY_DISTANCE_METERS_OFFSET)
    displayed_distance_meters = float(displayed_distance_value) if displayed_distance_value in range(0, 100_001) else None
    current_pace_value = _u32le(payload, ROWING_SUMMARY_CURRENT_PACE_TENTH_SECONDS_OFFSET)
    current_pace_500_millis = current_pace_value * 100 if current_pace_value in range(1, 36_001) else None
    average_pace_value = _u32le(payload, ROWING_SUMMARY_AVERAGE_PACE_TENTH_SECONDS_OFFSET)
    average_pace_500_millis = average_pace_value * 100 if average_pace_value in range(1, 36_001) else None
    summary_stroke_rate = (
        payload[ROWING_SUMMARY_STROKE_RATE_SPM_OFFSET]
        if payload[ROWING_SUMMARY_STROKE_RATE_SPM_OFFSET] in range(1, 81)
        else None
    )
    legacy_stroke_rate_value = _u32le(payload, ROWING_SUMMARY_LEGACY_STROKE_RATE_CENTI_SPM_OFFSET)
    legacy_stroke_rate = (
        round(legacy_stroke_rate_value / 100.0)
        if round(legacy_stroke_rate_value / 100.0) in range(1, 81)
        else None
    )
    stroke_rate_spm = summary_stroke_rate or legacy_stroke_rate or current.rowing_stroke_rate_spm
    stroke_count_value = _u32le(payload, ROWING_SUMMARY_STROKE_COUNT_CENTI_OFFSET)
    rounded_stroke_count = round(stroke_count_value / 100.0)
    stroke_count = rounded_stroke_count if rounded_stroke_count in range(0, MAX_REASONABLE_REP_COUNT + 1) else None

    if current.rowing_distance_meters is not None:
        if displayed_distance_meters is not None and displayed_distance_meters + 0.5 < current.rowing_distance_meters:
            monotonic_distance = current.rowing_distance_meters
        else:
            monotonic_distance = displayed_distance_meters
    else:
        monotonic_distance = displayed_distance_meters
    distance_samples = (
        (current.rowing_distance_samples_meters + (monotonic_distance,))[-MAX_ROWING_DISTANCE_SAMPLES:]
        if monotonic_distance is not None
        else current.rowing_distance_samples_meters
    )

    derived_elapsed = (
        round((monotonic_distance / 500.0) * average_pace_500_millis)
        if monotonic_distance is not None and monotonic_distance > 0.25 and average_pace_500_millis is not None
        else None
    )
    elapsed_millis = (
        derived_elapsed
        if derived_elapsed is not None and derived_elapsed in range(0, MAX_REASONABLE_ROWING_ELAPSED_MILLIS + 1)
        else current.rowing_elapsed_millis
    )
    if stroke_count is not None and stroke_count > 0:
        set_count = max(current.set_count or 1, 1)
    elif stroke_count is not None:
        set_count = current.set_count or 0
    else:
        set_count = current.set_count

    return RowingTelemetry(
        distance_meters=monotonic_distance,
        elapsed_millis=elapsed_millis,
        pace_500_millis=current_pace_500_millis or current.rowing_pace_500_millis,
        average_pace_500_millis=average_pace_500_millis or current.rowing_average_pace_500_millis,
        stroke_rate_spm=stroke_rate_spm,
        force_lb=current.rowing_drive_force_lb,
        start_millis=start_millis,
        stroke_start_millis=current.rowing_last_stroke_start_millis,
        distance_samples_meters=distance_samples,
        force_samples_lb=current.rowing_force_samples_lb,
        last_chunk_index=current.rowing_force_last_chunk_index,
        set_count=set_count,
        rep_count=stroke_count if stroke_count is not None else current.rep_count,
        phase=current.rep_phase or ("Rowing" if (monotonic_distance or 0.0) > 0.0 else "Ready"),
    )


def _parse_rowing_b4_telemetry(
    payload: bytes,
    current: VoltraState,
    start_millis: int,
    now_millis: int,
) -> RowingTelemetry | None:
    if len(payload) != ROWING_B4_SHORT_BYTES:
        return None
    force_tenths_lb = _u16le(payload, 0)
    if force_tenths_lb not in range(0, MAX_REASONABLE_ROWING_FORCE_TENTHS_LB + 1):
        return None

    force_lb = force_tenths_lb / ROWING_FORCE_TENTHS_PER_LB
    previous_force_lb = current.rowing_drive_force_lb if current.rowing_drive_force_lb is not None else current.force_lb
    phase = (
        "Ready"
        if force_lb < ROWING_RESET_FORCE_LB
        else "Recovery"
        if previous_force_lb is not None and force_lb < previous_force_lb - ROWING_FORCE_DIRECTION_DEADBAND_LB
        else "Drive"
        if force_lb >= ROWING_ACTIVE_FORCE_LB
        else "Ready"
    )
    force_samples = (current.rowing_force_samples_lb + (force_lb,))[-MAX_ROWING_FORCE_SAMPLES:]
    return _derive_rowing_telemetry(
        current=current,
        start_millis=start_millis,
        now_millis=now_millis,
        force_lb=force_lb,
        distance_samples_meters=current.rowing_distance_samples_meters,
        force_samples_lb=force_samples,
        last_chunk_index=current.rowing_force_last_chunk_index,
        set_count=current.set_count,
        rep_count=current.rep_count,
        phase=phase,
        distance_meters=current.rowing_distance_meters,
        stroke_rate_fallback=current.rowing_stroke_rate_spm,
        stroke_start_millis=current.rowing_last_stroke_start_millis,
    )


def _parse_rowing_status_telemetry(
    payload: bytes,
    current: VoltraState,
    start_millis: int,
    now_millis: int,
) -> RowingTelemetry | None:
    if len(payload) < ROWING_AA92_DISTANCE_OFFSET + 4:
        return None
    if payload[0] != ROWING_STATUS_TYPE:
        return None
    distance_centimeters = _u32le(payload, ROWING_AA92_DISTANCE_OFFSET)
    if distance_centimeters not in range(0, MAX_REASONABLE_ROWING_DISTANCE_CENTIMETERS + 1):
        return None
    distance_meters = distance_centimeters / 100.0
    previous_distance = current.rowing_distance_meters
    monotonic_distance = (
        previous_distance
        if previous_distance is not None and distance_meters + 0.5 < previous_distance
        else distance_meters
    )
    stroke_rate_fallback = payload[2] if len(payload) > 2 and payload[2] in range(1, 81) else None
    return _derive_rowing_telemetry(
        current=current,
        start_millis=start_millis,
        now_millis=now_millis,
        force_lb=current.rowing_drive_force_lb,
        distance_samples_meters=(current.rowing_distance_samples_meters + (monotonic_distance,))[-MAX_ROWING_DISTANCE_SAMPLES:],
        force_samples_lb=current.rowing_force_samples_lb,
        last_chunk_index=current.rowing_force_last_chunk_index,
        set_count=current.set_count,
        rep_count=current.rep_count,
        phase=current.rep_phase,
        distance_meters=monotonic_distance,
        stroke_rate_fallback=stroke_rate_fallback,
        stroke_start_millis=current.rowing_last_stroke_start_millis,
    )


def _parse_rowing_waveform_telemetry(
    payload: bytes,
    current: VoltraState,
    start_millis: int,
    now_millis: int,
) -> RowingTelemetry | None:
    if len(payload) < ROWING_WAVEFORM_HEADER_BYTES:
        return None
    if payload[0] != ROWING_WAVEFORM_TYPE or payload[1] not in TELEMETRY_ISOMETRIC_WAVEFORM_MARKERS:
        return None

    chunk_index = payload[2]
    declared_sample_count = _u16le(payload, 4)
    available_sample_count = (len(payload) - ROWING_WAVEFORM_HEADER_BYTES) // 2
    sample_count = min(declared_sample_count, available_sample_count)
    if sample_count <= 0:
        return None

    parsed_samples: list[float] = []
    for index in range(sample_count):
        offset = ROWING_WAVEFORM_HEADER_BYTES + (index * 2)
        sample_tenths_lb = _u16le(payload, offset)
        if sample_tenths_lb not in range(0, MAX_REASONABLE_ROWING_FORCE_TENTHS_LB + 1):
            return None
        parsed_samples.append(sample_tenths_lb / ROWING_FORCE_TENTHS_PER_LB)
    if not parsed_samples:
        return None

    should_reset = (
        chunk_index <= 1
        or current.rowing_force_last_chunk_index is None
        or chunk_index <= current.rowing_force_last_chunk_index
    )
    if should_reset:
        force_samples = tuple(parsed_samples)
    else:
        force_samples = (current.rowing_force_samples_lb + tuple(parsed_samples))[-MAX_ROWING_FORCE_SAMPLES:]
    force_lb = force_samples[-1] if force_samples else current.rowing_drive_force_lb
    return _derive_rowing_telemetry(
        current=current,
        start_millis=start_millis,
        now_millis=now_millis,
        force_lb=force_lb,
        distance_samples_meters=current.rowing_distance_samples_meters,
        force_samples_lb=force_samples,
        last_chunk_index=chunk_index,
        set_count=current.set_count,
        rep_count=current.rep_count,
        phase=current.rep_phase or "Drive",
        distance_meters=current.rowing_distance_meters,
        stroke_rate_fallback=None,
        stroke_start_millis=current.rowing_last_stroke_start_millis,
    )


def _derive_rowing_telemetry(
    *,
    current: VoltraState,
    start_millis: int,
    now_millis: int,
    force_lb: float | None,
    distance_samples_meters: tuple[float, ...],
    force_samples_lb: tuple[float, ...],
    last_chunk_index: int | None,
    set_count: int | None,
    rep_count: int | None,
    phase: str | None,
    distance_meters: float | None,
    stroke_rate_fallback: int | None,
    stroke_start_millis: int | None,
) -> RowingTelemetry:
    fallback_elapsed_millis = max(0, now_millis - start_millis)
    elapsed_millis = current.rowing_elapsed_millis or fallback_elapsed_millis
    strokes = rep_count if rep_count is not None else current.rep_count
    if stroke_rate_fallback is not None:
        stroke_rate_spm = stroke_rate_fallback
    elif fallback_elapsed_millis > 0 and strokes is not None and strokes > 0:
        stroke_rate_spm = max(1, min(80, round((strokes * 60_000.0) / fallback_elapsed_millis)))
    else:
        stroke_rate_spm = current.rowing_stroke_rate_spm

    calculated_pace_millis = None
    if distance_meters is not None and distance_meters > 0.25 and fallback_elapsed_millis > 0:
        calculated = round((fallback_elapsed_millis / distance_meters) * 500.0)
        if calculated in range(1_000, 3_600_001):
            calculated_pace_millis = calculated
    pace_500_millis = current.rowing_pace_500_millis or calculated_pace_millis
    average_pace_500_millis = current.rowing_average_pace_500_millis or pace_500_millis
    return RowingTelemetry(
        distance_meters=distance_meters,
        elapsed_millis=elapsed_millis,
        pace_500_millis=pace_500_millis,
        average_pace_500_millis=average_pace_500_millis,
        stroke_rate_spm=stroke_rate_spm,
        force_lb=force_lb,
        start_millis=start_millis,
        stroke_start_millis=stroke_start_millis,
        distance_samples_meters=distance_samples_meters[-MAX_ROWING_DISTANCE_SAMPLES:],
        force_samples_lb=force_samples_lb[-MAX_ROWING_FORCE_SAMPLES:],
        last_chunk_index=last_chunk_index,
        set_count=set_count,
        rep_count=rep_count,
        phase=phase,
    )


def _parse_power_workout_summary(packet: ParsedVoltraPacket) -> PowerWorkoutSummary | None:
    if packet.command_id != CMD_TELEMETRY or not packet.payload:
        return None
    if packet.payload[0] == POWER_WORKOUT_REP_SUMMARY_TYPE:
        return _parse_power_workout_rep_summary(packet.payload)
    if packet.payload[0] == POWER_WORKOUT_SUMMARY_TYPE:
        return _parse_power_workout_final_summary(packet.payload)
    return None


def _parse_power_workout_final_summary(payload: bytes) -> PowerWorkoutSummary | None:
    if len(payload) < POWER_WORKOUT_SUMMARY_MIN_BYTES:
        return None
    if payload[1] != POWER_WORKOUT_SUMMARY_LENGTH_MARKER:
        return None

    peak_force_tenths_lb = _u16le(payload, POWER_WORKOUT_SUMMARY_PEAK_FORCE_TENTHS_LB_OFFSET)
    peak_force_lb = (
        peak_force_tenths_lb / POWER_WORKOUT_FORCE_TENTHS_PER_LB
        if peak_force_tenths_lb in range(0, MAX_REASONABLE_POWER_WORKOUT_FORCE_TENTHS_LB + 1)
        else None
    )
    peak_power_watts = _u16le(payload, POWER_WORKOUT_SUMMARY_PEAK_POWER_WATTS_OFFSET)
    safe_peak_power_watts = peak_power_watts if peak_power_watts in range(0, MAX_REASONABLE_POWER_WORKOUT_WATTS + 1) else None
    time_to_peak_centiseconds = _u16le(payload, POWER_WORKOUT_SUMMARY_TIME_TO_PEAK_CENTISECONDS_OFFSET)
    time_to_peak_millis = (
        time_to_peak_centiseconds * 10
        if time_to_peak_centiseconds in range(1, MAX_REASONABLE_POWER_WORKOUT_TIME_TO_PEAK_CENTISECONDS + 1)
        else None
    )
    if peak_force_lb is None and safe_peak_power_watts is None and time_to_peak_millis is None:
        return None
    return PowerWorkoutSummary(
        peak_force_lb=peak_force_lb,
        peak_power_watts=safe_peak_power_watts,
        time_to_peak_millis=time_to_peak_millis,
        allow_wide_lower_time_to_peak_correction=False,
    )


def _parse_power_workout_rep_summary(payload: bytes) -> PowerWorkoutSummary | None:
    if len(payload) < POWER_WORKOUT_REP_SUMMARY_MIN_BYTES:
        return None
    if payload[1] != POWER_WORKOUT_REP_SUMMARY_LENGTH_MARKER:
        return None

    time_to_peak_centiseconds = _u16le(payload, POWER_WORKOUT_REP_SUMMARY_TIME_TO_PEAK_CENTISECONDS_OFFSET)
    if time_to_peak_centiseconds not in range(1, MAX_REASONABLE_POWER_WORKOUT_TIME_TO_PEAK_CENTISECONDS + 1):
        return None
    return PowerWorkoutSummary(
        peak_force_lb=None,
        peak_power_watts=None,
        time_to_peak_millis=time_to_peak_centiseconds * 10,
        allow_wide_lower_time_to_peak_correction=True,
    )


def _corrected_power_workout_summary_time_to_peak_millis(
    summary: PowerWorkoutSummary | None,
    current_millis: int | None,
) -> int | None:
    if summary is None or summary.time_to_peak_millis is None:
        return None
    if current_millis is None:
        return summary.time_to_peak_millis
    if summary.allow_wide_lower_time_to_peak_correction:
        return (
            summary.time_to_peak_millis
            if summary.time_to_peak_millis <= current_millis + POWER_WORKOUT_SUMMARY_TIME_CORRECTION_MAX_DELTA_MILLIS
            else None
        )
    return (
        summary.time_to_peak_millis
        if abs(summary.time_to_peak_millis - current_millis) <= POWER_WORKOUT_SUMMARY_TIME_CORRECTION_MAX_DELTA_MILLIS
        else None
    )


def _power_workout_start_threshold_tenths(
    *,
    previous_force_tenths_lb: int | None,
    current_force_tenths_lb: int,
    has_active_pull: bool,
    phase: str | None,
) -> int | None:
    if has_active_pull or phase != "Pull":
        return None
    if (
        previous_force_tenths_lb is not None
        and previous_force_tenths_lb < POWER_WORKOUT_PRIMARY_START_FORCE_TENTHS_LB
        and current_force_tenths_lb >= POWER_WORKOUT_PRIMARY_START_FORCE_TENTHS_LB
    ):
        return POWER_WORKOUT_PRIMARY_START_FORCE_TENTHS_LB
    if (
        previous_force_tenths_lb is None
        and current_force_tenths_lb >= POWER_WORKOUT_FALLBACK_START_FORCE_TENTHS_LB
    ):
        return POWER_WORKOUT_FALLBACK_START_FORCE_TENTHS_LB
    if (
        previous_force_tenths_lb is not None
        and previous_force_tenths_lb < POWER_WORKOUT_FALLBACK_START_FORCE_TENTHS_LB
        and current_force_tenths_lb >= POWER_WORKOUT_FALLBACK_START_FORCE_TENTHS_LB
    ):
        return POWER_WORKOUT_FALLBACK_START_FORCE_TENTHS_LB
    return None


def _parse_power_workout_telemetry(packet: ParsedVoltraPacket) -> PowerWorkoutTelemetry | None:
    if packet.command_id != CMD_TELEMETRY:
        return None
    payload = packet.payload
    if len(payload) < POWER_WORKOUT_LIVE_MIN_BYTES:
        return None
    if payload[0] != POWER_WORKOUT_LIVE_TYPE or payload[1] != POWER_WORKOUT_LIVE_LENGTH_MARKER:
        return None

    force_tenths_lb = _u16le(payload, POWER_WORKOUT_LIVE_FORCE_TENTHS_LB_OFFSET)
    if force_tenths_lb not in range(0, MAX_REASONABLE_POWER_WORKOUT_FORCE_TENTHS_LB + 1):
        return None
    tick = _u32le(payload, POWER_WORKOUT_LIVE_TICK_OFFSET)
    if tick < 0:
        return None
    return PowerWorkoutTelemetry(
        force_tenths_lb=force_tenths_lb,
        force_lb=force_tenths_lb / POWER_WORKOUT_FORCE_TENTHS_PER_LB,
        tick=tick,
    )


def _interpolate_power_workout_start_tick(
    *,
    start_force_tenths_lb: int,
    previous_force_tenths_lb: int | None,
    previous_tick: int | None,
    current_force_tenths_lb: int,
    current_tick: int,
) -> int:
    if (
        previous_force_tenths_lb is None
        or previous_tick is None
        or previous_tick >= current_tick
        or previous_force_tenths_lb >= start_force_tenths_lb
        or current_force_tenths_lb <= previous_force_tenths_lb
    ):
        return current_tick
    fraction = (
        (start_force_tenths_lb - previous_force_tenths_lb)
        / (current_force_tenths_lb - previous_force_tenths_lb)
    )
    return max(previous_tick, min(current_tick, round(previous_tick + ((current_tick - previous_tick) * fraction))))


def _derive_isometric_peak_relative_force_percent(
    *,
    peak_force_n: float | None,
    body_weight_n: float | None,
    metrics_type: int | None,
) -> float | None:
    if metrics_type is not None and metrics_type != ISOMETRIC_METRICS_TYPE_FORCE:
        return None
    if peak_force_n is None or not 0.0 <= peak_force_n <= MAX_REASONABLE_ISOMETRIC_FORCE_N:
        return None
    if body_weight_n is None or not MIN_REASONABLE_ISOMETRIC_BODY_WEIGHT_N <= body_weight_n <= MAX_REASONABLE_ISOMETRIC_BODY_WEIGHT_N:
        return None
    if body_weight_n == 0.0:
        return None
    return int((peak_force_n / body_weight_n) * 1000.0) / 10.0


def _parse_isometric_telemetry(
    packet: ParsedVoltraPacket,
    current: VoltraState,
    now_millis: int,
) -> IsometricTelemetry | None:
    return (
        _parse_legacy_isometric_telemetry(packet, current)
        or _parse_isometric_summary_telemetry(packet, current, now_millis)
        or _parse_b4_isometric_telemetry(packet, current, now_millis)
    )


def _parse_isometric_waveform(
    packet: ParsedVoltraPacket,
    current: VoltraState,
) -> IsometricWaveform | None:
    payload = packet.payload
    if packet.command_id != CMD_TELEMETRY or len(payload) < ISOMETRIC_WAVEFORM_HEADER_BYTES:
        return None
    if payload[0] != TELEMETRY_ISOMETRIC_WAVEFORM_TYPE or payload[1] not in TELEMETRY_ISOMETRIC_WAVEFORM_MARKERS:
        return None

    chunk_index = payload[2]
    declared_sample_count = _u16le(payload, 4)
    available_sample_count = (len(payload) - ISOMETRIC_WAVEFORM_HEADER_BYTES) // 2
    sample_count = min(declared_sample_count, available_sample_count)
    if sample_count <= 0:
        return None

    parsed_samples: list[float] = []
    for index in range(sample_count):
        offset = ISOMETRIC_WAVEFORM_HEADER_BYTES + (index * 2)
        sample_n = (_u16le(payload, offset) / 10.0) * LB_TO_NEWTONS
        if not 0.0 <= sample_n <= MAX_REASONABLE_ISOMETRIC_GRAPH_FORCE_N:
            return None
        parsed_samples.append(sample_n)
    if not parsed_samples:
        return None

    should_reset = (
        chunk_index <= 1
        or current.isometric_waveform_last_chunk_index is None
        or chunk_index <= current.isometric_waveform_last_chunk_index
    )
    if should_reset:
        merged_samples = tuple(parsed_samples)
    else:
        merged_samples = (
            current.isometric_waveform_samples_n + tuple(parsed_samples)
        )[-MAX_ISOMETRIC_WAVEFORM_SAMPLES:]
    return IsometricWaveform(samples_n=merged_samples, last_chunk_index=chunk_index)


def _parse_legacy_isometric_telemetry(
    packet: ParsedVoltraPacket,
    current: VoltraState,
) -> IsometricTelemetry | None:
    payload = packet.payload
    if packet.command_id != CMD_TELEMETRY or len(payload) < TELEMETRY_ISOMETRIC_MIN_BYTES:
        return None
    if payload[0] != TELEMETRY_REP_TYPE or payload[1] != TELEMETRY_REP_LENGTH_MARKER:
        return None
    if any(byte != 0 for byte in payload[2:11]) or any(byte != 0 for byte in payload[31:43]):
        return None

    tick = _u32le(payload, TELEMETRY_ISOMETRIC_TICK_OFFSET)
    status_primary = _u16le(payload, TELEMETRY_ISOMETRIC_STATUS_PRIMARY_OFFSET)
    status_secondary = _u16le(payload, TELEMETRY_ISOMETRIC_STATUS_SECONDARY_OFFSET)
    raw_carrier_force_n = (_u16le(payload, TELEMETRY_ISOMETRIC_FORCE_OFFSET) / 10.0) * LEGACY_ISOMETRIC_COARSE_FORCE_SCALE

    if status_secondary in TELEMETRY_ISOMETRIC_EXTENDED_LIVE_FORCE_MARKERS:
        current_force_n = status_primary * LEGACY_ISOMETRIC_PULL_FORCE_SCALE
        if not 0.0 <= current_force_n <= MAX_REASONABLE_ISOMETRIC_FORCE_N:
            return None
        starting_new_attempt = (
            current.isometric_current_force_n is None
            or current.isometric_telemetry_start_tick is None
            or current.isometric_carrier_status_secondary not in TELEMETRY_ISOMETRIC_EXTENDED_LIVE_FORCE_MARKERS
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
            peak_relative_force_percent=current.isometric_peak_relative_force_percent,
            elapsed_millis=elapsed_millis,
            tick=tick,
            start_tick=start_tick,
            starting_new_attempt=starting_new_attempt,
            raw_carrier_force_n=raw_carrier_force_n,
            carrier_status_primary=status_primary,
            carrier_status_secondary=status_secondary,
        )

    if (
        status_primary == 0
        and status_secondary == TELEMETRY_ISOMETRIC_COARSE_LIVE_FORCE_MARKER
        and TELEMETRY_ISOMETRIC_COARSE_LIVE_FORCE_RANGE_N[0]
        <= raw_carrier_force_n
        <= TELEMETRY_ISOMETRIC_COARSE_LIVE_FORCE_RANGE_N[1]
    ):
        current_force_n = raw_carrier_force_n
        starting_new_attempt = (
            current.isometric_current_force_n is None
            or current.isometric_telemetry_start_tick is None
            or current.isometric_carrier_status_secondary != TELEMETRY_ISOMETRIC_COARSE_LIVE_FORCE_MARKER
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
            peak_relative_force_percent=current.isometric_peak_relative_force_percent,
            elapsed_millis=elapsed_millis,
            tick=tick,
            start_tick=start_tick,
            starting_new_attempt=starting_new_attempt,
            raw_carrier_force_n=raw_carrier_force_n,
            carrier_status_primary=status_primary,
            carrier_status_secondary=status_secondary,
        )

    if status_secondary not in {
        TELEMETRY_ISOMETRIC_ACTIVE_MARKER,
        TELEMETRY_ISOMETRIC_PROGRESS_MARKER,
        TELEMETRY_ISOMETRIC_READY_MARKER,
        TELEMETRY_ISOMETRIC_ARMED_MARKER,
        TELEMETRY_ISOMETRIC_COMPLETED_MARKER,
    }:
        return None

    retain_completed_attempt = (
        bool(current.isometric_waveform_samples_n)
        or current.isometric_peak_relative_force_percent is not None
        or current.isometric_telemetry_start_tick is not None
    )
    return IsometricTelemetry(
        current_force_n=None,
        peak_force_n=current.isometric_peak_force_n if retain_completed_attempt else None,
        peak_relative_force_percent=(
            current.isometric_peak_relative_force_percent if retain_completed_attempt else None
        ),
        elapsed_millis=current.isometric_elapsed_millis if retain_completed_attempt else None,
        tick=tick,
        start_tick=current.isometric_telemetry_start_tick if retain_completed_attempt else None,
        starting_new_attempt=False,
        raw_carrier_force_n=raw_carrier_force_n,
        carrier_status_primary=status_primary,
        carrier_status_secondary=status_secondary,
    )


def _parse_isometric_summary_telemetry(
    packet: ParsedVoltraPacket,
    current: VoltraState,
    now_millis: int,
) -> IsometricTelemetry | None:
    payload = packet.payload
    if packet.command_id != CMD_TELEMETRY or len(payload) != TELEMETRY_ISOMETRIC_SUMMARY_BYTES:
        return None
    if (
        payload[0] != TELEMETRY_ISOMETRIC_SUMMARY_TYPE
        or payload[1] != TELEMETRY_ISOMETRIC_SUMMARY_LENGTH_MARKER
    ):
        return None

    has_collected_attempt_evidence = (
        current.isometric_telemetry_start_tick is not None
        or current.isometric_current_force_n is not None
        or bool(current.isometric_waveform_samples_n)
    )
    if not has_collected_attempt_evidence:
        return None

    peak_force_tenths_n = _u16le(payload, TELEMETRY_ISOMETRIC_SUMMARY_PEAK_FORCE_OFFSET)
    peak_relative_tenths_percent = _u16le(payload, TELEMETRY_ISOMETRIC_SUMMARY_PEAK_RELATIVE_FORCE_OFFSET)
    duration_seconds = _u16le(payload, TELEMETRY_ISOMETRIC_SUMMARY_DURATION_SECONDS_OFFSET)
    if not 0 <= peak_force_tenths_n <= int(MAX_REASONABLE_ISOMETRIC_FORCE_N * 10):
        return None
    if not 0 <= peak_relative_tenths_percent <= MAX_REASONABLE_ISOMETRIC_RELATIVE_FORCE_TENTHS_PERCENT:
        return None
    if not 0 <= duration_seconds <= MAX_REASONABLE_ISOMETRIC_DURATION_SECONDS:
        return None

    peak_force_n = peak_force_tenths_n / 10.0
    elapsed_millis = duration_seconds * 1_000
    summary_should_override_sparse_carrier_trace = (
        current.isometric_current_force_n is None
        and current.isometric_peak_relative_force_percent is None
        and 1 <= len(current.isometric_waveform_samples_n) <= MAX_SUMMARY_RECONCILIATION_SPARSE_SAMPLES
        and current.isometric_carrier_status_secondary == TELEMETRY_ISOMETRIC_ARMED_MARKER
    )
    summary_looks_stale = (
        current.isometric_peak_force_n is not None
        and peak_force_n + STALE_ISOMETRIC_SUMMARY_FORCE_TOLERANCE_N < current.isometric_peak_force_n
    ) or (
        current.isometric_elapsed_millis is not None
        and elapsed_millis + STALE_ISOMETRIC_SUMMARY_ELAPSED_TOLERANCE_MILLIS < current.isometric_elapsed_millis
    )
    if summary_looks_stale and not summary_should_override_sparse_carrier_trace:
        return None

    return IsometricTelemetry(
        current_force_n=None,
        peak_force_n=peak_force_n,
        peak_relative_force_percent=peak_relative_tenths_percent / 10.0,
        elapsed_millis=elapsed_millis,
        tick=current.isometric_telemetry_tick or now_millis,
        start_tick=current.isometric_telemetry_start_tick,
        starting_new_attempt=False,
        raw_carrier_force_n=current.isometric_carrier_force_n,
        carrier_status_primary=current.isometric_carrier_status_primary,
        carrier_status_secondary=current.isometric_carrier_status_secondary,
    )


def _parse_b4_isometric_telemetry(
    packet: ParsedVoltraPacket,
    current: VoltraState,
    now_millis: int,
) -> IsometricTelemetry | None:
    payload = packet.payload
    if packet.command_id != CMD_ISOMETRIC_STREAM:
        return None
    if len(payload) == 8:
        return (
            _parse_legacy_b4_isometric_telemetry(payload, current, now_millis)
            or _parse_modern_b4_isometric_telemetry(payload, current, now_millis)
        )
    if len(payload) == 12:
        return _parse_extended_modern_b4_isometric_telemetry(payload, current, now_millis)
    return None


def _parse_legacy_b4_isometric_telemetry(
    payload: bytes,
    current: VoltraState,
    now_millis: int,
) -> IsometricTelemetry | None:
    if _u16le(payload, 2) not in LEGACY_ISOMETRIC_STREAM_VARIANTS:
        return None
    if _u16le(payload, 6) not in range(ISOMETRIC_SAMPLE_RATE_MIN, ISOMETRIC_SAMPLE_RATE_MAX + 1):
        return None

    current_force_n = _u16le(payload, 0) * LB_TO_NEWTONS
    if not 0.0 <= current_force_n <= MAX_REASONABLE_ISOMETRIC_FORCE_N:
        return None
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
        peak_relative_force_percent=None,
        elapsed_millis=elapsed_millis,
        tick=now_millis,
        start_tick=start_tick,
        starting_new_attempt=starting_new_attempt,
        raw_carrier_force_n=current_force_n,
        carrier_status_primary=_u16le(payload, 2),
        carrier_status_secondary=None,
    )


def _parse_modern_b4_isometric_telemetry(
    payload: bytes,
    current: VoltraState,
    now_millis: int,
) -> IsometricTelemetry | None:
    current_force_n = float(_u16le(payload, 0))
    status_word = _u16le(payload, 2)
    reserved_word = _u16le(payload, 4)
    trailing_word = _u16le(payload, 6)
    if not 0.0 <= current_force_n <= MAX_REASONABLE_ISOMETRIC_FORCE_N:
        return None
    if status_word not in range(0, MAX_REASONABLE_ISOMETRIC_STATUS_WORD + 1):
        return None
    if reserved_word not in range(0, MAX_REASONABLE_ISOMETRIC_AUX_WORD + 1):
        return None
    if trailing_word not in range(0, MAX_REASONABLE_ISOMETRIC_AUX_WORD + 1):
        return None

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
        peak_relative_force_percent=None,
        elapsed_millis=elapsed_millis,
        tick=now_millis,
        start_tick=start_tick,
        starting_new_attempt=starting_new_attempt,
        raw_carrier_force_n=current_force_n,
        carrier_status_primary=status_word,
        carrier_status_secondary=None,
    )


def _parse_extended_modern_b4_isometric_telemetry(
    payload: bytes,
    current: VoltraState,
    now_millis: int,
) -> IsometricTelemetry | None:
    current_force_n = float(_u16le(payload, 0))
    aux_peak_word = _u16le(payload, 2)
    aux_elapsed_word = _u16le(payload, 4)
    status_word = _u16le(payload, 6)
    status_aux_word = _u16le(payload, 8)
    trailing_word = _u16le(payload, 10)
    if not 0.0 <= current_force_n <= MAX_REASONABLE_ISOMETRIC_FORCE_N:
        return None
    if aux_peak_word not in range(0, MAX_REASONABLE_ISOMETRIC_AUX_WORD + 1):
        return None
    if aux_elapsed_word not in range(0, MAX_REASONABLE_ISOMETRIC_AUX_WORD + 1):
        return None
    if status_word not in range(0, MAX_REASONABLE_ISOMETRIC_AUX_WORD + 1):
        return None
    if status_aux_word not in range(0, MAX_REASONABLE_ISOMETRIC_AUX_WORD + 1):
        return None
    if trailing_word not in range(0, MAX_REASONABLE_ISOMETRIC_AUX_WORD + 1):
        return None

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
        peak_relative_force_percent=None,
        elapsed_millis=elapsed_millis,
        tick=now_millis,
        start_tick=start_tick,
        starting_new_attempt=starting_new_attempt,
        raw_carrier_force_n=current_force_n,
        carrier_status_primary=status_word,
        carrier_status_secondary=status_aux_word,
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


def _u16be(payload: bytes, offset: int) -> int:
    if offset + 1 >= len(payload):
        return -1
    return int.from_bytes(payload[offset:offset + 2], byteorder="big", signed=False)


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
