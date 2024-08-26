# Dreo Smart Device Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge)](https://github.com/hacs/integration)

HomeAssistant integration for Dreo brand smart devices. Currently supports some models of Tower Fans, Air Circulators and Space Heaters.

You can purchase these devices from Amazon: [Dreo Fans on Amazon](https://www.amazon.com/gp/search?ie=UTF8&tag=jeffsteinbok-20&linkCode=ur2&linkId=264bf9285db76a172f81bad93760d162&camp=1789&creative=9325&index=hpc&keywords=Dreo%20Smart%20Fan)

This integration is based on the engineering that Gavin Zyonse did for the HomeBridge integration here: <https://github.com/zyonse/homebridge-dreo>.

> This documentation is intended to be accurate for the branch/tag it's in. If you are installing a specific version (including latest) of the integration, please change current viewing tag in GitHub to see the matching documentation.

## Interested in Contributing?

I'm always happy to have people add features via Pull Request. More info on how to capture network traces and what not can be found on: [Contributing](contributing.md).

## Table of Contents

- [Compatibility](#compatibility)
- [Installation](#installation)
- [Options](#options)
- [Debugging](#debugging)
- [Adding new Fans](#adding-new-fans)
- [To Do](#to-do)

## Compatibility

Currently supported models are listed below.

### Fans

The following fans types are supported. Not all variants have been tested.

| Fan Type | Model Prefix(es) | Notes |
| -------- | ------------ | ------ |
| Tower Fans | DR-HTF | |
| Air Circulators | DR-HAF, DR-HPF | |
| Ceiling Fans | DR-HCF | No light support. |

Models that have been specifically tested can be found below.

#### Tower Fans

- DR-HTF001S
- DR-HTF002S
- DR-HTF004S
- DR-HTF005S
- DR-HTF007S
- DR-HTF008S
- DR-HTF009S
- DR-HTF010S

#### Air Circulators

- DR-HAF001S
- DR-HAF003S
- DR-HAF004S
- DR-HPF001S
- DR-HPF002S
- DR-HPF004S
- DR-HPF005S

#### Ceiling Fans
-   DR-HCF001S - No Light Support

### Humidifiers

- No humidifiers are supported at this time, but possible support in the future is being discussed in [issue #60](https://github.com/JeffSteinbok/hass-dreo/issues/60)

### Space Heaters

- DR-HSH004S
- DR-HSH009S
- DR-HSH009AS
- WH719S
- WH739S

### Air Conditioners

- DR-HAC005S

### Cookers

- DR-KCM001S

Heaters are modeled as climate devices, which enables the ability to put a thermostat control for the heater into your HA dashboards. Some examples are shown below.

Oscillation is now supported, but shown under "swing mode" since this is how the climate device models that. Note that for all heaters, to satisfy UL listings the
remote control is disabled if it has not been used for 24 hours, which will then necessitate a quick tap on the WiFi button on the physical heater to resume the ability
to control the device remotely via either the Dreo app or this HA integration.

<table>
    <tr>
        <td><img src="https://raw.githubusercontent.com/jeffsteinbok/hass-dreo/main/auto-mode-thermostat.png" width="300" alt="eco/auto mode thermostat"></td>
        <td><img src="https://raw.githubusercontent.com/jeffsteinbok/hass-dreo/main/heat-mode-thermostat.png" width="300" alt="heat mode thermostat"></td>
        <td><img src="https://raw.githubusercontent.com/jeffsteinbok/hass-dreo/main/fan-mode-thermostat.png" width="300" alt="fan mode thermostat"></td>
        <td><img src="https://raw.githubusercontent.com/jeffsteinbok/hass-dreo/main/off-mode-thermostat.png" width="300" alt="off mode thermostat"></td>
    </tr>
    <tr>
        <td>Auto/Eco Mode</td>
        <td>Heat Mode</td>
        <td>Fan Mode</td>
        <td>Off</td>
    </tr>
    <tr>
        <td><img src="https://raw.githubusercontent.com/jeffsteinbok/hass-dreo/main/mode-list.png" width="200" alt="HVAC mode list"></td>
        <td><img src="https://raw.githubusercontent.com/jeffsteinbok/hass-dreo/main/fan-mode-list.png" width="200" alt="fan mode list"></td>
        <td><img src="https://raw.githubusercontent.com/jeffsteinbok/hass-dreo/main/preset-mode-list.png" width="200" alt="preset mode list"></td>
        <td><img src="https://raw.githubusercontent.com/jeffsteinbok/hass-dreo/main/swing-mode-list.png" width="200" alt="swing mode list"></td>
    </tr>
    <tr>
        <td>HVAC Modes</td>
        <td>Fan Modes</td>
        <td>Preset Modes</td>
        <td>Swing Modes</td>
    </tr>
    <tr>
        <td colspan="2" align="center"><img src="https://raw.githubusercontent.com/jeffsteinbok/hass-dreo/main/heater-entities.png" width="200" alt="heater entities"></td>
        <td colspan="2" align="center"><img src="https://raw.githubusercontent.com/jeffsteinbok/hass-dreo/main/compact-thermostat.png" width="200" alt="compact-thermostat"></td> 
    </tr>
    <tr>
        <td colspan="2" align="center">Heater Entities</td>
        <td colspan="2" align="center">Compact Thermostat View</td>
    </tr>
</table>

#### Different models

If you have a different model that you can try, please see instructions [below](#addingfans).

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

## Adding New Fans

Don't see your model listed above? Create an [issue](https://github.com/JeffSteinbok/hass-dreo/issues) and I'll add it.

**Please make sure to include:**

- Model - in the format above
- Number of speeds the fan supports (not including "off")
- Does the fan support oscillating?
- What preset modes are supported?
- Is temperature supported?

Depending on answers, I may reach out and need you to pull some debug logs.

### Debug Logs for New Fans

1. Enable [debugging](#debugging)
2. Go to the Dreo app on your mobile device and perform the various commands you want to be able to use in HA. Dreo servers will send updates to the WebSocket that the integration is listening on.
3. Go look at the logs, you should see something like the below. Create an [issue](https://github.com/JeffSteinbok/hass-dreo/issues) and include the lines related to `pydreo`, the diagnostics `json` file, and if possible, what actions you performed in the app.

```
2023-06-29 01:02:25,312 - pydreo - DEBUG - Received message for unknown or unsupported device. SN: XXX341964289-77f2977b24191a4a:001:0000000000b
2023-06-29 01:02:25,312 - pydreo - DEBUG - Message: {'method': 'control-report', 'devicesn': 'XXX0393341964289-77f2977b24191a4a:001:0000000000b', 'messageid': 'bdf23a1f-c8e1-4e22-8ad3-dc0cd5dfdc7c', 'timestamp': 1688025746, 'reported': {'windtype': 1}}
```

## To Do

This is my first HA plugin and a bit slow going; bunch of stuff left to do:

- Tests
