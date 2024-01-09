# Dreo Smart Device Integration for Home Assistant
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)

HomeAssistant integration for Dreo brand smart devices. Currently supports some models of Tower Fans and Air Circulators. 

You can purchase these devices from Amazon: [Dreo Fans on Amazon](https://www.amazon.com/gp/search?ie=UTF8&tag=jeffsteinbok-20&linkCode=ur2&linkId=264bf9285db76a172f81bad93760d162&camp=1789&creative=9325&index=hpc&keywords=Dreo%20Smart%20Fan)

This integration is based on the engineering that Gavin Zyonse did for the HomeBridge integration here: https://github.com/zyonse/homebridge-dreo.

> This documentation is intended to be accurate for the branch/tag it's in. If you are installing a specific version (including latest) of the integration, please change current viewing tag in GitHub to see the matching documentation.

## IMPORTANT NOTE ON CONFIGURATION
If you used the very early version of this that required editing `configuration.yaml`, you will need to do a 1-time reconfiguration. You can delete the configuration entries you added and go through the configuration flow within the HomeAssistant web site.

## Table of Contents
- [Compatability](#compatability)
- [Installation](#installation)
- [Options](#options)
- [Debugging](#debugging)
- [Adding new Fans](#addingFans)
- [To Do](#todo)
- [Contributing](contributing.md)
    
<a name="compatability"></a>
## IMPORTANT NOTE ON CONFIGURATION
If you used the very early version of this that required editing `configuration.yaml`, you will need to do a 1-time reconfiguration. You can delete the configuration entries you added and go through the configuration flow within the HomeAssistant web site.

## Table of Contents
- [Compatability](#compatability)
- [Installation](#installation)
- [Debugging](#debugging)
- [Adding new Fans](#addingFans)
- [To Do](#todo)
    
<a name="compatability"></a>
## Compatability
Currently supported fans:

Tower fans:
- DR-HTF001S
- DR-HTF002S
- DR-HTF004S
- DR-HTF005S
- DR-HTF007S
- DR-HTF008S

Air circulators:
- DR-HAF001S
- DR-HAF003S
- DR-HAF004S

If you have a different model that you can try, please see instructions [below](#addingfans).

<a name="installation"></a>
## Installation

### HACS (Recommended)

1. Add this repository to HACS *AS A CUSTOM REPOSITORY*.
1. Search for *Dreo Smart Device*, and choose install. 
1. Reboot Home Assistant and configure from the "Add Integration" flow.

Please note that there is a PR pending to add this to the default HACS repository.

### Manually
Copy the `dreo` directory into your `/config/custom_components` directory, then restart your HomeAssistant Core.

<a name="options"></a>
## Options
This plugin supports configuration from the HomeAssistant UX. The following options are available. 
|Option|Description|Default|
|------|-----------|-------|
|Auto-Reconnect WebSocket|Should the integration try to reconnect if the websocket connection fails. This should not need to be unchecked, but there have been occasional reports of crashes and we think this may be the cause.|True|

Note that at present you need to restart HA when you change an option for it to take effect.

<a name="debugging"></a>
## Debugging
Idealy, use the Diagnostics feature in HomeAssistant to get diagnostics from the integration. Sensitive info should be redacted automatically.

This integration logs to two loggers as shown below. To get verbose logs, change the log level.  Please have logs handy if you're reaching out for help.

```
logger:
    logs:
        dreo: debug
        pydreo: debug
```

You also may consider enabling verbose logging for the `websocket` component.

<a name="addingFans"></a>
## Adding New Fans
Don't see your model listed above? Let me know in the Issues and I'll add it. Please make sure to include:

* Model - in the format above
* Number of speeds the fan supports (not including "off")
* Does the fan support oscilating?
* What preset modes are supported?
* Is temperature supported?

Depending on answers, I may reach out and need you to pull some debug logs.

### Debug Logs for New Fans

1. Turn on **debug** logging for **pydreo** and start up HA.
1. Go to your Dreo app on your phone, and perform the various commands you want to be able to use in HA.  Dreo servers will send updates to the WebSocket i'm listening on.
1. Go look at the logs, you should see something like the below.  Send me that, and if you can, how it maps to the actions you were performing.

```
2023-06-29 01:02:25,312 - pydreo - DEBUG - Received message for unknown or unsupported device. SN: XXX341964289-77f2977b24191a4a:001:0000000000b
2023-06-29 01:02:25,312 - pydreo - DEBUG - Message: {'method': 'control-report', 'devicesn': 'XXX0393341964289-77f2977b24191a4a:001:0000000000b', 'messageid': 'bdf23a1f-c8e1-4e22-8ad3-dc0cd5dfdc7c', 'timestamp': 1688025746, 'reported': {'windtype': 1}}
```

<a name="addingFans"></a>
## Adding New Fans
Don't see your model listed above? Let me know in the Issues and I'll add it. Please make sure to include:

* Model - in the format above
* Number of speeds the fan supports (not including "off")
* Does the fan support oscilating?
* What preset modes are supported?
* Is temperature supported?

Depending on answers, I may reach out and need you to pull some debug logs.

### Debug Logs for New Fans

1. Turn on **debug** logging for **pydreo** and start up HA.
1. Go to your Dreo app on your phone, and perform the various commands you want to be able to use in HA.  Dreo servers will send updates to the WebSocket i'm listening on.
1. Go look at the logs, you should see something like the below.  Send me that, and if you can, how it maps to the actions you were performing.

```
2023-06-29 01:02:25,312 - pydreo - DEBUG - Received message for unknown or unsupported device. SN: XXX341964289-77f2977b24191a4a:001:0000000000b
2023-06-29 01:02:25,312 - pydreo - DEBUG - Message: {'method': 'control-report', 'devicesn': 'XXX0393341964289-77f2977b24191a4a:001:0000000000b', 'messageid': 'bdf23a1f-c8e1-4e22-8ad3-dc0cd5dfdc7c', 'timestamp': 1688025746, 'reported': {'windtype': 1}}
```

<a name="todo"></a>
## To Do
This is my first HA plugin and a bit slow going; bunch of stuff left to do:
* Tests
