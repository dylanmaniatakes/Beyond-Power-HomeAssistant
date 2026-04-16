# Beyond Power Voltra Dashboard Template

This folder contains a built-in Lovelace dashboard template for the `Beyond Power Voltra` integration.

It uses only standard Home Assistant cards and features, so it does not require HACS frontend cards.

## Files

- `beyond_power_voltra_dashboard.yaml`: a ready-to-import dashboard template

## Before You Import

The template assumes your entity IDs use the default prefix:

- `beyond_power_voltra`

If you kept the default integration/device name, that will usually be correct.

If your entity IDs are different:

1. Open Developer Tools > States in Home Assistant.
2. Search for `voltra`.
3. Find the prefix used by your entities.
4. Replace `beyond_power_voltra` throughout the YAML file before importing.

## Import Options

### Option 1: YAML dashboard

1. Go to Settings > Dashboards.
2. Add a new dashboard.
3. Choose YAML mode.
4. Paste in the contents of `beyond_power_voltra_dashboard.yaml`.

### Option 2: Raw configuration editor

1. Open an existing dashboard.
2. Open the dashboard menu.
3. Choose Raw configuration editor.
4. Paste in the dashboard contents or copy the cards you want.

## Layout Notes

The template is designed around the integration's current entity model:

- a quick session overview at the top
- live telemetry in the middle
- mode-specific controls that appear only for the active workout mode
- a settings/diagnostics section at the bottom

This keeps the dashboard easy to use without forcing every control to be visible at once.
