# Dreo Smart Device Integration for Home Assistant
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)

HomeAssistant integration for Dreo brand smart devices. 

This integration is based on the engineering that Gavin Zyonse did for the HomeBridge integration here: https://github.com/zyonse/homebridge-dreo.

## Compatability
Currently supported fans:
The integration will not load if the fan is of another model.

- DR-HTF001S
- DR-HTF008S

## Installation
_I plan to add HACS support in the near future, but for now, this is manually installed._

### HACS (Recommended)

1. Add this repository to HACS *AS A CUSTOM REPOSITORY*.
1. Search for *Dreo Smart Device*, and choose install. 
1. Reboot Home Assistant and configure as below.

### Manually
Copy the `dreo` directory into your `/config/custom_components` directory, then restart your HomeAssistant Core.

### Configuration
Add the following content to your `configuration.yaml` file.  I recommend using `secrets.yaml` and storing the login information there.

```
dreo:
  username: [email]
  password: [password]

fan:
    - platform: dreo  
```

### Debugging
This integration logs to two loggers as shown below. To get verbose logs, change the log level.  Please have logs handy if you're reaching out for help.

```
logger:
    logs:
        dreo: info
        pydreo: info
```

### To Do
This is my first HA plugin and a bit slow going; bunch of stuff left to do:
* CI Pipeline
* Tests
* Config Flow
* Temperature Sensor
* Creating a Device in HA for the fan, inclusive of logo.