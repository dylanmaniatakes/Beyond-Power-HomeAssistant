from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True, slots=True)
class VoltraState:
    address: str
    configured_name: str | None = None
    device_name: str | None = None
    available: bool = False
    connected: bool = False
    protocol_validated: bool = False
    status_message: str = "Waiting for connection."
    last_error: str | None = None
    last_updated: datetime | None = None
    battery_percent: int | None = None
    firmware_version: str | None = None
    serial_number: str | None = None
    activation_state: str | None = None
    cable_length_cm: float | None = None
    cable_offset_cm: float | None = None
    force_lb: float | None = None
    weight_lb: float | None = None
    resistance_band_max_force_lb: float | None = None
    resistance_band_length_cm: float | None = None
    resistance_band_by_range_of_motion: bool | None = None
    resistance_band_inverse: bool | None = None
    resistance_band_curve_logarithm: bool | None = None
    resistance_experience_intense: bool | None = None
    quick_cable_adjustment: bool | None = None
    damper_level_index: int | None = None
    assist_mode_enabled: bool | None = None
    chains_weight_lb: float | None = None
    eccentric_weight_lb: float | None = None
    inverse_chains: bool | None = None
    weight_training_extra_mode: int | None = None
    isokinetic_mode: int | None = None
    isokinetic_target_speed_mms: int | None = None
    isokinetic_speed_limit_mms: int | None = None
    isokinetic_constant_resistance_lb: float | None = None
    isokinetic_max_eccentric_load_lb: float | None = None
    isometric_max_force_lb: float | None = None
    isometric_max_duration_seconds: int | None = None
    isometric_current_force_n: float | None = None
    isometric_peak_force_n: float | None = None
    isometric_peak_relative_force_percent: float | None = None
    isometric_elapsed_millis: int | None = None
    isometric_telemetry_tick: int | None = None
    isometric_telemetry_start_tick: int | None = None
    isometric_carrier_force_n: float | None = None
    isometric_carrier_status_primary: int | None = None
    isometric_carrier_status_secondary: int | None = None
    isometric_waveform_samples_n: tuple[float, ...] = field(default_factory=tuple)
    isometric_waveform_last_chunk_index: int | None = None
    isometric_time_to_peak_millis: int | None = None
    isometric_rfd_100_n_per_s: float | None = None
    isometric_impulse_100_n_seconds: float | None = None
    isometric_graph_max_force_n: float | None = None
    isometric_waveform_average_step_millis: float | None = None
    set_count: int | None = None
    rep_count: int | None = None
    rep_phase: str | None = None
    workout_mode: str | None = None
    can_load: bool = False
    safety_reasons: tuple[str, ...] = field(
        default_factory=lambda: ("Device state has not been parsed yet.",),
    )
    low_battery: bool | None = None
    locked: bool | None = None
    child_locked: bool | None = None
    active_ota: bool | None = None
    parsed_device_state: bool = False
    workout_state: int | None = None
    fitness_mode: int | None = None
    load_engaged: bool | None = None
    ready: bool | None = None

    @property
    def display_name(self) -> str:
        return self.device_name or self.configured_name or "Voltra"
