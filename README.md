# Dreo Smart Device Integration for Home Assistant (Unofficial)

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge)](https://github.com/hacs/integration)

[![CI Validation](https://github.com/JeffSteinbok/hass-dreo/actions/workflows/ci.yaml/badge.svg)](https://github.com/JeffSteinbok/hass-dreo/actions/workflows/ci.yaml)
[![Release Automation](https://github.com/JeffSteinbok/hass-dreo/actions/workflows/release.yaml/badge.svg)](https://github.com/JeffSteinbok/hass-dreo/actions/workflows/release.yaml)


Unofficial HomeAssistant integration for Dreo brand smart devices. Currently supports most models of Fans, Air Conditioners, Humidifiers, Dehumidifiers and Space Heaters as well as ChefMaker. I do not work for Dreo; just something I'm doing for fun.

You can purchase these devices from Amazon: [Dreo Fans on Amazon](https://www.amazon.com/gp/search?ie=UTF8&tag=jeffsteinbok-20&linkCode=ur2&linkId=264bf9285db76a172f81bad93760d162&camp=1789&creative=9325&index=hpc&keywords=Dreo%20Smart%20Fan)

This integration is based on the engineering that Gavin Zyonse did for the HomeBridge integration here: <https://github.com/zyonse/homebridge-dreo>.

> This documentation is intended to be accurate for the branch/tag it's in. If you are installing a specific version (including latest) of the integration, please change current viewing tag in GitHub to see the matching documentation.

## A Note on Betas (Pre-Release)

The maintainers and I only have a small subset of the devices that this integration supports and we depend on users who open issues to confirm things work. I will keep a release in Beta until I get confirmation from folks that things work, then I'll promote.

## Interested in Contributing?

I'm always happy to have people add features via Pull Request. More info on how to capture network traces and what not can be found on: [Contributing](CONTRIBUTING.md).

## Table of Contents

- [Compatibility](#compatibility)
- [Installation](#installation)
- [Options](#options)
- [Debugging](#debugging)
- [Adding New Devices](#adding-new-devices)
- [To Do](#to-do)

## Compatibility

This integration supports the following device types:

| Device Type | Model Prefix(es) |
| ----------- | ---------------- |
| Tower Fans | DR-HTF |
| Air Circulators | DR-HAF, DR-HPF |
| Ceiling Fans | DR-HCF |
| Air Purifiers | DR-HAP |
| Space Heaters | DR-HSH, WH* |
| Air Conditioners | DR-HAC |
| Humidifiers | DR-HHM |
| Dehumidifiers | DR-HDH |
| Cookers (ChefMaker) | DR-KCM |
| Evaporative Coolers | DR-HEC |

**[View complete list of tested models →](SUPPORTED_MODELS.md)**

**[Space Heater Documentation →](HEATERS.md)** - Learn about heater-specific features, thermostat controls, and the 24-hour remote control timeout.

### Supported Entity Types

Depending on your device model and capabilities, the integration creates the following Home Assistant entities:

- **Fan** - Primary fan control (speed, oscillation, preset modes)
- **Climate** - For heaters and air conditioners (temperature control, modes)
- **Humidifier** - For humidifiers and dehumidifiers
- **Light** - Display lights and main lights (on/off, brightness, color temperature when supported)
- **RGB Light** - Atmosphere/ambient lights for ceiling fans (RGB color control)
- **Switch** - Individual device features (child lock, oscillation, mute, etc.)
- **Sensor** - Temperature, humidity, and other sensor readings
- **Number** - Adjustable numeric settings

## Installation

### HACS (Recommended)

Dreo is now part of the default [HACS](https://hacs.xyz) store. If you're not interested in development branches this is the easiest way to install.

#### Installing Dreo Smart Device Integration

1. Open `HACS`
2. Click `Integrations`
3. Search `Dreo`
4. Click the `Dreo Smart Device Integration` and install

### Manually

Copy the `dreo` directory into your `/config/custom_components` directory, then restart your HomeAssistant Core.

## Initial Configuration

> [!IMPORTANT]
> If you used the very early version of this that required editing `configuration.yaml`, you will need to do a one-time reconfiguration. Delete the configuration entries you added and then go through the configuration flow within HomeAssistant.

1. In HA, open `Settings`
2. Click `Devices & services`
3. Click `Add integration` (blue button at the bottom right of the screen)
4. Search `Dreo` and select it
5. Enter your `Dreo` username & password (same login you use on the Dreo app)

Once the Dreo app has been installed,

## Options

This plugin supports configuration from the HomeAssistant UX. The following options are available.
|Option|Description|Default|
|------|-----------|-------|
|Auto-Reconnect WebSocket|Should the integration try to reconnect if the websocket connection fails. This should not need to be unchecked, but there have been occasional reports of crashes and we think this may be the cause.|True|

Note that at present you need to restart HA when you change an option for it to take effect.

## Device Management

### Removing Devices

You can remove individual Dreo devices from Home Assistant through the UI:

1. Navigate to **Settings** → **Devices & Services**
2. Click on the **Dreo** integration
3. Click on the device you want to remove
4. Click the three-dot menu (⋮) in the top right
5. Select **Delete**
6. Confirm the deletion

The device will be removed from Home Assistant but will remain in your Dreo account. If you reload the integration or restart Home Assistant, the device will be re-discovered and added back automatically.

## Debugging

Use the **Diagnostics** feature in HomeAssistant to get diagnostics from the integration. Sensitive info should be redacted automatically.

In your `configuration.yaml` file, add this:

```
logger:
    logs:
        dreo: debug
        pydreo: debug
```

Now restart HomeAssistant. Perform the actions needed to generate some debugging info.

##### Download the full logs

Note that these may contain sensitive information, so do always check before sending them to someone.

1. In HA, open `Settings`
2. Click `System`
3. Click `Logs`
4. Click `Download full log`

##### Download diagnostics (`.json` file)

1. In HA, open `Settings`
2. Click `Device & services`
3. Click `Dreo`
4. Click on the three-dot hamburger menu (next to `Configure`) and click `Download diagnostics`.

#### Enable WebSocket debugging

In some cases, you may need to enable WebSocket debugging. You can do that by adding the following to your `configuration.yaml` file.

```
logger:
    logs:
        homeassistant.components.websocket_api: debug
```

## Adding New Devices

Don't see your model listed above? Create an [issue](https://github.com/JeffSteinbok/hass-dreo/issues) and I'll add it.

**Please make sure to include:**

- Model number (in the format shown in [Supported Models](SUPPORTED_MODELS.md))
- Device type (fan, heater, humidifier, etc.)
- For fans: Number of speeds supported (not including "off")
- Does the device support oscillating?
- What preset modes are supported?
- Any special features (temperature display, timer, etc.)

Depending on answers, I may reach out and need you to pull some debug logs.

### Debug Logs for New Devices

1. Enable [debugging](#debugging)
2. Go to the Dreo app on your mobile device and perform the various commands you want to be able to use in HA. Dreo servers will send updates to the WebSocket that the integration is listening on.
3. Go look at the logs, you should see something like the below. Create an [issue](https://github.com/JeffSteinbok/hass-dreo/issues) and include the lines related to `pydreo`, the diagnostics `json` file, and if possible, what actions you performed in the app.

```
2023-06-29 01:02:25,312 - pydreo - DEBUG - Received message for unknown or unsupported device. SN: XXX341964289-77f2977b24191a4a:001:0000000000b
2023-06-29 01:02:25,312 - pydreo - DEBUG - Message: {'method': 'control-report', 'devicesn': 'XXX0393341964289-77f2977b24191a4a:001:0000000000b', 'messageid': 'bdf23a1f-c8e1-4e22-8ad3-dc0cd5dfdc7c', 'timestamp': 1688025746, 'reported': {'windtype': 1}}
```
