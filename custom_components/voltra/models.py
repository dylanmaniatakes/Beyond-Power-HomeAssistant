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
    rowing_resistance_level: int | None = 4
    rowing_simulated_wear_level: int | None = 8
    rowing_target_meters: int | None = None
    assist_mode_enabled: bool | None = None
    chains_weight_lb: float | None = None
    eccentric_weight_lb: float | None = None
    inverse_chains: bool | None = None
    weight_training_extra_mode: int | None = None
    app_current_screen_id: int | None = None
    fitness_ongoing_ui: int | None = None
    custom_curve_points: tuple[float, float, float, float] = (0.0, 0.24696325, 0.5802966, 1.0)
    custom_curve_resistance_min_lb: int = 5
    custom_curve_resistance_limit_lb: int = 100
    custom_curve_range_of_motion_in: int = 117
    isokinetic_mode: int | None = None
    isokinetic_target_speed_mms: int | None = None
    isokinetic_speed_limit_mms: int | None = None
    isokinetic_constant_resistance_lb: float | None = None
    isokinetic_max_eccentric_load_lb: float | None = None
    isometric_max_force_lb: float | None = None
    isometric_max_duration_seconds: int | None = None
    isometric_metrics_type: int | None = None
    isometric_body_weight_n: float | None = None
    isometric_body_weight_100g: int | None = None
    isometric_body_weight_lb: float | None = None
    isometric_current_force_n: float | None = None
    isometric_peak_force_n: float | None = None
    isometric_peak_relative_force_percent: float | None = None
    isometric_elapsed_millis: int | None = None
    isometric_display_current_force_n: float | None = None
    isometric_display_peak_force_n: float | None = None
    isometric_display_peak_relative_force_percent: float | None = None
    isometric_display_elapsed_millis: int | None = None
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
    rowing_distance_meters: float | None = None
    rowing_elapsed_millis: int | None = None
    rowing_pace_500_millis: int | None = None
    rowing_average_pace_500_millis: int | None = None
    rowing_stroke_rate_spm: int | None = None
    rowing_drive_force_lb: float | None = None
    rowing_telemetry_start_millis: int | None = None
    rowing_last_stroke_start_millis: int | None = None
    rowing_distance_samples_meters: tuple[float, ...] = field(default_factory=tuple)
    rowing_force_samples_lb: tuple[float, ...] = field(default_factory=tuple)
    rowing_force_last_chunk_index: int | None = None
    workout_peak_force_lb: float | None = None
    workout_peak_power_watts: int | None = None
    workout_time_to_peak_millis: int | None = None
    workout_live_force_lb: float | None = None
    workout_live_tick: int | None = None
    workout_pull_start_tick: int | None = None
    workout_peak_force_tick: int | None = None
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
