# Dreo Smart Device Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge)](https://github.com/hacs/integration)

HomeAssistant integration for Dreo brand smart devices. Currently supports some models of Tower Fans, Air Circulators and Space Heaters.

You can purchase these devices from Amazon: [Dreo Fans on Amazon](https://www.amazon.com/gp/search?ie=UTF8&tag=jeffsteinbok-20&linkCode=ur2&linkId=264bf9285db76a172f81bad93760d162&camp=1789&creative=9325&index=hpc&keywords=Dreo%20Smart%20Fan)

This integration is based on the engineering that Gavin Zyonse did for the HomeBridge integration here: https://github.com/zyonse/homebridge-dreo.

> This documentation is intended to be accurate for the branch/tag it's in. If you are installing a specific version (including latest) of the integration, please change current viewing tag in GitHub to see the matching documentation.

## Table of Contents

-   [Compatibility](#compatibility)
-   [Installation](#installation)
-   [Options](#options)
-   [Debugging](#debugging)
-   [Adding new Fans](#adding-new-fans)
-   [To Do](#to-do)

## Compatibility

Currently supported models are listed below.

#### Tower fans

-   DR-HTF001S
-   DR-HTF002S
-   DR-HTF004S
-   DR-HTF005S
-   DR-HTF007S
-   DR-HTF008S

#### Air circulators

-   DR-HAF001S
-   DR-HAF003S
-   DR-HAF004S

#### Humidifiers

-   No humidifiers are supported at this time, but possible support in the future is being discussed in [issue #60](https://github.com/JeffSteinbok/hass-dreo/issues/60)

#### Space Heaters

-   DR-HSH004S

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

Use the Diagnostics feature in HomeAssistant to get diagnostics from the integration. Sensitive info should be redacted automatically.

In your `configuration.yaml` file, add this:

```
logger:
    logs:
        dreo: debug
        pydreo: debug
```

Now restart HomeAssistant. Perform the actions needed to generate some debugging info.

##### Download the full logs

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

-   Model - in the format above
-   Number of speeds the fan supports (not including "off")
-   Does the fan support oscillating?
-   What preset modes are supported?
-   Is temperature supported?

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

-   Tests
