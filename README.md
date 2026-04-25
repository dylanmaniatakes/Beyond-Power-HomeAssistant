# Beyond Power Voltra Home Assistant Integration

This folder contains a custom Home Assistant integration that talks to a Beyond Power Voltra directly over Bluetooth Low Energy.

Creator note: Technogizguy / Dylan Maniatakes.

It is built from the recovered protocol work already encoded in the Android app:

- official VOLTRA GATT service and characteristic UUIDs
- the captured read-only bootstrap/handshake sequence
- the recovered `0x55` frame format and CRC rules
- confirmed parameter IDs for Weight Training, Resistance Band, Damper, and Isokinetic controls
- the recovered startup-image media upload flow using the Android-style 720x720 JPEG path
- live notification parsing for battery, reps, sets, cable length, load state, and other status

## Branding

- Home Assistant name: `Beyond Power Voltra`
- Home Assistant brand assets: `custom_components/voltra/brand/icon.png` and `logo.png`
- HACS/repository brand assets: `brand/icon.png`, `brand/logo.png`, plus root `icon.png` / `logo.png`
- Source image: square Beyond Power logo artwork used to generate the local brand assets

## What It Exposes

The custom component creates a BLE-backed Beyond Power Voltra device with:

- sensors for battery, force, cable length, reps, sets, status, serial, firmware, activation state, and Isometric telemetry
- switches for load, workout modes, assist-friendly mode toggles, and inverse chains
- covers for assistant-friendly percentage control of weight, band force/length, Damper, Isokinetic settings, and other adjustable values
- numbers for target load, band force/length, Damper level, cable offset, Weight Training settings, and Isokinetic settings
- selects for workout mode, resistance settings, and the Isokinetic eccentric mode
- buttons for refresh and cable-length adjustment mode
- a service for uploading a custom startup/power-off image to the VOLTRA

## Startup Image Upload

Use the `voltra.upload_startup_image` service with an `image_path` on the Home Assistant host. By default, the integration center-crops and encodes the image as the same 720x720 JPEG style used by the Android app, then sends the `0xAD` header/chunk/finalize/apply transfer over BLE.

Example service data:

```yaml
image_path: /config/www/voltra-startup.jpg
prepare_image: true
```

If you have more than one Voltra configured, include the target `entry_id` field from the service UI.

## Safety Model

The integration intentionally mirrors the Android app's conservative behavior:

- it must see a valid VOLTRA response frame before control entities become available
- load uses the parsed safety state and will refuse to engage if the device does not look ready
- only the command set already promoted in the Android notes is implemented
- OTA and undocumented raw writes are intentionally excluded

## Install

1. Copy `custom_components/voltra` into your Home Assistant config directory's `custom_components/` folder.
2. Restart Home Assistant.
3. Add the `Beyond Power Voltra` integration from Settings > Devices & Services.
4. If Bluetooth discovery does not catch it automatically, add it manually with the Voltra's MAC address.

## Sharing

See [PUBLISHING.md](/Users/ticnitsi/Documents/Beyond-Power-HomeAssistant/PUBLISHING.md) for the clean path to share this privately now and prepare it for HACS later.

## Dashboard Template

A ready-to-import Lovelace dashboard template is included in [dashboards/README.md](/Users/ticnitsi/Documents/Beyond-Power-HomeAssistant/dashboards/README.md).

## Notes

- This integration assumes Home Assistant is running on hardware with reliable Bluetooth access to the Voltra.
- The component keeps retrying the recovered bootstrap until the protocol validates.
- This repository is the shareable Home Assistant package for the integration.
