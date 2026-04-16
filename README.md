# Beyond Power Voltra Home Assistant Integration

This folder contains a custom Home Assistant integration that talks to a Beyond Power Voltra directly over Bluetooth Low Energy.

Creator note: Technogizguy / Dylan Maniatakes.

It is built from the recovered protocol work already encoded in the Android app:

- official VOLTRA GATT service and characteristic UUIDs
- the captured read-only bootstrap/handshake sequence
- the recovered `0x55` frame format and CRC rules
- confirmed parameter IDs for Weight Training, Resistance Band, Damper, and Isokinetic controls
- live notification parsing for battery, reps, sets, cable length, load state, and other status

## Branding

- Home Assistant name: `Beyond Power Voltra`
- Local brand assets: `custom_components/voltra/brand/icon.png` and `logo.png`
- Source image: Beyond Power logo provided in this workspace

## What It Exposes

The custom component creates a BLE-backed Beyond Power Voltra device with:

- sensors for battery, force, cable length, reps, sets, status, serial, firmware, activation state, and Isometric telemetry
- switches for loaded, assist, and inverse chains
- numbers for target load, band force/length, Damper level, cable offset, Weight Training settings, and Isokinetic settings
- selects for workout mode, resistance settings, and the Isokinetic eccentric mode
- buttons for refresh and cable-length adjustment mode

## Safety Model

The integration intentionally mirrors the Android app's conservative behavior:

- it must see a valid VOLTRA response frame before control entities become available
- load uses the parsed safety state and will refuse to engage if the device does not look ready
- only the command set already promoted in the Android notes is implemented
- Custom Curve, OTA, and undocumented raw writes are intentionally excluded

## Install

1. Copy `custom_components/voltra` into your Home Assistant config directory's `custom_components/` folder.
2. Restart Home Assistant.
3. Add the `Beyond Power Voltra` integration from Settings > Devices & Services.
4. If Bluetooth discovery does not catch it automatically, add it manually with the Voltra's MAC address.

## Sharing

See [PUBLISHING.md](/Users/ticnitsi/Documents/BeyondPower-Port/home-assistant/PUBLISHING.md) for the clean path to share this privately now and prepare it for HACS later.

## Notes

- This integration assumes Home Assistant is running on hardware with reliable Bluetooth access to the Voltra.
- The component keeps retrying the recovered bootstrap until the protocol validates.
- All implementation files for this integration live under `home-assistant/`; nothing in `android/` was modified.
