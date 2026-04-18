# Voice Assistant Notes

Home Assistant stores voice aliases in the voice/expose layer, not inside the integration entity definitions.
That means this integration can improve names and device classes, but the exact extra phrases you want still need
to be added in Home Assistant.

Official docs:

- Assist / shared aliases: https://www.home-assistant.io/voice_control/aliases
- Google Assistant aliases in YAML: https://www.home-assistant.io/integrations/google_assistant/

## Recommended names

The integration now uses clearer voice-oriented entity names:

- `number.*_weight`
- `cover.*_resistance_level`
- `select.*_mode`
- `number.*_band_force`
- `number.*_chains`
- `number.*_eccentric`
- `switch.*_load`

## Recommended aliases

Add these in `Settings > Voice assistants > Expose` for the exposed entities you actually use.

- `Weight`
  - `target load`
  - `target weight`
  - `load weight`
  - `voltra weight`
- `Resistance level`
  - `resistance`
  - `weight level`
  - `resistance level`
- `Band force`
  - `band resistance`
  - `resistance band`
  - `band load`
- `Mode`
  - `workout mode`
  - `training mode`
- `Load`
  - `loaded`
  - `load state`
- `Chains`
  - `chain weight`
- `Eccentric`
  - `eccentric load`
- `Assist`
  - `assist mode`
- `Damper level`
  - `damper`
- `Target speed`
  - `speed`
  - `isokinetic speed`
- `Speed limit`
  - `max speed`

## Example Google Assistant YAML

Adjust the entity IDs to match your Home Assistant instance.

```yaml
google_assistant:
  entity_config:
    number.beyond_power_voltra_weight:
      aliases:
        - target load
        - target weight
        - voltra weight
    cover.beyond_power_voltra_resistance_level:
      aliases:
        - resistance
        - resistance level
        - weight level
    number.beyond_power_voltra_band_force:
      aliases:
        - band resistance
        - band force
    select.beyond_power_voltra_mode:
      aliases:
        - workout mode
        - training mode
```
